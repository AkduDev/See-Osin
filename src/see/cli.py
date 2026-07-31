"""CLI entry point for See OSINT tool."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from see import __version__
from see.core.aggregator import ModuleAggregator, OSINTResult
from see.core.parser import parse_phone_number
from see.core.schemas import DEFAULT_MODULES, OWNER_MODULES
from see.logo import LOGO
from see.output.json_formatter import JSONFormatter
from see.output.rich_display import RichDisplay
from see.utils.config import load_config
from see.utils.tor_client import TorManager

app = typer.Typer(
    name="see",
    help="Phone Number OSINT Tool - Get carrier, location, and more",
    no_args_is_help=False,
)

console = Console()


def _show_logo() -> None:
    """Display the See logo in terminal."""
    console.print(LOGO, style="bold cyan")
    console.print("  Phone Number OSINT Tool v0.1.0\n", style="dim")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Phone Number OSINT Tool - Get carrier, location, social media and more."""
    if ctx.invoked_subcommand is None:
        _show_logo()
        raise typer.Exit()


async def _run_scan(
    phone: str,
    output: Path | None,
    format: str,
    modules: list[str],
    use_tor: bool,
    no_tor: bool,
) -> None:
    """Common scan implementation for scan/owner commands."""
    config = load_config()
    tor_enabled = use_tor or (config.tor.enabled and not no_tor)

    if tor_enabled:
        typer.echo("Routing through Tor...", err=True)

    phone_info = parse_phone_number(phone)
    if not phone_info.is_possible:
        typer.echo("Error: Invalid phone number format", err=True)
        raise typer.Exit(1)

    # Aggregator auto-registers all modules
    aggregator = ModuleAggregator(config)
    result = await aggregator.run_lookup(phone_info, modules=modules)

    # Display results
    display = RichDisplay()
    json_fmt = JSONFormatter()

    if format in ("display", "both"):
        display.display(result)

    if format in ("json", "both"):
        if output:
            filepath = json_fmt.save(result, output.name)
            typer.echo(f"\nResults saved to {filepath}", err=True)
        elif format == "json":
            import json
            typer.echo(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


@app.command()
def scan(
    phone: str = typer.Argument(help="Phone number to scan (e.g., +34612345678)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
    tor: bool = typer.Option(False, "--tor", help="Route requests through Tor"),
    no_tor: bool = typer.Option(False, "--no-tor", help="Disable Tor even if configured"),
) -> None:
    """Scan a phone number and get basic OSINT data."""
    asyncio.run(_run_scan(phone, output, format, DEFAULT_MODULES, tor, no_tor))


@app.command()
def owner(
    phone: str = typer.Argument(help="Phone number to find owner (e.g., +34612345678)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
    tor: bool = typer.Option(False, "--tor", help="Route requests through Tor"),
    no_tor: bool = typer.Option(False, "--no-tor", help="Disable Tor even if configured"),
) -> None:
    """Find owner information for a phone number."""
    asyncio.run(_run_scan(phone, output, format, OWNER_MODULES, tor, no_tor))


@app.command()
def validate(
    phone: str = typer.Argument(help="Phone number to validate"),
) -> None:
    """Validate a phone number format."""
    phone_info = parse_phone_number(phone)

    typer.echo("\n=== Phone Validation ===")
    typer.echo(f"Input:         {phone_info.original}")
    typer.echo(f"E.164:         {phone_info.e164}")
    typer.echo(f"National:      {phone_info.national}")
    typer.echo(f"International: {phone_info.international}")
    typer.echo(f"Valid:         {'Yes' if phone_info.is_valid else 'No'}")
    typer.echo(f"Possible:      {'Yes' if phone_info.is_possible else 'No'}")
    typer.echo(f"Country:       {phone_info.country} (+{phone_info.country_code})")
    typer.echo(f"Type:          {phone_info.number_type.replace('_', ' ').title() if phone_info.number_type else 'Unknown'}")


@app.command()
def carrier(
    phone: str = typer.Argument(help="Phone number to check carrier"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    format: str = typer.Option("both", "--format", "-f", help="Output format: json, display, both"),
    tor: bool = typer.Option(False, "--tor", help="Route requests through Tor"),
    no_tor: bool = typer.Option(False, "--no-tor", help="Disable Tor"),
) -> None:
    """Get carrier information for a phone number."""
    asyncio.run(_run_scan(phone, output, format, ["phonenumbers"], tor, no_tor))


@app.command(name="config")
def config_cmd(
    set_key: Optional[str] = typer.Option(None, "--set", help="Set API key (format: key=value)"),
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
) -> None:
    """Configure See settings."""
    if show:
        config = load_config()
        typer.echo("\n=== Current Configuration ===")
        typer.echo(f"NumVerify API Key: {'Configured' if config.api_keys.numverify else 'Not set'}")
        typer.echo(f"Abstract API Key:  {'Configured' if config.api_keys.abstract else 'Not set'}")
        typer.echo(f"Tor Enabled:       {config.tor.enabled}")
        typer.echo(f"Tor SOCKS Port:    {config.tor.socks_port}")
        typer.echo(f"Timeout:           {config.lookup.timeout}")
        typer.echo(f"Retries:           {config.lookup.retries}")
        typer.echo(f"Modules:           {', '.join(config.lookup.modules)}")
    elif set_key:
        key, _, value = set_key.partition("=")
        if not value:
            typer.echo("Invalid format. Use: --set numverify=YOUR_KEY", err=True)
            raise typer.Exit(1)
        typer.echo(f"Setting {key}...")
        typer.echo("Note: For now, edit config.yaml manually")
    else:
        typer.echo("Use --show to view config or --set key=value to configure")


@app.command()
def version() -> None:
    """Show version information."""
    pass


@app.command()
def tor_status() -> None:
    """Check Tor connection status."""
    config = load_config()
    tor_client = TorManager.get_client(
        socks_port=config.tor.socks_port,
        control_port=config.tor.control_port,
    )

    typer.echo("\n=== Tor Status ===")

    if tor_client.is_available:
        typer.echo("Status:    ✓ Connected")
        typer.echo(f"Exit IP:   {tor_client.current_ip}")

        if tor_client.connect():
            typer.echo("Control:   ✓ Connected")
            typer.echo(f"Port:      {config.tor.socks_port}")
            typer.echo(f"Control:   {config.tor.control_port}")
        else:
            typer.echo("Control:   ✗ Not connected (circuit rotation disabled)")
    else:
        typer.echo("Status:    ✗ Not available")
        typer.echo("Make sure Tor is running: sudo systemctl start tor")


if __name__ == "__main__":
    app()
