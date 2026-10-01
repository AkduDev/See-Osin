"""Tests for P1 (blocking bugs) and P2 (stubs) fixes."""

from __future__ import annotations

from pathlib import Path

from see.core.types import PhoneResult

# ============================================================================
# P1 - JSONFormatter
# ============================================================================


def test_json_formatter_saves_result_object(tmp_path: Path):
    from see.output.json_formatter import JSONFormatter

    fmt = JSONFormatter(output_dir=tmp_path)
    result = PhoneResult(input_number="+34612345678")

    path = fmt.save(result, "out.json")

    assert path.exists()
    assert path.parent == tmp_path


def test_json_formatter_saves_dict(tmp_path: Path):
    from see.output.json_formatter import JSONFormatter

    fmt = JSONFormatter(output_dir=tmp_path)
    result = PhoneResult(input_number="+34612345678")

    path = fmt.save(result.to_dict(), "out.json")

    assert path.exists()


def test_json_formatter_accepts_path_with_subdir(tmp_path: Path):
    from see.output.json_formatter import JSONFormatter

    fmt = JSONFormatter(output_dir=tmp_path)
    target = tmp_path / "nested" / "deep" / "out.json"

    path = fmt.save(PhoneResult(input_number="x"), target)

    assert path == target
    assert path.exists()


def test_json_formatter_output_dir_accepts_str(tmp_path: Path):
    from see.output.json_formatter import JSONFormatter

    fmt = JSONFormatter(output_dir=str(tmp_path))

    assert fmt.output_dir == Path(tmp_path)


# ============================================================================
# P1 - Config env aliases
# ============================================================================
# NOTE: tests use monkeypatch so the real environment never leaks in.


def test_config_reads_see_and_bare_env_aliases(monkeypatch):
    from see.utils.config import load_config

    monkeypatch.setenv("SEE_HUNTER_KEY", "hunter_see")
    monkeypatch.setenv("DEHASHED_API_KEY", "dehashed_bare")
    monkeypatch.delenv("SEE_DEHASHED_KEY", raising=False)

    config = load_config(config_path=Path("nonexistent.yaml"))

    assert config.api_keys.hunter == "hunter_see"
    assert config.api_keys.dehashed == "dehashed_bare"


def test_config_reads_tor_and_output_env(monkeypatch):
    from see.utils.config import load_config

    monkeypatch.setenv("SEE_TOR_ENABLED", "true")
    monkeypatch.setenv("SEE_TOR_SOCKS_PORT", "9150")
    monkeypatch.setenv("SEE_OUTPUT_DIR", "./custom_results")

    config = load_config(config_path=Path("nonexistent.yaml"))

    assert config.tor.enabled is True
    assert config.tor.socks_port == 9150
    assert config.output.directory == Path("./custom_results")


# ============================================================================
# P1 - Engine registry
# ============================================================================


def test_engine_registers_modules():
    from see.core.engine import SeeEngine

    engine = SeeEngine()
    domains = engine.get_available_domains()

    assert "phones" in domains
    assert "emails" in domains
    assert "usernames" in domains


def test_engine_has_scan_email():
    from see.core.engine import SeeEngine

    assert hasattr(SeeEngine(), "scan_email")


def test_engine_generic_scan_unknown_domain_raises():
    import asyncio

    from see.core.engine import SeeEngine

    engine = SeeEngine()
    try:
        asyncio.run(engine.scan("target", domain="nonexistent"))
    except ValueError as e:
        assert "nonexistent" in str(e)
    else:  # pragma: no cover
        raise AssertionError("Expected ValueError")


def test_module_aggregator_does_not_crash():
    from see.core.aggregator import ModuleAggregator

    agg = ModuleAggregator()
    assert agg.available_modules == []


# ============================================================================
# P2 - Holehe
# ============================================================================


def test_holehe_mapping_pure():
    from see.modules.emails.providers.holehe import holehe_out_to_breaches

    out = [
        {"name": "github", "domain": "github.com", "method": "other",
         "exists": True, "others": None},
        {"name": "twitter", "domain": "twitter.com", "method": "other",
         "exists": False, "others": None},
        {"name": "imgur", "domain": "imgur.com", "method": "other",
         "exists": True, "others": {"FullName": "John"}},
    ]

    result = holehe_out_to_breaches(out, "a@b.com")

    assert result is not None
    assert result.total_breaches == 2
    assert "github.com" in result.sources
    assert "imgur.com" in result.sources
    assert "twitter.com" not in result.sources


def test_holehe_mapping_empty_returns_none():
    from see.modules.emails.providers.holehe import holehe_out_to_breaches

    assert holehe_out_to_breaches([], "a@b.com") is None
    assert holehe_out_to_breaches(
        [{"name": "x", "domain": "x.com", "exists": False}], "a@b.com"
    ) is None


# ============================================================================
# P2 - SMTP
# ============================================================================


def test_smtp_verify_rejects_invalid_email():
    import asyncio

    from see.modules.emails.providers.smtp import SMTPProvider
    from see.utils.config import load_config

    provider = SMTPProvider()
    result = asyncio.run(provider.verify_deliverability("no-at-sign", load_config()))

    assert result is None
    assert provider.supports_verification is True
    # Deliverability check must NOT claim to be a disposable check
    assert provider.supports_disposable is False


# ============================================================================
# P2 - Social URL formatting
# ============================================================================


def test_social_fmt_url_ignores_unknown_placeholders():
    from see.modules.emails.providers.social import SocialEmailProvider

    # discord uses {user_id} which we cannot resolve from an email
    url = SocialEmailProvider._fmt_url(
        "https://discord.com/users/{user_id}", "a@b.com", "alice"
    )
    assert "{user_id}" in url  # placeholder left as-is, no KeyError

    url2 = SocialEmailProvider._fmt_url(
        "https://x.com/{username}", "a@b.com", "alice"
    )
    assert url2 == "https://x.com/alice"


# ============================================================================
# P2 - DeHashed auth
# ============================================================================


def test_dehashed_uses_basic_auth():
    import base64

    from see.modules.emails.providers.dehashed import DeHashedProvider
    from see.utils.config import AppConfig

    config = AppConfig()
    config.api_keys.dehashed = "secret"
    config.api_keys.dehashed_email = "me@example.com"

    provider = DeHashedProvider(config)
    headers = provider._auth_headers(config)

    assert headers is not None
    assert headers["Authorization"].startswith("Basic ")
    decoded = base64.b64decode(headers["Authorization"].split(" ", 1)[1]).decode()
    assert decoded == "me@example.com:secret"

    assert provider.is_available is True


def test_dehashed_unavailable_without_account_email():
    from see.modules.emails.providers.dehashed import DeHashedProvider
    from see.utils.config import AppConfig

    config = AppConfig()
    config.api_keys.dehashed = "secret"

    provider = DeHashedProvider(config)
    assert provider.is_available is False
    assert provider._auth_headers(config) is None
