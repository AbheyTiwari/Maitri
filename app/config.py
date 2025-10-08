# config.py - Centralized Configuration Management

import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "Maitri AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "True").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SESSION_COOKIE_NAME: str = "maitri_session"
    
    # Database
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "maitri_ai")
    
    # Collections
    USERS_COLLECTION: str = "users"
    CONVERSATIONS_COLLECTION: str = "conversations"
    MEMORIES_COLLECTION: str = "user_memories"
    SESSIONS_COLLECTION: str = "sessions"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",  # For frontend development
    ]
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3:mini")
    OLLAMA_TIMEOUT: int = 30
    
    # AI Configuration
    MAX_CHAT_HISTORY: int = 20
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    
    # Emotion Detection
    EMOTION_DETECTION_ENABLED: bool = True
    EMOTION_DETECTION_INTERVAL: int = 100  # milliseconds
    DEEPFACE_BACKEND: str = "opencv"  # Options: opencv, ssd, dlib, mtcnn, retinaface
    ENFORCE_DETECTION: bool = False  # Set True for strict face detection
    
    # Memory Management
    MEMORY_IMPORTANCE_THRESHOLD: int = 3  # Store memories with importance >= 3
    MAX_MEMORIES_PER_THEME: int = 10
    MEMORY_RETENTION_DAYS: int = 90  # Delete old memories after 90 days
    
    # Speech Recognition
    SPEECH_RECOGNITION_LANG: str = "en-IN"
    TTS_RATE: float = 0.9
    TTS_PITCH: float = 1.0
    TTS_VOLUME: float = 1.0
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    LOGIN_RATE_LIMIT: str = "5/minute"
    SIGNUP_RATE_LIMIT: str = "3/minute"
    CHAT_RATE_LIMIT: str = "60/minute"
    
    # File Upload (for future features)
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".txt"]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "maitri_ai.log"
    
    # Session Management
    SESSION_TIMEOUT_MINUTES: int = 60
    CLEANUP_SESSIONS_HOURS: int = 24
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds
    WS_MAX_CONNECTIONS_PER_USER: int = 3
    
    # Mental Health Resources
    CRISIS_CONTACTS: dict = {
        "India": {
            "AASRA": "91-22-27546669",
            "Vandrevala Foundation": "1860-2662-345",
            "iCall": "9152987821",
            "Sneha": "044-24640050"
        }
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Emotion configurations
EMOTION_COLORS = {
    'happy': '#10b981',
    'sad': '#3b82f6',
    'angry': '#ef4444',
    'fearful': '#f59e0b',
    'surprised': '#8b5cf6',
    'disgusted': '#ec4899',
    'neutral': '#6b7280'
}

EMOTION_STRESS_LEVELS = {
    'happy': {'level': 'Low', 'score': 20},
    'neutral': {'level': 'Low', 'score': 30},
    'surprised': {'level': 'Moderate', 'score': 50},
    'disgusted': {'level': 'Moderate', 'score': 60},
    'sad': {'level': 'High', 'score': 80},
    'angry': {'level': 'High', 'score': 90},
    'fearful': {'level': 'Very High', 'score': 100}
}

# Theme keywords for memory extraction
THEME_KEYWORDS = {
    'work': ['work', 'job', 'career', 'office', 'colleague', 'boss', 'project', 'meeting', 'deadline'],
    'family': ['family', 'parent', 'mother', 'father', 'sibling', 'brother', 'sister', 'child', 'relative'],
    'relationship': ['relationship', 'partner', 'girlfriend', 'boyfriend', 'spouse', 'love', 'breakup', 'dating'],
    'mental_health': ['anxiety', 'depression', 'stress', 'therapy', 'mental', 'overwhelm', 'panic', 'worry'],
    'sleep': ['sleep', 'insomnia', 'tired', 'exhausted', 'rest', 'nightmare', 'dream', 'fatigue'],
    'health': ['health', 'doctor', 'medicine', 'pain', 'sick', 'hospital', 'illness', 'treatment'],
    'education': ['study', 'exam', 'school', 'college', 'university', 'class', 'homework', 'grade'],
    'finance': ['money', 'debt', 'salary', 'budget', 'savings', 'expense', 'financial', 'loan'],
    'social': ['friend', 'social', 'lonely', 'isolated', 'party', 'gathering', 'connection'],
    'hobbies': ['hobby', 'interest', 'passion', 'sport', 'music', 'art', 'reading', 'gaming']
}

# System prompts for different emotional states
EMOTION_SPECIFIC_PROMPTS = {
    'angry': """
When responding to someone who is angry:
- Validate their frustration without judgment
- Use grounding language: "That's really frustrating" vs "I understand you're upset"
- Acknowledge any injustice they're feeling
- Don't minimize or rush to calm them down
- Ask what boundary was crossed or what expectation was violated
    """,
    
    'sad': """
When responding to someone who is sad:
- Use softer, gentler language
- Acknowledge the pain directly: "This really hurts" vs "That's unfortunate"
- Give space for grief without rushing to silver linings
- Sit with the sadness rather than trying to fix it
- Ask what they're grieving (loss, disappointment, etc.)
    """,
    
    'fearful': """
When responding to someone who is fearful:
- Use reassuring but not dismissive language
- Acknowledge their courage in facing this fear
- Ground them: "Right now, in this moment, you're safe"
- Validate that fear is a natural protective response
- Ask what specifically feels threatening
    """,
    
    'happy': """
When responding to someone who is happy:
- Match their positive energy authentically
- Celebrate with them genuinely without overdoing it
- Ask them to savor the moment: "What's the best part?"
- Encourage them to notice what contributed to this feeling
- Help them anchor this positive experience
    """,
    
    'neutral': """
When responding to someone in a neutral state:
- Use balanced, attentive language
- Don't force emotion where there isn't any
- Ask open questions to understand their state
- Create space for whatever wants to emerge naturally
- Be curious without being intrusive
    """
}

# Conversation starters
CONVERSATION_STARTERS = [
    "How are you feeling today?",
    "What's been on your mind lately?",
    "Is there anything you'd like to talk about?",
    "How has your day been going?",
    "What brought you here today?"
]

# Wellness tips by emotion
WELLNESS_TIPS = {
    'stressed': [
        "Try the 4-7-8 breathing technique: breathe in for 4, hold for 7, out for 8",
        "Take a 5-minute walk outside if possible",
        "Write down 3 things you can control right now"
    ],
    'sad': [
        "Reach out to a friend or family member",
        "Allow yourself to feel without judgment",
        "Do something small that usually brings you comfort"
    ],
    'anxious': [
        "Ground yourself: name 5 things you can see, 4 you can touch, 3 you can hear",
        "Practice progressive muscle relaxation",
        "Remind yourself: 'This feeling will pass'"
    ]
}

# Export settings
__all__ = ['settings', 'EMOTION_COLORS', 'EMOTION_STRESS_LEVELS', 'THEME_KEYWORDS', 
           'EMOTION_SPECIFIC_PROMPTS', 'CONVERSATION_STARTERS', 'WELLNESS_TIPS']