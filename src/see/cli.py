"""CLI entry point for See OSINT framework."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from see import __version__
from see.core.engine import SeeEngine
from see.logo import LOGO
from see.output.json_formatter import JSONFormatter
from see.output.rich_display import RichDisplay
from see.utils.config import load_config

app = typer.Typer(
    name="see",
    help="See OSINT Framework - Phone, Email, Domain intelligence",
    no_args_is_help=False,
)

console = Console()

FormatOption = Literal["json", "display", "both"]


def _validate_format(output_format: str) -> str:
    """Reject unknown --format values early (before any network call)."""
    if output_format not in ("json", "display", "both"):
        raise typer.BadParameter(
            "format must be one of: json, display, both", param_hint="--format"
        )
    return output_format


def _emit_result(result, display_fn, output, output_format, output_dir) -> None:
    """
    Render a scan result: display, JSON to stdout and/or save to a file.

    Shared by all scan commands so output behavior stays consistent.
    """
    if output_format in ("display", "both"):
        display_fn(result)

    if output_format in ("json", "both"):
        if output:
            filepath = JSONFormatter(output_dir=output_dir).save(result, output)
            typer.echo(f"\nResults saved to {filepath}", err=True)
        elif output_format == "json":
            typer.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


def _configure_console_encoding() -> None:
    """Avoid UnicodeEncodeError on legacy Windows consoles (cp1252).

    Rich prints emoji in panel titles; when stdout/stderr use a legacy
    codepage and errors='strict', rendering crashes. Replace instead.
    """
    import sys

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")  # type: ignore[union-attr]
        except (AttributeError, ValueError):  # pragma: no cover - exotic streams
            pass


def _show_logo() -> None:
    """Display the See logo in terminal."""
    console.print(LOGO, style="bold cyan")
    console.print(f"  OSINT Framework v{__version__}\n", style="dim")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """See OSINT Framework - Intelligence gathering tool."""
    _configure_console_encoding()
    if ctx.invoked_subcommand is None:
        _show_logo()
        raise typer.Exit()


# ============================================================================
# Phone Commands
# ============================================================================


@app.command()
def phone_scan(
    number: str = typer.Argument(help="Phone number (e.g., +34612345678)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
    tor: bool | None = typer.Option(None, "--tor/--no-tor", help="Force Tor on/off (default: config)"),
) -> None:
    """Complete phone number scan."""
    asyncio.run(_phone_scan(number, output, output_format, "scan", tor))


@app.command()
def phone_carrier(
    number: str = typer.Argument(help="Phone number to check carrier"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Get carrier information."""
    asyncio.run(_phone_scan(number, output, output_format, "carrier"))


@app.command()
def phone_owner(
    number: str = typer.Argument(help="Phone number to find owner"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Find owner information."""
    asyncio.run(_phone_scan(number, output, output_format, "owner"))


@app.command()
def phone_spam(
    number: str = typer.Argument(help="Phone number to check for spam reports"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Check spam/scam reports for a phone number."""
    asyncio.run(_phone_scan(number, output, output_format, "spam"))


@app.command()
def phone_validate(
    number: str = typer.Argument(help="Phone number to validate"),
) -> None:
    """Validate a phone number format."""
    from see.modules.phones.domain import PhoneDomain
    
    domain = PhoneDomain()
    result = domain._parse_number(number)
    
    typer.echo("\n=== Phone Validation ===")
    typer.echo(f"Input:         {number}")
    typer.echo(f"E.164:         {result.get('e164', '')}")
    typer.echo(f"National:      {result.get('national', '')}")
    typer.echo(f"International: {result.get('international', '')}")
    typer.echo(f"Valid:         {'Yes' if result.get('valid') else 'No'}")
    typer.echo(f"Possible:      {'Yes' if result.get('possible') else 'No'}")
    typer.echo(f"Country:       {result.get('country', '')} (+{result.get('country_code', '')})")


async def _phone_scan(
    number: str,
    output: Path | None,
    output_format: str,
    scan_type: str,
    tor: bool | None = None,
) -> None:
    """Common phone scan implementation."""
    _validate_format(output_format)
    engine = SeeEngine()
    if tor is not None:
        engine.config.tor.enabled = tor
    
    if scan_type == "scan":
        result = await engine.scan_phone(number)
    elif scan_type == "carrier":
        from see.modules.phones.domain import PhoneDomain
        domain = PhoneDomain(engine.config)
        result = await domain.scan_carrier(number)
    elif scan_type == "owner":
        from see.modules.phones.domain import PhoneDomain
        domain = PhoneDomain(engine.config)
        result = await domain.scan_owner(number)
    elif scan_type == "spam":
        from see.modules.phones.domain import PhoneDomain
        domain = PhoneDomain(engine.config)
        result = await domain.scan_spam(number)
    else:
        raise ValueError(f"Unknown scan type: {scan_type}")
    
    _emit_result(
        result, RichDisplay().display_phone, output, output_format,
        engine.config.output.directory,
    )


# ============================================================================
# Email Commands
# ============================================================================


@app.command()
def email_scan(
    email: str = typer.Argument(help="Email address to scan"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
    tor: bool | None = typer.Option(None, "--tor/--no-tor", help="Force Tor on/off (default: config)"),
) -> None:
    """Complete email scan."""
    asyncio.run(_email_scan(email, output, output_format, "scan", tor))


@app.command()
def email_breaches(
    email: str = typer.Argument(help="Email address to check breaches"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Check email breaches."""
    asyncio.run(_email_scan(email, output, output_format, "breaches"))


@app.command()
def email_social(
    email: str = typer.Argument(help="Email address to find social profiles"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Find social media profiles by email."""
    asyncio.run(_email_scan(email, output, output_format, "social"))


@app.command()
def email_disposable(
    email: str = typer.Argument(help="Email address to check if disposable"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Check if email is disposable."""
    asyncio.run(_email_scan(email, output, output_format, "disposable"))


@app.command()
def email_verify(
    email: str = typer.Argument(help="Email address to verify (SMTP, no mail sent)"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Verify email deliverability via SMTP (RCPT TO, no mail sent)."""
    asyncio.run(_email_scan(email, output, output_format, "verify"))


async def _email_scan(
    email: str,
    output: Path | None,
    output_format: str,
    scan_type: str,
    tor: bool | None = None,
) -> None:
    """Common email scan implementation."""
    from see.core.engine import SeeEngine
    from see.modules.emails.domain import EmailDomain

    _validate_format(output_format)
    engine = SeeEngine()
    if tor is not None:
        engine.config.tor.enabled = tor
    domain = EmailDomain(engine.config)
    
    if scan_type == "scan":
        result = await domain.scan(email)
    elif scan_type == "breaches":
        result = await domain.scan_breaches(email)
    elif scan_type == "social":
        result = await domain.scan_social(email)
    elif scan_type == "disposable":
        result = await domain.scan_disposable(email)
    elif scan_type == "verify":
        result = await domain.scan_verify(email)
    else:
        raise ValueError(f"Unknown scan type: {scan_type}")
    
    _emit_result(
        result, RichDisplay().display_email, output, output_format,
        engine.config.output.directory,
    )


# ============================================================================
# Username Commands (Sherlock-style)
# ============================================================================


@app.command()
def username_scan(
    username: str = typer.Argument(help="Username to search across social platforms"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
    tor: bool = typer.Option(False, "--tor", help="Route requests through Tor"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Bypass the in-memory result cache"),
) -> None:
    """Search a username across social media platforms (Sherlock-style)."""
    asyncio.run(_username_scan(username, output, output_format, tor, no_cache))


async def _username_scan(
    username: str,
    output: Path | None,
    output_format: str,
    tor: bool = False,
    no_cache: bool = False,
) -> None:
    """Common username scan implementation."""
    from see.core.engine import SeeEngine
    from see.modules.usernames.domain import UsernameDomain

    _validate_format(output_format)
    engine = SeeEngine()
    domain = UsernameDomain(engine.config)
    result = await domain.scan(
        username, use_tor=tor, use_cache=not no_cache
    )

    _emit_result(
        result, RichDisplay().display_username, output, output_format,
        engine.config.output.directory,
    )


# ============================================================================
# Legacy Commands (for backward compatibility)
# ============================================================================


@app.command()
def scan(
    phone: str = typer.Argument(help="Phone number to scan"),
    output: Path | None = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    output_format: FormatOption = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Legacy scan command (use 'phone-scan' instead)."""
    asyncio.run(_phone_scan(phone, output, output_format, "scan"))


@app.command()
def version() -> None:
    """Show version information."""
    _show_logo()


# ============================================================================
# Config Commands
# ============================================================================


@app.command(name="config")
def config_cmd(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
) -> None:
    """Configure See settings."""
    if show:
        config = load_config()
        keys = [
            ("NumVerify API Key", config.api_keys.numverify),
            ("Abstract API Key", config.api_keys.abstract),
            ("NumLookup API Key", config.api_keys.numlookup),
            ("Hunter API Key", config.api_keys.hunter),
            ("DeHashed API Key", config.api_keys.dehashed),
            ("DeHashed Email", config.api_keys.dehashed_email),
            ("HIBP API Key", config.api_keys.hibp),
        ]
        typer.echo("\n=== Current Configuration ===")
        for label, value in keys:
            typer.echo(f"{label + ':':<22} {'Configured' if value else 'Not set'}")
        typer.echo(f"{'Tor Enabled:':<22} {config.tor.enabled}")
        typer.echo(f"{'Timeout:':<22} {config.lookup.timeout}")
        typer.echo(f"{'Retries:':<22} {config.lookup.retries}")
        typer.echo(f"{'Output directory:':<22} {config.output.directory}")
        typer.echo(f"{'HIBP delay (s):':<22} {config.rate_limit.hibp_delay_seconds}")
    else:
        typer.echo("Use --show to view current configuration")


if __name__ == "__main__":
    app()
