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

    def display_json(self, data: dict) -> None:
        """Display result as formatted JSON."""
        import json
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        self.console.print_json(formatted)
