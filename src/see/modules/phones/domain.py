"""Phone number OSINT domain."""

from __future__ import annotations

import asyncio
from typing import Any

import phonenumbers as pn

from see.core.types import PhoneResult
from see.modules.base import BaseModule
from see.modules.phones.providers import (
    AbstractProvider,
    DorksProvider,
    NumLookupProvider,
    NumVerifyProvider,
    PhonenumbersProvider,
    SpamProvider,
)
from see.utils.config import AppConfig, load_config
from see.utils.logger import get_logger

logger = get_logger("phone_domain")


class PhoneDomain(BaseModule):
    """
    Phone number OSINT domain.
    
    Coordinates multiple providers to gather intelligence
    about phone numbers worldwide.
    """
    
    def __init__(self, config: AppConfig | None = None):
        self.config = config or load_config()
        self.providers = self._init_providers()
    
    def _init_providers(self) -> list:
        """Initialize available providers."""
        providers = [
            PhonenumbersProvider(),
            NumVerifyProvider(),
            NumLookupProvider(),
            AbstractProvider(),
            SpamProvider(),
            DorksProvider(),
        ]
        
        # Filter to only available providers
        available = [p for p in providers if p.is_available]
        logger.info(f"Loaded {len(available)} phone providers: {[p.name for p in available]}")
        
        return available
    
    @property
    def name(self) -> str:
        return "phones"
    
    @property
    def description(self) -> str:
        return "Phone number OSINT - carrier, owner, social media"
    
    @property
    def domain(self) -> str:
        return "phones"
    
    @property
    def is_available(self) -> bool:
        """Check if at least one provider is available."""
        return len(self.providers) > 0
    
    async def scan(self, number: str, modules: list[str] | None = None) -> PhoneResult:
        """
        Perform complete phone number scan.
        
        Args:
            number: Phone number (E.164, national, or international)
            modules: Optional list of specific providers to use
        
        Returns:
            PhoneResult with all gathered intelligence
        """
        # Parse phone number
        parsed = self._parse_number(number)
        
        # Initialize result
        result = PhoneResult(
            input_number=number,
            e164=parsed.get("e164", ""),
            national=parsed.get("national", ""),
            international=parsed.get("international", ""),
            valid=parsed.get("valid", False),
            possible=parsed.get("possible", False),
            country=parsed.get("country", ""),
            country_code=parsed.get("country_code", ""),
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
    
    async def scan_carrier(self, number: str) -> PhoneResult:
        """Scan only for carrier information."""
        parsed = self._parse_number(number)
        
        result = PhoneResult(
            input_number=number,
            e164=parsed.get("e164", ""),
            valid=parsed.get("valid", False),
            country=parsed.get("country", ""),
            country_code=parsed.get("country_code", ""),
        )
        
        # Only run providers that support carrier
        tasks = []
        for provider in self.providers:
            if provider.supports_carrier:
                tasks.append(self._run_provider_carrier(provider, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return result
    
    async def scan_owner(self, number: str) -> PhoneResult:
        """Scan only for owner information."""
        parsed = self._parse_number(number)
        
        result = PhoneResult(
            input_number=number,
            e164=parsed.get("e164", ""),
            valid=parsed.get("valid", False),
            country=parsed.get("country", ""),
            country_code=parsed.get("country_code", ""),
        )
        
        # Only run providers that support owner
        tasks = []
        for provider in self.providers:
            if provider.supports_owner:
                tasks.append(self._run_provider_owner(provider, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return result
    
    async def scan_spam(self, number: str) -> PhoneResult:
        """Scan only for spam/scam reports and investigation links."""
        parsed = self._parse_number(number)
        
        result = PhoneResult(
            input_number=number,
            e164=parsed.get("e164", ""),
            valid=parsed.get("valid", False),
            country=parsed.get("country", ""),
            country_code=parsed.get("country_code", ""),
        )
        
        tasks = []
        for provider in self.providers:
            if provider.supports_spam:
                tasks.append(self._run_provider_spam(provider, result))
            elif provider.supports_search_links:
                tasks.append(self._run_provider_links(provider, result))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return result
    
    def _parse_number(self, number: str) -> dict[str, Any]:
        """Parse phone number using phonenumbers library."""
        try:
            # Try parsing with default region
            parsed = pn.parse(number, None)
            
            if not pn.is_valid_number(parsed):
                # Try with common regions
                for region in ["US", "GB", "ES", "MX", "AR", "CO"]:
                    parsed = pn.parse(number, region)
                    if pn.is_valid_number(parsed):
                        break
            
            return {
                "e164": pn.format_number(parsed, pn.PhoneNumberFormat.E164),
                "national": pn.format_number(parsed, pn.PhoneNumberFormat.NATIONAL),
                "international": pn.format_number(parsed, pn.PhoneNumberFormat.INTERNATIONAL),
                "valid": pn.is_valid_number(parsed),
                "possible": pn.is_possible_number(parsed),
                "country": pn.region_code_for_number(parsed) or "",
                "country_code": str(parsed.country_code),
                "number_type": pn.number_type(parsed),
            }
        except Exception as e:
            logger.error(f"Failed to parse number {number}: {e}")
            return {
                "e164": number,
                "national": number,
                "international": number,
                "valid": False,
                "possible": False,
                "country": "",
                "country_code": "",
            }
    
    async def _run_provider(self, provider: Any, result: PhoneResult) -> None:
        """Run a single provider and update result."""
        try:
            logger.info(f"Running provider: {provider.name}")
            
            # Get carrier
            if provider.supports_carrier:
                carrier = await provider.get_carrier(result.e164, self.config)
                if carrier and not result.carrier:
                    result.carrier = carrier
                    result.modules_used.append(provider.name)
            
            # Get owner
            if provider.supports_owner:
                owner = await provider.get_owner(result.e164, self.config)
                if owner and not result.owner:
                    result.owner = owner
                    if provider.name not in result.modules_used:
                        result.modules_used.append(provider.name)
            
            # Spam reports
            if provider.supports_spam:
                spam = await provider.get_spam(result.e164, self.config)
                if spam and not result.spam:
                    result.spam = spam
                    if provider.name not in result.modules_used:
                        result.modules_used.append(provider.name)
            
            # Investigation links (dorks, lookup sites)
            if provider.supports_search_links:
                links = await provider.get_search_links(result.e164, self.config)
                if links:
                    result.search_links.extend(links)
                    if provider.name not in result.modules_used:
                        result.modules_used.append(provider.name)
            
            logger.info(f"Provider {provider.name} completed")
            
        except Exception as e:
            error_msg = f"Provider {provider.name} failed: {e!s}"
            logger.error(error_msg)
            result.errors.append(error_msg)
    
    async def _run_provider_carrier(self, provider: Any, result: PhoneResult) -> None:
        """Run provider for carrier lookup only."""
        try:
            carrier = await provider.get_carrier(result.e164, self.config)
            if carrier and not result.carrier:
                result.carrier = carrier
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {e!s}")
    
    async def _run_provider_owner(self, provider: Any, result: PhoneResult) -> None:
        """Run provider for owner lookup only."""
        try:
            owner = await provider.get_owner(result.e164, self.config)
            if owner and not result.owner:
                result.owner = owner
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {e!s}")
    
    async def _run_provider_spam(self, provider: Any, result: PhoneResult) -> None:
        """Run provider for spam report lookup only."""
        try:
            spam = await provider.get_spam(result.e164, self.config)
            if spam and not result.spam:
                result.spam = spam
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {e!s}")
    
    async def _run_provider_links(self, provider: Any, result: PhoneResult) -> None:
        """Run provider for investigation links only."""
        try:
            links = await provider.get_search_links(result.e164, self.config)
            if links:
                result.search_links.extend(links)
                result.modules_used.append(provider.name)
        except Exception as e:
            result.errors.append(f"{provider.name}: {e!s}")


# Module instance for registration
phone_module = PhoneDomain()
