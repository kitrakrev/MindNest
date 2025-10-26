#!/bin/bash
#
# Start the Rock-Paper-Scissors API Server
#
# Usage: ./start_server.sh
#

echo "Starting Rock-Paper-Scissors API Server..."
echo ""
echo "The server will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Interactive Docs: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

cd "$(dirname "$0")"
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload

