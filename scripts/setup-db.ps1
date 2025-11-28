# Setup Database Schema in Supabase
# Run this script to apply the database schema

param(
    [string]$SupabaseUrl = $env:SUPABASE_URL,
    [string]$SupabaseKey = $env:SUPABASE_ANON_KEY
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🗄️  RelayX Database Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Load .env if exists
if (Test-Path ".env") {
    Write-Host "📄 Loading .env file..." -ForegroundColor Yellow
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([^=]+)=(.+)$') {
            $name = $matches[1]
            $value = $matches[2]
            Set-Item -Path "env:$name" -Value $value
        }
    }
    
    $SupabaseUrl = $env:SUPABASE_URL
    $SupabaseKey = $env:SUPABASE_ANON_KEY
}

if (-not $SupabaseUrl -or -not $SupabaseKey) {
    Write-Host "❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set" -ForegroundColor Red
    Write-Host "   Set them in .env or pass as parameters" -ForegroundColor Yellow
    exit 1
}

Write-Host "🔗 Supabase URL: $SupabaseUrl" -ForegroundColor White
Write-Host ""

# Read schema file
$schemaFile = "db\schema.sql"
if (-not (Test-Path $schemaFile)) {
    Write-Host "❌ Schema file not found: $schemaFile" -ForegroundColor Red
    exit 1
}

$schema = Get-Content $schemaFile -Raw

Write-Host "📋 Schema file loaded: $schemaFile" -ForegroundColor Green
Write-Host ""
Write-Host "================================================" -ForegroundColor Yellow
Write-Host "⚠️  IMPORTANT INSTRUCTIONS" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "To set up your database:" -ForegroundColor White
Write-Host ""
Write-Host "1. Go to: $SupabaseUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Navigate to: SQL Editor (in the left sidebar)" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Click: 'New Query'" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Copy the SQL from: db\schema.sql" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Paste and click 'Run'" -ForegroundColor Cyan
Write-Host ""
Write-Host "================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ Schema file is ready at: $schemaFile" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to open schema file in notepad..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

notepad $schemaFile

Write-Host ""
Write-Host "After running the schema, your database will have:" -ForegroundColor Green
Write-Host "   - agents table" -ForegroundColor White
Write-Host "   - calls table" -ForegroundColor White
Write-Host "   - transcripts table" -ForegroundColor White
Write-Host "   - call_analysis table" -ForegroundColor White
Write-Host "   - Default Sales Assistant agent" -ForegroundColor White
Write-Host ""
