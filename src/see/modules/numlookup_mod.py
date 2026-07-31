"""NumLookupAPI module for See OSINT tool."""

from __future__ import annotations

from typing import Any

from see.core.parser import PhoneInfo
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("numlookup")

NUMLOOKUP_BASE_URL = "https://api.numlookupapi.com/v1/validate"


class NumLookupModule(BaseModule):
    """NumLookupAPI module for global phone number validation."""

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
    def target_field(self) -> str:
        return "carrier"

    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config

        config = load_config()
        return bool(config.api_keys.numlookup)

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Lookup phone data using NumLookupAPI."""
        api_key = config.api_keys.numlookup

        if not api_key:
            logger.warning("NumLookupAPI key not configured, skipping")
            return None

        logger.info(f"Running NumLookupAPI lookup for {phone.e164}")

        headers = {"apikey": api_key}

        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
        ) as client:
            data = await client.get(
                NUMLOOKUP_BASE_URL,
                params={"phone": phone.e164},
                headers=headers,
            )

            if not data:
                logger.error("NumLookupAPI request failed")
                return None

            if not data.get("valid"):
                logger.warning("NumLookupAPI reports number as invalid")
                return {"valid": False, "source": "numlookup"}

            result = {
                "valid": data.get("valid", False),
                "carrier": data.get("carrier", "Unknown"),
                "location": data.get("location", "Unknown"),
                "line_type": data.get("line_type", "unknown"),
                "country": data.get("country_name", "Unknown"),
                "country_code": data.get("country_code", ""),
                "international_format": data.get("intl_format", ""),
                "local_format": data.get("local_format", ""),
                "source": "numlookup",
            }

            logger.info(f"NumLookupAPI result: carrier={result['carrier']}, location={result['location']}")
            return result
