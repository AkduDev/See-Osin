"""OSINT modules for See framework."""

from see.modules.base import BaseModule, BaseProvider
from see.modules.phones.domain import PhoneDomain

__all__ = [
    "BaseModule",
    "BaseProvider",
    "PhoneDomain",
]


def register_all_modules():
    """Register all available modules."""
    from see.core.registry import register_module
    from see.modules.phones.domain import phone_module
    
    register_module(phone_module)
