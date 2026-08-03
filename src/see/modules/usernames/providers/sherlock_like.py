"""Sherlock-style username search provider.

This is our own implementation: it does NOT shell out to the Sherlock CLI.
Instead it iterates the platforms in ``platforms.py``, builds each profile
URL and classifies the result by HTTP status code, HTML body text, or a
manual-review flag.

Optimizations:
- Status-code platforms skip downloading the response body (streamed).
- One hard timeout per request; bounded concurrency via a semaphore.
"""

from __future__ import annotations

import asyncio
from typing import Any

from see.core.types import SocialResult
from see.modules.usernames.providers.base import BaseUsernameProvider
from see.modules.usernames.providers.platforms import PLATFORMS
from see.core.constants import USER_AGENT
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("sherlock_like_provider")

# Concurrency control for the mass HTTP checks
MAX_CONCURRENCY = 12
CHECK_TIMEOUT = 8.0
REQUESTS_PER_MINUTE = 600


class SherlockLikeProvider(BaseUsernameProvider):
    """
    Username search across social platforms (own implementation).

    No API key required.
    """

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

    async def get_profiles(self, username: str, config: AppConfig) -> list[SocialResult]:
        """Search for the username across all configured platforms."""
        logger.info(f"Searching username '{username}' across {len(PLATFORMS)} platforms")

        results: list[SocialResult] = []
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async with HTTPClient(
            timeout=CHECK_TIMEOUT,
            retries=1,
            rate_limit_per_minute=REQUESTS_PER_MINUTE,
            use_tor=config.tor.enabled,
        ) as client:
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

        return results

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
                return self._make_result(name, username, url, found=False, status="check_manually")

            headers = dict(platform.get("headers") or {})
            headers.setdefault("User-Agent", USER_AGENT)

            # Only download the body when we actually inspect the HTML text
            try:
                raw = await asyncio.wait_for(
                    client.get_response(
                        url,
                        headers=headers,
                        read_body=(method == "text"),
                    ),
                    timeout=CHECK_TIMEOUT,
                )
            except Exception:
                return self._make_result(name, username, url, status="error", error="timeout")

            if raw is None:
                return self._make_result(name, username, url, status="error", error="request_error")

            status_code, text = raw

            if method == "text":
                return self._classify_text(name, username, url, status_code, text or "", platform)

            return self._classify_status(name, username, url, status_code)

    def _classify_status(
        self,
        name: str,
        username: str,
        url: str,
        status_code: int,
    ) -> SocialResult:
        """Classify a platform result based only on HTTP status code."""
        if status_code == 200:
            return self._make_result(name, username, url, found=True, status="found")
        if status_code in (404, 410, 400):
            return self._make_result(name, username, url, status="not_found")
        if status_code == 429:
            return self._make_result(name, username, url, status="error", error="rate_limited")
        if status_code == 403:
            return self._make_result(name, username, url, status="error", error="blocked")
        return self._make_result(name, username, url, status="error", error=f"http_{status_code}")

    def _classify_text(
        self,
        name: str,
        username: str,
        url: str,
        status_code: int,
        text: str,
        platform: dict[str, Any],
    ) -> SocialResult:
        """Classify a platform that always returns 200 by inspecting body text."""
        if status_code in (404, 410):
            return self._make_result(name, username, url, status="not_found")

        if status_code == 200:
            error_text = platform.get("error_text", "")
            lower_text = text.lower()
            if error_text and error_text.lower() in lower_text:
                return self._make_result(name, username, url, status="not_found")
            return self._make_result(name, username, url, found=True, status="found")

        return self._make_result(name, username, url, status="error", error=f"http_{status_code}")

    def _make_result(
        self,
        name: str,
        username: str,
        url: str,
        found: bool = False,
        status: str = "not_found",
        error: str | None = None,
    ) -> SocialResult:
        """Build a SocialResult consistently (single source of truth)."""
        return SocialResult(
            source="sherlock",
            platform=name,
            username=username,
            name="",
            url=url,
            found=found,
            status=status,
            error=error,
        )
