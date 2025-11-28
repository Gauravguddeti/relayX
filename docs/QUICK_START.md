# Quick Start Guide

Get RelayX running in 5 minutes! ⚡

## Prerequisites Check

```powershell
# Check all prerequisites
python --version    # Should be 3.11+
docker --version    # Should be installed
ollama version      # Should be installed
ngrok version       # Should be installed
```

## Step 1: Setup Environment (2 min)

```powershell
# Clone/navigate to project
cd D:\projects\RelayX

# Copy and edit .env (already done for you!)
# Just verify it has your Twilio and Supabase credentials
notepad .env
```

## Step 2: Setup Database (1 min)

```powershell
# Run database setup helper
.\scripts\setup-db.ps1

# This will:
# 1. Open your Supabase SQL editor in browser
# 2. Open the schema file in notepad
# 3. Copy schema → Paste in Supabase → Run
```

## Step 3: Start Services (2 min)

```powershell
# Start everything with one command!
.\scripts\start.ps1

# This automatically:
# ✅ Starts Ollama
# ✅ Starts ngrok tunnel
# ✅ Updates .env with ngrok URL
# ✅ Starts Backend (port 8000)
# ✅ Starts Voice Gateway (port 8001)
```

Wait for:
```
✨ RelayX is now running!
```

## Step 4: Test It! (30 sec)

```powershell
# Test health
curl http://localhost:8000/health

# Should show all "healthy"
```

## Step 5: Make Your First Call

### 5a. Create an Agent

```powershell
curl -X POST http://localhost:8000/agents `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Test Assistant",
    "system_prompt": "You are a friendly AI assistant. Keep responses under 2 sentences.",
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

Copy the `id` from response.

### 5b. Trigger a Call

⚠️ **IMPORTANT**: Before making real calls, you need to expose voice gateway via ngrok!

```powershell
# Start ngrok for voice gateway
ngrok http 8001
```

Copy the `https://` URL (e.g., `https://abc123.ngrok.io`)

Update `.env`:
```env
VOICE_GATEWAY_URL=https://abc123.ngrok.io
VOICE_GATEWAY_WS_URL=wss://abc123.ngrok.io
```

Restart services:
```powershell
# Press Ctrl+C to stop
.\scripts\start.ps1
```

Now make the call:
```powershell
curl -X POST http://localhost:8000/calls/outbound `
  -H "Content-Type: application/json" `
  -d '{
    "agent_id": "YOUR-AGENT-ID-HERE",
    "to_number": "+1234567890"
  }'
```

📞 **Your phone should ring!**

## What Just Happened?

1. ✅ Backend initiated call via Twilio API
2. ✅ Twilio called your number
3. ✅ Call audio streamed to Voice Gateway (WebSocket)
4. ✅ Whisper converted speech → text
5. ✅ LLM (Llama-3) generated response
6. ✅ Coqui TTS converted text → speech
7. ✅ Audio streamed back to phone
8. ✅ Transcript saved to Supabase

## View Call Results

```powershell
# Get call details
curl http://localhost:8000/calls/{call_id}

# Get full transcript
curl http://localhost:8000/calls/{call_id}/transcripts
```

Or check in Supabase dashboard:
- https://ddgmuyeresgwgojoegiw.supabase.co
- Go to Table Editor → `calls` → `transcripts`

## Common Commands

```powershell
# Start services
.\scripts\start.ps1

# Start without Docker (native Python)
.\scripts\start.ps1 -Native

# Skip ngrok setup
.\scripts\start.ps1 -SkipNgrok

# Test API
.\scripts\test-api.ps1

# Setup database
.\scripts\setup-db.ps1

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Folder Structure

```
RelayX/
├── backend/           # FastAPI backend (port 8000)
├── voice_gateway/     # Twilio WebSocket handler (port 8001)
├── shared/            # Shared modules (DB, LLM, STT, TTS)
├── db/                # Database schema
├── scripts/           # Startup and helper scripts
├── docs/              # Documentation
├── logs/              # Application logs
├── .env               # Your configuration
└── docker-compose.yml # Docker orchestration
```

## Next Steps

- 📖 Read full [README.md](../README.md)
- 🐛 Having issues? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📮 Test with Postman: Import `docs/RelayX_API.postman_collection.json`
- 🎯 Customize agent system prompts
- 🚀 Build your use case!

## Important URLs

**Local Services:**
- Backend: http://localhost:8000
- Voice Gateway: http://localhost:8001
- Ollama: http://localhost:11434

**External:**
- Supabase: https://ddgmuyeresgwgojoegiw.supabase.co
- Twilio Console: https://www.twilio.com/console
- ngrok Dashboard: http://127.0.0.1:4040

## Tips

1. 🔥 Always ensure ngrok is running for voice gateway when making real calls
2. 💾 Check logs if something fails: `docker-compose logs -f`
3. 🧪 Test with your own number first
4. 📝 Monitor transcripts in Supabase
5. ⚡ Use `base` Whisper model for faster processing

---

**You're all set! Happy calling! 🎉**
