"""Base module interface for See OSINT tool."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from see.core.parser import PhoneInfo
from see.utils.config import AppConfig


class BaseModule(ABC):
    """
    Abstract base class for all OSINT modules.

    Subclasses must implement:
    - name: Module identifier
    - description: Human-readable description
    - requires_api_key: Whether this module needs an API key
    - target_field: Which field in OSINTResult this module populates
    - lookup: The actual lookup logic

    Optional overrides:
    - is_available: Check if module is ready (default: True)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Module name identifier (e.g., 'phonenumbers', 'numverify')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Module description for display purposes."""
        pass

    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Whether this module requires an API key to function."""
        pass

    @property
    @abstractmethod
    def target_field(self) -> str:
        """
        The field name in OSINTResult this module populates.

        Examples:
        - 'carrier' for carrier lookup modules
        - 'owner' for owner/name lookup modules
        - 'social_profiles' for social media OSINT
        - 'search_dorks' for search engine dorks
        - 'location' for geolocation modules
        """
        pass

    @property
    def is_available(self) -> bool:
        """
        Check if this module is ready to use.

        Default implementation returns True. Override in subclasses
        that require API keys or external dependencies.

        Returns:
            True if module can be used, False otherwise
        """
        return True

    @abstractmethod
    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """
        Perform lookup for the given phone number.

        Args:
            phone: Parsed phone number information
            config: Application configuration

        Returns:
            Dictionary with lookup results, or None if no data available
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', target='{self.target_field}')>"
