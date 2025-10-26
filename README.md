# MindNest

AI-powered conversation platform with robot control integration.

## Projects

### 🎭 Chat Simulator (`chat_simulator/`)
Multi-agent AI conversation platform with:
- Dynamic persona creation and management
- Global Meta-Advisor with Letta memory integration
- Real-time conversation simulation
- TLDR summaries (text & video styles)
- Group management

### 🤖 Robot Controller (`bot_code/`)
SO-101 Rock-Paper-Scissors Robot API:
- REST API for robot gesture control
- Rock, Paper, Scissors gestures
- Shake animations and timing controls

## Quick Start

### Chat Simulator
\`\`\`bash
cd chat_simulator
cp .env.example .env  # Add your API keys
uv run main.py
\`\`\`
Visit: http://localhost:8000

### Robot Controller
\`\`\`bash
cd bot_code
uv run api.py
\`\`\`
API: http://localhost:8001

## Features
- Multi-persona AI conversations
- Persistent memory with Letta
- Robot control interface
- Real-time WebSocket updates
- Group-based simulations
