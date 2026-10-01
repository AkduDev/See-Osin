"""Logging configuration for See OSINT tool."""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "see",
    level: int = logging.INFO,
    log_file: Path | None = None,
    verbose: bool = False,
) -> logging.Logger:
    """Configure and return a structured logger."""

    logger = logging.getLogger(name)

    if verbose:
        level = logging.DEBUG

    logger.setLevel(level)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Get a child logger for a specific module."""
    return logging.getLogger(f"see.{module_name}")
