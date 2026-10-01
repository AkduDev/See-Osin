"""Configuration management for See OSINT tool."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel


class APIKeys(BaseModel):
    """API keys for external services."""

    numverify: str = ""
    abstract: str = ""
    numlookup: str = ""
    hunter: str = ""
    dehashed: str = ""
    hibp: str = ""
    # DeHashed uses HTTP Basic auth (account email as username, API key as password)
    dehashed_email: str = ""


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
    modules: List[str] = ["phones"]


class OutputConfig(BaseModel):
    """Output settings."""

    default_format: str = "both"
    directory: Path = Path("./results")


class RateLimitConfig(BaseModel):
    """Rate limiting settings."""

    numverify_per_minute: int = 10
    hibp_delay_seconds: float = 3.0


class AppConfig(BaseModel):
    """Main application configuration."""

    api_keys: APIKeys = APIKeys()
    tor: TorConfig = TorConfig()
    lookup: LookupConfig = LookupConfig()
    output: OutputConfig = OutputConfig()
    rate_limit: RateLimitConfig = RateLimitConfig()


def _load_dotenv(path: Path | None = None) -> None:
    """
    Load KEY=VALUE pairs from a local .env file into os.environ.

    Real environment variables always win (a key already set is never
    overwritten). No external dependency: simple parser for the format
    documented in .env.example (comments, optional ``export`` prefix,
    optional quotes).
    """
    path = path or Path(".env")
    if not path.is_file():
        return

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration with priority:
    1. Environment variables (highest)
    2. .env file (real environment always wins)
    3. Config file
    4. Default values (lowest)
    """
    _load_dotenv()

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

    # Override with environment variables (SEE_ prefix wins, bare name as alias
    # for README compatibility: e.g. HUNTER_API_KEY vs SEE_HUNTER_KEY)
    def _set_api_key(*env_names: str, field: str) -> None:
        for name in env_names:
            value = os.environ.get(name)
            if value:
                if "api_keys" not in config_data:
                    config_data["api_keys"] = {}
                config_data["api_keys"][field] = value
                break

    _set_api_key("SEE_NUMVERIFY_KEY", "NUMVERIFY_API_KEY", field="numverify")
    _set_api_key("SEE_ABSTRACT_KEY", "ABSTRACT_API_KEY", field="abstract")
    _set_api_key("SEE_NUMLOOKUP_KEY", "NUMLOOKUP_API_KEY", field="numlookup")
    _set_api_key("SEE_HUNTER_KEY", "HUNTER_API_KEY", field="hunter")
    _set_api_key("SEE_HIBP_KEY", "HIBP_API_KEY", field="hibp")
    _set_api_key("SEE_DEHASHED_KEY", "DEHASHED_API_KEY", field="dehashed")
    _set_api_key("SEE_DEHASHED_EMAIL", "DEHASHED_EMAIL", field="dehashed_email")

    # Tor environment variables
    def _set_tor(env_name: str, field: str, parse_bool: bool = False) -> None:
        value = os.environ.get(env_name)
        if value:
            if "tor" not in config_data:
                config_data["tor"] = {}
            if parse_bool:
                config_data["tor"][field] = value.lower() in ("true", "1", "yes")
            elif value.isdigit():
                config_data["tor"][field] = int(value)
            else:
                config_data["tor"][field] = value

    _set_tor("SEE_TOR_ENABLED", "enabled", parse_bool=True)
    _set_tor("SEE_TOR_SOCKS_PORT", "socks_port")
    _set_tor("SEE_TOR_CONTROL_PORT", "control_port")

    # Output overrides
    output_dir = os.environ.get("SEE_OUTPUT_DIR")
    if output_dir:
        if "output" not in config_data:
            config_data["output"] = {}
        config_data["output"]["directory"] = output_dir

    return AppConfig(**config_data)
