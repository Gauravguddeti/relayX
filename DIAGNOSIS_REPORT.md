# 🔬 DETAILED DIAGNOSIS REPORT: Voice Gateway Latency Issues

**Date:** December 10, 2025  
**System:** RelayX Voice Gateway  
**Call ID Analyzed:** `6beccd86-b9e1-4b69-8d1d-8f4dd720d0f6`

---

## Executive Summary

The system has **two critical issues**: 
1. **AI Echo Contamination** - The system records its own AI voice playback and tries to transcribe it
2. **Deepgram Returning Empty Transcriptions** for valid speech

**Result:** User experiences 9+ second delay after AI greeting before their response is recognized.

---

## Issue #1: AI Echo/TTS Playback Being Captured (CRITICAL)

### Evidence from Logs:
```
11:42:27.454 - Sent AI greeting (2.6s audio)
11:42:30.121 - Buffer collecting: 8000B, Energy: 90.0  ← AI playback being recorded!
11:42:30.124 - Buffer: 16000B, Energy: 66.3
11:42:30.127 - Buffer: 32000B, Energy: 127.0
11:42:31.188 - PROCESSING: 47520 bytes ← This is AI's own voice!
11:42:34.969 - Transcription: [EMPTY] ← Deepgram got garbage
```

### Root Cause:
The `is_speaking` flag turns off **TOO EARLY**. The code does:
```python
await asyncio.sleep(duration + 0.1)  # Wait for audio to play
session.is_speaking = False  # Then allow recording
```

**BUT** there's a timing issue:
- AI greeting is 2.6 seconds
- Code waits `2.6 + 0.1 = 2.7` seconds
- **BUT** Twilio has network latency + audio buffer delay
- Audio is still playing on user's phone while system starts recording
- **Result:** System records its own echo

### Timeline Analysis:

| Time | Event | Issue |
|------|-------|-------|
| 11:42:27.454 | AI sends 2.6s greeting | - |
| 11:42:30.0 | is_speaking=False (2.6s later) | ❌ Too early |
| 11:42:30.121 | Buffer starts collecting | ❌ Recording AI echo! |
| 11:42:31.188 | Process 47520 bytes | ❌ This is echo, not user |
| 11:42:34.969 | Deepgram: Empty | ❌ Can't transcribe echo |

---

## Issue #2: Deepgram Empty Transcriptions

### Evidence:
```
11:42:31.192 - Transcribing with Deepgram: /tmp/tmpanni2qar.wav
11:42:34.969 - Transcription: [EMPTY]  ← 3.8 seconds and nothing!

11:42:34.974 - Transcribing with Deepgram: /tmp/tmpljwxbtwq.wav  
11:42:35.784 - Transcription: [EMPTY]  ← 0.8 seconds, empty again
```

### Possible Causes:
1. **Audio is AI's own voice (echo)** - not human speech
2. **Deepgram parameters mismatch** - We send 16kHz but `nova-2-phonecall` might expect 8kHz
3. **Audio format issue** - WAV header might be incorrect

---

## Issue #3: Response Delay After Greeting

### Timeline for First User Response:

| Step | Timestamp | Duration | Notes |
|------|-----------|----------|-------|
| Greeting sent | 11:42:27.454 | - | 2.6s audio |
| First buffer | 11:42:30.121 | 2.7s after greeting | Should be immediate |
| Process attempt | 11:42:31.188 | 3.7s after greeting | Echo contamination |
| Empty result | 11:42:34.969 | 7.5s after greeting | Wasted 3.8s on Deepgram |
| Second attempt | 11:42:34.972 | - | Another empty |
| Third attempt | 11:42:35.787 | - | Finally gets "Yes" |
| **User "Yes" recognized** | 11:42:36.587 | **9.1s after greeting!** | ❌ Terrible UX |

---

## Issue #4: Baseline Energy Corruption

### Evidence:
```
Energy: 127.0 | Baseline: 127.0 | IsSilence: True
```

### Problem:
- `127` is the mulaw "silence" center value
- When baseline becomes 127, **ALL audio looks like silence**
- This happens because the baseline adapts to the loudest recent value
- The silence detection algorithm is broken

### Code Issue:
```python
# Current (wrong):
self.baseline_energy = min(self.recent_energy)  # Gets corrupted by 127

# Should be:
self.baseline_energy = min(e for e in self.recent_energy if e < 120)  # Ignore peaks
```

---

## Issue #5: Conversation Context Not Preserved

### Evidence:
```
11:42:46.916 - AI: "You mentioned your business makes outbound calls. Roughly how many calls..."
11:42:57.687 - User: "Yeah. We do."  ← Answering previous question
11:42:58.617 - AI: "You mentioned your business makes outbound calls. Roughly how many calls..."  ← REPEATS!
```

### Problem:
- LLM gets confused because conversation history has duplicates
- Or LLM is ignoring user's answer "Yeah. We do."

---

## Latency Breakdown Per Turn

| Component | Time | Target | Status |
|-----------|------|--------|--------|
| Silence detection | 1000ms | 500-700ms | ⚠️ Acceptable |
| Deepgram STT | **2-3.8 seconds** | <500ms | ❌ CRITICAL |
| Groq LLM | 200-600ms | <500ms | ✅ Good |
| Piper TTS | 200-400ms | <300ms | ✅ Good |
| Audio send | instant | instant | ✅ Good |
| **Total per turn** | **4-6 seconds** | <2 seconds | ❌ CRITICAL |

---

## Root Causes Summary

| Priority | Issue | Impact |
|----------|-------|--------|
| 🔴 P0 | AI echo being recorded | Wastes 3-4 seconds on false positives |
| 🔴 P0 | `is_speaking` buffer too short | Causes echo recording |
| 🔴 P0 | Deepgram taking 2-4 seconds | Should be <500ms |
| 🟡 P1 | Baseline energy corrupted to 127 | Bad silence detection |
| 🟡 P1 | Empty transcriptions from Deepgram | Wastes API calls + time |
| 🟠 P2 | LLM repeating responses | Context issue |

---

## Recommended Fixes for Senior Review

### Fix 1: Increase `is_speaking` Buffer (Quick Fix)
```python
# Current:
await asyncio.sleep(duration + 0.1)

# Recommended:
await asyncio.sleep(duration + 0.5)  # Add 500ms buffer for network latency
```

**Location:** `voice_gateway.py` lines ~538 and ~786

### Fix 2: Fix Deepgram Parameters
```python
# Current sends 16kHz but nova-2-phonecall expects 8kHz telephony
# Option A: Keep 8kHz native Twilio audio (don't upsample)
# Option B: Use nova-2 (general) instead of nova-2-phonecall
# Option C: Remove sample_rate param and let Deepgram auto-detect
```

**Location:** `shared/stt_client.py` lines ~97-107

### Fix 3: Fix Baseline Energy Algorithm
```python
# Filter out 127 peaks:
valid_energies = [e for e in self.recent_energy if e < 120]
if valid_energies:
    self.baseline_energy = min(valid_energies)
```

**Location:** `voice_gateway.py` in `detect_silence()` method

### Fix 4: Consider Switching to Groq Whisper
- Deepgram taking 2-4 seconds is abnormal (should be <500ms)
- Groq Whisper was taking ~1.4 seconds which is faster
- May be a Deepgram API issue or parameter mismatch

**Location:** `.env` - change `STT_PROVIDER=groq`

---

## Questions for Senior

1. Should we increase the post-speech buffer from 0.1s to 0.5s?
2. Is the Deepgram `nova-2-phonecall` model correct for 16kHz upsampled audio?
3. Should we switch back to Groq Whisper which was faster?
4. Should we implement proper echo cancellation in the audio pipeline?
5. Is the baseline energy algorithm approach correct or should we use a different VAD?

---

## System Configuration at Time of Issue

```env
STT_PROVIDER=deepgram
USE_CLOUD_STT=true
SILENCE_THRESHOLD_MS=700
MIN_AUDIO_DURATION_MS=400
SPEECH_ENERGY_THRESHOLD=20
MIN_SPEECH_ENERGY=3
```

---

## Raw Log Timestamps (for reference)

```
Greeting Generation:
- 11:42:26.527 - LLM request
- 11:42:27.132 - LLM response (605ms)
- 11:42:27.284 - TTS start
- 11:42:27.449 - TTS done (165ms)
- 11:42:27.454 - Audio sent to Twilio

First User Response (after greeting):
- 11:42:30.121 - Buffer starts (echo!)
- 11:42:31.188 - Process 47520 bytes
- 11:42:31.192 - Deepgram request #1
- 11:42:34.969 - Deepgram empty (3.8s!)
- 11:42:34.974 - Deepgram request #2
- 11:42:35.784 - Deepgram empty (0.8s)
- 11:42:35.789 - Deepgram request #3
- 11:42:36.587 - Finally got "Yes" (0.8s)
- 11:42:37.008 - LLM request
- 11:42:37.239 - LLM response (231ms)
- 11:42:37.343 - TTS start
- 11:42:37.571 - TTS done (228ms)
- 11:42:37.579 - Audio sent

Total time from greeting end to AI response: ~10 seconds (should be <3s)
```
