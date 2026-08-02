"""OSINT modules for See framework."""

from see.modules.base import BaseModule, BaseProvider
from see.modules.phones.domain import PhoneDomain
from see.modules.emails.domain import EmailDomain
from see.modules.usernames.domain import UsernameDomain

__all__ = [
    "BaseModule",
    "BaseProvider",
    "PhoneDomain",
    "EmailDomain",
    "UsernameDomain",
]


def register_all_modules():
    """Register all available modules."""
    from see.core.registry import register_module
    from see.modules.phones.domain import phone_module
    from see.modules.emails.domain import email_module
    from see.modules.usernames.domain import username_module
    
    register_module(phone_module)
    register_module(email_module)
    register_module(username_module)
