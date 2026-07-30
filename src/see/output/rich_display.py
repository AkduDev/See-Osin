"""Rich terminal display for See OSINT tool."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from see.core.aggregator import OSINTResult
from see.utils.logger import get_logger

logger = get_logger("rich_display")


class RichDisplay:
    """Displays OSINT results in terminal using Rich."""

    def __init__(self):
        self.console = Console()

    def display(self, result: OSINTResult) -> None:
        """
        Display OSINT result in terminal.

        Args:
            result: OSINTResult to display
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="cyan", width=12)
        table.add_column("Value")

        # Phone number
        table.add_row("Phone", result.input_number)
        table.add_row("", "")

        if result.parsed:
            # Validity
            valid_icon = "[green]✓ Yes[/green]" if result.parsed.is_valid else "[red]✗ No[/red]"
            table.add_row("Valid", valid_icon)

            # Type
            type_display = result.parsed.number_type.replace("_", " ").title()
            table.add_row("Type", type_display)

            # Country
            table.add_row("Country", f"{result.parsed.country} (+{result.parsed.country_code})")

        if result.carrier:
            carrier_name = result.carrier.get("carrier", "Unknown")
            if carrier_name and carrier_name != "Unknown":
                table.add_row("Carrier", carrier_name)

            location = result.carrier.get("location", "")
            if location and location != "Unknown":
                table.add_row("Location", location)

            timezone_val = result.carrier.get("timezone", "")
            if timezone_val and timezone_val != "Unknown":
                table.add_row("Timezone", timezone_val)

        if result.location:
            city = result.location.get("city", "")
            if city:
                table.add_row("City", city)

        # Source
        sources = result.modules_used
        if sources:
            table.add_row("", "")
            table.add_row("Source", ", ".join(sources))

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

    def display_json(self, result: OSINTResult) -> None:
        """Display result as formatted JSON."""
        import json
        data = result.to_dict()
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        self.console.print_json(formatted)
