"""Module registry for dynamic module loading."""

from __future__ import annotations

from typing import Any

from see.utils.logger import get_logger

logger = get_logger("registry")


class ModuleRegistry:
    """
    Registry for OSINT modules.
    
    Modules are registered dynamically and can be loaded
    based on the domain or command requested.
    """
    
    def __init__(self):
        self._modules: dict[str, Any] = {}
        self._domains: dict[str, str] = {}  # domain -> module_name
    
    def register(self, module: Any) -> None:
        """
        Register a module.
        
        Args:
            module: Module instance with name and domain properties
        """
        name = module.name
        domain = module.domain
        
        self._modules[name] = module
        self._domains[domain] = name
        
        logger.info(f"Registered module: {name} (domain: {domain})")
    
    def get_module(self, name: str) -> Any | None:
        """Get module by name."""
        return self._modules.get(name)
    
    def get_module_by_domain(self, domain: str) -> Any | None:
        """Get module by domain."""
        module_name = self._domains.get(domain)
        if module_name:
            return self._modules.get(module_name)
        return None
    
    @property
    def available_modules(self) -> list[str]:
        """List of available module names."""
        return list(self._modules.keys())
    
    @property
    def available_domains(self) -> list[str]:
        """List of available domains."""
        return list(self._domains.keys())
    
    def is_domain_available(self, domain: str) -> bool:
        """Check if a domain has a registered module."""
        return domain in self._domains


# Global registry instance
_registry: ModuleRegistry | None = None


def get_registry() -> ModuleRegistry:
    """Get the global registry instance."""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry


def register_module(module: Any) -> None:
    """Register a module in the global registry."""
    get_registry().register(module)
