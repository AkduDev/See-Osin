"""Base class for phone number providers."""

from __future__ import annotations

from see.core.types import CarrierResult, OwnerResult, SocialResult, SpamResult
from see.modules.base import BaseProvider
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("phone_provider")


class BasePhoneProvider(BaseProvider):
    """
    Base class for phone number providers.
    
    Providers implement the capabilities they support:
    - get_carrier: Get carrier information
    - get_owner: Get owner information
    - get_spam: Spam/scam report lookup
    - get_search_links: Manual investigation links (dorks, spam DBs)
    """
    
    @property
    def domain(self) -> str:
        return "phones"
    
    async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
        """Get carrier information for phone number. Default: not supported."""
        return None
    
    async def get_owner(self, phone: str, config: AppConfig) -> OwnerResult | None:
        """Get owner information for phone number. Default: not supported."""
        return None

    @property
    def supports_spam(self) -> bool:
        """Whether this provider supports spam/scam report lookup."""
        return False

    async def get_spam(self, phone: str, config: AppConfig) -> SpamResult | None:
        """Get spam/scam reports for phone number. Default: not supported."""
        return None

    @property
    def supports_search_links(self) -> bool:
        """Whether this provider generates investigation links."""
        return False

    async def get_search_links(
        self, phone: str, config: AppConfig
    ) -> list[SocialResult]:
        """Get manual investigation links (dorks, lookup sites). Default: none."""
        return []
