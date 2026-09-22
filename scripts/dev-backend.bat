@echo off
setlocal EnableDelayedExpansion

set "SCRIPTS_DIR=%~dp0"
for %%I in ("%SCRIPTS_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "BACKEND_DIR=%PROJECT_ROOT%\backend"

REM --- Locate the venv ---
set "VENV_DIR="
for %%C in (
    "%PROJECT_ROOT%\..\venv312"
    "%PROJECT_ROOT%\venv312"
    "%PROJECT_ROOT%\.venv"
) do (
    if not defined VENV_DIR (
        if exist "%%~fC\Scripts\python.exe" set "VENV_DIR=%%~fC"
    )
)

if not defined VENV_DIR (
    echo [X] No venv found. Searched:
    echo       %PROJECT_ROOT%\..\venv312
    echo       %PROJECT_ROOT%\venv312
    echo       %PROJECT_ROOT%\.venv
    echo.
    echo     Run scripts\setup.bat first.
    pause
    exit /b 1
)

REM --- Check backend exists ---
if not exist "%BACKEND_DIR%\app\main.py" (
    echo [X] Backend not found at "%BACKEND_DIR%".
    pause
    exit /b 1
)

REM --- Check port 8765 ---
netstat -ano -p tcp 2>nul | findstr /R /C:"LISTENING" | findstr /C:":8765 " >nul
if %errorlevel% equ 0 (
    echo [X] Port 8765 is already in use.
    echo     Stop the other backend first.
    pause
    exit /b 1
)

title RakeGlossary - Backend

call "%VENV_DIR%\Scripts\activate.bat"

cd /d "%BACKEND_DIR%"

REM --- Print python version for confirmation ---
for /f "delims=" %%V in ('python --version 2^>^&1') do set "PY_VERSION=%%V"

echo ============================================================
echo   RakeGlossary Backend
echo   http://127.0.0.1:8765        (API + SSE)
echo   http://127.0.0.1:8765/docs   (Swagger UI)
echo ============================================================
echo   Venv    : %VENV_DIR%
echo   Backend : %BACKEND_DIR%
echo   Python  : %PY_VERSION%
echo ============================================================
echo   Press Ctrl+C to stop.
echo ============================================================
echo.

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% neq 0 (
    echo [X] Backend exited with code %EXIT_CODE%.
    echo     See the log above for details.
) else (
    echo [i] Backend stopped normally.
)
echo.
pause
exit /b %EXIT_CODE%