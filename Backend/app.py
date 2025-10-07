# app.py
import asyncio
import base64
import json
import uuid
import numpy as np
import cv2
from deepface import DeepFace
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
import ollama

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This endpoint handles the main HTML page at the root URL (/)
@app.get("/")
async def get_index_page():
    return FileResponse("static/index.html")

# This endpoint handles all other static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


# In-memory storage for user sessions and chat history
user_sessions = {}

def load_deepface_models():
    try:
        DeepFace.analyze(img_path=np.zeros((100, 100, 3), dtype=np.uint8), actions=['emotion'], enforce_detection=False)
        print("DeepFace models loaded successfully.")
    except Exception as e:
        print(f"Error loading DeepFace models: {e}")

@app.on_event("startup")
async def startup_event():
    load_deepface_models()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    print(f"Client '{client_id}' connected.")
    
    if client_id not in user_sessions:
        user_sessions[client_id] = {
            "chat_history": [],
            "last_emotion": "neutral"
        }
        print(f"New session created for client '{client_id}'.")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

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
                        user_sessions[client_id]["last_emotion"] = emotion
                        await websocket.send_json({"type": "emotion_update", "emotion": emotion})
                except Exception as e:
                    print(f"DeepFace analysis error: {e}")
                    user_sessions[client_id]["last_emotion"] = "neutral"
                    await websocket.send_json({"type": "emotion_update", "emotion": "neutral"})

            elif message.get("type") == "chat_message":
                user_input = message["content"]
                current_emotion = user_sessions[client_id]["last_emotion"]
                chat_history = user_sessions[client_id]["chat_history"]

                system_prompt = (
                    f"You are Maitri, a supportive friend and insightful psychologist. "
                    f"You are speaking with a user who currently seems to be feeling {current_emotion}. "
                    f"Acknowledge their emotional state subtly in your response and provide a compassionate and helpful reply. "
                    f"Your responses should be empathetic and personal."
                )
                
                messages = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": user_input}]

                try:
                    ollama_response = ollama.chat(
                        model='phi3:mini',
                        messages=messages
                    )
                    assistant_message = ollama_response['message']['content']
                    user_sessions[client_id]["chat_history"].append({"role": "user", "content": user_input})
                    user_sessions[client_id]["chat_history"].append({"role": "assistant", "content": assistant_message})
                    
                    await websocket.send_json({"type": "chat_response", "content": assistant_message})
                except Exception as e:
                    print(f"Ollama chat error: {e}")
                    await websocket.send_json({"type": "chat_response", "content": "Sorry, I am having trouble connecting to the AI. Please try again later."})

    except WebSocketDisconnect:
        print(f"Client '{client_id}' disconnected.")