# Troubleshooting Guide

## Common Issues and Solutions

### 🔴 Ollama Issues

#### Problem: `ollama list` shows no models

**Solution:**
```powershell
ollama pull llama3:8b
ollama list  # Verify it's downloaded
```

#### Problem: Ollama not responding on port 11434

**Solution:**
```powershell
# Check if Ollama is running
Get-Process ollama

# If not running, start it
ollama serve

# Test the endpoint
curl http://localhost:11434/api/tags
```

---

### 🔴 ngrok Issues

#### Problem: ngrok tunnel not created

**Solution:**
```powershell
# Check if ngrok is authenticated
ngrok config check

# Add auth token if needed
ngrok config add-authtoken YOUR_TOKEN

# Test manually
ngrok http 11434
```

#### Problem: "ngrok tunnel expired" or "too many tunnels"

**Solution:**
- Free ngrok accounts have limits
- Kill existing ngrok processes:
```powershell
Get-Process ngrok | Stop-Process
```
- Restart the startup script

---

### 🔴 Docker Issues

#### Problem: Docker services won't start

**Solution:**
```powershell
# Check Docker is running
docker info

# If not, start Docker Desktop

# View logs
docker-compose logs -f

# Clean restart
docker-compose down
docker-compose up --build
```

#### Problem: Port already in use (8000 or 8001)

**Solution:**
```powershell
# Find process using the port
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# Kill the process (replace PID with actual PID)
Stop-Process -Id PID -Force
```

---

### 🔴 Supabase Issues

#### Problem: Database connection failed

**Solutions:**
1. Check credentials in `.env`:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...your-key
```

2. Verify project is active in Supabase dashboard

3. Run schema if not done:
```powershell
.\scripts\setup-db.ps1
```

#### Problem: "Agent not found" or "Call not found"

**Solution:**
- Ensure schema is applied
- Check data exists:
```sql
-- In Supabase SQL Editor
SELECT * FROM agents;
SELECT * FROM calls;
```

---

### 🔴 Twilio Issues

#### Problem: Calls not connecting

**Checklist:**
1. ✅ Twilio credentials correct in `.env`
2. ✅ Phone number is valid and verified
3. ✅ Voice gateway is publicly accessible (ngrok)
4. ✅ `VOICE_GATEWAY_URL` is set correctly
5. ✅ WebSocket URL uses `wss://` not `ws://`

**Test webhook URL:**
```powershell
curl https://your-gateway.ngrok.io/
```

#### Problem: "TwiML Error" or callback failures

**Solution:**
1. Check Twilio debugger: https://www.twilio.com/console/debugger
2. Verify TwiML URLs are accessible
3. Check voice gateway logs:
```powershell
docker-compose logs voice_gateway -f
```

---

### 🔴 Audio/Voice Issues

#### Problem: No audio or garbled audio

**Solutions:**
1. Check Whisper model is loaded:
```powershell
# In voice gateway logs
docker-compose logs voice_gateway | findstr "Whisper"
```

2. Check TTS model:
```powershell
# May take time to download first time
docker-compose logs voice_gateway | findstr "TTS"
```

3. Audio format conversion errors:
- Check logs for `audioop` errors
- Ensure `ffmpeg` is installed in container

#### Problem: STT not recognizing speech

**Solutions:**
- Use better Whisper model: `WHISPER_MODEL=small` or `medium`
- Check audio buffer size in `voice_gateway.py`
- Increase silence detection threshold

---

### 🔴 LLM Issues

#### Problem: LLM responses are slow

**Solutions:**
1. Use smaller model:
```powershell
ollama pull llama3:8b  # Instead of 70b
```

2. Reduce max_tokens in agent config

3. Check CPU/GPU usage

#### Problem: LLM gives generic "error" responses

**Solutions:**
1. Check ngrok URL is accessible:
```powershell
curl $env:LLM_BASE_URL/api/tags
```

2. Check Ollama logs for errors

3. Verify model is loaded:
```powershell
ollama ps
```

---

### 🔴 Development Issues

#### Problem: Python import errors

**Solution:**
```powershell
# Ensure shared modules are in path
# Add to main.py / voice_gateway.py:
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
```

#### Problem: Dependencies not installing

**Solution:**
```powershell
# Use correct requirements file
pip install -r requirements.txt

# For backend only
pip install -r backend/requirements.txt

# For voice gateway only
pip install -r voice_gateway/requirements.txt
```

#### Problem: Logs not appearing

**Solution:**
```powershell
# Create logs directory
New-Item -ItemType Directory -Force -Path logs/backend
New-Item -ItemType Directory -Force -Path logs/voice_gateway

# Check log level in code (should be INFO or DEBUG)
```

---

### 🔴 Performance Issues

#### Problem: High latency in conversations

**Optimizations:**
1. Use GPU for Whisper/TTS (if available)
2. Use `faster-whisper` instead of `openai-whisper`
3. Reduce LLM max_tokens
4. Use streaming for TTS (future enhancement)
5. Pre-load models at startup

#### Problem: High memory usage

**Solutions:**
1. Use smaller models:
   - Whisper: `tiny` or `base`
   - LLM: `llama3:8b` instead of larger
2. Limit concurrent calls
3. Add memory limits in docker-compose:
```yaml
deploy:
  resources:
    limits:
      memory: 4G
```

---

### 🔴 Network Issues

#### Problem: Services can't communicate

**Solution:**
```powershell
# Check Docker network
docker network ls
docker network inspect relayx_relayx_network

# Restart network
docker-compose down
docker-compose up
```

#### Problem: Ngrok URLs not updating in .env

**Solution:**
- Manually update `.env` with ngrok URLs
- Or run startup script again:
```powershell
.\scripts\start.ps1
```

---

## Debugging Tips

### Enable Debug Logging

In `backend/main.py` and `voice_gateway/voice_gateway.py`:
```python
logger.add("logs/debug.log", level="DEBUG")
```

### View Real-Time Logs

```powershell
# Backend
docker-compose logs backend -f

# Voice Gateway
docker-compose logs voice_gateway -f

# Both
docker-compose logs -f
```

### Test Individual Components

**Test LLM:**
```powershell
curl http://localhost:11434/api/tags
```

**Test Backend:**
```powershell
curl http://localhost:8000/health
```

**Test Voice Gateway:**
```powershell
curl http://localhost:8001/
```

### Inspect Database

```sql
-- Check recent calls
SELECT * FROM calls ORDER BY created_at DESC LIMIT 10;

-- Check transcripts
SELECT * FROM transcripts WHERE call_id = 'YOUR-CALL-ID' ORDER BY timestamp;

-- Check agents
SELECT * FROM agents;
```

---

## Getting Help

1. Check GitHub Issues
2. Review logs thoroughly
3. Test each component individually
4. Verify environment variables
5. Check Twilio debugger console

---

## Reset Everything

If all else fails:

```powershell
# Stop all services
docker-compose down

# Remove volumes
docker-compose down -v

# Clear logs
Remove-Item logs\* -Recurse -Force

# Rebuild
docker-compose up --build
```
