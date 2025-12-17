# Move Docker WSL data from C to D drive
# Your C drive has only 56MB left! Docker is using 40.7GB

Write-Host "🚨 MOVING DOCKER FROM C TO D DRIVE 🚨" -ForegroundColor Red
Write-Host "Current C drive free space: 56MB"
Write-Host "Docker is using: 40.7GB on C drive"
Write-Host ""

# 1. Shutdown everything
Write-Host "Step 1: Shutting down Docker and WSL..." -ForegroundColor Yellow
wsl --shutdown
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

# 2. Export docker-desktop
Write-Host "Step 2: Exporting docker-desktop (this will take 2-3 minutes)..." -ForegroundColor Yellow
wsl --export docker-desktop D:\DockerData\docker-desktop.tar

# 3. Unregister from C drive
Write-Host "Step 3: Removing docker-desktop from C drive..." -ForegroundColor Yellow
wsl --unregister docker-desktop

# 4. Import to D drive
Write-Host "Step 4: Importing docker-desktop to D:\DockerData..." -ForegroundColor Yellow
wsl --import docker-desktop D:\DockerData\docker-desktop D:\DockerData\docker-desktop.tar --version 2

# 5. Clean up tar file
Write-Host "Step 5: Cleaning up..." -ForegroundColor Yellow
Remove-Item D:\DockerData\docker-desktop.tar -Force

Write-Host ""
Write-Host "✅ DONE! Docker moved to D drive" -ForegroundColor Green
Write-Host "Freed up ~40GB on C drive" -ForegroundColor Green
Write-Host ""
Write-Host "Now open Docker Desktop settings and set:"
Write-Host "  Settings > Resources > WSL Integration > Enable Ubuntu"
Write-Host ""
Write-Host "Then restart Docker Desktop"
