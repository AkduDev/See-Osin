"""Google Dorks module for See OSINT tool.

Search phone numbers across search engines using dork queries.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from see.core.parser import PhoneInfo
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("google_dorks")

# Sites to include in dork queries
DORK_SITES = [
    ("facebook.com", "Facebook"),
    ("instagram.com", "Instagram"),
    ("twitter.com", "Twitter"),
    ("linkedin.com", "LinkedIn"),
    ("github.com", "GitHub"),
]


class GoogleDorksModule(BaseModule):
    """OSINT module for phone number search engine lookups."""

    @property
    def name(self) -> str:
        return "google_dorks"

    @property
    def description(self) -> str:
        return "Search engine dorks for phone number OSINT"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def target_field(self) -> str:
        return "search_dorks"

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Generate search engine dorks for the phone number."""
        logger.info(f"Generating Google dorks for {phone.e164}")

        formats = self._generate_formats(phone)
        dorks = []
        search_urls = []

        for fmt in formats:
            dork = self._create_dork(fmt)
            dorks.append(dork)
            search_urls.append(self._create_search_urls(dork["query"]))

        for dork in self._create_site_dorks(phone):
            dorks.append(dork)
            search_urls.append(self._create_search_urls(dork["query"]))

        logger.info(f"Generated {len(dorks)} dorks")
        return {"dorks": dorks, "search_urls": search_urls, "source": "google_dorks"}

    def _generate_formats(self, phone: PhoneInfo) -> list[str]:
        """Generate different formats of the phone number."""
        formats = [
            phone.e164,
            phone.e164.replace("+", ""),
            phone.international,
            phone.national,
            phone.national.replace(" ", "-"),
        ]

        # Add parentheses format
        if len(phone.national_number) > 6:
            area = phone.national_number[:3]
            rest = phone.national_number[3:]
            formats.append(f"({area}) {rest}")
            formats.append(f"({area}){rest}")

        return list(set(formats))

    def _create_dork(self, phone_format: str) -> dict[str, str]:
        """Create a search dork for a phone format."""
        return {"query": f'"{phone_format}"', "description": f"Exact match for {phone_format}"}

    def _create_site_dorks(self, phone: PhoneInfo) -> list[dict[str, str]]:
        """Create site-specific search dorks."""
        return [
            {"query": f'site:{site} "{phone.e164}"', "description": f"Search {name} for {phone.e164}"}
            for site, name in DORK_SITES
        ]

    def _create_search_urls(self, query: str) -> dict[str, str | None]:
        """Create search URLs for a query."""
        encoded = quote_plus(query)
        return {
            "query": query,
            "google": f"https://www.google.com/search?q={encoded}",
            "bing": f"https://www.bing.com/search?q={encoded}",
            "duckduckgo": f"https://duckduckgo.com/?q={encoded}",
        }
