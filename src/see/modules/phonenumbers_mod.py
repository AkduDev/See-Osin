"""Phonenumbers offline module for See OSINT tool."""

from __future__ import annotations

from typing import Any

import phonenumbers
from phonenumbers import carrier, geocoder, timezone as tz

from see.core.parser import PhoneInfo
from see.core.schemas import get_phone_type_name
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("phonenumbers")


class PhonenumbersModule(BaseModule):
    """Offline phone number lookup using Google's phonenumbers library."""

    @property
    def name(self) -> str:
        return "phonenumbers"

    @property
    def description(self) -> str:
        return "Offline phone metadata (carrier, country, timezone)"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def target_field(self) -> str:
        return "carrier"

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Lookup phone metadata using phonenumbers library."""
        logger.info(f"Running phonenumbers lookup for {phone.e164}")

        try:
            parsed = phonenumbers.parse(phone.e164, None)

            carrier_name = carrier.name_for_number(parsed, "en") or "Unknown"
            location = geocoder.description_for_number(parsed, "en") or "Unknown"
            time_zones = list(tz.time_zones_for_number(parsed))
            timezone_str = time_zones[0] if time_zones else "Unknown"

            num_type = phonenumbers.number_type(parsed)
            line_type = get_phone_type_name(num_type)

            result = {
                "carrier": carrier_name,
                "location": location,
                "timezone": timezone_str,
                "line_type": line_type,
                "source": "phonenumbers",
            }

            logger.info(f"Phonenumbers result: carrier={carrier_name}, location={location}")
            return result

        except Exception as e:
            logger.error(f"Phonenumbers lookup failed: {e}")
            return None
