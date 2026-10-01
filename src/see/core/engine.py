"""Main OSINT engine for See framework."""

from __future__ import annotations

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
        self._ensure_modules_registered()
    
    @staticmethod
    def _ensure_modules_registered() -> None:
        """Register domain modules on first use (CLI never calls it explicitly)."""
        from see.core.registry import get_registry as _get_registry

        if not _get_registry().available_domains:
            from see.modules import register_all_modules

            register_all_modules()
    
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
    
    async def scan_username(
        self,
        username: str,
        modules: list[str] | None = None,
        use_tor: bool | None = None,
        use_cache: bool = True,
    ) -> Any:
        """
        Search a username across social media platforms.
        
        Args:
            username: Username to search
            modules: Optional list of specific providers to use
            use_tor: Optional override to route requests through Tor.
                When None, the configured value is used.
            use_cache: Whether to serve repeat scans from cache.
        
        Returns:
            UsernameResult with found profiles
        """
        from see.modules.usernames.domain import UsernameDomain
        
        domain = UsernameDomain(self.config)
        return await domain.scan(username, modules, use_tor=use_tor, use_cache=use_cache)
    
    async def scan_email(self, email: str, modules: list[str] | None = None) -> Any:
        """
        Scan an email address.

        Args:
            email: Email address to scan
            modules: Optional list of specific providers to use

        Returns:
            EmailResult with aggregated data
        """
        from see.modules.emails.domain import EmailDomain

        domain = EmailDomain(self.config)
        return await domain.scan(email, modules)
    
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
        self._ensure_modules_registered()
        module = self.registry.get_module_by_domain(domain)
        
        if module is None:
            logger.error(f"No module found for domain: {domain}")
            raise ValueError(f"Unknown domain: {domain}")
        
        return await module.scan(target, **kwargs)
    
    def get_available_domains(self) -> list[str]:
        """Get list of available domains."""
        self._ensure_modules_registered()
        return self.registry.available_domains
