# Enhanced RelayX Startup Script
# Configures TWO ngrok tunnels: one for Ollama, one for Voice Gateway

param(
    [switch]$SkipNgrok,
    [switch]$Native,
    [switch]$StopOllama
)

$ErrorActionPreference = "Stop"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🚀 RelayX AI Caller - Enhanced Startup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$OLLAMA_PORT = 11434
$BACKEND_PORT = 8000
$VOICE_GATEWAY_PORT = 8001
$ENV_FILE = ".env"

# ==================== FUNCTIONS ====================

function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
    } catch {
        return $false
    }
    return $false
}

function Wait-ForOllama {
    Write-Host "⏳ Waiting for Ollama to be ready..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$OLLAMA_PORT/api/tags" -TimeoutSec 2
            Write-Host "✅ Ollama is ready!" -ForegroundColor Green
            return $true
        } catch {
            $attempt++
            Start-Sleep -Seconds 1
        }
    }
    
    Write-Host "❌ Ollama failed to start" -ForegroundColor Red
    return $false
}

function Start-NgrokTunnel {
    param(
        [int]$Port,
        [string]$Name
    )
    
    Write-Host "🌐 Starting ngrok for $Name (port $Port)..." -ForegroundColor Yellow
    
    # Start ngrok in background
    $logFile = "logs\ngrok_$Name.log"
    $process = Start-Process -FilePath "ngrok" -ArgumentList "http", $Port -PassThru -WindowStyle Hidden -RedirectStandardOutput $logFile
    
    Write-Host "⏳ Waiting for ngrok to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 4
    
    # Fetch ngrok public URL from API
    $attempt = 0
    while ($attempt -lt 15) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 2
            
            if ($response.tunnels -and $response.tunnels.Count -gt 0) {
                # Find tunnel for this port
                foreach ($tunnel in $response.tunnels) {
                    $tunnelUrl = $tunnel.config.addr
                    if ($tunnelUrl -match ":$Port") {
                        $publicUrl = $tunnel.public_url
                        Write-Host "✅ ngrok tunnel active for $Name`: $publicUrl" -ForegroundColor Green
                        return $publicUrl
                    }
                }
                
                # Fallback: return first tunnel if port matching fails
                if ($response.tunnels.Count -eq 1) {
                    $publicUrl = $response.tunnels[0].public_url
                    Write-Host "✅ ngrok tunnel active: $publicUrl" -ForegroundColor Green
                    return $publicUrl
                }
            }
        } catch {
            $attempt++
            Start-Sleep -Seconds 1
        }
    }
    
    Write-Host "❌ Failed to get ngrok URL for $Name" -ForegroundColor Red
    return $null
}

function Update-EnvFile {
    param(
        [string]$OllamaUrl,
        [string]$VoiceGatewayUrl
    )
    
    Write-Host "📝 Updating $ENV_FILE with ngrok URLs..." -ForegroundColor Yellow
    
    if (-not (Test-Path $ENV_FILE)) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" $ENV_FILE
            Write-Host "✅ Created .env from .env.example" -ForegroundColor Green
        } else {
            Write-Host "❌ .env.example not found!" -ForegroundColor Red
            return $false
        }
    }
    
    # Read .env content
    $envContent = Get-Content $ENV_FILE
    
    # Update LLM_BASE_URL
    $updatedLLM = $false
    for ($i = 0; $i -lt $envContent.Count; $i++) {
        if ($envContent[$i] -match "^LLM_BASE_URL=") {
            $envContent[$i] = "LLM_BASE_URL=$OllamaUrl"
            $updatedLLM = $true
        }
        if ($envContent[$i] -match "^VOICE_GATEWAY_URL=") {
            $envContent[$i] = "VOICE_GATEWAY_URL=$VoiceGatewayUrl"
        }
        if ($envContent[$i] -match "^VOICE_GATEWAY_WS_URL=") {
            # Convert https to wss
            $wsUrl = $VoiceGatewayUrl -replace "^https://", "wss://"
            $envContent[$i] = "VOICE_GATEWAY_WS_URL=$wsUrl"
        }
    }
    
    if (-not $updatedLLM) {
        $envContent += "LLM_BASE_URL=$OllamaUrl"
    }
    
    # Write back to file
    $envContent | Set-Content $ENV_FILE
    
    Write-Host "✅ Updated URLs in .env:" -ForegroundColor Green
    Write-Host "   LLM_BASE_URL=$OllamaUrl" -ForegroundColor White
    Write-Host "   VOICE_GATEWAY_URL=$VoiceGatewayUrl" -ForegroundColor White
    return $true
}

function Start-OllamaService {
    Write-Host "🧠 Starting Ollama service..." -ForegroundColor Yellow
    
    # Check if already running
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$OLLAMA_PORT/api/tags" -TimeoutSec 2
        Write-Host "✅ Ollama already running" -ForegroundColor Green
        return $true
    } catch {
        # Not running, start it
        Write-Host "Starting Ollama..." -ForegroundColor Yellow
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        
        if (Wait-ForOllama) {
            return $true
        }
        return $false
    }
}

function Test-DockerRunning {
    try {
        docker info 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Wait-ForService {
    param(
        [string]$Url,
        [string]$Name,
        [int]$MaxAttempts = 30
    )
    
    Write-Host "⏳ Waiting for $Name to be ready..." -ForegroundColor Yellow
    $attempt = 0
    
    while ($attempt -lt $MaxAttempts) {
        try {
            $response = Invoke-RestMethod -Uri $Url -TimeoutSec 2 -ErrorAction SilentlyContinue
            Write-Host "✅ $Name is ready!" -ForegroundColor Green
            return $true
        } catch {
            $attempt++
            Start-Sleep -Seconds 2
        }
    }
    
    Write-Host "⚠️  $Name is taking longer than expected" -ForegroundColor Yellow
    return $false
}

# ==================== MAIN SCRIPT ====================

Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

# Check required commands
$requiredCommands = @("ollama", "docker", "docker-compose")
$missingCommands = @()

foreach ($cmd in $requiredCommands) {
    if (-not (Test-Command $cmd)) {
        $missingCommands += $cmd
        Write-Host "❌ $cmd not found" -ForegroundColor Red
    } else {
        Write-Host "✅ $cmd found" -ForegroundColor Green
    }
}

if (-not $SkipNgrok -and -not (Test-Command "ngrok")) {
    Write-Host "❌ ngrok not found" -ForegroundColor Red
    $missingCommands += "ngrok"
}

if ($missingCommands.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Missing commands: $($missingCommands -join ', ')" -ForegroundColor Red
    Write-Host "Please install missing tools and try again." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 1: Start Ollama
if (-not (Start-OllamaService)) {
    Write-Host "❌ Failed to start Ollama" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Setup ngrok tunnels
$ollamaUrl = "http://localhost:$OLLAMA_PORT"
$voiceGatewayUrl = "http://localhost:$VOICE_GATEWAY_PORT"

if (-not $SkipNgrok) {
    Write-Host "🌐 Setting up ngrok tunnels..." -ForegroundColor Cyan
    Write-Host ""
    
    # Kill any existing ngrok processes
    Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Start tunnel for Ollama
    $ollamaUrl = Start-NgrokTunnel -Port $OLLAMA_PORT -Name "Ollama"
    
    if (-not $ollamaUrl) {
        Write-Host "❌ Failed to create Ollama ngrok tunnel" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: For voice gateway, you need to start services first," -ForegroundColor Yellow
    Write-Host "   then run a separate ngrok tunnel." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   We'll start services with localhost URLs for now." -ForegroundColor Yellow
    Write-Host "   After services are up, run:" -ForegroundColor Cyan
    Write-Host "   ngrok http $VOICE_GATEWAY_PORT" -ForegroundColor White
    Write-Host ""
    
    # For now, use localhost for voice gateway (will be updated manually)
    $voiceGatewayUrl = "https://your-gateway.ngrok.io"
    
    # Update .env file
    if (-not (Update-EnvFile -OllamaUrl $ollamaUrl -VoiceGatewayUrl $voiceGatewayUrl)) {
        Write-Host "❌ Failed to update .env file" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⏭️  Skipping ngrok setup" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: Start services
if ($Native) {
    Write-Host "🚀 Starting services natively..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check if Python venv exists
    if (-not (Test-Path "venv")) {
        Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv venv
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    }
    
    # Activate venv and install dependencies
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
    pip install -r requirements.txt --quiet
    
    Write-Host ""
    Write-Host "🚀 Starting backend on port $BACKEND_PORT..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; cd backend; python main.py" -WindowStyle Normal
    
    Start-Sleep -Seconds 3
    
    Write-Host "🚀 Starting voice gateway on port $VOICE_GATEWAY_PORT..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; cd voice_gateway; python voice_gateway.py" -WindowStyle Normal
    
    # Wait for services
    Wait-ForService -Url "http://localhost:$BACKEND_PORT/" -Name "Backend"
    Wait-ForService -Url "http://localhost:$VOICE_GATEWAY_PORT/" -Name "Voice Gateway"
    
} else {
    Write-Host "🐳 Starting Docker services..." -ForegroundColor Cyan
    Write-Host ""
    
    # Check Docker is running
    if (-not (Test-DockerRunning)) {
        Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
    
    # Build and start services
    Write-Host "Building and starting containers..." -ForegroundColor Yellow
    docker-compose up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker services started" -ForegroundColor Green
        
        # Wait for services to be ready
        Wait-ForService -Url "http://localhost:$BACKEND_PORT/" -Name "Backend"
        Wait-ForService -Url "http://localhost:$VOICE_GATEWAY_PORT/" -Name "Voice Gateway"
    } else {
        Write-Host "❌ Docker services failed to start" -ForegroundColor Red
        Write-Host "Check logs with: docker-compose logs -f" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "✨ RelayX is now running!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 Service URLs:" -ForegroundColor Cyan
Write-Host "   Backend API:      http://localhost:$BACKEND_PORT" -ForegroundColor White
Write-Host "   Voice Gateway:    http://localhost:$VOICE_GATEWAY_PORT" -ForegroundColor White
Write-Host "   Ollama (local):   http://localhost:$OLLAMA_PORT" -ForegroundColor White
if ($ollamaUrl -ne "http://localhost:$OLLAMA_PORT") {
    Write-Host "   Ollama (public):  $ollamaUrl" -ForegroundColor White
}
Write-Host ""

if (-not $SkipNgrok) {
    Write-Host "================================================" -ForegroundColor Yellow
    Write-Host "⚡ NEXT STEP: Expose Voice Gateway" -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To enable Twilio calls, run in a NEW terminal:" -ForegroundColor White
    Write-Host ""
    Write-Host "   ngrok http $VOICE_GATEWAY_PORT" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Then update .env with the ngrok URL:" -ForegroundColor White
    Write-Host "   VOICE_GATEWAY_URL=https://your-url.ngrok.io" -ForegroundColor Cyan
    Write-Host "   VOICE_GATEWAY_WS_URL=wss://your-url.ngrok.io" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "And restart services:" -ForegroundColor White
    Write-Host "   .\scripts\start.ps1" -ForegroundColor Cyan
    Write-Host ""
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📚 Next Steps:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1️⃣  Setup database:" -ForegroundColor Yellow
Write-Host "   .\scripts\setup-db.ps1" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  Test backend:" -ForegroundColor Yellow
Write-Host "   curl http://localhost:$BACKEND_PORT/health" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  Create an agent:" -ForegroundColor Yellow
Write-Host "   .\scripts\test-api.ps1" -ForegroundColor White
Write-Host ""
Write-Host "4️⃣  Make a test call:" -ForegroundColor Yellow
Write-Host "   See docs/QUICK_START.md" -ForegroundColor White
Write-Host ""
Write-Host "📖 Full documentation: README.md" -ForegroundColor Cyan
Write-Host ""

if (-not $StopOllama) {
    Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
    Write-Host ""
    
    # Keep script running
    try {
        while ($true) {
            Start-Sleep -Seconds 5
        }
    } finally {
        Write-Host ""
        Write-Host "🛑 Shutting down..." -ForegroundColor Yellow
        
        if (-not $Native) {
            docker-compose down
        }
        
        # Kill ngrok
        Get-Process ngrok -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}
