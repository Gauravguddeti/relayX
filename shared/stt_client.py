"""
Speech-to-Text using Groq Whisper API or Local Whisper
Converts audio to text
"""
import numpy as np
from loguru import logger
import os
import tempfile
from typing import Optional
from groq import Groq


class STTClient:
    """Whisper-based Speech-to-Text client (Cloud or Local)"""
    
    def __init__(self, model_name: str = None):
        self.use_cloud = os.getenv("USE_CLOUD_STT", "true").lower() == "true"
        self.model_name = model_name or os.getenv("WHISPER_MODEL", "base")
        
        if self.use_cloud:
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
            audio_data: Raw audio bytes (mulaw/pcm)
            audio_file: Path to audio file
            language: Language code (default: en)
        
        Returns:
            Transcribed text or None
        """
        try:
            # If audio_data provided, save to temp file
            temp_file = None
            if audio_data:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(audio_data)
                    temp_file = f.name
                    audio_file = temp_file
            
            if not audio_file:
                logger.error("No audio data or file provided")
                return None
            
            # Use cloud or local transcription
            if self.use_cloud:
                # Groq Whisper API
                logger.debug(f"Transcribing with Groq API: {audio_file}")
                with open(audio_file, "rb") as file:
                    transcription = self.client.audio.transcriptions.create(
                        file=(os.path.basename(audio_file), file.read()),
                        model="whisper-large-v3",
                        language=language,
                        response_format="text"
                    )
                text = transcription.strip() if isinstance(transcription, str) else ""
            else:
                # Local Whisper
                logger.debug(f"Transcribing with local Whisper: {audio_file}")
                result = self.model.transcribe(
                    audio_file,
                    language=language,
                    fp16=False
                )
                text = result.get("text", "").strip()
            
            logger.info(f"Transcription: {text}")
            
            # Clean up temp file
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
