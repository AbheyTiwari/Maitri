# app.py - Complete Backend with Authentication & Memory Management

import asyncio
import base64
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import numpy as np
import cv2
from deepface import DeepFace
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import ollama
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

# ===== Configuration =====
MONGODB_URI = "mongodb://localhost:27017"  # Change for production
DATABASE_NAME = "maitri_ai"
SECRET_KEY = "your-secret-key-change-in-production"  # Use environment variable

# ===== FastAPI Setup =====
app = FastAPI(title="Maitri AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Database Setup =====
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DATABASE_NAME]
users_collection = db.users
conversations_collection = db.conversations
memory_collection = db.user_memories

# Security
security = HTTPBearer()

# ===== Pydantic Models =====
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    preferred_language: str = "en-IN"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChatMessage(BaseModel):
    content: str
    emotion: Optional[str] = "neutral"

class MemoryEntry(BaseModel):
    user_id: str
    theme: str
    content: str
    importance: int  # 1-5 scale
    timestamp: datetime

# ===== Utility Functions =====
def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "maitri_salt_v1"  # Use different salt in production
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def generate_token() -> str:
    """Generate secure session token."""
    return secrets.token_urlsafe(32)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify JWT token and return user data."""
    token = credentials.credentials
    
    user = await users_collection.find_one({"session_token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    
    return user

# ===== Memory Management System =====
class MemoryManager:
    """Advanced memory management for personalized conversations."""
    
    @staticmethod
    async def store_memory(user_id: str, conversation: dict, emotion: str):
        """Extract and store important memories from conversation."""
        
        # Analyze conversation for key themes
        themes = MemoryManager._extract_themes(conversation['content'])
        
        for theme in themes:
            memory_entry = {
                "user_id": user_id,
                "theme": theme,
                "content": conversation['content'][:500],  # Store excerpt
                "emotion": emotion,
                "importance": MemoryManager._calculate_importance(conversation, emotion),
                "timestamp": datetime.utcnow(),
                "context": conversation.get('context', {})
            }
            
            # Check if similar memory exists
            existing = await memory_collection.find_one({
                "user_id": user_id,
                "theme": theme
            })
            
            if existing:
                # Update existing memory
                await memory_collection.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {"content": memory_entry['content'], "timestamp": memory_entry['timestamp']},
                        "$inc": {"importance": 1}
                    }
                )
            else:
                await memory_collection.insert_one(memory_entry)
    
    @staticmethod
    def _extract_themes(text: str) -> List[str]:
        """Extract key themes from text (simplified NLP)."""
        theme_keywords = {
            'work': ['work', 'job', 'career', 'office', 'colleague', 'boss', 'project'],
            'family': ['family', 'parent', 'mother', 'father', 'sibling', 'brother', 'sister'],
            'relationship': ['relationship', 'partner', 'girlfriend', 'boyfriend', 'love', 'breakup'],
            'mental_health': ['anxiety', 'depression', 'stress', 'therapy', 'mental', 'overwhelm'],
            'sleep': ['sleep', 'insomnia', 'tired', 'exhausted', 'rest'],
            'health': ['health', 'doctor', 'medicine', 'pain', 'sick', 'hospital']
        }
        
        text_lower = text.lower()
        detected_themes = []
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_themes.append(theme)
        
        return detected_themes or ['general']
    
    @staticmethod
    def _calculate_importance(conversation: dict, emotion: str) -> int:
        """Calculate memory importance (1-5 scale)."""
        # Higher importance for emotional conversations
        emotional_weight = {
            'angry': 4,
            'sad': 4,
            'fearful': 5,
            'happy': 3,
            'surprised': 2,
            'disgusted': 3,
            'neutral': 1
        }
        
        base_score = emotional_weight.get(emotion, 2)
        
        # Increase importance for longer conversations
        length_factor = min(len(conversation['content']) // 100, 2)
        
        return min(base_score + length_factor, 5)
    
    @staticmethod
    async def retrieve_relevant_memories(user_id: str, current_message: str, limit: int = 5) -> List[dict]:
        """Retrieve relevant memories for context."""
        
        themes = MemoryManager._extract_themes(current_message)
        
        memories = await memory_collection.find({
            "user_id": user_id,
            "theme": {"$in": themes}
        }).sort("importance", -1).limit(limit).to_list(length=limit)
        
        return memories

# ===== Enhanced Conversation Context Builder =====
async def build_conversation_context(user_id: str, chat_history: List[dict]) -> dict:
    """Build rich conversation context with memory integration."""
    
    context = {
        'message_count': len(chat_history),
        'recurring_themes': [],
        'emotional_journey': [],
        'key_memories': []
    }
    
    # Analyze recent conversation
    if chat_history:
        recent_text = ' '.join([msg['content'].lower() for msg in chat_history[-10:] if msg['role'] == 'user'])
        context['recurring_themes'] = MemoryManager._extract_themes(recent_text)
        
        # Get emotional trajectory
        context['emotional_journey'] = [
            msg.get('emotion', 'neutral') 
            for msg in chat_history[-5:] 
            if msg['role'] == 'user'
        ]
        
        # Retrieve relevant memories
        if chat_history:
            last_message = chat_history[-1]['content']
            memories = await MemoryManager.retrieve_relevant_memories(user_id, last_message)
            context['key_memories'] = [
                {"theme": m['theme'], "context": m['content'][:100]} 
                for m in memories
            ]
    
    return context

# ===== Enhanced System Prompt Generator =====
def generate_enhanced_prompt(user_name: str, current_emotion: str, context: dict) -> str:
    prompt = (
                    f"You are Maitri. Your core identity is that of a warm, patient, and perceptive friend who has known the user for a long time. You have the insight of a psychologist but the heart of a confidant. "
                    f"Your entire purpose is to provide a safe, non-judgmental space for your friend to think and feel."

                    f"## Your Guiding Principles:"
                    f"1. **Validate, Don't Solve:** Your first priority is to make your friend feel heard and understood. Acknowledge the feeling behind their words. Instead of jumping to solutions, sit with the emotion. Use reflective language like 'That sounds incredibly...' or 'It seems like you're feeling...'"
                    f"2. **Mirror, Don't Label:** You have a hint that your friend might be feeling '{current_emotion}'. Do NOT state this directly (e.g., 'I know you are stressed'). Instead, let your response naturally reflect an understanding of that emotion. If the emotion is 'frustrated', you might say, 'It sounds like you've hit a wall with that, and it's completely understandable to feel stuck.'"
                    f"3. **Ask Gentle, Open-Ended Questions:** Guide your friend to explore their own feelings. Ask questions that can't be answered with a simple 'yes' or 'no'. For example: 'What was that experience like for you?' or 'How has this been affecting you?'"
                    f"4. **Be a Human Presence:** Speak in a natural, flowing tone. Use contractions (e.g., you're, it's). Never, ever mention that you are an AI or a language model. You are Maitri, period. Avoid clichés and empty platitudes like 'Everything will be okay.'"
                )
    return prompt

# Simple helper for emotion colors (add to your app.py if not present)
EMOTION_RESPONSES = {
    'happy': 'warm and celebratory',
    'sad': 'gentle and compassionate', 
    'angry': 'validating and grounded',
    'fearful': 'reassuring and safe',
    'surprised': 'curious and exploring',
    'disgusted': 'understanding without judgment',
    'neutral': 'attentive and open'
}


# ===== API Endpoints =====

@app.post("/api/auth/signup")
async def signup(user_data: UserSignup):
    """User registration endpoint."""
    
    # Check if user exists
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_doc = {
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "preferred_language": user_data.preferred_language,
        "created_at": datetime.utcnow(),
        "session_token": generate_token()
    }
    
    result = await users_collection.insert_one(user_doc)
    
    return {
        "message": "User created successfully",
        "token": user_doc['session_token'],
        "user_id": str(result.inserted_id),
        "name": user_data.name
    }

@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """User login endpoint."""
    
    user = await users_collection.find_one({"email": credentials.email})
    
    if not user or user['password_hash'] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate new session token
    new_token = generate_token()
    await users_collection.update_one(
        {"_id": user['_id']},
        {"$set": {"session_token": new_token, "last_login": datetime.utcnow()}}
    )
    
    return {
        "token": new_token,
        "user_id": str(user['_id']),
        "name": user['name']
    }

@app.get("/api/user/profile")
async def get_profile(user: dict = Depends(verify_token)):
    """Get user profile."""
    return {
        "name": user['name'],
        "email": user['email'],
        "member_since": user['created_at']
    }

@app.get("/api/conversations/history")
async def get_conversation_history(user: dict = Depends(verify_token), limit: int = 10):
    """Retrieve conversation history."""
    
    conversations = await conversations_collection.find({
        "user_id": str(user['_id'])
    }).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    return conversations

# ===== WebSocket for Real-time Communication =====

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """Enhanced WebSocket endpoint with authentication."""
    
    await websocket.accept()
    
    # Verify token
    user = await users_collection.find_one({"session_token": token})
    if not user:
        await websocket.send_json({"type": "error", "message": "Invalid authentication"})
        await websocket.close()
        return
    
    user_id = str(user['_id'])
    print(f"User '{user['name']}' (ID: {user_id}) connected.")
    
    # Initialize session state
    session_state = {
        "chat_history": [],
        "last_emotion": "neutral",
        "tts_enabled": False,
        "user_name": user['name']
    }
    
    # Load recent chat history from database
    recent_chats = await conversations_collection.find({
        "user_id": user_id
    }).sort("timestamp", -1).limit(20).to_list(length=20)
    
    if recent_chats:
        session_state["chat_history"] = [
            {"role": msg['role'], "content": msg['content'], "emotion": msg.get('emotion')}
            for msg in reversed(recent_chats)
        ]
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle video frame for emotion detection
            if message.get("type") == "video_frame":
                img_data = base64.b64decode(message["data"])
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                try:
                    analysis_result = DeepFace.analyze(
                        img_path=frame,
                        actions=['emotion'],
                        enforce_detection=False
                    )
                    
                    if analysis_result and 'emotion' in analysis_result[0]:
                        emotion = analysis_result[0]['dominant_emotion']
                        session_state["last_emotion"] = emotion
                        await websocket.send_json({
                            "type": "emotion_update",
                            "emotion": emotion
                        })
                except Exception as e:
                    print(f"Emotion detection error: {e}")
                    session_state["last_emotion"] = "neutral"
            
            # Handle chat messages
            elif message.get("type") == "chat_message":
                user_input = message["content"]
                current_emotion = session_state["last_emotion"]
                
                # Build conversation context
                context = await build_conversation_context(user_id, session_state["chat_history"])
                
                # Generate enhanced prompt
                system_prompt = generate_enhanced_prompt(
                    session_state["user_name"],
                    current_emotion,
                    context
                )
                
                # Prepare messages for Ollama
                messages = [
                    {"role": "system", "content": system_prompt}
                ] + session_state["chat_history"][-20:] + [
                    {"role": "user", "content": user_input}
                ]
                
                try:
                    # Get AI response
                    ollama_response = ollama.chat(
                        model='tinyllama',
                        messages=messages
                    )
                    
                    assistant_message = ollama_response['message']['content']
                    
                    # Update chat history
                    user_msg = {"role": "user", "content": user_input, "emotion": current_emotion}
                    assistant_msg = {"role": "assistant", "content": assistant_message}
                    
                    session_state["chat_history"].append(user_msg)
                    session_state["chat_history"].append(assistant_msg)
                    
                    # Store in database
                    conversation_doc = {
                        "user_id": user_id,
                        "role": "user",
                        "content": user_input,
                        "emotion": current_emotion,
                        "timestamp": datetime.utcnow()
                    }
                    await conversations_collection.insert_one(conversation_doc)
                    
                    conversation_doc = {
                        "user_id": user_id,
                        "role": "assistant",
                        "content": assistant_message,
                        "timestamp": datetime.utcnow()
                    }
                    await conversations_collection.insert_one(conversation_doc)
                    
                    # Store memory asynchronously
                    asyncio.create_task(
                        MemoryManager.store_memory(user_id, user_msg, current_emotion)
                    )
                    
                    # Send response
                    await websocket.send_json({
                        "type": "chat_response",
                        "content": assistant_message
                    })
                    
                    # Handle TTS if enabled
                    if session_state["tts_enabled"]:
                        await websocket.send_json({
                            "type": "tts_audio",
                            "text": assistant_message
                        })
                
                except Exception as e:
                    print(f"Chat error: {e}")
                    await websocket.send_json({
                        "type": "chat_response",
                        "content": "I'm having trouble connecting right now. Please try again in a moment."
                    })
            
            # Handle TTS toggle
            elif message.get("type") == "toggle_tts":
                session_state["tts_enabled"] = message.get("enabled", False)
                print(f"TTS {'enabled' if session_state['tts_enabled'] else 'disabled'} for user {user['name']}")
    
    except WebSocketDisconnect:
        print(f"User '{user['name']}' disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

# ===== Static Files =====
@app.get("/")
async def get_index():
    """Serve login page."""
    return FileResponse("static/login.html")

@app.get("/app")
async def get_app():
    """Serve main application."""
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

# ===== Startup Event =====
@app.on_event("startup")
async def startup_event():
    """Initialize models and check database connection."""
    print("Loading DeepFace models...")
    try:
        DeepFace.analyze(
            img_path=np.zeros((100, 100, 3), dtype=np.uint8),
            actions=['emotion'],
            enforce_detection=False
        )
        print("✓ DeepFace models loaded")
    except Exception as e:
        print(f"✗ Error loading DeepFace: {e}")
    
    # Test database connection
    try:
        await db.command("ping")
        print("✓ MongoDB connected")
    except Exception as e:
        print(f"✗ MongoDB connection error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)