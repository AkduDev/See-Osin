"""Social email provider for email OSINT."""

from __future__ import annotations

from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import SocialResult
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("social_email_provider")


class SocialEmailProvider(BaseEmailProvider):
    """
    Provider for checking social media profiles by email.
    
    Uses various techniques to find social media accounts
    associated with an email address.
    No API key required.
    """
    
    @property
    def name(self) -> str:
        return "social_email"
    
    @property
    def description(self) -> str:
        return "Social media profiles lookup by email"
    
    @property
    def requires_api_key(self) -> bool:
        return False
    
    @property
    def supports_social(self) -> bool:
        return True
    
    def is_available(self) -> bool:
        """Check if provider is available."""
        return True
    
    async def get_social_profiles(self, email: str, config: AppConfig) -> list[SocialResult]:
        """Find social media profiles for email."""
        logger.info(f"Searching social profiles for {email}")
        
        profiles = []
        
        # Services that can be checked by email
        services = [
            ("gravatar", f"https://gravatar.com/{self._md5(email)}.json"),
            ("github", f"https://api.github.com/search/users?q={email}+in:email"),
        ]
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
            use_tor=config.tor.enabled,
        ) as client:
            for service_name, url in services:
                try:
                    if service_name == "gravatar":
                        profile = await self._check_gravatar(client, email, url)
                        if profile:
                            profiles.append(profile)
                    
                    elif service_name == "github":
                        profile = await self._check_github(client, email, url)
                        if profile:
                            profiles.append(profile)
                    
                except Exception as e:
                    logger.warning(f"Failed to check {service_name}: {e}")
                    continue
        
        return profiles
    
    async def _check_gravatar(self, client: HTTPClient, email: str, url: str) -> SocialResult | None:
        """Check Gravatar for profile."""
        try:
            data = await client.get(url)
            
            if data and "entry" in data:
                entry = data["entry"][0]
                return SocialResult(
                    source="social_email",
                    platform="gravatar",
                    username=email.split('@')[0],
                    name=entry.get("displayName", ""),
                    url=entry.get("profileUrl", ""),
                    found=True,
                    status="found",
                )
        except Exception as e:
            logger.debug(f"Gravatar check failed: {e}")
        
        return None
    
    async def _check_github(self, client: HTTPClient, email: str, url: str) -> SocialResult | None:
        """Check GitHub for user by email."""
        try:
            data = await client.get(url)
            
            if data and "items" in data and len(data["items"]) > 0:
                user = data["items"][0]
                return SocialResult(
                    source="social_email",
                    platform="github",
                    username=user.get("login", ""),
                    name=user.get("name", ""),
                    url=user.get("html_url", ""),
                    found=True,
                    status="found",
                )
        except Exception as e:
            logger.debug(f"GitHub check failed: {e}")
        
        return None
    
    def _md5(self, text: str) -> str:
        """Generate MD5 hash for Gravatar."""
        import hashlib
        return hashlib.md5(text.lower().strip().encode()).hexdigest()
