# Setup Cloudflare Tunnel for RelayX
# This replaces ngrok with Cloudflare Tunnel (free, no warning pages)

Write-Host "Setting up Cloudflare Tunnel..." -ForegroundColor Cyan

# Step 1: Download cloudflared
Write-Host "`n[1/5] Downloading cloudflared..." -ForegroundColor Yellow
$cloudflaredUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
$cloudflaredPath = "$PSScriptRoot\cloudflared.exe"

if (Test-Path $cloudflaredPath) {
    Write-Host "   cloudflared already exists, skipping download" -ForegroundColor Green
} else {
    Invoke-WebRequest -Uri $cloudflaredUrl -OutFile $cloudflaredPath -UseBasicParsing
    Write-Host "   Downloaded cloudflared" -ForegroundColor Green
}

# Step 2: Login to Cloudflare (opens browser)
Write-Host "`n[2/5] Login to Cloudflare..." -ForegroundColor Yellow
Write-Host "   This will open your browser. Login with your Cloudflare account." -ForegroundColor Gray
Write-Host "   If you don't have one, create a free account at cloudflare.com" -ForegroundColor Gray
Start-Sleep -Seconds 2
& $cloudflaredPath tunnel login

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n   ERROR: Cloudflare login failed" -ForegroundColor Red
    exit 1
}

Write-Host "   Login successful!" -ForegroundColor Green

# Step 3: Create tunnel
Write-Host "`n[3/5] Creating tunnel..." -ForegroundColor Yellow
$tunnelName = "relayx-voice"
& $cloudflaredPath tunnel create $tunnelName

if ($LASTEXITCODE -ne 0) {
    Write-Host "   Tunnel may already exist, continuing..." -ForegroundColor Yellow
}

# Step 4: Get tunnel info
Write-Host "`n[4/5] Getting tunnel information..." -ForegroundColor Yellow
$tunnelList = & $cloudflaredPath tunnel list --output json | ConvertFrom-Json
$tunnel = $tunnelList | Where-Object { $_.name -eq $tunnelName } | Select-Object -First 1

if (-not $tunnel) {
    Write-Host "   ERROR: Could not find tunnel" -ForegroundColor Red
    exit 1
}

$tunnelId = $tunnel.id
Write-Host "   Tunnel ID: $tunnelId" -ForegroundColor Green

# Step 5: Create config file
Write-Host "`n[5/5] Creating tunnel configuration..." -ForegroundColor Yellow
$configPath = "$env:USERPROFILE\.cloudflared\config.yml"
$configDir = Split-Path $configPath

if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$configContent = @"
tunnel: $tunnelId
credentials-file: $env:USERPROFILE\.cloudflared\$tunnelId.json

ingress:
  - hostname: relayx-voice.trycloudflare.com
    service: http://localhost:8001
  - service: http_status:404
"@

$configContent | Out-File -FilePath $configPath -Encoding UTF8
Write-Host "   Configuration saved to: $configPath" -ForegroundColor Green

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "CLOUDFLARE TUNNEL SETUP COMPLETE!" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Stop Docker containers: docker-compose down"
Write-Host "2. Run: .\start_with_cloudflare.ps1"
Write-Host "3. The tunnel will automatically get a public URL"
Write-Host "`nPress any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
