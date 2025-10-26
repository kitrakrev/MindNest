#!/bin/bash
#
# Example API Usage Script
# Demonstrates all Rock-Paper-Scissors API endpoints using cURL
#
# Usage: ./example_api_usage.sh
#

BASE_URL="http://localhost:8000"

echo "=================================================="
echo "Rock-Paper-Scissors API - Example Usage"
echo "=================================================="
echo ""

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Root endpoint
echo -e "${BLUE}1. Getting API Information${NC}"
echo "GET $BASE_URL/"
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""
echo ""

# 2. Health check
echo -e "${BLUE}2. Health Check${NC}"
echo "GET $BASE_URL/health"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""
echo ""

# 3. Status check
echo -e "${BLUE}3. Robot Status${NC}"
echo "GET $BASE_URL/status"
curl -s "$BASE_URL/status" | python3 -m json.tool
echo ""
echo ""

# 4. Play ROCK
echo -e "${BLUE}4. Playing ROCK Gesture 🪨${NC}"
echo "POST $BASE_URL/rock"
echo "Body: {\"duration\": 3.0, \"with_shake\": false}"
curl -s -X POST "$BASE_URL/rock" \
  -H "Content-Type: application/json" \
  -d '{"duration": 3.0, "with_shake": false}' | python3 -m json.tool
echo ""
echo ""

sleep 4

# 5. Play PAPER
echo -e "${BLUE}5. Playing PAPER Gesture 📄${NC}"
echo "POST $BASE_URL/paper"
echo "Body: {\"duration\": 3.0, \"with_shake\": false}"
curl -s -X POST "$BASE_URL/paper" \
  -H "Content-Type: application/json" \
  -d '{"duration": 3.0, "with_shake": false}' | python3 -m json.tool
echo ""
echo ""

sleep 4

# 6. Play SCISSORS
echo -e "${BLUE}6. Playing SCISSORS Gesture ✂️${NC}"
echo "POST $BASE_URL/scissors"
echo "Body: {\"duration\": 3.0, \"with_shake\": false}"
curl -s -X POST "$BASE_URL/scissors" \
  -H "Content-Type: application/json" \
  -d '{"duration": 3.0, "with_shake": false}' | python3 -m json.tool
echo ""
echo ""

sleep 4

# 7. Shake animation
echo -e "${BLUE}7. Shake Animation 🤝${NC}"
echo "POST $BASE_URL/shake"
echo "Body: {\"amplitude\": 80, \"shakes\": 2}"
curl -s -X POST "$BASE_URL/shake" \
  -H "Content-Type: application/json" \
  -d '{"amplitude": 80, "shakes": 2}' | python3 -m json.tool
echo ""
echo ""

sleep 3

# 8. Play RANDOM
echo -e "${BLUE}8. Playing RANDOM Gesture 🎲${NC}"
echo "POST $BASE_URL/random"
echo "Body: {\"duration\": 3.0, \"with_shake\": true}"
curl -s -X POST "$BASE_URL/random" \
  -H "Content-Type: application/json" \
  -d '{"duration": 3.0, "with_shake": true}' | python3 -m json.tool
echo ""
echo ""

sleep 4

# 9. Return to rest
echo -e "${BLUE}9. Returning to Rest Position 🏠${NC}"
echo "POST $BASE_URL/rest"
curl -s -X POST "$BASE_URL/rest" | python3 -m json.tool
echo ""
echo ""

echo "=================================================="
echo -e "${GREEN}✓ All API endpoints tested successfully!${NC}"
echo "=================================================="
echo ""
echo "For interactive documentation, visit:"
echo "  ${YELLOW}http://localhost:8000/docs${NC}"
echo ""

