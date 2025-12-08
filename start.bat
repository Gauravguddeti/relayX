@echo off
echo ========================================
echo    RelayX AI Caller - Starting Services
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [2/3] Starting Backend on port 8000...
start "RelayX Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

echo [3/3] Starting Voice Gateway on port 8001...
start "RelayX Voice Gateway" cmd /k "cd /d %~dp0voice_gateway && python voice_gateway.py"

echo.
echo ========================================
echo    Services Started Successfully!
echo ========================================
echo.
echo Backend:        http://localhost:8000
echo Voice Gateway:  http://localhost:8001
echo Dashboard:      http://localhost:8000/static/dashboard.html
echo.
echo Press any key to stop all services...
pause >nul

echo.
echo Stopping services...
taskkill /FI "WindowTitle eq RelayX Backend*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq RelayX Voice Gateway*" /T /F >nul 2>&1

echo Services stopped.
pause
