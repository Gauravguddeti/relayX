# One-time setup for permanent Cloudflare Tunnel
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Cloudflare Permanent Tunnel Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if cloudflared is installed
Write-Host "[Step 1/5] Checking for cloudflared..." -ForegroundColor Yellow
if (-not (Test-Path "cloudflared.exe")) {
    Write-Host "Downloading cloudflared..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
    Write-Host "✅ Downloaded cloudflared.exe" -ForegroundColor Green
} else {
    Write-Host "✅ cloudflared.exe already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "[Step 2/5] Login to Cloudflare" -ForegroundColor Yellow
Write-Host "This will open a browser window. Please:" -ForegroundColor White
Write-Host "  1. Create a FREE Cloudflare account (if you don't have one)" -ForegroundColor White
Write-Host "  2. Authorize the tunnel" -ForegroundColor White
Write-Host ""
Write-Host "Press any key when ready..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

.\cloudflared.exe tunnel login

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Login failed. Please try again." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Logged in successfully!" -ForegroundColor Green
Write-Host ""

# Step 3: Create a named tunnel
Write-Host "[Step 3/5] Creating named tunnel 'relayx'..." -ForegroundColor Yellow
.\cloudflared.exe tunnel create relayx

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Tunnel might already exist, checking..." -ForegroundColor Yellow
}

Write-Host "✅ Tunnel 'relayx' ready!" -ForegroundColor Green
Write-Host ""

# Step 4: Get tunnel info
Write-Host "[Step 4/5] Getting tunnel details..." -ForegroundColor Yellow
$tunnelInfo = .\cloudflared.exe tunnel info relayx 2>&1 | Out-String

# Extract tunnel ID
$tunnelId = ($tunnelInfo | Select-String -Pattern "Your tunnel ([a-f0-9-]+)" | ForEach-Object { $_.Matches.Groups[1].Value })

if (-not $tunnelId) {
    # Try alternative method - list tunnels and find relayx
    $tunnelsList = .\cloudflared.exe tunnel list 2>&1 | Out-String
    $tunnelId = ($tunnelsList | Select-String -Pattern "([a-f0-9-]+)\s+relayx" | ForEach-Object { $_.Matches.Groups[1].Value })
}

if (-not $tunnelId) {
    Write-Host "❌ Could not find tunnel ID. Please check manually with:" -ForegroundColor Red
    Write-Host "   .\cloudflared.exe tunnel list" -ForegroundColor Yellow
    exit 1
}

Write-Host "Tunnel ID: $tunnelId" -ForegroundColor Cyan

# Create tunnel URL
$tunnelUrl = "https://$tunnelId.cfargotunnel.com"
Write-Host "Permanent URL: $tunnelUrl" -ForegroundColor Green
Write-Host ""

# Step 5: Get credentials
Write-Host "[Step 5/5] Locating credentials..." -ForegroundColor Yellow
$credentialsPath = "$env:USERPROFILE\.cloudflared\$tunnelId.json"

if (-not (Test-Path $credentialsPath)) {
    Write-Host "❌ Credentials file not found at: $credentialsPath" -ForegroundColor Red
    Write-Host "Looking for any tunnel credentials..." -ForegroundColor Yellow
    
    $cloudflaredDir = "$env:USERPROFILE\.cloudflared"
    if (Test-Path $cloudflaredDir) {
        $jsonFiles = Get-ChildItem -Path $cloudflaredDir -Filter "*.json"
        if ($jsonFiles.Count -gt 0) {
            $credentialsPath = $jsonFiles[0].FullName
            Write-Host "Found credentials: $credentialsPath" -ForegroundColor Yellow
        }
    }
}

if (Test-Path $credentialsPath) {
    # Copy credentials to project directory
    Copy-Item -Path $credentialsPath -Destination ".\tunnel-credentials.json" -Force
    Write-Host "✅ Credentials saved to tunnel-credentials.json" -ForegroundColor Green
} else {
    Write-Host "❌ Could not locate credentials file" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  ✅ Setup Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your permanent tunnel URL is:" -ForegroundColor Cyan
Write-Host "  $tunnelUrl" -ForegroundColor White
Write-Host ""
Write-Host "Now updating Docker configuration..." -ForegroundColor Yellow

# Update .env file
$envPath = ".env"
$envContent = Get-Content $envPath -Raw

if ($envContent -match 'VOICE_GATEWAY_URL=.*') {
    $envContent = $envContent -replace 'VOICE_GATEWAY_URL=.*', "VOICE_GATEWAY_URL=$tunnelUrl"
} else {
    $envContent += "`nVOICE_GATEWAY_URL=$tunnelUrl"
}

# Add tunnel ID and credentials path
if ($envContent -match 'CLOUDFLARE_TUNNEL_ID=.*') {
    $envContent = $envContent -replace 'CLOUDFLARE_TUNNEL_ID=.*', "CLOUDFLARE_TUNNEL_ID=$tunnelId"
} else {
    $envContent += "`nCLOUDFLARE_TUNNEL_ID=$tunnelId"
}

if ($envContent -match 'CLOUDFLARE_TUNNEL_CREDENTIALS=.*') {
    $envContent = $envContent -replace 'CLOUDFLARE_TUNNEL_CREDENTIALS=.*', "CLOUDFLARE_TUNNEL_CREDENTIALS=./tunnel-credentials.json"
} else {
    $envContent += "`nCLOUDFLARE_TUNNEL_CREDENTIALS=./tunnel-credentials.json"
}

Set-Content -Path $envPath -Value $envContent -NoNewline
Write-Host "✅ Updated .env file" -ForegroundColor Green

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. I'll update docker-compose.yml to use the named tunnel" -ForegroundColor White
Write-Host "  2. Run: docker-compose down && docker-compose up -d" -ForegroundColor White
Write-Host "  3. Your tunnel will ALWAYS use: $tunnelUrl" -ForegroundColor White
Write-Host ""
Write-Host "Tunnel credentials saved. Keep tunnel-credentials.json safe!" -ForegroundColor Yellow
Write-Host ""
