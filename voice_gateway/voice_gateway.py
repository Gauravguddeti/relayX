"""
Voice Gateway for RelayX AI Caller
Handles Twilio Media Streams via WebSocket
Real-time pipeline: Audio → STT → LLM → TTS → Audio
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import asyncio
import base64
import json
import sys
import os
from loguru import logger
from datetime import datetime
import audioop
import tempfile
import torch
import numpy as np

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
    version="1.0.0"
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
VAD_SAMPLE_RATE = 16000  # Silero VAD expects 16kHz

# Silero VAD model (loaded at startup)
silero_vad_model = None

# Call sessions storage
active_sessions = {}


class CallSession:
    """Manages state for an active call"""
    
    # Configurable timing parameters - OPTIMIZED FOR FAST NATURAL CONVERSATION
    SILENCE_THRESHOLD_MS = 1200  # 1200ms of silence = user done speaking (prevents mid-sentence splits)
    MIN_AUDIO_DURATION_MS = 400  # Minimum 0.4s of audio before processing (catch quick responses)
    VAD_THRESHOLD = 0.5  # Silero VAD speech probability threshold (0.0-1.0)
    MIN_SPEECH_ENERGY = 50  # Reject audio with energy < 50 (pure silence/echo is ~120-128)
    VAD_CHUNK_SIZE = 512  # Minimum bytes needed for Silero VAD (about 64ms at 8kHz)
    
    def __init__(self, call_id: str, agent_id: str, stream_sid: str):
        self.call_id = call_id
        self.agent_id = agent_id
        self.stream_sid = stream_sid
        self.audio_buffer = bytearray()
        self.vad_buffer = bytearray()  # Separate buffer for VAD processing
        self.is_speaking = False  # AI is currently speaking
        self.conversation_history = []
        self.agent_config = None
        self.last_user_speech = None
        self.last_audio_time = datetime.now()
        self.silence_start = None
        self.created_at = datetime.now()
        
        logger.info(f"CallSession created: {call_id} | StreamSID: {stream_sid}")
    
    def add_audio_chunk(self, audio_data: bytes):
        """Add audio chunk to buffer"""
        self.audio_buffer.extend(audio_data)
    
    def get_and_clear_buffer(self) -> bytes:
        """Get audio buffer and clear it"""
        data = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        return data
    
    def has_sufficient_audio(self, min_duration_ms: Optional[int] = None) -> bool:
        """Check if buffer has enough audio (approx)"""
        if min_duration_ms is None:
            min_duration_ms = self.MIN_AUDIO_DURATION_MS
        # Rough estimate: mulaw is 1 byte per sample at 8kHz
        # So 1 second = 8000 bytes
        min_bytes = (TWILIO_SAMPLE_RATE * min_duration_ms) // 1000
        return len(self.audio_buffer) >= min_bytes
    
    def detect_silence(self, audio_data: bytes) -> bool:
        """Silero VAD-based speech detection with buffering"""
        global silero_vad_model
        
        if len(audio_data) == 0 or silero_vad_model is None:
            return True
        
        # Add chunk to VAD buffer
        self.vad_buffer.extend(audio_data)
        
        # We need at least VAD_CHUNK_SIZE bytes to run Silero VAD
        if len(self.vad_buffer) < self.VAD_CHUNK_SIZE:
            # Not enough data yet - assume silence for now
            return True
        
        try:
            # Process the accumulated buffer with Silero VAD
            vad_data = bytes(self.vad_buffer)
            
            # Convert mulaw to linear PCM (required for VAD)
            pcm_data = audioop.ulaw2lin(vad_data, 2)  # 16-bit PCM
            
            # Convert to numpy array
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
            
            # Resample from 8kHz to 16kHz for Silero VAD
            audio_16k = np.interp(
                np.linspace(0, len(audio_array), len(audio_array) * 2),
                np.arange(len(audio_array)),
                audio_array
            ).astype(np.int16)
            
            # Normalize to [-1, 1] float32
            audio_float = audio_16k.astype(np.float32) / 32768.0
            
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio_float)
            
            # Get speech probability from Silero VAD
            speech_prob = silero_vad_model(audio_tensor, VAD_SAMPLE_RATE).item()
            
            # Clear VAD buffer after processing
            self.vad_buffer.clear()
            
            # Return True if silence (speech probability below threshold)
            is_silence = speech_prob < self.VAD_THRESHOLD
            
            return is_silence
            
        except Exception as e:
            logger.warning(f"Silero VAD error: {e}")
            # Clear buffer on error to prevent repeated failures
            self.vad_buffer.clear()
            # Fallback: simple energy-based detection
            energy = sum(abs(b - 127) for b in audio_data) / len(audio_data)
            return energy > 120 or energy < 60
    
    def update_silence_state(self, is_silence: bool):
        """Track silence duration for VAD"""
        if is_silence:
            if self.silence_start is None:
                self.silence_start = datetime.now()
        else:
            self.silence_start = None
    
    def get_silence_duration_ms(self) -> int:
        """Get current silence duration in milliseconds"""
        if self.silence_start is None:
            return 0
        return int((datetime.now() - self.silence_start).total_seconds() * 1000)
    
    def reset_for_ai_speech(self):
        """Reset state when AI starts speaking to prevent echo contamination"""
        self.audio_buffer.clear()
        self.silence_start = None
        self.recent_energy = []  # Reset baseline tracking
        self.baseline_energy = 70.0  # Reset to default


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


# ==================== WEBSOCKET HANDLER ====================

@app.websocket("/ws/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    """
    Main WebSocket handler for Twilio Media Streams
    
    Flow:
    1. Receive audio chunks from Twilio (mulaw encoded)
    2. Buffer audio until we have enough for STT
    3. Convert to text (Whisper)
    4. Send to LLM with conversation history
    5. Generate speech (TTS)
    6. Stream audio back to Twilio
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
                    
                    # Generate opening line with LLM using agent's prompt
                    GREETING_PROMPT = """SYSTEM OVERRIDE (HIGHEST PRIORITY):
You must follow all safety guidelines. Refuse harmful, illegal, or abusive requests.
Never share private information. Stay professional and helpful.

IMPORTANT: Output ONLY the exact words you will speak. NO meta-commentary, NO quotes, NO explanations like "Here's my opening line". Just speak naturally.

OUTBOUND CALL BEHAVIOR:
- This is an OUTBOUND call - YOU called THEM
- Introduce yourself briefly and ask if they have a moment
- Keep it SHORT (1-2 sentences max)
- Sound natural and friendly

VOICE FORMATTING RULES (CRITICAL FOR TTS):
- NEVER write times as digits like "12:00" - say "twelve PM" or "noon"
- NEVER write "24/7" - say "twenty four seven"
- Write numbers as words for better pronunciation

Examples (output like these, NO quotes):
Hi! This is Emma from TechCorp. I wanted to reach out about your recent inquiry. Do you have a quick moment?
Hello! This is Mark with ABC Services. I'm following up on your interest. Is now a good time?"""
                    
                    base_prompt = agent.get("resolved_system_prompt") or agent.get("system_prompt", "You are a helpful AI assistant. Which works for outbound calls.")
                    system_prompt = f"{GREETING_PROMPT}\n\n{base_prompt}"
                    
                    greeting = await llm.generate_response(
                        messages=[{"role": "user", "content": "Say your opening line now."}],
                        system_prompt=system_prompt,
                        temperature=agent.get("temperature", 0.7),
                        max_tokens=60
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
                    
                    # Save greeting to database BEFORE sending (for conversation context)
                    await db.add_transcript(
                        call_id=call_id,
                        speaker="agent",
                        text=greeting
                    )
                    
                    # Set speaking flag and clear buffer BEFORE sending (blocks new audio)
                    session.is_speaking = True
                    session.reset_for_ai_speech()  # Clear buffer and reset baseline to prevent echo
                    duration = await send_ai_response(websocket, stream_sid, greeting, tts, db, call_id)
                    
                    # Keep is_speaking=True for audio duration + 1s buffer (Twilio network latency + audio buffering)
                    await asyncio.sleep(duration + 1.0)
                    session.is_speaking = False
                
                elif event == "media":
                    # Audio data received
                    if not session:
                        logger.warning("Media event but no session!")
                        continue
                    
                    # Decode mulaw audio
                    payload = data["media"]["payload"]
                    audio_data = base64.b64decode(payload)
                    
                    # Update last audio time
                    session.last_audio_time = datetime.now()
                    
                    # Skip processing if AI is speaking (prevents echo and interruption)
                    if session.is_speaking:
                        # Don't buffer during AI speech - prevents echo contamination
                        logger.debug(f"🚫 Skipping audio during AI speech: {len(audio_data)} bytes | is_speaking={session.is_speaking}")
                        continue
                    
                    # Detect silence
                    is_silence = session.detect_silence(audio_data)
                    session.update_silence_state(is_silence)
                    
                    # Add to buffer
                    session.add_audio_chunk(audio_data)
                    
                    # Log every second with silence status
                    if len(session.audio_buffer) % 8000 == 0:
                        # Calculate energy and speech probability for debug
                        energy = sum(abs(b - 127) for b in audio_data) / len(audio_data) if audio_data else 0
                        logger.info(f"📊 Buffer: {len(session.audio_buffer)}B | Silence: {session.get_silence_duration_ms()}ms | Energy: {energy:.1f} | IsSilence: {is_silence} | is_speaking: {session.is_speaking}")
                    
                    # Process when sufficient audio + silence detected (fast response)
                    if session.has_sufficient_audio() and session.get_silence_duration_ms() > session.SILENCE_THRESHOLD_MS:
                        logger.info(f"🎤 PROCESSING: {len(session.audio_buffer)} bytes, {session.get_silence_duration_ms()}ms silence")
                        await process_user_speech(session, websocket, stt, llm, tts, db)
                
                elif event == "stop":
                    # Stream ended
                    logger.info(f"Stream stopped: {stream_sid}")
                    break
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for call {call_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
        
    except Exception as e:
        logger.error(f"WebSocket error for call {call_id}: {e}")
    
    finally:
        # Cleanup
        if session and session.stream_sid in active_sessions:
            del active_sessions[session.stream_sid]
        
        logger.info(f"WebSocket closed for call {call_id}")
        
        try:
            await websocket.close()
        except:
            pass


async def process_user_speech(
    session: CallSession,
    websocket: WebSocket,
    stt: STTClient,
    llm: LLMClient,
    tts: TTSClient,
    db: SupabaseDB
):
    """Process accumulated user speech"""
    try:
        # Get audio from buffer
        audio_mulaw = session.get_and_clear_buffer()
        
        if not audio_mulaw:
            return
        
        logger.info(f"Processing {len(audio_mulaw)} bytes of audio for call {session.call_id}")
        
        # Check audio quality - calculate average energy
        avg_energy = sum(abs(b - 127) for b in audio_mulaw) / len(audio_mulaw)
        
        # Check for pure silence (mulaw value 128 = silence)
        silence_ratio = sum(1 for b in audio_mulaw if abs(b - 127) <= 1) / len(audio_mulaw)
        
        logger.debug(f"Audio energy: {avg_energy:.1f} | Silence ratio: {silence_ratio:.2%}")
        
        # Reject if mostly silence (>70% silence values)
        if silence_ratio > 0.70:
            logger.info(f"Audio is {silence_ratio:.1%} silence - skipping transcription")
            return
        
        # Reject if energy too low (likely silence/background noise/echo)
        if avg_energy < session.MIN_SPEECH_ENERGY:
            logger.info(f"Audio energy too low ({avg_energy:.1f}), likely background noise/echo - skipping transcription")
            return
        
        # Convert mulaw to linear PCM for Whisper
        audio_pcm = audioop.ulaw2lin(audio_mulaw, 2)  # 2 bytes per sample (16-bit)
        
        # Upsample from 8kHz to 16kHz for better Whisper accuracy
        audio_pcm_16k, _ = audioop.ratecv(audio_pcm, 2, 1, TWILIO_SAMPLE_RATE, 16000, None)
        
        # Save to temp WAV file for Whisper
        import wave
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
            with wave.open(f, 'wb') as wav:
                wav.setnchannels(1)  # Mono
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(16000)  # 16kHz for better Whisper accuracy
                wav.writeframes(audio_pcm_16k)
        
        # Transcribe
        user_text = stt.transcribe_audio(audio_file=wav_path)
        
        # Cleanup temp file
        try:
            os.unlink(wav_path)
        except:
            pass
        
        if not user_text or len(user_text.strip()) < 2:
            logger.debug("No meaningful speech detected")
            return
        
        logger.info(f"User said: {user_text}")
        
        # Save to database
        await db.add_transcript(
            call_id=session.call_id,
            speaker="user",
            text=user_text
        )
        
        # Get conversation history
        conversation_history = await db.get_conversation_history(session.call_id, limit=6)
        
        # Add current user message
        messages = conversation_history + [{"role": "user", "content": user_text}]
        
        # Get LLM response with safety prefix and guardrails
        INTERNAL_SAFETY = """SYSTEM OVERRIDE (HIGHEST PRIORITY):
You must follow all safety guidelines. Refuse harmful, illegal, or abusive requests.
Never share private information. Stay professional and helpful.

OUTBOUND CALL BEHAVIOR:
- This is an OUTBOUND call - YOU called THEM, not the other way around
- You already introduced yourself and asked if they have a moment
- If they say "yes", "sure", "go ahead" - proceed with your pitch/purpose
- If they say "no", "busy", "not now" - politely offer to call back: "No problem! When would be a better time to reach you?"
- If they ask "who is this?" or "what's this about?" - briefly reintroduce and explain your purpose
- Be respectful of their time - get to the point quickly
- Don't keep asking "how can I help you" - YOU are calling with a specific purpose

NATURAL CONVERSATION FLOW (CRITICAL):
- Accept partial responses naturally - "Yes", "Yeah", "Okay" are valid confirmations, don't challenge them
- If user gives a short answer like "Yes" to a question asking for details, simply rephrase or move forward naturally
- NEVER say "you repeated yourself" or "that's what I just asked" - it's rude and breaks rapport
- NEVER point out supposed "misunderstandings" or "deviations" - just continue naturally
- NEVER say things like "It seems like there was a slight deviation" or "I was expecting a different response"
- If a response seems unclear or garbled, ASSUME it was positive and continue. Say "Got it!" and move on.
- If you genuinely can't understand, say "Sorry, I didn't catch that. Could you say that again?"
- Keep the conversation flowing smoothly - don't be overly literal or robotic
- Phone conversations naturally have brief responses - embrace them, don't fight them
- Speech recognition is imperfect - if something sounds weird, assume the user said something reasonable and keep going

BREVITY IS CRUCIAL (PHONE CALL ETIQUETTE):
- Keep responses VERY SHORT - aim for 1-2 sentences maximum per response (under 5 seconds of speech)
- NEVER give responses longer than 3 sentences - people will hang up
- Long speeches make people tune out on phone calls - keep it punchy
- Break complex information into smaller chunks - ask a question, get feedback, continue
- If user says "thank you" or gives minimal responses, they may be trying to end politely - wrap up quickly
- Don't over-explain - give just enough information to move forward
- After explaining something, ask ONE simple question to keep them engaged
- Respect that their time is valuable - be concise and direct

GUARDRAILS - STAY ON TOPIC:
- You are a business assistant with a specific purpose defined in your system prompt
- DO NOT answer general knowledge questions (geography, history, trivia, celebrities, pop culture, etc.)
- DO NOT engage with random topics unrelated to your business purpose
- If asked off-topic questions, politely redirect: "I'm here to help with [your business purpose]. How can I assist you with that?"
- If user is clearly not interested or being disruptive, politely end the call
- Stay focused on your goal and don't get sidetracked

VOICE FORMATTING RULES (CRITICAL FOR TTS):
- NEVER write times as digits like "12:00" or "1:00" - TTS will say "zero zero"
- ALWAYS write times in words: "twelve PM", "one AM", "two thirty PM", "ten fifteen AM"
- Examples: "nine AM", "three thirty PM", "twelve noon", "midnight"
- For half hours: "two thirty" not "2:30"
- For quarter hours: "three fifteen" or "quarter past three" not "3:15"

NUMBERS & SLASHES (IMPORTANT):
- NEVER write "24/7" - say "twenty four seven" or "around the clock"
- NEVER write "365" - say "three sixty five" or "all year"
- NEVER write "50%" - say "fifty percent" or "half"
- Write numbers as words for better pronunciation: "twenty four" not "24"

CALL ENDING PROTOCOL:
- When the conversation goal is complete or user wants to end, say: "Thanks for your time! If you have any questions later, feel free to reach out. You can hang up now. Goodbye!"
- After saying goodbye, the user will disconnect - DO NOT continue talking
- If user says goodbye/bye/I have to go, acknowledge and end: "Thank you, goodbye!"
- Do not keep the call going unnecessarily - respect the user's time"""
        
        base_prompt = session.agent_config.get("resolved_system_prompt") or session.agent_config.get("system_prompt", "You are a helpful AI assistant.")
        system_prompt = f"{INTERNAL_SAFETY}\n\n{base_prompt}"
        temperature = session.agent_config.get("temperature", 0.7)
        max_tokens = 50  # Very short responses for fast conversation
        
        try:
            ai_response = await llm.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"AI response: {ai_response}")
        except Exception as llm_error:
            logger.error(f"⚠️  GROQ API FAILURE (not system issue): {llm_error}")
            # Send error message to caller
            error_message = "I'm having trouble connecting to my AI service right now. This is a Groq API issue. Please try again in a moment."
            await send_ai_response(websocket, session.stream_sid, error_message, tts, db, session.call_id)
            session.is_speaking = False
            return
        
        # Save AI response to database
        await db.add_transcript(
            call_id=session.call_id,
            speaker="agent",
            text=ai_response
        )
        
        # Generate speech and send to Twilio
        session.is_speaking = True
        session.reset_for_ai_speech()  # Clear buffer and reset baseline to prevent echo
        duration = await send_ai_response(websocket, session.stream_sid, ai_response, tts, db, session.call_id)
        
        # Keep is_speaking=True for audio duration + 1s buffer (Twilio network latency + audio buffering)
        await asyncio.sleep(duration + 1.0)
        session.is_speaking = False
        
    except Exception as e:
        logger.error(f"Error processing user speech: {e}")


async def send_ai_response(
    websocket: WebSocket,
    stream_sid: str,
    text: str,
    tts: TTSClient,
    db: SupabaseDB,
    call_id: str
) -> float:
    """Generate speech and send to Twilio. Returns audio duration in seconds."""
    try:
        # Generate speech
        audio_file = tts.generate_speech(text)
        
        if not audio_file:
            logger.error("TTS failed to generate audio")
            return
        
        # Read WAV file
        import wave
        with wave.open(audio_file, 'rb') as wav:
            # Get audio params
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            framerate = wav.getframerate()
            
            # Read frames
            audio_pcm = wav.readframes(wav.getnframes())
        
        # Cleanup temp file
        try:
            os.unlink(audio_file)
        except:
            pass
        
        # Convert to Twilio's format (8kHz mono mulaw)
        # First, resample if needed
        if framerate != TWILIO_SAMPLE_RATE:
            # Simple resampling using audioop
            audio_pcm, _ = audioop.ratecv(
                audio_pcm,
                sample_width,
                channels,
                framerate,
                TWILIO_SAMPLE_RATE,
                None
            )
        
        # Convert stereo to mono if needed
        if channels == 2:
            audio_pcm = audioop.tomono(audio_pcm, sample_width, 1, 1)
        
        # Convert to mulaw (remove normalization - causes distortion)
        audio_mulaw = audioop.lin2ulaw(audio_pcm, sample_width)
        
        # Send to Twilio in chunks
        # Twilio expects chunks of 20ms worth of audio
        chunk_size = int(TWILIO_SAMPLE_RATE * 0.02)  # 20ms = 160 bytes at 8kHz
        
        for i in range(0, len(audio_mulaw), chunk_size):
            chunk = audio_mulaw[i:i + chunk_size]
            payload = base64.b64encode(chunk).decode('utf-8')
            
            message = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": payload
                }
            }
            
            await websocket.send_text(json.dumps(message))
            
            # No delay - send as fast as possible, Twilio buffers it
        
        # Calculate audio duration (bytes / sample_rate)
        audio_duration_seconds = len(audio_mulaw) / TWILIO_SAMPLE_RATE
        
        # Mark sent
        logger.info(f"Sent AI speech to Twilio: {len(audio_mulaw)} bytes ({audio_duration_seconds:.1f}s)")
        
        return audio_duration_seconds
        
    except Exception as e:
        logger.error(f"Error sending AI response: {e}")
        return 0.0


# ==================== STARTUP ====================

# Global ngrok URL storage
ngrok_public_url = None

@app.on_event("startup")
async def startup_event():
    """Initialize services and start ngrok tunnel"""
    global ngrok_public_url, silero_vad_model
    
    logger.info("Starting RelayX Voice Gateway...")
    
    # Start ngrok tunnel automatically
    try:
        import subprocess
        import requests
        import time
        
        logger.info("Starting ngrok tunnel on port 8001...")
        
        # Start ngrok with configuration to avoid browser warning
        # Use --log=stdout --log-level=info for debugging if needed
        subprocess.Popen(
            ["ngrok", "http", "8001", "--log=stdout"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for ngrok to start
        time.sleep(3)
        
        # Get public URL from ngrok API
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
    
    # Load Silero VAD model
    try:
        logger.info("Loading Silero VAD model...")
        silero_vad_model, _ = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        silero_vad_model.eval()  # Set to evaluation mode
        logger.info("✅ Silero VAD ready (smart speech detection enabled)")
    except Exception as e:
        logger.error(f"Failed to load Silero VAD: {e}")
        logger.warning("Falling back to energy-based silence detection")
        silero_vad_model = None
    
    # Pre-load AI models
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
    
    logger.info("🎉 Voice Gateway startup complete")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("VOICE_GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("VOICE_GATEWAY_PORT", 8001))
    
    uvicorn.run(
        "voice_gateway:app",
        host=host,
        port=port,
        reload=False,  # Disable reload to keep models in memory
        log_level="info"
    )
