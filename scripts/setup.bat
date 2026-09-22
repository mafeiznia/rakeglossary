REM این را فقط یک بار اجرا می‌کنی (یا هر وقت pyproject.toml یا package.json تغییر کرد).
@echo off
setlocal

REM ============================================================
REM  RakeGlossary — One-time setup script
REM  Installs backend (Python) and frontend (Node) dependencies
REM ============================================================

set "PROJECT_ROOT=%~dp0.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

REM --- Locate the venv -----------------------------------------
REM  Try common locations; first one that exists wins.
set "VENV_DIR="
if exist "%PROJECT_ROOT%\..\venv312\Scripts\python.exe" set "VENV_DIR=%PROJECT_ROOT%\..\venv312"
if not defined VENV_DIR if exist "%PROJECT_ROOT%\venv312\Scripts\python.exe" set "VENV_DIR=%PROJECT_ROOT%\venv312"
if not defined VENV_DIR if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" set "VENV_DIR=%PROJECT_ROOT%\.venv"

echo ============================================================
echo   RakeGlossary Setup
echo ============================================================
echo   Project root : %PROJECT_ROOT%
echo   Backend dir  : %BACKEND_DIR%
echo   Frontend dir : %FRONTEND_DIR%
echo   Venv         : %VENV_DIR%
echo ============================================================
echo.

REM --- Create venv if it does not exist ------------------------
if not defined VENV_DIR (
    echo [i] No venv found. Creating one at %PROJECT_ROOT%\venv312 ...
    python -m venv "%PROJECT_ROOT%\venv312"
    if errorlevel 1 (
        echo.
        echo [X] Failed to create venv. Is Python 3.12 installed and on PATH?
        pause
        exit /b 1
    )
    set "VENV_DIR=%PROJECT_ROOT%\venv312"
)

REM --- Backend --------------------------------------------------
echo.
echo [1/2] Installing backend dependencies (this may take a while)...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [X] Could not activate venv.
    pause
    exit /b 1
)

cd /d "%BACKEND_DIR%"
python -m pip install --upgrade pip
pip install -e ".[dev]"
if errorlevel 1 (
    echo.
    echo [X] Backend dependency installation failed.
    call deactivate
    pause
    exit /b 1
)

REM --- spaCy model --------------------------------------------
echo.
echo [i] Checking spaCy English model...
python -c "import spacy; spacy.load('en_core_web_sm')" 2>nul
if errorlevel 1 (
    echo [i] Downloading en_core_web_sm ...
    python -m spacy download en_core_web_sm
)

REM --- NLTK data ----------------------------------------------
echo.
echo [i] Checking NLTK data...
python -c "import nltk; nltk.data.find('corpora/stopwords'); nltk.data.find('tokenizers/punkt'); nltk.data.find('tokenizers/punkt_tab')" 2>nul
if errorlevel 1 (
    echo [i] Downloading NLTK resources ...
    set "NLTK_ALLOW_PROXIED_URLOPEN=1"
    python -c "import nltk; nltk.download('stopwords', quiet=True); nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)"
)

call deactivate

REM --- Frontend ------------------------------------------------
echo.
echo [2/2] Installing frontend dependencies...
cd /d "%FRONTEND_DIR%"
call npm install
if errorlevel 1 (
    echo.
    echo [X] Frontend dependency installation failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Setup complete!
echo ============================================================
echo   Next steps:
echo     - Double-click scripts\dev.bat to start both servers
echo ============================================================
echo.
pause