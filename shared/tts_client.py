"""
Text-to-Speech using Sarvam AI
Cloud-based TTS with excellent Indian language support
"""
from loguru import logger
import os
import re
import io
import wave
from typing import Optional
from shared.sarvam_client import get_sarvam_client


class TTSClient:
    """TTS client for generating speech using Sarvam AI"""
    
    def __init__(self, model_name: str = None):
        logger.info("Initializing Sarvam TTS Client...")
        self.sarvam_client = get_sarvam_client()
        logger.info("✅ Sarvam TTS ready")
    
    async def generate_speech_bytes(
        self,
        text: str,
        speaker: Optional[str] = None,
        language: str = "en"
    ) -> Optional[bytes]:
        """
        Generate speech and return as bytes
        
        Args:
            text: Text to convert
            speaker: Speaker voice (Male/Female)
            language: Language code (en, hi, mr, bn, ta, te, kn, ml, pa, gu, or)
        
        Returns:
            Audio bytes (WAV format)
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided to TTS")
                return None
            
            # Map language code to Sarvam format
            sarvam_code = language if "-" in language else f"{language}-IN"
            
            # Determine speaker gender
            speaker_gender = speaker if speaker in ["Male", "Female"] else "Male"
            
            logger.debug(f"Generating speech: {text[:50]}... (lang={sarvam_code})")
            
            raw_audio = await self.sarvam_client.text_to_speech(
                text, 
                language_code=sarvam_code,
                speaker_gender=speaker_gender
            )
            
            if raw_audio:
                # Sarvam returns raw PCM audio at 8kHz, 16-bit mono
                # Wrap it in a WAV container for compatibility with voice gateway
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(8000)  # 8kHz (Sarvam setting)
                    wav_file.writeframes(raw_audio)
                
                wav_bytes = wav_buffer.getvalue()
                logger.info(f"✅ Sarvam TTS generated {len(wav_bytes)} bytes WAV")
                return wav_bytes
            else:
                logger.warning(f"Sarvam TTS returned no audio for: {text[:30]}...")
                return None
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    async def generate_speech_streaming(self, text: str, language: str = "en") -> list:
        """
        Generate speech sentence-by-sentence for streaming
        Returns list of (sentence_text, audio_bytes) tuples
        """
        try:
            # Split text into sentences
            sentences = re.split(r'([.!?]+(?:\s+|$))', text)
            
            # Reconstruct sentences with punctuation
            sentence_list = []
            for i in range(0, len(sentences) - 1, 2):
                if sentences[i].strip():
                    sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                    sentence_list.append(sentence.strip())
            
            # Handle case where last item is text without punctuation
            if len(sentences) % 2 == 1 and sentences[-1].strip():
                sentence_list.append(sentences[-1].strip())
            
            # Generate audio for each sentence
            results = []
            for sentence in sentence_list:
                if not sentence or len(sentence) < 2:
                    continue
                
                audio_bytes = await self.generate_speech_bytes(sentence, language=language)
                if audio_bytes:
                    results.append((sentence, audio_bytes))
            
            return results
            
        except Exception as e:
            logger.error(f"Streaming TTS error: {e}")
            # Fallback: return single chunk with all text
            audio_bytes = await self.generate_speech_bytes(text, language=language)
            return [(text, audio_bytes)] if audio_bytes else []
    
    def list_speakers(self) -> list:
        """List available speakers"""
        return ["Male", "Female"]


# Global instance
tts_client = None


def get_tts_client() -> TTSClient:
    """Get or create global TTS client instance"""
    global tts_client
    if tts_client is None:
        tts_client = TTSClient()
    return tts_client
