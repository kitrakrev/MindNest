"""
Quick test script for RPS controller
"""
from rps_controller import RPSController
import time

print("🤖 Testing RPS Controller")
print("=" * 50)

# Initialize
controller = RPSController()

if not controller.bus:
    print("❌ Robot not connected!")
    exit(1)

print("✅ Robot connected!")
print("\nTesting gestures...\n")

# Test each gesture
for gesture in ["rock", "paper", "scissors"]:
    print(f"Showing {gesture.upper()}...")
    controller.move_to_gesture(gesture, duration=1.0, with_shake=False)
    time.sleep(0.5)

# Return to rest
print("\nReturning to rest...")
controller.move_to_gesture("rest")

# Cleanup
controller.disconnect()
print("\n✅ Test complete!")

