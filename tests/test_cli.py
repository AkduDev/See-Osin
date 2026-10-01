"""P4 tests: CLI flags consistency, config --show and .env loading."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from see.cli import _validate_format, app

runner = CliRunner()


# ============================================================================
# CLI commands
# ============================================================================


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0


def test_phone_validate_command():
    result = runner.invoke(app, ["phone-validate", "+34612345678"])

    assert result.exit_code == 0
    assert "E.164" in result.output
    assert "+34612345678" in result.output


def test_config_show_lists_all_keys():
    result = runner.invoke(app, ["config", "--show"])

    assert result.exit_code == 0
    for label in ("NumVerify", "Hunter", "DeHashed", "HIBP", "Output directory"):
        assert label in result.output


def test_email_disposable_has_output_and_format_flags():
    result = runner.invoke(app, ["email-disposable", "--help"])

    assert result.exit_code == 0
    assert "--format" in result.output
    assert "--output" in result.output


def test_validate_format_rejects_typo():
    with pytest.raises(typer.BadParameter):
        _validate_format("jsn")

    assert _validate_format("json") == "json"
    assert _validate_format("both") == "both"


def test_invalid_format_rejected_before_any_scan():
    # Fails fast (click Choice or early manual check) - no network call happens
    result = runner.invoke(app, ["phone-scan", "+34612345678", "--format", "jsn"])
    assert result.exit_code != 0


def test_scan_commands_expose_tor_flags():
    for command in ("phone-scan", "email-scan"):
        result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0
        assert "--tor" in result.output
        assert "--no-tor" in result.output


# ============================================================================
# .env loading (README tells users to create .env - it must actually work)
# ============================================================================


def test_dotenv_file_is_loaded(tmp_path: Path, monkeypatch):
    from see.utils.config import load_config

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text('SEE_HIBP_KEY="from-dotfile"\n', encoding="utf-8")

    try:
        config = load_config()
        assert config.api_keys.hibp == "from-dotfile"
    finally:
        # load_config writes to os.environ; clean up so nothing leaks
        os.environ.pop("SEE_HIBP_KEY", None)


def test_real_env_wins_over_dotenv(tmp_path: Path, monkeypatch):
    from see.utils.config import load_config

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("SEE_HIBP_KEY=from-dotfile\n", encoding="utf-8")
    monkeypatch.setenv("SEE_HIBP_KEY", "from-environment")

    config = load_config()
    assert config.api_keys.hibp == "from-environment"


def test_dotenv_ignores_comments_and_blank_lines(tmp_path: Path, monkeypatch):
    from see.utils.config import load_config

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "# comment\n\nexport SEE_HUNTER_KEY=exported_value\n", encoding="utf-8"
    )

    try:
        config = load_config()
        assert config.api_keys.hunter == "exported_value"
    finally:
        os.environ.pop("SEE_HUNTER_KEY", None)
