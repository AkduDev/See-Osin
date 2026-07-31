"""Disposable email provider for email OSINT."""

from __future__ import annotations

import dns.resolver
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import DisposableResult
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("disposable_provider")

# Known disposable email domains
DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwaway.email", "temp-mail.org", "guerrillamail.com",
    "mailinator.com", "yopmail.com", "trashmail.com", "fakeinbox.com",
    "sharklasers.com", "guerrillamailblock.com", "grr.la", "dispostable.com",
    "maildrop.cc", "tempail.com", "tempmail.net", "temp-mail.io",
    "10minutemail.com", "mailnesia.com", "tempail.net", "temp-mail.com",
    "throwaway.email", "burnermail.io", "harakirimail.com", "mohmal.com",
}

# Known webmail providers
WEBMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
    "aol.com", "icloud.com", "mail.com", "protonmail.com", "proton.me",
    "zoho.com", "yandex.com", "gmx.com", "fastmail.com", "tutanota.com",
}


class DisposableProvider(BaseEmailProvider):
    """
    Provider for checking disposable email addresses.
    
    Checks if an email is from a disposable/temporary email service.
    No API key required.
    """
    
    @property
    def name(self) -> str:
        return "disposable"
    
    @property
    def description(self) -> str:
        return "Disposable email detection"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    @property
    def supports_disposable(self) -> bool:
        return True
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True
    
    async def check_disposable(self, email: str, config: AppConfig) -> DisposableResult | None:
        """Check if email is disposable."""
        logger.info(f"Checking disposable status for {email}")
        
        domain = email.split('@')[-1].lower() if '@' in email else ''
        
        if not domain:
            return None
        
        # Check if domain is in disposable list
        is_disposable = domain in DISPOSABLE_DOMAINS
        
        # Check if domain is webmail
        is_webmail = domain in WEBMAIL_DOMAINS
        
        # Check MX records
        mx_found = False
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_found = len(mx_records) > 0
        except Exception as e:
            logger.debug(f"MX lookup failed for {domain}: {e}")
        
        return DisposableResult(
            source="disposable",
            email=email,
            is_disposable=is_disposable,
            is_webmail=is_webmail,
            provider=domain.split('.')[0],
            mx_found=mx_found,
        )
