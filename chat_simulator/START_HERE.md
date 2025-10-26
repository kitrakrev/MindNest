# 🎭 Chat Simulator - Start Here!

Welcome to the Chat Simulator! This guide will get you up and running in 5 minutes.

## ⚡ Quick Setup

### Fastest Way (Recommended)
```bash
# From the parent directory (SO-TEST/)
cd SO-TEST

# Install dependencies
uv pip install fastapi uvicorn pydantic pydantic-settings python-multipart openai python-dotenv websockets

# Start the server
python chat_simulator/start.py
```

### Alternative: Using uv run
```bash
cd chat_simulator
uv run --no-project python start.py
```

### Environment Configuration
The `.env` file is already configured with:
- OpenAI API endpoint: `https://janitorai.com/hackathon`
- API Key: `calhacks2047`

The API will be available at: **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

## 🎯 Try It Out!

### Option 1: Run the Quick Start Demo
```bash
python examples/quick_start.py
```

This will:
- Create 2 personas
- Start a simulation
- Send messages
- Generate a TLDR summary

### Option 2: Try Persona Generation (New!)
```bash
python examples/generate_personas_demo.py
```

This demonstrates:
- Creating personas from conversations
- Uploading conversation files
- Generating from descriptions
- Running simulations with auto-generated personas

## 🚀 Main Features

### 1. **Create Personas Manually**
```bash
curl -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tech Enthusiast",
    "persona_type": "user",
    "system_prompt": "You are passionate about technology.",
    "description": "A tech lover"
  }'
```

### 2. **Generate Personas from Conversations** ✨
```bash
# Paste a conversation
curl -X POST "http://localhost:8000/api/personas/generate/from-conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_text": "Alice: Hi!\nBob: Hello there!",
    "auto_create": true
  }'

# Or upload a file
curl -X POST "http://localhost:8000/api/personas/generate/from-file" \
  -F "file=@examples/sample_conversation.txt" \
  -F "auto_create=true"
```

### 3. **Create a Simulation**
```bash
curl -X POST "http://localhost:8000/api/simulation/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Chat",
    "persona_ids": ["persona_abc", "persona_def"],
    "config": {"max_turns": 10}
  }'
```

### 4. **Start the Conversation**
```bash
curl -X POST "http://localhost:8000/api/simulation/{sim_id}/start"
```

### 5. **Get TLDR Summary**
```bash
curl -X POST "http://localhost:8000/api/chat/tldr" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "sim_abc",
    "last_n_messages": 10
  }'
```

## 📖 Documentation

- **README.md** - Overview and quick reference
- **PERSONA_GENERATION_GUIDE.md** - Detailed persona generation guide
- **README_NEW.md** - Complete API documentation
- **http://localhost:8000/docs** - Interactive API docs

## 🎨 Project Structure

```
chat_simulator/
├── main.py                 # FastAPI application
├── run.py                  # Simple runner script
├── core/
│   ├── config.py          # Configuration settings
│   └── queue_manager.py   # Message queue system
├── models/
│   ├── persona.py         # Persona data models
│   ├── message.py         # Message data models
│   ├── simulation.py      # Simulation data models
│   └── persona_generation.py  # Persona gen models
├── services/
│   ├── llm_service.py     # LLM integration
│   ├── persona_service.py # Persona management
│   ├── persona_generator.py  # AI persona generation ✨
│   └── simulation_service.py # Simulation orchestration
├── api/routes/
│   ├── personas.py        # Persona endpoints
│   ├── chat.py           # Chat endpoints
│   └── simulation.py     # Simulation endpoints
└── examples/
    ├── quick_start.py     # Basic demo
    ├── generate_personas_demo.py  # Persona generation demo ✨
    ├── sample_conversation.txt    # Example conversation
    └── personas.json      # Example persona definitions
```

## ✨ What's Special

1. **Dynamic Persona Creation**: Generate personas from conversations automatically
2. **AI-Powered**: Uses LLM to analyze speaking styles and create realistic personas
3. **Memory System**: Short-term and long-term memory for each persona
4. **Queue Management**: Robust message handling for concurrent conversations
5. **Real-time Updates**: WebSocket support for live chat
6. **TLDR Summaries**: Automatic conversation summarization

## 🎮 Workflow Example

```python
# 1. Upload a conversation (e.g., from Slack, Discord, etc.)
POST /api/personas/generate/from-file
  → Creates 3 personas automatically

# 2. Create a simulation with those personas
POST /api/simulation/
  → Returns simulation_id

# 3. Start the simulation
POST /api/simulation/{simulation_id}/start
  → Personas start chatting

# 4. Jump in with your own message
POST /api/chat/message
  → Add your thoughts

# 5. Get a summary
POST /api/chat/tldr
  → "Alice, Bob, and Charlie discussed AI ethics..."
```

## 🔧 Configuration

Edit `.env` to customize:
- LLM model and parameters
- Memory sizes
- Queue settings
- Max personas

## 🐛 Troubleshooting

**Server won't start?**
- Make sure uv is installed: `pip install uv`
- Check dependencies: `uv pip install -e .`

**No personas generated?**
- Check conversation format (Name: message)
- Ensure at least 2 messages per person
- Verify API key is set in `.env`

**Simulation not responding?**
- Check logs in terminal
- Verify personas are active
- Check queue stats: `GET /api/chat/queue/stats/{session_id}`

## 🎉 You're Ready!

1. Start the server: `python run.py`
2. Open docs: http://localhost:8000/docs
3. Run a demo: `python examples/generate_personas_demo.py`
4. Build something amazing! 🚀

## 📚 Next Steps

- Read **PERSONA_GENERATION_GUIDE.md** for advanced features
- Try uploading your own conversation files
- Experiment with different persona traits
- Build your own client application

---

**Questions?** Check the `/docs` endpoint or read the detailed guides!

