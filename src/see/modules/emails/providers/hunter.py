"""Hunter.io provider for email OSINT."""

from __future__ import annotations

from typing import Any

from see.core.types import SocialResult
from see.modules.emails.providers.base import BaseEmailProvider
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("hunter_provider")

HUNTER_BASE_URL = "https://api.hunter.io/v2"


class HunterProvider(BaseEmailProvider):
    """
    Provider using Hunter.io API.
    
    Provides company, phone, job title, and social media information
    associated with an email address.
    Requires API key from https://hunter.io
    """
    
    def __init__(self, config: AppConfig | None = None):
        self._config = config
        self._cache: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "hunter"
    
    @property
    def description(self) -> str:
        return "Email intelligence via Hunter.io API"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    @property
    def supports_social(self) -> bool:
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config
        config = self._config or load_config()
        return bool(config.api_keys.hunter)
    
    async def get_email_info(self, email: str, config: AppConfig) -> dict[str, Any] | None:
        """
        Get email information from Hunter.io.
        
        Returns:
            Dictionary with name, phone, company, job_title, social profiles
        """
        import time

        cached = self._cache.get(email)
        if cached and (time.time() - cached["at"]) < 300:
            return cached["data"]

        api_key = config.api_keys.hunter
        
        if not api_key:
            logger.warning("Hunter.io API key not configured")
            return None
        
        logger.info(f"Running Hunter.io lookup for {email}")
        
        url = f"{HUNTER_BASE_URL}/email-verifier"
        params = {
            "email": email,
            "api_key": api_key,
        }
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=2,  # Hunter has strict rate limits
            use_tor=config.tor.enabled,
        ) as client:
            data = await client.get(url, params=params)
            
            if not data:
                logger.error("Hunter.io request failed")
                self._cache[email] = {"at": time.time(), "data": None}
                return None
            
            # Extract information
            result = {
                "email": email,
                "status": data.get("data", {}).get("status", "unknown"),
                "confidence": data.get("data", {}).get("confidence", 0),
                "sources": data.get("data", {}).get("sources", []),
                "metadata": data.get("data", {}).get("metadata", {}),
            }
            
            # Extract additional data from metadata
            metadata = result.get("metadata", {})
            if metadata:
                result["name"] = metadata.get("name", "")
                result["company"] = metadata.get("company", "")
                result["job_title"] = metadata.get("job_title", "")
                result["phone"] = metadata.get("phone", "")
                result["linkedin"] = metadata.get("linkedin", "")
                result["twitter"] = metadata.get("twitter", "")
                result["location"] = metadata.get("location", "")

            self._cache[email] = {"at": time.time(), "data": result}
            return result
    
    async def get_social_profiles(self, email: str, config: AppConfig) -> list[SocialResult]:
        """Get social media profiles for email using Hunter.io."""
        info = await self.get_email_info(email, config)
        
        if not info:
            return []
        
        profiles = []
        
        # LinkedIn
        if info.get("linkedin"):
            profiles.append(SocialResult(
                source="hunter",
                platform="linkedin",
                username=info["linkedin"].split("/")[-1],
                name=info.get("name", ""),
                url=info["linkedin"],
                found=True,
                status="found",
            ))
        
        # Twitter
        if info.get("twitter"):
            profiles.append(SocialResult(
                source="hunter",
                platform="twitter",
                username=info["twitter"].replace("@", ""),
                name=info.get("name", ""),
                url=f"https://twitter.com/{info['twitter'].replace('@', '')}",
                found=True,
                status="found",
            ))
        
        return profiles
