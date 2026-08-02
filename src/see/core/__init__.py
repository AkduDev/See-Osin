"""Core components for See OSINT framework."""

from see.core.types import (
    BaseResult,
    CarrierResult,
    OwnerResult,
    SocialResult,
    BreachResult,
    DisposableResult,
    EmailResult,
    PhoneResult,
    UsernameResult,
)
from see.core.registry import ModuleRegistry, get_registry, register_module
from see.core.engine import SeeEngine

__all__ = [
    # Types
    "BaseResult",
    "CarrierResult",
    "OwnerResult",
    "SocialResult",
    "BreachResult",
    "DisposableResult",
    "EmailResult",
    "PhoneResult",
    "UsernameResult",
    # Registry
    "ModuleRegistry",
    "get_registry",
    "register_module",
    # Engine
    "SeeEngine",
]
