"""
Quick debug script to test simulation and message flow
"""
import asyncio
import sys
sys.path.insert(0, '.')

from services.simulation_service import SimulationService
from services.persona_service import persona_service
from models.simulation import SimulationCreate, SimulationConfig, SimulationType
from core.queue_manager import MessageQueueManager

async def test_simulation():
    print("🔍 Testing Simulation System")
    print("=" * 60)
    
    # Create queue manager
    queue_manager = MessageQueueManager()
    
    # Create simulation service
    sim_service = SimulationService(queue_manager)
    
    # Check personas
    print("\n1. Checking Personas:")
    all_personas = persona_service.list_personas()
    print(f"   Found {len(all_personas)} personas")
    for p in all_personas:
        print(f"   - {p.name} ({p.id}) - Active: {p.is_active}")
    
    if len(all_personas) < 2:
        print("   ⚠️ Need at least 2 personas for testing!")
        return
    
    # Create a test simulation
    print("\n2. Creating Test Simulation:")
    try:
        persona_ids = [p.id for p in all_personas[:7]]  # Use 7 personas
        sim_create = SimulationCreate(
            name="Debug Test",
            persona_ids=persona_ids,
            type=SimulationType.CHAT,
            config=SimulationConfig(
                max_turns=5,
                turn_delay=1.0
            )
        )
        simulation = sim_service.create_simulation(sim_create)
        print(f"   ✓ Created simulation: {simulation.id}")
        print(f"   ✓ Personas: {len(simulation.persona_ids)}")
    except Exception as e:
        print(f"   ❌ Failed to create simulation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Start simulation
    print("\n3. Starting Simulation:")
    try:
        success = await sim_service.start_simulation(simulation.id)
        if success:
            print(f"   ✓ Simulation started")
        else:
            print(f"   ❌ Failed to start simulation")
            return
    except Exception as e:
        print(f"   ❌ Error starting simulation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Wait and check messages
    print("\n4. Waiting for messages (10 seconds):")
    await asyncio.sleep(10)
    
    print("\n5. Checking Messages:")
    try:
        messages = await queue_manager.get_recent_messages(simulation.id, limit=50)
        print(f"   Found {len(messages)} messages")
        
        if len(messages) == 0:
            print("   ⚠️ NO MESSAGES GENERATED!")
            print("\n   Possible issues:")
            print("   1. LLM_API_KEY not set in .env")
            print("   2. LLM_BASE_URL not configured")
            print("   3. Error in LLM service")
            
            # Check simulation status
            sim = sim_service.get_simulation(simulation.id)
            print(f"\n   Simulation status: {sim.status}")
            print(f"   Message count: {sim.message_count}")
        else:
            print("\n   ✓ Messages generated successfully!")
            for i, msg in enumerate(messages[:5], 1):
                print(f"   {i}. [{msg.persona_id}]: {msg.content[:60]}...")
    
    except Exception as e:
        print(f"   ❌ Error getting messages: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Debug test complete!")

if __name__ == "__main__":
    asyncio.run(test_simulation())

