"""Tests for See OSINT framework."""

from __future__ import annotations

try:
    import pytest
except ImportError:  # pragma: no cover - allows running without pytest installed
    pytest = None


def test_import():
    """Test that main modules can be imported."""
    from see.core.constants import DISPOSABLE_DOMAINS, FREE_EMAIL_PROVIDERS
    from see.core.types import (
        CarrierResult,
        EmailResult,
        OwnerResult,
        PhoneResult,
        UsernameResult,
    )

    assert PhoneResult is not None
    assert EmailResult is not None
    assert CarrierResult is not None
    assert OwnerResult is not None
    assert UsernameResult is not None
    assert len(DISPOSABLE_DOMAINS) > 0
    assert len(FREE_EMAIL_PROVIDERS) > 0


def test_username_module_registered():
    """Test that the usernames domain is registered."""
    from see.core.registry import get_registry
    from see.modules import register_all_modules

    register_all_modules()
    registry = get_registry()
    assert "usernames" in registry.available_domains


def test_username_platforms_configured():
    """Test that the sherlock-like provider has platforms configured."""
    from see.modules.usernames.providers.platforms import PLATFORMS

    assert len(PLATFORMS) > 20

    methods = {p["method"] for p in PLATFORMS}
    assert methods <= {"status", "text", "manual"}

    # Every platform must have a URL template with the {username} placeholder
    for platform in PLATFORMS:
        assert "{username}" in platform["url"]
