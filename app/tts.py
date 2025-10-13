# tts.py - eSpeak-NG Implementation for Indian Languages

import subprocess
import platform
import os
from pathlib import Path
from typing import Optional

class ESpeakTTS:
    """
    eSpeak-NG TTS engine for Indian languages.
    100% offline and free.
    """
    
    def __init__(self, language: str = "en-in", rate: int = 150, pitch: int = 50):
        """
        Initialize eSpeak-NG TTS.
        
        Args:
            language: Language code (en-in, hi, ta, te, bn, gu, kn, ml, mr)
            rate: Speech rate (80-450, default 175, lower = slower)
            pitch: Voice pitch (0-99, default 50)
        """
        self.language_codes = {
            "en-IN": "en-in",      # English (India)
            "hi-IN": "hi",         # Hindi
            "ta-IN": "ta",         # Tamil
            "te-IN": "te",         # Telugu
            "bn-IN": "bn",         # Bengali
            "gu-IN": "gu",         # Gujarati
            "kn-IN": "kn",         # Kannada
            "ml-IN": "ml",         # Malayalam
            "mr-IN": "mr",         # Marathi
            "pa-IN": "pa",         # Punjabi
            "ur-IN": "ur",         # Urdu
        }
        
        self.language = self.language_codes.get(language, "en-in")
        self.rate = rate
        self.pitch = pitch
        self.espeak_path = self._find_espeak()
        
        if not self.espeak_path:
            print("⚠️  eSpeak-NG not found. Please install it first.")
            print("   Install from: speech/espeak-ng.msi")
    
    def _find_espeak(self) -> Optional[str]:
        """Find eSpeak-NG executable."""
        # Try common locations
        common_paths = [
            "C:\\Program Files\\eSpeak NG\\espeak-ng.exe",
            "C:\\Program Files (x86)\\eSpeak NG\\espeak-ng.exe",
            "espeak-ng",  # If in PATH
        ]
        
        for path in common_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return path
            except:
                continue
        
        return None
    
    def speak(self, text: str, save_to_file: Optional[str] = None) -> bool:
        """
        Speak the given text using eSpeak-NG.
        
        Args:
            text: Text to speak
            save_to_file: Optional WAV file path to save audio
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.espeak_path:
            print("❌ eSpeak-NG not available")
            return False
        
        if not text or not text.strip():
            return False
        
        try:
            # Build command
            cmd = [
                self.espeak_path,
                "-v", self.language,
                "-s", str(self.rate),
                "-p", str(self.pitch),
            ]
            
            # Add output file if specified
            if save_to_file:
                cmd.extend(["-w", save_to_file])
            
            # Add text
            cmd.append(text)
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"❌ eSpeak error: {result.stderr}")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ TTS timeout - text too long")
            return False
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return False
    
    def set_language(self, language: str):
        """Change TTS language."""
        self.language = self.language_codes.get(language, "en-in")
    
    def set_rate(self, rate: int):
        """Change speech rate (80-450)."""
        self.rate = max(80, min(450, rate))
    
    def set_pitch(self, pitch: int):
        """Change voice pitch (0-99)."""
        self.pitch = max(0, min(99, pitch))


# Main TTS interface for your app
class MaitriTTS:
    """
    Main TTS interface for Maitri AI.
    Uses eSpeak-NG for all languages.
    """
    
    def __init__(self, language: str = "en-IN", rate: int = 150, pitch: int = 50):
        """
        Initialize Maitri TTS.
        
        Args:
            language: Language code (en-IN, hi-IN, ta-IN, etc.)
            rate: Speech rate (80-450, default 150 = natural)
            pitch: Voice pitch (0-99, default 50 = neutral)
        """
        self.engine = ESpeakTTS(language=language, rate=rate, pitch=pitch)
        self.enabled = True
        
        # Test if working
        if self.engine.espeak_path:
            print(f"✅ TTS ready - Language: {language}, Rate: {rate}")
        else:
            print("⚠️  TTS not available - Please install eSpeak-NG")
            self.enabled = False
    
    def speak(self, text: str, save_to_file: Optional[str] = None) -> bool:
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            save_to_file: Optional file path to save audio
        
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False
        
        return self.engine.speak(text, save_to_file)
    
    def set_language(self, language: str):
        """Change TTS language."""
        self.engine.set_language(language)
        print(f"🌐 TTS language changed to: {language}")
    
    def set_rate(self, rate: int):
        """Change speech rate."""
        self.engine.set_rate(rate)
        print(f"⚡ Speech rate changed to: {rate}")
    
    def set_pitch(self, pitch: int):
        """Change voice pitch."""
        self.engine.set_pitch(pitch)
        print(f"🎵 Voice pitch changed to: {pitch}")
    
    def toggle(self, enabled: bool):
        """Enable or disable TTS."""
        self.enabled = enabled


# Legacy function for backwards compatibility
def speak(text: str):
    """Simple speak function - maintains compatibility with old code."""
    tts = MaitriTTS()
    tts.speak(text)


# Test function
if __name__ == "__main__":
    print("🎙️  Testing Maitri TTS\n")
    
    tts = MaitriTTS(language="hi-IN", rate=150)
    # Test Hindi
    print("\nTesting Hindi...")
    tts.set_language("hi-IN")
    tts.speak("नमस्ते! मैं मैत्री हूं, आपका एआई साथी। आप कैसे हैं?")
    