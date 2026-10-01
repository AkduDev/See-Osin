"""Spam/scam report provider for phone OSINT."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from see.core.types import SpamResult
from see.modules.phones.providers.base import BasePhoneProvider
from see.utils.config import AppConfig
from see.utils.http_client import HTTPClient
from see.utils.logger import get_logger

logger = get_logger("spam_provider")

# Should I Answer publishes community reports for a number at this URL.
# Tellows (403 for bots) and WhoCallsMe (no stable search URL) are only
# offered as manual links via the dorks provider.
SIASWER_URL = "https://www.shouldianswer.co.uk/search?q={query}"

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Words that are part of the rating breakdown, not category names
_RATING_WORDS = ("negativa", "negative", "positiva", "positive", "neutral")


def _strip_tags(html: str) -> str:
    """Remove HTML tags and collapse whitespace (pure, testable)."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;?", " ", text)
    return re.sub(r"\s+", " ", text)


def parse_shouldianswer(html: str) -> dict[str, Any]:
    """
    Extract rating, counts and categories from a Should I Answer page.

    Pure function so it can be unit-tested against a saved page and
    tolerate the English/Spanish variants of the site. When nothing
    recognizable is found, returns rating "unknown" (no fake data).
    """
    text = _strip_tags(html)
    low = text.lower()

    result: dict[str, Any] = {
        "rating": "unknown",
        "total_reports": 0,
        "positive": 0,
        "negative": 0,
        "categories": [],
    }

    # Rating phrase: "evaluación negativa" / "negative evaluation"
    m = re.search(
        r"(?:evaluaci[oó]n|evaluation|rating)\s+"
        r"(negativa|negative|positiva|positive|neutral)",
        low,
    )
    if m:
        word = m.group(1)
        result["rating"] = {
            "negativa": "negative",
            "negative": "negative",
            "positiva": "positive",
            "positive": "positive",
            "neutral": "neutral",
        }[word]

    # Header badge: "NEGATIVA VENDEDOR TELEFONICO"
    if result["rating"] == "unknown":
        m = re.search(r"\b(NEGATIVA|NEGATIVE|POSITIVA|POSITIVE|NEUTRAL)\b", text, re.I)
        if m:
            result["rating"] = {
                "negativa": "negative",
                "negative": "negative",
                "positiva": "positive",
                "positive": "positive",
                "neutral": "neutral",
            }[m.group(1).lower()]

    # Counts: "5x negativa3x positiva"
    m = re.search(r"(\d+)\s*x\s*(?:\s*stars?\s*)?(?:negativa|negative)", low)
    if m:
        result["negative"] = int(m.group(1))
    m = re.search(r"(\d+)\s*x\s*(?:\s*stars?\s*)?(?:positiva|positive)", low)
    if m:
        result["positive"] = int(m.group(1))

    # Categories: "4x Vendedor telefonico1x Servicios financieros..."
    # On plain text the segments run together, so stop at the next "Nx".
    for m in re.finditer(
        r"(\d+)\s*x\s+([^\d]{3,50}?)(?=\s*\d+\s*x|$)", text, re.I
    ):
        count, name = int(m.group(1)), m.group(2).strip(" .,-")
        if not name or any(w in name.lower() for w in _RATING_WORDS):
            continue
        if len(result["categories"]) < 10:
            result["categories"].append(f"{count}x {name}")

    # Total reports: explicit sentence, else sum of breakdown counts
    m = re.search(r"coleccionado\s*(\d+)|collected\s*(\d+)", low)
    if m:
        result["total_reports"] = int(m.group(1) or m.group(2))
    else:
        m = re.search(r"(\d+)\s*(?:evaluaciones|reviews|bewertungen)", low)
        if m:
            result["total_reports"] = int(m.group(1))
        else:
            result["total_reports"] = result["positive"] + result["negative"]

    # Rating fallback from counts when no phrase was found
    if result["rating"] == "unknown" and result["total_reports"] > 0:
        if result["negative"] > result["positive"]:
            result["rating"] = "negative"
        elif result["positive"] > result["negative"]:
            result["rating"] = "positive"
        else:
            result["rating"] = "neutral"

    return result


class SpamProvider(BasePhoneProvider):
    """
    Provider for spam/scam reports about a phone number.

    Scrapes Should I Answer community reports (no API key). Parsing is
    defensive: if the page layout changes, rating stays "unknown" and
    the report URL is still returned for manual review.
    """

    @property
    def name(self) -> str:
        return "spam"

    @property
    def description(self) -> str:
        return "Spam/scam community reports (Should I Answer)"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def supports_spam(self) -> bool:
        return True

    @property
    def is_available(self) -> bool:
        return True

    async def get_spam(self, phone: str, config: AppConfig) -> SpamResult | None:
        """Look up community spam reports for the phone number."""
        if not phone:
            return None

        url = SIASWER_URL.format(query=quote(phone, safe=""))
        logger.info(f"Checking spam reports for {phone}")

        try:
            async with HTTPClient(
                timeout=min(config.lookup.timeout, 15),
                retries=2,
                use_tor=config.tor.enabled,
            ) as client:
                response = await client.get_response(
                    url, headers={"User-Agent": BROWSER_UA}
                )
        except Exception as e:
            logger.warning(f"Spam lookup failed: {e}")
            return None

        if response is None:
            return None

        status, body = response
        if status != 200 or not body:
            # Site changed/blocked: report honestly, no fake score
            logger.info(f"Spam lookup got HTTP {status} for {phone}")
            return SpamResult(
                source="shouldianswer",
                number=phone,
                url=url,
                rating="unknown",
            )

        parsed = parse_shouldianswer(body)

        # "No reports" pages still parse to unknown/0 - keep them anyway
        # so the caller can link to the source.
        return SpamResult(
            source="shouldianswer",
            number=phone,
            url=url,
            rating=parsed["rating"],
            total_reports=parsed["total_reports"],
            positive=parsed["positive"],
            negative=parsed["negative"],
            categories=parsed["categories"],
        )
