# RelayX - AI Outbound Caller

<div align="center">

🤖 **Production-ready AI-powered outbound calling system**

Built with Twilio • Supabase • Groq Whisper • Llama-3.1 • Piper TTS

[Architecture](#-architecture) • [Setup](#-quick-start) • [Usage](#-usage) • [Tech Stack](#-tech-stack)

</div>

---

## 📋 Overview

RelayX is a production-ready AI voice calling system that enables intelligent phone conversations. Features:

- ✅ **Outbound Calls** - Make AI-powered calls using Twilio
- ✅ **Natural Speech** - Piper TTS with high-quality voices (libritts-high)
- ✅ **Real-time STT** - Groq Whisper API for fast, accurate transcription
- ✅ **Smart AI** - Groq Llama-3.1-8b-instant for natural conversations
- ✅ **Speech Recognition** - Twilio Gather with phone_call model
- ✅ **Full Tracking** - Complete call transcripts and metadata in Supabase
- ✅ **Web Dashboard** - Real-time monitoring and testing interface
- ✅ **Auto Tunneling** - ngrok automatically exposes local services

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Twilio Cloud                        │
│                 (Phone Network + Speech Recognition)        │
└────────────────┬───────────────────────┬────────────────────┘
                 │                       │
                 │ Gather (Speech)       │ HTTP Callbacks
                 │ + Play (Audio)        │ (Status Updates)
                 ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                Voice Gateway (FastAPI)                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────┐ │
│  │  Groq    │──▶│   Groq   │──▶│  Piper  │──▶│ Twilio  │ │
│  │ Whisper  │   │  Llama   │   │   TTS   │   │  Play   │ │
│  │  (STT)   │   │  (LLM)   │   │ (Local) │   │ (HTTP)  │ │
│  └──────────┘   └──────────┘   └──────────┘   └─────────┘ │
│                                                             │
│  • Serve TTS audio via HTTP (/audio/{filename})            │
│  • Handle Gather callbacks (/gather/{call_id})             │
│  • Generate TwiML with Gather + Play                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Store Transcripts
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Backend + Dashboard                  │
│  • Agent Management (AI personalities)                      │
│  • Call Initiation & Tracking                              │
│  • Real-time Dashboard (auto-refresh)                       │
│  • API Credit Monitoring                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Supabase (PostgreSQL)                      │
│  • agents (AI configs)  • calls (metadata)                  │
│  • transcripts (history) • timestamps & analytics           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    ngrok (Auto-started)                     │
│  Exposes: https://xxxx.ngrok-free.app → localhost:8001     │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Windows** (PowerShell)
- **Python 3.11+**
- **ngrok** (installed and in PATH)
- **Twilio Account** (trial or paid)
- **Supabase Project**
- **Groq API Key** (free tier: 14,400 requests/day)

### 1️⃣ Clone and Setup

```powershell
cd D:\projects\RelayX
pip install -r requirements.txt
```

### 2️⃣ Configure Environment

Edit `.env` file:

```env
# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key

# API Keys
GROQ_API_KEY=gsk_your_key_here  # Get from https://console.groq.com

# Cloud Service Toggle
USE_CLOUD_STT=true   # Groq Whisper (recommended)
USE_CLOUD_TTS=false  # Piper TTS (local, fast)
USE_CLOUD_LLM=true   # Groq Llama (recommended)
```

### 3️⃣ Setup Database

Run the schema in your Supabase SQL Editor:

1. Go to your Supabase project → SQL Editor
2. Copy contents from `db/schema.sql`
3. Execute

This creates:
- `agents` - AI agent configurations (personality, prompts)
- `calls` - Call metadata (status, duration, SID)
- `transcripts` - Full conversation history

### 4️⃣ Start Services

**One Command Startup:**

```powershell
.\start.ps1
```

This automatically:
1. ✅ Checks prerequisites (Python, ngrok)
2. ✅ Kills old processes (clean restart)
3. ✅ Starts Backend API (port 8000)
4. ✅ Starts Voice Gateway (port 8001)
5. ✅ Launches ngrok tunnel (auto-configured)
6. ✅ Opens dashboard in browser

**Services Running:**
- Backend API: http://localhost:8000
- Dashboard: http://localhost:8000/dashboard
- Voice Gateway: https://xxxx.ngrok-free.app
- API Docs: http://localhost:8000/docs

### 5️⃣ Verify & Test

Open the dashboard: http://localhost:8000/dashboard

You'll see:
- **Live Stats**: Active calls, total calls, API credits
- **Test Call**: Make a test call to any verified number
- **Call History**: Recent calls with transcripts
- **Agent Management**: Configure AI personalities

## 📖 Usage

### Via Dashboard (Easiest)

1. Open http://localhost:8000/dashboard
2. Select your AI agent (default: "Sales Assistant")
3. Enter phone number (E.164 format: +1234567890)
4. Click "📋 Use: +917278082005" for quick-fill
5. Click "🎯 Start Call"
6. Watch real-time logs and transcripts

### Via API

**Create an AI Agent:**

```powershell
curl -X POST http://localhost:8000/agents `
  -H "Content-Type: application/json" `
  -d '{
    "name": "Emma - Customer Support",
    "system_prompt": "You are Emma, a warm and friendly AI assistant. Speak naturally with pauses. Keep responses SHORT (1-2 sentences).",
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

**Make an Outbound Call:**

```powershell
curl -X POST http://localhost:8000/calls/outbound `
  -H "Content-Type: application/json" `
  -d '{
    "agent_id": "uuid-from-previous-step",
    "to_number": "+1234567890"
  }'
```

Response:
```json
{
  "id": "call-uuid",
  "agent_id": "agent-uuid",
  "to_number": "+1234567890",
  "from_number": "+15079365100",
  "status": "initiated",
  "created_at": "2025-11-23T..."
}
```powershell
curl -X POST http://localhost:8000/calls/outbound `
  -H "Content-Type: application/json" `
  -d '{
    "agent_id": "your-agent-uuid",
    "to_number": "+1234567890"
  }'
```

**Get Call Transcript:**

```powershell
curl http://localhost:8000/calls/{call_id}/transcripts
```

## 🔌 API Reference

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents` | Create new agent |
| GET | `/agents` | List all agents |
| GET | `/agents/{id}` | Get agent details |
| PATCH | `/agents/{id}` | Update agent |

### Calls

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/calls/outbound` | Initiate outbound call |
| GET | `/calls` | List calls (filter by agent_id, status) |
| GET | `/calls/{id}` | Get call details |
| GET | `/calls/{id}/transcripts` | Get full conversation |
| GET | `/stats` | Dashboard statistics |
| GET | `/api-credits` | API usage tracking |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Detailed health status |
| GET | `/dashboard` | Web dashboard UI |
| GET | `/docs` | Interactive API docs |

## 🛠️ Tech Stack

### Backend & Infrastructure
- **FastAPI** - High-performance async API framework
- **Uvicorn** - ASGI server with auto-reload
- **Supabase (PostgreSQL)** - Database with real-time features
- **ngrok** - Secure tunneling for local development
- **Twilio** - Voice API and phone network

### AI & ML
- **Groq API** - Ultra-fast inference (14,400 req/day free)
  - Whisper Large v3 for STT (fastest commercial STT)
  - Llama 3.1 8B Instant for conversational AI
- **Piper TTS** - Local neural TTS (ONNX runtime)
  - Model: en_US-libritts-high (50MB, natural voice)
  - Speed: <1s generation, CPU-only, no GPU required

### Voice Processing
- **Twilio Gather** - Phone-optimized speech recognition
- **Audio Serving** - HTTP endpoints for TTS playback
- **Speech Hints** - Context-aware recognition improvements

### Frontend
- **Vanilla HTML/CSS/JS** - Zero build step, instant reload
- **Auto-refresh Dashboard** - WebSocket-like polling (10s/15s intervals)
- **Responsive Design** - Works on mobile/tablet/desktop

## 📁 Project Structure

```
RelayX/
├── backend/
│   ├── main.py                    # FastAPI backend + API endpoints
│   ├── static/
│   │   └── dashboard.html         # Real-time web dashboard
│   └── requirements.txt
│
├── voice_gateway/
│   ├── voice_gateway.py           # Twilio integration + TwiML
│   └── requirements.txt
│
├── shared/                        # Shared modules across services
│   ├── database.py                # Supabase client wrapper
│   ├── llm_client.py              # Groq LLM integration
│   ├── stt_client.py              # Groq Whisper STT
│   └── tts_client.py              # Piper TTS (local)
│
├── db/
│   └── schema.sql                 # PostgreSQL database schema
│
├── start.ps1                      # One-command startup script
├── .env                           # Configuration (not in git)
├── requirements.txt               # Python dependencies
└── README.md
```

### Key Files

**backend/main.py** (498 lines)
- Agent CRUD operations
- Call initiation with Twilio
- Dashboard statistics API
- API credit tracking
- Health checks

**voice_gateway/voice_gateway.py** (768 lines)
- TwiML generation with Gather
- Gather callback handling
- Piper TTS audio serving
- Conversation management
- Auto-ngrok tunnel setup

**shared/tts_client.py** (193 lines)
- Piper voice model management
- Auto-download high-quality voices
- WAV file generation
- Text normalization

**backend/static/dashboard.html** (571 lines)
- Real-time stats (active calls, credits)
- Test call interface with quick-fill
- Live call logs streaming
- Call history with transcripts
- Responsive grid layout

## 🐛 Troubleshooting

### ngrok Browser Warning

If Twilio can't reach your TwiML:

```powershell
# Get authtoken from https://dashboard.ngrok.com
ngrok config add-authtoken YOUR_TOKEN
```

### Call Connects But No Voice

```powershell
# Check voice gateway logs
cat logs/voice_gateway.log | Select-String "TwiML requested"

# Should see: "TwiML requested for call: {call_id}"
```

### Twilio Trial Message Not Bypassing

Twilio trial accounts require manual keypress - cannot be automated. Solutions:
1. **Add $1+ credit** to remove trial restrictions
2. **Verify the recipient number** in Twilio console
3. **Manually press 1** when you hear the trial message

### Speech Not Detected

Increase timeout in `voice_gateway.py`:
- `timeout="6"` - Time to start speaking
- `speechTimeout="3"` - Silence duration to end

### Piper Voice Sounds Robotic

Voice model might not be downloaded. Check:
```powershell
ls ~\.local\share\piper\
# Should see: en_US-libritts-high.onnx (50MB)
```

### API Credits Showing Wrong

Dashboard updates every 15s. Estimates:
- Groq: 8000 tokens/day - (calls × 500 tokens)
- Based on call count, not actual usage

## 🚧 Roadmap

- [x] Core outbound calling
- [x] Real-time STT/LLM/TTS pipeline  
- [x] Twilio Gather for speech input
- [x] Piper TTS for natural voice
- [x] Real-time web dashboard
- [x] API credit tracking
- [x] Call transcripts & history
- [ ] Inbound call handling
- [ ] Call recording storage (S3/Supabase)
- [ ] Post-call analysis (sentiment, summary)
- [ ] Multi-language support (Piper has 50+ voices)
- [ ] Webhook notifications (Slack, Discord)
- [ ] Advanced analytics dashboard
- [ ] Voice cloning (Piper custom voices)

## 💡 Key Features

### Why This Stack?

**Groq API** - 10x faster than OpenAI (300 tokens/sec vs 30)
- Free tier: 14,400 requests/day
- Whisper: 0.5s transcription (vs 2-3s)
- Llama 3.1: Natural conversations

**Piper TTS** - Production-ready local TTS
- No API costs (vs $15/1M chars for ElevenLabs)
- <1s generation time
- High-quality voices (22kHz sample rate)
- CPU-only (no GPU needed)

**Twilio Gather** - Better than WebSocket streaming
- Built-in VAD (Voice Activity Detection)
- Phone-optimized speech model
- Automatic timeout handling
- Lower latency than custom WebSocket

**Supabase** - PostgreSQL with superpowers
- Real-time subscriptions (future feature)
- Built-in auth (future feature)
- RESTful API auto-generated
- Free tier: 500MB database

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! This is an active project.

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 🙏 Acknowledgments

- **Twilio** - Telephony infrastructure & Gather API
- **Supabase** - PostgreSQL database platform
- **Groq** - Lightning-fast LLM inference
- **Piper TTS** - High-quality neural TTS (rhasspy project)
- **Meta** - Llama 3.1 language models
- **OpenAI** - Whisper speech recognition model

---

<div align="center">

**Built with ❤️ for developers who need AI voice calls**

[Report Bug](https://github.com/your-repo/issues) • [Request Feature](https://github.com/your-repo/issues) • [Documentation](https://github.com/your-repo/wiki)

</div>
