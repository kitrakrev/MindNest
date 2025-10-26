# 🎭 Chat Simulator

A production-ready FastAPI service for simulating conversations among multiple AI personas with LLM integration, SQLite database, and beautiful web UI.

## ✨ Features

- 🎨 **Modern Web UI** - Beautiful, responsive interface
- 🗄️ **SQLite Database** - Persistent storage for all data
- 👥 **Group Chats** - Organize personas into groups
- 🤖 **AI-Powered** - Dynamic persona generation
- 💬 **Real-time** - Live conversation updates
- 📝 **TLDR** - Auto-summarize conversations
- 🔄 **Queue System** - Robust message handling

## Quick Start

```bash
# Install dependencies
cd chat_simulator
uv pip install fastapi uvicorn pydantic pydantic-settings python-multipart openai python-dotenv websockets sqlalchemy aiosqlite

# Run the service
python run.py
```

## Access the Application

- **Web UI**: http://localhost:8000/
- **API Docs**: http://localhost:8000/docs
- **Database**: SQLite file created automatically

## Features

✅ 1. Choose simulation type (chat/views)
✅ 2. User persona or real people types
✅ 3. Create personas or upload from file
✅ 4. System prompts with short & long-term memory
✅ 5. Simulate conversations with user interruption
✅ 6. TLDR generation for discussions
✅ 7. Queue system for message management
✨ 8. **AI-powered persona generation from conversations**
✨ 9. **Generate personas from text descriptions**
✨ 10. **Upload conversation files to create personas**

## Persona Generation

Create personas automatically:

```bash
# From conversation transcript
curl -X POST "http://localhost:8000/api/personas/generate/from-conversation" \
  -H "Content-Type: application/json" \
  -d '{"conversation_text": "Alice: Hi!\nBob: Hello!", "auto_create": true}'

# From description
curl -X POST "http://localhost:8000/api/personas/generate/from-description" \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Science", "description": "A scientist", "traits": ["curious"]}'

# From file upload
curl -X POST "http://localhost:8000/api/personas/generate/from-file" \
  -F "file=@conversation.txt" \
  -F "auto_create=true"
```

Try the demo: `python examples/generate_personas_demo.py`

See full documentation and examples in the API docs! 