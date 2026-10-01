"""Shared constants for See OSINT tool."""

from __future__ import annotations

# ============================================================================
# Email Constants
# ============================================================================

# Free email providers
FREE_EMAIL_PROVIDERS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
    "aol.com", "icloud.com", "mail.com", "protonmail.com", "proton.me",
    "zoho.com", "yandex.com", "gmx.com", "fastmail.com", "tutanota.com",
}

# Disposable email domains
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.email", "temp-mail.org", "guerrillamail.com",
    "mailinator.com", "yopmail.com", "trashmail.com", "fakeinbox.com",
    "sharklasers.com", "guerrillamailblock.com", "grr.la", "dispostable.com",
    "maildrop.cc", "tempail.com", "tempmail.net", "temp-mail.io",
    "10minutemail.com", "mailnesia.com", "tempail.net", "temp-mail.com",
    "burnermail.io", "harakirimail.com", "mohmal.com",
}

# Known webmail providers
WEBMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
    "aol.com", "icloud.com", "mail.com", "protonmail.com", "proton.me",
    "zoho.com", "yandex.com", "gmx.com", "fastmail.com", "tutanota.com",
}


# ============================================================================
# Phone Constants
# ============================================================================

# Phone number type mapping (phonenumbers library -> string)
PHONE_TYPE_MAP: dict[int, str] = {}  # Will be populated at runtime


def init_phone_type_map() -> dict[int, str]:
    """Initialize the phone type mapping. Call once at startup."""
    global PHONE_TYPE_MAP

    try:
        import phonenumbers

        PHONE_TYPE_MAP = {
            phonenumbers.PhoneNumberType.FIXED_LINE: "fixed_line",
            phonenumbers.PhoneNumberType.MOBILE: "mobile",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_line_or_mobile",
            phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
            phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium_rate",
            phonenumbers.PhoneNumberType.SHARED_COST: "shared_cost",
            phonenumbers.PhoneNumberType.VOIP: "voip",
            phonenumbers.PhoneNumberType.PERSONAL_NUMBER: "personal",
            phonenumbers.PhoneNumberType.PAGER: "pager",
            phonenumbers.PhoneNumberType.UAN: "uan",
            phonenumbers.PhoneNumberType.VOICEMAIL: "voicemail",
            phonenumbers.PhoneNumberType.UNKNOWN: "unknown",
        }
    except ImportError:
        # Fallback if phonenumbers not installed
        PHONE_TYPE_MAP = {}

    return PHONE_TYPE_MAP


def get_phone_type_name(type_value: int) -> str:
    """Get human-readable phone type name from type value."""
    if not PHONE_TYPE_MAP:
        init_phone_type_map()
    return PHONE_TYPE_MAP.get(type_value, "unknown")


# ============================================================================
# Module Constants
# ============================================================================

# Default modules for different lookup types.
# Only the domain modules registered by see.modules.register_all_modules()
# exist: providers (phonenumbers, spam, dorks, ...) live inside each domain.
DEFAULT_MODULES = ["phones"]
OWNER_MODULES = ["phones"]

# Module name -> target field mapping
MODULE_TARGET_FIELDS: dict[str, str] = {
    "phonenumbers": "carrier",
    "numverify": "carrier",
    "numlookup": "carrier",
    "abstract": "owner",
    "spam": "spam",
    "dorks": "search_links",
    "holehe": "breaches",
    "hibp": "breaches",
}


# ============================================================================
# HTTP Constants
# ============================================================================

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
