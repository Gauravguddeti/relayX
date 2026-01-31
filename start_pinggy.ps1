# Pinggy - Free tunnel (no signup, no credit card!)
Write-Host "Starting Pinggy tunnel..." -ForegroundColor Cyan
Write-Host ""

# Download pinggy if not exists
if (-not (Test-Path "pinggy.exe")) {
    Write-Host "Downloading Pinggy..." -ForegroundColor Yellow
    # Use the correct GitHub releases URL
    Invoke-WebRequest -Uri "https://github.com/Pinggy-io/pinggy_cli/releases/latest/download/pinggy_windows_amd64.exe" -OutFile "pinggy.exe"
    Write-Host "Downloaded successfully!" -ForegroundColor Green
}

Write-Host "Starting tunnel on port 8001..." -ForegroundColor Cyan
Write-Host "Tunnel URL will be displayed below:" -ForegroundColor Yellow
Write-Host ""

# Start tunnel - use http mode for port 8001
.\pinggy.exe http 8001

# The URL will be displayed in the output
