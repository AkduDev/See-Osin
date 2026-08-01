"""Base classes for OSINT modules and providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from see.core.types import CarrierResult, OwnerResult, SocialResult
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("module_base")


class BaseModule(ABC):
    """
    Base class for all OSINT modules.
    
    Each module represents a domain (phones, emails, etc)
    and coordinates multiple providers for that domain.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Module name."""
        ...
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Module description."""
        ...
    
    @property
    @abstractmethod
    def domain(self) -> str:
        """Domain this module handles (phones, emails, etc)."""
        ...
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if module is available."""
        ...
    
    @abstractmethod
    async def scan(self, target: str, **kwargs) -> Any:
        """Perform OSINT scan on target."""
        ...


class BaseProvider(ABC):
    """
    Base class for all API providers.
    
    Providers are responsible for fetching data from
    external APIs and services.
    """
    
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
    def supports_carrier(self) -> bool:
        """Whether this provider supports carrier lookup."""
        return False
    
    @property
    def supports_owner(self) -> bool:
        """Whether this provider supports owner lookup."""
        return False
    
    @property
    def supports_social(self) -> bool:
        """Whether this provider supports social media lookup."""
        return False
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (API key configured, etc)."""
        ...
    
    async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
        """Get carrier information for phone number."""
        return None
    
    async def get_owner(self, phone: str, config: AppConfig) -> OwnerResult | None:
        """Get owner information for phone number."""
        return None
    
    async def get_social(self, phone: str, config: AppConfig) -> list[SocialResult]:
        """Get social media profiles for phone number."""
        return []
