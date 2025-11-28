# Test the Backend API
# Quick health check and test calls

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🧪 RelayX API Tests" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$BACKEND_URL = "http://localhost:8000"

# Test 1: Health Check
Write-Host "1️⃣  Testing health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$BACKEND_URL/health" -Method GET
    Write-Host "✅ Health Check Passed" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Health Check Failed: $_" -ForegroundColor Red
}

Write-Host ""

# Test 2: List Agents
Write-Host "2️⃣  Listing agents..." -ForegroundColor Yellow
try {
    $agents = Invoke-RestMethod -Uri "$BACKEND_URL/agents" -Method GET
    Write-Host "✅ Found $($agents.Count) agent(s)" -ForegroundColor Green
    $agents | ConvertTo-Json -Depth 3
    
    if ($agents.Count -gt 0) {
        $agentId = $agents[0].id
        Write-Host ""
        Write-Host "First agent ID: $agentId" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Failed to list agents: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📝 To create an agent:" -ForegroundColor Yellow
Write-Host ""
Write-Host @'
curl -X POST http://localhost:8000/agents `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Sales Assistant",
    "system_prompt": "You are a friendly sales assistant. Keep responses under 2 sentences.",
    "temperature": 0.7,
    "max_tokens": 150
  }'
'@ -ForegroundColor White

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📞 To make a test call:" -ForegroundColor Yellow
Write-Host ""
Write-Host @'
curl -X POST http://localhost:8000/calls/outbound `
  -H "Content-Type: application/json" `
  -d '{
    "agent_id": "YOUR-AGENT-ID-HERE",
    "to_number": "+1234567890"
  }'
'@ -ForegroundColor White
Write-Host ""
