@echo off
echo ========================================
echo    RelayX AI Caller - Starting Services
echo ========================================
echo.

REM Use the new PowerShell script that handles Docker and Cloudflare Tunnel
powershell -ExecutionPolicy Bypass -File "%~dp0start_relayx.ps1"

echo.
pause
