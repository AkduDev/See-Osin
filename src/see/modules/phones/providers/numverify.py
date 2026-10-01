"""NumVerify API provider for phone OSINT."""

from __future__ import annotations

from see.core.types import CarrierResult
from see.modules.phones.providers.base import BasePhoneProvider
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("numverify_provider")

NUMVERIFY_BASE_URL = "https://apilayer.net/api/validate"


class NumVerifyProvider(BasePhoneProvider):
    """
    Provider using NumVerify API.
    
    Provides carrier, location, and line type information.
    Requires API key from https://numverify.com
    """
    
    @property
    def name(self) -> str:
        return "numverify"
    
    @property
    def description(self) -> str:
        return "Carrier, location, and line type via NumVerify API"
    
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
        return bool(config.api_keys.numverify)
    
    async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
        """Get carrier information using NumVerify API."""
        api_key = config.api_keys.numverify
        
        if not api_key:
            logger.warning("NumVerify API key not configured")
            return None
        
        logger.info(f"Running NumVerify lookup for {phone}")
        
        params = {
            "access_key": api_key,
            "number": phone.replace("+", ""),
            "country_code": "",
            "format": 1,
        }
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
        ) as client:
            data = await client.get(NUMVERIFY_BASE_URL, params=params)
            
            if not data:
                logger.error("NumVerify API request failed")
                return None
            
            if not data.get("valid"):
                logger.warning("NumVerify reports number as invalid")
                return CarrierResult(
                    source="numverify",
                    valid=False,
                )
            
            return CarrierResult(
                source="numverify",
                carrier=data.get("carrier", "Unknown"),
                line_type=data.get("line_type", "unknown"),
                country=data.get("country_name", "Unknown"),
                country_code=data.get("country_code", ""),
                location=data.get("location", ""),
                valid=True,
            )
