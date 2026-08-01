"""Gravatar provider for email OSINT."""

from __future__ import annotations

import hashlib
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import SocialResult
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("gravatar_provider")

GRAVATAR_BASE_URL = "https://gravatar.com"


class GravatarProvider(BaseEmailProvider):
    """
    Provider for Gravatar profile lookup.
    
    Retrieves profile information from Gravatar using email hash.
    No API key required.
    """
    
    @property
    def name(self) -> str:
        return "gravatar"
    
    @property
    def description(self) -> str:
        return "Gravatar profile lookup"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    @property
    def supports_social(self) -> bool:
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True
    
    async def get_social_profiles(self, email: str, config: AppConfig) -> list[SocialResult]:
        """Get Gravatar profile for email."""
        logger.info(f"Checking Gravatar for {email}")
        
        profiles = []
        
        # Generate email hash
        email_hash = self._md5(email.lower().strip())
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
            use_tor=config.tor.enabled,
        ) as client:
            # Get profile info
            profile = await self._get_profile(client, email_hash, email)
            if profile:
                profiles.append(profile)
        
        return profiles
    
    async def _get_profile(self, client: HTTPClient, email_hash: str, email: str) -> SocialResult | None:
        """Get Gravatar profile."""
        try:
            # Try JSON API
            url = f"{GRAVATAR_BASE_URL}/{email_hash}.json"
            data = await client.get(url)
            
            if data and "entry" in data:
                entry = data["entry"][0]
                
                # Get display name
                display_name = entry.get("displayName", "")
                
                # Get profile URL
                profile_url = entry.get("profileUrl", f"{GRAVATAR_BASE_URL}/{email_hash}")
                
                # Get photos
                photos = entry.get("photos", [])
                photo_url = photos[0].get("value", "") if photos else ""
                
                # Get accounts (social links)
                accounts = entry.get("accounts", [])
                
                return SocialResult(
                    source="gravatar",
                    platform="gravatar",
                    username=email.split('@')[0],
                    name=display_name,
                    url=profile_url,
                    found=True,
                    status="found",
                )
            
            # Check if avatar exists
            avatar_url = f"{GRAVATAR_BASE_URL}/{email_hash}.jpg?d=404"
            response = await client.get(avatar_url)
            
            # If we get a response, the email has a Gravatar
            if response:
                return SocialResult(
                    source="gravatar",
                    platform="gravatar",
                    username=email.split('@')[0],
                    name="",
                    url=f"{GRAVATAR_BASE_URL}/{email_hash}",
                    found=True,
                    status="found",
                )
            
        except Exception as e:
            logger.debug(f"Gravatar check failed: {e}")
        
        return None
    
    def _md5(self, text: str) -> str:
        """Generate MD5 hash for Gravatar."""
        return hashlib.md5(text.encode()).hexdigest()
