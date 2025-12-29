import logging
import threading
import queue
from typing import Optional
from config import config

try:
    import speech_recognition as sr
    import pyttsx3
    # Test PyAudio specifically
    import pyaudio
    VOICE_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    sr = None
    pyttsx3 = None
    pyaudio = None
    if "pyaudio" in str(e).lower():
        logging.warning("PyAudio not available. Install with: pip install pyaudio")
    else:
        logging.warning(f"Voice libraries not available: {e}. Install with: pip install SpeechRecognition pyttsx3 pyaudio")

class VoiceInterface:
    """Voice interface for the AI Assistant"""
    
    def __init__(self):
        if not VOICE_AVAILABLE:
            # Check which specific library is missing
            missing_libs = []
            try:
                import speech_recognition
            except ImportError:
                missing_libs.append("SpeechRecognition")
            try:
                import pyttsx3
            except ImportError:
                missing_libs.append("pyttsx3")
            try:
                import pyaudio
            except ImportError:
                missing_libs.append("pyaudio")
            
            if missing_libs:
                raise ImportError(f"Missing voice libraries: {', '.join(missing_libs)}. Install with: pip install {' '.join(missing_libs)}")
            else:
                raise ImportError("Could not find PyAudio; check installation")
        
        # Import modules again to ensure they're available in this scope
        import speech_recognition as sr
        import pyttsx3
            
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self._configure_tts()
        
        # Voice settings
        self.language = config.get('voice.language', 'en-US')
        self.timeout = config.get('voice.timeout', 5)
        
        # Threading for non-blocking TTS
        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()
        
        # Calibrate microphone
        self._calibrate_microphone()
        
        logging.info("Voice interface initialized")
    
    def _configure_tts(self):
        """Configure text-to-speech settings for Aura"""
        try:
            # Set voice properties for Aura (female voice)
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to find a female voice for Aura
                female_voice_found = False
                for voice in voices:
                    voice_name = voice.name.lower()
                    # Look for common female voice indicators
                    if any(indicator in voice_name for indicator in [
                        'female', 'zira', 'hazel', 'susan', 'linda', 'karen', 
                        'michelle', 'sarah', 'lisa', 'jennifer', 'maria'
                    ]):
                        self.tts_engine.setProperty('voice', voice.id)
                        female_voice_found = True
                        logging.info(f"Selected female voice: {voice.name}")
                        break
                
                if not female_voice_found:
                    # Fallback to first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)
                    logging.info(f"Using fallback voice: {voices[0].name}")
            
            # Set speech rate and volume for Aura (clear, professional female voice)
            self.tts_engine.setProperty('rate', 170)  # Slightly slower for clarity
            self.tts_engine.setProperty('volume', 0.9)  # Clear volume
            
            # Additional voice properties for better quality
            try:
                # Try to make voice more natural sounding
                self.tts_engine.setProperty('rate', 175)
            except:
                pass
            
        except Exception as e:
            logging.warning(f"Could not configure Aura TTS voice: {e}")
    
    def _calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            print("🎤 Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Microphone calibrated")
        except Exception as e:
            logging.warning(f"Microphone calibration failed: {e}")
    
    def _tts_worker(self):
        """Worker thread for text-to-speech"""
        while True:
            try:
                text = self.tts_queue.get()
                if text is None:  # Shutdown signal
                    break
                
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
            except Exception as e:
                logging.error(f"TTS error: {e}")
            finally:
                self.tts_queue.task_done()
    
    def get_input(self) -> Optional[str]:
        """Get voice input from user"""
        try:
            print("🎧 Listening... (speak now)")
            
            with self.microphone as source:
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=self.timeout, phrase_time_limit=10)
            
            print("🔄 Processing speech...")
            
            # Recognize speech using Google's service
            try:
                command = self.recognizer.recognize_google(audio, language=self.language)
                print(f"✅ Heard: {command}")
                return command
                
            except sr.UnknownValueError:
                self.output("Sorry, I didn't understand that. Please try again.")
                return None
                
            except sr.RequestError as e:
                logging.error(f"Speech recognition service error: {e}")
                self.output("Speech recognition service is unavailable.")
                return None
                
        except sr.WaitTimeoutError:
            print("⏰ No speech detected within timeout period")
            return None
            
        except Exception as e:
            logging.error(f"Voice input error: {e}")
            self.output("Voice input error occurred.")
            return None
    
    def output(self, text: str):
        """Output text via speech"""
        print(f"🗣️  {text}")
        
        # Add to TTS queue for non-blocking speech
        try:
            self.tts_queue.put(text, timeout=1)
        except queue.Full:
            logging.warning("TTS queue full, skipping speech output")
    
    def cleanup(self):
        """Cleanup voice interface resources"""
        try:
            # Stop TTS thread
            self.tts_queue.put(None)  # Shutdown signal
            self.tts_thread.join(timeout=2)
            
            # Stop TTS engine
            if hasattr(self, 'tts_engine'):
                self.tts_engine.stop()
                
        except Exception as e:
            logging.error(f"Voice interface cleanup error: {e}")

class TextInterface:
    """Text interface for the AI Assistant"""
    
    def __init__(self):
        logging.info("Text interface initialized")
    
    def get_input(self) -> Optional[str]:
        """Get text input from user"""
        try:
            command = input("\n💬 Enter command: ").strip()
            return command if command else None
        except (EOFError, KeyboardInterrupt):
            return "exit"
        except Exception as e:
            logging.error(f"Text input error: {e}")
            return None
    
    def output(self, text: str):
        """Output text to console"""
        print(f"🤖 {text}")
    
    def cleanup(self):
        """Cleanup text interface resources"""
        pass  # No cleanup needed for text interface
