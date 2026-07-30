"""Abstract API Person Lookup module for See OSINT tool."""

from __future__ import annotations

from typing import Any

from see.core.parser import PhoneInfo
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("abstract")

ABSTRACT_BASE_URL = "https://phonevalidation.abstractapi.com/v1/"


class AbstractPersonModule(BaseModule):
    """Abstract API module for phone number owner lookup."""

    @property
    def name(self) -> str:
        return "abstract"

    @property
    def description(self) -> str:
        return "Owner name and location via Abstract API"

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
        """Lookup owner information using Abstract Phone Validation API."""
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

            result = {
                "name": data.get("name", {}).get("full", ""),
                "location": data.get("location", {}).get("city", ""),
                "country": data.get("location", {}).get("country", {}).get("name", ""),
                "carrier": data.get("carrier", ""),
                "line_type": data.get("line_type", ""),
                "source": "abstract",
            }

            logger.info(f"Abstract result: name={result['name']}, location={result['location']}")
            return result
