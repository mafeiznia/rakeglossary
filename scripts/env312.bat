@echo off
REM ============================================================
REM  RakeGlossary — Interactive CMD with venv activated
REM  Opens a new cmd window with the Python venv ready to use.
REM ============================================================

set "SCRIPTS_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPTS_DIR%.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"

REM --- Locate venv (same search order as dev.bat / setup.bat) ---
set "VENV_DIR="
if exist "%PROJECT_ROOT%\..\venv312\Scripts\activate.bat" set "VENV_DIR=%PROJECT_ROOT%\..\venv312"
if not defined VENV_DIR if exist "%PROJECT_ROOT%\venv312\Scripts\activate.bat" set "VENV_DIR=%PROJECT_ROOT%\venv312"
if not defined VENV_DIR if exist "%PROJECT_ROOT%\.venv\Scripts\activate.bat" set "VENV_DIR=%PROJECT_ROOT%\.venv"

if not defined VENV_DIR (
    echo.
    echo [X] No venv found. Looked in:
    echo       %PROJECT_ROOT%\..\venv312
    echo       %PROJECT_ROOT%\venv312
    echo       %PROJECT_ROOT%\.venv
    echo.
    echo     Run scripts\setup.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "%BACKEND_DIR%" (
    echo [X] Backend folder not found: %BACKEND_DIR%
    pause
    exit /b 1
)

REM --- Activate venv and cd into backend in THIS shell ---
call "%VENV_DIR%\Scripts\activate.bat"
cd /d "%BACKEND_DIR%"

echo ============================================================
echo   RakeGlossary - Interactive CMD
echo ============================================================
echo   Venv    : %VENV_DIR%
echo   Workdir : %BACKEND_DIR%
echo ============================================================
echo.
echo   Ready. Try:
echo     python -m pytest tests/ -v
echo     python -m uvicorn app.main:app --reload --port 8765
echo.
echo   Type 'exit' to close this window.
echo ============================================================
echo.

REM Start an interactive child cmd — it inherits the activated venv
cmd