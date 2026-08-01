"""Tests for See OSINT framework."""

from __future__ import annotations

import pytest


def test_import():
    """Test that main modules can be imported."""
    from see.core.types import PhoneResult, EmailResult, CarrierResult, OwnerResult
    from see.core.constants import DISPOSABLE_DOMAINS, FREE_EMAIL_PROVIDERS
    from see.core.engine import SeeEngine
    
    assert PhoneResult is not None
    assert EmailResult is not None
    assert CarrierResult is not None
    assert OwnerResult is not None
    assert len(DISPOSABLE_DOMAINS) > 0
    assert len(FREE_EMAIL_PROVIDERS) > 0
