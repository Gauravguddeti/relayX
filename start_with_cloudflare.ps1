# Start RelayX with Cloudflare Tunnel
Write-Host "Starting RelayX with Cloudflare Tunnel..." -ForegroundColor Cyan

# Stop existing containers
Write-Host "`n[1/3] Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Start containers (without ngrok)
Write-Host "`n[2/3] Starting containers..." -ForegroundColor Yellow
docker-compose up -d frontend backend voice-gateway redis

# Wait for services to be ready
Write-Host "`n[3/3] Starting Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "   Waiting for voice gateway..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Start cloudflared tunnel
$cloudflaredPath = "$PSScriptRoot\cloudflared.exe"

if (-not (Test-Path $cloudflaredPath)) {
    Write-Host "   ERROR: cloudflared not found. Run setup_cloudflare_tunnel.ps1 first" -ForegroundColor Red
    exit 1
}

Write-Host "   Starting tunnel..." -ForegroundColor Gray
$tunnelProcess = Start-Process -FilePath $cloudflaredPath -ArgumentList "tunnel", "run", "relayx-voice" -PassThru -NoNewWindow

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "RELAYX STARTED WITH CLOUDFLARE TUNNEL!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

# Get tunnel URL
Start-Sleep -Seconds 3
Write-Host "`nFetching tunnel URL..." -ForegroundColor Yellow

# Try to get the URL from cloudflared
$tunnelInfo = & $cloudflaredPath tunnel info relayx-voice 2>&1

Write-Host "`nTunnel is running!" -ForegroundColor Green
Write-Host "To get your public URL, check: https://dash.cloudflare.com" -ForegroundColor Yellow
Write-Host "`nIMPORTANT: Copy the tunnel URL and update your .env file:" -ForegroundColor Yellow
Write-Host "VOICE_GATEWAY_URL=https://your-tunnel-url.trycloudflare.com" -ForegroundColor Gray

Write-Host "`nServices:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  Voice GW:  http://localhost:8001" -ForegroundColor White
Write-Host "  Tunnel:    Running (check Cloudflare dashboard)" -ForegroundColor White

Write-Host "`nPress Ctrl+C to stop all services" -ForegroundColor Gray
Write-Host "To view logs: docker-compose logs -f voice-gateway" -ForegroundColor Gray

# Keep script running
try {
    Wait-Process -Id $tunnelProcess.Id
} catch {
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    docker-compose down
}
