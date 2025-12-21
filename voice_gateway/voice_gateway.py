"""
Voice Gateway for RelayX AI Caller
Handles Twilio Media Streams via WebSocket
Real-time pipeline: Audio → STT → LLM → TTS → Audio

ARCHITECTURE (Vapi-style, optimized for <4s response):
- 3-state machine: LISTENING, USER_SPEAKING, AI_SPEAKING
- VAD edge-trigger: 240ms speech start, 300ms silence end
- TRUE barge-in: Interrupt AI mid-speech
- Intent pre-classifier: Handle casual responses before LLM
- NO adaptive silence, NO post-TTS sleep, NO cooldowns
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from enum import Enum
import asyncio
import base64
import json
import sys
import os
from loguru import logger
from datetime import datetime
import audioop
import tempfile
import webrtcvad
import numpy as np
import io
import wave

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.database import get_db, SupabaseDB
from shared.llm_client import get_llm_client, LLMClient
from shared.stt_client import get_stt_client, STTClient
from shared.tts_client import get_tts_client, TTSClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logger
logger.add("logs/voice_gateway.log", rotation="1 day", retention="7 days", level="INFO")

# Initialize FastAPI
app = FastAPI(
    title="RelayX Voice Gateway",
    description="Twilio Media Stream handler for AI voice calls",
    version="2.0.0"  # Major rewrite with barge-in support
)

# Add CORS middleware to allow dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Audio settings for Twilio
TWILIO_SAMPLE_RATE = 8000  # Twilio uses 8kHz
TWILIO_AUDIO_FORMAT = "mulaw"  # μ-law encoding

# WebRTC VAD (lightweight, <1ms per frame)
# Mode: 0=Quality, 1=Low Bitrate, 2=Aggressive, 3=Very Aggressive
# Using mode=2 (Aggressive) to reduce false positives from noise/echo
vad = webrtcvad.Vad(mode=2)

# Call sessions storage
active_sessions = {}


# ==================== SIMPLIFIED 3-STATE MACHINE ====================
class ConversationState(Enum):
    """Simple 3-state conversation model (like Vapi.ai)"""
    LISTENING = "listening"        # Waiting for user to speak
    USER_SPEAKING = "user_speaking"  # User is actively speaking
    AI_SPEAKING = "ai_speaking"    # AI is outputting audio


# ==================== INTENT PRE-CLASSIFIER (Before LLM) ====================
# These patterns are handled WITHOUT calling LLM - saves 200-500ms
AFFIRM_PATTERNS = ["yeah", "yes", "yep", "yup", "haan", "ok", "okay", "sure", "exactly", "right", "correct", "absolutely", "definitely", "of course", "alright", "fine", "go ahead", "please", "i'm down", "im down", "down for that", "down for it", "sounds good", "let's do it", "lets do it", "i'm in", "im in", "count me in", "deal", "perfect", "great", "awesome", "cool", "bet"]
ACK_PATTERNS = ["hmm", "uh huh", "uh-huh", "huh", "mm", "mhm", "mmhmm", "i see", "got it"]
OPEN_PATTERNS = ["what's up", "whats up", "what is this", "who is this", "who's calling", "whos calling", "what do you want", "yes what", "yeah what", "hello", "hi"]
NEGATIVE_PATTERNS = ["no", "nope", "nah", "not interested", "no thanks", "no thank you", "busy", "not now", "call later", "don't call", "wrong number"]
GOODBYE_PATTERNS = ["bye", "goodbye", "see you", "thanks bye", "thank you bye", "gotta go", "have to go", "talk later", "bye-bye", "bye bye"]

# NOISE WORDS - Single words that are likely STT errors from echo/noise
# These should NEVER create a user turn or reach LLM context
NOISE_WORDS = [
    # Common STT noise artifacts
    "you", "the", "a", "i", "um", "uh", "ah", "oh", "er", "hmm", "hm",
    # Partial words / fragments
    "it", "is", "to", "in", "on", "an", "and", "or", "so", "be",
    # Very short non-meaningful
    "k", "m", "n", "s", "t", "y",
]

# ECHO PHRASES - Multi-word patterns that match AI speech (potential echo)
# If detected within 2 seconds of AI speaking, treat as echo
ECHO_PHRASE_PATTERNS = [
    "thank you", "thanks", "got a moment", "this is", "from relay",
    "no problem", "you're welcome", "have a great", "you"
]


def classify_intent(text: str, time_since_ai_spoke_ms: float = 9999) -> tuple[str, str | None]:
    """
    Fast intent classification for short utterances (runs in <1ms)
    Returns: (intent, scripted_response or None)
    
    Intents:
    - "noise" → Likely STT error from echo/noise, ignore
    - "echo" → Detected AI echo pattern, ignore
    - "affirm" → User said yes/okay, continue with pitch
    - "ack" → User acknowledged, continue naturally  
    - "open" → User wants context, explain purpose
    - "negative" → User declined, offer callback
    - "goodbye" → User ending call
    - "llm" → Need full LLM processing
    
    Args:
        text: The transcribed text
        time_since_ai_spoke_ms: Milliseconds since AI finished speaking (for echo detection)
    """
    text_lower = text.lower().strip()
    words = text_lower.split()
    
    # ==================== NOISE DETECTION ====================
    # Single word that's likely STT noise - SKIP entirely
    # "you" is ALWAYS noise as single word (common phone echo artifact)
    if len(words) == 1 and (text_lower in NOISE_WORDS or text_lower == "you"):
        return ("noise", None)  # Will be skipped
    
    # Very short gibberish (1-2 chars) - likely noise
    if len(text_lower) <= 2:
        return ("noise", None)
    
    # ==================== ECHO DETECTION ====================
    # If AI just spoke and this matches AI speech patterns, it's likely echo
    if time_since_ai_spoke_ms < 2000:  # Within 2 seconds of AI speaking (increased from 1.5s)
        for pattern in ECHO_PHRASE_PATTERNS:
            if pattern in text_lower:
                return ("echo", None)  # Detected as AI echo
    
    # Very short utterances - classify directly
    if len(words) <= 5:
        # Check patterns (order matters - more specific first)
        for pattern in GOODBYE_PATTERNS:
            if pattern in text_lower:
                return ("goodbye", "Thanks for your time! Goodbye!")
        
        for pattern in NEGATIVE_PATTERNS:
            if pattern in text_lower:
                return ("negative", None)  # Let LLM handle graceful decline
        
        for pattern in OPEN_PATTERNS:
            if text_lower.startswith(pattern) or pattern in text_lower:
                return ("open", None)  # Let LLM explain context
        
        for pattern in AFFIRM_PATTERNS:
            if pattern in text_lower or text_lower == pattern:
                return ("affirm", None)  # Continue with pitch
        
        for pattern in ACK_PATTERNS:
            if pattern in text_lower:
                return ("ack", None)  # Continue naturally
    
    # Longer utterances need LLM
    return ("llm", None)


class CallSession:
    """
    Manages state for an active call
    
    SIMPLIFIED STATE MACHINE (Vapi-style):
    - Only 3 states: LISTENING, USER_SPEAKING, AI_SPEAKING
    - VAD edge-trigger with HYSTERESIS: 200ms speech start, 240ms silence end
    - TRUE barge-in: User can interrupt AI mid-speech
    - ECHO PROTECTION: 300ms ignore window after TTS completes
    - ENERGY SANITY: Filter out non-speech noise
    - POST-NOISE COOLDOWN: Brief delay after noise detection
    """
    
    # VAD HYSTERESIS TIMINGS (prevents false triggers)
    SPEECH_START_MS = 200      # VAD speech for 200ms → USER_SPEAKING (was 120ms)
    SPEECH_END_MS = 240        # VAD silence for 240ms → End utterance (was 300ms)
    
    # AUDIO DURATION THRESHOLDS (critical for filtering noise)
    MIN_AUDIO_DURATION_MS = 400   # Minimum 400ms to even consider processing (was 200ms)
    MIN_STT_DURATION_MS = 500     # Minimum 500ms before sending to STT (prevent short noise)
    DISCARD_FIRST_IF_SHORT_MS = 350  # Discard first utterance after AI if < 350ms
    
    # ENERGY THRESHOLDS (mulaw: 127 is zero-crossing/silence center)
    # Only minimum energy check - mobile AGC produces high energy that is valid speech
    MIN_SPEECH_ENERGY = 30     # Minimum energy to consider as possible speech (lowered for mobile)
    
    # PROTECTION WINDOWS
    ECHO_IGNORE_MS = 400       # Ignore VAD for 400ms after TTS completes (was 300ms)
    POST_NOISE_COOLDOWN_MS = 200  # Cooldown after noise detection before arming again
    
    # WebRTC VAD frame settings
    VAD_FRAME_DURATION_MS = 30  # 30ms frames for accuracy
    VAD_FRAME_BYTES = 240       # 30ms at 8kHz = 240 bytes
    
    # Frame counts for hysteresis (at 30ms per frame)
    SPEECH_START_FRAMES = 8    # 8 frames × 30ms = 240ms of speech to trigger (was 7)
    SPEECH_END_FRAMES = 10     # 10 frames × 30ms = 300ms of silence to end (was 8)
    
    def __init__(self, call_id: str, agent_id: str, stream_sid: str):
        self.call_id = call_id
        self.agent_id = agent_id
        self.stream_sid = stream_sid
        self.audio_buffer = bytearray()
        self.vad_buffer = bytearray()  # Buffer for VAD frame alignment
        
        # SIMPLIFIED STATE (3 states only)
        self.state = ConversationState.LISTENING
        
        # VAD edge detection with hysteresis
        self.speech_start_time = None
        self.silence_start_time = None
        self.consecutive_speech_frames = 0
        self.consecutive_silence_frames = 0
        
        # ECHO PROTECTION: Track when TTS finished
        self.tts_end_time = None  # Set when TTS completes
        
        # LLM IN-FLIGHT PROTECTION
        self.llm_in_flight = False  # True while waiting for LLM response
        
        # POST-NOISE COOLDOWN
        self.noise_detected_time = None  # Set when noise is detected
        
        # TURN TRACKING (for first-utterance-after-AI logic)
        self.ai_turn_count = 0  # Increments each time AI speaks
        self.last_ai_turn_end = None  # When AI last finished speaking
        self.utterances_since_ai = 0  # Count of user utterances since AI spoke
        
        # Conversation context
        self.conversation_history = []
        self.agent_config = None
        self.last_user_text = None
        self.last_user_text_time = None
        self.last_ai_response = None  # Track last AI response to prevent repetition
        self.created_at = datetime.now()
        
        # Barge-in support
        self.ai_audio_task = None  # Track ongoing AI audio for interruption
        self.interrupted = False    # Flag to stop AI audio
        
        logger.info(f"CallSession created: {call_id} | StreamSID: {stream_sid}")
    
    def add_audio_chunk(self, audio_data: bytes):
        """Add audio chunk to buffer"""
        self.audio_buffer.extend(audio_data)
    
    def get_and_clear_buffer(self) -> bytes:
        """Get audio buffer and clear it"""
        data = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        return data
    
    def has_sufficient_audio(self) -> bool:
        """Check if buffer has enough audio"""
        min_bytes = (TWILIO_SAMPLE_RATE * self.MIN_AUDIO_DURATION_MS) // 1000
        return len(self.audio_buffer) >= min_bytes
    
    def is_in_echo_window(self) -> bool:
        """Check if we're still in the echo ignore window after TTS"""
        if self.tts_end_time is None:
            return False
        elapsed_ms = (datetime.now() - self.tts_end_time).total_seconds() * 1000
        return elapsed_ms < self.ECHO_IGNORE_MS
    
    def is_in_noise_cooldown(self) -> bool:
        """Check if we're still in cooldown after noise detection"""
        if self.noise_detected_time is None:
            return False
        elapsed_ms = (datetime.now() - self.noise_detected_time).total_seconds() * 1000
        return elapsed_ms < self.POST_NOISE_COOLDOWN_MS
    
    def mark_noise_detected(self):
        """Mark that noise was detected, starting cooldown"""
        self.noise_detected_time = datetime.now()
    
    def is_first_utterance_after_ai(self) -> bool:
        """Check if this is the first utterance after AI finished speaking"""
        return self.utterances_since_ai == 0 and self.last_ai_turn_end is not None
    
    def mark_ai_turn_complete(self):
        """Mark that AI finished speaking"""
        self.ai_turn_count += 1
        self.last_ai_turn_end = datetime.now()
        self.utterances_since_ai = 0
    
    def mark_user_utterance(self):
        """Mark that user made a real utterance (not noise)"""
        self.utterances_since_ai += 1
    
    def detect_speech_vad(self, audio_data: bytes) -> bool:
        """
        WebRTC VAD speech detection with SANITY CHECKS
        
        Returns True ONLY if:
        1. Not in echo ignore window (300ms after TTS)
        2. Energy is in valid speech range (not noise/clipping)
        3. WebRTC VAD confirms speech OR energy strongly suggests speech
        """
        global vad
        
        if len(audio_data) == 0:
            return False
        
        # Calculate energy (mulaw: 127 is silence, deviation indicates sound)
        energy = sum(abs(b - 127) for b in audio_data) / len(audio_data)
        
        # ==================== SANITY CHECK 1: Echo Window ====================
        if self.is_in_echo_window():
            # Still in echo ignore period - don't detect any speech
            return False
        
        # ==================== SANITY CHECK 2: Minimum Energy ====================
        # Energy < MIN_SPEECH_ENERGY: Too quiet, likely silence
        # NOTE: We removed MAX_NOISE_ENERGY check because mobile phones with AGC
        # produce high-energy audio (often 127) that is valid speech, not noise.
        # WebRTC VAD handles actual noise detection better than energy thresholds.
        if energy < self.MIN_SPEECH_ENERGY:
            return False  # Too quiet to be speech
        
        # Add to VAD buffer for frame alignment
        self.vad_buffer.extend(audio_data)
        
        # WebRTC VAD needs exact frame sizes
        if len(self.vad_buffer) < self.VAD_FRAME_BYTES:
            # Not enough for WebRTC VAD, use energy-only detection
            # Only trigger if energy is in strong speech range
            return 50 < energy < 100
        
        try:
            speech_frame_count = 0
            total_frames = 0
            
            # Process all complete frames
            while len(self.vad_buffer) >= self.VAD_FRAME_BYTES:
                frame_data = bytes(self.vad_buffer[:self.VAD_FRAME_BYTES])
                self.vad_buffer = self.vad_buffer[self.VAD_FRAME_BYTES:]
                
                # Convert mulaw to PCM for VAD
                pcm_data = audioop.ulaw2lin(frame_data, 2)
                total_frames += 1
                
                if vad.is_speech(pcm_data, TWILIO_SAMPLE_RATE):
                    speech_frame_count += 1
            
            # Require majority of frames to be speech (reduces false positives)
            is_speech = speech_frame_count > (total_frames / 2) if total_frames > 0 else False
            
            # Only trust energy fallback for STRONG speech indicators
            if not is_speech and 55 < energy < 90:
                # Energy suggests possible speech but VAD disagrees
                # Trust VAD more than energy (VAD is ML-based)
                pass  # Don't override VAD decision
            
            return is_speech
            
        except Exception as e:
            logger.warning(f"VAD error: {e}")
            self.vad_buffer.clear()
            # Fallback: stricter energy-based detection
            return 55 < energy < 90
    
    def update_vad_state(self, is_speech: bool) -> str | None:
        """
        VAD edge-trigger state machine with HYSTERESIS
        Returns: "speech_start", "speech_end", or None
        
        HYSTERESIS prevents false triggers:
        - Speech start: 8 consecutive speech frames (~240ms)
        - Speech end: 10 consecutive silence frames (~300ms)
        
        PROTECTION:
        - Ignores VAD during echo window (400ms after TTS)
        - Ignores VAD while LLM is in-flight
        - Ignores VAD during post-noise cooldown (200ms)
        """
        # ==================== PROTECTION CHECKS ====================
        if self.is_in_echo_window():
            # Still in echo protection window - ignore all VAD
            self.consecutive_speech_frames = 0
            self.consecutive_silence_frames = 0
            return None
        
        if self.llm_in_flight:
            # LLM is processing - ignore VAD to prevent false triggers
            return None
        
        if self.is_in_noise_cooldown():
            # Just detected noise - brief cooldown before arming again
            self.consecutive_speech_frames = 0
            return None
        
        # ==================== STATE MACHINE ====================
        if is_speech:
            self.consecutive_speech_frames += 1
            self.consecutive_silence_frames = 0
            
            # Check for speech start trigger (only in LISTENING state)
            if self.consecutive_speech_frames >= self.SPEECH_START_FRAMES and self.state == ConversationState.LISTENING:
                logger.info(f"🎙️ VAD: Speech detected for {self.consecutive_speech_frames} frames ({self.consecutive_speech_frames * 30}ms) - triggering speech_start")
                return "speech_start"
        else:
            self.consecutive_silence_frames += 1
            # DON'T reset speech frames immediately - allow gaps in speech
            # Only reset after significant silence (4 frames = 120ms)
            if self.consecutive_silence_frames >= 4:
                self.consecutive_speech_frames = 0
            
            # Check for speech end trigger (only during USER_SPEAKING)
            if self.state == ConversationState.USER_SPEAKING:
                if self.consecutive_silence_frames >= self.SPEECH_END_FRAMES:
                    logger.info(f"🔇 VAD: Silence for {self.consecutive_silence_frames} frames ({self.consecutive_silence_frames * 30}ms) - triggering speech_end")
                    return "speech_end"
        
        return None
    
    def reset_for_listening(self):
        """Reset state for listening mode - DOES NOT clear echo window"""
        self.speech_start_time = None
        self.silence_start_time = None
        self.consecutive_speech_frames = 0
        self.consecutive_silence_frames = 0
        self.vad_buffer.clear()
        self.llm_in_flight = False
        self.state = ConversationState.LISTENING
        # NOTE: tts_end_time is NOT cleared - echo window must expire naturally
    
    def interrupt_ai(self):
        """Signal to interrupt ongoing AI audio"""
        self.interrupted = True
        logger.info("🛑 BARGE-IN: User interrupted AI speech")
# ==================== TWIML ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "RelayX Voice Gateway",
        "status": "running",
        "active_calls": len(active_sessions)
    }


@app.get("/info")
async def get_info():
    """Get gateway info including ngrok URL"""
    effective_url = os.getenv("VOICE_GATEWAY_URL") or ngrok_public_url or "not configured"
    return {
        "service": "RelayX Voice Gateway",
        "status": "running",
        "active_calls": len(active_sessions),
        "ngrok_url": effective_url,
        "port": int(os.getenv("VOICE_GATEWAY_PORT", 8001))
    }


@app.post("/twiml/{call_id}")
async def twiml_handler(call_id: str, request: Request):
    """
    Generate TwiML with Media Streams for real-time bidirectional audio
    This enables sub-1-second response times and natural interruptions
    """
    try:
        logger.info(f"TwiML requested for call: {call_id}")
        
        # Get call details from database
        db = get_db()
        call = await db.get_call(call_id)
        
        if not call:
            logger.error(f"Call {call_id} not found in database")
            return Response(content="<Response><Say>Call not found</Say></Response>", media_type="application/xml")
        
        # Update call status
        await db.update_call(call_id, status="in-progress", started_at=datetime.now())
        logger.info(f"Call {call_id} status updated to in-progress")
        
        # Get WebSocket URL (use VOICE_GATEWAY_WS_URL or convert HTTP to WSS)
        ws_url = os.getenv("VOICE_GATEWAY_WS_URL")
        if not ws_url:
            # Try to build from VOICE_GATEWAY_URL
            base_url = os.getenv("VOICE_GATEWAY_URL") or ngrok_public_url
            if base_url:
                # Convert https:// to wss://
                ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        
        if not ws_url or ws_url.startswith("wss://your-"):
            logger.error("WebSocket URL not configured properly")
            return Response(
                content="<Response><Say>WebSocket configuration error</Say></Response>",
                media_type="application/xml"
            )
        
        # Generate TwiML with Media Streams for real-time audio
        ws_endpoint = f"{ws_url}/ws/{call_id}"
        
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{ws_endpoint}">
            <Parameter name="call_id" value="{call_id}"/>
        </Stream>
    </Connect>
</Response>"""
        
        logger.info(f"TwiML with Media Streams generated for {call_id} -> {ws_endpoint}")
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error generating TwiML for {call_id}: {e}", exc_info=True)
        return Response(
            content="<Response><Say>Sorry, there was an error</Say></Response>",
            media_type="application/xml"
        )


async def generate_call_analysis(call_id: str, db):
    """Generate AI-powered call analysis summary"""
    try:
        # Get transcripts
        transcripts = await db.get_transcripts(call_id)
        
        if not transcripts or len(transcripts) < 2:
            logger.info(f"Not enough transcript data for analysis: {call_id}")
            return
        
        # Build conversation text
        conversation_text = "\n".join([
            f"{t['speaker'].upper()}: {t['text']}" 
            for t in transcripts
        ])
        
        # Use LLM to analyze the call
        llm = get_llm_client()
        
        analysis_prompt = f"""Analyze this phone call conversation. Read the ENTIRE conversation carefully and provide accurate analysis.

CONVERSATION:
{conversation_text}

ANALYSIS INSTRUCTIONS:

1. SUMMARY: Write 2-3 sentences describing what happened in the call

2. KEY POINTS: List 2-4 main topics or important details discussed

3. USER SENTIMENT: This is CRITICAL - analyze the user's actual emotional state throughout the conversation.
   
   Look for these indicators:
   - POSITIVE: Words like "great", "perfect", "excellent", "love it", "sounds good", "thank you", enthusiasm, eagerness
   - NEGATIVE: Words like "frustrated", "confused", "problem", "issue", "disappointed", "not happy", complaints, resistance
   - NEUTRAL: Purely factual responses, business-like tone, no emotional indicators either way
   
   Pay attention to:
   - How they started vs how they ended (did sentiment improve or worsen?)
   - Their willingness to engage (eager questions vs reluctant answers?)
   - Their word choices (positive/negative language)
   - Overall tone (friendly vs cold, cooperative vs resistant)
   
   DO NOT default to neutral - only choose neutral if there are truly no emotional indicators.
   
   Choose the sentiment that BEST matches the conversation:
   - very_positive: User is enthusiastic, excited, multiple positive words, highly engaged
   - positive: User is friendly, cooperative, satisfied, helpful
   - neutral: User is purely factual/business-like with NO emotional indicators either way
   - negative: User shows frustration, annoyance, dissatisfaction, or reluctance
   - very_negative: User is angry, hostile, very upset, or openly hostile

4. OUTCOME: Based on the conversation result:
   - interested: User wants to proceed/book/buy
   - not_interested: User declined or not interested
   - call_later: User wants to be contacted later
   - needs_more_info: User needs more information before deciding
   - wrong_number: Wrong person or misunderstanding
   - other: Doesn't fit above categories

5. NEXT ACTION: Specific recommended follow-up step

Return ONLY valid JSON (no other text):
{{
  "summary": "",
  "key_points": [],
  "user_sentiment": "",
  "outcome": "",
  "next_action": ""
}}"""
        
        messages = [{"role": "user", "content": analysis_prompt}]
        response = await llm.generate_response(
            messages=messages,
            system_prompt="You are a call analysis assistant. Analyze conversations and provide structured insights.",
            temperature=0.3,
            max_tokens=300
        )
        
        # Parse JSON response
        import json
        try:
            analysis_data = json.loads(response)
        except:
            # Fallback if LLM doesn't return valid JSON
            logger.warning(f"Failed to parse LLM analysis as JSON for {call_id}")
            analysis_data = {
                "summary": response[:200],
                "key_points": ["Analysis failed to parse"],
                "user_sentiment": "neutral",
                "outcome": "other",
                "next_action": "Review transcript manually"
            }
        
        # Save analysis
        await db.save_call_analysis(
            call_id=call_id,
            summary=analysis_data.get("summary", ""),
            key_points=analysis_data.get("key_points", []),
            user_sentiment=analysis_data.get("user_sentiment", "neutral"),
            outcome=analysis_data.get("outcome", "other"),
            next_action=analysis_data.get("next_action", "")
        )
        
        logger.info(f"✅ Call analysis saved for {call_id}: {analysis_data.get('outcome')}")
        
    except Exception as e:
        logger.error(f"Error generating call analysis for {call_id}: {e}")


@app.post("/callbacks/status/{call_id}")
async def status_callback(call_id: str, request: Request):
    """
    Handle Twilio status callbacks
    Updates call status in database
    """
    try:
        form_data = await request.form()
        status = form_data.get("CallStatus")
        call_sid = form_data.get("CallSid")
        duration = form_data.get("CallDuration")
        
        logger.info(f"Status callback for {call_id}: {status} | SID: {call_sid}")
        
        db = get_db()
        update_data = {"status": status}
        
        # Handle terminal states (call is done)
        if status in ["completed", "busy", "no-answer", "failed", "canceled"]:
            update_data["ended_at"] = datetime.now()
            if duration:
                update_data["duration"] = int(duration)
            
            # Only generate analysis for completed calls with conversation
            if status == "completed":
                try:
                    await generate_call_analysis(call_id, db)
                except Exception as analysis_error:
                    logger.error(f"Failed to generate call analysis for {call_id}: {analysis_error}")
        
        await db.update_call(call_id, **update_data)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in status callback for {call_id}: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/callbacks/recording/{call_id}")
async def recording_callback(call_id: str, request: Request):
    """
    Handle Twilio recording callbacks
    Saves recording URL to database
    """
    try:
        form_data = await request.form()
        recording_url = form_data.get("RecordingUrl")
        recording_sid = form_data.get("RecordingSid")
        recording_duration = form_data.get("RecordingDuration")
        
        logger.info(f"Recording callback for {call_id}: {recording_sid} | Duration: {recording_duration}s")
        
        if recording_url:
            db = get_db()
            # Twilio recording URL needs .mp3 appended for direct download
            full_recording_url = f"{recording_url}.mp3"
            
            update_data = {
                "recording_url": full_recording_url,
            }
            
            if recording_duration:
                update_data["recording_duration"] = int(recording_duration)
            
            await db.update_call(call_id, **update_data)
            logger.info(f"✅ Recording URL saved for {call_id}: {full_recording_url}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error in recording callback for {call_id}: {e}")
        return {"status": "error", "message": str(e)}


# ==================== WEBSOCKET HANDLER (VAPI-STYLE) ====================

@app.websocket("/ws/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    """
    Main WebSocket handler for Twilio Media Streams
    
    VAPI-STYLE ARCHITECTURE:
    - 3-state machine: LISTENING → USER_SPEAKING → AI_SPEAKING
    - VAD edge-trigger: 240ms speech start, 300ms silence end
    - TRUE barge-in: User can interrupt AI mid-speech
    - NO post-TTS sleep, NO cooldowns, NO adaptive silence
    
    Target: <4s total response time (including STT + LLM + TTS)
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for call {call_id}")
    
    session = None
    
    try:
        # Get call and agent details
        db = get_db()
        call = await db.get_call(call_id)
        
        if not call:
            logger.error(f"Call {call_id} not found")
            await websocket.close()
            return
        
        agent = await db.get_agent(call["agent_id"])
        if not agent:
            logger.error(f"Agent {call['agent_id']} not found")
            await websocket.close()
            return
        
        # Initialize AI clients
        llm = get_llm_client()
        stt = get_stt_client()
        tts = get_tts_client()
        
        stream_sid = None
        
        # Main message loop
        while True:
            try:
                # Receive message from Twilio
                message = await websocket.receive_text()
                data = json.loads(message)
                event = data.get("event")
                
                if event == "start":
                    # Stream started
                    stream_sid = data["start"]["streamSid"]
                    logger.info(f"Stream started: {stream_sid}")
                    
                    # Create session
                    session = CallSession(call_id, agent["id"], stream_sid)
                    session.agent_config = agent
                    active_sessions[stream_sid] = session
                    
                    # Generate opening line with LLM
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
                    
                    base_prompt = agent.get("resolved_system_prompt") or agent.get("system_prompt", "You are a helpful AI assistant.")
                    system_prompt = f"{GREETING_PROMPT}\n\n{base_prompt}"
                    
                    greeting = await llm.generate_response(
                        messages=[{"role": "user", "content": "Generate your opening line for this cold call."}],
                        system_prompt=system_prompt,
                        temperature=agent.get("temperature", 0.7),
                        max_tokens=50  # Increased for better greeting
                    )
                    
                    # Clean meta-commentary
                    import re
                    if any(word in greeting.lower() for word in ['here', 'opening', 'line:', 'say:', '"']):
                        match = re.search(r'[""]([^""]+)[""]', greeting)
                        if match:
                            greeting = match.group(1)
                        else:
                            greeting = re.sub(r'^.*?(?:opening line|here|say)s?:?\s*', '', greeting, flags=re.IGNORECASE).strip().strip('"\'')
                    
                    logger.info(f"Generated greeting: {greeting}")
                    
                    # Save to database
                    await db.add_transcript(call_id=call_id, speaker="agent", text=greeting)
                    
                    # Set AI_SPEAKING state and send audio
                    session.state = ConversationState.AI_SPEAKING
                    session.interrupted = False
                    await send_ai_response_with_bargein(websocket, session, greeting, tts, db, call_id)
                    
                    # Mark AI turn complete for first-utterance tracking
                    session.mark_ai_turn_complete()
                    
                    # Immediately ready for user input (NO SLEEP!)
                    session.reset_for_listening()
                    logger.info("🟢 AI finished speaking - ready for user input (state: LISTENING)")
                
                elif event == "media":
                    if not session:
                        continue
                    
                    # Decode audio
                    payload = data["media"]["payload"]
                    audio_data = base64.b64decode(payload)
                    
                    # ==================== BARGE-IN: Check for interruption during AI speech ====================
                    if session.state == ConversationState.AI_SPEAKING:
                        # Run VAD on incoming audio even during AI speech
                        is_speech = session.detect_speech_vad(audio_data)
                        if is_speech:
                            # User is speaking over AI - INTERRUPT!
                            session.interrupt_ai()
                            session.state = ConversationState.USER_SPEAKING
                            session.speech_start_time = datetime.now()
                            session.audio_buffer.clear()  # Start fresh buffer for user speech
                            logger.info("🛑 BARGE-IN DETECTED: Switching to USER_SPEAKING")
                        continue  # Don't buffer AI's own audio
                    
                    # ==================== VAD EDGE-TRIGGER STATE MACHINE ====================
                    is_speech = session.detect_speech_vad(audio_data)
                    vad_event = session.update_vad_state(is_speech)
                    
                    # ==================== AUDIO BUFFERING: ONLY in USER_SPEAKING ====================
                    # This is critical to prevent echo/noise from polluting the buffer
                    if session.state == ConversationState.USER_SPEAKING:
                        session.add_audio_chunk(audio_data)
                    
                    # State transitions based on VAD edges
                    if vad_event == "speech_start" and session.state == ConversationState.LISTENING:
                        # User started speaking (210ms of speech detected)
                        session.state = ConversationState.USER_SPEAKING
                        session.add_audio_chunk(audio_data)  # Add the triggering audio too
                        logger.info(f"🎤 Speech START detected - state: USER_SPEAKING | Echo window: {session.is_in_echo_window()}")
                    
                    elif vad_event == "speech_end" and session.state == ConversationState.USER_SPEAKING:
                        # User finished speaking (240ms of silence)
                        audio_duration = len(session.audio_buffer) / 8000
                        if session.has_sufficient_audio():
                            logger.info(f"🎤 Speech END detected - processing {len(session.audio_buffer)}B ({audio_duration:.2f}s)")
                            await process_user_speech_fast(session, websocket, stt, llm, tts, db)
                        else:
                            logger.debug(f"Speech end but insufficient audio ({len(session.audio_buffer)}B) - skipping")
                            session.reset_for_listening()
                    
                    # Periodic debug logging (every second)
                    if len(session.audio_buffer) % 8000 == 0 and len(session.audio_buffer) > 0:
                        energy = sum(abs(b - 127) for b in audio_data) / len(audio_data) if audio_data else 0
                        echo_status = "ECHO_WINDOW" if session.is_in_echo_window() else "clear"
                        logger.info(f"📊 State: {session.state.value} | Buffer: {len(session.audio_buffer)}B | Speech: {is_speech} | Energy: {energy:.1f} | {echo_status}")
                
                elif event == "stop":
                    logger.info(f"Stream stopped: {stream_sid}")
                    break
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for call {call_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                continue
        
    except Exception as e:
        logger.error(f"WebSocket error for call {call_id}: {e}", exc_info=True)
    
    finally:
        if session and session.stream_sid in active_sessions:
            del active_sessions[session.stream_sid]
        logger.info(f"WebSocket closed for call {call_id}")
        try:
            await websocket.close()
        except:
            pass


# ==================== FAST USER SPEECH PROCESSING (Vapi-style) ====================

async def process_user_speech_fast(
    session: CallSession,
    websocket: WebSocket,
    stt: STTClient,
    llm: LLMClient,
    tts: TTSClient,
    db: SupabaseDB
):
    """
    Process user speech with CONVERSATION INTEGRITY CHECKS
    
    Flow:
    1. AUDIO QUALITY GATES - Reject short/low-energy audio before STT
    2. STT transcription
    3. INTENT CLASSIFICATION - Detect noise, corrections, intents
    4. CORRECTION PHRASE HANDLING - Extract real intent from "No, I said X"
    5. Response generation (scripted or LLM)
    6. TTS → Send audio with barge-in support
    """
    try:
        # Get audio
        audio_mulaw = session.get_and_clear_buffer()
        if not audio_mulaw:
            session.reset_for_listening()
            return
        
        audio_duration_ms = (len(audio_mulaw) / TWILIO_SAMPLE_RATE) * 1000
        logger.info(f"Processing {len(audio_mulaw)} bytes ({audio_duration_ms:.0f}ms) for call {session.call_id}")
        
        # ==================== AUDIO QUALITY GATE 1: Duration ====================
        # Very short audio is almost certainly noise/echo, don't waste STT call
        if audio_duration_ms < session.MIN_STT_DURATION_MS:
            # Special case: First utterance after AI is more likely to be echo
            if session.is_first_utterance_after_ai() and audio_duration_ms < session.DISCARD_FIRST_IF_SHORT_MS:
                logger.info(f"🚫 First utterance after AI too short ({audio_duration_ms:.0f}ms < {session.DISCARD_FIRST_IF_SHORT_MS}ms) - likely echo, discarding")
                session.mark_noise_detected()
                session.reset_for_listening()
                return
            
            if audio_duration_ms < session.MIN_AUDIO_DURATION_MS:
                logger.info(f"🚫 Audio too short ({audio_duration_ms:.0f}ms < {session.MIN_AUDIO_DURATION_MS}ms) - skipping STT")
                session.mark_noise_detected()
                session.reset_for_listening()
                return
        
        # ==================== AUDIO QUALITY GATE 2: Energy ====================
        # Only check minimum energy - max energy check removed because mobile phones
        # with AGC produce high-energy audio (often 127) that is valid speech
        avg_energy = sum(abs(b - 127) for b in audio_mulaw) / len(audio_mulaw)
        if avg_energy < session.MIN_SPEECH_ENERGY:
            logger.info(f"🚫 Energy too low ({avg_energy:.1f} < {session.MIN_SPEECH_ENERGY}) - skipping")
            session.mark_noise_detected()
            session.reset_for_listening()
            return
        
        # Convert to WAV for STT
        audio_pcm = audioop.ulaw2lin(audio_mulaw, 2)
        audio_pcm_16k, _ = audioop.ratecv(audio_pcm, 2, 1, TWILIO_SAMPLE_RATE, 16000, None)
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(audio_pcm_16k)
        wav_buffer.seek(0)
        wav_bytes = wav_buffer.read()
        
        # STT transcription
        stt_start = datetime.now()
        user_text = stt.transcribe_audio(audio_data=wav_bytes)
        stt_duration = (datetime.now() - stt_start).total_seconds() * 1000
        
        if not user_text or len(user_text.strip()) < 2:
            logger.debug("No meaningful speech detected")
            session.mark_noise_detected()
            session.reset_for_listening()
            return
        
        logger.info(f"👤 User said: '{user_text}' (STT: {stt_duration:.0f}ms)")
        
        # ==================== CORRECTION PHRASE HANDLING ====================
        # Detect "No, I said X" or "I said X" patterns and extract the real intent
        import re
        correction_match = re.match(r"^(?:no,?\s*)?i\s+said\s+['\"]?(.+?)['\"]?\.?$", user_text.lower().strip(), re.IGNORECASE)
        if correction_match:
            extracted_text = correction_match.group(1).strip()
            logger.info(f"🔄 Correction phrase detected - extracting: '{extracted_text}'")
            # Use the extracted text instead of the full correction phrase
            user_text = extracted_text
        
        # Duplicate/echo detection
        if session.last_user_text and session.last_user_text_time:
            time_since = (datetime.now() - session.last_user_text_time).total_seconds()
            if time_since < 2.0 and user_text.lower().strip() == session.last_user_text.lower().strip():
                logger.warning(f"🚫 Duplicate detected within {time_since:.1f}s - skipping")
                session.mark_noise_detected()
                session.reset_for_listening()
                return
        
        # ==================== INTENT PRE-CLASSIFICATION ====================
        # Calculate time since AI spoke for echo detection
        time_since_ai_ms = 9999.0
        if session.last_ai_turn_end:
            time_since_ai_ms = (datetime.now() - session.last_ai_turn_end).total_seconds() * 1000
        
        intent, scripted_response = classify_intent(user_text, time_since_ai_ms)
        logger.info(f"🧠 Intent: {intent} (time since AI: {time_since_ai_ms:.0f}ms)")
        
        # ==================== NOISE/ECHO DETECTION - Skip entirely ====================
        if intent in ("noise", "echo"):
            reason = "echo" if intent == "echo" else "noise"
            logger.info(f"🔇 {reason.title()} detected ('{user_text}') - ignoring, starting cooldown")
            session.mark_noise_detected()
            session.reset_for_listening()
            return
        
        # ==================== MARK REAL USER UTTERANCE ====================
        session.mark_user_utterance()
        session.last_user_text = user_text
        session.last_user_text_time = datetime.now()
        
        # Save user transcript
        await db.add_transcript(call_id=session.call_id, speaker="user", text=user_text)
        
        # Handle scripted responses (no LLM needed)
        if scripted_response:
            ai_response = scripted_response
            logger.info(f"⚡ Scripted response (no LLM): {ai_response}")
        else:
            # ==================== SET LLM IN-FLIGHT FLAG ====================
            # This prevents VAD from triggering false speech during LLM wait
            session.llm_in_flight = True
            
            # Get conversation history (more context for better responses)
            conversation_history = await db.get_conversation_history(session.call_id, limit=10)
            messages = conversation_history + [{"role": "user", "content": user_text}]
            
            # Debug: Log conversation context being sent
            logger.debug(f"📝 Conversation context: {len(conversation_history)} previous messages + current: '{user_text}'")
            if conversation_history:
                logger.debug(f"📝 Last exchange: {conversation_history[-2:] if len(conversation_history) >= 2 else conversation_history}")
            
            # Build system prompt based on intent
            if intent == "affirm":
                # User said yes/okay - add context to help LLM continue
                intent_hint = """
CONTEXT: User just confirmed/agreed (said yes, okay, sure, etc.)
ACTION: Continue with your pitch or next question. Do NOT ask them to clarify. Do NOT repeat your last question."""
            elif intent == "ack":
                # User acknowledged - continue naturally
                intent_hint = """
CONTEXT: User acknowledged (hmm, uh-huh, I see)
ACTION: Continue speaking naturally. They are listening."""
            elif intent == "open":
                # User wants context
                intent_hint = """
CONTEXT: User wants to know who you are or what this is about.
ACTION: Briefly explain your purpose in 1-2 sentences."""
            elif intent == "negative":
                # User declined
                intent_hint = """
CONTEXT: User seems uninterested or busy.
ACTION: Acknowledge respectfully and offer to call back at a better time. Don't be pushy."""
            else:
                intent_hint = ""
            
            # PROFESSIONAL SALES AGENT PROMPT - Applied to ALL calls
            SALES_AGENT_RULES = """CRITICAL RULES FOR PHONE CONVERSATION:

1. NEVER REPEAT - If you already asked something, MOVE FORWARD. Check the conversation history!
2. ONE QUESTION per response - Never combine multiple questions
3. UNDERSTAND SLANG:
   - "I'm down" / "down for that" / "bet" = YES, they agree
   - "sounds good" / "cool" / "awesome" = positive response
   - "yeah" / "yep" / "sure" = affirmative
4. UNDERSTAND NUMBERS:
   - "4-5" or "four to five" = the number 4 or 5 (SMALL)
   - NEVER interpret "4-5" as "400-500"
5. FOLLOW CONTEXT:
   - If user answered a question, move to the NEXT step
   - Don't re-ask what they already answered
6. MAX 15 WORDS per response - Keep it short!
7. NATURAL SPEECH - Use "I'm", "you're", "that's", "cool", "got it"
8. ADVANCE THE CONVERSATION - Each response moves toward the goal
9. SCHEDULING FLOW:
   - First get DAY → Then get TIME → Then get EMAIL
   - Never skip steps!
"""
            base_prompt = session.agent_config.get("resolved_system_prompt") or session.agent_config.get("system_prompt", "You are a helpful assistant.")
            
            # Add last AI response context to prevent repetition
            repetition_guard = ""
            if session.last_ai_response:
                repetition_guard = f"\n\nIMPORTANT: Your last response was: \"{session.last_ai_response}\"\nDO NOT repeat this. Say something different or move the conversation forward.\n"
            
            system_prompt = f"{SALES_AGENT_RULES}{intent_hint}{repetition_guard}\n\n{base_prompt}"
            
            try:
                llm_start = datetime.now()
                ai_response = await llm.generate_response(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=session.agent_config.get("temperature", 0.7),
                    max_tokens=80  # Increased from 40 for better responses
                )
                llm_duration = (datetime.now() - llm_start).total_seconds() * 1000
                logger.info(f"🤖 LLM response ({llm_duration:.0f}ms): {ai_response}")
                
                # Check if LLM repeated itself despite instructions
                if session.last_ai_response and ai_response.strip().lower() == session.last_ai_response.strip().lower():
                    logger.warning(f"🔄 LLM repeated itself - using fallback")
                    ai_response = "I understand. Is there anything specific you'd like to know?"
                    
            except Exception as e:
                logger.error(f"LLM error: {e}")
                ai_response = "Sorry, I'm having a technical issue. Can you say that again?"
            finally:
                # Clear LLM in-flight flag
                session.llm_in_flight = False
        
        # Save AI response and track it
        session.last_ai_response = ai_response
        await db.add_transcript(call_id=session.call_id, speaker="agent", text=ai_response)
        
        # Send AI response with barge-in support
        session.state = ConversationState.AI_SPEAKING
        session.interrupted = False
        await send_ai_response_with_bargein(websocket, session, ai_response, tts, db, session.call_id)
        
        # Mark AI turn complete for turn tracking
        session.mark_ai_turn_complete()
        
        # Ready for next input (NO SLEEP!)
        session.reset_for_listening()
        logger.info("🟢 AI finished - ready for user input")
        
    except Exception as e:
        logger.error(f"Error in process_user_speech_fast: {e}", exc_info=True)
        session.reset_for_listening()


async def send_ai_response_with_bargein(
    websocket: WebSocket,
    session: CallSession,
    text: str,
    tts: TTSClient,
    db: SupabaseDB,
    call_id: str
) -> float:
    """
    Send AI audio with BARGE-IN support
    
    While streaming audio:
    - Check session.interrupted flag
    - If True: Stop immediately, user is speaking
    - NO post-audio sleep!
    """
    try:
        # Generate speech
        tts_start = datetime.now()
        sentence_chunks = tts.generate_speech_streaming(text)
        tts_gen_time = (datetime.now() - tts_start).total_seconds() * 1000
        logger.info(f"⚡ TTS generated in {tts_gen_time:.0f}ms")
        
        if not sentence_chunks:
            logger.error("TTS failed to generate audio")
            return 0.0
        
        total_duration = 0.0
        
        for sentence_text, wav_bytes in sentence_chunks:
            # Check for barge-in before each sentence
            if session.interrupted:
                logger.info(f"🛑 BARGE-IN: Stopping TTS mid-stream")
                break
            
            logger.debug(f"Streaming: {sentence_text[:30]}...")
            
            # Convert WAV to Twilio format
            wav_buffer = io.BytesIO(wav_bytes)
            with wave.open(wav_buffer, 'rb') as wav:
                channels = wav.getnchannels()
                sample_width = wav.getsampwidth()
                framerate = wav.getframerate()
                audio_pcm = wav.readframes(wav.getnframes())
            
            # Resample to 8kHz
            if framerate != TWILIO_SAMPLE_RATE:
                audio_pcm, _ = audioop.ratecv(audio_pcm, sample_width, channels, framerate, TWILIO_SAMPLE_RATE, None)
            
            # Mono
            if channels == 2:
                audio_pcm = audioop.tomono(audio_pcm, sample_width, 1, 1)
            
            # Convert to mulaw
            audio_mulaw = audioop.lin2ulaw(audio_pcm, sample_width)
            
            # Send in 20ms chunks
            chunk_size = int(TWILIO_SAMPLE_RATE * 0.02)
            
            for i in range(0, len(audio_mulaw), chunk_size):
                # Check barge-in during streaming
                if session.interrupted:
                    logger.info("🛑 BARGE-IN during chunk streaming")
                    break
                
                chunk = audio_mulaw[i:i + chunk_size]
                payload = base64.b64encode(chunk).decode('utf-8')
                
                message = {
                    "event": "media",
                    "streamSid": session.stream_sid,
                    "media": {"payload": payload}
                }
                
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as ws_error:
                    logger.warning(f"WebSocket send failed (connection closed?): {ws_error}")
                    return total_duration
            
            if session.interrupted:
                break
            
            sentence_duration = len(audio_mulaw) / TWILIO_SAMPLE_RATE
            total_duration += sentence_duration
            logger.debug(f"Sent sentence: {sentence_duration:.2f}s")
        
        # ==================== SET ECHO PROTECTION WINDOW ====================
        # This is CRITICAL: Mark when TTS finished so VAD ignores echo for 300ms
        session.tts_end_time = datetime.now()
        logger.debug(f"🔇 Echo protection window started (300ms)")
        
        if session.interrupted:
            logger.info(f"⚡ AI speech interrupted after {total_duration:.1f}s")
        else:
            logger.info(f"✅ AI speech complete: {total_duration:.1f}s | Echo window active")
        
        return total_duration
        
    except Exception as e:
        logger.error(f"Error in send_ai_response_with_bargein: {e}", exc_info=True)
        # Still set echo protection even on error
        session.tts_end_time = datetime.now()
        return 0.0


# ==================== STARTUP ====================

# Global ngrok URL storage
ngrok_public_url = None

@app.on_event("startup")
async def startup_event():
    """Initialize services and start ngrok tunnel"""
    global ngrok_public_url
    
    logger.info("Starting RelayX Voice Gateway v2.0 (Vapi-style architecture)...")
    logger.info("Features: VAD edge-trigger, barge-in support, intent pre-classification")
    
    # Start ngrok tunnel automatically
    try:
        import subprocess
        import requests
        import time
        
        logger.info("Starting ngrok tunnel on port 8001...")
        
        subprocess.Popen(
            ["ngrok", "http", "8001", "--log=stdout"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        time.sleep(3)
        
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        
        if tunnels:
            ngrok_public_url = tunnels[0]["public_url"]
            logger.info(f"✅ Ngrok tunnel ready: {ngrok_public_url}")
        else:
            logger.warning("⚠️ Ngrok started but no tunnels found")
            
    except Exception as e:
        logger.warning(f"Could not start ngrok automatically: {e}")
        logger.info("You can start ngrok manually: ngrok http 8001")
    
    logger.info("✅ WebRTC VAD ready (240ms speech start, 300ms speech end)")
    
    try:
        logger.info("Loading STT client...")
        stt = get_stt_client()
        logger.info("✅ STT ready")
    except Exception as e:
        logger.error(f"Failed to load STT: {e}")
    
    try:
        logger.info("Loading TTS client...")
        tts = get_tts_client()
        logger.info("✅ TTS ready")
    except Exception as e:
        logger.error(f"Failed to load TTS: {e}")
    
    logger.info("🎉 Voice Gateway startup complete - Target: <4s response time")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("VOICE_GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("VOICE_GATEWAY_PORT", 8001))
    
    uvicorn.run(
        "voice_gateway:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
