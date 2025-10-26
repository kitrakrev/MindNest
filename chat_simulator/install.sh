#!/bin/bash

# Chat Simulator - Installation Script

echo "🎭 Chat Simulator - Installation"
echo "=================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "   Install it with: pip install uv"
    exit 1
fi

echo "✓ Found uv package manager"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
uv pip install -e .

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "=================================="
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Create .env file (copy from .env.example)"
echo "  2. Add your API keys to .env"
echo "  3. Start the server: python run.py"
echo "  4. Open http://localhost:8000/docs"
echo "  5. Test with: http://localhost:8000"
echo ""
echo "📖 Documentation:"
echo "   - START_HERE.md - Getting started guide"
echo "   - LETTA_INTEGRATION_GUIDE.md - Letta setup for Global Agent"
echo "   - PERSONA_GENERATION_GUIDE.md - Generate personas from conversations"
echo "=================================="

