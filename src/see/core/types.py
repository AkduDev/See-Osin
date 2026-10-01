"""Shared types for See OSINT framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

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
class BreachResult(BaseResult):
    """Result from breach lookup."""
    
    email: str = ""
    breaches: list[dict[str, Any]] = field(default_factory=list)
    total_breaches: int = 0
    sources: list[str] = field(default_factory=list)


@dataclass
class DisposableResult(BaseResult):
    """Result from disposable email check."""
    
    email: str = ""
    is_disposable: bool = False
    is_webmail: bool = False
    provider: str = ""
    mx_found: bool = False


@dataclass
class SpamResult(BaseResult):
    """Result from phone spam/report lookup (e.g. Should I Answer)."""

    number: str = ""
    url: str = ""
    rating: str = ""  # negative, positive, neutral, unknown
    total_reports: int = 0
    positive: int = 0
    negative: int = 0
    categories: list[str] = field(default_factory=list)


@dataclass
class EmailResult:
    """Aggregated result for email OSINT."""
    
    input_email: str
    valid: bool = False
    is_disposable: bool = False
    is_webmail: bool = False
    is_free: bool = False
    
    # Domain info
    domain: str = ""
    provider: str = ""
    mx_records: list[str] = field(default_factory=list)
    
    # Personal info
    name: str = ""
    phone_numbers: list[str] = field(default_factory=list)
    location: str = ""
    
    # Work info
    company: str = ""
    job_title: str = ""
    linkedin: str = ""
    
    # Results from providers
    breaches: BreachResult | None = None
    disposable: DisposableResult | None = None
    social_profiles: list[SocialResult] = field(default_factory=list)

    # SMTP deliverability (see SMTPProvider.verify_deliverability)
    deliverability: dict[str, Any] | None = None
    
    # Metadata
    modules_used: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    query_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "input": self.input_email,
            "query_time": self.query_time,
            "modules_used": self.modules_used,
            "errors": self.errors,
            "email": {
                "valid": self.valid,
                "is_disposable": self.is_disposable,
                "is_webmail": self.is_webmail,
                "is_free": self.is_free,
                "domain": self.domain,
                "provider": self.provider,
                "mx_records": self.mx_records,
            },
            "personal": {
                "name": self.name,
                "phone_numbers": self.phone_numbers,
                "location": self.location,
            },
            "work": {
                "company": self.company,
                "job_title": self.job_title,
                "linkedin": self.linkedin,
            },
        }
        
        if self.breaches:
            result["breaches"] = {
                "total": self.breaches.total_breaches,
                "sources": self.breaches.sources,
                "breaches": self.breaches.breaches,
            }
        
        if self.disposable:
            result["disposable"] = {
                "is_disposable": self.disposable.is_disposable,
                "is_webmail": self.disposable.is_webmail,
                "provider": self.disposable.provider,
                "mx_found": self.disposable.mx_found,
            }

        if self.deliverability:
            result["deliverability"] = self.deliverability
        
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
    spam: SpamResult | None = None
    social_profiles: list[SocialResult] = field(default_factory=list)
    # Investigation links (Google dorks, spam DBs) - manual follow-up
    search_links: list[SocialResult] = field(default_factory=list)
    
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
        
        if self.spam:
            result["spam"] = {
                "rating": self.spam.rating,
                "total_reports": self.spam.total_reports,
                "positive": self.spam.positive,
                "negative": self.spam.negative,
                "categories": self.spam.categories,
                "url": self.spam.url,
                "source": self.spam.source,
            }
        
        if self.search_links:
            result["search_links"] = [
                {
                    "platform": p.platform,
                    "url": p.url,
                    "status": p.status,
                }
                for p in self.search_links
            ]
        
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


@dataclass
class UsernameResult(BaseResult):
    """Aggregated result for username OSINT (social media search)."""

    input_username: str = ""

    # Results
    profiles: list[SocialResult] = field(default_factory=list)
    platforms_checked: int = 0
    found_count: int = 0
    not_found_count: int = 0

    # Metadata
    modules_used: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    query_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "input": self.input_username,
            "query_time": self.query_time,
            "modules_used": self.modules_used,
            "errors": self.errors,
            "username": {
                "platforms_checked": self.platforms_checked,
                "found_count": self.found_count,
                "not_found_count": self.not_found_count,
            },
            "profiles": [
                {
                    "platform": p.platform,
                    "username": p.username,
                    "name": p.name,
                    "url": p.url,
                    "found": p.found,
                    "status": p.status,
                }
                for p in self.profiles
            ],
        }

        return result
