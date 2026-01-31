# Quick Docker Rebuild Script
# Run this after making code changes to backend or voice_gateway

Write-Host "🔄 Stopping containers..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "🏗️  Rebuilding containers..." -ForegroundColor Cyan
docker-compose build backend voice-gateway

Write-Host ""
Write-Host "🚀 Starting containers..." -ForegroundColor Green
docker-compose up -d

Write-Host ""
Write-Host "✅ Containers rebuilt and restarted!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Container status:" -ForegroundColor White
docker-compose ps

Write-Host ""
Write-Host "📝 View logs with:" -ForegroundColor White
Write-Host "   docker logs -f relayx-backend" -ForegroundColor Gray
Write-Host "   docker logs -f relayx-voice-gateway" -ForegroundColor Gray
