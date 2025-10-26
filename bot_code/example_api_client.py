#!/usr/bin/env python3
"""
Example Python client for Rock-Paper-Scissors API

Demonstrates how to interact with the API using the requests library.
"""

import requests
import time
import sys
from typing import Dict, Any


class RPSClient:
    """Client for interacting with the Rock-Paper-Scissors API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the RPS API client.
        
        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make a request to the API."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            if hasattr(e.response, 'json'):
                print(f"   Detail: {e.response.json().get('detail', 'Unknown error')}")
            raise
    
    def get_info(self) -> Dict[Any, Any]:
        """Get API information."""
        return self._request("GET", "/")
    
    def health_check(self) -> Dict[Any, Any]:
        """Check API and robot health."""
        return self._request("GET", "/health")
    
    def get_status(self) -> Dict[Any, Any]:
        """Get robot status."""
        return self._request("GET", "/status")
    
    def connect(self, port: str = None) -> Dict[Any, Any]:
        """Connect to robot."""
        json_data = {"port": port} if port else {}
        return self._request("POST", "/connect", json=json_data)
    
    def disconnect(self) -> Dict[Any, Any]:
        """Disconnect from robot."""
        return self._request("POST", "/disconnect")
    
    def play_rock(self, duration: float = 3.0, with_shake: bool = False) -> Dict[Any, Any]:
        """Play rock gesture."""
        return self._request("POST", "/rock", json={
            "duration": duration,
            "with_shake": with_shake
        })
    
    def play_paper(self, duration: float = 3.0, with_shake: bool = False) -> Dict[Any, Any]:
        """Play paper gesture."""
        return self._request("POST", "/paper", json={
            "duration": duration,
            "with_shake": with_shake
        })
    
    def play_scissors(self, duration: float = 3.0, with_shake: bool = False) -> Dict[Any, Any]:
        """Play scissors gesture."""
        return self._request("POST", "/scissors", json={
            "duration": duration,
            "with_shake": with_shake
        })
    
    def play_random(self, duration: float = 3.0, with_shake: bool = False) -> Dict[Any, Any]:
        """Play random gesture."""
        return self._request("POST", "/random", json={
            "duration": duration,
            "with_shake": with_shake
        })
    
    def shake(self, amplitude: int = 80, shakes: int = 2) -> Dict[Any, Any]:
        """Perform shake animation."""
        return self._request("POST", "/shake", json={
            "amplitude": amplitude,
            "shakes": shakes
        })
    
    def rest(self) -> Dict[Any, Any]:
        """Move to rest position."""
        return self._request("POST", "/rest")


def example_basic_gestures():
    """Example: Play individual gestures."""
    print("=" * 60)
    print("Example 1: Playing Individual Gestures")
    print("=" * 60)
    
    client = RPSClient()
    
    # Check health
    print("\n1. Checking health...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    
    # Play rock
    print("\n2. Playing ROCK 🪨")
    result = client.play_rock(duration=3.0)
    print(f"   ✓ {result['message']}")
    time.sleep(4)
    
    # Play paper
    print("\n3. Playing PAPER 📄")
    result = client.play_paper(duration=3.0)
    print(f"   ✓ {result['message']}")
    time.sleep(4)
    
    # Play scissors
    print("\n4. Playing SCISSORS ✂️")
    result = client.play_scissors(duration=3.0)
    print(f"   ✓ {result['message']}")
    time.sleep(4)
    
    # Rest
    print("\n5. Returning to rest 🏠")
    client.rest()
    
    print("\n✓ Example completed!\n")


def example_random_game():
    """Example: Play a full rock-paper-scissors game."""
    print("=" * 60)
    print("Example 2: Full Rock-Paper-Scissors Game")
    print("=" * 60)
    
    client = RPSClient()
    
    # Countdown
    print("\n🎮 Starting game!")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    
    # Shake
    print("\n🤝 Shaking...")
    client.shake(amplitude=100, shakes=2)
    time.sleep(3)
    
    # Play random
    print("\n🎲 Choosing gesture...")
    result = client.play_random(duration=3.0, with_shake=False)
    gesture = result['gesture']
    print(f"   🎯 Robot chose: {gesture.upper()}!")
    time.sleep(4)
    
    # Rest
    print("\n🏠 Returning to rest...")
    client.rest()
    
    print("\n✓ Game completed!\n")
    return gesture


def example_multiple_random():
    """Example: Play multiple random gestures."""
    print("=" * 60)
    print("Example 3: Multiple Random Gestures")
    print("=" * 60)
    
    client = RPSClient()
    
    gestures = []
    rounds = 3
    
    for i in range(1, rounds + 1):
        print(f"\n🎲 Round {i}/{rounds}")
        result = client.play_random(duration=2.0, with_shake=True)
        gesture = result['gesture']
        gestures.append(gesture)
        print(f"   Chose: {gesture.upper()}")
        time.sleep(3)
    
    # Rest
    print("\n🏠 Returning to rest...")
    client.rest()
    
    # Stats
    print("\n" + "=" * 60)
    print("Game Statistics")
    print("=" * 60)
    print(f"Rounds played: {rounds}")
    print(f"Rock: {gestures.count('rock')}")
    print(f"Paper: {gestures.count('paper')}")
    print(f"Scissors: {gestures.count('scissors')}")
    print("\n✓ Example completed!\n")


def example_with_shake():
    """Example: Gestures with shake animation."""
    print("=" * 60)
    print("Example 4: Gestures with Shake")
    print("=" * 60)
    
    client = RPSClient()
    
    gestures = ["rock", "paper", "scissors"]
    
    for gesture in gestures:
        print(f"\n🤝 Playing {gesture.upper()} with shake...")
        
        if gesture == "rock":
            result = client.play_rock(duration=2.0, with_shake=True)
        elif gesture == "paper":
            result = client.play_paper(duration=2.0, with_shake=True)
        else:
            result = client.play_scissors(duration=2.0, with_shake=True)
        
        print(f"   ✓ {result['message']}")
        time.sleep(3)
    
    # Rest
    print("\n🏠 Returning to rest...")
    client.rest()
    
    print("\n✓ Example completed!\n")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Rock-Paper-Scissors API Client Examples" + " " * 8 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    try:
        # Test connection first
        client = RPSClient()
        print("Testing connection to API server...")
        info = client.get_info()
        print(f"✓ Connected to: {info['name']}\n")
        
        # Menu
        print("Select an example to run:")
        print("  1. Basic Gestures (rock, paper, scissors)")
        print("  2. Full RPS Game with countdown")
        print("  3. Multiple Random Rounds")
        print("  4. Gestures with Shake Animation")
        print("  5. Run All Examples")
        print("  q. Quit")
        
        choice = input("\nEnter choice (1-5 or q): ").strip()
        
        if choice == "1":
            example_basic_gestures()
        elif choice == "2":
            example_random_game()
        elif choice == "3":
            example_multiple_random()
        elif choice == "4":
            example_with_shake()
        elif choice == "5":
            print("\nRunning all examples...\n")
            example_basic_gestures()
            time.sleep(2)
            example_random_game()
            time.sleep(2)
            example_multiple_random()
            time.sleep(2)
            example_with_shake()
            print("\n🎉 All examples completed!")
        elif choice.lower() == "q":
            print("Goodbye!")
            return 0
        else:
            print("Invalid choice")
            return 1
        
        return 0
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API server")
        print("   Make sure the server is running:")
        print("   uv run uvicorn api:app --host 0.0.0.0 --port 8000")
        return 1
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

