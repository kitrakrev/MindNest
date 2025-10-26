# Environment Setup Guide

## 🔐 API Keys Configuration

All API keys and sensitive configuration are now moved to `.env` file for security.

---

## Quick Setup

### 1. Create `.env` File

Create a `.env` file in the `chat_simulator` directory:

```bash
cd chat_simulator
touch .env
```

### 2. Add Your API Keys

Copy this template into your `.env` file:

```bash
# === Server Settings ===
HOST=0.0.0.0
PORT=8000
DEBUG=true

# === LLM Settings ===
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=your_llm_base_url_here
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=300

# === Letta Settings (Optional - for Global Agent) ===
# Set LETTA_ENABLED=true to use Letta for stateful global agent
LETTA_ENABLED=false
LETTA_API_KEY=your_letta_api_key_here
LETTA_BASE_URL=https://api.letta.com
LETTA_AGENT_NAME=global-meta-advisor
LETTA_MODEL=openai/gpt-4
LETTA_EMBEDDING=openai/text-embedding-3-small

# === Memory Settings ===
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_SIZE=100

# === Simulation Settings ===
DEFAULT_SIMULATION_TYPE=chat
MAX_PERSONAS=20
MAX_QUEUE_SIZE=1000
MESSAGE_TIMEOUT=30
```

### 3. Update Your API Keys

Replace the placeholders with your actual values:

```bash
# Example with your actual keys:
LLM_API_KEY=calhacks2047
LLM_BASE_URL=https://janitorai.com/hackathon

# If using Letta:
LETTA_ENABLED=true
LETTA_API_KEY=sk-let-your-actual-key-here
```

### 4. Verify Configuration

Start the server to verify everything is configured correctly:

```bash
python run.py
```

---

## 🔑 Getting API Keys

### LLM API Key (Required)

The system uses OpenAI-compatible APIs. Configure based on your provider:

**Option 1: OpenAI**
```bash
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo
```

**Option 2: JanitorAI (Hackathon)**
```bash
LLM_API_KEY=calhacks2047
LLM_BASE_URL=https://janitorai.com/hackathon
LLM_MODEL=gpt-3.5-turbo
```

**Option 3: Custom/Self-hosted**
```bash
LLM_API_KEY=your_key
LLM_BASE_URL=http://localhost:8080/v1
LLM_MODEL=your-model-name
```

### Letta API Key (Optional)

Only needed if you want to enable Letta for the Global Agent:

1. **Get Letta Key:**
   - Visit [Letta Cloud](https://www.letta.com/)
   - Create account
   - Get API key from dashboard

2. **Configure:**
   ```bash
   LETTA_ENABLED=true
   LETTA_API_KEY=sk-let-your-key-here
   ```

3. **Learn More:**
   - See `LETTA_INTEGRATION_GUIDE.md` for full documentation
   - Reference: https://docs.letta.com/overview

---

## ⚙️ Configuration Options

### Token Limits

The system is optimized for **concise, precise outputs**:

```bash
LLM_MAX_TOKENS=300  # Max tokens per response (reduced for brevity)
```

**Responses are limited to:**
- Persona responses: 2-3 sentences max
- Global agent advice: 3-4 sentences max
- Summaries: 2 sentences max
- Persona generation: 2 sentences max

### Memory Settings

```bash
SHORT_TERM_MEMORY_SIZE=10   # Recent interactions
LONG_TERM_MEMORY_SIZE=100   # Important memories
```

### Simulation Settings

```bash
DEFAULT_SIMULATION_TYPE=chat  # or "views"
MAX_PERSONAS=20               # Maximum personas allowed
MAX_QUEUE_SIZE=1000          # Message queue size
MESSAGE_TIMEOUT=30            # Timeout in seconds
```

---

## 🔒 Security Best Practices

### 1. Never Commit `.env`

The `.env` file is already in `.gitignore`. Never commit it!

```bash
# Check your .gitignore includes:
.env
.env.local
```

### 2. Use Environment-Specific Files

For different environments:

```bash
.env              # Main environment file (gitignored)
.env.example      # Template for others (committed)
.env.production   # Production settings (gitignored)
.env.development  # Development settings (gitignored)
```

### 3. Rotate Keys Regularly

Periodically update your API keys, especially if:
- Keys are exposed
- Team members change
- Switching providers

---

## 🧪 Testing Configuration

### Verify Setup

```bash
# Start server
python run.py

# Check status endpoint
curl http://localhost:8000/api/global-agent/status
```

Expected response:
```json
{
  "letta_enabled": false,
  "letta_configured": false,
  "service_type": "traditional"
}
```

### Test LLM Connection

```bash
# Create a test persona
curl -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Persona",
    "system_prompt": "You are a helpful test persona.",
    "persona_type": "user"
  }'
```

---

## 🐛 Troubleshooting

### Issue: "LLM_API_KEY not set"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify it contains LLM_API_KEY
cat .env | grep LLM_API_KEY

# Restart server after adding keys
python run.py
```

### Issue: "Letta not initialized"

This is expected if `LETTA_ENABLED=false`. To enable:

```bash
# In .env
LETTA_ENABLED=true
LETTA_API_KEY=your_key_here

# Restart server
python run.py
```

### Issue: Server won't start

**Check:**
1. `.env` file is in correct directory (`chat_simulator/`)
2. All required keys are set (LLM_API_KEY, LLM_BASE_URL)
3. No syntax errors in `.env` (no spaces around =)

**Correct:**
```bash
LLM_API_KEY=mykey
```

**Incorrect:**
```bash
LLM_API_KEY = mykey  # NO SPACES!
```

---

## 📝 Example `.env` Files

### Minimal Setup (Development)

```bash
HOST=0.0.0.0
PORT=8000
DEBUG=true

LLM_API_KEY=calhacks2047
LLM_BASE_URL=https://janitorai.com/hackathon
LLM_MODEL=gpt-3.5-turbo
```

### Full Setup (Production with Letta)

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# LLM
LLM_API_KEY=sk-prod-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=300

# Letta
LETTA_ENABLED=true
LETTA_API_KEY=sk-let-prod-key-here
LETTA_BASE_URL=https://api.letta.com
LETTA_AGENT_NAME=global-meta-advisor-prod
LETTA_MODEL=openai/gpt-4
LETTA_EMBEDDING=openai/text-embedding-3-small

# Memory
SHORT_TERM_MEMORY_SIZE=10
LONG_TERM_MEMORY_SIZE=100

# Simulation
DEFAULT_SIMULATION_TYPE=chat
MAX_PERSONAS=20
MAX_QUEUE_SIZE=1000
MESSAGE_TIMEOUT=30
```

---

## ✅ Ready to Go!

Once your `.env` file is configured:

```bash
# Install dependencies
pip install -e .

# Start the server
python run.py

# Visit the docs
open http://localhost:8000/docs
```

---

## 📚 Additional Resources

- **Main README:** `README.md`
- **Getting Started:** `START_HERE.md`
- **Letta Integration:** `LETTA_INTEGRATION_GUIDE.md`
- **Persona Generation:** `PERSONA_GENERATION_GUIDE.md`

---

**Need Help?** Check the troubleshooting section or review the documentation files listed above.

