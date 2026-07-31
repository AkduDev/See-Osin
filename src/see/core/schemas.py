"""Shared schemas and type definitions for See OSINT tool."""

from __future__ import annotations

from typing import Any, Protocol, TypedDict


# ============================================================================
# Module Result Types
# ============================================================================


class CarrierResult(TypedDict, total=False):
    """Result from carrier lookup modules (phonenumbers, numverify)."""

    carrier: str
    location: str
    timezone: str
    line_type: str
    source: str
    # NumVerify specific
    valid: bool
    country: str
    country_code: str
    international_format: str
    local_format: str


class OwnerResult(TypedDict, total=False):
    """Result from owner lookup modules (abstract)."""

    name: str
    location: str
    country: str
    carrier: str
    line_type: str
    source: str


class SocialProfile(TypedDict):
    """A single social media profile found."""

    platform: str
    platform_id: str
    type: str
    found: bool
    url: str | None
    status: str


class SocialResult(TypedDict, total=False):
    """Result from social media OSINT modules (maigret)."""

    profiles: list[SocialProfile]
    platforms_checked: list[str]
    found_count: int
    source: str


class DorkQuery(TypedDict):
    """A single search engine dork."""

    query: str
    description: str


class SearchURLs(TypedDict):
    """Search URLs for a dork query."""

    query: str
    google: str
    bing: str | None
    duckduckgo: str | None


class DorksResult(TypedDict, total=False):
    """Result from search engine dorks modules."""

    dorks: list[DorkQuery]
    search_urls: list[SearchURLs]
    source: str


# ============================================================================
# Module Protocol
# ============================================================================


class Module(Protocol):
    """Protocol defining the interface for OSINT modules."""

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def requires_api_key(self) -> bool: ...

    @property
    def target_field(self) -> str: ...

    @property
    def is_available(self) -> bool: ...

    async def lookup(self, phone: Any, config: Any) -> dict[str, Any] | None: ...


# ============================================================================
# Configuration Types
# ============================================================================


class APIKeysDict(TypedDict, total=False):
    """API keys configuration."""

    numverify: str
    abstract: str
    opencellid: str
    numlookup: str


class TorDict(TypedDict, total=False):
    """Tor configuration."""

    enabled: bool
    socks_port: int
    control_port: int
    max_requests_per_circuit: int
    auto_rotate: bool
    exit_countries: list[str]


# ============================================================================
# Constants
# ============================================================================

# Phone number type mapping (phonenumbers library -> string)
# This is the single source of truth for type conversion
PHONE_TYPE_MAP: dict[int, str] = {}  # Will be populated at runtime

# Default modules for different lookup types
DEFAULT_MODULES = ["phonenumbers", "numverify", "numlookup", "maigret", "google_dorks"]
OWNER_MODULES = ["phonenumbers", "numverify", "numlookup", "abstract", "maigret", "google_dorks", "reverse_lookup"]

# Module name -> target field mapping
MODULE_TARGET_FIELDS: dict[str, str] = {
    "phonenumbers": "carrier",
    "numverify": "carrier",
    "numlookup": "carrier",
    "abstract": "owner",
    "maigret": "social_profiles",
    "google_dorks": "search_dorks",
    "reverse_lookup": "owner",
    "opencellid": "location",
    "spam": "spam",
    "hibp": "breaches",
}


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
