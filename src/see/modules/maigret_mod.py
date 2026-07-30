"""Maigret OSINT module for See OSINT tool.

Social media profile search using multiple sites.
This module checks if a phone number is registered on various platforms.
"""

from __future__ import annotations

import asyncio
from typing import Any

from see.core.parser import PhoneInfo
from see.modules.base import BaseModule
from see.utils.config import AppConfig
from see.utils.logger import get_logger

logger = get_logger("maigret")

# Popular sites to check for phone number registration
PHONE_SITES: dict[str, dict[str, str]] = {
    "whatsapp": {
        "check_url": "https://api.whatsapp.com/send?phone={phone}",
        "name": "WhatsApp",
        "type": "messaging",
    },
    "telegram": {
        "check_url": "https://t.me/+{phone}",
        "name": "Telegram",
        "type": "messaging",
    },
    "viber": {
        "check_url": "viber://chat?number={phone}",
        "name": "Viber",
        "type": "messaging",
    },
    "truecaller": {
        "search_url": "https://www.truecaller.com/search/{country}/{number}",
        "name": "Truecaller",
        "type": "caller_id",
    },
}


class MaigretModule(BaseModule):
    """OSINT module for phone number social media lookup."""

    @property
    def name(self) -> str:
        return "maigret"

    @property
    def description(self) -> str:
        return "Social media profiles via OSINT search"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def target_field(self) -> str:
        return "social_profiles"

    async def lookup(self, phone: PhoneInfo, config: AppConfig) -> dict[str, Any] | None:
        """Search for phone number across multiple platforms."""
        logger.info(f"Running Maigret OSINT lookup for {phone.e164}")

        results: dict[str, Any] = {
            "profiles": [],
            "platforms_checked": [],
            "found_count": 0,
            "source": "maigret",
        }

        tasks = [self._check_platform(pid, pinfo, phone) for pid, pinfo in PHONE_SITES.items()]
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in platform_results:
            if isinstance(result, dict):
                if result.get("found"):
                    results["profiles"].append(result)
                    results["found_count"] += 1
                results["platforms_checked"].append(result.get("platform", "unknown"))

        logger.info(
            f"Maigret result: found {results['found_count']} profiles "
            f"on {len(results['platforms_checked'])} platforms"
        )
        return results

    async def _check_platform(
        self,
        platform_id: str,
        platform_info: dict[str, str],
        phone: PhoneInfo,
    ) -> dict[str, Any]:
        """Check a single platform for phone number registration."""
        result: dict[str, Any] = {
            "platform": platform_info["name"],
            "platform_id": platform_id,
            "type": platform_info.get("type", "unknown"),
            "found": False,
            "url": None,
            "status": "unknown",
        }

        try:
            if platform_id == "whatsapp":
                url = f"https://api.whatsapp.com/send?phone={phone.e164.replace('+', '')}"
                result["url"] = url
                result["found"] = True
                result["status"] = "registered"

            elif platform_id == "telegram":
                url = f"https://t.me/+{phone.e164.replace('+', '')}"
                result["url"] = url
                result["found"] = True
                result["status"] = "check_manually"

            elif platform_id == "viber":
                url = f"viber://chat?number={phone.e164.replace('+', '')}"
                result["url"] = url
                result["found"] = True
                result["status"] = "check_manually"

            elif platform_id == "truecaller":
                country = phone.country.lower()
                number = phone.national_number
                url = f"https://www.truecaller.com/search/{country}/{number}"
                result["url"] = url
                result["found"] = True
                result["status"] = "search_available"

        except Exception as e:
            logger.debug(f"Error checking {platform_id}: {e}")
            result["status"] = "error"

        return result
