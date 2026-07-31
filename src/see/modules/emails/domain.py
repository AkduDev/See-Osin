"""Email OSINT domain."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from see.core.types import EmailResult, BreachResult, DisposableResult, SocialResult
from see.modules.base import BaseModule
from see.modules.emails.providers import (
    HoleheProvider,
    DisposableProvider,
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
            HoleheProvider(),
            DisposableProvider(),
            SocialEmailProvider(),
        ]
        
        # Filter to only available providers
        available = [p for p in providers if p.is_available()]
        logger.info(f"Loaded {len(available)} email providers: {[p.name for p in available]}")
        
        return available
    
    @property
    def name(self) -> str:
        return "emails"
    
    @property
    def description(self) -> str:
        return "Email OSINT - breaches, disposable, social media"
    
    @property
    def domain(self) -> str:
        return "emails"
    
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
    
    async def _run_provider(self, provider: Any, result: EmailResult) -> None:
        """Run a single provider and update result."""
        try:
            logger.info(f"Running provider: {provider.name}")
            
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


# Module instance for registration
email_module = EmailDomain()
