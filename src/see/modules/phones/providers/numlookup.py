"""NumLookupAPI provider for phone OSINT."""

from __future__ import annotations

from see.core.types import CarrierResult
from see.modules.phones.providers.base import BasePhoneProvider
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("numlookup_provider")

NUMLOOKUP_BASE_URL = "https://api.numlookupapi.com/v1/validate"


class NumLookupProvider(BasePhoneProvider):
    """
    Provider using NumLookupAPI.
    
    Provides global carrier, location, and line type information.
    Requires API key from https://numlookupapi.com
    """
    
    @property
    def name(self) -> str:
        return "numlookup"
    
    @property
    def description(self) -> str:
        return "Global carrier, location, and line type via NumLookupAPI"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    @property
    def supports_carrier(self) -> bool:
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config
        config = load_config()
        return bool(config.api_keys.numlookup)
    
    async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
        """Get carrier information using NumLookupAPI."""
        api_key = config.api_keys.numlookup
        
        if not api_key:
            logger.warning("NumLookupAPI key not configured")
            return None
        
        logger.info(f"Running NumLookupAPI lookup for {phone}")
        
        headers = {"apikey": api_key}
        url = f"{NUMLOOKUP_BASE_URL}/{phone}"
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
        ) as client:
            data = await client.get(url, headers=headers)
            
            if not data:
                logger.error("NumLookupAPI request failed")
                return None
            
            if not data.get("valid"):
                logger.warning("NumLookupAPI reports number as invalid")
                return CarrierResult(
                    source="numlookup",
                    valid=False,
                )
            
            return CarrierResult(
                source="numlookup",
                carrier=data.get("carrier", "Unknown"),
                line_type=data.get("line_type", "unknown"),
                country=data.get("country_name", "Unknown"),
                country_code=data.get("country_code", ""),
                location=data.get("location", ""),
                valid=True,
            )
