"""JSON output formatter for See OSINT tool."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from see.core.aggregator import OSINTResult
from see.utils.logger import get_logger

logger = get_logger("json_formatter")

ResultLike = OSINTResult | dict


def _to_dict(result: ResultLike) -> dict:
    """Accept a dataclass result (with to_dict) or an already-built dict."""
    if isinstance(result, dict):
        return result
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    raise TypeError(f"Unsupported result type: {type(result).__name__}")


def _target_name(result: ResultLike) -> str:
    if isinstance(result, dict):
        return str(result.get("input", "result"))
    return str(
        getattr(result, "input_username", None)
        or getattr(result, "input_number", None)
        or getattr(result, "input_email", None)
        or getattr(result, "input", None)
        or "result"
    )


class JSONFormatter:
    """Formats OSINT results as JSON."""

    def __init__(self, output_dir: Path | str = Path("./results")):
        self.output_dir = Path(output_dir)

    def format(self, result: ResultLike) -> str:
        """Format OSINT result as JSON string."""
        data = _to_dict(result)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(self, result: ResultLike, filename: str | Path | None = None) -> Path:
        """
        Save result to JSON file.

        Args:
            result: OSINTResult (or dict) to save
            filename: Optional filename or full path (auto-generated if not provided).
                If it contains a directory part, that directory is used instead
                of the configured output_dir.

        Returns:
            Path to saved file
        """
        path: Path | None = Path(filename) if filename is not None else None

        if path is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            target_clean = _target_name(result).replace("+", "").replace(" ", "")
            path = Path(f"scan_{target_clean}_{timestamp}.json")

        # A filename with a parent dir wins over the configured output_dir
        if len(path.parts) > 1:
            filepath = path
            filepath.parent.mkdir(parents=True, exist_ok=True)
        else:
            # Create directory only when saving (lazy initialization)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            filepath = self.output_dir / path.name

        data = _to_dict(result)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {filepath}")
        return filepath
