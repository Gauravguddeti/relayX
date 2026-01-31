# 🔧 RelayX Voice Gateway - Critical Bugs & Fixes Report

## 📋 CONTEXT
- **Project**: RelayX AI voice calling platform
- **Tech Stack**: FastAPI + Twilio Media Streams + Sarvam AI (TTS/STT) + Groq LLM
- **Current File**: `voice_gateway/voice_gateway.py` (2113 lines)
- **TTS Voice**: Manisha (bulbul:v2)
- **STT Model**: saarika:v2.5
- **Current Tunnel**: https://attending-camps-dos-bundle.trycloudflare.com

---

## 🔴 CRITICAL BUG #1: GREETING_PROMPT Scope Error

### Error Log:
```
2026-01-31 13:26:13.580 | ERROR | voice_gateway:websocket_handler:1533 - Error processing message: cannot access local variable 'GREETING_PROMPT' where it is not associated with a value
```

### Problem:
Line 1403-1421: `GREETING_PROMPT` is defined **inside** the `else` block (when `session.LANGUAGE_SELECTION_ENABLED` is False), but if language selection is enabled and an error occurs in the exception handler (line 1533), it tries to reference a variable that doesn't exist in that scope.

### Code Location:
```python
# Line 1388-1403 (LANGUAGE SELECTION PATH)
if session.LANGUAGE_SELECTION_ENABLED:
    logger.info("🗣️ Requesting language selection")
    prompt = "Hello. Do you prefer English, Hindi, or Marathi?"
    # ... TTS code ...
    session.mark_ai_turn_complete()
    session.reset_for_listening()
else:
    # STANDARD GREETING FLOW
    # Line 1405: GREETING_PROMPT defined HERE (inside else block)
    GREETING_PROMPT = """You are making an OUTBOUND sales call..."""
    # ... rest of greeting logic ...
```

### Fix Needed:
Move `GREETING_PROMPT` definition outside the conditional block OR remove it from error context.

---

## 🔴 CRITICAL BUG #2: STT Never Triggers - User Speech Not Transcribed

### Symptoms:
- User spoke for **10 seconds** (buffer grew from 8KB → 80KB)
- VAD detected speech correctly (`Speech: True` in logs)
- **STT was NEVER called** - no transcription happened
- Call ended with buffered audio lost

### Log Evidence:
```
2026-01-31 13:26:17.722 | INFO | Speech START detected - state: USER_SPEAKING
2026-01-31 13:26:18.707 | INFO | State: user_speaking | Buffer: 8000B | Speech: True
2026-01-31 13:26:23.623 | INFO | State: user_speaking | Buffer: 16000B | Speech: True
2026-01-31 13:26:25.466 | INFO | State: user_speaking | Buffer: 24000B | Speech: True
... (continues to 80000B)
2026-01-31 13:26:41.441 | INFO | Stream stopped: MZ7ab877c81bff781bd64b7a585da00513
2026-01-31 13:26:41.442 | INFO | WebSocket closed
```

**Notice**: No "Speech END detected" log, no STT call, no transcription.

### Root Cause:

#### VAD State Machine Logic (Lines 545-595):
```python
def update_vad_state(self, is_speech: bool):
    # ...
    if is_speech:
        self.consecutive_speech_frames += 1
        self.consecutive_silence_frames = 0
        # Triggers speech_start after 200ms
    else:
        self.consecutive_silence_frames += 1
        # ⚠️ REQUIRES 250ms (8.3 frames) OF CONTINUOUS SILENCE
        if self.consecutive_silence_frames >= self.SPEECH_END_FRAMES:
            return "speech_end"
```

#### Current Thresholds (Lines 277-283):
```python
SPEECH_START_MS = 200      # 200ms to trigger speech start
SPEECH_END_MS = 250        # ⚠️ 250ms SILENCE required to end speech
MIN_AUDIO_DURATION_MS = 350
MIN_STT_DURATION_MS = 450
```

#### WebSocket Handler (Lines 1507-1513):
```python
elif vad_event == "speech_end" and session.state == ConversationState.USER_SPEAKING:
    # ⚠️ THIS NEVER FIRES if user doesn't pause for 250ms
    audio_duration = len(session.audio_buffer) / 8000
    if session.has_sufficient_audio():
        await process_user_speech_fast(session, websocket, stt, llm, tts, db)
```

### Why It's Broken:
1. User says "English" continuously without pausing
2. VAD detects `Speech: True` continuously
3. `consecutive_silence_frames` never reaches 8.3 frames (250ms)
4. `speech_end` event never fires
5. User hangs up → Stream stops → Buffer lost → No STT call

**This is UNNATURAL** - people don't pause 250ms mid-sentence in normal conversation.

---

## 🔴 CRITICAL BUG #3: Language Selection + Agent Greeting Issue

### Problem:
After language selection (line 1670-1693), the greeting generation uses a **generic prompt** instead of the agent's full context:

```python
# Line 1675-1677 (CURRENT - WRONG)
greeting_prompt = f"User has just selected {detected_lang}. Generate a short, polite opening line in {detected_lang}."
messages = [{"role": "user", "content": greeting_prompt}]
response_text = await llm.generate_response(messages=messages, system_prompt=lang_instruction[detected_lang], max_tokens=60)
```

This results in **"How can I assist you?"** instead of **"Hi, I'm Nihal from RelayX Sales..."**

### Already Fixed (but verify):
Lines 1673-1692 should now have the GREETING_PROMPT with full agent context included.

---

## 🛠️ THREE CRITICAL FIXES NEEDED

### Fix #1: GREETING_PROMPT Scope (5 minutes)

**Option A** - Move outside conditional:
```python
# Line ~1385 (BEFORE the if statement)
GREETING_PROMPT = """You are making an OUTBOUND sales call. Generate your opening line.

CRITICAL RULES:
- Output ONLY the exact words you will speak - nothing else
- NO quotes, NO meta-commentary like "Here's my opening line:"
- Keep it to 2 sentences MAX (this is a phone call)
- Sound natural and confident, not robotic
- Use contractions: "I'm" not "I am", "you're" not "you are"

STRUCTURE:
1. Brief introduction (name + company)
2. Polite ask if they have a moment

VOICE FORMATTING:
- Write times as words: "twelve PM" not "12:00"
- Write "twenty four seven" not "24/7"
- Numbers as words for pronunciation"""

# Then use it in both paths
if session.LANGUAGE_SELECTION_ENABLED:
    # ... language selection code ...
else:
    # Use GREETING_PROMPT here
```

---

### Fix #2: Force-Process STT After 5 Seconds (10 minutes)

Add timeout check in WebSocket handler (around line 1470):

```python
# After line 1470 (in the event == "media" section)
# ==================== FORCE PROCESS TIMEOUT ====================
if session.state == ConversationState.USER_SPEAKING:
    speaking_duration = (datetime.now() - session.user_speaking_start_time).total_seconds()
    buffer_duration = len(session.audio_buffer) / TWILIO_SAMPLE_RATE
    
    # Force process if user speaking > 5s without natural pause
    if speaking_duration > 5.0 and buffer_duration > 1.0:
        logger.warning(f"⏱️ Force processing: {speaking_duration:.1f}s speaking, {buffer_duration:.1f}s buffered - no pause detected")
        await process_user_speech_fast(session, websocket, stt, llm, tts, db)
        continue
```

---

### Fix #3: Reduce SPEECH_END_MS Threshold (2 minutes)

Change line 278:
```python
# CURRENT (TOO LONG)
SPEECH_END_MS = 250        # 250ms silence required

# CHANGE TO (MORE NATURAL)
SPEECH_END_MS = 180        # 180ms silence required (6 frames * 30ms)
```

Also update line 279:
```python
# Update derived value
SPEECH_END_FRAMES = SPEECH_END_MS // VAD_FRAME_DURATION_MS  # Will be 6 frames
```

---

## 📊 OPTIONAL SIMPLIFICATIONS (Later)

### Current Complexity Issues:
- **18+ state variables** in CallSession class
- **14 timing thresholds** (can reduce to 6-7)
- **3-layer state machine** (Conversation + VAD + Protection)
- **Multiple overlapping protections**:
  - Echo window (350ms)
  - Noise cooldown (150ms)
  - LLM in-flight block
  - Grace period (300ms)
  - First utterance special case

### Detailed Complexity Analysis:

#### CallSession Class State Variables (18+):
```python
- state (LISTENING/USER_SPEAKING/AI_SPEAKING)
- audio_buffer
- consecutive_speech_frames
- consecutive_silence_frames  
- speech_start_time
- tts_end_time (echo protection)
- noise_detected_time
- llm_in_flight (prevents VAD)
- user_speaking_start_time (timeout detection)
- interrupt_grace_start_time
- interrupt_speech_frames
- last_ai_response
- language_verified
- selected_language
- resolved_system_prompt
- agent_config
- call_id
- stream_sid
```

#### All Timing Thresholds (14):
```python
SPEECH_START_MS = 200
SPEECH_END_MS = 250
MIN_AUDIO_DURATION_MS = 350
MIN_STT_DURATION_MS = 450
DISCARD_FIRST_IF_SHORT_MS = 300
ECHO_IGNORE_MS = 350
POST_NOISE_COOLDOWN_MS = 150
VAD_FRAME_DURATION_MS = 30
USER_SPEAKING_TIMEOUT_MS = 25000
INTERRUPT_GRACE_PERIOD_MS = 300
INTERRUPT_MIN_DURATION_MS = 400
MIN_SPEECH_ENERGY = 30
SPEECH_START_FRAMES = 6-7
SPEECH_END_FRAMES = 8-9
```

### Simplification Suggestions:
1. **Merge duplicate variables**:
   - `speech_start_time` + `user_speaking_start_time` → single variable
   
2. **Remove redundant protections**:
   - Noise cooldown (redundant with echo window)
   - Grace period (redundant with speech_start threshold)
   - First utterance special case (causes confusion)

3. **Consolidate thresholds**:
   - MIN_AUDIO_DURATION_MS (350ms) + MIN_STT_DURATION_MS (450ms) → single value
   - Use same base unit (e.g., all in ms, calculate frames dynamically)

4. **Simplify state machine**:
   - Current: ConversationState + VAD frames + Protection flags
   - Target: ConversationState + VAD frames only
   - Protection can be simple boolean checks, not separate state layers

5. **Remove non-critical tracking**:
   - `last_ai_response` (for repetition detection - can be simpler)
   - Multiple interrupt detection variables (consolidate to 2-3)

---

## 📂 FILE LOCATIONS

- **Main file**: `d:\spec-driven-projects\RelayX\voice_gateway\voice_gateway.py`
- **Sarvam config**: `d:\spec-driven-projects\RelayX\shared\sarvam_client.py`
- **Backend routes**: `d:\spec-driven-projects\RelayX\backend\call_routes.py`
- **Database client**: `d:\spec-driven-projects\RelayX\shared\database.py`
- **Docker compose**: `d:\spec-driven-projects\RelayX\docker-compose.yml`

---

## 🎯 PRIORITY ORDER

### CRITICAL (Must Fix Now):
1. **HIGH**: Fix #2 (Force STT timeout) - Users can't communicate without this
2. **HIGH**: Fix #3 (Reduce SPEECH_END_MS) - Makes conversation more natural
3. **MEDIUM**: Fix #1 (GREETING_PROMPT scope) - Crashes on errors

### IMPORTANT (Next Session):
4. Add buffer overflow protection (max 30 seconds)
5. Add explicit hang-up detection handler
6. Test multilingual greetings (Hindi/Marathi)

### OPTIMIZATION (When Stable):
7. Simplify state machine
8. Consolidate timing thresholds
9. Remove redundant protections
10. Reduce CallSession variables

---

## ✅ WHAT'S ALREADY WORKING

- ✅ TTS (Manisha voice, bulbul:v2)
- ✅ Cloudflare tunnel connectivity
- ✅ VAD speech detection (WebRTC)
- ✅ Database/Supabase connection
- ✅ Twilio integration
- ✅ Call initiation
- ✅ Audio streaming (mulaw → PCM conversion)
- ✅ Language selection UI (English/Hindi/Marathi prompt)

---

## 🧪 TEST PLAN AFTER FIXES

### Test Case 1: Short Response
1. Call rings
2. User answers
3. User says "English" (1 second)
4. **Expected**: STT triggers, agent responds with full greeting

### Test Case 2: Long Continuous Speech
1. Call rings
2. User answers
3. User talks for 8+ seconds without pausing
4. **Expected**: Force-process kicks in at 5s, STT processes partial buffer

### Test Case 3: Natural Pauses
1. Call rings
2. User answers
3. User says "I want... (pause 200ms)... English"
4. **Expected**: STT triggers after 180ms pause

### Test Case 4: Multiple Languages
1. Test Hindi selection
2. Test Marathi selection
3. **Expected**: Agent greeting uses full context in selected language

---

## 📞 CURRENT KNOWN ISSUES

### Confirmed Bugs:
- ❌ GREETING_PROMPT scope error (crashes)
- ❌ STT never triggers without 250ms pause
- ❌ No fallback for long speech (10s+ without pause)

### Suspected Issues:
- ⚠️ Buffer overflow risk (no max buffer size limit visible)
- ⚠️ Stream close during USER_SPEAKING loses buffered audio
- ⚠️ LLM in-flight blocking might be too aggressive

### Working But Needs Improvement:
- ⏺️ Barge-in detection (works but complex)
- ⏺️ Echo protection (350ms might be too long)
- ⏺️ Energy thresholds (MIN_SPEECH_ENERGY = 30 might be too low)

---

## 🔍 DEBUG COMMANDS

```bash
# Check recent voice gateway logs
docker logs relayx-voice-gateway --tail 200 | grep -E "STT|TTS|Speech|Error"

# Monitor real-time logs
docker logs -f relayx-voice-gateway

# Check specific call logs
docker logs relayx-voice-gateway 2>&1 | grep "dd0a2044-c715-4f7a-91f5-b9ed7a2868e4"

# Restart voice gateway
docker-compose restart voice-gateway

# Check Cloudflare tunnel status
docker logs relayx-cloudflare-tunnel --tail 20
```

---

## 🚀 DEPLOYMENT NOTES

### After implementing fixes:
1. Rebuild voice-gateway container: `docker-compose build voice-gateway`
2. Restart with new code: `docker-compose up -d voice-gateway`
3. Test with multiple call scenarios
4. Monitor logs for 5-10 test calls
5. Verify transcriptions appear in dashboard

### Environment:
- Python 3.11
- WebRTC VAD 2.x
- Sarvam AI API (requires valid key)
- Groq API (llama-3.3-70b-versatile)
- Supabase PostgreSQL

---

**Report Generated**: 2026-01-31  
**Status**: Ready for Implementation  
**Next Action**: Copy to Claude Opus for fixes

