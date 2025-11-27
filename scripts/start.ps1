# RelayX Auto-Start Script
# Automatically starts all RelayX services

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RelayX AI Caller - Starting" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Check if ngrok is installed
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokPath) {
    Write-Host "ERROR: ngrok not found!" -ForegroundColor Red
    Write-Host "Install: winget install ngrok" -ForegroundColor Yellow
    exit 1
}

Write-Host "Prerequisites OK" -ForegroundColor Green
Write-Host ""

# Kill any existing processes on ports 8000 and 8001
Write-Host "Cleaning up old processes..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000,8001 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 1

# Start Backend API
Write-Host ""
Write-Host "Starting Backend API (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; .\venv\Scripts\Activate.ps1; cd backend; `$host.ui.RawUI.WindowTitle='RelayX Backend'; python main.py"
)

# Wait for backend to start
Write-Host "   Waiting for backend..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Test backend health
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
    Write-Host "   Backend OK | DB: $($health.database) | LLM: $($health.llm)" -ForegroundColor Green
} catch {
    Write-Host "   Backend started but health check failed" -ForegroundColor Yellow
}

# Start Voice Gateway (with auto-ngrok)
Write-Host ""
Write-Host "Starting Voice Gateway + Auto-ngrok (Port 8001)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PWD'; .\venv\Scripts\Activate.ps1; cd voice_gateway; `$host.ui.RawUI.WindowTitle='RelayX Voice Gateway'; python voice_gateway.py"
)

# Wait for voice gateway and ngrok
Write-Host "   Waiting for voice gateway and ngrok tunnel..." -ForegroundColor Gray
Start-Sleep -Seconds 8

# Get ngrok public URL
try {
    $ngrokApi = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -Method Get
    $publicUrl = $ngrokApi.tunnels[0].public_url
    Write-Host "   Voice Gateway ready!" -ForegroundColor Green
    Write-Host "   Public URL: $publicUrl" -ForegroundColor Cyan
} catch {
    Write-Host "   Could not get ngrok URL (may still be starting)" -ForegroundColor Yellow
    $publicUrl = "http://localhost:8001"
}

# Open Dashboard
Write-Host ""
Write-Host "Opening Web Dashboard..." -ForegroundColor Magenta
Start-Sleep -Seconds 2
Start-Process "http://localhost:8000/dashboard"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  RelayX is Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Dashboard:     http://localhost:8000/dashboard" -ForegroundColor Cyan
Write-Host "Backend API:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "Voice Gateway: $publicUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop services" -ForegroundColor Gray
Write-Host ""
