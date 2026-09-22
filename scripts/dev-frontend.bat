@echo off
setlocal EnableDelayedExpansion

set "SCRIPTS_DIR=%~dp0"
for %%I in ("%SCRIPTS_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"

if not exist "%FRONTEND_DIR%\package.json" (
    echo [X] Frontend not found at "%FRONTEND_DIR%".
    pause
    exit /b 1
)

REM --- Check port 5173 ---
netstat -ano -p tcp 2>nul | findstr /R /C:"LISTENING" | findstr /C:":5173 " >nul
if %errorlevel% equ 0 (
    echo [X] Port 5173 is already in use.
    echo     Stop the other frontend first.
    pause
    exit /b 1
)

title RakeGlossary - Frontend

cd /d "%FRONTEND_DIR%"

REM --- Print node version for confirmation ---
for /f "delims=" %%V in ('node --version 2^>^&1') do set "NODE_VERSION=%%V"

echo ============================================================
echo   RakeGlossary Frontend
echo   http://localhost:5173
echo ============================================================
echo   Frontend : %FRONTEND_DIR%
echo   Node     : %NODE_VERSION%
echo ============================================================
echo   Press Ctrl+C to stop.
echo ============================================================
echo.

call npm run dev
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE% neq 0 (
    echo [X] Frontend exited with code %EXIT_CODE%.
) else (
    echo [i] Frontend stopped normally.
)
echo.
pause
exit /b %EXIT_CODE%