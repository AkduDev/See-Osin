"""Email OSINT domain."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from see.core.types import EmailResult
from see.modules.base import BaseModule
from see.modules.emails.providers import (
    DeHashedProvider,
    DisposableProvider,
    EmailIntelligenceProvider,
    GravatarProvider,
    HIBPProvider,
    HoleheProvider,
    HunterProvider,
    ReverseEmailProvider,
    SMTPProvider,
    SocialEmailProvider,
)
from see.utils.config import AppConfig, load_config
from see.utils.logger import get_logger

logger = get_logger("email_domain")

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
}


class EmailDomain(BaseModule):
    """
    Email OSINT domain.
    
    Coordinates multiple providers to gather intelligence
    about email addresses.
    """
    
    def __init__(self, config: AppConfig | None = None):
        self.config = config or load_config()
        self.providers = self._init_providers()
    
    def _init_providers(self) -> list:
        """Initialize available providers."""
        providers = [
            HIBPProvider(self.config),
            HoleheProvider(),
            DisposableProvider(),
            SocialEmailProvider(),
            EmailIntelligenceProvider(),
            ReverseEmailProvider(),
            HunterProvider(self.config),
            DeHashedProvider(self.config),
            SMTPProvider(),
            GravatarProvider(),
        ]
        
        # Filter to only available providers
        available = [p for p in providers if p.is_available]
        logger.info(f"Loaded {len(available)} email providers: {[p.name for p in available]}")
        
        return available
    
    @property
    def name(self) -> str:
        return "emails"
    
    @property
    def description(self) -> str:
        return "Email OSINT - breaches, disposable, social media, intelligence"
    
    @property
    def domain(self) -> str:
        return "emails"
    
    @property
    def is_available(self) -> bool:
        """Check if at least one provider is available."""
        return len(self.providers) > 0
    
    async def scan(self, email: str, modules: list[str] | None = None) -> EmailResult:
        """
        Perform complete email scan.
        
        Args:
            email: Email address to investigate
            modules: Optional list of specific providers to use
        
        Returns:
            EmailResult with all gathered intelligence
        """
        # Validate and parse email
        parsed = self._parse_email(email)
        
        # Initialize result
        result = EmailResult(
            input_email=email,
            valid=parsed.get("valid", False),
            domain=parsed.get("domain", ""),
            provider=parsed.get("provider", ""),
            is_free=parsed.get("is_free", False),
            is_disposable=parsed.get("is_disposable", False),
        )
        
        # Filter providers if specific modules requested
        providers = self.providers
        if modules:
            providers = [p for p in providers if p.name in modules]
        
        # Run all providers in parallel
        tasks = []
        for provider in providers:
            tasks.append(self._run_provider(provider, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Gather additional intelligence
        await self._gather_intelligence(email, result)
        
        return result
    
    async def scan_breaches(self, email: str) -> EmailResult:
        """Scan only for breach information."""
        parsed = self._parse_email(email)
        
        result = EmailResult(
            input_email=email,
            valid=parsed.get("valid", False),
            domain=parsed.get("domain", ""),
        )
        
        # Only run providers that support breaches
        tasks = []
        for provider in self.providers:
            if provider.supports_breaches:
                tasks.append(self._run_provider_breaches(provider, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return result
    
    async def scan_social(self, email: str) -> EmailResult:
        """Scan only for social media profiles."""
        parsed = self._parse_email(email)
        
        result = EmailResult(
            input_email=email,
            valid=parsed.get("valid", False),
            domain=parsed.get("domain", ""),
        )
        
        # Only run providers that support social
        tasks = []
        for provider in self.providers:
            if provider.supports_social:
                tasks.append(self._run_provider_social(provider, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return result
    
    async def scan_disposable(self, email: str) -> EmailResult:
        """Check if email is disposable."""
        parsed = self._parse_email(email)
        
        result = EmailResult(
            input_email=email,
            valid=parsed.get("valid", False),
            domain=parsed.get("domain", ""),
            is_disposable=parsed.get("is_disposable", False),
        )
        
        # Only run providers that support disposable check
        tasks = []
        for provider in self.providers:
            if provider.supports_disposable:
                tasks.append(self._run_provider_disposable(provider, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return result
    
    async def scan_verify(self, email: str) -> EmailResult:
        """Verify deliverability of an email via SMTP (RCPT TO, no mail sent)."""
        parsed = self._parse_email(email)
        
        result = EmailResult(
            input_email=email,
            valid=parsed.get("valid", False),
            domain=parsed.get("domain", ""),
        )
        
        for provider in self.providers:
            if provider.supports_verification:
                await self._run_provider_verify(provider, result)
        
        return result
    
    async def scan_intelligence(self, email: str) -> dict[str, Any]:
        """Gather email intelligence (DNS, MX, SPF, DKIM, DMARC)."""
        for provider in self.providers:
            if hasattr(provider, 'get_email_intelligence'):
                return await provider.get_email_intelligence(email, self.config)
        return {}
    
    def _parse_email(self, email: str) -> dict[str, Any]:
        """Parse and validate email address."""
        try:
            # Basic regex validation
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            is_valid = bool(re.match(email_regex, email))
            
            # Extract domain
            domain = email.split('@')[-1].lower() if '@' in email else ''
            
            # Check if free provider
            is_free = domain in FREE_EMAIL_PROVIDERS
            
            # Check if disposable
            is_disposable = domain in DISPOSABLE_DOMAINS
            
            # Get provider name
            provider = domain.split('.')[0] if domain else ''
            
            return {
                "valid": is_valid,
                "domain": domain,
                "provider": provider,
                "is_free": is_free,
                "is_disposable": is_disposable,
            }
        except Exception as e:
            logger.error(f"Failed to parse email {email}: {e}")
            return {
                "valid": False,
                "domain": "",
                "provider": "",
                "is_free": False,
                "is_disposable": False,
            }
    
    async def _gather_intelligence(self, email: str, result: EmailResult) -> None:
        """Gather additional email intelligence."""
        try:
            # Get email intelligence
            intelligence = await self.scan_intelligence(email)
            
            if intelligence:
                # Add intelligence to result
                if intelligence.get("mx_records"):
                    result.mx_records = [mx.get("exchange", "") for mx in intelligence["mx_records"]]
                
                if intelligence.get("provider_info"):
                    result.provider = intelligence["provider_info"].get("name", result.provider)
                
                # Add intelligence to modules used
                if "email_intelligence" not in result.modules_used:
                    result.modules_used.append("email_intelligence")
        
        except Exception as e:
            logger.error(f"Failed to gather intelligence: {e}")
            result.errors.append(f"Intelligence gathering failed: {str(e)}")
    
    async def _run_provider(self, provider: Any, result: EmailResult) -> None:
        """Run a single provider and update result."""
        try:
            logger.info(f"Running provider: {provider.name}")
            
            # Hunter.io - Get email info
            if provider.name == "hunter":
                info = await provider.get_email_info(result.input_email, self.config)
                if info:
                    if info.get("name"):
                        result.name = info["name"]
                    if info.get("phone"):
                        result.phone_numbers.append(info["phone"])
                    if info.get("company"):
                        result.company = info["company"]
                    if info.get("job_title"):
                        result.job_title = info["job_title"]
                    if info.get("linkedin"):
                        result.linkedin = info["linkedin"]
                    if info.get("location"):
                        result.location = info["location"]
                    
                    # Get social profiles
                    social = await provider.get_social_profiles(result.input_email, self.config)
                    if social:
                        result.social_profiles.extend(social)
                    
                    if provider.name not in result.modules_used:
                        result.modules_used.append(provider.name)
            
            # DeHashed - Get breach data
            elif provider.name == "dehashed":
                data = await provider.get_breach_data(result.input_email, self.config)
                if data:
                    # Breaches
                    if data.get("breaches"):
                        from see.core.types import BreachResult
                        result.breaches = BreachResult(
                            source="dehashed",
                            email=result.input_email,
                            breaches=data["breaches"],
                            total_breaches=len(data["breaches"]),
                            sources=data.get("sources", []),
                        )
                    
                    # Phone numbers
                    if data.get("phone_numbers"):
                        result.phone_numbers.extend(data["phone_numbers"])
                    
                    # Names
                    if data.get("names") and not result.name:
                        result.name = data["names"][0]
                    
                    # Social profiles
                    social = await provider.get_social_profiles(result.input_email, self.config)
                    if social:
                        result.social_profiles.extend(social)
                    
                    if provider.name not in result.modules_used:
                        result.modules_used.append(provider.name)
            
            # Other providers
            else:
                # Get breaches
                if provider.supports_breaches:
                    breaches = await provider.get_breaches(result.input_email, self.config)
                    if breaches and not result.breaches:
                        result.breaches = breaches
                        result.modules_used.append(provider.name)
                
                # Check disposable
                if provider.supports_disposable:
                    disposable = await provider.check_disposable(result.input_email, self.config)
                    if disposable:
                        result.disposable = disposable
                        result.is_disposable = disposable.is_disposable
                        result.is_webmail = disposable.is_webmail
                        if provider.name not in result.modules_used:
                            result.modules_used.append(provider.name)
                
                # Get social profiles
                if provider.supports_social:
                    social = await provider.get_social_profiles(result.input_email, self.config)
                    if social:
                        result.social_profiles.extend(social)
                        if provider.name not in result.modules_used:
                            result.modules_used.append(provider.name)
                
                # Verify deliverability (SMTP)
                if provider.supports_verification:
                    verify = await provider.verify_deliverability(result.input_email, self.config)
                    if verify:
                        result.deliverability = verify
                        if provider.name not in result.modules_used:
                            result.modules_used.append(provider.name)
            
            logger.info(f"Provider {provider.name} completed")
            
        except Exception as e:
            error_msg = f"Provider {provider.name} failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
    
    async def _run_provider_breaches(self, provider: Any, result: EmailResult) -> None:
        """Run provider for breach lookup only."""
        try:
            breaches = await provider.get_breaches(result.input_email, self.config)
            if breaches and not result.breaches:
                result.breaches = breaches
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {str(e)}")
    
    async def _run_provider_social(self, provider: Any, result: EmailResult) -> None:
        """Run provider for social media lookup only."""
        try:
            social = await provider.get_social_profiles(result.input_email, self.config)
            if social:
                result.social_profiles.extend(social)
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {str(e)}")
    
    async def _run_provider_disposable(self, provider: Any, result: EmailResult) -> None:
        """Run provider for disposable check only."""
        try:
            disposable = await provider.check_disposable(result.input_email, self.config)
            if disposable:
                result.disposable = disposable
                result.is_disposable = disposable.is_disposable
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {str(e)}")
    
    async def _run_provider_verify(self, provider: Any, result: EmailResult) -> None:
        """Run provider for SMTP deliverability verification only."""
        try:
            verify = await provider.verify_deliverability(result.input_email, self.config)
            if verify:
                result.deliverability = verify
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {str(e)}")


# Module instance for registration
email_module = EmailDomain()
