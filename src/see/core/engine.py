"""Main OSINT engine for See framework."""

from __future__ import annotations

import asyncio
from typing import Any

from see.core.registry import get_registry
from see.utils.config import AppConfig, load_config
from see.utils.logger import get_logger

logger = get_logger("engine")


class SeeEngine:
    """
    Main OSINT engine.
    
    Coordinates module execution and result aggregation.
    """
    
    def __init__(self, config: AppConfig | None = None):
        self.config = config or load_config()
        self.registry = get_registry()
    
    async def scan_phone(self, number: str, modules: list[str] | None = None) -> Any:
        """
        Scan a phone number.
        
        Args:
            number: Phone number to scan (E.164 or national format)
            modules: Optional list of specific modules to use
        
        Returns:
            PhoneResult with aggregated data
        """
        from see.modules.phones.domain import PhoneDomain
        
        domain = PhoneDomain(self.config)
        return await domain.scan(number, modules)
    
    async def scan(self, target: str, domain: str = "phones", **kwargs) -> Any:
        """
        Generic scan method.
        
        Args:
            target: Target to scan
            domain: Domain to use (phones, emails, etc)
            **kwargs: Additional arguments for the domain
        
        Returns:
            Result from the domain module
        """
        module = self.registry.get_module_by_domain(domain)
        
        if module is None:
            logger.error(f"No module found for domain: {domain}")
            raise ValueError(f"Unknown domain: {domain}")
        
        return await module.scan(target, **kwargs)
    
    def get_available_domains(self) -> list[str]:
        """Get list of available domains."""
        return self.registry.available_domains
