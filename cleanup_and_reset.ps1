# RelayX Docker Cleanup and Reset Script
# This script will completely clean Docker and remove local Python dependencies

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  RelayX Docker Cleanup & Reset" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Confirm action
$confirmation = Read-Host "This will DELETE all Docker containers, images, volumes, and build cache. Continue? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "Step 1: Stopping all running containers..." -ForegroundColor Yellow
docker-compose down
docker stop $(docker ps -aq) 2>$null

Write-Host ""
Write-Host "Step 2: Removing all containers..." -ForegroundColor Yellow
docker rm -f $(docker ps -aq) 2>$null

Write-Host ""
Write-Host "Step 3: Removing all images..." -ForegroundColor Yellow
docker rmi -f $(docker images -q) 2>$null

Write-Host ""
Write-Host "Step 4: Removing all volumes..." -ForegroundColor Yellow
docker volume rm $(docker volume ls -q) 2>$null

Write-Host ""
Write-Host "Step 5: Removing all networks (except defaults)..." -ForegroundColor Yellow
docker network prune -f

Write-Host ""
Write-Host "Step 6: Cleaning build cache..." -ForegroundColor Yellow
docker builder prune -a -f

Write-Host ""
Write-Host "Step 7: Full system prune..." -ForegroundColor Yellow
docker system prune -a --volumes -f

Write-Host ""
Write-Host "Step 8: Removing Python cache and local packages..." -ForegroundColor Yellow

# Remove Python cache directories
Get-ChildItem -Path . -Include __pycache__,*.pyc,*.pyo,.pytest_cache,.mypy_cache -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Remove local Python virtual environments if any
if (Test-Path "venv") {
    Write-Host "  - Removing venv folder..." -ForegroundColor Gray
    Remove-Item -Recurse -Force venv
}
if (Test-Path ".venv") {
    Write-Host "  - Removing .venv folder..." -ForegroundColor Gray
    Remove-Item -Recurse -Force .venv
}

# Remove pip cache
Write-Host "  - Cleaning pip cache..." -ForegroundColor Gray
pip cache purge 2>$null

# Remove Piper TTS cache (voice models)
$piperCache = "$env:USERPROFILE\.local\share\piper"
if (Test-Path $piperCache) {
    Write-Host "  - Removing Piper TTS cache (voice models)..." -ForegroundColor Gray
    Remove-Item -Recurse -Force $piperCache
}

# Remove Whisper model cache
$whisperCache = "$env:USERPROFILE\.cache\whisper"
if (Test-Path $whisperCache) {
    Write-Host "  - Removing Whisper model cache..." -ForegroundColor Gray
    Remove-Item -Recurse -Force $whisperCache
}

# Remove torch hub cache (Silero VAD)
$torchCache = "$env:USERPROFILE\.cache\torch"
if (Test-Path $torchCache) {
    Write-Host "  - Removing PyTorch/Silero cache..." -ForegroundColor Gray
    Remove-Item -Recurse -Force $torchCache
}

Write-Host ""
Write-Host "Step 9: Checking Docker disk usage..." -ForegroundColor Yellow
docker system df

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Cleanup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Docker has been reset to a clean state." -ForegroundColor Cyan
Write-Host "All local Python caches and models removed." -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: docker-compose build --no-cache" -ForegroundColor White
Write-Host "  2. Run: docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "This will rebuild containers from scratch with dependencies inside Docker only." -ForegroundColor Gray
