"""
Text-to-Speech using Piper TTS
Fast, lightweight, open-source TTS
"""
from loguru import logger
import os
import tempfile
from typing import Optional
import wave
import io
from piper import PiperVoice


class TTSClient:
    """TTS client for generating speech using Piper TTS"""
    
    def __init__(self, model_name: str = None):
        # Use Piper TTS - fast and lightweight
        logger.info("Loading Piper TTS...")
        
        # Use American English voice - smoother and more natural sounding
        # en_US-ryan-medium: Clear American male voice (best quality/naturalness)
        voice_name = "en_US-ryan-medium"
        model_path = os.path.join(os.path.expanduser("~"), ".local", "share", "piper", f"{voice_name}.onnx")
        
        if not os.path.exists(model_path):
            logger.info(f"Downloading high-quality Piper voice: {voice_name}")
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # Download from correct Hugging Face mirror
            import urllib.request
            base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/{voice_name}.onnx"
            config_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/{voice_name}.onnx.json"
            
            logger.info("Downloading model files (this may take a moment)...")
            try:
                urllib.request.urlretrieve(base_url, model_path)
                urllib.request.urlretrieve(config_url, f"{model_path}.json")
                logger.info("✅ Voice model downloaded")
            except Exception as e:
                logger.error(f"Failed to download model: {e}")
                logger.info("Falling back to lower quality voice")
                # Fallback to low quality American voice if high quality fails
                voice_name = "en_US-ryan-low"
                model_path = os.path.join(os.path.expanduser("~"), ".local", "share", "piper", f"{voice_name}.onnx")
                base_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/low/{voice_name}.onnx"
                config_url = f"https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/low/{voice_name}.onnx.json"
                urllib.request.urlretrieve(base_url, model_path)
                urllib.request.urlretrieve(config_url, f"{model_path}.json")
        
        self.voice = PiperVoice.load(model_path)
        logger.info("✅ Piper TTS ready")
    
    def generate_speech(
        self,
        text: str,
        output_file: Optional[str] = None,
        speaker: Optional[str] = None,
        language: str = "en"
    ) -> Optional[str]:
        """
        Generate speech from text
        
        Args:
            text: Text to convert to speech
            output_file: Output file path (if None, creates temp file)
            speaker: Speaker voice (ignored for Piper)
            language: Language code (ignored for Piper)
        
        Returns:
            Path to generated audio file
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided to TTS")
                return None
            
            # Create output file if not provided
            if not output_file:
                fd, output_file = tempfile.mkstemp(suffix=".wav")
                os.close(fd)
            
            logger.debug(f"Generating speech: {text[:50]}...")
            
            # Clean text - remove excessive processing that causes breaking
            enhanced_text = self._enhance_text_naturalness(text)
            
            # Generate speech with Piper - use clean synthesis
            audio_chunks = []
            try:
                # Synthesize audio (Piper doesn't support length_scale in this version)
                for audio_chunk in self.voice.synthesize(enhanced_text):
                    audio_chunks.append(audio_chunk)
            except Exception as e:
                logger.error(f"Piper synthesis error: {e}")
                # Fallback: try with original text if enhancement caused issues
                audio_chunks = []
                for audio_chunk in self.voice.synthesize(text):
                    audio_chunks.append(audio_chunk)
            
            # Combine chunks and write WAV file with consistent format
            if audio_chunks:
                # Get audio properties from first chunk
                sample_rate = audio_chunks[0].sample_rate
                sample_width = audio_chunks[0].sample_width
                channels = audio_chunks[0].sample_channels
                
                # Combine all audio data
                combined_audio = b''.join(chunk.audio_int16_bytes for chunk in audio_chunks)
                
                # Write WAV file with proper headers and consistent format
                with wave.open(output_file, "wb") as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    # Ensure we write complete frames
                    wav_file.writeframes(combined_audio)
                
                # Verify file was created properly
                if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                    logger.error(f"TTS file generation failed: {output_file}")
                    return None
            
            logger.info(f"Speech generated with Piper TTS: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_speech_bytes(
        self,
        text: str,
        speaker: Optional[str] = None,
        language: str = "en"
    ) -> Optional[bytes]:
        """
        Generate speech and return as bytes
        
        Args:
            text: Text to convert
            speaker: Speaker voice
            language: Language code
        
        Returns:
            Audio bytes (WAV format)
        """
        try:
            # Generate to temp file
            audio_file = self.generate_speech(text, speaker=speaker, language=language)
            
            if not audio_file:
                return None
            
            # Read bytes
            with open(audio_file, "rb") as f:
                audio_bytes = f.read()
            
            # Clean up
            if os.path.exists(audio_file):
                os.unlink(audio_file)
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"TTS bytes error: {e}")
            return None
    
    def generate_speech_streaming(self, text: str) -> list:
        """
        Generate speech sentence-by-sentence for streaming
        Returns list of (sentence_text, audio_bytes) tuples
        This enables lower latency by streaming first sentence while generating rest
        """
        import re
        
        try:
            # Split text into sentences
            # Match periods, exclamation marks, question marks followed by space/end
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
                
                # Generate audio bytes for this sentence (IN-MEMORY)
                audio_bytes = self._generate_sentence_bytes(sentence)
                if audio_bytes:
                    results.append((sentence, audio_bytes))
            
            return results
            
        except Exception as e:
            logger.error(f"Streaming TTS error: {e}")
            # Fallback: return single chunk with all text
            audio_bytes = self.generate_speech_bytes(text)
            return [(text, audio_bytes)] if audio_bytes else []
    
    def _generate_sentence_bytes(self, text: str) -> Optional[bytes]:
        """Generate audio bytes for a single sentence (in-memory, no file I/O)"""
        try:
            # Clean text
            enhanced_text = self._enhance_text_naturalness(text)
            
            # Generate audio chunks
            audio_chunks = []
            for audio_chunk in self.voice.synthesize(enhanced_text):
                audio_chunks.append(audio_chunk)
            
            if not audio_chunks:
                return None
            
            # Get audio properties
            sample_rate = audio_chunks[0].sample_rate
            sample_width = audio_chunks[0].sample_width
            channels = audio_chunks[0].sample_channels
            
            # Combine all audio data
            combined_audio = b''.join(chunk.audio_int16_bytes for chunk in audio_chunks)
            
            # Create WAV in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(sample_width)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(combined_audio)
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            logger.error(f"Sentence TTS error: {e}")
            return None
    
    def list_speakers(self) -> list:
        """List available speakers (not supported by Piper)"""
        return []
    
    def _enhance_text_naturalness(self, text: str) -> str:
        """Clean and prepare text for natural speech - keep it simple"""
        import re
        
        # Clean up text for more natural speech
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure proper spacing after punctuation
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([,;:])([^\s])', r'\1 \2', text)
        
        # Remove any markdown or special formatting
        text = text.replace('*', '').replace('_', '').replace('#', '')
        
        # Add subtle pauses for more natural phrasing
        # Replace dashes with commas for better pacing
        text = text.replace(' - ', ', ')
        
        # Add micro-pauses after conjunctions for natural flow
        text = re.sub(r'\b(and|but|or|so)\b(?!,)', r'\1,', text)
        
        return text.strip()


# Global instance
tts_client = None


def get_tts_client() -> TTSClient:
    """Get or create global TTS client instance"""
    global tts_client
    if tts_client is None:
        tts_client = TTSClient()
    return tts_client
