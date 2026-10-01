"""Tests for P1 (blocking bugs), P2 (stubs) and P3 (new providers) fixes."""

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


# ============================================================================
# P3 - HIBP provider
# ============================================================================


def test_hibp_payload_mapping():
    from see.modules.emails.providers.hibp import parse_hibp_payload

    payload = [
        {
            "Name": "Adobe",
            "Title": "Adobe",
            "Domain": "adobe.com",
            "BreachDate": "2013-10-04",
            "PwnCount": 152445165,
            "DataClasses": ["Email addresses", "Passwords"],
        },
        {
            "Name": "LinkedIn",
            "Title": None,
            "Domain": "linkedin.com",
            "BreachDate": "2012-05-05",
            "PwnCount": 164620,
            "DataClasses": ["Email addresses"],
        },
    ]

    result = parse_hibp_payload(payload, "test@example.com")

    assert result is not None
    assert result.source == "hibp"
    assert result.email == "test@example.com"
    assert result.total_breaches == 2
    assert result.breaches[0]["name"] == "Adobe"
    assert result.breaches[0]["pwn_count"] == 152445165
    # Title is null -> falls back to Name
    assert result.breaches[1]["name"] == "LinkedIn"
    assert result.sources == ["adobe.com", "linkedin.com"]


def test_hibp_empty_payload_returns_none():
    from see.modules.emails.providers.hibp import parse_hibp_payload

    assert parse_hibp_payload([], "a@b.com") is None


def test_hibp_requires_api_key():
    from see.modules.emails.providers.hibp import HIBPProvider
    from see.utils.config import AppConfig

    config = AppConfig()
    provider = HIBPProvider(config)
    assert provider.is_available is False

    config.api_keys.hibp = "0123456789abcdef0123456789abcdef"
    assert HIBPProvider(config).is_available is True


def test_email_domain_registers_hibp_only_with_key():
    from see.modules.emails.domain import EmailDomain
    from see.utils.config import AppConfig

    config = AppConfig()
    names = [p.name for p in EmailDomain(config).providers]
    assert "hibp" not in names

    config.api_keys.hibp = "test-key"
    names = [p.name for p in EmailDomain(config).providers]
    assert "hibp" in names


def test_config_reads_hibp_key_env(monkeypatch):
    from see.utils.config import load_config

    monkeypatch.setenv("SEE_HIBP_KEY", "abcdef1234567890")
    config = load_config()
    assert config.api_keys.hibp == "abcdef1234567890"


# ============================================================================
# P3 - Spam provider (Should I Answer scraping)
# ============================================================================

_SAMPLE_SIA_PAGE = """
<html><body>
  <h1>612345678</h1>
  <span>NEGATIVA VENDEDOR TELEFONICO</span>
  <p>Numero de telefono 612345678 tiene evaluacion negativa.</p>
  <div>5x negativa3x positiva</div>
  <div>Categorias</div>
  <div>4x Vendedor telefonico1x Servicios financieros</div>
</body></html>
"""


def test_spam_parser_reads_rating_counts_categories():
    from see.modules.phones.providers.spam import parse_shouldianswer

    parsed = parse_shouldianswer(_SAMPLE_SIA_PAGE)

    assert parsed["rating"] == "negative"
    assert parsed["negative"] == 5
    assert parsed["positive"] == 3
    assert parsed["total_reports"] >= 8
    assert any("Vendedor" in c for c in parsed["categories"])
    # Rating words are not categories
    assert not any("negativa" in c.lower() for c in parsed["categories"])


def test_spam_parser_unknown_when_nothing_recognizable():
    from see.modules.phones.providers.spam import parse_shouldianswer

    parsed = parse_shouldianswer("<html><body>Nothing here</body></html>")

    assert parsed["rating"] == "unknown"
    assert parsed["total_reports"] == 0
    assert parsed["categories"] == []


def test_phone_domain_has_spam_and_dorks_providers():
    from see.modules.phones.domain import PhoneDomain

    names = [p.name for p in PhoneDomain().providers]
    assert "spam" in names
    assert "dorks" in names


# ============================================================================
# P3 - Dorks / investigation links
# ============================================================================


def test_dorks_builds_search_links():
    from see.modules.phones.providers.dorks import build_search_links

    links = build_search_links("+34612345678")

    assert len(links) >= 8
    urls = [lnk.url for lnk in links]
    assert any("google.com/search" in u for u in urls)
    assert any("tellows" in u for u in urls)
    assert all(lnk.status == "check_manually" for lnk in links)
    assert build_search_links("") == []


def test_phone_result_serializes_spam_and_search_links():
    from see.core.types import PhoneResult, SocialResult, SpamResult

    result = PhoneResult(input_number="+34612345678")
    result.spam = SpamResult(
        source="shouldianswer",
        rating="negative",
        total_reports=8,
        positive=3,
        negative=5,
        url="https://www.shouldianswer.co.uk/search?q=%2B34612345678",
    )
    result.search_links = [
        SocialResult(
            source="dorks",
            platform="dork_google_exact",
            url="https://www.google.com/search?q=x",
            status="check_manually",
        )
    ]

    data = result.to_dict()
    assert data["spam"]["rating"] == "negative"
    assert data["spam"]["negative"] == 5
    assert data["search_links"][0]["platform"] == "dork_google_exact"


# ============================================================================
# P3 - Constants cleanup (orphan module references)
# ============================================================================


def test_constants_have_no_orphan_modules():
    from see.core.constants import DEFAULT_MODULES, MODULE_TARGET_FIELDS, OWNER_MODULES

    assert "maigret" not in DEFAULT_MODULES + OWNER_MODULES
    assert "google_dorks" not in MODULE_TARGET_FIELDS
    assert "social_media" not in MODULE_TARGET_FIELDS
    assert "opencellid" not in MODULE_TARGET_FIELDS
    assert MODULE_TARGET_FIELDS["hibp"] == "breaches"
    assert MODULE_TARGET_FIELDS["dorks"] == "search_links"
