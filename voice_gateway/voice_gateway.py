"""
Voice Gateway for RelayX AI Caller
Handles Twilio Media Streams via WebSocket
Real-time pipeline: Audio → STT → LLM → TTS → Audio
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import base64
import json
import sys
import os
from loguru import logger
from datetime import datetime
import audioop
from io import BytesIO
import tempfile
import shutil

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

# Call sessions storage
active_sessions = {}

# Audio file storage for TTS playback
AUDIO_DIR = tempfile.mkdtemp(prefix="relayx_audio_")
logger.info(f"Audio directory: {AUDIO_DIR}")


class CallSession:
    """Manages state for an active call"""
    
    def __init__(self, call_id: str, agent_id: str, stream_sid: str):
        self.call_id = call_id
        self.agent_id = agent_id
        self.stream_sid = stream_sid
        self.audio_buffer = bytearray()
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
    
    def has_sufficient_audio(self, min_duration_ms: int = 2000) -> bool:
        """Check if buffer has enough audio (approx)"""
        # Rough estimate: mulaw is 1 byte per sample at 8kHz
        # So 1 second = 8000 bytes
        min_bytes = (TWILIO_SAMPLE_RATE * min_duration_ms) // 1000
        return len(self.audio_buffer) >= min_bytes
    
    def detect_silence(self, audio_data: bytes, threshold: int = 5) -> bool:
        """Simple energy-based silence detection"""
        if len(audio_data) == 0:
            return True
        # Calculate average absolute value (simple energy)
        energy = sum(abs(b - 127) for b in audio_data) / len(audio_data)
        return energy < threshold
    
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


# ==================== TWIML ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "RelayX Voice Gateway",
        "status": "running",
        "active_calls": len(active_sessions)
    }


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve TTS audio files for Twilio"""
    file_path = os.path.join(AUDIO_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav")
    return Response(content="Not found", status_code=404)


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
    Generate TwiML with Gather for proper user input handling
    This is called by Twilio when the call connects
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
        
        # Get agent to generate appropriate opening
        agent = await db.get_agent(call["agent_id"])
        
        # Use VOICE_GATEWAY_URL env var first (set externally), then ngrok auto-detection
        base_url = os.getenv("VOICE_GATEWAY_URL") or ngrok_public_url or "https://your-gateway-url.ngrok.io"
        
        logger.info(f"Using base_url for TwiML: {base_url}")
        
        # Generate opening line using LLM based on agent's system prompt
        # This allows outbound calls to pitch properly instead of generic "how can I help"
        tts = get_tts_client()
        llm = get_llm_client()
        
        # Determine call direction and generate appropriate opening
        direction = call.get("direction", "outbound")
        logger.info(f"Call {call_id} direction: {direction}")
        
        if direction == "outbound" and agent:
            # For outbound calls: AI initiates with a pitch/intro based on the agent's purpose
            base_prompt = agent.get("resolved_system_prompt") or agent.get("prompt_text") or agent.get("system_prompt", "")
            
            opening_prompt = f"""Based on your role and purpose, generate a SHORT opening line for an OUTBOUND phone call.

YOUR ROLE/PURPOSE:
{base_prompt[:500]}

REQUIREMENTS:
- This is an OUTBOUND call where YOU are calling the person
- Introduce yourself briefly (1 sentence max)
- Be polite and ask if they have a moment
- Keep it under 20 words total
- Sound natural and friendly, not robotic
- DO NOT ask "how can I help you" - YOU are the one reaching out

GOOD EXAMPLES:
- "Hi, this is Emma from ABC Dental. Hope you're doing well! Do you have a quick minute?"
- "Hello! I'm calling from XYZ Insurance about your recent inquiry. Is now a good time?"
- "Hi there! This is Alex with customer support following up on your account. Got a moment?"

Return ONLY the opening line, nothing else."""

            try:
                greeting_text = await llm.generate_response(
                    messages=[{"role": "user", "content": opening_prompt}],
                    system_prompt="You generate natural phone call opening lines. Be brief and friendly.",
                    temperature=0.7,
                    max_tokens=50
                )
                # Clean up any quotes or extra formatting
                greeting_text = greeting_text.strip().strip('"').strip("'")
                logger.info(f"Generated outbound opening: {greeting_text}")
            except Exception as e:
                logger.warning(f"Failed to generate opening, using fallback: {e}")
                greeting_text = "Hi there! This is your AI assistant calling. Do you have a moment to chat?"
        else:
            # For inbound calls: Standard greeting asking how to help
            greeting_text = "Hello! Thanks for calling. How can I help you today?"
        
        greeting_audio = tts.generate_speech(greeting_text)
        
        if greeting_audio and base_url and not base_url.startswith("https://your-gateway"):
            # Copy to audio directory
            import uuid
            audio_filename = f"{call_id}_greeting_{uuid.uuid4().hex[:8]}.wav"
            audio_path = os.path.join(AUDIO_DIR, audio_filename)
            shutil.copy2(greeting_audio, audio_path)
            
            # Cleanup temp file
            try:
                os.unlink(greeting_audio)
            except:
                pass
            
            audio_url = f"{base_url}/audio/{audio_filename}"
            
            # Generate TwiML with Gather using Piper audio
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" timeout="10" speechTimeout="auto" speechModel="phone_call" action="{base_url}/gather/{call_id}" method="POST" language="en-US" hints="help, information, support, yes, no">
        <Play>{audio_url}</Play>
    </Gather>
    <Say voice="Polly.Joanna">I didn't hear anything. Let me transfer you to a human assistant. Goodbye!</Say>
    <Hangup/>
</Response>"""
        else:
            # Fallback to Polly voice with dynamic greeting
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" timeout="10" speechTimeout="auto" speechModel="phone_call" action="{base_url}/gather/{call_id}" method="POST" language="en-US" hints="help, information, support, yes, no">
        <Say voice="Polly.Joanna">{greeting_text}</Say>
    </Gather>
    <Say voice="Polly.Joanna">I didn't hear anything. Goodbye!</Say>
    <Hangup/>
</Response>"""
        
        logger.info(f"TwiML with Gather generated for {call_id}")
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error generating TwiML for {call_id}: {e}", exc_info=True)
        return Response(
            content="<Response><Say>Sorry, there was an error</Say></Response>",
            media_type="application/xml"
        )


@app.post("/gather/{call_id}")
async def gather_callback(call_id: str, request: Request):
    """
    Handle Gather callback with user speech input
    Process speech and continue conversation
    """
    try:
        form_data = await request.form()
        speech_result = form_data.get("SpeechResult", "")
        confidence = form_data.get("Confidence", "0")
        
        logger.info(f"Gather callback for {call_id}: '{speech_result}' (confidence: {confidence})")
        
        if not speech_result:
            # No speech detected - give another chance
            base_url = os.getenv("VOICE_GATEWAY_URL", ngrok_public_url if ngrok_public_url else "")
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" timeout="10" speechTimeout="auto" speechModel="phone_call" action="{base_url}/gather/{call_id}" method="POST" language="en-US">
        <Say voice="Polly.Joanna">I didn't catch that. Could you please speak a bit louder and tell me what you need?</Say>
    </Gather>
    <Say voice="Polly.Joanna">I still couldn't hear you. Please call back when you're ready. Goodbye!</Say>
    <Hangup/>
</Response>"""
            return Response(content=twiml, media_type="application/xml")
        
        # Get database and AI clients
        db = get_db()
        llm = get_llm_client()
        tts = get_tts_client()
        
        # Get call and agent details
        call = await db.get_call(call_id)
        if not call:
            logger.error(f"Call {call_id} not found")
            return Response(content="<Response><Say>Call not found</Say><Hangup/></Response>", media_type="application/xml")
        
        agent = await db.get_agent(call["agent_id"])
        if not agent:
            logger.error(f"Agent {call['agent_id']} not found")
            return Response(content="<Response><Say>Agent not found</Say><Hangup/></Response>", media_type="application/xml")
        
        # Save user transcript
        await db.add_transcript(
            call_id=call_id,
            speaker="user",
            text=speech_result
        )
        
        # Get conversation history
        conversation_history = await db.get_conversation_history(call_id, limit=6)
        
        # Add current user message
        messages = conversation_history + [{"role": "user", "content": speech_result}]
        
        # Get LLM response with safety prefix and guardrails
        INTERNAL_SAFETY = """SYSTEM OVERRIDE (HIGHEST PRIORITY):
You must follow all safety guidelines. Refuse harmful, illegal, or abusive requests.
Never share private information. Stay professional and helpful.

GUARDRAILS - STAY ON TOPIC:
- You are a business assistant with a specific purpose defined in your system prompt
- DO NOT answer general knowledge questions (geography, history, trivia, celebrities, etc.)
- DO NOT engage with random topics unrelated to your business purpose
- If asked off-topic questions, politely redirect: "I'm here to help with [your business purpose]. How can I assist you with that?"
- If user is clearly not interested or being disruptive, politely end the call
- Stay focused on your goal and don't get sidetracked

TIME FORMATTING FOR VOICE:
- NEVER write times as digits like "12:00" or "1:00" - the TTS will say "zero zero"
- ALWAYS write times in words: "twelve PM", "one AM", "two thirty PM", "ten fifteen AM"
- Examples: "nine AM", "three thirty PM", "twelve noon", "midnight"
- For half hours: "two thirty" not "2:30"
- For quarter hours: "three fifteen" or "quarter past three" not "3:15"

CALL ENDING PROTOCOL:
- When the conversation goal is complete or user wants to end, say: "Thanks for your time! If you have any questions later, feel free to reach out. You can hang up now. Goodbye!"
- If user says goodbye/bye/I have to go, acknowledge and end: "Thank you, goodbye!"
- Do not keep the call going unnecessarily - respect the user's time"""
        
        base_prompt = agent.get("resolved_system_prompt") or agent.get("system_prompt", "You are Emma, a helpful AI assistant.")
        
        # Search knowledge base for relevant context
        knowledge_context = ""
        try:
            agent_id = call.get("agent_id")
            relevant_knowledge = await db.search_knowledge(agent_id, speech_result, limit=2)
            if relevant_knowledge:
                knowledge_context = "\n\nRELEVANT INFORMATION FROM KNOWLEDGE BASE:\n"
                for kb in relevant_knowledge:
                    knowledge_context += f"- {kb['title']}: {kb['content'][:300]}...\n"
                knowledge_context += "\nUse this information to answer the user's question if relevant.\n"
                logger.info(f"Found {len(relevant_knowledge)} relevant knowledge entries")
        except Exception as kb_error:
            logger.warning(f"Knowledge base search failed: {kb_error}")
        
        system_prompt = f"{INTERNAL_SAFETY}\n\n{base_prompt}{knowledge_context}"
        temperature = agent.get("temperature", 0.7)
        max_tokens = agent.get("max_tokens", 150)
        
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
            # Return error TwiML indicating Groq is down
            return Response(
                content="<Response><Say voice='Polly.Joanna'>I'm having trouble connecting to my AI service. This is a Groq API issue, not a system problem. Please try again in a moment.</Say><Hangup/></Response>",
                media_type="application/xml"
            )
        
        # Save AI transcript
        await db.add_transcript(
            call_id=call_id,
            speaker="agent",
            text=ai_response
        )
        
        # Generate speech with Piper TTS
        audio_file = tts.generate_speech(ai_response)
        
        if not audio_file:
            logger.error("TTS failed")
            return Response(content="<Response><Say voice='Polly.Joanna'>Sorry, I'm having trouble speaking</Say><Hangup/></Response>", media_type="application/xml")
        
        # Copy to audio directory with unique filename
        import uuid
        audio_filename = f"{call_id}_{uuid.uuid4().hex[:8]}.wav"
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        shutil.copy2(audio_file, audio_path)
        
        # Cleanup original temp file
        try:
            os.unlink(audio_file)
        except:
            pass
        
        # Use ngrok URL to serve Piper audio
        base_url = os.getenv("VOICE_GATEWAY_URL", ngrok_public_url if ngrok_public_url else "")
        if base_url and not base_url.startswith("https://your-gateway"):
            audio_url = f"{base_url}/audio/{audio_filename}"
            
            # Continue conversation with another Gather using Piper TTS audio
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" timeout="10" speechTimeout="auto" speechModel="phone_call" action="{base_url}/gather/{call_id}" method="POST" language="en-US" hints="help, information, support, yes, no, more, details, thanks, goodbye">
        <Play>{audio_url}</Play>
    </Gather>
    <Say voice="Polly.Joanna">Thank you for calling. Goodbye!</Say>
    <Hangup/>
</Response>"""
        else:
            # Fallback to Polly voice
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{ai_response}</Say>
    <Hangup/>
</Response>"""
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error in gather callback for {call_id}: {e}", exc_info=True)
        return Response(
            content="<Response><Say>Sorry, there was an error</Say><Hangup/></Response>",
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
                    
                    # Send initial greeting
                    greeting = "Hello! How can I help you today?"
                    await send_ai_response(websocket, stream_sid, greeting, tts, db, call_id)
                
                elif event == "media":
                    # Audio data received
                    if not session:
                        continue
                    
                    # Skip processing if AI is speaking (prevent interruption)
                    if session.is_speaking:
                        continue
                    
                    # Decode mulaw audio
                    payload = data["media"]["payload"]
                    audio_data = base64.b64decode(payload)
                    
                    # Update last audio time
                    session.last_audio_time = datetime.now()
                    
                    # Detect if current chunk is silence
                    is_silence = session.detect_silence(audio_data)
                    session.update_silence_state(is_silence)
                    
                    # Add to buffer
                    session.add_audio_chunk(audio_data)
                    
                    # Process when:
                    # 1. We have sufficient audio AND
                    # 2. User has stopped speaking (500ms of silence)
                    if session.has_sufficient_audio() and session.get_silence_duration_ms() > 500:
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
        
        # Convert mulaw to linear PCM for Whisper
        audio_pcm = audioop.ulaw2lin(audio_mulaw, 2)  # 2 bytes per sample (16-bit)
        
        # Save to temp WAV file for Whisper
        import wave
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
            with wave.open(f, 'wb') as wav:
                wav.setnchannels(1)  # Mono
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(TWILIO_SAMPLE_RATE)
                wav.writeframes(audio_pcm)
        
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

GUARDRAILS - STAY ON TOPIC:
- You are a business assistant with a specific purpose defined in your system prompt
- DO NOT answer general knowledge questions (geography, history, trivia, celebrities, pop culture, etc.)
- DO NOT engage with random topics unrelated to your business purpose
- If asked off-topic questions, politely redirect: "I'm here to help with [your business purpose]. How can I assist you with that?"
- If user is clearly not interested or being disruptive, politely end the call
- Stay focused on your goal and don't get sidetracked

TIME FORMATTING FOR VOICE:
- NEVER write times as digits like "12:00" or "1:00" - the TTS will say "zero zero"
- ALWAYS write times in words: "twelve PM", "one AM", "two thirty PM", "ten fifteen AM"
- Examples: "nine AM", "three thirty PM", "twelve noon", "midnight"
- For half hours: "two thirty" not "2:30"
- For quarter hours: "three fifteen" or "quarter past three" not "3:15"

CALL ENDING PROTOCOL:
- When the conversation goal is complete or user wants to end, say: "Thanks for your time! If you have any questions later, feel free to reach out. You can hang up now. Goodbye!"
- After saying goodbye, the user will disconnect - DO NOT continue talking
- If user says goodbye/bye/I have to go, acknowledge and end: "Thank you, goodbye!"
- Do not keep the call going unnecessarily - respect the user's time"""
        
        base_prompt = session.agent_config.get("resolved_system_prompt") or session.agent_config.get("system_prompt", "You are a helpful AI assistant.")
        system_prompt = f"{INTERNAL_SAFETY}\n\n{base_prompt}"
        temperature = session.agent_config.get("temperature", 0.7)
        max_tokens = session.agent_config.get("max_tokens", 150)
        
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
        await send_ai_response(websocket, session.stream_sid, ai_response, tts, db, session.call_id)
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
):
    """Generate speech and send to Twilio"""
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
        
        # Normalize audio level to prevent clipping/distortion
        if sample_width == 2:  # 16-bit audio
            # Calculate max amplitude
            max_amplitude = audioop.max(audio_pcm, sample_width)
            if max_amplitude > 0:
                # Normalize to 90% of max range to prevent clipping
                target_max = int(32767 * 0.9)
                factor = target_max / max_amplitude
                if factor < 1.0:  # Only normalize if too loud
                    audio_pcm = audioop.mul(audio_pcm, sample_width, factor)
        
        # Convert to mulaw
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
            
            # Small delay to maintain timing (20ms per chunk)
            await asyncio.sleep(0.02)
        
        # Add small pause after AI finishes speaking
        await asyncio.sleep(0.3)
        
        logger.info(f"Sent AI speech to Twilio: {len(audio_mulaw)} bytes")
        
    except Exception as e:
        logger.error(f"Error sending AI response: {e}")


# ==================== STARTUP ====================

# Global ngrok URL storage
ngrok_public_url = None

@app.on_event("startup")
async def startup_event():
    """Initialize services and start ngrok tunnel"""
    global ngrok_public_url
    
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
