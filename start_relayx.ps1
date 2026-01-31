# Complete startup script for RelayX
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "  RelayX - Starting All Services" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Start all Docker services
Write-Host "`n[1/3] Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be healthy
Write-Host "`n[2/3] Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Extract and update Cloudflare Tunnel URL
Write-Host "`n[3/3] Getting Cloudflare Tunnel URL..." -ForegroundColor Yellow
& .\update_tunnel_url.ps1

Write-Host "`n===========================================" -ForegroundColor Green
Write-Host "  ✅ RelayX is Ready!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running:" -ForegroundColor Cyan
Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:      http://localhost:8000" -ForegroundColor White
Write-Host "  Voice Gateway: http://localhost:8001" -ForegroundColor White
Write-Host "  Redis:        localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "Cloudflare Tunnel URL has been updated in .env" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "To stop all services:" -ForegroundColor Yellow
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
