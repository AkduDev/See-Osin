"""JSON output formatter for See OSINT tool."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from see.core.aggregator import OSINTResult
from see.utils.logger import get_logger

logger = get_logger("json_formatter")


class JSONFormatter:
    """Formats OSINT results as JSON."""

    def __init__(self, output_dir: Path = Path("./results")):
        self.output_dir = output_dir

    def format(self, result: OSINTResult) -> str:
        """Format OSINT result as JSON string."""
        data = result.to_dict()
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, result: OSINTResult, filename: str | None = None) -> Path:
        """
        Save result to JSON file.

        Args:
            result: OSINTResult to save
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to saved file
        """
        # Create directory only when saving (lazy initialization)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            phone_clean = result.input_number.replace("+", "").replace(" ", "")
            filename = f"scan_{phone_clean}_{timestamp}.json"

        filepath = self.output_dir / filename
        data = result.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {filepath}")
        return filepath
