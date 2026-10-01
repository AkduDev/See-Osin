"""Base provider for email OSINT."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from see.core.types import BreachResult, DisposableResult, SocialResult
from see.utils.config import AppConfig


class BaseEmailProvider(ABC):
    """Base class for email OSINT providers."""
    
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
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        return False
    
    @property
    def supports_breaches(self) -> bool:
        """Whether this provider supports breach lookup."""
        return False
    
    @property
    def supports_disposable(self) -> bool:
        """Whether this provider supports disposable email check."""
        return False
    
    @property
    def supports_social(self) -> bool:
        """Whether this provider supports social media lookup."""
        return False
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        ...
    
    async def get_breaches(self, email: str, config: AppConfig) -> Optional[BreachResult]:
        """Get breach information for email."""
        return None
    
    async def check_disposable(self, email: str, config: AppConfig) -> Optional[DisposableResult]:
        """Check if email is disposable."""
        return None
    
    async def get_social_profiles(self, email: str, config: AppConfig) -> list[SocialResult]:
        """Get social media profiles for email."""
        return []

    @property
    def supports_verification(self) -> bool:
        """Whether this provider supports SMTP-style deliverability checks."""
        return False

    async def verify_deliverability(self, email: str, config: AppConfig) -> dict | None:
        """Verify whether an email address is deliverable (RCPT TO, no mail sent)."""
        return None
