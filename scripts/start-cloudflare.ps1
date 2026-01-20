# RelayX Startup Script with Cloudflare Tunnel
# Replaces ngrok with cloudflared for better reliability

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   RelayX Voice AI Platform" -ForegroundColor Cyan
Write-Host "   Starting with Cloudflare Tunnel" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if cloudflared is installed
$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "❌ cloudflared not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Cloudflare Tunnel:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" -ForegroundColor White
    Write-Host "  2. Or use Chocolatey: choco install cloudflared" -ForegroundColor White
    Write-Host ""
    Write-Host "Falling back to ngrok..." -ForegroundColor Yellow
    & "$PSScriptRoot\start-docker.ps1"
    exit 1
}

Write-Host "✅ Cloudflare Tunnel found" -ForegroundColor Green
Write-Host ""

# Check Docker
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    Write-Host "❌ Docker not found! Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker found" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Starting RelayX services..." -ForegroundColor Cyan
Write-Host ""

# Start Docker Compose (without ngrok container)
Write-Host "📦 Building and starting containers..." -ForegroundColor Yellow
docker-compose up -d backend voice-gateway frontend redis

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Failed to start containers" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Containers started successfully" -ForegroundColor Green
Write-Host ""

# Wait for services to be ready
Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Check service health
Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Cyan
Write-Host ""

$backendHealthy = $false
$voiceGatewayHealthy = $false
$frontendHealthy = $false
$redisHealthy = $false

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ Backend is healthy" -ForegroundColor Green
        $backendHealthy = $true
    }
} catch {
    Write-Host "  ⚠️  Backend health check failed" -ForegroundColor Yellow
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ Voice Gateway is healthy" -ForegroundColor Green
        $voiceGatewayHealthy = $true
    }
} catch {
    Write-Host "  ⚠️  Voice Gateway health check failed" -ForegroundColor Yellow
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ Frontend is healthy" -ForegroundColor Green
        $frontendHealthy = $true
    }
} catch {
    Write-Host "  ⚠️  Frontend health check failed" -ForegroundColor Yellow
}

try {
    docker exec relayx-redis redis-cli ping | Out-Null
    Write-Host "  ✅ Redis is healthy" -ForegroundColor Green
    $redisHealthy = $true
} catch {
    Write-Host "  ⚠️  Redis health check failed" -ForegroundColor Yellow
}

Write-Host ""

# Start Cloudflare Tunnel
Write-Host "🌐 Starting Cloudflare Tunnel..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Tunneling localhost:8001 (Voice Gateway)" -ForegroundColor White
Write-Host ""

# Start cloudflared in background
$cloudflaredJob = Start-Job -ScriptBlock {
    cloudflared tunnel --url http://localhost:8001 --no-autoupdate
}

# Wait a moment for tunnel to start
Start-Sleep -Seconds 5

# Try to get tunnel URL from cloudflared logs
Write-Host "🔗 Cloudflare Tunnel URL:" -ForegroundColor Yellow
Write-Host ""

$logOutput = Receive-Job -Job $cloudflaredJob -ErrorAction SilentlyContinue
if ($logOutput -match "https://[a-z0-9-]+\.trycloudflare\.com") {
    $tunnelUrl = $matches[0]
    Write-Host "  $tunnelUrl" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Copy this URL and set it as VOICE_GATEWAY_URL in your .env file" -ForegroundColor Cyan
} else {
    Write-Host "  Tunnel starting... Check output above for URL" -ForegroundColor Yellow
    Write-Host "  Or visit: http://localhost:4040 (if tunnel dashboard is available)" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   🎉 RelayX is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Service URLs:" -ForegroundColor Cyan
Write-Host "  • Frontend:      http://localhost:3000" -ForegroundColor White
Write-Host "  • Backend API:   http://localhost:8000" -ForegroundColor White
Write-Host "  • Voice Gateway: http://localhost:8001" -ForegroundColor White
Write-Host "  • Redis:         redis://localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitoring:" -ForegroundColor Cyan
Write-Host "  • Backend logs:  docker-compose logs -f backend" -ForegroundColor White
Write-Host "  • Voice logs:    docker-compose logs -f voice-gateway" -ForegroundColor White
Write-Host "  • Cache stats:   docker exec relayx-redis redis-cli INFO stats" -ForegroundColor White
Write-Host ""
Write-Host "⚡ Performance Enhancements:" -ForegroundColor Cyan
Write-Host "  • LLM Model: Llama 3.3 70B Versatile" -ForegroundColor White
Write-Host "  • Redis caching enabled" -ForegroundColor White
Write-Host "  • Speculative STT active" -ForegroundColor White
Write-Host "  • Cloudflare Tunnel (faster than ngrok)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow
Write-Host ""

# Keep script running and show live logs
try {
    docker-compose logs -f --tail=50
} finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    Stop-Job -Job $cloudflaredJob -ErrorAction SilentlyContinue
    Remove-Job -Job $cloudflaredJob -ErrorAction SilentlyContinue
    docker-compose down
    Write-Host "✅ Services stopped" -ForegroundColor Green
}
