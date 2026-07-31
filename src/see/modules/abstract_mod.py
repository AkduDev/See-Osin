"""Abstract API Phone Intelligence module for See OSINT tool."""

from __future__ import annotations

from typing import Any

from see.core.parser import PhoneInfo
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("abstract")

ABSTRACT_BASE_URL = "https://phoneintelligence.abstractapi.com/v1/"


class AbstractPersonModule(BaseModule):
    """Abstract API module for phone number owner lookup."""

    @property
    def name(self) -> str:
        return "abstract"

    @property
    def description(self) -> str:
        return "Owner name, carrier, location, risk and breaches via Abstract API"

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def target_field(self) -> str:
        return "owner"

    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config

        config = load_config()
        return bool(config.api_keys.abstract)

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Lookup owner information using Abstract Phone Intelligence API."""
        api_key = config.api_keys.abstract

        if not api_key:
            logger.warning("Abstract API key not configured, skipping")
            return None

        logger.info(f"Running Abstract lookup for {phone.e164}")

        params = {
            "api_key": api_key,
            "phone": phone.e164,
        }

        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
        ) as client:
            data = await client.get(ABSTRACT_BASE_URL, params=params)

            if not data:
                logger.error("Abstract API request failed")
                return None

            # Extract registration info (owner name)
            registration = data.get("phone_registration", {})
            carrier = data.get("phone_carrier", {})
            location = data.get("phone_location", {})
            validation = data.get("phone_validation", {})
            risk = data.get("phone_risk", {})
            breaches = data.get("phone_breaches", {})

            result = {
                "name": registration.get("name", ""),
                "type": registration.get("type", ""),
                "carrier": carrier.get("name", ""),
                "line_type": carrier.get("line_type", ""),
                "location": location.get("city", ""),
                "region": location.get("region", ""),
                "country": location.get("country_name", ""),
                "country_code": location.get("country_code", ""),
                "timezone": location.get("timezone", ""),
                "is_valid": validation.get("is_valid", False),
                "line_status": validation.get("line_status", ""),
                "is_voip": validation.get("is_voip", False),
                "risk_level": risk.get("risk_level", ""),
                "is_disposable": risk.get("is_disposable", False),
                "total_breaches": breaches.get("total_breaches", 0),
                "source": "abstract",
            }

            logger.info(f"Abstract result: name={result['name']}, carrier={result['carrier']}")
            return result
