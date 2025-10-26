#!/usr/bin/env python3
"""Simple runner script for the Chat Simulator API."""
import sys
import os

# Add current directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    print("🎭 Starting Chat Simulator API...")
    print("   API docs: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

