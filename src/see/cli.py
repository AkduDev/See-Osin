"""CLI entry point for See OSINT framework."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

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


def _show_logo() -> None:
    """Display the See logo in terminal."""
    console.print(LOGO, style="bold cyan")
    console.print(f"  OSINT Framework v{__version__}\n", style="dim")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """See OSINT Framework - Intelligence gathering tool."""
    if ctx.invoked_subcommand is None:
        _show_logo()
        raise typer.Exit()


# ============================================================================
# Phone Commands
# ============================================================================


@app.command()
def phone_scan(
    number: str = typer.Argument(help="Phone number (e.g., +34612345678)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Complete phone number scan."""
    asyncio.run(_phone_scan(number, output, format, "scan"))


@app.command()
def phone_carrier(
    number: str = typer.Argument(help="Phone number to check carrier"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Get carrier information."""
    asyncio.run(_phone_scan(number, output, format, "carrier"))


@app.command()
def phone_owner(
    number: str = typer.Argument(help="Phone number to find owner"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Find owner information."""
    asyncio.run(_phone_scan(number, output, format, "owner"))


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
    format: str,
    scan_type: str,
) -> None:
    """Common phone scan implementation."""
    engine = SeeEngine()
    
    if scan_type == "scan":
        result = await engine.scan_phone(number)
    elif scan_type == "carrier":
        from see.modules.phones.domain import PhoneDomain
        domain = PhoneDomain()
        result = await domain.scan_carrier(number)
    elif scan_type == "owner":
        from see.modules.phones.domain import PhoneDomain
        domain = PhoneDomain()
        result = await domain.scan_owner(number)
    else:
        raise ValueError(f"Unknown scan type: {scan_type}")
    
    # Display results
    display = RichDisplay()
    json_fmt = JSONFormatter()
    
    if format in ("display", "both"):
        display.display_phone(result)
    
    if format in ("json", "both"):
        if output:
            filepath = json_fmt.save(result.to_dict(), output.name)
            typer.echo(f"\nResults saved to {filepath}", err=True)
        elif format == "json":
            import json
            typer.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


# ============================================================================
# Email Commands
# ============================================================================


@app.command()
def email_scan(
    email: str = typer.Argument(help="Email address to scan"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Complete email scan."""
    asyncio.run(_email_scan(email, output, format, "scan"))


@app.command()
def email_breaches(
    email: str = typer.Argument(help="Email address to check breaches"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Check email breaches."""
    asyncio.run(_email_scan(email, output, format, "breaches"))


@app.command()
def email_social(
    email: str = typer.Argument(help="Email address to find social profiles"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Find social media profiles by email."""
    asyncio.run(_email_scan(email, output, format, "social"))


@app.command()
def email_disposable(
    email: str = typer.Argument(help="Email address to check if disposable"),
) -> None:
    """Check if email is disposable."""
    asyncio.run(_email_scan(email, None, "display", "disposable"))


async def _email_scan(
    email: str,
    output: Path | None,
    format: str,
    scan_type: str,
) -> None:
    """Common email scan implementation."""
    from see.modules.emails.domain import EmailDomain
    
    domain = EmailDomain()
    
    if scan_type == "scan":
        result = await domain.scan(email)
    elif scan_type == "breaches":
        result = await domain.scan_breaches(email)
    elif scan_type == "social":
        result = await domain.scan_social(email)
    elif scan_type == "disposable":
        result = await domain.scan_disposable(email)
    else:
        raise ValueError(f"Unknown scan type: {scan_type}")
    
    # Display results
    display = RichDisplay()
    json_fmt = JSONFormatter()
    
    if format in ("display", "both"):
        display.display_email(result)
    
    if format in ("json", "both"):
        if output:
            filepath = json_fmt.save(result.to_dict(), output.name)
            typer.echo(f"\nResults saved to {filepath}", err=True)
        elif format == "json":
            import json
            typer.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


# ============================================================================
# Legacy Commands (for backward compatibility)
# ============================================================================


@app.command()
def scan(
    phone: str = typer.Argument(help="Phone number to scan"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
) -> None:
    """Legacy scan command (use 'phone-scan' instead)."""
    asyncio.run(_phone_scan(phone, output, format, "scan"))


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
        typer.echo("\n=== Current Configuration ===")
        typer.echo(f"NumVerify API Key: {'Configured' if config.api_keys.numverify else 'Not set'}")
        typer.echo(f"Abstract API Key:  {'Configured' if config.api_keys.abstract else 'Not set'}")
        typer.echo(f"NumLookup API Key: {'Configured' if config.api_keys.numlookup else 'Not set'}")
        typer.echo(f"Tor Enabled:       {config.tor.enabled}")
        typer.echo(f"Timeout:           {config.lookup.timeout}")
        typer.echo(f"Retries:           {config.lookup.retries}")
    else:
        typer.echo("Use --show to view current configuration")


if __name__ == "__main__":
    app()
