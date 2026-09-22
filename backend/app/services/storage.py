"""Secure file storage for uploaded documents.

Layout:
    data/projects/{sanitized_title}__{id8}/
        ├─ file1.docx
        ├─ file2.pdf
        └─ ...

The `{id8}` suffix (first 8 chars of the project UUID) guarantees
uniqueness even if two projects have the same title. When a project
is renamed, the folder is renamed too and all source paths are updated.
"""

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger("services.storage")

_ALLOWED_EXTENSIONS = {".pdf", ".docx", ".epub", ".txt"}
_MAX_BYTES = 200 * 1024 * 1024  # 200 MB per file
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._\-]+")
_TITLE_ILLEGAL_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class StorageError(Exception):
    """Raised when an upload cannot be persisted."""


# ---------------------------------------------------------------------------
# Filename sanitization
# ---------------------------------------------------------------------------


def _sanitize_filename(name: str) -> str:
    name = Path(name).name
    stem = Path(name).stem
    ext = Path(name).suffix.lower()
    stem = _SAFE_NAME_RE.sub("_", stem)[:80] or "upload"
    return f"{stem}{ext}"


def sanitize_title(title: str, max_len: int = 40) -> str:
    """Turn a project title into a filesystem-safe folder-name component."""
    if not title:
        return "Untitled"
    cleaned = _TITLE_ILLEGAL_RE.sub("_", title).strip(" .")
    if not cleaned:
        return "Untitled"
    return cleaned[:max_len]


# ---------------------------------------------------------------------------
# Project folder helpers
# ---------------------------------------------------------------------------


def project_folder_name(project_id: str, title: str) -> str:
    """Compute the folder name for a project: `{sanitized_title}__{id8}`."""
    short_id = project_id.replace("-", "")[:8]
    return f"{sanitize_title(title)}__{short_id}"


def get_project_dir(project_id: str, title: str) -> Path:
    """Return (and ensure) the upload folder for `project_id`."""
    d = settings.paths.projects / project_folder_name(project_id, title)
    d.mkdir(parents=True, exist_ok=True)
    return d


def find_project_dir(project_id: str) -> Path | None:
    """Locate the folder for a project by its `__{id8}` suffix."""
    short_id = project_id.replace("-", "")[:8]
    parent = settings.paths.projects
    if not parent.exists():
        return None
    suffix = f"__{short_id}"
    for p in parent.iterdir():
        if p.is_dir() and p.name.endswith(suffix):
            return p
    return None


def rename_project_folder(
    project_id: str,
    old_title: str,
    new_title: str,
) -> Path | None:
    """Rename a project's folder. Returns the new path (or None if missing)."""
    old_dir = find_project_dir(project_id)
    if old_dir is None:
        log.warning(f"No folder found for project {project_id[:8]}")
        return None

    new_name = project_folder_name(project_id, new_title)
    new_dir = old_dir.parent / new_name

    if old_dir == new_dir:
        return new_dir

    try:
        old_dir.rename(new_dir)
        log.info(f"Renamed project folder: " f"'{old_dir.name}' → '{new_dir.name}'")
        return new_dir
    except OSError as exc:
        log.warning(f"Could not rename project folder: {exc}")
        return old_dir


# ---------------------------------------------------------------------------
# File storage
# ---------------------------------------------------------------------------


def save_upload_for_project(
    file_bytes: bytes,
    original_name: str,
    project_id: str,
    project_title: str,
) -> Path:
    """Persist a file under the project's folder and return its path."""
    safe_name = _sanitize_filename(original_name)
    ext = Path(safe_name).suffix.lower()

    if ext not in _ALLOWED_EXTENSIONS:
        raise StorageError(
            f"Unsupported extension '{ext}'. " f"Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}"
        )

    if len(file_bytes) == 0:
        raise StorageError("Uploaded file is empty.")

    if len(file_bytes) > _MAX_BYTES:
        raise StorageError(f"File too large ({len(file_bytes)} bytes). Max: {_MAX_BYTES} bytes.")

    project_dir = get_project_dir(project_id, project_title)
    unique = uuid.uuid4().hex[:12]
    final_path = project_dir / f"{unique}__{safe_name}"

    try:
        final_path.write_bytes(file_bytes)
    except OSError as exc:
        log.exception(f"Failed to save upload to {final_path}")
        raise StorageError(f"Could not write file: {exc}") from exc

    log.info(
        f"Saved upload '{original_name}' -> "
        f"'{final_path.parent.name}/{final_path.name}' "
        f"({len(file_bytes)} bytes)"
    )
    return final_path


def delete_upload(path: str | Path) -> None:
    """Remove a single uploaded file. Never raises."""
    try:
        p = Path(path)
        if p.exists() and p.is_file():
            p.unlink()
            log.info(f"Deleted upload '{p.name}'")
    except OSError as exc:
        log.warning(f"Could not delete '{path}': {exc}")


def delete_project_dir(project_id: str) -> None:
    """Remove the entire project folder. Never raises."""
    try:
        d = find_project_dir(project_id)
        if d is not None and d.exists() and d.is_dir():
            shutil.rmtree(d, ignore_errors=True)
            log.info(f"Deleted project folder '{d.name}'")
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Could not delete project folder for {project_id}: {exc}")
