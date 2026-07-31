"""Shared types for See OSINT framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol


# ============================================================================
# Result Types
# ============================================================================


@dataclass
class BaseResult:
    """Base class for all OSINT results."""
    
    source: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success: bool = True
    error: str | None = None


@dataclass
class CarrierResult(BaseResult):
    """Result from carrier lookup."""
    
    carrier: str = ""
    line_type: str = ""
    country: str = ""
    country_code: str = ""
    location: str = ""
    timezone: str = ""
    valid: bool = False


@dataclass
class OwnerResult(BaseResult):
    """Result from owner lookup."""
    
    name: str = ""
    type: str = ""  # consumer, business, unknown
    risk_level: str = ""
    is_disposable: bool = False
    is_voip: bool = False
    total_breaches: int = 0


@dataclass
class SocialResult(BaseResult):
    """Result from social media lookup."""
    
    platform: str = ""
    username: str = ""
    name: str = ""
    url: str = ""
    found: bool = False
    status: str = ""  # found, not_found, check_manually


@dataclass
class PhoneResult:
    """Aggregated result for phone number OSINT."""
    
    input_number: str
    e164: str = ""
    national: str = ""
    international: str = ""
    valid: bool = False
    possible: bool = False
    
    # Country info
    country: str = ""
    country_code: str = ""
    
    # Results from providers
    carrier: CarrierResult | None = None
    owner: OwnerResult | None = None
    social_profiles: list[SocialResult] = field(default_factory=list)
    
    # Metadata
    modules_used: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    query_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "input": self.input_number,
            "query_time": self.query_time,
            "modules_used": self.modules_used,
            "errors": self.errors,
            "number": {
                "e164": self.e164,
                "national": self.national,
                "international": self.international,
                "valid": self.valid,
                "possible": self.possible,
            },
            "country": {
                "code": self.country,
                "country_code": self.country_code,
            },
        }
        
        if self.carrier:
            result["carrier"] = {
                "name": self.carrier.carrier,
                "line_type": self.carrier.line_type,
                "location": self.carrier.location,
                "source": self.carrier.source,
            }
        
        if self.owner:
            result["owner"] = {
                "name": self.owner.name,
                "type": self.owner.type,
                "risk_level": self.owner.risk_level,
                "source": self.owner.source,
            }
        
        if self.social_profiles:
            result["social_profiles"] = [
                {
                    "platform": p.platform,
                    "username": p.username,
                    "name": p.name,
                    "url": p.url,
                    "found": p.found,
                    "status": p.status,
                }
                for p in self.social_profiles
            ]
        
        return result


# ============================================================================
# Module Protocol
# ============================================================================


class Module(Protocol):
    """Protocol defining the interface for OSINT modules."""
    
    @property
    def name(self) -> str:
        """Module name."""
        ...
    
    @property
    def description(self) -> str:
        """Module description."""
        ...
    
    @property
    def domain(self) -> str:
        """Domain this module handles (phones, emails, etc)."""
        ...
    
    def is_available(self) -> bool:
        """Check if module is available (API keys configured, etc)."""
        ...
    
    async def scan(self, target: str, **kwargs) -> Any:
        """Perform OSINT scan on target."""
        ...


# ============================================================================
# Provider Protocol
# ============================================================================


class Provider(Protocol):
    """Protocol defining the interface for API providers."""
    
    @property
    def name(self) -> str:
        """Provider name."""
        ...
    
    @property
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key."""
        ...
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        ...
    
    async def get_carrier(self, phone: str) -> CarrierResult | None:
        """Get carrier information for phone number."""
        ...
    
    async def get_owner(self, phone: str) -> OwnerResult | None:
        """Get owner information for phone number."""
        ...
