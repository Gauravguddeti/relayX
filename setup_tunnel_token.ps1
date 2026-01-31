# Alternative: Get tunnel token directly
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Tunnel - Quick Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Getting your permanent tunnel token..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Steps:" -ForegroundColor Cyan
Write-Host "  1. Go to: https://one.dash.cloudflare.com/" -ForegroundColor White
Write-Host "  2. Sign up/Login (FREE account)" -ForegroundColor White
Write-Host "  3. Go to: Networks > Tunnels" -ForegroundColor White
Write-Host "  4. Click 'Create a tunnel'" -ForegroundColor White
Write-Host "  5. Name it: relayx" -ForegroundColor White
Write-Host "  6. Copy the tunnel TOKEN (starts with 'eyJ...')" -ForegroundColor White
Write-Host "  7. In the tunnel settings, add:" -ForegroundColor White
Write-Host "     - Public hostname: [your-tunnel-name].cfargotunnel.com" -ForegroundColor White
Write-Host "     - Service: http://voice-gateway:8001" -ForegroundColor White
Write-Host ""
Write-Host "Paste your tunnel TOKEN here:" -ForegroundColor Cyan
$tunnelToken = Read-Host

if (-not $tunnelToken -or $tunnelToken.Length -lt 50) {
    Write-Host "❌ Invalid token. Please try again." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Enter your tunnel URL (e.g., https://relayx-abc123.cfargotunnel.com):" -ForegroundColor Cyan
$tunnelUrl = Read-Host

if (-not $tunnelUrl -or -not $tunnelUrl.StartsWith("https://")) {
    Write-Host "❌ Invalid URL. Must start with https://" -ForegroundColor Red
    exit 1
}

# Update .env file
Write-Host ""
Write-Host "Updating configuration..." -ForegroundColor Yellow

$envPath = ".env"
$envContent = Get-Content $envPath -Raw

# Update or add CLOUDFLARE_TUNNEL_TOKEN
if ($envContent -match 'CLOUDFLARE_TUNNEL_TOKEN=.*') {
    $envContent = $envContent -replace 'CLOUDFLARE_TUNNEL_TOKEN=.*', "CLOUDFLARE_TUNNEL_TOKEN=$tunnelToken"
} else {
    $envContent += "`nCLOUDFLARE_TUNNEL_TOKEN=$tunnelToken"
}

# Update or add VOICE_GATEWAY_URL
if ($envContent -match 'VOICE_GATEWAY_URL=.*') {
    $envContent = $envContent -replace 'VOICE_GATEWAY_URL=.*', "VOICE_GATEWAY_URL=$tunnelUrl"
} else {
    $envContent += "`nVOICE_GATEWAY_URL=$tunnelUrl"
}

Set-Content -Path $envPath -Value $envContent -NoNewline

Write-Host "✅ Configuration saved!" -ForegroundColor Green
Write-Host ""
Write-Host "Your permanent tunnel URL: $tunnelUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now restart Docker:" -ForegroundColor Yellow
Write-Host "  docker-compose down && docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "✅ Done! Your tunnel will ALWAYS use this URL!" -ForegroundColor Green
Write-Host ""
