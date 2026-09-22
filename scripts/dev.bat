@echo off
setlocal EnableDelayedExpansion

set "SCRIPTS=%~dp0"
for %%I in ("%SCRIPTS%..") do set "PROJECT_ROOT=%%~fI"

echo ============================================================
echo   RakeGlossary - Starting dev environment
echo ============================================================
echo.

REM --- Check backend exists ---
if not exist "%PROJECT_ROOT%\backend\app\main.py" (
    echo [X] Backend not found at "%PROJECT_ROOT%\backend".
    echo     Run scripts\setup.bat first.
    pause
    exit /b 1
)

REM --- Check frontend exists ---
if not exist "%PROJECT_ROOT%\frontend\package.json" (
    echo [X] Frontend not found at "%PROJECT_ROOT%\frontend".
    echo     Run scripts\setup.bat first.
    pause
    exit /b 1
)

REM --- Check ports ---
call :check_port 8765 "Backend"
if errorlevel 1 (
    echo.
    echo [X] Port 8765 is already in use.
    echo     Another backend is running, or a different app is using it.
    echo     Close the other window and try again.
    pause
    exit /b 1
)

call :check_port 5173 "Frontend"
if errorlevel 1 (
    echo.
    echo [X] Port 5173 is already in use.
    echo     Another frontend is running, or a different app is using it.
    echo     Close the other window and try again.
    pause
    exit /b 1
)

echo [1/2] Starting backend in a new window...
start "RakeGlossary Backend" cmd /k ""%SCRIPTS%dev-backend.bat""

REM Give the backend a moment to bind the port
timeout /t 3 /nobreak >nul

echo [2/2] Starting frontend in a new window...
start "RakeGlossary Frontend" cmd /k ""%SCRIPTS%dev-frontend.bat""

echo.
echo ============================================================
echo   Both servers started in separate windows.
echo.
echo     Backend  : http://127.0.0.1:8765
echo     API Docs : http://127.0.0.1:8765/docs
echo     Frontend : http://localhost:5173
echo.
echo   Close the two windows to stop the servers.
echo ============================================================
echo.

timeout /t 5 /nobreak >nul
exit /b 0

REM ============================================================
REM  Helper: check whether a TCP port is already listening
REM  Usage: call :check_port <port> <label>
REM  Returns errorlevel=0 if free, errorlevel=1 if in use
REM ============================================================
:check_port
netstat -ano -p tcp 2>nul | findstr /R /C:"LISTENING" | findstr /C:":%~1 " >nul
if %errorlevel% equ 0 (
    echo [!] Port %~1 ^(%~2^) is already in use.
    exit /b 1
)
exit /b 0