"""Services package — business logic layer."""

from __future__ import annotations

import importlib

from app.services.progress import ProgressEvent, ProgressTracker, tracker
from app.services.storage import (
    StorageError,
    delete_project_dir,
    delete_upload,
    save_upload_for_project,
)

__all__ = [
    "ProgressEvent",
    "ProgressTracker",
    "StorageError",
    "delete_project_dir",
    "delete_upload",
    "save_upload_for_project",
    "tracker",
]


def __getattr__(name: str):
    """Lazy-load heavier service modules on first access."""
    if name in {
        "project_service",
        "source_service",
        "glossary_service",
        "export_service",
        "pipeline_runner",
        "settings_service",
    }:
        return importlib.import_module(f".{name}", __package__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
