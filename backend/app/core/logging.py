"""Centralized logging configuration using loguru.

Provides:
- Console output with colors.
- Rotating file output in data/logs/.
- A `get_logger` helper that tags records with a component name.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def _build_file_sink(path: Path):
    """Create a rotating file sink with UTF-8 encoding."""
    return {
        "sink": str(path),
        "rotation": "10 MB",
        "retention": "14 days",
        "compression": "zip",
        "encoding": "utf-8",
        "enqueue": True,
        "level": settings.log_level,
    }


def configure_logging() -> None:
    """Initialize loguru sinks. Safe to call multiple times."""
    logger.remove()

    logger.add(
        sys.stdout,
        level=settings.log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[component]}</cyan> | {message}"
        ),
        filter=lambda record: record["extra"].setdefault("component", "app") or True,
    )

    logger.add(**_build_file_sink(settings.paths.logs / "rakeglossary.log"))


def get_logger(component: str):
    """Return a logger bound to a component name (e.g., 'extractor.pdf')."""
    return logger.bind(component=component)


configure_logging()
