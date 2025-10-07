# tts.py

import pyttsx3
from config import VOICE_INDEX, SPEECH_RATE

# Initialize engine
engine = pyttsx3.init("sapi5")

# Configure voice and speed
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[VOICE_INDEX].id)
engine.setProperty('rate', SPEECH_RATE)

def speak(text: str):
    """Speaks the given text aloud."""
    print(f"INDICA says: {text}")
    engine.say(text)
    engine.runAndWait()