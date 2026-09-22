# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for RakeGlossary desktop app.

Build with (from project root):
    pyinstaller desktop/build.spec

Output:
    dist/RakeGlossary/RakeGlossary.exe  (one-folder mode)
"""

import sys
from PyInstaller.utils.hooks import collect_data_files
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# PyInstaller sets SPECPATH to the directory containing this file
SPEC_DIR = Path(SPECPATH)  # desktop/
PROJECT_ROOT = SPEC_DIR.parent  # rakeglossary/

BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
LAUNCHER = SPEC_DIR / "launcher.py"

# spaCy model location
import en_core_web_sm  # noqa: E402
SPACY_MODEL_DIR = Path(en_core_web_sm.__file__).parent

# NLTK data location (minimal bundle shipped with the app)
NLTK_DATA = BACKEND_DIR / "nltk_data_minimal"

# LLM providers JSON
LLM_PROVIDERS = (
    BACKEND_DIR / "app" / "pipeline" / "definitions" / "llm_providers.json"
)

# Sanity checks
for p in (FRONTEND_DIST, LAUNCHER, SPACY_MODEL_DIR, NLTK_DATA, LLM_PROVIDERS):
    if not p.exists():
        raise SystemExit(f"Required path does not exist: {p}")

print(f"[spec] project_root   = {PROJECT_ROOT}")
print(f"[spec] backend_dir    = {BACKEND_DIR}")
print(f"[spec] frontend_dist  = {FRONTEND_DIST}")
print(f"[spec] spacy_model    = {SPACY_MODEL_DIR}")
print(f"[spec] nltk_data      = {NLTK_DATA}")
print(f"[spec] llm_providers  = {LLM_PROVIDERS}")


# ---------------------------------------------------------------------------
# Data files bundled into the app
# ---------------------------------------------------------------------------

# YAKE ships stopword lists inside its package — PyInstaller doesn't
# pick them up automatically.
yake_datas = collect_data_files("yake")

datas = [
    # Frontend SPA
    (str(FRONTEND_DIST), "frontend/dist"),

    # LLM providers config
    (str(LLM_PROVIDERS), "backend/app/pipeline/definitions"),

    # spaCy English model
    (str(SPACY_MODEL_DIR), "en_core_web_sm"),

    # NLTK data (stopwords, punkt, ...)
    (str(NLTK_DATA / "corpora"), "nltk_data/corpora"),
    (str(NLTK_DATA / "tokenizers"), "nltk_data/tokenizers"),
] + yake_datas


# ---------------------------------------------------------------------------
# Hidden imports (PyInstaller cannot always infer these)
# ---------------------------------------------------------------------------

hiddenimports = [
    # Uvicorn dynamic imports
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",

    # SQLAlchemy sqlite driver
    "sqlalchemy.dialects.sqlite",

    # spaCy English model
    "en_core_web_sm",

    # Pydantic v2 dynamic pieces
    "pydantic.deprecated.decorator",
]


# ---------------------------------------------------------------------------
# Excludes: keep the bundle lean
# ---------------------------------------------------------------------------

excludes = [
    "tkinter",
    "matplotlib",
    "IPython",
    "pytest",
    "tests",
    # --- Optional offline translation (moved to [offline] extra) ---
    # Excluded from the default bundle to save ~500 MB.
    # Users who need offline translation can install it separately.
    "argostranslate",
    "stanza",
    "torch",
    "torchvision",
    "torchaudio",
    "torchtext",
    "torchdata",
    "ctranslate2",
    "onnxruntime",
    "transformers",
]


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

block_cipher = None

a = Analysis(
    [str(LAUNCHER)],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[str(SPEC_DIR / "hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)


# ---------------------------------------------------------------------------
# EXE + COLLECT (one-folder mode)
# ---------------------------------------------------------------------------

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RakeGlossary",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # set to False after debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # auto (ARM64 on this machine)
    codesign_identity=None,
    entitlements_file=None,
    # icon=str(SPEC_DIR / "assets" / "icon.ico"),  # add later
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RakeGlossary",
)