"""Enhanced social media provider for email OSINT."""

from __future__ import annotations

import hashlib
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import SocialResult
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("social_email_provider")

# Platforms that can be checked by email
PLATFORMS = {
    "gravatar": {
        "url": "https://gravatar.com/{hash}.json",
        "type": "md5",
    },
    "github": {
        "url": "https://api.github.com/search/users?q={email}+in:email",
        "type": "email",
    },
    "twitter": {
        "url": "https://api.twitter.com/2/users/by?email={email}",
        "type": "email",
        "requires_auth": True,
    },
    "linkedin": {
        "url": "https://www.linkedin.com/in/{email}",
        "type": "email",
        "check_manually": True,
    },
    "instagram": {
        "url": "https://www.instagram.com/{username}/",
        "type": "username_from_email",
        "check_manually": True,
    },
    "facebook": {
        "url": "https://www.facebook.com/{email}",
        "type": "email",
        "check_manually": True,
    },
    "tiktok": {
        "url": "https://www.tiktok.com/@{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "pinterest": {
        "url": "https://www.pinterest.com/{username}/",
        "type": "username_from_email",
        "check_manually": True,
    },
    "reddit": {
        "url": "https://www.reddit.com/user/{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "snapchat": {
        "url": "https://www.snapchat.com/add/{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "youtube": {
        "url": "https://www.youtube.com/@{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "spotify": {
        "url": "https://open.spotify.com/user/{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "steam": {
        "url": "https://steamcommunity.com/id/{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "discord": {
        "url": "https://discord.com/users/{user_id}",
        "type": "user_id",
        "check_manually": True,
    },
    "telegram": {
        "url": "https://t.me/{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "twitch": {
        "url": "https://www.twitch.tv/{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "medium": {
        "url": "https://medium.com/@{username}",
        "type": "username_from_email",
        "check_manually": True,
    },
    "keybase": {
        "url": "https://keybase.io/_/api/1.0/user/lookup.json?email={email}",
        "type": "email",
    },
    "skype": {
        "url": "https://www.skype.com/en/",
        "type": "check_manually",
        "check_manually": True,
    },
}


class SocialEmailProvider(BaseEmailProvider):
    """
    Enhanced provider for checking social media profiles by email.
    
    Uses multiple techniques to find social media accounts
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
        username = email.split('@')[0]
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
            use_tor=config.tor.enabled,
        ) as client:
            # Check each platform
            for platform_name, platform_info in PLATFORMS.items():
                try:
                    if platform_info.get("requires_auth"):
                        # Skip platforms that require authentication
                        continue
                    
                    if platform_info.get("check_manually"):
                        # Add manual check suggestion
                        profiles.append(SocialResult(
                            source="social_email",
                            platform=platform_name,
                            username=username,
                            name="",
                            url=platform_info["url"].format(
                                email=email,
                                username=username,
                                hash=self._md5(email),
                            ),
                            found=False,
                            status="check_manually",
                        ))
                        continue
                    
                    # Auto-check platforms
                    profile = await self._check_platform(
                        client, email, username, platform_name, platform_info
                    )
                    if profile:
                        profiles.append(profile)
                    
                except Exception as e:
                    logger.warning(f"Failed to check {platform_name}: {e}")
                    continue
        
        return profiles
    
    async def _check_platform(
        self,
        client: HTTPClient,
        email: str,
        username: str,
        platform_name: str,
        platform_info: dict,
    ) -> SocialResult | None:
        """Check a specific platform."""
        try:
            url = platform_info["url"].format(
                email=email,
                username=username,
                hash=self._md5(email),
            )
            
            if platform_name == "gravatar":
                return await self._check_gravatar(client, email, url)
            elif platform_name == "github":
                return await self._check_github(client, email, url)
            elif platform_name == "keybase":
                return await self._check_keybase(client, email, url)
            
        except Exception as e:
            logger.debug(f"Failed to check {platform_name}: {e}")
        
        return None
    
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
    
    async def _check_keybase(self, client: HTTPClient, email: str, url: str) -> SocialResult | None:
        """Check Keybase for user by email."""
        try:
            data = await client.get(url)
            
            if data and data.get("them"):
                user = data["them"][0]
                basics = user.get("basics", {})
                profile = user.get("profile", {})
                return SocialResult(
                    source="social_email",
                    platform="keybase",
                    username=basics.get("username", ""),
                    name=profile.get("full_name", ""),
                    url=f"https://keybase.io/{basics.get('username', '')}",
                    found=True,
                    status="found",
                )
        except Exception as e:
            logger.debug(f"Keybase check failed: {e}")
        
        return None
    
    def _md5(self, text: str) -> str:
        """Generate MD5 hash for Gravatar."""
        return hashlib.md5(text.lower().strip().encode()).hexdigest()
