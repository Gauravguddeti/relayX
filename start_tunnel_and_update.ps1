# Get Cloudflare Tunnel URL from logs
$logPath = "$env:TEMP\cloudflared_output.txt"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\cloudflared.exe tunnel --url http://localhost:8001 *> '$logPath'" -WindowStyle Normal

Write-Host "Starting tunnel... waiting for URL..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

if (Test-Path $logPath) {
    $content = Get-Content $logPath -Raw
    if ($content -match "https://([a-z0-9-]+)\.trycloudflare\.com") {
        $tunnelUrl = $matches[0]
        Write-Host "`n========================================" -ForegroundColor Cyan
        Write-Host "TUNNEL URL: $tunnelUrl" -ForegroundColor Green
        Write-Host "========================================`n" -ForegroundColor Cyan
        
        # Update .env
        $envPath = ".env"
        $envContent = Get-Content $envPath -Raw
        $envContent = $envContent -replace 'VOICE_GATEWAY_URL=.*', "VOICE_GATEWAY_URL=$tunnelUrl"
        $envContent | Out-File $envPath -Encoding UTF8 -NoNewline
        
        Write-Host "Updated .env with new URL" -ForegroundColor Green
        Write-Host "Restarting Docker services..." -ForegroundColor Yellow
        
        docker-compose restart backend voice-gateway
        
        Write-Host "`nAll set! Try making a call now." -ForegroundColor Green
    }
}
