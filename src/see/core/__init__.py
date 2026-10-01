"""Core components for See OSINT framework."""

from see.core.engine import SeeEngine
from see.core.registry import ModuleRegistry, get_registry, register_module
from see.core.types import (
    BaseResult,
    BreachResult,
    CarrierResult,
    DisposableResult,
    EmailResult,
    OwnerResult,
    PhoneResult,
    SocialResult,
    UsernameResult,
)

__all__ = [
    "BaseResult",
    "BreachResult",
    "CarrierResult",
    "DisposableResult",
    "EmailResult",
    "ModuleRegistry",
    "OwnerResult",
    "PhoneResult",
    "SeeEngine",
    "SocialResult",
    "UsernameResult",
    "get_registry",
    "register_module",
]
