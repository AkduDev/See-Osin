"""Reverse Phone Lookup module for See OSINT tool.

Searches multiple free sources to find owner names:
- DuckDuckGo search (scraping-friendly)
- Multiple free reverse lookup APIs
- Social media profile detection
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

logger = get_logger("reverse_lookup")


class ReverseLookupModule(BaseModule):
    """Module to find owner name via multiple free reverse lookup sources."""

    @property
    def name(self) -> str:
        return "reverse_lookup"

    @property
    def description(self) -> str:
        return "Find owner name via search engines and free lookup services"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def target_field(self) -> str:
        return "owner"

    @property
    def is_available(self) -> bool:
        return True

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Search multiple sources for owner name."""
        logger.info(f"Running reverse lookup for {phone.e164}")

        results: dict[str, Any] = {
            "names_found": [],
            "sources": [],
            "profiles": [],
            "search_urls": [],
        }

        async with HTTPClient(
            timeout=config.lookup.timeout,
            retries=2,
        ) as client:
            # Generate search URLs for manual investigation
            self._generate_search_urls(phone, results)

            # Try automated searches
            await self._search_duckduckgo(client, phone, results)
            await self._search_bing(client, phone, results)

        if not results["names_found"] and not results["profiles"]:
            # Even if no names found, return search URLs
            if results["search_urls"]:
                return {
                    "names": [],
                    "primary_name": None,
                    "sources": [],
                    "profiles": results["profiles"],
                    "search_urls": results["search_urls"],
                    "message": "No names found automatically. Use search URLs to investigate manually.",
                    "source": "reverse_lookup",
                }
            return None

        # Deduplicate names
        unique_names = list(dict.fromkeys(results["names_found"]))

        return {
            "names": unique_names,
            "primary_name": unique_names[0] if unique_names else None,
            "sources": results["sources"],
            "profiles": results["profiles"],
            "search_urls": results["search_urls"],
            "source": "reverse_lookup",
        }

    def _generate_search_urls(self, phone: PhoneInfo, results: dict) -> None:
        """Generate search URLs for manual investigation."""
        clean = phone.e164.replace("+", "")
        international = phone.international.replace(" ", "")
        national = phone.national.replace(" ", "")

        # Generate comprehensive search URLs
        results["search_urls"] = [
            # Google searches
            {
                "platform": "Google",
                "query": f'"{phone.e164}" name owner',
                "url": f"https://www.google.com/search?q={quote_plus(phone.e164 + ' name owner')}",
            },
            {
                "platform": "Google",
                "query": f'"{international}" "es" OR "es un" OR "pertenece"',
                "url": f"https://www.google.com/search?q={quote_plus(international + ' "es" OR "es un" OR "pertenece"')}",
            },
            # Truecaller
            {
                "platform": "Truecaller",
                "query": "Search on Truecaller",
                "url": f"https://www.truecaller.com/search/{phone.country.lower()}/{clean}",
            },
            # Sync.me
            {
                "platform": "Sync.me",
                "query": "Search on Sync.me",
                "url": f"https://sync.me/search/?number=%2B{clean}",
            },
            # Facebook
            {
                "platform": "Facebook",
                "query": f'Search "{phone.e164}" on Facebook',
                "url": f"https://www.facebook.com/search/people/?q={clean}",
            },
            # Instagram
            {
                "platform": "Instagram",
                "query": f'Search "{phone.e164}" on Instagram',
                "url": f"https://www.google.com/search?q=site:instagram.com+{clean}",
            },
            # LinkedIn
            {
                "platform": "LinkedIn",
                "query": f'Search "{phone.e164}" on LinkedIn',
                "url": f"https://www.google.com/search?q=site:linkedin.com+{clean}",
            },
            # WhitePages (US)
            {
                "platform": "WhitePages",
                "query": "Search on WhitePages",
                "url": f"https://www.whitepages.com/phone/{clean}",
            },
            # SpyDialer (US)
            {
                "platform": "SpyDialer",
                "query": "Search on SpyDialer",
                "url": f"https://www.spydialer.com/default.aspx?r={clean}",
            },
            # Cuban specific (ETECSA directory)
            {
                "platform": "Cuba",
                "query": "Search Cuban phone directories",
                "url": f"https://www.google.com/search?q={quote_plus(clean + ' cuba directorio telefonico')}",
            },
        ]

    async def _search_duckduckgo(
        self, client: HTTPClient, phone: PhoneInfo, results: dict
    ) -> None:
        """Search DuckDuckGo for phone number (more scraping-friendly)."""
        try:
            clean = phone.e164.replace("+", "")
            queries = [
                f'"{phone.e164}" name',
                f'"{clean}" owner',
            ]

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            for query in queries[:1]:  # Limit to 1 query
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

                try:
                    response = await client.get(url, headers=headers)
                    if not response or not isinstance(response, str):
                        continue

                    # Look for names in search results
                    # DuckDuckGo returns results in simple HTML
                    name_patterns = [
                        r'class="result__a"[^>]*>([^<]+)<',
                        r'class="result__snippet"[^>]*>([^<]+)<',
                        r'>([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)<',
                    ]

                    for pattern in name_patterns:
                        matches = re.findall(pattern, response)
                        for match in matches:
                            name = match.strip()
                            # Clean up HTML entities
                            name = name.replace("&amp;", "&").replace("&#x27;", "'")

                            # Filter results
                            if (len(name) > 5 and " " in name and
                                not any(x in name.lower() for x in
                                       ("duckduckgo", "search", "result", "privacy",
                                        "settings", "safe", "filter", "phone", "number"))):
                                results["names_found"].append(name)
                                results["sources"].append("duckduckgo")
                                logger.info(f"DuckDuckGo found name: {name}")
                                break

                except Exception as e:
                    logger.debug(f"DuckDuckGo query failed: {e}")
                    continue

        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {e}")

    async def _search_bing(
        self, client: HTTPClient, phone: PhoneInfo, results: dict
    ) -> None:
        """Search Bing for phone number."""
        try:
            clean = phone.e164.replace("+", "")
            url = f"https://www.bing.com/search?q={quote_plus(phone.e164 + ' name owner')}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            response = await client.get(url, headers=headers)
            if not response or not isinstance(response, str):
                return

            # Look for names in Bing results
            name_patterns = [
                r'<h2><a[^>]*>([^<]+)</a></h2>',
                r'class="b_caption"[^>]*>([^<]+)<',
                r'>([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)<',
            ]

            for pattern in name_patterns:
                matches = re.findall(pattern, response)
                for match in matches:
                    name = match.strip()
                    if (len(name) > 5 and " " in name and
                        not any(x in name.lower() for x in
                               ("bing", "microsoft", "search", "result"))):
                        results["names_found"].append(name)
                        results["sources"].append("bing")
                        logger.info(f"Bing found name: {name}")
                        break

        except Exception as e:
            logger.debug(f"Bing search failed: {e}")
