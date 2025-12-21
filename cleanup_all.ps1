#!/usr/bin/env pwsh
# Complete Docker and Python cleanup script

Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "  RelayX Complete Cleanup" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Stop all containers
Write-Host "`nStep 1: Stopping all RelayX containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>$null

# Remove ALL Docker images, containers, volumes
Write-Host "`nStep 2: Removing ALL Docker resources..." -ForegroundColor Yellow
docker system prune -af --volumes 2>$null

# Remove Docker build cache
Write-Host "`nStep 3: Clearing Docker build cache..." -ForegroundColor Yellow
docker builder prune -af 2>$null

# Remove Python cache files
Write-Host "`nStep 4: Removing Python cache files..." -ForegroundColor Yellow
Get-ChildItem -Path . -Include __pycache__,*.pyc,*.pyo,.pytest_cache -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Remove local pip packages (if any were installed locally)
Write-Host "`nStep 5: Checking for local Python packages..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  Removing venv folder..." -ForegroundColor Red
    Remove-Item -Path "venv" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path ".venv") {
    Write-Host "  Removing .venv folder..." -ForegroundColor Red
    Remove-Item -Path ".venv" -Recurse -Force -ErrorAction SilentlyContinue
}

# Check Docker space
Write-Host "`nStep 6: Checking Docker disk usage..." -ForegroundColor Yellow
docker system df

Write-Host "`n=====================================" -ForegroundColor Green
Write-Host "  Cleanup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Run: .\rebuild_docker.ps1" -ForegroundColor White
Write-Host "  2. Docker will download ONLY minimal packages" -ForegroundColor White
Write-Host "  3. No torch, numpy, whisper, or heavy ML libs!" -ForegroundColor White
Write-Host "`nExpected Docker size: ~2-3GB (down from 10-20GB)" -ForegroundColor Green
