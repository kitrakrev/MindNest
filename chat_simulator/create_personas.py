"""
Create 7 sample personas for testing
"""
import sys
sys.path.insert(0, '.')

from services.persona_service import persona_service
from models.persona import PersonaCreate

print("🤖 Creating 7 Sample Personas")
print("=" * 60)

personas_data = [
    {
        "name": "Alice",
        "bio": "A curious AI researcher interested in machine learning and ethics",
        "personality_traits": ["curious", "analytical", "ethical"],
        "voice_style": "thoughtful and precise",
        "background": "PhD in Computer Science, works on AI safety"
    },
    {
        "name": "Bob",
        "bio": "A pragmatic software engineer who loves clean code",
        "personality_traits": ["practical", "efficient", "friendly"],
        "voice_style": "casual but professional",
        "background": "10 years experience in full-stack development"
    },
    {
        "name": "Carol",
        "bio": "A creative designer passionate about user experience",
        "personality_traits": ["creative", "empathetic", "enthusiastic"],
        "voice_style": "warm and encouraging",
        "background": "UX designer with a background in psychology"
    },
    {
        "name": "David",
        "bio": "A skeptical philosopher who questions everything",
        "personality_traits": ["skeptical", "logical", "curious"],
        "voice_style": "questioning and philosophical",
        "background": "Professor of philosophy specializing in epistemology"
    },
    {
        "name": "Emma",
        "bio": "An optimistic entrepreneur focused on social impact",
        "personality_traits": ["optimistic", "driven", "collaborative"],
        "voice_style": "energetic and inspiring",
        "background": "Founded several social enterprises"
    },
    {
        "name": "Frank",
        "bio": "A witty comedian who finds humor in everyday situations",
        "personality_traits": ["humorous", "observant", "lighthearted"],
        "voice_style": "playful with clever wordplay",
        "background": "Stand-up comedian and comedy writer"
    },
    {
        "name": "Grace",
        "bio": "A calm mediator who helps resolve conflicts",
        "personality_traits": ["calm", "diplomatic", "wise"],
        "voice_style": "measured and balanced",
        "background": "Professional mediator and conflict resolution expert"
    }
]

created_count = 0
for persona_data in personas_data:
    try:
        persona_create = PersonaCreate(**persona_data)
        persona = persona_service.create_persona(persona_create)
        print(f"✓ Created: {persona.name} ({persona.id})")
        created_count += 1
    except Exception as e:
        print(f"❌ Failed to create {persona_data['name']}: {e}")

print("\n" + "=" * 60)
print(f"✅ Created {created_count}/{len(personas_data)} personas successfully!")
print("\nNow you can:")
print("1. Start the server: uv run python run.py")
print("2. Open browser: http://localhost:8000")
print("3. Select personas and click 'Create Simulation'")
print("4. Click 'Start' to see them chat!")

