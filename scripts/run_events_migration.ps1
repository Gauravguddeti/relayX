# Run scheduled events database migration

$ErrorActionPreference = "Stop"

Write-Host "Running scheduled events migration..." -ForegroundColor Cyan

$env:SUPABASE_URL = (Get-Content .env | Select-String "SUPABASE_URL" | ForEach-Object { $_ -replace "SUPABASE_URL=", "" })
$env:SUPABASE_KEY = (Get-Content .env | Select-String "SUPABASE_SERVICE_KEY" | ForEach-Object { $_ -replace "SUPABASE_SERVICE_KEY=", "" })

if (-not $env:SUPABASE_URL -or -not $env:SUPABASE_KEY) {
    Write-Host "Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in .env" -ForegroundColor Red
    exit 1
}

Write-Host "Connecting to Supabase..." -ForegroundColor Yellow

python -c @"
import os
import psycopg2
from urllib.parse import urlparse

# Parse Supabase URL to get database connection details
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url:
    print('Error: SUPABASE_URL not set')
    exit(1)

# Extract project ID from URL
project_id = supabase_url.split('//')[1].split('.')[0]

# Construct direct database URL (you'll need the password from Supabase dashboard)
# For this script, we'll use the REST API approach with Supabase client

from supabase import create_client, Client

client: Client = create_client(supabase_url, supabase_key)

# Read migration file
with open('db/migrations/010_add_scheduled_events.sql', 'r') as f:
    migration_sql = f.read()

print('Migration file loaded. Please run this SQL manually in Supabase SQL editor:')
print('=' * 80)
print(migration_sql)
print('=' * 80)
print()
print('Go to: Supabase Dashboard > SQL Editor > New Query')
print('Paste the SQL above and click Run')
"@

Write-Host ""
Write-Host "Alternative: Run migration manually in Supabase dashboard" -ForegroundColor Cyan
Write-Host "1. Go to https://supabase.com/dashboard/project/YOUR_PROJECT/sql" -ForegroundColor White
Write-Host "2. Open db/migrations/010_add_scheduled_events.sql" -ForegroundColor White
Write-Host "3. Copy and paste the SQL" -ForegroundColor White
Write-Host "4. Click 'Run'" -ForegroundColor White
