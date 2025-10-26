#!/bin/bash
# Quick Start Script for Chat Simulator with Persistence

echo "🎭 Chat Simulator - Quick Start"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "Creating .env template..."
    cat > .env << 'EOF'
# LLM Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
LLM_API_KEY=your_openai_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=300

# Database (default is SQLite)
DATABASE_URL=sqlite+aiosqlite:///./chat_simulator.db

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
EOF
    echo "✓ Created .env file"
    echo "⚠️  Please edit .env and add your LLM_API_KEY"
    echo ""
    read -p "Press Enter after editing .env..."
fi

# Check if database exists
if [ -f "chat_simulator.db" ]; then
    echo "✓ Database found (chat_simulator.db)"
    # Count personas
    PERSONA_COUNT=$(sqlite3 chat_simulator.db "SELECT COUNT(*) FROM personas;" 2>/dev/null || echo "0")
    echo "  Current personas: $PERSONA_COUNT"
else
    echo "⚠️  No database found - will be created on first run"
fi

echo ""
echo "Choose an option:"
echo "1. Start server (existing data)"
echo "2. Start fresh (clear all data first)"
echo "3. Create 7 sample personas then start"
echo "4. Just create personas (don't start server)"
echo "5. Show system stats"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting server..."
        echo "   Open: http://localhost:8000"
        echo ""
        uv run python run.py
        ;;
    2)
        echo ""
        echo "⚠️  This will DELETE ALL DATA!"
        read -p "Type 'yes' to confirm: " confirm
        if [ "$confirm" = "yes" ]; then
            rm -f chat_simulator.db
            echo "✓ Database deleted"
            echo "🚀 Starting fresh server..."
            echo "   Open: http://localhost:8000"
            echo ""
            uv run python run.py &
            SERVER_PID=$!
            echo "Waiting for server to start..."
            sleep 5
            echo ""
            echo "📝 Creating 7 sample personas..."
            ./create_personas_api.sh
            echo ""
            echo "✅ Ready! Open http://localhost:8000"
            wait $SERVER_PID
        else
            echo "Cancelled."
        fi
        ;;
    3)
        echo ""
        echo "🚀 Starting server in background..."
        uv run python run.py > /tmp/chat_sim.log 2>&1 &
        SERVER_PID=$!
        echo "   Server PID: $SERVER_PID"
        sleep 5
        
        echo "📝 Creating 7 sample personas..."
        chmod +x create_personas_api.sh
        ./create_personas_api.sh
        
        echo ""
        echo "✅ Ready! Open http://localhost:8000"
        echo ""
        echo "Server is running in background (PID: $SERVER_PID)"
        echo "To stop: kill $SERVER_PID"
        ;;
    4)
        echo ""
        echo "🚀 Starting server temporarily..."
        uv run python run.py > /tmp/chat_sim.log 2>&1 &
        SERVER_PID=$!
        sleep 5
        
        echo "📝 Creating 7 sample personas..."
        chmod +x create_personas_api.sh
        ./create_personas_api.sh
        
        echo ""
        echo "Stopping server..."
        kill $SERVER_PID
        echo "✓ Personas created and saved to database"
        ;;
    5)
        echo ""
        if [ ! -f "chat_simulator.db" ]; then
            echo "❌ No database found"
            exit 1
        fi
        
        echo "📊 System Statistics"
        echo "===================="
        echo ""
        echo "Personas:    $(sqlite3 chat_simulator.db 'SELECT COUNT(*) FROM personas;' 2>/dev/null || echo '0')"
        echo "Groups:      $(sqlite3 chat_simulator.db 'SELECT COUNT(*) FROM groups;' 2>/dev/null || echo '0')"
        echo "Simulations: $(sqlite3 chat_simulator.db 'SELECT COUNT(*) FROM simulations;' 2>/dev/null || echo '0')"
        echo "Messages:    $(sqlite3 chat_simulator.db 'SELECT COUNT(*) FROM messages;' 2>/dev/null || echo '0')"
        echo ""
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

