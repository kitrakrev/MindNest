"""
Rock-Paper-Scissors Controller for SO-101 Robot Arm

Simplified version extracted from Bob Table Mate.
Controls the SO-101 arm to play rock-paper-scissors with gestures and shake animations.

Usage:
    python rps_controller.py
"""

import time
import random
import logging
from dotenv import load_dotenv

# LeRobot for SO-101 arm
from lerobot.motors.feetech import FeetechMotorsBus
from lerobot.motors import Motor, MotorNormMode

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RPSController:
    """
    Rock-Paper-Scissors controller for SO-101 robot arm.
    Handles gestures and animations for the game.
    """
    
    # SO-101 positions for rock-paper-scissors gestures
    GESTURES = {
        "rock": {
            "shoulder_pan": 2048,
            "shoulder_lift": 1800,
            "elbow_flex": 1500,
            "wrist_flex": 2048,
            "wrist_roll": 2048,
            "clasp": 1200,  # Tight closed fist (gripper fully closed)
        },
        "paper": {
            "shoulder_pan": 2048,
            "shoulder_lift": 1800,
            "elbow_flex": 1800,
            "wrist_flex": 2048,
            "wrist_roll": 2048,
            "clasp": 2900,  # Open hand (gripper fully open)
        },
        "scissors": {
            "shoulder_pan": 2048,
            "shoulder_lift": 1800,
            "elbow_flex": 1700,
            "wrist_flex": 2048,
            "wrist_roll": 2048,
            "clasp": 2200,  # Partially open (V shape, gripper half open)
        },
        "rest": {
            "shoulder_pan": 2048,
            "shoulder_lift": 2048,
            "elbow_flex": 2048,
            "wrist_flex": 2048,
            "wrist_roll": 2048,
            "clasp": 2048,  # Neutral gripper position
        },
    }
    
    def __init__(self, port: str = None):
        """
        Initialize the RPS controller.
        
        Args:
            port: Serial port for the robot arm (e.g., /dev/tty.usbmodem*)
                  If None, will try to auto-detect or use ROBOT_PORT env var
        """
        import os
        import glob
        
        # Try to get port from environment or parameter
        if port is None:
            port = os.getenv("ROBOT_PORT")
        
        # If still no port, try to auto-detect
        if port is None:
            tty_ports = glob.glob("/dev/tty.usbmodem*")
            cu_ports = glob.glob("/dev/cu.usbmodem*")
            available = tty_ports + cu_ports
            
            if available:
                port = available[0]  # Use first available
                logger.info(f"🔍 Auto-detected port: {port}")
            else:
                port = "/dev/tty.usbmodem5A7A0187131"  # Fallback
                logger.warning(f"⚠️ No USB ports found, using default: {port}")
        
        self.port = port
        self.bus = None
        self.motors = None
        self.current_gesture = "rest"
        self._init_arm()
    
    def _init_arm(self):
        """Initialize the SO-101 arm motors."""
        # Motor configuration for SO-101
        motor_config = {
            "shoulder_pan": Motor(1, "sts3215", MotorNormMode.RANGE_M100_100),
            "shoulder_lift": Motor(2, "sts3215", MotorNormMode.RANGE_M100_100),
            "elbow_flex": Motor(3, "sts3215", MotorNormMode.RANGE_M100_100),
            "wrist_flex": Motor(4, "sts3215", MotorNormMode.RANGE_M100_100),
            "wrist_roll": Motor(5, "sts3215", MotorNormMode.RANGE_M100_100),
            "clasp": Motor(6, "sts3215", MotorNormMode.RANGE_M100_100),
        }
        
        logger.info(f"🔌 Connecting to robot at {self.port}...")
        logger.info(f"   Motors: {list(motor_config.keys())}")
        
        try:
            # Create bus and connect
            self.bus = FeetechMotorsBus(port=self.port, motors=motor_config)
            self.bus.connect()
            logger.info("✓ FeetechMotorsBus.connect() successful")
            
            # Store motors dict
            self.motors = motor_config
            
            # Verify connection by reading a position
            test_pos = self.bus.read("Present_Position", "shoulder_pan", normalize=False)
            logger.info(f"✓ SO-101 arm connected successfully! (shoulder_pan: {test_pos})")
            
            # Small delay for stability
            time.sleep(0.5)
            logger.info("✓ Robot ready for rock-paper-scissors!")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize arm: {e}")
            logger.error(f"   Port: {self.port}")
            logger.error(f"   Check: Is robot plugged in? Is port correct?")
            logger.error(f"   Try running: ls -la /dev/tty.usbmodem*")
            import traceback
            logger.error(traceback.format_exc())
            self.bus = None
            self.motors = None
    
    def check_connectivity(self) -> bool:
        """Check if robot is connected and motors are responsive."""
        if not self.bus or not self.motors:
            logger.error("❌ Robot bus or motors not initialized")
            return False
        
        try:
            # Try to read a position to verify connectivity
            test_motor = "shoulder_pan"
            if test_motor in self.motors:
                pos = self.bus.read("Present_Position", test_motor, normalize=False)
                logger.debug(f"✓ Robot connectivity verified (shoulder_pan: {pos})")
                return True
            else:
                logger.error("❌ Motors not found in bus")
                return False
        except Exception as e:
            logger.error(f"❌ Robot connectivity check failed: {e}")
            return False
    
    def smooth_move(self, motor_name: str, target_pos: int, steps: int = 50, total_time: float = 5.0):
        """
        Move a motor smoothly to target position using many small steps.
        
        Args:
            motor_name: Name of the motor to move
            target_pos: Target position
            steps: Number of intermediate steps (more = smoother)
            total_time: Total time for the movement in seconds
        """
        if motor_name not in self.motors:
            return
        
        # Read current position
        try:
            current_pos = self.bus.read("Present_Position", motor_name, normalize=False)
        except:
            current_pos = 2048  # Default if can't read
        
        # Calculate step size and delay
        delta = target_pos - current_pos
        step_size = delta / steps
        step_delay = total_time / steps
        
        # Move in small increments
        for i in range(steps):
            intermediate_pos = int(current_pos + step_size * (i + 1))
            self.bus.write("Goal_Position", motor_name, intermediate_pos, normalize=False)
            time.sleep(step_delay)
    
    def shake_gesture(self, amplitude: int = 80, shakes: int = 2) -> bool:
        """
        Shake the arm side to side - animated buildup for the game!
        Uses very smooth, gradual movements with many small steps.
        
        Args:
            amplitude: How far to shake (motor units, reduced for smoothness)
            shakes: Number of shake cycles
            
        Returns:
            True if successful, False otherwise
        """
        if not self.bus:
            logger.error("❌ Cannot shake: Robot not connected")
            return False
        
        if not self.check_connectivity():
            return False
        
        try:
            base_pan = 2048
            
            # Very smooth shaking with many small steps
            for i in range(shakes):
                # Calculate smooth amplitude (starts small, gets bigger)
                current_amplitude = int(amplitude * (0.5 + 0.5 * (i + 1) / shakes))
                
                # Smooth shake left (30 steps over 2 seconds)
                self.smooth_move("shoulder_pan", base_pan - current_amplitude, steps=30, total_time=2.0)
                self.smooth_move("wrist_roll", 2048 + current_amplitude // 3, steps=30, total_time=0.5)
                
                # Smooth shake right (30 steps over 2 seconds)
                self.smooth_move("shoulder_pan", base_pan + current_amplitude, steps=30, total_time=2.0)
                self.smooth_move("wrist_roll", 2048 - current_amplitude // 3, steps=30, total_time=0.5)
            
            # Return to center very smoothly (50 steps over 3 seconds)
            self.smooth_move("shoulder_pan", base_pan, steps=50, total_time=3.0)
            self.smooth_move("wrist_roll", 2048, steps=50, total_time=2.0)
            
            logger.info("✓ Shake gesture completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during shake: {e}")
            return False
    
    def move_to_gesture(self, gesture: str, duration: float = 3.0, with_shake: bool = False) -> bool:
        """
        Move arm to a specific gesture with smooth movements.
        
        Args:
            gesture: Target gesture name ("rock", "paper", "scissors", "rest")
            duration: Time to hold the gesture (seconds)
            with_shake: Whether to shake before showing gesture
            
        Returns:
            True if successful, False otherwise
        """
        # Check connectivity first
        if not self.bus or gesture not in self.GESTURES:
            logger.error(f"❌ Cannot execute gesture '{gesture}': Robot not initialized or invalid gesture")
            return False
        
        if not self.check_connectivity():
            logger.error(f"❌ Cannot execute gesture '{gesture}': Connectivity check failed")
            return False
        
        positions = self.GESTURES[gesture].copy()
        
        try:
            # Shake if requested
            if with_shake:
                logger.info("🤝 Shaking before gesture...")
                shake_success = self.shake_gesture()
                if not shake_success:
                    logger.warning("⚠️ Shake failed, continuing with gesture...")
            
            # Move to target positions smoothly (100 steps over 10 seconds)
            logger.info(f"🤖 Moving smoothly to gesture: {gesture}")
            for motor_name, target_pos in positions.items():
                if motor_name in self.motors:
                    # Smooth movement: 100 steps over 10 seconds as requested
                    self.smooth_move(motor_name, target_pos, steps=100, total_time=5.0)
                    logger.debug(f"  {motor_name} → {target_pos}")
            
            # Hold the gesture
            time.sleep(duration)
            self.current_gesture = gesture
            logger.info(f"✓ Gesture '{gesture}' completed successfully (held for {duration}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error moving to gesture '{gesture}': {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def play_rock_paper_scissors(self) -> str:
        """
        Play a full rock-paper-scissors game with countdown, shake, and random choice.
        Uses smooth movements throughout.
        
        Returns:
            The chosen gesture ("rock", "paper", or "scissors"), or None if failed
        """
        # Check connectivity first
        if not self.check_connectivity():
            logger.error("❌ Cannot play RPS: Robot not connected")
            return None
        
        logger.info("🎮 Starting Rock-Paper-Scissors game!")
        logger.info("=" * 50)
        
        # Countdown
        for i in range(3, 0, -1):
            logger.info(f"🎲 Rock... Paper... Scissors... {i}")
            time.sleep(1.0)
        
        # Final shake before reveal (with smooth movements)
        logger.info("🤝 *Shaking excitedly*")
        shake_success = self.shake_gesture(amplitude=80, shakes=2)
        if not shake_success:
            logger.error("❌ Shake failed during RPS game")
            return None
        
        # Choose random gesture
        gestures = ["rock", "paper", "scissors"]
        chosen = random.choice(gestures)
        
        logger.info(f"🎯 I choose... {chosen.upper()}!")
        
        # Show gesture with smooth movement (100 steps over 10 seconds) and hold
        success = self.move_to_gesture(chosen, duration=3.0, with_shake=False)
        if not success:
            logger.error(f"❌ Failed to show {chosen} gesture")
            return None
        
        # Return to rest smoothly
        time.sleep(1.0)
        self.move_to_gesture("rest", duration=2.0)
        
        logger.info("=" * 50)
        logger.info(f"✓ RPS game completed! Robot chose: {chosen}")
        return chosen
    
    def disconnect(self):
        """Disconnect the arm and return to rest position."""
        if self.bus:
            try:
                logger.info("🏠 Returning to rest position...")
                self.move_to_gesture("rest")
                time.sleep(0.5)
                self.bus.disconnect()
                logger.info("✓ Robot arm disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting arm: {e}")


def demo():
    """
    Demo function showing all RPS capabilities.
    """
    print("\n" + "=" * 70)
    print("ROCK-PAPER-SCISSORS CONTROLLER DEMO")
    print("=" * 70)
    print("\nInitializing robot arm...")
    
    # Initialize controller
    controller = RPSController()
    
    if not controller.bus:
        print("\n❌ Failed to initialize robot arm!")
        print("Please check:")
        print("  1. Robot is plugged in via USB")
        print("  2. Port is correct (check with: ls /dev/tty.usbmodem*)")
        print("  3. You have permissions to access the port")
        return
    
    print("\n✓ Robot arm initialized successfully!")
    
    try:
        # Demo 1: Show each gesture
        print("\n" + "=" * 70)
        print("DEMO 1: Individual Gestures")
        print("=" * 70)
        
        for gesture in ["rock", "paper", "scissors"]:
            print(f"\nShowing {gesture.upper()}...")
            controller.move_to_gesture(gesture, duration=1.5, with_shake=True)
            time.sleep(0.5)
        
        # Demo 2: Play a full game
        print("\n" + "=" * 70)
        print("DEMO 2: Full RPS Game")
        print("=" * 70)
        result = controller.play_rock_paper_scissors()
        
        if result:
            print(f"\n✓ Game completed! Robot chose: {result.upper()}")
        
        # Demo 3: Multiple games
        print("\n" + "=" * 70)
        print("DEMO 3: Multiple Games")
        print("=" * 70)
        
        results = []
        for game_num in range(1, 4):
            print(f"\n--- Game {game_num} ---")
            result = controller.play_rock_paper_scissors()
            if result:
                results.append(result)
            time.sleep(1)
        
        print(f"\n✓ Played {len(results)} games!")
        print(f"Results: {', '.join([r.upper() for r in results])}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    finally:
        print("\n" + "=" * 70)
        print("Cleaning up...")
        controller.disconnect()
        print("✓ Demo complete!")
        print("=" * 70 + "\n")


def interactive_mode():
    """
    Interactive mode - let user control the robot.
    """
    print("\n" + "=" * 70)
    print("ROCK-PAPER-SCISSORS CONTROLLER - Interactive Mode")
    print("=" * 70)
    print("\nInitializing robot arm...")
    
    controller = RPSController()
    
    if not controller.bus:
        print("\n❌ Failed to initialize robot arm!")
        return
    
    print("\n✓ Robot arm ready!")
    print("\nCommands:")
    print("  rock     - Show rock gesture")
    print("  paper    - Show paper gesture")
    print("  scissors - Show scissors gesture")
    print("  play     - Play a full RPS game")
    print("  shake    - Just shake")
    print("  rest     - Return to rest position")
    print("  quit     - Exit")
    print("\n" + "=" * 70 + "\n")
    
    try:
        while True:
            command = input("Enter command: ").strip().lower()
            
            if command == "quit" or command == "q":
                break
            elif command in ["rock", "paper", "scissors"]:
                controller.move_to_gesture(command, duration=2.0, with_shake=True)
            elif command == "play":
                controller.play_rock_paper_scissors()
            elif command == "shake":
                controller.shake_gesture()
            elif command == "rest":
                controller.move_to_gesture("rest")
            elif command == "help":
                print("\nCommands: rock, paper, scissors, play, shake, rest, quit")
            else:
                print(f"Unknown command: {command}. Type 'help' for commands.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    finally:
        print("\nCleaning up...")
        controller.disconnect()
        print("✓ Goodbye!")


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        interactive_mode()


if __name__ == "__main__":
    main()

