"""Abstract API provider for phone OSINT."""

from __future__ import annotations

from see.core.types import CarrierResult, OwnerResult
from see.modules.phones.providers.base import BasePhoneProvider
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("abstract_provider")

ABSTRACT_BASE_URL = "https://phoneintelligence.abstractapi.com/v1/"


class AbstractProvider(BasePhoneProvider):
    """
    Provider using Abstract Phone Intelligence API.
    
    Provides carrier, location, owner, risk, and breach information.
    Requires API key from https://abstractapi.com
    """
    
    @property
    def name(self) -> str:
        return "abstract"
    
    @property
    def description(self) -> str:
        return "Owner, carrier, risk, and breaches via Abstract API"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    @property
    def supports_carrier(self) -> bool:
        return True
    
    @property
    def supports_owner(self) -> bool:
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config
        config = load_config()
        return bool(config.api_keys.abstract)
    
    async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
        """Get carrier information using Abstract API."""
        data = await self._fetch_data(phone, config)
        
        if not data:
            return None
        
        carrier = data.get("phone_carrier", {})
        location = data.get("phone_location", {})
        validation = data.get("phone_validation", {})
        
        return CarrierResult(
            source="abstract",
            carrier=carrier.get("name", ""),
            line_type=carrier.get("line_type", ""),
            country=location.get("country_name", ""),
            country_code=location.get("country_code", ""),
            location=location.get("city", ""),
            timezone=location.get("timezone", ""),
            valid=validation.get("is_valid", False),
        )
    
    async def get_owner(self, phone: str, config: AppConfig) -> OwnerResult | None:
        """Get owner information using Abstract API."""
        data = await self._fetch_data(phone, config)
        
        if not data:
            return None
        
        registration = data.get("phone_registration", {})
        risk = data.get("phone_risk", {})
        breaches = data.get("phone_breaches", {})
        validation = data.get("phone_validation", {})
        
        name = registration.get("name")
        if not name:
            return None
        
        return OwnerResult(
            source="abstract",
            name=name,
            type=registration.get("type", ""),
            risk_level=risk.get("risk_level", ""),
            is_disposable=risk.get("is_disposable", False),
            is_voip=validation.get("is_voip", False),
            total_breaches=breaches.get("total_breaches", 0) or 0,
        )
    
    async def _fetch_data(self, phone: str, config: AppConfig) -> dict | None:
        """Fetch data from Abstract API."""
        api_key = config.api_keys.abstract
        
        if not api_key:
            logger.warning("Abstract API key not configured")
            return None
        
        logger.info(f"Running Abstract lookup for {phone}")
        
        params = {
            "api_key": api_key,
            "phone": phone,
        }
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
        ) as client:
            data = await client.get(ABSTRACT_BASE_URL, params=params)
            
            if not data:
                logger.error("Abstract API request failed")
                return None
            
            return data
