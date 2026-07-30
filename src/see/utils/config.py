"""Configuration management for See OSINT tool."""

import os
from pathlib import Path
from typing import Optional, List

import yaml
from pydantic import BaseModel


class APIKeys(BaseModel):
    """API keys for external services."""

    numverify: str = ""
    abstract: str = ""
    opencellid: str = ""


class TorConfig(BaseModel):
    """Tor proxy configuration."""

    enabled: bool = False
    socks_port: int = 9050
    control_port: int = 9051
    max_requests_per_circuit: int = 10
    auto_rotate: bool = True
    exit_countries: List[str] = []


class LookupConfig(BaseModel):
    """Lookup settings."""

    timeout: int = 30
    retries: int = 3
    modules: List[str] = ["phonenumbers", "numverify"]


class OutputConfig(BaseModel):
    """Output settings."""

    default_format: str = "both"
    directory: Path = Path("./results")


class RateLimitConfig(BaseModel):
    """Rate limiting settings."""

    numverify_per_minute: int = 10
    opencellid_per_minute: int = 10
    hibp_delay_seconds: float = 3.0


class AppConfig(BaseModel):
    """Main application configuration."""

    api_keys: APIKeys = APIKeys()
    tor: TorConfig = TorConfig()
    lookup: LookupConfig = LookupConfig()
    output: OutputConfig = OutputConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration with priority:
    1. Environment variables (highest)
    2. Config file
    3. Default values (lowest)
    """
    config_data = {}

    search_paths = [
        config_path,
        Path("config.yaml"),
        Path.home() / ".config" / "see" / "config.yaml",
    ]

    for path in search_paths:
        if path and path.exists():
            with open(path) as f:
                config_data = yaml.safe_load(f) or {}
            break

    # Override with environment variables
    env_key = os.environ.get("SEE_NUMVERIFY_KEY")
    if env_key:
        if "api_keys" not in config_data:
            config_data["api_keys"] = {}
        config_data["api_keys"]["numverify"] = env_key

    env_key = os.environ.get("SEE_ABSTRACT_KEY")
    if env_key:
        if "api_keys" not in config_data:
            config_data["api_keys"] = {}
        config_data["api_keys"]["abstract"] = env_key

    # Tor environment variables
    tor_enabled = os.environ.get("SEE_TOR_ENABLED")
    if tor_enabled:
        if "tor" not in config_data:
            config_data["tor"] = {}
        config_data["tor"]["enabled"] = tor_enabled.lower() in ("true", "1", "yes")

    return AppConfig(**config_data)
