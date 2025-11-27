# RelayX Docker Start Script
# Starts all RelayX services using Docker Compose

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RelayX AI Caller - Docker Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerPath) {
    Write-Host "ERROR: Docker not found!" -ForegroundColor Red
    Write-Host "Install: winget install Docker.DockerDesktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
try {
    docker ps | Out-Null
} catch {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and configure your API keys" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to continue anyway or Ctrl+C to exit"
}

Write-Host "Prerequisites OK" -ForegroundColor Green
Write-Host ""

# Stop any existing containers
Write-Host "Stopping existing containers..." -ForegroundColor Yellow
docker-compose down 2>&1 | Out-Null

# Build and start containers
Write-Host "Building and starting containers..." -ForegroundColor Cyan
docker-compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Waiting for services to start..." -ForegroundColor Gray
    Start-Sleep -Seconds 10

    # Test backend health
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 5
        Write-Host "Backend OK | DB: $($health.database) | LLM: $($health.llm)" -ForegroundColor Green
    } catch {
        Write-Host "Backend starting (health check pending)" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  RelayX is Ready!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dashboard:     http://localhost:8000/dashboard" -ForegroundColor Cyan
    Write-Host "Backend API:   http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "Voice Gateway: http://localhost:8001" -ForegroundColor Cyan
    Write-Host "Ngrok UI:      http://localhost:4040" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "View logs:     docker-compose logs -f" -ForegroundColor Gray
    Write-Host "Stop services: docker-compose down" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to start containers" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}
