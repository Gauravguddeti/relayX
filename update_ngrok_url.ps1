# Script to extract ngrok URL and update .env
Write-Host "Waiting for ngrok to start..." -ForegroundColor Cyan

# Wait for ngrok to be ready (max 30 seconds)
$maxAttempts = 30
$attempt = 0
$ngrokUrl = $null

while ($attempt -lt $maxAttempts -and -not $ngrokUrl) {
    Start-Sleep -Seconds 1
    $attempt++
    
    # Get ngrok tunnel info from API
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -ErrorAction SilentlyContinue
        if ($response.tunnels -and $response.tunnels.Count -gt 0) {
            $ngrokUrl = $response.tunnels[0].public_url
            Write-Host "Found ngrok URL: $ngrokUrl" -ForegroundColor Green
            break
        }
    } catch {
        # ngrok not ready yet
    }
    
    Write-Host "." -NoNewline
}

if (-not $ngrokUrl) {
    Write-Host "`nFailed to get ngrok URL after $maxAttempts seconds" -ForegroundColor Red
    Write-Host "Check logs with: docker logs relayx-ngrok" -ForegroundColor Yellow
    exit 1
}

Write-Host "`nUpdating .env file..." -ForegroundColor Cyan

# Read .env file
$envPath = ".env"
$envContent = Get-Content $envPath -Raw

# Update VOICE_GATEWAY_URL
if ($envContent -match 'VOICE_GATEWAY_URL=.*') {
    $envContent = $envContent -replace 'VOICE_GATEWAY_URL=.*', "VOICE_GATEWAY_URL=$ngrokUrl"
    Write-Host "Updated VOICE_GATEWAY_URL to: $ngrokUrl" -ForegroundColor Green
} else {
    # Add if not exists
    $envContent += "`nVOICE_GATEWAY_URL=$ngrokUrl"
    Write-Host "Added VOICE_GATEWAY_URL: $ngrokUrl" -ForegroundColor Green
}

# Save updated .env
Set-Content -Path $envPath -Value $envContent -NoNewline

Write-Host "`nRecreating backend and voice-gateway to apply new URL..." -ForegroundColor Cyan
docker-compose up -d --force-recreate --no-deps backend voice-gateway

Write-Host "`n✅ ngrok URL updated and services restarted!" -ForegroundColor Green
Write-Host "ngrok URL: $ngrokUrl" -ForegroundColor Cyan
Write-Host "`nTesting the URL..." -ForegroundColor Yellow

# Test if ngrok URL is accessible
try {
    $testResponse = Invoke-WebRequest -Uri "$ngrokUrl/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ ngrok tunnel is working! Status: $($testResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: Could not reach $ngrokUrl/health" -ForegroundColor Yellow
    Write-Host "    This might be the ngrok warning page issue..." -ForegroundColor Yellow
}

Write-Host "`nYou can view ngrok dashboard at: http://localhost:4040" -ForegroundColor Cyan
