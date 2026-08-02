"""Base class for username OSINT providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from see.core.types import SocialResult
from see.utils.config import AppConfig


class BaseUsernameProvider(ABC):
    """Base class for providers that search usernames across platforms."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Provider description."""
        ...

    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True

    @abstractmethod
    async def get_profiles(self, username: str, config: AppConfig) -> list[SocialResult]:
        """Search for username across platforms."""
        ...
