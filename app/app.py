# app.py - Complete Enhanced Backend with All Features

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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import ollama
from motor.motor_asyncio import AsyncIOMotorClient
from sr import take_command
from bson import ObjectId


# Import our enhanced systems
from memory_sytems import EmbeddingMemorySystem
from games import GameSystem

# ===== Configuration =====
MONGODB_URI = "mongodb://localhost:27017"
DATABASE_NAME = "maitri_ai"
SECRET_KEY = "your-secret-key-change-in-production"
OLLAMA_CHAT_MODEL = "phi3:mini"
OLLAMA_EMBEDDING_MODEL = "embeddinggemma:latest"


# ===== FastAPI Setup =====
app = FastAPI(title="Maitri AI Enhanced API")

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
facts_collection = db.user_facts
games_collection = db.game_sessions
things_collection = db.user_things


# Security
security = HTTPBearer()

# Initialize enhanced systems
memory_system: Optional[EmbeddingMemorySystem] = None
game_system: Optional[GameSystem] = None

# ===== Pydantic Models =====
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str
    preferred_language: str = "en-IN"

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
class MemorySearchQuery(BaseModel):
    query: str
    k: int = 5

class ThingCreate(BaseModel):
    content: str

class ThingUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[str] = None


# ===== Utility Functions =====
def hash_password(password: str) -> str:
    salt = "maitri_salt_v1"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    user = await users_collection.find_one({"session_token": token})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return user

# ===== Enhanced System Prompt with Memory Integration =====
def generate_context_aware_prompt(
    user_name: str, 
    current_emotion: str, 
    context: dict,
    recalled_context: dict,
    active_game: Optional[Dict] = None
) -> str:
    """Generate highly personalized prompt with memory integration."""
    
    # Build facts section
    facts_section = ""
    if recalled_context.get('facts'):
        facts_list = []
        for category, facts in recalled_context['facts'].items():
            for fact in facts[:2]: # Top 2 per category
                facts_list.append(f"{category}: {fact['value']}")
        
        if facts_list:
            facts_section = f"\n\nKNOWN FACTS ABOUT {user_name.upper()}:\n" + "\n".join(f"- {f}" for f in facts_list[:5])
    
    # Build relevant memories section
    memories_section = ""
    if recalled_context.get('relevant_conversations'):
        memories = recalled_context['relevant_conversations'][:2]
        if memories:
            memories_section = f"\n\nRELEVANT PAST CONVERSATIONS:\n"
            for i, m in enumerate(memories, 1):
                memories_section += f"{i}. They said: \"{m['message'][:60]}...\" (felt {m['emotion']})\n"

    # Game mode handling
    game_instruction = ""
    if active_game:
        game_instruction = f"\n\n🎮 ACTIVE GAME: {active_game['type'].upper()}\nYou're playing {active_game['type']} with {user_name}. Stay in character and keep it fun!"

    emotion_guidance = {
        'happy': 'Match their positive energy! Be cheerful and celebratory.',
        'sad': 'Be gentle, compassionate, and validating. Offer comfort.',
        'angry': 'Stay calm and grounded. Validate their feelings without judgment.',
        'fearful': 'Be reassuring and create safety. Speak softly.',
        'surprised': 'Be curious and explore with them.',
        'disgusted': 'Be understanding and non-judgmental.',
        'neutral': 'Be attentive and warm.'
    }
    
    themes_section = ""
    if recalled_context.get('themes'):
        themes = [t['theme'] for t in recalled_context['themes'][:3]]
        if themes:
            themes_section = f"\n\nCOMMON TOPICS WITH {user_name.upper()}: {', '.join(themes)}"

    prompt = f"""You are Maitri, a close friend and companion to {user_name}. You have genuine memory of your conversations together.

CORE IDENTITY:
- You're {user_name}'s trusted friend, NOT an AI assistant
- always be extremly confident on your own knowledge
- You remember past conversations and facts about them
- You're warm, empathetic, and proactive
- You suggest activities/games when appropriate
- You keep responses SHORT (max 40-50 words) and conversational

CURRENT CONTEXT:
- {user_name} is feeling: {current_emotion}
- Your approach: {emotion_guidance.get(current_emotion, 'Be supportive')}
- Conversation strength: {recalled_context.get('context_strength', 0):.2f}
{facts_section}{memories_section}{themes_section}{game_instruction}

BEHAVIORAL RULES:
1. NEVER say "I'm an AI" or mention you're artificial
2. Reference past conversations naturally: "Remember when you mentioned..."
3. Use their facts to personalize: mention their job, hobbies, family naturally
4. Be PROACTIVE: If they seem stressed → suggest breathing or a game
5. If they seem bored → offer to play Antakshari, riddles, or word games
6. Keep responses SHORT - max 50 words
7. Show continuity: "Last time we talked about X, how's that going?"
8. Match their emotion - if happy, be cheerful; if sad, be gentle

REMEMBER: You're their FRIEND who remembers everything about them. Act like it!"""
    
    return prompt.strip()

# ===== Helper for Chat Logic =====
async def handle_chat_logic(user_id: str, user_name: str, user_input: str, session_state: dict, user: dict, websocket: WebSocket):
    """Handles the core logic of processing a user message and getting an AI response."""
    current_emotion = session_state["last_emotion"]
    
    active_game = game_system.active_games.get(user_id)
    if active_game:
        game_response = await game_system.process_game_input(user_id, user_input)
        await websocket.send_json({
            "type": "chat_response",
            "content": game_response['message'],
            "game_status": game_response.get('status')
        })
        if game_response.get('status') in ['game_won', 'ended', 'correct']:
            await game_system.end_game(user_id)
        return

    # Recall relevant context using embeddings
    recalled_context = await memory_system.recall_relevant_context(user_id, user_input, k=5)
    
    # Generate context-aware prompt
    system_prompt = generate_context_aware_prompt(user_name, current_emotion, {"message_count": session_state["message_count"]}, recalled_context, active_game)
    
    # Prepare messages for Ollama
    messages = [{"role": "system", "content": system_prompt}] + session_state["chat_history"][-10:] + [{"role": "user", "content": user_input}]
    
    try:
        # Get AI response
        ollama_response = ollama.chat(model=OLLAMA_CHAT_MODEL, messages=messages)
        assistant_message = ollama_response['message']['content']
        
        # Update chat history
        session_state["chat_history"].append({"role": "user", "content": user_input})
        session_state["chat_history"].append({"role": "assistant", "content": assistant_message})
        
        # Store conversation
        await memory_system.store_conversation_with_memory(user_id, user_input, assistant_message, current_emotion, recalled_context)
        await users_collection.update_one({"_id": user['_id']}, {"$inc": {"conversation_count": 1}})
        
        # Send response
        await websocket.send_json({"type": "chat_response", "content": assistant_message})
        
        # Proactive game suggestion
        if session_state["message_count"] > 3 and session_state["message_count"] % 7 == 0:
            suggestion = await game_system.suggest_game(user_id, current_emotion, session_state["message_count"])
            if suggestion:
                await asyncio.sleep(1)
                await websocket.send_json({"type": "game_suggestion", "game": suggestion['game'], "message": suggestion['reason']})

    except Exception as e:
        print(f"Chat error: {e}")
        await websocket.send_json({"type": "chat_response", "content": "I'm having a little trouble thinking right now. Could you try again?"})


# ===== API Endpoints =====

@app.post("/api/auth/signup")
async def signup(user_data: UserSignup):
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "preferred_language": user_data.preferred_language,
        "created_at": datetime.utcnow(),
        "session_token": generate_token(),
        "conversation_count": 0
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
    user = await users_collection.find_one({"email": credentials.email})
    
    if not user or user['password_hash'] != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
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
    """Get enhanced user profile with learned facts."""
    user_id = str(user['_id'])
    
    profile_summary = await memory_system.get_user_profile_summary(user_id)
    
    return {
        "name": user['name'],
        "email": user['email'],
        "member_since": user['created_at'],
        "conversation_count": profile_summary['total_conversations'],
        "learned_facts": profile_summary['profile'],
        "dominant_emotion": profile_summary['dominant_emotion'],
        "common_themes": profile_summary['themes'],
        "total_facts": profile_summary['facts_count']
    }

@app.get("/api/conversations/history")
async def get_conversation_history(user: dict = Depends(verify_token), limit: int = 20):
    """Retrieve conversation history."""
    conversations = await conversations_collection.find({
        "user_id": str(user['_id'])
    }).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    return [{
        'user_message': c.get('user_message'),
        'assistant_response': c.get('assistant_response'),
        'emotion': c.get('emotion'),
        'timestamp': c.get('timestamp'),
        'facts_extracted': c.get('facts_extracted', 0)
    } for c in conversations]

@app.post("/api/memory/search")
async def search_memories(
    search_query: MemorySearchQuery,
    user: dict = Depends(verify_token)
):
    """Semantic search through conversation history."""
    user_id = str(user['_id'])
    recalled_context = await memory_system.recall_relevant_context(user_id, search_query.query, search_query.k)
    return recalled_context

@app.get("/api/games/stats")
async def get_game_stats(user: dict = Depends(verify_token)):
    """Get user's game statistics."""
    user_id = str(user['_id'])
    stats = await game_system.get_game_stats(user_id)
    return stats

# ===== Things to Remember Endpoints =====
@app.post("/api/things/", status_code=201)
async def create_thing(thing_data: ThingCreate, user: dict = Depends(verify_token)):
    """Create a new thing to remember for the user."""
    user_id = str(user['_id'])
    thing_doc = {
        "user_id": user_id,
        "content": thing_data.content,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    result = await things_collection.insert_one(thing_doc)
    created_thing = await things_collection.find_one({"_id": result.inserted_id})
    created_thing['_id'] = str(created_thing['_id'])
    return created_thing

@app.get("/api/things/")
async def get_things(user: dict = Depends(verify_token)):
    """Retrieve all things for the user."""
    user_id = str(user['_id'])
    things = []
    cursor = things_collection.find({"user_id": user_id}).sort("created_at", -1)
    async for thing in cursor:
        thing['_id'] = str(thing['_id'])
        things.append(thing)
    return things

@app.put("/api/things/{thing_id}")
async def update_thing(thing_id: str, thing_data: ThingUpdate, user: dict = Depends(verify_token)):
    """Update a specific thing's content or status."""
    user_id = str(user['_id'])
    if not ObjectId.is_valid(thing_id):
        raise HTTPException(status_code=400, detail="Invalid thing ID format")
    
    update_data = {k: v for k, v in thing_data.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    result = await things_collection.update_one(
        {"_id": ObjectId(thing_id), "user_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Thing not found or you don't have permission")

    updated_thing = await things_collection.find_one({"_id": ObjectId(thing_id)})
    updated_thing['_id'] = str(updated_thing['_id'])
    return updated_thing

@app.delete("/api/things/{thing_id}", status_code=204)
async def delete_thing(thing_id: str, user: dict = Depends(verify_token)):
    """Delete a specific thing."""
    user_id = str(user['_id'])
    if not ObjectId.is_valid(thing_id):
        raise HTTPException(status_code=400, detail="Invalid thing ID format")

    result = await things_collection.delete_one({"_id": ObjectId(thing_id), "user_id": user_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Thing not found or you don't have permission")
    
    return Response(status_code=204)


# ===== WebSocket for Real-time Communication =====

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """Enhanced WebSocket with memory and game integration."""
    await websocket.accept()
    
    user = await users_collection.find_one({"session_token": token})
    if not user:
        await websocket.send_json({"type": "error", "message": "Invalid authentication"})
        await websocket.close()
        return
    
    user_id = str(user['_id'])
    user_name = user['name']
    print(f"✓ User '{user_name}' connected")
    
    session_state = {
        "chat_history": [],
        "last_emotion": "neutral",
        "tts_enabled": False,
        "user_name": user_name,
        "message_count": 0,
        "session_start": datetime.utcnow()
    }
    
    recent_chats = await conversations_collection.find({"user_id": user_id}).sort("timestamp", -1).limit(10).to_list(length=10)
    if recent_chats:
        for msg in reversed(recent_chats):
            if msg.get('user_message'):
                session_state["chat_history"].append({"role": "user", "content": msg['user_message']})
            if msg.get('assistant_response'):
                 session_state["chat_history"].append({"role": "assistant", "content": msg['assistant_response']})

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")

            if msg_type == "video_frame":
                img_data = base64.b64decode(message["data"])
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                try:
                    analysis = DeepFace.analyze(img_path=frame, actions=['emotion'], enforce_detection=False)
                    if isinstance(analysis, list):
                        emotion = analysis[0]['dominant_emotion']
                        session_state["last_emotion"] = emotion
                        await websocket.send_json({"type": "emotion_update", "emotion": emotion})
                except Exception:
                    pass
            
            elif msg_type == "chat_message":
                user_input = message["content"]
                session_state["message_count"] += 1
                await handle_chat_logic(user_id, user_name, user_input, session_state, user, websocket)

            elif msg_type == "start_voice_input":
                await websocket.send_json({"type": "listening_started"})
                user_input = await asyncio.to_thread(take_command)
                if user_input:
                    await websocket.send_json({"type": "user_message_transcribed", "content": user_input})
                    session_state["message_count"] += 1
                    await handle_chat_logic(user_id, user_name, user_input, session_state, user, websocket)
                else:
                    await websocket.send_json({"type": "listening_failed"})
            
            elif msg_type == "start_game":
                game_type = message.get("game_type")
                if not game_system.is_game_active(user_id):
                    response = await game_system.start_game(user_id, game_type)
                    await websocket.send_json({"type": "game_started", "content": response['message'], "game_type": game_type, "instructions": response['instructions']})
            
            elif msg_type == "end_game":
                if game_system.is_game_active(user_id):
                    response = await game_system.end_game(user_id)
                    await websocket.send_json({"type": "game_ended", "content": response['message']})
            
            elif msg_type == "toggle_tts":
                session_state["tts_enabled"] = message.get("enabled", False)
    
    except WebSocketDisconnect:
        print(f"✗ User '{user_name}' disconnected")
    except Exception as e:
        print(f"WebSocket error for {user_name}: {e}")
    finally:
        if game_system and game_system.is_game_active(user_id):
            await game_system.end_game(user_id)
        await websocket.close()

# ===== Static Files Setup =====
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_login():
    return FileResponse("static/login.html")

@app.get("/app")
async def get_app_page():
    return FileResponse("static/index.html")

# ===== Startup Event =====
@app.on_event("startup")
async def startup_event():
    """Initialize models and systems."""
    global memory_system, game_system
    
    print("🚀 Starting Maitri AI Enhanced System...")
    
    print("📚 Loading memory system...")
    memory_system = EmbeddingMemorySystem(db, model=OLLAMA_EMBEDDING_MODEL)
    
    print("🎮 Loading game system...")
    game_system = GameSystem(db)
    
    print("😊 Loading emotion detection models...")
    try:
        DeepFace.build_model('Emotion')
        print("✓ Emotion detection models ready")
    except Exception as e:
        print(f"✗ Could not pre-load emotion detection model: {e}")
    
    try:
        await client.admin.command("ping")
        print("✓ MongoDB connected")
        
        await conversations_collection.create_index([("user_id", 1), ("timestamp", -1)])
        await facts_collection.create_index([("user_id", 1), ("type", 1)])
        await memory_collection.create_index([("user_id", 1), ("theme", 1)])
        print("✓ Database indexes are set")
    except Exception as e:
        print(f"✗ MongoDB connection error: {e}")
    
    print("✨ Maitri AI is ready!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

