import os
import io
import json
import base64
import httpx
import asyncio
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class SarvamClient:
    """Client for Sarvam AI STT and TTS APIs"""
    
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        if not self.api_key:
            logger.warning("SARVAM_API_KEY not found in environment variables")
        
        self.base_url = "https://api.sarvam.ai"
        self.headers = {"api-subscription-key": self.api_key}

    async def text_to_speech(self, text: str, language_code: str = "hi-IN", speaker_gender: str = "Male") -> bytes:
        """
        Generate speech from text using Sarvam AI (Bulbul)
        
        Args:
            text: Text to speak
            language_code: Target language (hi-IN, bn-IN, kn-IN, ml-IN, mr-IN, od-IN, pa-IN, ta-IN, te-IN, en-IN)
            speaker_gender: "Male" or "Female"
            
        Returns:
            Audio bytes (WAV/PCM)
        """
        try:
            url = f"{self.base_url}/text-to-speech"
            
            payload = {
                "inputs": [text],
                "target_language_code": language_code,
                "speaker": "meera" if speaker_gender == "Female" else "amartya", # Default voices
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.5,
                "speech_sample_rate": 8000, # Match Twilio
                "enable_preprocessing": True,
                "model": "bulbul:v1"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers, timeout=10.0)
                
                if response.status_code != 200:
                    logger.error(f"Sarvam TTS error {response.status_code}: {response.text}")
                    return None
                
                data = response.json()
                if not data or not data.get("audios"):
                    return None
                
                # Decode base64 audio
                audio_b64 = data["audios"][0]
                return base64.b64decode(audio_b64)
                
        except Exception as e:
            logger.error(f"Sarvam TTS exception: {e}")
            return None

    async def speech_to_text(self, audio_data: bytes, language_code: str = "hi-IN") -> str:
        """
        Transcribe audio using Sarvam AI (Saarika)
        
        Args:
            audio_data: Audio bytes (WAV/MP3)
            language_code: Expected language or 'unknown'
            
        Returns:
            Transcribed text
        """
        try:
            url = f"{self.base_url}/speech-to-text"
            
            # Create multipart form data
            files = {'file': ('audio.wav', audio_data, 'audio/wav')}
            data = {
                'language_code': language_code,
                'model': 'saarika:v1' 
            }
            
            # Note: httpx handles multipart boundaries automatically
            async with httpx.AsyncClient() as client:
                # We need to NOT set Content-Type header manually for multipart
                headers_no_ct = {k: v for k, v in self.headers.items() if k.lower() != 'content-type'}
                
                response = await client.post(url, files=files, data=data, headers=headers_no_ct, timeout=10.0)
                
                if response.status_code != 200:
                    logger.error(f"Sarvam STT error {response.status_code}: {response.text}")
                    return ""
                
                result = response.json()
                return result.get("transcript", "")
                
        except Exception as e:
            logger.error(f"Sarvam STT exception: {e}")
            return ""

_sarvam_client = None

def get_sarvam_client():
    global _sarvam_client
    if not _sarvam_client:
        _sarvam_client = SarvamClient()
    return _sarvam_client
