# localhost.run - Free SSH tunnel (no signup, no credit card!)
Write-Host "Starting localhost.run tunnel..." -ForegroundColor Cyan
Write-Host "This will create a persistent tunnel as long as this window stays open" -ForegroundColor Yellow
Write-Host ""

# Use SSH to create tunnel
ssh -R 80:localhost:8001 nokey@localhost.run

# The URL will be displayed in the output
