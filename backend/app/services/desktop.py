"""Desktop integration helpers (Downloads folder, file manager)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.core.logging import get_logger

log = get_logger("services.desktop")


def get_downloads_dir() -> Path:
    """Return the user's Downloads folder, scoped to RakeGlossary.

    Path: ``<home>/Downloads/RakeGlossary`` (created if missing).
    """
    downloads = Path.home() / "Downloads" / "RakeGlossary"
    downloads.mkdir(parents=True, exist_ok=True)
    return downloads


def open_in_file_manager(path: Path, select: bool = True) -> bool:
    """Open the OS file manager at ``path``, optionally selecting it.

    Returns ``True`` if the launcher command was issued, ``False`` on error.
    """
    try:
        path = path.resolve()
        if not path.exists():
            log.warning(f"open_in_file_manager: path does not exist: {path}")
            return False

        if sys.platform == "win32":
            if select and path.is_file():
                subprocess.Popen(["explorer", "/select,", str(path)])
            else:
                target = path if path.is_dir() else path.parent
                subprocess.Popen(["explorer", str(target)])
            return True

        if sys.platform == "darwin":
            if select:
                subprocess.Popen(["open", "-R", str(path)])
            else:
                target = path if path.is_dir() else path.parent
                subprocess.Popen(["open", str(target)])
            return True

        # Linux / BSD
        target = path if path.is_dir() else path.parent
        subprocess.Popen(["xdg-open", str(target)])
        return True

    except (FileNotFoundError, OSError) as exc:
        log.warning(f"Could not open file manager at {path}: {exc}")
        return False
