"""Hashing utilities for See OSINT tool."""

from __future__ import annotations

import hashlib


def md5(text: str) -> str:
    """Generate MD5 hash for text (used for Gravatar)."""
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def sha256(text: str) -> str:
    """Generate SHA256 hash for text."""
    return hashlib.sha256(text.encode()).hexdigest()
