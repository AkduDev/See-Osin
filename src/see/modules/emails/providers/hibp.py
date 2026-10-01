"""Have I Been Pwned provider for email breach checking."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import quote

from see.core.types import BreachResult
from see.modules.emails.providers.base import BaseEmailProvider
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("hibp_provider")

HIBP_BASE_URL = "https://haveibeenpwned.com/api/v3"

# HIBP rejects requests without an identifiable user agent (403)
HIBP_USER_AGENT = "See-OSINT/0.2 (https://github.com/AkduDev/See-Osin)"


def parse_hibp_payload(payload: list[dict[str, Any]], email: str) -> BreachResult | None:
    """Map HIBP breach list to a BreachResult (pure, testable)."""
    if not payload:
        return None

    breaches: list[dict[str, Any]] = []
    sources: list[str] = []

    for entry in payload:
        breach = {
            "name": entry.get("Title") or entry.get("Name", ""),
            "date": entry.get("BreachDate", ""),
            "domain": entry.get("Domain", ""),
            "pwn_count": entry.get("PwnCount", 0),
            "data_classes": entry.get("DataClasses", []),
        }
        breaches.append(breach)
        domain = breach["domain"] or breach["name"]
        if domain and domain not in sources:
            sources.append(domain)

    if not breaches:
        return None

    return BreachResult(
        source="hibp",
        email=email,
        breaches=breaches,
        total_breaches=len(breaches),
        sources=sources,
    )


class HIBPProvider(BaseEmailProvider):
    """
    Provider using the Have I Been Pwned v3 API.

    Requires an HIBP subscription key (see https://haveibeenpwned.com/API/Key).
    Respects the documented rate limit via config.rate_limit.hibp_delay_seconds.

    API semantics: 404 means "not in any breach" (a valid negative answer);
    401/403/429 are raised as errors so they never masquerade as clean results.
    """

    def __init__(self, config: AppConfig | None = None):
        self._config = config

    @property
    def name(self) -> str:
        return "hibp"

    @property
    def description(self) -> str:
        return "Email breach check via Have I Been Pwned API"

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def supports_breaches(self) -> bool:
        return True

    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config
        config = self._config or load_config()
        return bool(config.api_keys.hibp)

    async def get_breaches(self, email: str, config: AppConfig) -> BreachResult | None:
        """Check if the email appears in known breaches (HIBP v3)."""
        api_key = (config.api_keys.hibp or "").strip()
        if not api_key:
            logger.warning("HIBP API key not configured (SEE_HIBP_KEY)")
            return None

        # Respect documented rate limit
        delay = config.rate_limit.hibp_delay_seconds
        if delay > 0:
            await asyncio.sleep(delay)

        url = (
            f"{HIBP_BASE_URL}/breachedaccount/{quote(email, safe='')}"
            f"?truncateResponse=false"
        )
        headers = {
            "hibp-api-key": api_key,
            "user-agent": HIBP_USER_AGENT,
            "Accept": "application/json",
        }

        logger.info(f"Running HIBP breach check for {email}")

        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=1,  # HIBP: no aggressive retries, respect rate limit
            use_tor=config.tor.enabled,
        ) as client:
            response = await client.get_response(url, headers=headers)

        if response is None:
            return None

        status, body = response

        if status == 404:
            # Not found in any breach - a clean negative answer
            return None
        if status == 401:
            raise RuntimeError("HIBP: invalid API key")
        if status == 403:
            raise RuntimeError(f"HIBP: forbidden ({(body or '').strip()[:120]})")
        if status == 429:
            raise RuntimeError("HIBP: rate limit exceeded, retry later")
        if status != 200 or not body:
            return None

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            logger.error("HIBP: unexpected non-JSON response")
            return None

        return parse_hibp_payload(payload, email)
