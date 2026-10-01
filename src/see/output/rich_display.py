"""Rich terminal display for See OSINT framework."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from see.utils.logger import get_logger

logger = get_logger("rich_display")


class RichDisplay:
    """Displays OSINT results in terminal using Rich."""

    def __init__(self):
        self.console = Console()

    def display_phone(self, result) -> None:
        """
        Display phone scan result in terminal.
        
        Args:
            result: PhoneResult to display
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Value")

        # Phone number
        table.add_row("Phone", result.input_number)
        table.add_row("", "")

        # Validity
        valid_icon = "[green]✓ Yes[/green]" if result.valid else "[red]✗ No[/red]"
        table.add_row("Valid", valid_icon)

        # Type
        if result.carrier:
            type_display = result.carrier.line_type.replace("_", " ").title() if result.carrier.line_type else "Unknown"
            table.add_row("Type", type_display)

        # Country
        table.add_row("Country", f"{result.country} (+{result.country_code})")

        # Carrier
        if result.carrier and result.carrier.carrier:
            table.add_row("Carrier", result.carrier.carrier)

        # Location
        if result.carrier and result.carrier.location:
            table.add_row("Location", result.carrier.location)

        # Timezone
        if result.carrier and result.carrier.timezone:
            table.add_row("Timezone", result.carrier.timezone)

        # Owner
        if result.owner and result.owner.name:
            table.add_row("Owner", f"[bold green]{result.owner.name}[/bold green]")

        # Risk
        if result.owner and result.owner.risk_level:
            table.add_row("Risk", result.owner.risk_level)

        # Source
        if result.modules_used:
            table.add_row("", "")
            table.add_row("Source", ", ".join(result.modules_used))

        # Errors
        if result.errors:
            table.add_row("", "")
            for error in result.errors:
                table.add_row("[red]Error[/red]", error)

        # Create panel
        panel = Panel(
            table,
            title=f"[bold blue]📱 {result.input_number}[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)

    def display_email(self, result) -> None:
        """
        Display email scan result in terminal.
        
        Args:
            result: EmailResult to display
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Value")

        # Email
        table.add_row("Email", result.input_email)
        table.add_row("", "")

        # Validity
        valid_icon = "[green]✓ Yes[/green]" if result.valid else "[red]✗ No[/red]"
        table.add_row("Valid", valid_icon)

        # Domain
        table.add_row("Domain", result.domain)

        # Provider
        table.add_row("Provider", result.provider)

        # Free email
        free_icon = "[green]✓ Yes[/green]" if result.is_free else "[red]✗ No[/red]"
        table.add_row("Free Email", free_icon)

        # Disposable
        disposable_icon = "[red]⚠ Yes[/red]" if result.is_disposable else "[green]✓ No[/green]"
        table.add_row("Disposable", disposable_icon)

        # Webmail
        webmail_icon = "[green]✓ Yes[/green]" if result.is_webmail else "[red]✗ No[/red]"
        table.add_row("Webmail", webmail_icon)

        # SMTP deliverability
        if result.deliverability:
            deliv = result.deliverability
            if deliv.get("mx_found"):
                icon = "[green]✓ Deliverable[/green]" if deliv.get("is_deliverable") else "[red]✗ Not accepted[/red]"
                code = deliv.get("smtp_code")
                table.add_row("SMTP", f"{icon} (code {code}, MX {deliv.get('mx_host', '')})")
            else:
                table.add_row("SMTP", "[red]✗ No MX records[/red]")

        # Personal info
        if result.name or result.phone_numbers or result.location:
            table.add_row("", "")
            table.add_row("[bold]PERSONAL[/bold]", "")
            
            if result.name:
                table.add_row("Name", f"[green]{result.name}[/green]")
            
            if result.phone_numbers:
                for phone in result.phone_numbers[:3]:  # Show first 3
                    table.add_row("Phone", f"[cyan]{phone}[/cyan]")
            
            if result.location:
                table.add_row("Location", result.location)

        # Work info
        if result.company or result.job_title or result.linkedin:
            table.add_row("", "")
            table.add_row("[bold]WORK[/bold]", "")
            
            if result.company:
                table.add_row("Company", result.company)
            
            if result.job_title:
                table.add_row("Job Title", result.job_title)
            
            if result.linkedin:
                table.add_row("LinkedIn", f"[link={result.linkedin}]{result.linkedin}[/link]")

        # MX Records
        if result.mx_records:
            table.add_row("", "")
            table.add_row("MX Records", f"[cyan]{len(result.mx_records)} found[/cyan]")
            for mx in result.mx_records[:3]:  # Show first 3
                table.add_row("  →", mx)

        # Breaches
        if result.breaches and result.breaches.total_breaches > 0:
            table.add_row("", "")
            table.add_row("[bold]BREACHES[/bold]", f"[red]{result.breaches.total_breaches} found[/red]")
            for breach in result.breaches.breaches[:5]:  # Show first 5
                name = breach.get("name", "Unknown")
                date = breach.get("date", "")
                table.add_row("  →", f"{name} ({date})" if date else name)

        # Social profiles
        if result.social_profiles:
            table.add_row("", "")
            table.add_row("[bold]SOCIAL MEDIA[/bold]", f"[green]{len(result.social_profiles)} links[/green]")
            
            # Separate found and manual check profiles
            found_profiles = [p for p in result.social_profiles if p.found]
            manual_profiles = [p for p in result.social_profiles if not p.found]
            
            # Show found profiles
            for profile in found_profiles[:10]:  # Show first 10 found
                table.add_row("  ✓", f"[green]{profile.platform}[/green]: {profile.url}")
            
            # Show manual check profiles - group by type
            if manual_profiles:
                table.add_row("", "")
                table.add_row("[bold]INVESTIGATE[/bold]", "[dim]Click links to check[/dim]")
                
                # Search engines
                search_profiles = [p for p in manual_profiles if p.platform.startswith("search_")]
                if search_profiles:
                    table.add_row("", "[bold]Search Engines:[/bold]")
                    for profile in search_profiles[:4]:
                        platform = profile.platform.replace("search_", "").title()
                        table.add_row("  🔍", f"{platform}")
                
                # Social platforms
                social_plat = [p for p in manual_profiles if p.platform.startswith("social_")]
                if social_plat:
                    table.add_row("", "[bold]Social Platforms:[/bold]")
                    for profile in social_plat[:8]:
                        platform = profile.platform.replace("social_", "").title()
                        table.add_row("  👤", f"{platform}")

        # Source
        if result.modules_used:
            table.add_row("", "")
            table.add_row("Source", ", ".join(result.modules_used))

        # Errors
        if result.errors:
            table.add_row("", "")
            for error in result.errors:
                table.add_row("[red]Error[/red]", error)

        # Create panel
        panel = Panel(
            table,
            title=f"[bold blue]📧 {result.input_email}[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)

    def display_json(self, data: dict) -> None:
        """Display result as formatted JSON."""
        import json
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        self.console.print_json(formatted)

    def display_username(self, result) -> None:
        """
        Display username scan result in terminal.

        Args:
            result: UsernameResult to display
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan", width=14)
        table.add_column("Value")

        # Username
        table.add_row("Username", result.input_username)
        table.add_row("", "")

        # Summary
        table.add_row("Platforms", f"[cyan]{result.platforms_checked}[/cyan] checked")
        table.add_row(
            "Found",
            f"[green]✓ {result.found_count}[/green] found / "
            f"[red]✗ {result.not_found_count}[/red] not found",
        )

        # Found profiles
        found_profiles = [p for p in result.profiles if p.found]
        if found_profiles:
            table.add_row("", "")
            table.add_row("[bold]FOUND PROFILES[/bold]", f"[green]{len(found_profiles)}[/green]")
            for profile in found_profiles[:15]:  # Show first 15
                table.add_row("  ✓", f"[green]{profile.platform}[/green]: {profile.url}")

        # Manual check profiles
        manual_profiles = [p for p in result.profiles if p.status == "check_manually"]
        if manual_profiles:
            table.add_row("", "")
            table.add_row("[bold]CHECK MANUALLY[/bold]", f"[yellow]{len(manual_profiles)}[/yellow]")
            for profile in manual_profiles[:10]:
                table.add_row("  🔍", f"{profile.platform}: {profile.url}")

        # Errors
        errors = [p for p in result.profiles if p.status == "error"]
        if errors:
            table.add_row("", "")
            table.add_row("[bold]ERRORS[/bold]", f"[red]{len(errors)}[/red]")
            for profile in errors[:8]:
                reason = profile.error or "unknown"
                table.add_row("  ⚠", f"{profile.platform} ({reason})")

        # Source
        if result.modules_used:
            table.add_row("", "")
            table.add_row("Source", ", ".join(result.modules_used))

        # Panel errors
        if result.errors:
            table.add_row("", "")
            for error in result.errors:
                table.add_row("[red]Error[/red]", error)

        # Create panel
        panel = Panel(
            table,
            title=f"[bold blue]🔍 {result.input_username}[/bold blue]",
            border_style="blue",
            padding=(1, 2),
        )

        self.console.print(panel)
