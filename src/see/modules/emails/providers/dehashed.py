"""DeHashed provider for email OSINT."""

from __future__ import annotations

import base64
from typing import Any

from see.modules.emails.providers.base import BaseEmailProvider
from see.core.types import BreachResult, SocialResult
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("dehashed_provider")

DEHASHED_BASE_URL = "https://api.dehashed.com"


class DeHashedProvider(BaseEmailProvider):
    """
    Provider using DeHashed API.
    
    Provides breach data, phone numbers, addresses, passwords,
    and usernames associated with an email address.
    Requires API key from https://dehashed.com
    """
    
    @property
    def name(self) -> str:
        return "dehashed"
    
    @property
    def description(self) -> str:
        return "Breach data and personal info via DeHashed API"
    
    @property
    def requires_api_key(self) -> bool:
        return True
    
    @property
    def supports_breaches(self) -> bool:
        return True
    
    @property
    def supports_social(self) -> bool:
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if API key is configured."""
        from see.utils.config import load_config
        config = load_config()
        return bool(config.api_keys.dehashed)
    
    async def get_breach_data(self, email: str, config: AppConfig) -> dict[str, Any] | None:
        """
        Get breach data from DeHashed.
        
        Returns:
            Dictionary with breaches, phone numbers, addresses, passwords
        """
        api_key = config.api_keys.dehashed
        
        if not api_key:
            logger.warning("DeHashed API key not configured")
            return None
        
        logger.info(f"Running DeHashed lookup for {email}")
        
        url = f"{DEHASHED_BASE_URL}/search"
        params = {
            "query": f"email:{email}",
        }
        
        # DeHashed uses API key in headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        
        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=config.lookup.retries,
            use_tor=config.tor.enabled,
        ) as client:
            data = await client.get(url, params=params, headers=headers)
            
            if not data:
                logger.error("DeHashed request failed")
                return None
            
            # Extract results
            results = data.get("results", [])
            
            if not results:
                return None
            
            # Aggregate data
            aggregated = {
                "email": email,
                "breaches": [],
                "phone_numbers": [],
                "addresses": [],
                "passwords": [],
                "usernames": [],
                "names": [],
                "sources": [],
            }
            
            for entry in results:
                # Breach info
                if entry.get("database_name"):
                    breach = {
                        "name": entry.get("database_name", ""),
                        "date": entry.get("breach_date", ""),
                        "records": entry.get("records_in_database", ""),
                        "password": entry.get("password", ""),
                        "hash": entry.get("hashed_password", ""),
                        "salt": entry.get("salt", ""),
                    }
                    aggregated["breaches"].append(breach)
                    
                    if entry.get("database_name") not in aggregated["sources"]:
                        aggregated["sources"].append(entry.get("database_name", ""))
                
                # Phone numbers
                if entry.get("phone_number"):
                    if entry["phone_number"] not in aggregated["phone_numbers"]:
                        aggregated["phone_numbers"].append(entry["phone_number"])
                
                # Addresses
                if entry.get("address"):
                    address = entry["address"]
                    if address not in aggregated["addresses"]:
                        aggregated["addresses"].append(address)
                
                # Passwords
                if entry.get("password"):
                    password_info = {
                        "password": entry["password"],
                        "hash": entry.get("hashed_password", ""),
                        "salt": entry.get("salt", ""),
                    }
                    aggregated["passwords"].append(password_info)
                
                # Usernames
                if entry.get("username"):
                    if entry["username"] not in aggregated["usernames"]:
                        aggregated["usernames"].append(entry["username"])
                
                # Names
                if entry.get("name"):
                    if entry["name"] not in aggregated["names"]:
                        aggregated["names"].append(entry["name"])
            
            return aggregated
    
    async def get_breaches(self, email: str, config: AppConfig) -> BreachResult | None:
        """Get breach information for email."""
        data = await self.get_breach_data(email, config)
        
        if not data or not data.get("breaches"):
            return None
        
        return BreachResult(
            source="dehashed",
            email=email,
            breaches=data["breaches"],
            total_breaches=len(data["breaches"]),
            sources=data.get("sources", []),
        )
    
    async def get_social_profiles(self, email: str, config: AppConfig) -> list[SocialResult]:
        """Get social media profiles from breach data."""
        data = await self.get_breach_data(email, config)
        
        if not data:
            return []
        
        profiles = []
        
        # Add usernames as potential social profiles
        for username in data.get("usernames", []):
            profiles.append(SocialResult(
                source="dehashed",
                platform="breach_username",
                username=username,
                name="",
                url="",
                found=True,
                status="found",
            ))
        
        return profiles
