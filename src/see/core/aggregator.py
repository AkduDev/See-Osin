"""Module aggregator for See OSINT tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from see.core.parser import PhoneInfo
from see.core.constants import MODULE_TARGET_FIELDS, OWNER_MODULES, DEFAULT_MODULES
from see.modules.base import BaseModule
from see.utils.config import AppConfig, load_config
from see.utils.logger import get_logger

logger = get_logger("aggregator")


@dataclass
class OSINTResult:
    """Complete OSINT result for a phone number."""

    input_number: str
    parsed: PhoneInfo | None = None
    owner: dict[str, Any] | None = None
    carrier: dict[str, Any] | None = None
    location: dict[str, Any] | None = None
    social_profiles: dict[str, Any] | None = None
    search_dorks: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)
    modules_used: list[str] = field(default_factory=list)
    query_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {
            "input": self.input_number,
            "query_time": self.query_time,
            "modules_used": self.modules_used,
            "errors": self.errors if self.errors else [],
        }

        if self.parsed:
            result["number"] = {
                "e164": self.parsed.e164,
                "national": self.parsed.national,
                "international": self.parsed.international,
                "valid": self.parsed.is_valid,
                "possible": self.parsed.is_possible,
                "type": self.parsed.number_type,
            }
            result["country"] = {
                "code": self.parsed.country,
                "country_code": f"+{self.parsed.country_code}",
            }

        # Add non-None result fields
        for field_name in ("owner", "carrier", "location", "social_profiles", "search_dorks"):
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value

        return result


class ModuleAggregator:
    """
    Aggregates results from multiple OSINT modules.

    Features:
    - Auto-registration of built-in modules
    - Target field-based result merging (no hardcoded module names)
    - Automatic availability checking
    """

    def __init__(self, config: AppConfig | None = None):
        self.config = config or load_config()
        self._modules: dict[str, BaseModule] = {}

        # Auto-register built-in modules
        self._register_builtin_modules()

    def _register_builtin_modules(self) -> None:
        """Register all built-in modules."""
        from see.modules import (
            PhonenumbersModule,
            NumVerifyModule,
            NumLookupModule,
            AbstractPersonModule,
            MaigretModule,
            GoogleDorksModule,
            ReverseLookupModule,
            SocialMediaModule,
        )

        builtin_modules = [
            PhonenumbersModule(),
            NumVerifyModule(),
            NumLookupModule(),
            AbstractPersonModule(),
            MaigretModule(),
            GoogleDorksModule(),
            ReverseLookupModule(),
            SocialMediaModule(),
        ]

        for module in builtin_modules:
            self.register_module(module)

    def register_module(self, module: BaseModule) -> None:
        """
        Register an OSINT module.

        Args:
            module: Module instance implementing BaseModule interface
        """
        self._modules[module.name] = module
        logger.debug(f"Registered module: {module.name} -> {module.target_field}")

    def get_module(self, name: str) -> BaseModule | None:
        """Get a registered module by name."""
        return self._modules.get(name)

    @property
    def available_modules(self) -> list[str]:
        """List of module names that are available (have required keys)."""
        return [name for name, m in self._modules.items() if m.is_available]

    async def run_lookup(
        self,
        phone_info: PhoneInfo,
        modules: list[str] | None = None,
    ) -> OSINTResult:
        """
        Run registered modules and aggregate results.

        Args:
            phone_info: Parsed phone number information
            modules: Optional list of specific modules to run.
                     If None, uses default modules from config.

        Returns:
            OSINTResult with aggregated data
        """
        result = OSINTResult(input_number=phone_info.original, parsed=phone_info)

        enabled_modules = modules or self.config.lookup.modules
        logger.info(f"Running lookup with modules: {enabled_modules}")

        tasks = []
        for module_name in enabled_modules:
            module = self._modules.get(module_name)
            if module is None:
                logger.warning(f"Module '{module_name}' not registered, skipping")
                result.errors.append(f"Module '{module_name}' not available")
                continue

            if not module.is_available:
                logger.info(f"Module '{module_name}' not available (missing API key?), skipping")
                continue

            tasks.append(self._run_module(module, phone_info, result))

        if tasks:
            import asyncio
            await asyncio.gather(*tasks, return_exceptions=True)

        return result

    async def run_owner_lookup(self, phone_info: PhoneInfo) -> OSINTResult:
        """Run owner-specific lookup modules."""
        return await self.run_lookup(phone_info, modules=OWNER_MODULES)

    async def _run_module(
        self,
        module: BaseModule,
        phone_info: PhoneInfo,
        result: OSINTResult,
    ) -> None:
        """Run a single module and update result using target_field."""
        try:
            logger.info(f"Running module: {module.name}")
            data = await module.lookup(phone_info, self.config)

            if data:
                result.modules_used.append(module.name)
                self._merge_result(module.target_field, data, result)
                logger.info(f"Module {module.name} completed successfully")
            else:
                logger.debug(f"Module {module.name} returned no data")

        except Exception as e:
            error_msg = f"Module {module.name} failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    def _merge_result(self, target_field: str, data: dict, result: OSINTResult) -> None:
        """
        Merge module result into OSINTResult using target_field.

        This is the single point of merge logic - no hardcoded module names.
        """
        current = getattr(result, target_field)
        if current is None:
            setattr(result, target_field, data)
        else:
            # Merge dictionaries if both are dicts
            if isinstance(current, dict) and isinstance(data, dict):
                current.update(data)
            else:
                # Replace if not mergeable
                setattr(result, target_field, data)
