# RelayX - Complete Architecture Guide

## 📖 Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Breakdown](#component-breakdown)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Authentication System](#authentication-system)
9. [Deployment Architecture](#deployment-architecture)

---

## Overview

**RelayX** is a production-ready AI-powered outbound calling system that enables intelligent phone conversations. It's designed as a multi-service architecture with real-time voice processing, web dashboard management, and comprehensive call analytics.

### What It Does
- Makes AI-powered outbound phone calls via Twilio
- Conducts natural conversations using LLM (Large Language Models)
- Converts speech to text in real-time (STT)
- Generates human-like voice responses (TTS)
- Tracks and analyzes all conversations
- Provides web dashboard for management and monitoring
- Supports multi-user authentication and access control

### Key Features
- ✅ Real-time voice conversations with <4s response time
- ✅ Natural language understanding and generation
- ✅ Voice Activity Detection (VAD) for barge-in support
- ✅ Web-based agent configuration and testing
- ✅ Complete call transcripts and analytics
- ✅ Calendar integration (Cal.com)
- ✅ Knowledge base for agent context
- ✅ Multi-user authentication with JWT
- ✅ Dockerized microservices architecture

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Frontend (React + TypeScript)                          │   │
│  │  - Dashboard, Agent Config, Call Management             │   │
│  │  - Real-time monitoring, Analytics                       │   │
│  │  Served on: http://localhost:3000 (Docker/Nginx)        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVICES                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Backend API (FastAPI)                                   │   │
│  │  - Agent CRUD operations                                 │   │
│  │  - Call initiation & tracking                            │   │
│  │  - Knowledge base management                             │   │
│  │  - Authentication & authorization                        │   │
│  │  - Calendar integration (Cal.com)                        │   │
│  │  Port: 8000 (Docker)                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↕                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Voice Gateway (FastAPI + WebSocket)                     │   │
│  │  - Real-time audio stream processing                     │   │
│  │  - Speech-to-Text (STT) via Groq Whisper                │   │
│  │  - LLM conversation via Groq Llama-3.1                   │   │
│  │  - Text-to-Speech (TTS) local/cloud                     │   │
│  │  - Voice Activity Detection (VAD)                        │   │
│  │  Port: 8001 (Docker)                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Twilio    │  │   Supabase   │  │     Groq     │           │
│  │  Phone API  │  │  PostgreSQL  │  │   LLM/STT    │           │
│  │  WebSocket  │  │   Database   │  │     APIs     │           │
│  └─────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Communication Flow

```
User Browser → Frontend (React) → Backend API (FastAPI) → Database (Supabase)
                                      ↓
                                Twilio API (Initiates Call)
                                      ↓
                            Twilio → Voice Gateway (WebSocket)
                                      ↓
                            STT → LLM → TTS → Audio Response
                                      ↓
                              Back to Twilio → Caller
```

---

## Component Breakdown

### 1. Frontend (React + TypeScript)

**Location:** `/frontend/src/`

**Purpose:** User interface for managing AI calling agents and monitoring calls

**Key Pages:**
- **LandingPage** - Public homepage
- **LoginPage** - User authentication
- **Dashboard** - Main control panel with stats and recent calls
- **BotSettings** - Create and configure AI agents
- **TestBot** - Test agent responses before deployment
- **Calls** - View all call history and details
- **CallDetails** - Deep dive into individual call transcripts
- **Contacts** - Manage contact lists
- **CalIntegration** - Calendar integration settings
- **KnowledgeBase** - Upload context for agents

**Tech Stack:**
- React 18 with TypeScript
- Vite (Build tool)
- TailwindCSS (Styling)
- React Router v6 (Navigation)
- Nginx (Production server in Docker)

**Key Files:**
```
frontend/
├── src/
│   ├── App.tsx               # Main app with routing
│   ├── main.tsx              # Entry point
│   ├── pages/                # Page components
│   │   ├── Dashboard.tsx
│   │   ├── BotSettings.tsx
│   │   ├── Calls.tsx
│   │   └── ...
│   ├── components/           # Reusable UI components
│   └── contexts/
│       └── AuthContext.tsx   # Authentication state management
├── nginx.conf                # Production nginx config
├── Dockerfile                # Multi-stage build
└── package.json              # Dependencies
```

**Docker:**
- Builds static assets with Vite
- Serves via Nginx on port 80 (mapped to 3000)
- Proxies API requests to backend:8000

---

### 2. Backend API (FastAPI)

**Location:** `/backend/`

**Purpose:** Core business logic, API endpoints, authentication, and orchestration

**Main File:** `main.py` (1324 lines)

**Key Responsibilities:**
1. **Agent Management**
   - CRUD operations for AI agents
   - Prompt configuration and templates
   - Voice settings management

2. **Call Management**
   - Initiate outbound calls via Twilio
   - Track call status and metadata
   - Store and retrieve call transcripts
   - Call analytics and sentiment analysis

3. **Authentication & Authorization**
   - JWT-based auth (access + refresh tokens)
   - User registration and login
   - Password hashing with bcrypt
   - Protected routes with user_id injection

4. **Knowledge Base**
   - Upload text/document context for agents
   - URL scraping and content extraction
   - Associate knowledge with specific agents

5. **Calendar Integration**
   - Cal.com API integration
   - Event scheduling during calls
   - Calendar availability checking

**API Endpoints Structure:**

```python
# Authentication
POST   /auth/login          # Login with email/password
POST   /auth/signup         # Create new user account
POST   /auth/refresh        # Refresh access token

# Agents
GET    /agents              # List all agents (user-scoped)
POST   /agents              # Create new agent
GET    /agents/{id}         # Get agent details
PUT    /agents/{id}         # Update agent configuration
DELETE /agents/{id}         # Delete agent

# Calls
POST   /calls/outbound      # Initiate outbound call
GET    /calls               # List all calls (user-scoped)
GET    /calls/{id}          # Get call details
GET    /calls/{id}/transcripts   # Get call transcript
GET    /calls/{id}/analysis      # Get call analytics

# Knowledge Base
GET    /api/agents/{id}/knowledge        # Get agent's knowledge
POST   /api/knowledge                    # Add knowledge entry
POST   /api/knowledge/from-url           # Scrape URL for knowledge
DELETE /api/knowledge/{id}               # Remove knowledge entry
POST   /api/knowledge/upload             # Upload file

# Calendar (Cal.com)
GET    /cal/events          # List upcoming events
POST   /cal/events          # Create new event
GET    /cal/availability    # Check availability

# System
GET    /health              # Health check endpoint
GET    /api-credits         # Check API usage/credits
```

**Key Files:**
```
backend/
├── main.py               # Main FastAPI app (1324 lines)
├── auth.py               # JWT authentication utilities
├── auth_routes.py        # Auth endpoint implementations
├── cal_routes.py         # Calendar integration routes
├── requirements.txt      # Python dependencies
├── Dockerfile            # Backend container config
└── static/               # Static assets for dashboard
```

**Dependencies:**
- FastAPI (Web framework)
- Uvicorn (ASGI server)
- python-jose (JWT handling)
- bcrypt (Password hashing)
- Twilio SDK (Phone API)
- httpx (HTTP client)
- Supabase Python SDK

---

### 3. Voice Gateway (Real-time Call Handler)

**Location:** `/voice_gateway/`

**Purpose:** Real-time audio processing and conversation management during active calls

**Main File:** `voice_gateway.py` (1417 lines)

**Architecture Type:** Event-driven state machine with WebSocket communication

**State Machine (3 States):**
```
LISTENING (Initial)
    ↓ (VAD detects speech start)
USER_SPEAKING
    ↓ (VAD detects silence end)
AI_SPEAKING
    ↓ (TTS playback complete)
LISTENING (Loop)
```

**Core Pipeline:**
```
1. Twilio Call → WebSocket Connection
2. Audio Chunks (μ-law PCM) → Buffer
3. VAD (Voice Activity Detection) → Trigger
4. STT (Speech-to-Text) → Transcript
5. LLM (Language Model) → Response
6. TTS (Text-to-Speech) → Audio
7. Audio → Twilio → Caller
```

**Key Features:**

1. **Voice Activity Detection (VAD)**
   - Uses WebRTC VAD algorithm
   - 240ms speech start threshold
   - 300ms silence end threshold
   - Enables natural conversation flow

2. **Speech-to-Text (STT)**
   - Groq Whisper API (primary)
   - AssemblyAI (fallback)
   - Deepgram (alternative)
   - Real-time transcription <500ms

3. **Large Language Model (LLM)**
   - Groq Llama-3.1-8b-instant
   - Context-aware responses
   - Agent personality injection
   - Knowledge base integration

4. **Text-to-Speech (TTS)**
   - Piper TTS (local, ultra-fast)
   - Fish Audio (cloud, high quality)
   - OpenAI TTS (alternative)
   - Streaming audio generation

5. **Barge-in Support**
   - User can interrupt AI mid-speech
   - Instant state transition
   - Audio buffer management

**WebSocket Events:**
```python
# Twilio → Voice Gateway
{
  "event": "media",
  "media": {
    "payload": "base64_audio_chunk"
  }
}

# Voice Gateway → Twilio
{
  "event": "media",
  "media": {
    "payload": "base64_audio_response"
  }
}
```

**Performance Targets:**
- Total response time: <4 seconds
- STT latency: <500ms
- LLM latency: <2 seconds
- TTS latency: <1 second

**Key Files:**
```
voice_gateway/
├── voice_gateway.py      # Main WebSocket handler (1417 lines)
├── requirements.txt      # Python dependencies
├── Dockerfile            # Voice gateway container
└── start.sh             # Container startup script
```

---

### 4. Shared Modules

**Location:** `/shared/`

**Purpose:** Reusable components shared between backend and voice gateway

**Modules:**

1. **database.py** - Supabase Database Client
```python
class SupabaseDB:
    # Agent operations
    async def create_agent()
    async def get_agent()
    async def list_agents()
    async def update_agent()
    
    # Call operations
    async def create_call()
    async def get_call()
    async def update_call()
    
    # Transcript operations
    async def create_transcript()
    async def get_transcripts()
    
    # Knowledge base operations
    async def create_knowledge()
    async def get_agent_knowledge()
```

2. **llm_client.py** - Language Model Interface
```python
class LLMClient:
    async def generate_response(prompt, context)
    async def analyze_intent(text)
    async def classify_sentiment(text)
```

3. **stt_client.py** - Speech-to-Text Client
```python
class STTClient:
    async def transcribe_audio(audio_bytes)
    async def transcribe_stream(audio_stream)
```

4. **tts_client.py** - Text-to-Speech Client
```python
class TTSClient:
    async def synthesize(text, voice_id)
    async def stream_audio(text)
```

5. **url_scraper.py** - Web Content Extraction
```python
async def scrape_url(url)
async def extract_text(html)
async def clean_content(text)
```

6. **cal_client.py** - Cal.com Integration
```python
class CalClient:
    async def get_events()
    async def create_event()
    async def check_availability()
```

---

## Data Flow

### 1. User Creates Agent (Web UI)

```
User (Browser)
  ↓ Fill form (name, prompt, voice settings)
Frontend (React)
  ↓ POST /agents {name, prompt_text, voice_settings}
Backend (FastAPI)
  ↓ Validate data, add user_id
Supabase Database
  ↓ Insert into agents table
Backend
  ↓ Return agent object {id, name, ...}
Frontend
  ↓ Show success message, navigate to dashboard
```

### 2. User Initiates Call

```
User (Browser)
  ↓ Click "Make Call" with phone number
Frontend
  ↓ POST /calls/outbound {agent_id, phone_number}
Backend (FastAPI)
  ↓ Get agent from database
  ↓ Create call record (status: initiated)
  ↓ Call Twilio API
Twilio
  ↓ Dial phone number
  ↓ On connect → POST to voice gateway webhook
Voice Gateway
  ↓ Establish WebSocket connection
  ↓ Start audio streaming
```

### 3. Active Call (Real-time)

```
Caller speaks
  ↓
Twilio (phone network)
  ↓ Audio chunks via WebSocket
Voice Gateway
  ↓ VAD detects speech
  ↓ Buffer audio → STT (Groq Whisper)
  ↓ Transcript: "I need help with my order"
  ↓ Get agent prompt + knowledge
  ↓ LLM (Groq Llama-3.1) generates response
  ↓ Response: "I'd be happy to help! What's your order number?"
  ↓ TTS (Piper) converts to audio
  ↓ Stream audio via WebSocket
Twilio
  ↓ Play audio to caller
  ↓ Save transcript to database
```

### 4. Call Analysis (Post-call)

```
Call ends
  ↓
Voice Gateway
  ↓ Update call status (completed)
  ↓ POST to backend with final transcript
Backend
  ↓ Analyze conversation with LLM
  ↓ Extract: sentiment, outcome, key points
  ↓ Store analysis in database
Frontend (auto-refresh)
  ↓ Show updated call list
User clicks call
  ↓ GET /calls/{id}
Backend
  ↓ Return call details + transcript + analysis
Frontend
  ↓ Display full conversation view
```

---

## Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first CSS
- **React Router v6** - Client-side routing
- **Nginx** - Production web server

### Backend
- **Python 3.11** - Runtime
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **python-jose** - JWT implementation
- **bcrypt** - Password hashing

### Voice Processing
- **Groq Whisper** - STT (14,400 req/day free)
- **Groq Llama-3.1** - LLM (14,400 req/day free)
- **Piper TTS** - Local text-to-speech
- **WebRTC VAD** - Voice activity detection

### Communication
- **Twilio** - Phone network API
- **WebSocket** - Real-time audio streaming

### Database
- **Supabase** - PostgreSQL managed service
- **PostgREST** - Auto-generated REST API

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **ngrok** - Local tunneling (development)

---

## API Reference

### Authentication

#### POST /auth/login
```json
Request:
{
  "email": "test@relayx.ai",
  "password": "test123"
}

Response:
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "test@relayx.ai",
    "name": "Test User"
  }
}
```

#### POST /auth/signup
```json
Request:
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "name": "John Doe"
}

Response:
{
  "message": "User created successfully",
  "user_id": "uuid"
}
```

### Agents

#### POST /agents
```json
Request:
{
  "name": "Sales Assistant",
  "prompt_text": "You are a helpful sales assistant...",
  "voice_settings": {
    "voice_id": "en_US-libritts-high",
    "speed": 1.0
  },
  "llm_model": "llama3:8b",
  "temperature": 0.7,
  "max_tokens": 150
}

Response:
{
  "id": "uuid",
  "name": "Sales Assistant",
  "prompt_text": "You are a helpful sales assistant...",
  "user_id": "uuid",
  "created_at": "2025-12-22T14:00:00Z",
  ...
}
```

#### GET /agents
```json
Response:
[
  {
    "id": "uuid",
    "name": "Sales Assistant",
    "is_active": true,
    "call_count": 25,
    "avg_duration": 180,
    "last_used": "2025-12-22T14:00:00Z"
  },
  ...
]
```

### Calls

#### POST /calls/outbound
```json
Request:
{
  "agent_id": "uuid",
  "phone_number": "+1234567890",
  "metadata": {
    "campaign": "Q4 Outreach"
  }
}

Response:
{
  "call_id": "uuid",
  "status": "initiated",
  "twilio_sid": "CAxxxx",
  "message": "Call initiated successfully"
}
```

#### GET /calls/{call_id}
```json
Response:
{
  "id": "uuid",
  "agent_id": "uuid",
  "phone_number": "+1234567890",
  "status": "completed",
  "duration": 180,
  "outcome": "interested",
  "sentiment": "positive",
  "created_at": "2025-12-22T14:00:00Z",
  "ended_at": "2025-12-22T14:03:00Z",
  "transcripts": [
    {
      "speaker": "ai",
      "text": "Hello! This is Emma from RelayX...",
      "timestamp": "2025-12-22T14:00:05Z"
    },
    {
      "speaker": "user",
      "text": "Hi, who's calling?",
      "timestamp": "2025-12-22T14:00:10Z"
    },
    ...
  ]
}
```

---

## Database Schema

### Tables

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    company TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### auth_tokens
```sql
CREATE TABLE auth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### agents
```sql
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    template_source TEXT,
    voice_settings JSONB DEFAULT '{}',
    llm_model TEXT DEFAULT 'llama3:8b',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 150,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### calls
```sql
CREATE TABLE calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    phone_number TEXT NOT NULL,
    status TEXT DEFAULT 'initiated',
    twilio_sid TEXT,
    duration INTEGER,
    outcome TEXT,
    sentiment TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);
```

#### transcripts
```sql
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id UUID REFERENCES calls(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL,
    text TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

#### knowledge_base
```sql
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_type TEXT DEFAULT 'manual',
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Relationships

```
users (1) ──→ (N) agents
users (1) ──→ (N) calls
users (1) ──→ (N) knowledge_base
users (1) ──→ (N) auth_tokens

agents (1) ──→ (N) calls
agents (1) ──→ (N) knowledge_base

calls (1) ──→ (N) transcripts
```

---

## Authentication System

### JWT-based Authentication

**Token Types:**
1. **Access Token** - Short-lived (1 hour), used for API requests
2. **Refresh Token** - Long-lived (30 days), used to get new access tokens

**Flow:**

```
1. Login (POST /auth/login)
   ↓
   Verify password with bcrypt
   ↓
   Generate access_token (exp: 1h)
   Generate refresh_token (exp: 30d)
   ↓
   Store refresh_token in auth_tokens table
   ↓
   Return both tokens to client

2. API Request
   ↓
   Send: Authorization: Bearer {access_token}
   ↓
   Backend verifies JWT signature
   ↓
   Extract user_id from token
   ↓
   Inject user_id into request
   ↓
   Process request (user-scoped)

3. Token Refresh (when access_token expires)
   ↓
   POST /auth/refresh {refresh_token}
   ↓
   Verify refresh_token in database
   ↓
   Generate new access_token
   ↓
   Return new access_token
```

**Protected Routes:**
```python
@app.get("/agents")
async def list_agents(user_id: str = Depends(get_current_user_id)):
    # user_id automatically extracted from JWT
    agents = await db.list_agents(user_id=user_id)
    return agents
```

**Password Security:**
- Bcrypt hashing with salt rounds
- 72-byte max password length (bcrypt limit)
- Never store plaintext passwords

---

## Deployment Architecture

### Docker Compose Setup

**Services:**
1. **frontend** - React app (port 3000)
2. **backend** - FastAPI API (port 8000)
3. **voice-gateway** - WebSocket handler (port 8001)

**Network:**
- All services on `relayx-network` bridge
- Internal DNS resolution (service names)
- Only frontend, backend, voice-gateway exposed externally

**Volumes:**
- Code mounted for live reload in development
- Logs persisted to `./logs`
- Docker socket mounted for backend (optional)

### Environment Variables

**Required:**
```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...

# Groq API
GROQ_API_KEY=gsk_xxxxx

# Authentication
JWT_SECRET_KEY=your-secret-key-here

# Cal.com (optional)
CAL_API_KEY=cal_live_xxxxx
```

### Production Considerations

1. **Scaling**
   - Voice Gateway: Scale horizontally with load balancer
   - Backend: Stateless, can scale easily
   - Frontend: Static assets, use CDN

2. **Security**
   - Use HTTPS (SSL/TLS)
   - Rotate JWT secrets regularly
   - Rate limiting on API endpoints
   - Input validation and sanitization

3. **Monitoring**
   - Log aggregation (ELK stack)
   - Error tracking (Sentry)
   - Performance monitoring (New Relic)
   - Call analytics dashboard

4. **Database**
   - Regular backups (Supabase handles this)
   - Connection pooling
   - Index optimization

---

## Directory Structure

```
RelayX/
├── backend/                    # FastAPI backend service
│   ├── main.py                # Main API application (1324 lines)
│   ├── auth.py                # JWT utilities
│   ├── auth_routes.py         # Auth endpoints
│   ├── cal_routes.py          # Calendar endpoints
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container
│   └── static/                # Dashboard assets
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.tsx            # Main app component
│   │   ├── pages/             # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── BotSettings.tsx
│   │   │   ├── Calls.tsx
│   │   │   └── ...
│   │   ├── components/        # Reusable components
│   │   └── contexts/          # React contexts
│   ├── nginx.conf             # Production server config
│   ├── Dockerfile             # Frontend container
│   └── package.json           # NPM dependencies
│
├── voice_gateway/              # Real-time call handler
│   ├── voice_gateway.py       # WebSocket handler (1417 lines)
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Voice gateway container
│   └── start.sh               # Startup script
│
├── shared/                     # Shared modules
│   ├── database.py            # Supabase client (521 lines)
│   ├── llm_client.py          # LLM interface
│   ├── stt_client.py          # Speech-to-text
│   ├── tts_client.py          # Text-to-speech
│   ├── url_scraper.py         # Web content extraction
│   └── cal_client.py          # Cal.com integration
│
├── docker-compose.yml          # Multi-service orchestration
├── .env                        # Environment variables
├── requirements.txt            # Root Python dependencies
├── RUN_THIS_MIGRATION.sql     # Database setup
│
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── QUICK_START.md
│   └── TROUBLESHOOTING.md
│
└── logs/                       # Application logs
    ├── backend.log
    └── voice_gateway.log
```

---

## How It All Works Together

### Scenario: User Makes a Call

**Step-by-step:**

1. **User logs in** (frontend/LoginPage.tsx)
   - Enters email/password
   - Frontend sends POST to /auth/login
   - Backend verifies credentials with bcrypt
   - Returns JWT tokens
   - Frontend stores in localStorage

2. **User creates agent** (frontend/BotSettings.tsx)
   - Fills form with agent name, personality prompt
   - Selects voice settings
   - Frontend sends POST to /agents with JWT
   - Backend validates token, extracts user_id
   - Saves agent to database with user_id
   - Returns agent object

3. **User initiates call** (frontend/Dashboard.tsx)
   - Selects agent, enters phone number
   - Frontend sends POST to /calls/outbound
   - Backend validates agent ownership
   - Creates call record (status: initiated)
   - Calls Twilio API to dial number
   - Returns call_id

4. **Twilio connects call**
   - Caller answers phone
   - Twilio sends webhook to voice gateway
   - Voice gateway establishes WebSocket
   - Sends initial greeting via TTS

5. **Real-time conversation** (voice_gateway/voice_gateway.py)
   - Audio streams from Twilio via WebSocket
   - VAD detects when user speaks
   - Buffers audio, sends to STT (Groq Whisper)
   - Gets transcript: "I'm interested in your product"
   - Fetches agent prompt + knowledge from database
   - Sends to LLM (Groq Llama-3.1) with context
   - LLM generates: "That's great! Let me tell you about..."
   - Converts to audio via TTS (Piper)
   - Streams audio back to Twilio
   - Saves transcript to database

6. **Call ends**
   - User hangs up or conversation completes
   - Voice gateway updates call status
   - Sends final transcript to backend
   - Backend analyzes with LLM (sentiment, outcome)
   - Stores analysis in database

7. **User views results** (frontend/CallDetails.tsx)
   - Dashboard shows updated call count
   - User clicks on call
   - Frontend fetches GET /calls/{id}
   - Backend returns call details + transcripts
   - Frontend displays conversation timeline
   - Shows analytics (sentiment, duration, outcome)

---

## Performance & Optimization

### Response Time Targets
- **Total call response**: <4 seconds (user speaks → AI responds)
  - STT: <500ms
  - LLM: <2s
  - TTS: <1s
  - Network: <500ms

### Optimization Techniques

1. **Voice Gateway**
   - Streaming TTS (start playing before complete)
   - Audio buffer management
   - VAD edge-trigger (no polling)
   - Connection pooling for API calls

2. **Backend**
   - Async I/O with FastAPI
   - Database query optimization (indexes)
   - Response caching (Redis potential)
   - Batch operations where possible

3. **Frontend**
   - Code splitting (lazy loading)
   - Asset optimization (Vite)
   - Client-side caching
   - Debounced API calls

### Scalability

**Current:** Single-instance deployment (Docker Compose)

**Future:**
- Kubernetes for orchestration
- Load balancer for voice gateway
- Horizontal scaling of backend
- CDN for frontend static assets
- Redis for session/cache
- Message queue for async tasks (RabbitMQ/Redis)

---

## Next Steps & Roadmap

### Immediate
- ✅ Authentication system (DONE)
- ✅ Multi-user support (DONE)
- ✅ Calendar integration (DONE)
- 🔲 Contacts management UI
- 🔲 Bulk calling campaigns
- 🔲 Advanced analytics dashboard

### Short-term
- 🔲 Voice recording playback
- 🔲 Real-time call monitoring
- 🔲 A/B testing for agents
- 🔲 Custom TTS voice training
- 🔲 SMS follow-up automation

### Long-term
- 🔲 Inbound call handling
- 🔲 Multi-language support
- 🔲 CRM integrations
- 🔲 Advanced NLU (intent detection)
- 🔲 Mobile app (React Native)

---

## Troubleshooting

### Common Issues

**1. Docker containers not starting**
```bash
# Check logs
docker logs relayx-backend
docker logs relayx-voice-gateway

# Rebuild
docker compose build --no-cache
docker compose up -d
```

**2. Authentication not working**
- Verify JWT_SECRET_KEY in .env
- Check password hash in database
- Clear browser localStorage

**3. Calls not connecting**
- Verify Twilio credentials
- Check VOICE_GATEWAY_URL is publicly accessible
- Ensure ngrok is running (development)

**4. Database connection failed**
- Verify SUPABASE_URL and SUPABASE_ANON_KEY
- Check Supabase project status
- Run RUN_THIS_MIGRATION.sql if tables missing

---

## Conclusion

RelayX is a comprehensive AI calling system with:
- 3-tier architecture (Frontend, Backend, Voice Gateway)
- Real-time voice processing with <4s response
- Multi-user authentication with JWT
- Comprehensive call analytics
- Dockerized deployment
- Production-ready scalability

**Tech Highlights:**
- FastAPI for high-performance async APIs
- React for modern, responsive UI
- WebSocket for real-time communication
- Groq API for cost-effective AI (free tier)
- Supabase for managed PostgreSQL
- Docker for consistent deployment

**Key Files to Understand:**
1. `backend/main.py` - Core API logic
2. `voice_gateway/voice_gateway.py` - Real-time call handling
3. `shared/database.py` - Database operations
4. `frontend/src/App.tsx` - UI routing
5. `docker-compose.yml` - Service orchestration

For more details, see:
- README.md - Quick start guide
- docs/ARCHITECTURE.md - Technical deep dive
- docs/TROUBLESHOOTING.md - Common issues

---

**Created:** December 22, 2025
**Version:** 1.0
**Status:** Production-ready with authentication
