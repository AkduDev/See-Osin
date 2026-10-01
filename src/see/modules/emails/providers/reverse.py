"""Reverse email lookup provider for email OSINT."""

from __future__ import annotations

from see.core.types import SocialResult
from see.modules.emails.providers.base import BaseEmailProvider
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("reverse_email_provider")


class ReverseEmailProvider(BaseEmailProvider):
    """
    Provider for reverse email lookup.
    
    Searches for email address across various web sources
    to find associated accounts and information.
    No API key required.
    """
    
    @property
    def name(self) -> str:
        return "reverse_email"
    
    @property
    def description(self) -> str:
        return "Reverse email lookup across web sources"
    
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
        """Find social media profiles for email using web search."""
        logger.info(f"Running reverse email lookup for {email}")
        
        profiles = []
        
        # Search engines and social platforms
        search_urls = [
            {
                "name": "Google",
                "url": f"https://www.google.com/search?q=%22{email}%22",
                "type": "search",
            },
            {
                "name": "DuckDuckGo",
                "url": f"https://duckduckgo.com/html/?q=%22{email}%22",
                "type": "search",
            },
            {
                "name": "Bing",
                "url": f"https://www.bing.com/search?q=%22{email}%22",
                "type": "search",
            },
            {
                "name": "Yandex",
                "url": f"https://yandex.com/search/?text=%22{email}%22",
                "type": "search",
            },
        ]
        
        # Social platforms with email search
        social_searches = [
            {
                "name": "Facebook",
                "url": f"https://www.facebook.com/search/people/?q={email}",
                "type": "social",
            },
            {
                "name": "LinkedIn",
                "url": f"https://www.linkedin.com/search/results/all/?keywords={email}",
                "type": "social",
            },
            {
                "name": "Twitter",
                "url": f"https://twitter.com/search?q={email}",
                "type": "social",
            },
            {
                "name": "Instagram",
                "url": f"https://www.instagram.com/accounts/login/?next=/explore/search/keyword/?q={email}",
                "type": "social",
            },
            {
                "name": "TikTok",
                "url": f"https://www.tiktok.com/search?q={email}",
                "type": "social",
            },
            {
                "name": "Reddit",
                "url": f"https://www.reddit.com/search/?q={email}",
                "type": "social",
            },
            {
                "name": "Pinterest",
                "url": f"https://www.pinterest.com/search/pins/?q={email}",
                "type": "social",
            },
            {
                "name": "YouTube",
                "url": f"https://www.youtube.com/results?search_query={email}",
                "type": "social",
            },
        ]
        
        # NOTE: no HTTP request is made here. Real scraping needs JS/rendering
        # or an API; we honestly return search links for manual investigation
        # instead of pretending to have checked these platforms.
        for search in search_urls:
            profiles.append(SocialResult(
                source="reverse_email",
                platform=f"search_{search['name'].lower()}",
                username=email.split('@')[0],
                name="",
                url=search["url"],
                found=False,
                status="check_manually",
            ))

        for social in social_searches:
            profiles.append(SocialResult(
                source="reverse_email",
                platform=f"social_{social['name'].lower()}",
                username=email.split('@')[0],
                name="",
                url=social["url"],
                found=False,
                status="check_manually",
            ))

        return profiles
