# Maitri AI सहायक 🪷

<div align="center">

![Maitri AI Banner](https://img.shields.io/badge/Maitri_AI-Mental_Wellbeing_Companion-blueviolet?style=for-the-badge&logo=心)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-brightgreen.svg)](https://mongodb.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-orange.svg)](https://ollama.ai)

**Your Personal AI Companion for Mental Wellbeing**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

Maitri AI is an **emotion-aware conversational AI companion** designed to support mental wellbeing through:

- 🎭 **Real-time emotion detection** from facial expressions
- 🧠 **Semantic memory** that remembers your conversations contextually
- 🗣️ **Multi-language voice interaction** (English, Hindi, Tamil, Telugu, etc.)
- 🎮 **Interactive stress-relief games** (Antakshari, Riddles, Word Games)
- 💾 **Intelligent fact extraction** to personalize conversations
- 🌍 **100% offline AI** - Your data never leaves your device

---

## ✨ Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Emotion Detection** | Uses DeepFace to analyze facial expressions in real-time |
| **Semantic Memory** | Stores conversations as vector embeddings for intelligent recall |
| **Fact Learning** | Automatically extracts and remembers facts about you |
| **Voice Input/Output** | Speech-to-text (Google API) and TTS (eSpeak-NG) |
| **Game System** | Antakshari, riddles, trivia, and word association games |
| **Multi-language** | Support for 11+ Indian languages |

### Technical Highlights

- **Local AI Processing**: Uses Ollama for on-device inference
- **WebSocket Communication**: Real-time bidirectional messaging
- **Vector Similarity Search**: Finds relevant past conversations using embeddings
- **Proactive Engagement**: Suggests games based on emotional state
- **Fact Extraction**: Regex-based extraction of personal information
- **Theme Detection**: Categorizes conversations into topics (work, family, health, etc.)

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Login Page  │  │  Chat UI     │  │  Analytics   │      │
│  │  (login.html)│  │ (index.html) │  │  Dashboard   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↕ WebSocket
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                           │
│  ┌────────────────────────────────────────────────────┐     │
│  │  app.py - Main Server                              │     │
│  │  • HTTP Endpoints (auth, profile, API)             │     │
│  │  • WebSocket Handler (real-time chat)              │     │
│  │  • System Integration                              │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    AI & PROCESSING                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Ollama AI  │  │  DeepFace    │  │  eSpeak-NG   │      │
│  │  (phi3:mini) │  │  (Emotion)   │  │    (TTS)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEMS                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Semantic   │  │     Game     │  │     Fact     │      │
│  │    Memory    │  │    System    │  │  Extraction  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                      MONGODB                                │
│  • users  • conversations  • memories  • facts  • games     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → WebSocket → Backend
2. **Memory Recall** → Embedding search → Relevant context
3. **AI Processing** → Ollama generates response
4. **Fact Extraction** → Store learned information
5. **Response Delivery** → WebSocket → User Interface
6. **(Parallel) Emotion Detection** → DeepFace → UI update

---

## 🚀 Installation

### Prerequisites

- **Python 3.9+**
- **MongoDB 6.0+** (local or Atlas)
- **Ollama** (for local AI)
- **eSpeak-NG** (for TTS)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/maitri-ai.git
cd maitri-ai
```

### Step 2: Install Python Dependencies

```bash
pip install fastapi uvicorn motor pydantic pydantic-settings
pip install python-multipart websockets
pip install ollama deepface numpy opencv-python
pip install SpeechRecognition python-dotenv
```

### Step 3: Install Ollama and Models

```bash
# Install Ollama from https://ollama.ai

# Pull required models
ollama pull phi3:mini              # Chat model
ollama pull nomic-embed-text       # Embedding model
```

### Step 4: Install eSpeak-NG (TTS)

**Windows:**
```bash
# Download and install from: speech/espeak-ng.msi
# Or from: https://github.com/espeak-ng/espeak-ng/releases
```

**Linux:**
```bash
sudo apt-get install espeak-ng
```

**macOS:**
```bash
brew install espeak-ng
```

### Step 5: Setup MongoDB

**Option A: Local MongoDB**
```bash
# Install from: https://www.mongodb.com/try/download/community
# Start MongoDB service
mongod --dbpath /path/to/data
```

**Option B: MongoDB Atlas (Cloud)**
- Create free cluster at https://www.mongodb.com/cloud/atlas
- Get connection string

### Step 6: Configure Environment

Create `.env` file:

```env
# Database
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=maitri_ai

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# Ollama
OLLAMA_MODEL=phi3:mini
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# TTS Settings
TTS_LANGUAGE=en-IN
TTS_RATE=150
TTS_PITCH=50

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

### Step 7: Create Static Folder

```bash
mkdir static
# Move index.html and login.html to static/
mv index.html static/
mv login.html static/
```

---

## 🎮 Usage

### Start the Server

```bash
python app.py
```

Or with uvicorn:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Access the Application

1. Open browser: `http://localhost:8000`
2. **Sign Up**: Create account with email and password
3. **Login**: Enter credentials
4. **Start Chatting**: Share what's on your mind

### Using Features

#### 🎤 Voice Input
1. Click "🎤 Voice" button
2. Speak when prompted
3. Your speech will be transcribed and sent

#### 📷 Camera (Emotion Detection)
1. Click "📷 Camera" button
2. Allow camera access
3. Emotion detected every 500ms
4. Updates displayed in right sidebar

#### 🔊 Text-to-Speech
1. Click "🔇 TTS" button to enable
2. AI responses will be spoken aloud
3. Language matches your profile preference

#### 🎮 Playing Games
- Maitri proactively suggests games based on:
  - Your emotional state
  - Conversation length
  - Engagement level
  
**Available Games:**
- **Antakshari**: Hindi song name chain
- **Riddles**: Solve brain teasers
- **Word Association**: Build word chains
- **Trivia**: Answer quiz questions

---

## 📂 Project Structure

```
maitri-ai/
├── app.py                  # Main FastAPI server
├── config.py               # Configuration management
├── memory_systems.py       # Semantic memory & embeddings
├── games.py                # Interactive game system
├── tts.py                  # Text-to-speech (eSpeak-NG)
├── sr.py                   # Speech recognition
├── static/
│   ├── index.html         # Main application UI
│   └── login.html         # Authentication page
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
└── README.md             # This file
```

---

## 🧠 How It Works

### Memory System

#### 1. Conversation Storage
```python
User: "I work as a teacher"
  ↓
Embedding: [0.23, 0.45, 0.12, ...] (768 dimensions)
  ↓
MongoDB: Store with timestamp, emotion, themes
```

#### 2. Fact Extraction
```python
Input: "My name is Raj and I'm a software engineer"
  ↓
Extracted Facts:
  - {type: 'name', value: 'raj'}
  - {type: 'job', value: 'software engineer'}
  ↓
MongoDB: facts_collection
```

#### 3. Semantic Recall
```python
Query: "How's my job going?"
  ↓
Generate embedding: [0.21, 0.43, ...]
  ↓
Compare with past conversations (cosine similarity)
  ↓
Recall: "Last time you mentioned work stress..."
```

### Emotion Detection

```python
Webcam Frame (every 500ms)
  ↓
Base64 encode → WebSocket → Backend
  ↓
DeepFace.analyze(frame)
  ↓
Returns: {
  'dominant_emotion': 'happy',
  'emotion': {
    'happy': 85.2,
    'sad': 8.1,
    'neutral': 6.7
  }
}
  ↓
Update UI + Adjust AI tone
```

---

## 🔧 Configuration

### Language Options

```python
TTS_LANGUAGES = {
    "en-IN": "English (India)",
    "hi-IN": "Hindi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "bn-IN": "Bengali",
    "gu-IN": "Gujarati",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "pa-IN": "Punjabi",
    "ur-IN": "Urdu"
}
```

### Emotion Configuration

```python
EMOTION_STRESS_LEVELS = {
    'happy': {'level': 'Low', 'score': 20},
    'neutral': {'level': 'Low', 'score': 30},
    'surprised': {'level': 'Moderate', 'score': 50},
    'sad': {'level': 'High', 'score': 80},
    'angry': {'level': 'High', 'score': 90},
    'fearful': {'level': 'Very High', 'score': 100}
}
```

---

## 🔐 Security Features

- **Password Hashing**: SHA-256 with salt
- **Session Tokens**: Secure random tokens (32 bytes)
- **Token Verification**: Every WebSocket/API request
- **CORS Protection**: Configured origins only
- **Input Validation**: Pydantic models

---

## 📊 API Endpoints

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login

### User Management
- `GET /api/user/profile` - Get user profile with learned facts
- `GET /api/conversations/history` - Retrieve chat history

### Memory & Search
- `POST /api/memory/search` - Semantic search through memories

### Games
- `GET /api/games/stats` - Get game statistics

### Things to Remember
- `POST /api/things/` - Create reminder
- `GET /api/things/` - Get all reminders
- `PUT /api/things/{id}` - Update reminder
- `DELETE /api/things/{id}` - Delete reminder

### WebSocket
- `WS /ws/{token}` - Real-time chat connection

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request



## 🐛 Troubleshooting

### Common Issues

**1. Ollama Connection Error**
```bash
# Ensure Ollama is running
ollama list

# Pull models if missing
ollama pull phi3:mini
ollama pull nomic-embed-text
```

**2. MongoDB Connection Error**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Or check connection string in .env
```

**3. eSpeak-NG Not Found**
```bash
# Windows: Reinstall from speech/espeak-ng.msi
# Linux: sudo apt-get install espeak-ng
# macOS: brew install espeak-ng
```

**4. Camera Not Working**
- Allow camera permissions in browser
- Check browser console for errors
- Ensure HTTPS or localhost (required for camera access)

**5. Voice Recognition Failing**
- Check microphone permissions
- Ensure internet connection (uses Google API)
- Verify microphone in browser settings

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ollama** - Local AI inference
- **DeepFace** - Facial emotion recognition
- **eSpeak-NG** - Text-to-speech engine
- **FastAPI** - Modern web framework
- **MongoDB** - Flexible database

---

## 💬 Support

For support:
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/maitri-ai/discussions)

---

## 🌟 Mental Health Resources

**India:**
- AASRA: 91-22-27546669
- Vandrevala Foundation: 1860-2662-345
- iCall: 9152987821
- Sneha: 044-24640050

**International:**
- Visit: https://findahelpline.com

---

<div align="center">

**Made with ❤️ for mental wellbeing**

⭐ Star this repo if it helped you!

</div>

