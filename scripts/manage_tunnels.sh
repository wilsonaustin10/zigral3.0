#!/bin/bash

# Script to manage SSH tunnels for Zigral development
# Author: AI Assistant
# Date: 2023-11-28

# Constants
VM_INSTANCE="zigral-chrome-embed"
ZONE="us-south1-c"
USER="wilson_austin10"
NOVNC_LOCAL_PORT=8901
NOVNC_REMOTE_PORT=6081
VITE_LOCAL_PORT=8090
VITE_REMOTE_PORT=5173

# ANSI color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a tunnel is already running
check_tunnel() {
    local port=$1
    if pgrep -f "ssh.*:$port" > /dev/null; then
        return 0 # Tunnel is running
    else
        return 1 # Tunnel is not running
    fi
}

# Function to start a tunnel
start_tunnel() {
    local local_port=$1
    local remote_port=$2
    local tunnel_name=$3

    if check_tunnel $local_port; then
        echo -e "${YELLOW}Tunnel for $tunnel_name already running on port $local_port${NC}"
    else
        echo -e "${BLUE}Starting $tunnel_name tunnel on port $local_port -> $remote_port...${NC}"
        gcloud compute ssh ${USER}@${VM_INSTANCE} --zone=${ZONE} -- -L ${local_port}:localhost:${remote_port} -N &
        sleep 1
        if check_tunnel $local_port; then
            echo -e "${GREEN}$tunnel_name tunnel started successfully!${NC}"
        else
            echo -e "${RED}Failed to start $tunnel_name tunnel!${NC}"
        fi
    fi
}

# Function to stop a tunnel
stop_tunnel() {
    local port=$1
    local tunnel_name=$2
    
    if check_tunnel $port; then
        echo -e "${BLUE}Stopping $tunnel_name tunnel on port $port...${NC}"
        pkill -f "ssh.*:$port" 2>/dev/null
        sleep 1
        if ! check_tunnel $port; then
            echo -e "${GREEN}$tunnel_name tunnel stopped successfully!${NC}"
        else
            echo -e "${RED}Failed to stop $tunnel_name tunnel!${NC}"
        fi
    else
        echo -e "${YELLOW}No $tunnel_name tunnel running on port $port${NC}"
    fi
}

# Function to show tunnel status
show_status() {
    echo -e "${BLUE}Checking tunnel status...${NC}"
    
    if check_tunnel $NOVNC_LOCAL_PORT; then
        echo -e "${GREEN}✓ noVNC tunnel is running${NC} (localhost:$NOVNC_LOCAL_PORT -> $VM_INSTANCE:$NOVNC_REMOTE_PORT)"
        echo -e "  Access URL: ${BLUE}http://localhost:$NOVNC_LOCAL_PORT/vnc.html?autoconnect=true${NC}"
    else
        echo -e "${RED}✗ noVNC tunnel is not running${NC}"
    fi
    
    if check_tunnel $VITE_LOCAL_PORT; then
        echo -e "${GREEN}✓ Vite UI tunnel is running${NC} (localhost:$VITE_LOCAL_PORT -> $VM_INSTANCE:$VITE_REMOTE_PORT)"
        echo -e "  Access URL: ${BLUE}http://localhost:$VITE_LOCAL_PORT${NC}"
    else
        echo -e "${RED}✗ Vite UI tunnel is not running${NC}"
    fi
}

# Function to print usage
usage() {
    echo -e "${BLUE}Zigral SSH Tunnel Manager${NC}"
    echo ""
    echo -e "Usage: $0 [command]"
    echo ""
    echo -e "Commands:"
    echo -e "  ${GREEN}start${NC}       Start all tunnels"
    echo -e "  ${GREEN}stop${NC}        Stop all tunnels"
    echo -e "  ${GREEN}restart${NC}     Restart all tunnels"
    echo -e "  ${GREEN}status${NC}      Show tunnel status"
    echo -e "  ${GREEN}start-novnc${NC} Start only noVNC tunnel"
    echo -e "  ${GREEN}start-vite${NC}  Start only Vite UI tunnel"
    echo -e "  ${GREEN}stop-novnc${NC}  Stop only noVNC tunnel"
    echo -e "  ${GREEN}stop-vite${NC}   Stop only Vite UI tunnel"
    echo -e "  ${GREEN}help${NC}        Show this help message"
    echo ""
    echo -e "Example: $0 start"
}

# Main logic
case "$1" in
    start)
        start_tunnel $NOVNC_LOCAL_PORT $NOVNC_REMOTE_PORT "noVNC"
        start_tunnel $VITE_LOCAL_PORT $VITE_REMOTE_PORT "Vite UI"
        show_status
        ;;
    stop)
        stop_tunnel $NOVNC_LOCAL_PORT "noVNC"
        stop_tunnel $VITE_LOCAL_PORT "Vite UI"
        ;;
    restart)
        stop_tunnel $NOVNC_LOCAL_PORT "noVNC"
        stop_tunnel $VITE_LOCAL_PORT "Vite UI"
        sleep 1
        start_tunnel $NOVNC_LOCAL_PORT $NOVNC_REMOTE_PORT "noVNC"
        start_tunnel $VITE_LOCAL_PORT $VITE_REMOTE_PORT "Vite UI"
        show_status
        ;;
    status)
        show_status
        ;;
    start-novnc)
        start_tunnel $NOVNC_LOCAL_PORT $NOVNC_REMOTE_PORT "noVNC"
        ;;
    start-vite)
        start_tunnel $VITE_LOCAL_PORT $VITE_REMOTE_PORT "Vite UI"
        ;;
    stop-novnc)
        stop_tunnel $NOVNC_LOCAL_PORT "noVNC"
        ;;
    stop-vite)
        stop_tunnel $VITE_LOCAL_PORT "Vite UI"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        usage
        exit 1
        ;;
esac

exit 0 