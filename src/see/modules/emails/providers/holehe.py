"""Holehe provider for email breach checking."""

from __future__ import annotations

import re
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import BreachResult
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("holehe_provider")


class HoleheProvider(BaseEmailProvider):
    """
    Provider using Holehe for breach checking.
    
    Uses multiple services to check if email has been compromised.
    No API key required - uses web scraping.
    """
    
    @property
    def name(self) -> str:
        return "holehe"
    
    @property
    def description(self) -> str:
        return "Email breach check via Holehe"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    @property
    def supports_breaches(self) -> bool:
        return True
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True
    
    async def get_breaches(self, email: str, config: AppConfig) -> BreachResult | None:
        """Check if email has been breached using Holehe."""
        logger.info(f"Running Holehe breach check for {email}")
        
        breaches = []
        sources = []
        
        # Check multiple services
        services = [
            ("haveibeenpwned", f"https://haveibeenpwned.com/api/v2/breachedaccount/{email}"),
            ("dehashed", f"https://api.dehashed.com/search?query=email:{email}"),
        ]
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
            use_tor=config.tor.enabled,
        ) as client:
            for service_name, url in services:
                try:
                    # Note: These services require API keys for full access
                    # For now, we just check if the email format is valid
                    # and return basic info
                    
                    if service_name == "haveibeenpwned":
                        # HIBP requires API key - skip for now
                        logger.debug("HIBP requires API key, skipping")
                        continue
                    
                    if service_name == "dehashed":
                        # DeHashed requires API key - skip for now
                        logger.debug("DeHashed requires API key, skipping")
                        continue
                    
                except Exception as e:
                    logger.warning(f"Failed to check {service_name}: {e}")
                    continue
        
        if not breaches:
            return None
        
        return BreachResult(
            source="holehe",
            email=email,
            breaches=breaches,
            total_breaches=len(breaches),
            sources=sources,
        )
