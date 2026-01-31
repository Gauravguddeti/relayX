# Script to extract Cloudflare Tunnel URL from Docker logs and update .env
Write-Host "Waiting for Cloudflare Tunnel to start..." -ForegroundColor Cyan

# Wait for the tunnel to be ready (max 30 seconds)
$maxAttempts = 30
$attempt = 0
$tunnelUrl = $null

while ($attempt -lt $maxAttempts -and -not $tunnelUrl) {
    Start-Sleep -Seconds 1
    $attempt++
    
    # Get logs from cloudflare tunnel container
    $logs = docker logs relayx-cloudflare-tunnel 2>&1 | Select-String -Pattern "https://.*\.trycloudflare\.com"
    
    if ($logs) {
        # Extract the URL from the logs
        $tunnelUrl = ($logs | Select-Object -First 1).Line -replace '.*?(https://[^\s]+\.trycloudflare\.com).*', '$1'
        Write-Host "Found tunnel URL: $tunnelUrl" -ForegroundColor Green
        break
    }
    
    Write-Host "." -NoNewline
}

if (-not $tunnelUrl) {
    Write-Host "`nFailed to get Cloudflare Tunnel URL after $maxAttempts seconds" -ForegroundColor Red
    Write-Host "Check logs with: docker logs relayx-cloudflare-tunnel" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nUpdating .env file..." -ForegroundColor Cyan

# Read .env file
$envPath = ".env"
$envContent = Get-Content $envPath -Raw

# Update VOICE_GATEWAY_URL
if ($envContent -match 'VOICE_GATEWAY_URL=.*') {
    $envContent = $envContent -replace 'VOICE_GATEWAY_URL=.*', "VOICE_GATEWAY_URL=$tunnelUrl"
    Write-Host "Updated VOICE_GATEWAY_URL to: $tunnelUrl" -ForegroundColor Green
} else {
    # Add if not exists
    $envContent += "`nVOICE_GATEWAY_URL=$tunnelUrl"
    Write-Host "Added VOICE_GATEWAY_URL: $tunnelUrl" -ForegroundColor Green
}

# Save updated .env
Set-Content -Path $envPath -Value $envContent -NoNewline

Write-Host "`nRecreating backend and voice-gateway to apply new URL..." -ForegroundColor Cyan
docker-compose up -d --force-recreate --no-deps backend voice-gateway

Write-Host "`n✅ Cloudflare Tunnel URL updated and services restarted!" -ForegroundColor Green
Write-Host "Tunnel URL: $tunnelUrl" -ForegroundColor Cyan
Write-Host "`nNote: This URL will change each time Docker is restarted." -ForegroundColor Yellow
