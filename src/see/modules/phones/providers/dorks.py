"""Google dorks / investigation links provider for phone OSINT."""

from __future__ import annotations

from urllib.parse import quote

from see.core.types import SocialResult
from see.modules.phones.providers.base import BasePhoneProvider
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("dorks_provider")


def build_search_links(e164: str) -> list[SocialResult]:
    """
    Build manual investigation links for a phone number (pure, testable).

    Includes search-engine dorks and community spam directories.
    These are follow-up links for the analyst - we do not pretend to
    have checked them.
    """
    if not e164:
        return []

    n = e164
    bare = e164.lstrip("+")
    quoted = quote(f'"{n}"', safe="")

    dorks = [
        ("dork_google_exact", f"https://www.google.com/search?q={quoted}"),
        ("dork_google_spam",
         "https://www.google.com/search?q=" + quote(f'"{n}" spam OR estafa OR scam', safe="")),
        ("dork_google_contact",
         "https://www.google.com/search?q=" + quote(f'"{n}" email OR telefono OR contact', safe="")),
        ("dork_google_facebook",
         "https://www.google.com/search?q=" + quote(f'"{n}" site:facebook.com', safe="")),
        ("dork_bing_exact", f"https://www.bing.com/search?q={quoted}"),
        ("dork_ddg_exact", f"https://duckduckgo.com/html/?q={quoted}"),
        ("db_tellows", f"https://www.tellows.de/num/{bare}"),
        ("db_shouldianswer", f"https://www.shouldianswer.co.uk/search?q={quote(n, safe='')}"),
        ("db_whocallsme", f"https://whocallsme.com/Phone-Number.aspx/{bare}"),
        ("db_numlookup", f"https://www.numlookup.com/reverse-phone-lookup/{bare}"),
    ]

    return [
        SocialResult(
            source="dorks",
            platform=name,
            username="",
            name="",
            url=url,
            found=False,
            status="check_manually",
        )
        for name, url in dorks
    ]


class DorksProvider(BasePhoneProvider):
    """
    Provider that generates search-engine dorks and lookup-site links
    for manual follow-up (Google, Bing, DuckDuckGo, Tellows, ...).
    No network requests, no API key.
    """

    @property
    def name(self) -> str:
        return "dorks"

    @property
    def description(self) -> str:
        return "Google dorks and manual lookup links for the number"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def supports_search_links(self) -> bool:
        return True

    @property
    def is_available(self) -> bool:
        return True

    async def get_search_links(
        self, phone: str, config: AppConfig
    ) -> list[SocialResult]:
        """Generate investigation links for the phone number."""
        links = build_search_links(phone)
        logger.info(f"Generated {len(links)} investigation links for {phone}")
        return links
