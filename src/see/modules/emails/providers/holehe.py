"""Holehe provider for email breach checking."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from see.core.types import BreachResult
from see.modules.emails.providers.base import BaseEmailProvider
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("holehe_provider")

# Curated subset of holehe modules: stable endpoints, low false-positive rate.
# Running all ~120 modules per scan is slow and most are dead in 2026.
HOLEHE_MODULE_ALLOWLIST = frozenset(
    {
        "gravatar",
        "github",
        "aboutme",
        "archive",
        "codepen",
        "docker",
        "imgur",
        "patreon",
        "wordpress",
        "lastfm",
        "tumblr",
        "flickr",
        "spotify",
        "discord",
        "venmo",
        "ebay",
        "adobe",
        "protonmail",
        "yahoo",
        "office365",
        "replit",
        "strava",
        "komoot",
    }
)


def holehe_out_to_breaches(out: list[dict[str, Any]], email: str) -> BreachResult | None:
    """Map raw holehe module output to a BreachResult (pure, testable)."""
    breaches: list[dict[str, Any]] = []
    sources: list[str] = []

    for entry in out:
        if not entry.get("exists"):
            continue
        name = entry.get("name", "unknown")
        breach = {
            "name": name,
            "domain": entry.get("domain", ""),
            "method": entry.get("method", ""),
        }
        if entry.get("others"):
            breach["details"] = entry["others"]
        breaches.append(breach)
        domain = entry.get("domain", "") or name
        if domain not in sources:
            sources.append(domain)

    if not breaches:
        return None

    return BreachResult(
        source="holehe",
        email=email,
        breaches=breaches,
        total_breaches=len(breaches),
        sources=sources,
    )


def _run_holehe_sync(
    email: str, timeout: int, modules: list[str] | frozenset | None = None
) -> list[dict[str, Any]]:
    """Run holehe modules synchronously in a worker thread (trio loop)."""
    import httpx
    import trio
    from holehe.core import get_functions, import_submodules, launch_module

    wanted = set(modules) if modules else set(HOLEHE_MODULE_ALLOWLIST)
    all_modules = import_submodules("holehe.modules")
    websites = [fn for fn in get_functions(all_modules) if getattr(fn, "__name__", "") in wanted]
    if not websites:
        return []

    out: list[dict[str, Any]] = []

    async def _runner() -> None:
        client = httpx.AsyncClient(timeout=timeout)
        try:
            async with trio.open_nursery() as nursery:
                for website in websites:
                    nursery.start_soon(launch_module, website, email, client, out)
        finally:
            await client.aclose()

    trio.run(_runner)
    return out


class HoleheProvider(BaseEmailProvider):
    """
    Provider using Holehe for account-existence checking.

    Runs a curated subset of holehe modules (no API key required).
    A hit means the email has an account on that site, not necessarily
    a password breach.
    """

    def __init__(self, modules: list[str] | None = None):
        self._modules = list(modules) if modules else sorted(HOLEHE_MODULE_ALLOWLIST)
        self._last_run: dict[str, Any] = {"email": "", "at": 0.0}

    @property
    def name(self) -> str:
        return "holehe"

    @property
    def description(self) -> str:
        return "Email account-existence check via Holehe (curated modules)"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def supports_breaches(self) -> bool:
        return True

    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        try:
            import holehe  # noqa: F401
            import trio  # noqa: F401
            return True
        except ImportError:
            return False

    async def get_breaches(self, email: str, config: AppConfig) -> BreachResult | None:
        """Check email against holehe modules (runs in a thread, trio loop)."""
        logger.info(f"Running Holehe check for {email} ({len(self._modules)} modules)")

        try:
            out = await asyncio.to_thread(
                _run_holehe_sync, email, config.lookup.timeout, self._modules
            )
        except Exception as e:
            logger.warning(f"Holehe scan failed: {e}")
            return None

        rate_limited = sum(1 for e in out if e.get("rateLimit"))
        if rate_limited:
            logger.info(f"Holehe: {rate_limited} modules rate-limited")

        result = holehe_out_to_breaches(out, email)
        self._last_run = {"email": email, "at": time.time()}
        return result
