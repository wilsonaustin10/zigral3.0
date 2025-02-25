#!/bin/bash

# Script to start the Zigral development environment with noVNC
# Usage: ./start_dev_environment.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Zigral Development Environment${NC}"

# Kill any existing SSH tunnels
echo -e "${YELLOW}Cleaning up existing SSH tunnels...${NC}"
pkill -f "ssh.*:8090" 2>/dev/null
pkill -f "ssh.*:8901" 2>/dev/null
sleep 1

# Start the Vite development server in the background
echo -e "${YELLOW}Starting Vite development server...${NC}"
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c --command="cd /home/wilson_austin10/zigral-vnc/src/ui && npm run dev -- --host 0.0.0.0" &
VITE_PID=$!
sleep 5

# Determine which port Vite is using
echo -e "${YELLOW}Checking Vite server port...${NC}"
VITE_PORT=$(gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c --command="netstat -tulpn 2>/dev/null | grep node | grep -oP '(?<=:)[0-9]+(?= )'")

if [ -z "$VITE_PORT" ]; then
  echo -e "${YELLOW}Couldn't determine Vite port, defaulting to 5173${NC}"
  VITE_PORT=5173
else
  echo -e "${GREEN}Vite server is running on port $VITE_PORT${NC}"
fi

# Create SSH tunnels
echo -e "${YELLOW}Creating SSH tunnels...${NC}"
echo -e "${YELLOW}Creating tunnel for Vite server (localhost:8090 -> remote:$VITE_PORT)${NC}"
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8090:localhost:$VITE_PORT -N &
TUNNEL1_PID=$!

echo -e "${YELLOW}Creating tunnel for noVNC (localhost:8901 -> remote:6080)${NC}"
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8901:localhost:6080 -N &
TUNNEL2_PID=$!

sleep 3

# Check if tunnels are established
if ps -p $TUNNEL1_PID > /dev/null && ps -p $TUNNEL2_PID > /dev/null; then
    echo -e "${GREEN}SSH tunnels established successfully.${NC}"
    echo -e "${GREEN}You can now access:${NC}"
    echo -e "${GREEN}  - Frontend: http://localhost:8090${NC}"
    echo -e "${GREEN}  - noVNC: http://localhost:8901/vnc.html?autoconnect=true${NC}"
else
    echo -e "${RED}Failed to establish one or more SSH tunnels.${NC}"
    echo -e "${YELLOW}You might need to run this script again or manually create the tunnels.${NC}"
fi

echo -e "${YELLOW}To stop the development environment, press Ctrl+C or run: pkill -f 'ssh.*:8090' && pkill -f 'ssh.*:8901'${NC}"

# Keep the script running to maintain the tunnels
wait $TUNNEL1_PID $TUNNEL2_PID 