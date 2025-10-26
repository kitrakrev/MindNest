"""
Test the ultra-smooth movements (100 steps in 10 seconds)
"""
from rps_controller import RPSController
import time

print("🤖 Testing Ultra-Smooth Movements")
print("=" * 70)
print("Settings: 100 steps over 10 seconds per motor movement")
print("=" * 70)

controller = RPSController()

if not controller.bus:
    print("❌ Robot not connected!")
    exit(1)

print("✅ Robot connected!")
print("\nWatch the robot move in slow motion...\n")

# Test 1: Single smooth gesture
print("1. Smooth ROCK gesture (100 steps / 10 seconds)...")
controller.move_to_gesture("rock", duration=2.0, with_shake=False)
print("   ✓ Rock complete\n")
time.sleep(2)

# Test 2: Smooth transition to paper
print("2. Smooth PAPER gesture (100 steps / 10 seconds)...")
controller.move_to_gesture("paper", duration=2.0, with_shake=False)
print("   ✓ Paper complete\n")
time.sleep(2)

# Test 3: Smooth scissors
print("3. Smooth SCISSORS gesture (100 steps / 10 seconds)...")
controller.move_to_gesture("scissors", duration=2.0, with_shake=False)
print("   ✓ Scissors complete\n")
time.sleep(2)

# Test 4: Smooth shake
# print("4. Ultra-smooth SHAKE (30 steps / 2 seconds per direction)...")
# controller.shake_gesture(amplitude=80, shakes=1)
# print("   ✓ Shake complete\n")
# time.sleep(1)

# Return to rest
print("5. Smooth return to REST (100 steps / 10 seconds)...")
controller.move_to_gesture("rest")

# Cleanup
controller.disconnect()
print("\n" + "=" * 70)
print("✅ Ultra-smooth movement test complete!")
print("=" * 70)

