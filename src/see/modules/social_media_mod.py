"""Social Media OSINT module for See OSINT tool.

Searches social media platforms for phone number associations:
- Instagram
- Facebook
- TikTok
- Twitter/X
- LinkedIn
- Snapchat
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from see.core.parser import PhoneInfo
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("social_media")


class SocialMediaModule(BaseModule):
    """Module to find social media profiles associated with a phone number."""

    @property
    def name(self) -> str:
        return "social_media"

    @property
    def description(self) -> str:
        return "Find Instagram, Facebook, TikTok, Twitter profiles by phone number"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def target_field(self) -> str:
        return "social_profiles"

    @property
    def is_available(self) -> bool:
        return True

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Search social media platforms for phone number."""
        logger.info(f"Running social media OSINT for {phone.e164}")

        profiles = []
        search_urls = []

        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=2,
        ) as client:
            # Search each platform
            await self._search_instagram(client, phone, profiles, search_urls)
            await self._search_facebook(client, phone, profiles, search_urls)
            await self._search_tiktok(client, phone, profiles, search_urls)
            await self._search_twitter(client, phone, profiles, search_urls)
            await self._search_linkedin(client, phone, profiles, search_urls)
            await self._search_snapchat(client, phone, profiles, search_urls)

        if not profiles and not search_urls:
            return None

        return {
            "profiles": profiles,
            "search_urls": search_urls,
            "platforms_checked": ["Instagram", "Facebook", "TikTok", "Twitter", "LinkedIn", "Snapchat"],
            "found_count": len(profiles),
            "source": "social_media",
        }

    async def _search_instagram(
        self, client: HTTPClient, phone: PhoneInfo, profiles: list, search_urls: list
    ) -> None:
        """Search Instagram for phone number."""
        try:
            clean = phone.e164.replace("+", "")

            # Method 1: Direct search URL
            search_url = f"https://www.instagram.com/accounts/login/?next=/explore/search/keyword/?q={clean}"
            search_urls.append({
                "platform": "Instagram",
                "query": f"Search phone on Instagram",
                "url": f"https://www.google.com/search?q=site:instagram.com+{clean}",
            })

            # Method 2: Try to find via Google
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            url = f"https://www.google.com/search?q=site:instagram.com+{clean}"
            response = await client.get(url, headers=headers)

            if response and isinstance(response, str):
                # Extract Instagram usernames from Google results
                username_patterns = [
                    r'instagram\.com/([a-zA-Z0-9_.]+)',
                    r'"username"\s*:\s*"([^"]+)"',
                    r'@"([a-zA-Z0-9_.]+)"',
                ]

                found_usernames = set()
                for pattern in username_patterns:
                    matches = re.findall(pattern, response)
                    for match in matches:
                        username = match.strip()
                        # Filter out common non-username strings
                        if (username and len(username) > 2 and
                            username.lower() not in ("instagram", "login", "signup",
                                                       "explore", "reels", "stories")):
                            found_usernames.add(username)

                for username in list(found_usernames)[:3]:
                    profiles.append({
                        "platform": "Instagram",
                        "username": username,
                        "url": f"https://www.instagram.com/{username}/",
                        "type": "social",
                        "status": "found_via_search",
                    })
                    logger.info(f"Instagram found: @{username}")

        except Exception as e:
            logger.debug(f"Instagram search failed: {e}")

    async def _search_facebook(
        self, client: HTTPClient, phone: PhoneInfo, profiles: list, search_urls: list
    ) -> None:
        """Search Facebook for phone number."""
        try:
            clean = phone.e164.replace("+", "")

            # Generate search URLs
            search_urls.append({
                "platform": "Facebook",
                "query": f"Search phone on Facebook",
                "url": f"https://www.facebook.com/search/people/?q={clean}",
            })

            # Try Google search for Facebook profiles
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            url = f"https://www.google.com/search?q=site:facebook.com+{clean}"
            response = await client.get(url, headers=headers)

            if response and isinstance(response, str):
                # Extract Facebook profile info
                name_patterns = [
                    r'facebook\.com/([a-zA-Z0-9.]+)',
                    r'"name"\s*:\s*"([^"]{3,50})"',
                    r'>([A-Z][a-z]+ [A-Z][a-z]+)</span>',
                ]

                found_profiles = set()
                for pattern in name_patterns:
                    matches = re.findall(pattern, response)
                    for match in matches:
                        match = match.strip()
                        if match and len(match) > 2:
                            if "." in match or match.isalnum():
                                # Likely a username
                                if match.lower() not in ("facebook", "meta", "login"):
                                    found_profiles.add(("username", match))
                            elif " " in match:
                                # Likely a name
                                if match.lower() not in ("facebook", "meta"):
                                    found_profiles.add(("name", match))

                for ptype, value in list(found_profiles)[:3]:
                    if ptype == "username":
                        profiles.append({
                            "platform": "Facebook",
                            "username": value,
                            "url": f"https://www.facebook.com/{value}/",
                            "type": "social",
                            "status": "found_via_search",
                        })
                        logger.info(f"Facebook found: @{value}")
                    else:
                        profiles.append({
                            "platform": "Facebook",
                            "name": value,
                            "url": f"https://www.facebook.com/search/people/?q={quote_plus(value)}",
                            "type": "social",
                            "status": "found_via_search",
                        })
                        logger.info(f"Facebook found name: {value}")

        except Exception as e:
            logger.debug(f"Facebook search failed: {e}")

    async def _search_tiktok(
        self, client: HTTPClient, phone: PhoneInfo, profiles: list, search_urls: list
    ) -> None:
        """Search TikTok for phone number."""
        try:
            clean = phone.e164.replace("+", "")

            # Generate search URL
            search_urls.append({
                "platform": "TikTok",
                "query": f"Search phone on TikTok",
                "url": f"https://www.google.com/search?q=site:tiktok.com+{clean}",
            })

            # Try Google search
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            url = f"https://www.google.com/search?q=site:tiktok.com+{clean}"
            response = await client.get(url, headers=headers)

            if response and isinstance(response, str):
                # Extract TikTok usernames
                username_patterns = [
                    r'tiktok\.com/@([a-zA-Z0-9_.]+)',
                    r'"uniqueId"\s*:\s*"([^"]+)"',
                    r'"nickname"\s*:\s*"([^"]+)"',
                ]

                found_usernames = set()
                for pattern in username_patterns:
                    matches = re.findall(pattern, response)
                    for match in matches:
                        username = match.strip()
                        if (username and len(username) > 2 and
                            username.lower() not in ("tiktok", "login", "signup")):
                            found_usernames.add(username)

                for username in list(found_usernames)[:3]:
                    profiles.append({
                        "platform": "TikTok",
                        "username": username,
                        "url": f"https://www.tiktok.com/@{username}",
                        "type": "social",
                        "status": "found_via_search",
                    })
                    logger.info(f"TikTok found: @{username}")

        except Exception as e:
            logger.debug(f"TikTok search failed: {e}")

    async def _search_twitter(
        self, client: HTTPClient, phone: PhoneInfo, profiles: list, search_urls: list
    ) -> None:
        """Search Twitter/X for phone number."""
        try:
            clean = phone.e164.replace("+", "")

            # Generate search URLs
            search_urls.append({
                "platform": "Twitter",
                "query": f"Search phone on Twitter",
                "url": f"https://www.google.com/search?q=site:twitter.com+OR+site:x.com+{clean}",
            })

            # Try Google search
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            url = f"https://www.google.com/search?q=site:twitter.com+OR+site:x.com+{clean}"
            response = await client.get(url, headers=headers)

            if response and isinstance(response, str):
                # Extract Twitter usernames
                username_patterns = [
                    r'twitter\.com/([a-zA-Z0-9_]+)',
                    r'x\.com/([a-zA-Z0-9_]+)',
                    r'@"([a-zA-Z0-9_]+)"',
                ]

                found_usernames = set()
                for pattern in username_patterns:
                    matches = re.findall(pattern, response)
                    for match in matches:
                        username = match.strip()
                        if (username and len(username) > 2 and
                            username.lower() not in ("twitter", "x", "login", "signup",
                                                       "explore", "search")):
                            found_usernames.add(username)

                for username in list(found_usernames)[:3]:
                    profiles.append({
                        "platform": "Twitter",
                        "username": username,
                        "url": f"https://twitter.com/{username}",
                        "type": "social",
                        "status": "found_via_search",
                    })
                    logger.info(f"Twitter found: @{username}")

        except Exception as e:
            logger.debug(f"Twitter search failed: {e}")

    async def _search_linkedin(
        self, client: HTTPClient, phone: PhoneInfo, profiles: list, search_urls: list
    ) -> None:
        """Search LinkedIn for phone number."""
        try:
            clean = phone.e164.replace("+", "")

            # Generate search URL
            search_urls.append({
                "platform": "LinkedIn",
                "query": f"Search phone on LinkedIn",
                "url": f"https://www.google.com/search?q=site:linkedin.com+{clean}",
            })

            # Try Google search
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            url = f"https://www.google.com/search?q=site:linkedin.com+{clean}"
            response = await client.get(url, headers=headers)

            if response and isinstance(response, str):
                # Extract LinkedIn profiles
                name_patterns = [
                    r'linkedin\.com/in/([a-zA-Z0-9-]+)',
                    r'"name"\s*:\s*"([^"]{3,50})"',
                ]

                found = set()
                for pattern in name_patterns:
                    matches = re.findall(pattern, response)
                    for match in matches:
                        match = match.strip()
                        if match and len(match) > 2:
                            if match.lower() not in ("linkedin", "login", "signup"):
                                found.add(match)

                for value in list(found)[:3]:
                    if "-" in value or value.isalnum():
                        profiles.append({
                            "platform": "LinkedIn",
                            "username": value,
                            "url": f"https://linkedin.com/in/{value}",
                            "type": "professional",
                            "status": "found_via_search",
                        })
                        logger.info(f"LinkedIn found: {value}")
                    else:
                        profiles.append({
                            "platform": "LinkedIn",
                            "name": value,
                            "url": f"https://linkedin.com/search/results/all/?keywords={quote_plus(value)}",
                            "type": "professional",
                            "status": "found_via_search",
                        })
                        logger.info(f"LinkedIn found name: {value}")

        except Exception as e:
            logger.debug(f"LinkedIn search failed: {e}")

    async def _search_snapchat(
        self, client: HTTPClient, phone: PhoneInfo, profiles: list, search_urls: list
    ) -> None:
        """Search Snapchat for phone number."""
        try:
            clean = phone.e164.replace("+", "")

            # Generate search URL
            search_urls.append({
                "platform": "Snapchat",
                "query": f"Search phone on Snapchat",
                "url": f"https://www.google.com/search?q=site:snapchat.com+{clean}",
            })

            # Try Google search
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            url = f"https://www.google.com/search?q=site:snapchat.com+{clean}"
            response = await client.get(url, headers=headers)

            if response and isinstance(response, str):
                # Extract Snapchat usernames
                username_patterns = [
                    r'snapchat\.com/add/([a-zA-Z0-9_.-]+)',
                    r'"username"\s*:\s*"([^"]+)"',
                ]

                found_usernames = set()
                for pattern in username_patterns:
                    matches = re.findall(pattern, response)
                    for match in matches:
                        username = match.strip()
                        if (username and len(username) > 2 and
                            username.lower() not in ("snapchat", "login", "signup")):
                            found_usernames.add(username)

                for username in list(found_usernames)[:3]:
                    profiles.append({
                        "platform": "Snapchat",
                        "username": username,
                        "url": f"https://snapchat.com/add/{username}",
                        "type": "social",
                        "status": "found_via_search",
                    })
                    logger.info(f"Snapchat found: @{username}")

        except Exception as e:
            logger.debug(f"Snapchat search failed: {e}")
