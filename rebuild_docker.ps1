# RelayX Docker Rebuild Script
# Rebuilds Docker containers from scratch with optimized caching

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  RelayX Docker Rebuild" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Step 1: Stopping running containers..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "Step 2: Building images with no cache (fresh build)..." -ForegroundColor Yellow
Write-Host "  This will download dependencies into Docker only." -ForegroundColor Gray
Write-Host ""

docker-compose build --no-cache --progress=plain

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Step 3: Starting containers..." -ForegroundColor Yellow
    docker-compose up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "=====================================" -ForegroundColor Green
        Write-Host "  Build Complete!" -ForegroundColor Green
        Write-Host "=====================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Containers are running:" -ForegroundColor Cyan
        docker-compose ps
        
        Write-Host ""
        Write-Host "View logs with:" -ForegroundColor Yellow
        Write-Host "  docker-compose logs -f" -ForegroundColor White
        Write-Host ""
        Write-Host "Check Docker disk usage:" -ForegroundColor Yellow
        docker system df
    } else {
        Write-Host ""
        Write-Host "Failed to start containers!" -ForegroundColor Red
        Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Build failed! Check the error messages above." -ForegroundColor Red
}
