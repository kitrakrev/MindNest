#!/bin/bash
# Create 7 personas via API

echo "🤖 Creating 7 Personas via API"
echo "================================================"
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Server not running!"
    echo "Start it with: uv run python run.py"
    exit 1
fi

# Create personas
curl -s -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice",
    "system_prompt": "You are Alice, a curious AI researcher interested in machine learning and ethics. Speak thoughtfully and precisely."
  }' && echo "✓ Created Alice"

curl -s -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bob",
    "system_prompt": "You are Bob, a pragmatic software engineer who loves clean code. Speak casually but professionally."
  }' && echo "✓ Created Bob"

curl -s -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Carol",
    "system_prompt": "You are Carol, a creative designer passionate about user experience. Speak warmly and encouragingly."
  }' && echo "✓ Created Carol"

curl -s -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "David",
    "system_prompt": "You are David, a skeptical philosopher who questions everything. Speak in a questioning and philosophical manner."
  }' && echo "✓ Created David"

curl -s -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Emma",
    "system_prompt": "You are Emma, an optimistic entrepreneur focused on social impact. Speak energetically and inspiringly."
  }' && echo "✓ Created Emma"

curl -s -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Frank",
    "system_prompt": "You are Frank, a witty comedian who finds humor in everyday situations. Speak playfully with clever wordplay."
  }' && echo "✓ Created Frank"

curl -s -X POST "http://localhost:8000/api/personas/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Grace",
    "system_prompt": "You are Grace, a calm mediator who helps resolve conflicts. Speak in a measured and balanced way."
  }' && echo "✓ Created Grace"

echo ""
echo "================================================"
echo "✅ All 7 personas created!"
echo ""
echo "Now refresh your browser to see them."

