"""
Speech-to-Text using Deepgram, Groq Whisper API or Local Whisper
Converts audio to text
"""
import numpy as np
from loguru import logger
import os
import tempfile
from typing import Optional
from groq import Groq
import requests
import time
import json


class STTClient:
    """Speech-to-Text client supporting Deepgram, Groq Whisper, or Local Whisper"""
    
    def __init__(self, model_name: str = None):
        self.use_cloud = os.getenv("USE_CLOUD_STT", "true").lower() == "true"
        self.stt_provider = os.getenv("STT_PROVIDER", "groq").lower()  # deepgram, groq, assemblyai, or local
        self.model_name = model_name or os.getenv("WHISPER_MODEL", "base")
        
        if self.use_cloud:
            if self.stt_provider == "deepgram":
                # Use Deepgram API - Best for real-time phone calls
                api_key = os.getenv("DEEPGRAM_API_KEY")
                if not api_key:
                    raise ValueError("DEEPGRAM_API_KEY not found in environment")
                self.deepgram_key = api_key
                self.deepgram_url = "https://api.deepgram.com/v1/listen"
                logger.info("Using Deepgram API (cloud) - Best for real-time")
            elif self.stt_provider == "assemblyai":
                # Use AssemblyAI API
                api_key = os.getenv("ASSEMBLYAI_API_KEY")
                if not api_key:
                    raise ValueError("ASSEMBLYAI_API_KEY not found in environment")
                self.assemblyai_key = api_key
                self.assemblyai_upload_url = "https://api.assemblyai.com/v2/upload"
                self.assemblyai_transcript_url = "https://api.assemblyai.com/v2/transcript"
                logger.info("Using AssemblyAI API (cloud)")
            else:
                # Use Groq's Whisper API (FREE, fast)
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY not found in environment")
                self.client = Groq(api_key=api_key)
                logger.info("Using Groq Whisper API (cloud)")
        else:
            # Use local Whisper model
            import whisper
            logger.info(f"Loading local Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            logger.info("Local Whisper model loaded successfully")
    
    def transcribe_audio(
        self, 
        audio_data: Optional[bytes] = None,
        audio_file: Optional[str] = None,
        language: str = "en"
    ) -> Optional[str]:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Raw audio bytes (WAV format for in-memory processing)
            audio_file: Path to audio file
            language: Language code (default: en)
        
        Returns:
            Transcribed text or None
        """
        try:
            # IN-MEMORY PROCESSING: No temp files if audio_data provided
            temp_file = None
            audio_bytes = None
            
            if audio_data and not audio_file:
                # Use audio_data directly (already in WAV format from voice gateway)
                audio_bytes = audio_data
            elif audio_file:
                # Read from file if provided
                with open(audio_file, "rb") as f:
                    audio_bytes = f.read()
            
            if not audio_bytes and not audio_file:
                logger.error("No audio data or file provided")
                return None
            
            # Use cloud or local transcription
            if self.use_cloud:
                if self.stt_provider == "deepgram":
                    # Deepgram API - Fast and accurate for phone calls
                    logger.debug(f"Transcribing with Deepgram (in-memory)")
                    
                    headers = {
                        "Authorization": f"Token {self.deepgram_key}",
                        "Content-Type": "audio/wav"
                    }
                    
                    # Deepgram parameters optimized for fast phone calls
                    params = {
                        "model": "nova-2-phonecall",  # Phone-specific model - faster + better for telephony
                        "language": language,
                        "smart_format": "true",
                        "punctuate": "false",  # Skip punctuation for speed
                        "diarize": "false",
                        "filler_words": "false",
                        "profanity_filter": "false",
                        "encoding": "linear16",  # Match our WAV format
                        "sample_rate": "16000"  # Match our upsampled rate
                    }
                    
                    # Send audio bytes directly (no file I/O)
                    response = requests.post(
                        self.deepgram_url,
                        headers=headers,
                        params=params,
                        data=audio_bytes,
                        timeout=10
                    )
                    
                    if response.status_code != 200:
                        logger.error(f"Deepgram error: {response.status_code} - {response.text}")
                        return None
                    
                    result = response.json()
                    text = ""
                    try:
                        text = result["results"]["channels"][0]["alternatives"][0]["transcript"]
                    except (KeyError, IndexError):
                        logger.warning(f"No transcript in Deepgram response: {result}")
                        return None
                
                elif self.stt_provider == "assemblyai":
                    # AssemblyAI API
                    logger.debug(f"Transcribing with AssemblyAI: {audio_file}")
                    
                    # Upload audio file
                    headers = {"authorization": self.assemblyai_key}
                    with open(audio_file, "rb") as f:
                        upload_response = requests.post(
                            self.assemblyai_upload_url,
                            headers=headers,
                            data=f
                        )
                    
                    if upload_response.status_code != 200:
                        logger.error(f"AssemblyAI upload failed: {upload_response.text}")
                        return None
                    
                    audio_url = upload_response.json()["upload_url"]
                    
                    # Request transcription
                    transcript_request = {
                        "audio_url": audio_url,
                        "language_code": language
                    }
                    transcript_response = requests.post(
                        self.assemblyai_transcript_url,
                        json=transcript_request,
                        headers=headers
                    )
                    
                    if transcript_response.status_code != 200:
                        logger.error(f"AssemblyAI transcription request failed: {transcript_response.text}")
                        return None
                    
                    transcript_id = transcript_response.json()["id"]
                    
                    # Poll for result
                    polling_url = f"{self.assemblyai_transcript_url}/{transcript_id}"
                    max_retries = 60
                    for _ in range(max_retries):
                        polling_response = requests.get(polling_url, headers=headers)
                        result = polling_response.json()
                        
                        if result["status"] == "completed":
                            text = result["text"].strip()
                            break
                        elif result["status"] == "error":
                            logger.error(f"AssemblyAI transcription error: {result.get('error')}")
                            return None
                        
                        time.sleep(0.5)
                    else:
                        logger.error("AssemblyAI transcription timeout")
                        return None
                else:
                    # Groq Whisper API (IN-MEMORY)
                    logger.debug(f"Transcribing with Groq API (in-memory)")
                    # Send audio bytes directly without file
                    # CRITICAL: Detailed prompt helps Whisper with phone call audio quality
                    transcription = self.client.audio.transcriptions.create(
                        file=("audio.wav", audio_bytes),
                        model="whisper-large-v3",
                        language=language,
                        response_format="text",
                        prompt="Phone call. Common: what's up, hello, yes, yeah, no, okay, I'm down, sounds good, four to five, bye. Numbers like '4-5' mean small amounts."
                    )
                    text = transcription.strip() if isinstance(transcription, str) else ""
            else:
                # Local Whisper (needs temp file fallback)
                if audio_bytes and not audio_file:
                    # Create temp file only for local Whisper
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        f.write(audio_bytes)
                        temp_file = f.name
                    audio_file = temp_file
                
                logger.debug(f"Transcribing with local Whisper: {audio_file}")
                result = self.model.transcribe(
                    audio_file,
                    language=language,
                    fp16=False
                )
                text = result.get("text", "").strip()
            
            logger.info(f"Transcription: {text}")
            
            # Clean up temp file (only if we created one)
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)
            
            return text if text else None
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return None
    
    def transcribe_numpy(self, audio_array: np.ndarray, sample_rate: int = 16000) -> Optional[str]:
        """
        Transcribe from numpy array (useful for streaming)
        
        Args:
            audio_array: Numpy array of audio samples
            sample_rate: Sample rate in Hz
        
        Returns:
            Transcribed text
        """
        try:
            # Whisper expects audio at 16kHz
            if sample_rate != 16000:
                # Resample if needed (requires librosa or scipy)
                from scipy import signal
                num_samples = int(len(audio_array) * 16000 / sample_rate)
                audio_array = signal.resample(audio_array, num_samples)
            
            # Normalize to [-1, 1]
            if audio_array.dtype == np.int16:
                audio_array = audio_array.astype(np.float32) / 32768.0
            
            result = self.model.transcribe(audio_array, fp16=False)
            text = result.get("text", "").strip()
            
            if text:
                logger.info(f"Transcription: {text}")
            
            return text if text else None
            
        except Exception as e:
            logger.error(f"STT numpy error: {e}")
            return None


# Global instance
stt_client = None

def get_stt_client() -> STTClient:
    """Get or create global STT client"""
    global stt_client
    if stt_client is None:
        stt_client = STTClient()
    return stt_client
