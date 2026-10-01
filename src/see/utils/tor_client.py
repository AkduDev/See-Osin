"""Tor client with automatic circuit rotation for See OSINT tool."""

from __future__ import annotations

import time
from typing import Any

import httpx
from httpx_socks import AsyncProxyTransport, SyncProxyTransport

from see.utils.logger import get_logger

logger = get_logger("tor")

try:
    from stem.control import Controller

    STEM_AVAILABLE = True
except ImportError:
    STEM_AVAILABLE = False
    logger.warning("stem library not installed. Circuit rotation disabled.")


class TorClient:
    """
    Tor client with automatic circuit rotation.

    Features:
    - SOCKS5 proxy through Tor
    - Automatic circuit rotation every N requests
    - Manual circuit rotation
    - Exit node country selection
    """

    def __init__(
        self,
        socks_port: int = 9050,
        control_port: int = 9051,
        max_requests_per_circuit: int = 10,
        timeout: float = 30.0,
    ):
        self.socks_port = socks_port
        self.control_port = control_port
        self.max_requests_per_circuit = max_requests_per_circuit
        self.timeout = timeout

        self._controller: Any = None
        self._request_count = 0
        self._connected = False

    @property
    def is_available(self) -> bool:
        """Check if Tor is available."""
        try:
            transport = self.get_transport()
            with httpx.Client(transport=transport, timeout=5.0) as client:
                response = client.get("https://check.torproject.org/api/ip")
                return response.status_code == 200
        except Exception:
            return False

    @property
    def current_ip(self) -> str | None:
        """Get current exit node IP."""
        try:
            transport = self.get_transport()
            with httpx.Client(transport=transport, timeout=10.0) as client:
                response = client.get("https://api.ipify.org")
                if response.status_code == 200:
                    return response.text.strip()
        except Exception as e:
            logger.debug(f"Exit IP lookup failed: {e}")
        return None

    def connect(self, password: str | None = None) -> bool:
        """Connect to Tor control port."""
        if not STEM_AVAILABLE:
            logger.warning("stem not available, cannot connect to control port")
            return False

        try:
            self._controller = Controller.from_port(port=self.control_port)
            self._controller.authenticate(password=password)
            self._connected = True
            logger.info("Connected to Tor controller")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to Tor controller: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from Tor controller."""
        if self._controller:
            try:
                self._controller.close()
            except Exception as e:
                logger.debug(f"Error closing controller: {e}")
            self._controller = None
            self._connected = False
            logger.info("Disconnected from Tor controller")

    def rotate_circuit(self) -> bool:
        """Request a new Tor circuit (NEWNYM signal)."""
        if not self._connected or not self._controller:
            logger.warning("Not connected to Tor controller")
            return False

        try:
            self._controller.signal("NEWNYM")
            time.sleep(2)  # Wait for new circuit
            self._request_count = 0
            new_ip = self.current_ip
            logger.info(f"Circuit rotated. New exit IP: {new_ip}")
            return True
        except Exception as e:
            logger.error(f"Circuit rotation failed: {e}")
            return False

    def should_rotate(self) -> bool:
        """Check if circuit should be rotated based on request count."""
        return self._request_count >= self.max_requests_per_circuit

    def increment_request_count(self) -> None:
        """Increment the request counter."""
        self._request_count += 1

    def get_transport(self) -> SyncProxyTransport:
        """Get a SOCKS5 transport through Tor."""
        return SyncProxyTransport.from_url(f"socks5://127.0.0.1:{self.socks_port}")

    def get_async_transport(self) -> AsyncProxyTransport:
        """Get an async SOCKS5 transport through Tor."""
        return AsyncProxyTransport.from_url(f"socks5://127.0.0.1:{self.socks_port}")

    def get_client(self, **kwargs: Any) -> httpx.Client:
        """Get a configured httpx client through Tor."""
        transport = self.get_transport()
        return httpx.Client(transport=transport, timeout=self.timeout, follow_redirects=True, **kwargs)

    def get_async_client(self, **kwargs: Any) -> httpx.AsyncClient:
        """Get a configured async httpx client through Tor."""
        transport = self.get_async_transport()
        return httpx.AsyncClient(transport=transport, timeout=self.timeout, follow_redirects=True, **kwargs)

    def fetch(self, url: str, **kwargs: Any) -> httpx.Response | None:
        """Fetch a URL through Tor with automatic circuit rotation."""
        if self.should_rotate():
            self.rotate_circuit()

        client: httpx.Client | None = None
        try:
            client = self.get_client(**kwargs)
            response = client.get(url)
            self.increment_request_count()
            return response
        except Exception as e:
            logger.error(f"Tor fetch failed: {e}")
            return None
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception as e:
                    logger.debug(f"Tor client close failed: {e}")

    async def async_fetch(self, url: str, **kwargs: Any) -> httpx.Response | None:
        """Async fetch a URL through Tor."""
        if self.should_rotate():
            self.rotate_circuit()

        client: httpx.AsyncClient | None = None
        try:
            client = self.get_async_client(**kwargs)
            response = await client.get(url)
            self.increment_request_count()
            return response
        except Exception as e:
            logger.error(f"Async Tor fetch failed: {e}")
            return None
        finally:
            if client is not None:
                try:
                    await client.aclose()
                except Exception as e:
                    logger.debug(f"Tor async client close failed: {e}")


class TorManager:
    """Singleton manager for Tor client."""

    _instance: TorManager | None = None
    _client: TorClient | None = None

    @classmethod
    def get_client(cls, **kwargs: Any) -> TorClient:
        """Get or create Tor client instance."""
        if cls._client is None:
            cls._client = TorClient(**kwargs)
        return cls._client

    @classmethod
    def disconnect(cls) -> None:
        """Disconnect and cleanup Tor client."""
        if cls._client:
            cls._client.disconnect()
            cls._client = None
