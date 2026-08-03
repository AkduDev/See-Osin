"""HTTP client with Tor support and rate limiting for See OSINT tool."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from see.utils.logger import get_logger

logger = get_logger("http_client")


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_minute: float = 60):
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0

    async def acquire(self) -> None:
        """Wait until rate limit allows next request."""
        now = time.monotonic()
        time_since_last = now - self.last_request_time

        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_request_time = time.monotonic()


async def _execute_with_retry(
    client: httpx.AsyncClient,
    url: str,
    retries: int,
    rate_limiter: RateLimiter,
    tor_client: Any = None,
    params: dict | None = None,
    headers: dict | None = None,
) -> dict[str, Any] | None:
    """
    Execute HTTP request with retry logic.

    This is the single source of truth for retry handling.
    """
    for attempt in range(retries):
        await rate_limiter.acquire()

        try:
            logger.debug(f"GET {url} (attempt {attempt + 1}/{retries})")
            response = await client.get(url, params=params, headers=headers)

            # Rotate Tor circuit if needed
            if tor_client and tor_client.should_rotate():
                tor_client.rotate_circuit()

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP {e.response.status_code} for {url}")
            if e.response.status_code == 429:
                wait_time = 2 ** (attempt + 1)
                logger.info(f"Rate limited, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                if tor_client:
                    tor_client.rotate_circuit()
            elif e.response.status_code >= 500:
                await asyncio.sleep(2 ** attempt)
            else:
                return None

        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)

    logger.error(f"All {retries} attempts failed for {url}")
    return None


class HTTPClient:
    """Async HTTP client with rate limiting, retries, and optional Tor support."""

    def __init__(
        self,
        timeout: float = 30.0,
        retries: int = 3,
        rate_limit_per_minute: float = 60,
        use_tor: bool = False,
        tor_client: Any = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.rate_limiter = RateLimiter(rate_limit_per_minute)
        self.use_tor = use_tor
        self.tor_client = tor_client
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> HTTPClient:
        if self.use_tor and self.tor_client:
            self._client = self.tor_client.get_async_client()
        else:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any) -> None:
        if self._client:
            await self._client.aclose()

    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any] | None:
        """Make GET request with retries and rate limiting."""
        if not self._client:
            raise RuntimeError("HTTPClient not initialized. Use 'async with'.")

        return await _execute_with_retry(
            client=self._client,
            url=url,
            retries=self.retries,
            rate_limiter=self.rate_limiter,
            tor_client=self.tor_client if self.use_tor else None,
            params=params,
            headers=headers,
        )

    async def get_response(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        follow_redirects: bool = True,
        read_body: bool = True,
        method: str = "GET",
    ) -> tuple[int, str | None] | None:
        """
        Make a request for existence checks.

        Uses streaming so the body is only downloaded when needed.

        Args:
            url: URL to request
            params: Optional query parameters
            headers: Optional request headers
            follow_redirects: Whether to follow redirects
            read_body: Whether to read the response body. When False the
                connection is closed right after the status line, which is
                much cheaper (used for status-code-only checks).
            method: HTTP method to use ("GET" or "HEAD").

        Returns:
            ``(status_code, body_text)`` tuple, or None on request error.
            ``body_text`` is ``None`` when ``read_body`` is False or the
            method is "HEAD".
        """
        if not self._client:
            raise RuntimeError("HTTPClient not initialized. Use 'async with'.")

        await self.rate_limiter.acquire()

        tor_client = self.tor_client if self.use_tor else None
        if tor_client and tor_client.should_rotate():
            tor_client.rotate_circuit()

        try:
            logger.debug(f"{method} {url} (raw)")
            async with self._client.stream(
                method,
                url,
                params=params,
                headers=headers,
                follow_redirects=follow_redirects,
            ) as response:
                status_code = response.status_code
                if method == "HEAD" or not read_body:
                    return status_code, None
                content = await response.aread()
                return status_code, content.decode("utf-8", errors="replace")
        except httpx.RequestError as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        finally:
            if tor_client:
                tor_client.increment_request_count()


class SyncHTTPClient:
    """Sync HTTP client with optional Tor support."""

    def __init__(
        self,
        timeout: float = 30.0,
        retries: int = 3,
        use_tor: bool = False,
        tor_client: Any = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.use_tor = use_tor
        self.tor_client = tor_client

    def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any] | None:
        """Make sync GET request with retries."""
        if self.use_tor and self.tor_client:
            client = self.tor_client.get_client()
        else:
            client = httpx.Client(timeout=self.timeout)

        try:
            for attempt in range(self.retries):
                try:
                    logger.debug(f"GET {url} (attempt {attempt + 1}/{self.retries})")
                    response = client.get(url, params=params, headers=headers)

                    if self.use_tor and self.tor_client and self.tor_client.should_rotate():
                        self.tor_client.rotate_circuit()

                    response.raise_for_status()
                    return response.json()

                except httpx.HTTPStatusError as e:
                    logger.warning(f"HTTP {e.response.status_code} for {url}")
                    if e.response.status_code == 429:
                        wait_time = 2 ** (attempt + 1)
                        logger.info(f"Rate limited, waiting {wait_time}s")
                        time.sleep(wait_time)
                        if self.use_tor and self.tor_client:
                            self.tor_client.rotate_circuit()
                    elif e.response.status_code >= 500:
                        time.sleep(2 ** attempt)
                    else:
                        return None

                except httpx.RequestError as e:
                    logger.error(f"Request error: {e}")
                    if attempt < self.retries - 1:
                        time.sleep(2 ** attempt)

        finally:
            client.close()

        logger.error(f"All {self.retries} attempts failed for {url}")
        return None
