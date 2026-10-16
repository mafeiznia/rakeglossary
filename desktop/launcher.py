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
# NLTK data path (needed in both dev and frozen mode)
# ---------------------------------------------------------------------------


def _configure_nltk_path() -> None:
    """Make NLTK find the bundled or user-installed nltk_data directory.

    - In dev: NLTK already looks in %APPDATA%/nltk_data
    - In frozen mode: the bundle ships nltk_data/ at <_MEIPASS>/nltk_data
    """
    import nltk

    paths: list[str] = []
    if getattr(sys, "frozen", False):
        # PyInstaller extracts datas to sys._MEIPASS
        bundled = Path(sys._MEIPASS) / "nltk_data"  # type: ignore[attr-defined]
        if bundled.is_dir():
            paths.append(str(bundled))

    # Always add the user-level fallback
    appdata = os.getenv("APPDATA")
    if appdata:
        user_path = Path(appdata) / "nltk_data"
        if user_path.is_dir():
            paths.append(str(user_path))

    for p in paths:
        if p not in nltk.data.path:
            nltk.data.path.insert(0, p)
            log.info(f"NLTK data path added: {p}")


_configure_nltk_path()


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

    icon_path = _resolve_icon_path()

    webview.create_window(
        title="RakeGlossary",
        url=f"http://{HOST}:{port}/",
        width=1280,
        height=800,
        min_size=(900, 600),
        text_select=True,
    )

    # On Windows, set the window/taskbar icon via ctypes. We use this
    # because pywebview 6.x with the EdgeChromium backend does not honor
    # the `icon=` parameter reliably.
    if icon_path is not None:
        threading.Thread(
            target=_force_windows_window_icon,
            args=("RakeGlossary", icon_path),
            daemon=True,
        ).start()

    webview.start(debug=False)

    log.info("Window closed. Backend will stop with the process.")

# ---------------------------------------------------------------------------
# Windows window icon helper
# ---------------------------------------------------------------------------


def _resolve_icon_path() -> Path | None:
    """Return the path to the .ico icon, in both dev and frozen modes."""
    if getattr(sys, "frozen", False):
        # PyInstaller: assets/ was bundled via build.spec
        candidate = Path(sys._MEIPASS) / "assets" / "icon.ico"  # type: ignore[attr-defined]
    else:
        # Dev mode: desktop/assets/icon.ico relative to this file
        candidate = Path(__file__).resolve().parent / "assets" / "icon.ico"
    return candidate if candidate.is_file() else None


def _force_windows_window_icon(window_title: str, ico_path: Path) -> None:
    """Set the window + taskbar icon on Windows via ctypes.

    pywebview's `icon=` parameter is not always honored on Windows when
    using the EdgeChromium backend, so we set the icon ourselves after
    the window has been created.

    Runs in a background thread because the window doesn't exist yet at
    the time main() calls this.
    """
    if sys.platform != "win32":
        return

    import ctypes

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]

    WM_SETICON = 0x0080
    ICON_SMALL = 0
    ICON_BIG = 1
    IMAGE_ICON = 1
    LR_LOADFROMFILE = 0x0000
    LR_DEFAULTSIZE = 0x0040
    SM_CXSMICON = 49
    SM_CYSMICON = 50

    # Poll for the window to appear (up to ~10 seconds)
    hwnd = 0
    for _ in range(100):
        hwnd = user32.FindWindowW(None, window_title)
        if hwnd:
            break
        time.sleep(0.1)

    if not hwnd:
        log.warning(f"Could not find window '{window_title}' to set icon.")
        return

    ico_str = str(ico_path)

    hicon_big = user32.LoadImageW(
        None, ico_str, IMAGE_ICON, 0, 0,
        LR_LOADFROMFILE | LR_DEFAULTSIZE,
    )
    hicon_small = user32.LoadImageW(
        None, ico_str, IMAGE_ICON,
        user32.GetSystemMetrics(SM_CXSMICON),
        user32.GetSystemMetrics(SM_CYSMICON),
        LR_LOADFROMFILE,
    )

    if hicon_big:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
    if hicon_small:
        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)

    log.info(f"Window icon applied from {ico_path}")

if __name__ == "__main__":
    main()