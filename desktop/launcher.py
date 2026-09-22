"""RakeGlossary desktop launcher.

Starts the FastAPI backend in a background thread, then opens a native
window (WebView2 on Windows) pointing at the served SPA.

Run from the project root:
    python desktop/launcher.py

In production (PyInstaller bundle), the frontend build is expected at
`frontend/dist/` and the backend at `backend/app/`.
"""

from __future__ import annotations

import logging
import os
import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn
import webview

# ---------------------------------------------------------------------------
# Path resolution: works both in dev and inside a PyInstaller bundle
# ---------------------------------------------------------------------------


def _project_root() -> Path:
    """Return the project root in dev, or the bundle root in a frozen app."""
    if getattr(sys, "frozen", False):
        # PyInstaller sets sys._MEIPASS to the bundle's temporary directory
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # Dev: this file is at <root>/desktop/launcher.py
    return Path(__file__).resolve().parent.parent


ROOT = _project_root()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIST = ROOT / "frontend" / "dist"

# Make `app` importable
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ---------------------------------------------------------------------------
# Logging (must come before any code that logs)
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger("launcher")


# ---------------------------------------------------------------------------
# Runtime data directory
# ---------------------------------------------------------------------------
# In dev:       <project>/data/
# In production: %APPDATA%\RakeGlossary\data\


def _configure_data_dir() -> Path:
    """Set RG_DATA_DIR so app.core.config picks the right path."""
    if getattr(sys, "frozen", False):
        appdata = os.getenv("APPDATA")
        if appdata:
            base = Path(appdata) / "RakeGlossary"
        else:
            base = Path.home() / ".rakeglossary"
    else:
        # Dev mode: keep data/ next to the project
        base = ROOT

    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["RG_DATA_DIR"] = str(data_dir)
    log.info(f"Data directory: {data_dir}")
    return data_dir


_DATA_DIR = _configure_data_dir()


# ---------------------------------------------------------------------------
# Port management
# ---------------------------------------------------------------------------

HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _find_free_port(preferred: int = DEFAULT_PORT) -> int:
    """Return `preferred` if it's free, else any free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, preferred))
            return preferred
        except OSError:
            # Fall back to an OS-assigned port
            s.bind((HOST, 0))
            return s.getsockname()[1]


def _wait_for_server(host: str, port: int, timeout: float = 15.0) -> bool:
    """Block until the server accepts TCP connections, or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.1)
    return False


# ---------------------------------------------------------------------------
# Backend thread
# ---------------------------------------------------------------------------


def _run_backend(host: str, port: int) -> None:
    """Run uvicorn in this thread. Called from a daemon thread."""
    try:
        from app.main import app  # noqa: WPS433
    except Exception as exc:  # noqa: BLE001
        log.exception(f"Failed to import the FastAPI app: {exc}")
        raise

    log.info(f"Starting backend on http://{host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    port = _find_free_port(DEFAULT_PORT)
    log.info(f"Using port {port}")

    backend_thread = threading.Thread(
        target=_run_backend,
        args=(HOST, port),
        daemon=True,
        name="uvicorn-backend",
    )
    backend_thread.start()

    if not _wait_for_server(HOST, port):
        log.error("Backend did not start within the timeout. Exiting.")
        sys.exit(1)

    log.info("Backend is up. Opening window...")

    webview.create_window(
        title="RakeGlossary",
        url=f"http://{HOST}:{port}/",
        width=1280,
        height=800,
        min_size=(900, 600),
        text_select=True,
    )

    webview.start(debug=False)

    log.info("Window closed. Backend will stop with the process.")


if __name__ == "__main__":
    main()