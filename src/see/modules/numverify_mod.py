"""NumVerify API module for See OSINT tool."""

from __future__ import annotations

from typing import Any

from see.core.parser import PhoneInfo
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("numverify")

NUMVERIFY_BASE_URL = "http://apilayer.net/api/validate"


class NumVerifyModule(BaseModule):
    """NumVerify API module for carrier and location data."""

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
    def target_field(self) -> str:
        return "carrier"

    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config

        config = load_config()
        return bool(config.api_keys.numverify)

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Lookup phone data using NumVerify API."""
        api_key = config.api_keys.numverify

        if not api_key:
            logger.warning("NumVerify API key not configured, skipping")
            return None

        logger.info(f"Running NumVerify lookup for {phone.e164}")

        params = {
            "access_key": api_key,
            "number": phone.e164.replace("+", ""),
            "country_code": "",
            "format": 1,
        }

        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
            rate_limit_per_minute=config.rate_limit.numverify_per_minute,
        ) as client:
            data = await client.get(NUMVERIFY_BASE_URL, params=params)

            if not data:
                logger.error("NumVerify API request failed")
                return None

            if not data.get("valid"):
                logger.warning("NumVerify reports number as invalid")
                return {"valid": False, "source": "numverify"}

            result = {
                "valid": data.get("valid", False),
                "carrier": data.get("carrier", "Unknown"),
                "location": data.get("location", "Unknown"),
                "line_type": data.get("line_type", "unknown"),
                "country": data.get("country_name", "Unknown"),
                "country_code": data.get("country_code", ""),
                "international_format": data.get("international_format", ""),
                "local_format": data.get("local_format", ""),
                "source": "numverify",
            }

            logger.info(f"NumVerify result: carrier={result['carrier']}, location={result['location']}")
            return result
