"""Phone number parser and normalizer for See OSINT tool."""

from __future__ import annotations

import re
from dataclasses import dataclass

import phonenumbers
from phonenumbers import PhoneNumberFormat

from see.core.schemas import get_phone_type_name
from see.utils.logger import get_logger

logger = get_logger("parser")


@dataclass
class PhoneInfo:
    """Parsed phone number information."""

    original: str
    normalized: str
    e164: str
    national: str
    international: str
    country_code: int
    country: str
    national_number: str
    is_valid: bool
    is_possible: bool
    number_type: str | None = None


def parse_phone_number(phone_input: str, default_country: str = "US") -> PhoneInfo:
    """
    Parse and validate a phone number.

    Args:
        phone_input: Phone number string in any format
        default_country: Default country code for numbers without prefix

    Returns:
        PhoneInfo object with parsed information
    """
    logger.info(f"Parsing phone number: {phone_input}")

    cleaned = _clean_phone_number(phone_input)
    logger.debug(f"Cleaned input: {cleaned}")

    try:
        parsed = phonenumbers.parse(cleaned, default_country)
    except phonenumbers.NumberParseException:
        try:
            parsed = phonenumbers.parse(cleaned, None)
        except phonenumbers.NumberParseException as e:
            logger.error(f"Failed to parse phone number: {e}")
            return PhoneInfo(
                original=phone_input,
                normalized=cleaned,
                e164="",
                national="",
                international="",
                country_code=0,
                country="",
                national_number=cleaned,
                is_valid=False,
                is_possible=False,
            )

    is_valid = phonenumbers.is_valid_number(parsed)
    is_possible = phonenumbers.is_possible_number(parsed)

    country_code = parsed.country_code
    country = phonenumbers.region_code_for_number(parsed) or "Unknown"
    national_number = str(parsed.national_number)

    e164 = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    national = phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL)
    international = phonenumbers.format_number(parsed, PhoneNumberFormat.INTERNATIONAL)

    # Use shared type mapping from schemas.py
    num_type = phonenumbers.number_type(parsed)
    number_type = get_phone_type_name(num_type)

    logger.info(f"Parsed: {e164} | Country: {country} | Valid: {is_valid} | Type: {number_type}")

    return PhoneInfo(
        original=phone_input,
        normalized=e164,
        e164=e164,
        national=national,
        international=international,
        country_code=country_code,
        country=country,
        national_number=national_number,
        is_valid=is_valid,
        is_possible=is_possible,
        number_type=number_type,
    )


def _clean_phone_number(phone: str) -> str:
    """Clean phone number string."""
    phone = phone.strip()
    phone = phone.replace("tel:", "").replace("TEL:", "")
    cleaned = re.sub(r"[^\d+\-() ]", "", phone)
    return cleaned


def get_country_name(country_code: str) -> str:
    """Get country name from country code."""
    import pycountry

    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name if country else "Unknown"
    except Exception:
        return "Unknown"
