# Quick Cloudflare Tunnel for RelayX (No signup required!)
Write-Host "Starting Quick Cloudflare Tunnel..." -ForegroundColor Cyan

# Download cloudflared if not exists
$cloudflaredPath = "$PSScriptRoot\cloudflared.exe"
if (-not (Test-Path $cloudflaredPath)) {
    Write-Host "Downloading cloudflared..." -ForegroundColor Yellow
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $cloudflaredPath -UseBasicParsing
    Write-Host "Downloaded!" -ForegroundColor Green
}

# Start tunnel (generates random URL automatically)
Write-Host "`nStarting tunnel to http://localhost:8001..." -ForegroundColor Yellow
Write-Host "This will generate a random public URL with NO warnings!" -ForegroundColor Green
Write-Host "`nWait for the URL to appear below..." -ForegroundColor Cyan
Write-Host "="*60

& $cloudflaredPath tunnel --url http://localhost:8001
