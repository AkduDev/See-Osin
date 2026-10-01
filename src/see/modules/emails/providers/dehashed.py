"""DeHashed provider for email OSINT."""

from __future__ import annotations

import base64
from typing import Any

from see.core.types import BreachResult, SocialResult
from see.modules.emails.providers.base import BaseEmailProvider
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("dehashed_provider")

DEHASHED_BASE_URL = "https://api.dehashed.com"


class DeHashedProvider(BaseEmailProvider):
    """
    Provider using DeHashed API.

    Provides breach data, phone numbers, addresses,
    and usernames associated with an email address.
    Requires an account email + API key from https://dehashed.com
    (HTTP Basic auth: account email as username, API key as password).
    """

    def __init__(self, config: AppConfig | None = None):
        self._config = config
        self._cache: dict[str, Any] = {}

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
        """Check if API credentials are configured."""
        from see.utils.config import load_config
        config = self._config or load_config()
        return bool(config.api_keys.dehashed and config.api_keys.dehashed_email)

    def _auth_headers(self, config: AppConfig) -> dict[str, str] | None:
        """Build HTTP Basic auth headers (account email + API key)."""
        account = (config.api_keys.dehashed_email or "").strip()
        api_key = (config.api_keys.dehashed or "").strip()

        if not api_key:
            logger.warning("DeHashed API key not configured")
            return None
        if not account:
            logger.warning("DeHashed account email not configured (SEE_DEHASHED_EMAIL)")
            return None

        token = base64.b64encode(f"{account}:{api_key}".encode()).decode()
        return {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        }
    
    async def get_breach_data(self, email: str, config: AppConfig, include_passwords: bool = False) -> dict[str, Any] | None:
        """
        Get breach data from DeHashed.
        
        Args:
            email: Email address to search
            config: Application config
            include_passwords: Whether to include passwords in output (default: False for security)
        
        Returns:
            Dictionary with breaches, phone numbers, addresses, usernames
        """
        import time

        cached = self._cache.get(email)
        if cached and (time.time() - cached["at"]) < 300:
            return cached["data"]

        headers = self._auth_headers(config)
        if headers is None:
            return None

        logger.info(f"Running DeHashed lookup for {email}")

        url = f"{DEHASHED_BASE_URL}/search"
        params = {
            "query": f"email:{email}",
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
                # Cache negative result too (avoids re-query in same scan)
                self._cache[email] = {"at": time.time(), "data": None}
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
                    }
                    # Only include password info if explicitly requested
                    if include_passwords:
                        breach["password"] = entry.get("password", "")
                        breach["hash"] = entry.get("hashed_password", "")
                        breach["salt"] = entry.get("salt", "")
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
                
                # Passwords (only if explicitly requested)
                if include_passwords and entry.get("password"):
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

            self._cache[email] = {"at": time.time(), "data": aggregated}
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
