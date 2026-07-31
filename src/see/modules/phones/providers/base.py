"""Base class for phone number providers."""

from __future__ import annotations

from abc import abstractmethod

from see.modules.base import BaseProvider
from see.core.types import CarrierResult, OwnerResult
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("phone_provider")


class BasePhoneProvider(BaseProvider):
    """
    Base class for phone number providers.
    
    All phone providers must implement at least one of:
    - get_carrier: Get carrier information
    - get_owner: Get owner information
    """
    
    @property
    def domain(self) -> str:
        return "phones"
    
    @abstractmethod
    async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
        """Get carrier information for phone number."""
        ...
    
    async def get_owner(self, phone: str, config: AppConfig) -> OwnerResult | None:
        """Get owner information for phone number. Default: not supported."""
        return None
