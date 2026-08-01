"""Phonenumbers library provider for phone OSINT."""

from __future__ import annotations

import phonenumbers as pn
from phonenumbers import carrier as pn_carrier
from phonenumbers import timezone as pn_tz

from see.modules.phones.providers.base import BasePhoneProvider
from see.core.types import CarrierResult
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("phonenumbers_provider")


class PhonenumbersProvider(BasePhoneProvider):
    """
    Provider using the phonenumbers library.
    
    This is a local library that provides carrier and timezone
    information without API keys.
    """
    
    @property
    def name(self) -> str:
        return "phonenumbers"
    
    @property
    def description(self) -> str:
        return "Carrier and timezone via phonenumbers library"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    @property
    def supports_carrier(self) -> bool:
        return True
    
    @property
    def is_available(self) -> bool:
        """Always available (local library)."""
        return True
    
    async def get_carrier(self, phone: str, config: AppConfig) -> CarrierResult | None:
        """Get carrier information using phonenumbers library."""
        try:
            parsed = pn.parse(phone, None)
            
            if not pn.is_valid_number(parsed):
                return None
            
            carrier_name = pn_carrier.name_for_number(parsed, "en") or ""
            carrier_name_full = pn_carrier.name_for_number(parsed, "es") or carrier_name
            
            # Get timezone
            tz_list = pn_tz.time_zones_for_number(parsed)
            timezone_str = tz_list[0] if tz_list else ""
            
            # Get region
            region = pn.region_code_for_number(parsed) or ""
            
            # Determine line type
            number_type = pn.number_type(parsed)
            line_type = self._get_line_type(number_type)
            
            return CarrierResult(
                source="phonenumbers",
                carrier=carrier_name_full or carrier_name,
                line_type=line_type,
                country=region,
                country_code=str(parsed.country_code),
                timezone=timezone_str,
                valid=True,
            )
            
        except Exception as e:
            logger.error(f"Phonenumbers lookup failed: {e}")
            return None
    
    def _get_line_type(self, number_type: int) -> str:
        """Convert phonenumbers type to string."""
        type_map = {
            pn.PhoneNumberType.MOBILE: "mobile",
            pn.PhoneNumberType.FIXED_LINE: "fixed_line",
            pn.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
            pn.PhoneNumberType.TOLL_FREE: "toll_free",
            pn.PhoneNumberType.PREMIUM_RATE: "premium_rate",
            pn.PhoneNumberType.SHARED_COST: "shared_cost",
            pn.PhoneNumberType.VOIP: "voip",
            pn.PhoneNumberType.PERSONAL_NUMBER: "personal",
            pn.PhoneNumberType.PAGER: "pager",
            pn.PhoneNumberType.UAN: "uan",
            pn.PhoneNumberType.VOICEMAIL: "voicemail",
            pn.PhoneNumberType.UNKNOWN: "unknown",
        }
        return type_map.get(number_type, "unknown")
