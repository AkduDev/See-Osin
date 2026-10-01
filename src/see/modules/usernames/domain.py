"""Username OSINT domain (Sherlock-style social media search)."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from see.core.types import UsernameResult
from see.modules.base import BaseModule
from see.modules.usernames.providers import SherlockLikeProvider
from see.utils.config import AppConfig, load_config
from see.utils.logger import get_logger

logger = get_logger("username_domain")

USERNAME_REGEX = r"^[a-zA-Z0-9_.-]{2,64}$"


class UsernameDomain(BaseModule):
    """
    Username OSINT domain.

    Coordinates providers that search for a username across
    social media platforms (own Sherlock-style implementation).
    """

    def __init__(self, config: AppConfig | None = None):
        self.config = config or load_config()
        self.providers = self._init_providers()

    def _init_providers(self) -> list:
        """Initialize available providers."""
        providers = [SherlockLikeProvider()]

        available = [p for p in providers if p.is_available]
        logger.info(f"Loaded {len(available)} username providers: {[p.name for p in available]}")

        return available

    @property
    def name(self) -> str:
        return "usernames"

    @property
    def description(self) -> str:
        return "Username OSINT - search social media profiles by username"

    @property
    def domain(self) -> str:
        return "usernames"

    @property
    def is_available(self) -> bool:
        """Check if at least one provider is available."""
        return len(self.providers) > 0

    async def scan(
        self,
        username: str,
        modules: list[str] | None = None,
        use_tor: bool | None = None,
        use_cache: bool = True,
    ) -> UsernameResult:
        """
        Search for a username across social platforms.

        Args:
            username: Username to search (e.g. "john_doe")
            modules: Optional list of specific providers to use
            use_tor: Optional override to route requests through Tor.
                When None, the value in the config file is used.
            use_cache: Whether to serve repeat scans from the in-memory cache.

        Returns:
            UsernameResult with all found profiles
        """
        username = username.strip()

        result = UsernameResult(
            source="usernames",
            input_username=username,
        )

        if not self._is_valid_username(username):
            error_msg = "Invalid username: must be 2-64 chars using letters, digits, _ - ."
            logger.warning(error_msg)
            result.errors.append(error_msg)
            result.success = False
            return result

        providers = self.providers
        if modules:
            providers = [p for p in providers if p.name in modules]

        tasks = [
            self._run_provider(p, username, result, use_tor, use_cache)
            for p in providers
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        result.found_count = sum(1 for p in result.profiles if p.found)
        result.not_found_count = sum(1 for p in result.profiles if p.status == "not_found")
        result.platforms_checked = len(result.profiles)

        logger.info(
            f"Username scan complete: {result.found_count} found, "
            f"{result.not_found_count} not found, {result.platforms_checked} checked"
        )

        return result

    def _is_valid_username(self, username: str) -> bool:
        """Validate username format."""
        return bool(re.match(USERNAME_REGEX, username))

    async def _run_provider(
        self,
        provider: Any,
        username: str,
        result: UsernameResult,
        use_tor: bool | None = None,
        use_cache: bool = True,
    ) -> None:
        """Run a single provider and update result."""
        try:
            logger.info(f"Running provider: {provider.name}")
            profiles = await provider.get_profiles(
                username, self.config, use_tor=use_tor, use_cache=use_cache
            )

            if profiles:
                result.profiles.extend(profiles)
                result.modules_used.append(provider.name)

            logger.info(f"Provider {provider.name} completed")
        except Exception as e:
            error_msg = f"Provider {provider.name} failed: {e!s}"
            logger.error(error_msg)
            result.errors.append(error_msg)


# Module instance for registration
username_module = UsernameDomain()
