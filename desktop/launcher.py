"""RakeGlossary desktop launcher.

Starts the FastAPI backend in a background thread, then opens a native
window (WebView2 on Windows) pointing at the served SPA.

Run from the project root:
    python desktop/launcher.py

In production (PyInstaller bundle), the frontend build is expected at
`frontend/dist/` and the backend at `backend/app/`.
"""

from __future__ import annotations

import base64
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
# Log redirection (must run BEFORE logging.basicConfig)
#
# When built with console=False, sys.stdout and sys.stderr are None in the
# frozen .exe. Redirect them to a log file so:
#   - uvicorn / loguru / logging don't crash on None
#   - users can still find logs for debugging
# ---------------------------------------------------------------------------


def _setup_log_redirection() -> None:
    """Redirect stdout/stderr to a log file in %APPDATA%\\RakeGlossary\\logs.

    Only active when running as a frozen .exe (console=False). In dev mode
    (python desktop/launcher.py), we keep stdout/stderr attached to the
    console for immediate feedback.
    """
    if not getattr(sys, "frozen", False):
        return

    # Where to put the log file
    appdata = os.getenv("APPDATA")
    if appdata:
        log_dir = Path(appdata) / "RakeGlossary" / "logs"
    else:
        log_dir = Path.home() / ".rakeglossary" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "launcher.log"

    # Rotate: keep the previous session's log
    if log_file.exists():
        backup = log_file.with_suffix(".prev.log")
        try:
            if backup.exists():
                backup.unlink()
            log_file.rename(backup)
        except OSError:
            pass

    # Open in line-buffered mode for real-time writes
    f = open(log_file, "w", encoding="utf-8", buffering=1)

    # On Windows with console=False, stdout/stderr can be None.
    # Some libraries call sys.stdout.isatty() or sys.stderr.fileno().
    # We give them the file handle, which supports both.
    sys.stdout = f
    sys.stderr = f

    # Silence "no console" complaints from Python
    import io

    if sys.stdin is None:
        sys.stdin = io.StringIO()


# Must run before logging.basicConfig and before any imports that log
_setup_log_redirection()

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
# Splash screen (shown while the backend starts)
# ---------------------------------------------------------------------------

_SPLASH_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body {
    width: 100%; height: 100%;
    overflow: hidden;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    user-select: none;
    cursor: default;
  }
  body {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: linear-gradient(135deg, #6366F1 0%, #4338CA 100%);
    color: white;
    padding: 24px;
    -webkit-app-region: drag;
  }
  .icon {
    width: 84px; height: 84px;
    margin-bottom: 18px;
    filter: drop-shadow(0 6px 14px rgba(0,0,0,0.28));
    pointer-events: none;
  }
  h1 {
    font-size: 22px; font-weight: 600;
    letter-spacing: 0.3px;
    margin-bottom: 4px;
  }
  .subtitle {
    font-size: 11.5px;
    opacity: 0.82;
    margin-bottom: 26px;
  }
  .spinner {
    width: 26px; height: 26px;
    border: 3px solid rgba(255,255,255,0.25);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  .loading-text {
    margin-top: 14px;
    font-size: 12px;
    opacity: 0.9;
    letter-spacing: 0.2px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
  <img class="icon" src="data:image/png;base64,{icon_b64}" alt="">
  <h1>RakeGlossary</h1>
  <div class="subtitle">Automated Glossary Generator</div>
  <div class="spinner"></div>
  <div class="loading-text">Starting up…</div>
</body>
</html>"""


def _build_splash_html() -> str:
    """Build the splash screen HTML with the app icon inline as base64."""
    icon_b64 = ""
    icon_path = _resolve_icon_path()
    if icon_path is not None:
        try:
            icon_b64 = base64.b64encode(icon_path.read_bytes()).decode("ascii")
        except OSError as exc:
            log.warning(f"Could not read icon for splash: {exc}")
    return _SPLASH_HTML_TEMPLATE.replace("{icon_b64}", icon_b64)

# ---------------------------------------------------------------------------
# Port management
# ---------------------------------------------------------------------------
def _center_position(width: int, height: int) -> tuple[int, int] | None:
    """Return (x, y) to center a window on the primary monitor.

    Returns None if the screen size can't be determined (falls back to
    letting the OS decide).
    """
    try:
        if sys.platform == "win32":
            import ctypes

            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            # SM_CXSCREEN = 0, SM_CYSCREEN = 1 (primary monitor)
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
            if screen_w <= 0 or screen_h <= 0:
                return None
            x = max(0, (screen_w - width) // 2)
            y = max(0, (screen_h - height) // 2)
            return (x, y)
    except Exception as exc:  # noqa: BLE001
        log.warning(f"Could not compute center position: {exc}")
    return None

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

    icon_path = _resolve_icon_path()

    # 1) Create ONE window. It starts with the splash HTML, then we
    #    navigate it to the app URL once the backend is ready. This way
    #    the window keeps its size/position from start to finish (no
    #    "jump" between splash and main window).
    main_w, main_h = 1280, 800
    main_pos = _center_position(main_w, main_h)

    window_kwargs: dict = {
        "title": "RakeGlossary",
        "html": _build_splash_html(),
        "width": main_w,
        "height": main_h,
        "min_size": (900, 600),
        "text_select": True,
    }
    if main_pos is not None:
        window_kwargs["x"] = main_pos[0]
        window_kwargs["y"] = main_pos[1]

    window = webview.create_window(**window_kwargs)

    # 2) Start the backend in a background thread
    backend_thread = threading.Thread(
        target=_run_backend,
        args=(HOST, port),
        daemon=True,
        name="uvicorn-backend",
    )
    backend_thread.start()

    # 3) Runs inside pywebview's GUI event loop right after the window
    #    is created. A worker thread waits for the backend and then
    #    swaps the splash for the real app.
    def _on_started() -> None:
        def _wait_and_navigate() -> None:
            if not _wait_for_server(HOST, port):
                log.error("Backend did not start within the timeout. Exiting.")
                os._exit(1)

            log.info("Backend is up. Loading application...")

            # Load the real app in the SAME window (no jump)
            try:
                window.load_url(f"http://{HOST}:{port}/")
            except Exception as exc:  # noqa: BLE001
                log.error(f"Failed to load app URL: {exc}")

            # Apply the window icon on Windows
            if icon_path is not None:
                threading.Thread(
                    target=_force_windows_window_icon,
                    args=("RakeGlossary", icon_path),
                    daemon=True,
                ).start()

        threading.Thread(target=_wait_and_navigate, daemon=True).start()

    # 4) Start the GUI loop
    webview.start(func=_on_started, debug=False)

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