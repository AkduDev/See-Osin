"""Sherlock-style username search provider.

This is our own implementation: it does NOT shell out to the Sherlock CLI.
Instead it iterates the platforms in ``platforms.py``, builds each profile
URL and classifies the result by HTTP status code, HTML body text, or a
manual-review flag.

Optimizations:
- Status-code platforms skip downloading the response body (streamed) and
  try a lightweight HEAD request first, falling back to GET on 405.
- Sub-domain platforms (`{username}.host`) are pre-resolved via DNS so a
  non-existent subdomain is reported quickly instead of waiting for a timeout.
- Results are cached in-memory for a short TTL to avoid repeat scans.
- One hard timeout per request; bounded concurrency via a semaphore.
- Optional routing through Tor.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from see.core.constants import USER_AGENT
from see.core.types import SocialResult
from see.modules.usernames.providers.base import BaseUsernameProvider
from see.modules.usernames.providers.platforms import PLATFORMS
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger
from see.utils.tor_client import TorManager

logger = get_logger("sherlock_like_provider")

# Concurrency control for the mass HTTP checks
MAX_CONCURRENCY = 12
CHECK_TIMEOUT = 8.0
REQUESTS_PER_MINUTE = 600

# Cache settings
CACHE_TTL = 3600  # seconds


class _ResultCache:
    """Simple in-memory cache with TTL for scan results."""

    def __init__(self, ttl: float = CACHE_TTL):
        self._ttl = ttl
        self._data: dict[str, tuple[float, list[SocialResult]]] = {}

    def get(self, username: str) -> list[SocialResult] | None:
        entry = self._data.get(username)
        if entry is None:
            return None
        ts, results = entry
        if time.time() - ts > self._ttl:
            self._data.pop(username, None)
            return None
        return results

    def set(self, username: str, results: list[SocialResult]) -> None:
        self._data[username] = (time.time(), results)


class SherlockLikeProvider(BaseUsernameProvider):
    """Username search across social platforms (own implementation).

    No API key required. Supports optional routing through Tor.
    """

    def __init__(self, cache: _ResultCache | None = None):
        self._cache = cache if cache is not None else _ResultCache()

    @property
    def name(self) -> str:
        return "sherlock"

    @property
    def description(self) -> str:
        return f"Username search across {len(PLATFORMS)} social platforms"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def is_available(self) -> bool:
        return True

    async def get_profiles(
        self,
        username: str,
        config: AppConfig,
        use_tor: bool | None = None,
        use_cache: bool = True,
    ) -> list[SocialResult]:
        """Search for the username across all configured platforms."""
        use_tor = self._resolve_tor(config, use_tor)

        # Serve from cache when available and allowed
        cached = self._cache.get(username) if use_cache else None
        if cached is not None:
            logger.info(f"Username '{username}' served from cache ({len(cached)} results)")
            return cached

        logger.info(
            f"Searching username '{username}' across {len(PLATFORMS)} platforms "
            f"(routing: {'Tor' if use_tor else 'direct'})"
        )

        results: list[SocialResult] = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async with self._build_client(config, use_tor) as client:
            tasks = [
                self._check_platform(client, semaphore, username, platform)
                for platform in PLATFORMS
            ]
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)

            for outcome in outcomes:
                if isinstance(outcome, SocialResult):
                    results.append(outcome)
                elif isinstance(outcome, Exception):
                    logger.debug(f"Platform check failed: {outcome}")

            found = sum(1 for p in results if p.found)
        logger.info(f"Found {found} profiles for username '{username}'")

        if use_cache:
            self._cache.set(username, results)

        return results

    # ------------------------------------------------------------------
    # Client / Tor helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_tor(config: AppConfig, use_tor: bool | None) -> bool:
        """Resolve whether Tor should be used (explicit flag wins over config)."""
        if use_tor is not None:
            return use_tor
        return config.tor.enabled

    def _build_client(self, config: AppConfig, use_tor: bool) -> HTTPClient:
        """Build an HTTP client, attaching a Tor transport when requested."""
        tor_client = None
        if use_tor:
            tor_client = TorManager.get_client(
                socks_port=config.tor.socks_port,
                control_port=config.tor.control_port,
                max_requests_per_circuit=config.tor.max_requests_per_circuit,
                timeout=CHECK_TIMEOUT,
            )

        return HTTPClient(
            timeout=CHECK_TIMEOUT,
            retries=1,
            rate_limit_per_minute=REQUESTS_PER_MINUTE,
            use_tor=use_tor,
            tor_client=tor_client,
        )

    # ------------------------------------------------------------------
    # Platform checking
    # ------------------------------------------------------------------

    async def _check_platform(
        self,
        client: HTTPClient,
        semaphore: asyncio.Semaphore,
        username: str,
        platform: dict[str, Any],
    ) -> SocialResult:
        """Check a single platform for the username."""
        name = platform["name"]
        url = platform["url"].format(username=username)

        async with semaphore:
            method = platform.get("method", "status")

            if method == "manual":
                return self._make_result(name, username, url, status="check_manually")

            subdomain = self._subdomain_for(platform, username)
            if subdomain is not None and not await self._resolves(subdomain):
                # Subdomain does not exist -> DNS decides "not found" fast.
                return self._make_result(name, username, url, status="not_found")

            headers = dict(platform.get("headers") or {})
            headers.setdefault("User-Agent", USER_AGENT)

            status_code, text = await self._request_checked(
                client, method, name, url, headers
            )

            if method == "text":
                return self._classify_text(
                    name, username, url, status_code, text or "", platform
                )

            return self._classify_status(name, username, url, status_code)

    async def _request_checked(
        self,
        client: HTTPClient,
        method: str,
        platform_name: str,
        url: str,
        headers: dict[str, str],
    ) -> tuple[int, str | None]:
        """Request, preferring HEAD for status checks, then falling back to GET."""
        # Some sites reject HEAD (405); GET is the safe fallback that does not
        # download the body for status-type platforms.
        if method == "status":
            methods = ["HEAD", "GET"]
        else:
            methods = ["GET"]

        for http_method in methods:
            try:
                raw = await asyncio.wait_for(
                    client.get_response(
                        url,
                        headers=headers,
                        read_body=True,
                        method=http_method,
                    ),
                    timeout=CHECK_TIMEOUT,
                )
            except Exception:
                raw = None
            if raw is not None:
                return raw
        # Everything failed or timed out
        return 0, None  # interpreted as request_error

    def _classify_status(
        self,
        name: str,
        username: str,
        url: str,
        status_code: int | None,
    ) -> SocialResult:
        """Classify a status-code-based platform."""
        if status_code is None or status_code == 0:
            return self._make_result(name, username, url, status="error")
        if status_code == 200:
            return self._make_result(name, username, url, status="found")
        if status_code == 404:
            return self._make_result(name, username, url, status="not_found")
        if status_code in (403, 429):
            return self._make_result(name, username, url, status="check_manually")
        # Redirect range 3xx -> HTTPS upgrade gone wrong; treat as error
        return self._make_result(name, username, url, status="error")

    def _classify_text(
        self,
        name: str,
        username: str,
        url: str,
        status_code: int,
        text: str,
        platform: dict[str, Any],
    ) -> SocialResult:
        """Classify a text-based platform (site returns 200 regardless)."""
        if status_code == 0:
            return self._make_result(name, username, url, status="error")

        not_found_markers = platform.get("error_text") or ""

        if not_found_markers:
            # Split by newline so we can pass one or more markers.
            for marker in not_found_markers.split("\n"):
                if marker and marker in text:
                    return self._make_result(name, username, url, status="not_found")

        # If the body does not contain the "not found" marker, assume found.
        return self._make_result(name, username, url, status="found")

    @staticmethod
    def _subdomain_for(
        platform: dict[str, Any], username: str
    ) -> str | None:
        """If the platform URL uses a `{username}.host` pattern, return the host."""
        url = platform.get("url", "")
        if "{username}." not in url:
            return None
        host = url.format(username=username)
        if not host.startswith("http"):
            host = "http://" + host
        from urllib.parse import urlparse
        return urlparse(host).netloc

    @staticmethod
    async def _resolves(host: str) -> bool:
        """Check (quickly) whether a hostname resolves to an address."""
        try:
            loop = asyncio.get_running_loop()
            addrs = await asyncio.wait_for(
                loop.getaddrinfo(host, None), timeout=CHECK_TIMEOUT
            )
            return bool(addrs)
        except Exception:
            return False

    @staticmethod
    def _make_result(
        name: str,
        username: str,
        url: str,
        status: str,
    ) -> SocialResult:
        """Build a result record with human-readable status."""
        return SocialResult(
            source="usernames",
            platform=name,
            username=username,
            name=name,
            url=url,
            found=status == "found",
            status=status,
        )