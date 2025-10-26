"""
Test the new smooth shake gesture
"""
from rps_controller import RPSController
import time

print("🤖 Testing Smooth Shake")
print("=" * 50)

controller = RPSController()

if not controller.bus:
    print("❌ Robot not connected!")
    exit(1)

print("✅ Robot connected!")

# Test shake standalone
print("\n1. Testing smooth shake (standalone)...")
controller.shake_gesture(amplitude=100, shakes=2)
time.sleep(1)

# Test shake with gesture
print("\n2. Testing smooth shake + rock gesture...")
controller.move_to_gesture("rock", duration=1.5, with_shake=True)
time.sleep(1)

# Test full RPS game (includes shake)
print("\n3. Testing full RPS game with smooth shake...")
result = controller.play_rock_paper_scissors()
print(f"   Robot chose: {result.upper()}")

# Cleanup
controller.disconnect()
print("\n✅ Smooth shake test complete!")

