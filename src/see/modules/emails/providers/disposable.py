"""Disposable email provider for email OSINT."""

from __future__ import annotations

import asyncio

import dns.resolver

from see.core.constants import DISPOSABLE_DOMAINS, WEBMAIL_DOMAINS
from see.core.types import DisposableResult
from see.modules.emails.providers.base import BaseEmailProvider
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("disposable_provider")


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
    
    @property
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
        
        # Check MX records (run in thread to avoid blocking)
        mx_found = False
        try:
            def check_mx():
                return dns.resolver.resolve(domain, 'MX')
            mx_records = await asyncio.to_thread(check_mx)
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
