#!/bin/bash
# Master demo script for Zigral VNC integration

# Set up script variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$SCRIPT_DIR/demo.log"
CONTAINER_NAME="zigral-vnc-chromium"
FRONTEND_PORT=8090
VNC_PORT=5900
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"

# Start logging
echo "Starting Zigral VNC demo at $(date)" | tee -a "$LOG_FILE"
echo "=========================" | tee -a "$LOG_FILE"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "ERROR: Docker is not running. Please start Docker and try again." | tee -a "$LOG_FILE"
        exit 1
    fi
}

# Function to stop existing containers
stop_existing_containers() {
    echo "Stopping any existing containers..." | tee -a "$LOG_FILE"
    docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
    docker ps -q --filter "expose=$VNC_PORT" | xargs -r docker stop > /dev/null 2>&1 || true
}

# Function to start the VNC container
start_vnc_container() {
    echo "Starting VNC container ($CONTAINER_NAME)..." | tee -a "$LOG_FILE"
    docker run --rm -d -p $VNC_PORT:5900 -p 6080:6080 -p 6081:6081 -p 9222:9222 --name $CONTAINER_NAME zigral-vnc-agent-vm-chromium
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to start VNC container" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    echo "Waiting for VNC server to initialize..." | tee -a "$LOG_FILE"
    sleep 5
    
    # Check if container is running
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "ERROR: VNC container is not running" | tee -a "$LOG_FILE"
        exit 1
    fi
    
    echo "VNC container started successfully" | tee -a "$LOG_FILE"
}

# Function to start the frontend server
start_frontend() {
    echo "Starting frontend server on port $FRONTEND_PORT..." | tee -a "$LOG_FILE"
    cd "$SCRIPT_DIR"
    
    # Make sure start_frontend.sh is executable
    chmod +x "$SCRIPT_DIR/start_frontend.sh"
    
    # Start the frontend server in the background
    FRONTEND_PID=""
    export FRONTEND_PORT=$FRONTEND_PORT
    export VNC_HOST="localhost"
    export VNC_PORT=6080
    
    "$SCRIPT_DIR/start_frontend.sh" > frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # Wait for the frontend to start
    echo "Waiting for frontend server to start..." | tee -a "$LOG_FILE"
    sleep 5
    
    # Check if frontend is running
    if ! curl -s "http://localhost:${FRONTEND_PORT}" > /dev/null; then
        echo "ERROR: Frontend server failed to start" | tee -a "$LOG_FILE"
        cat frontend.log | tee -a "$LOG_FILE"
        exit 1
    fi
    
    echo "Frontend server started successfully (PID: $FRONTEND_PID)" | tee -a "$LOG_FILE"
}

# Function to run the demo scripts
run_demos() {
    echo "Running demo scripts..." | tee -a "$LOG_FILE"
    cd "$SCRIPT_DIR"
    
    # Set environment variables for demos
    export FRONTEND_URL=$FRONTEND_URL
    export GOOGLE_EMAIL=${GOOGLE_EMAIL:-"demo@example.com"}
    export GOOGLE_PASSWORD=${GOOGLE_PASSWORD:-"demopassword"}
    export TEST_SHEET_ID=${TEST_SHEET_ID:-"1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"}
    
    # Run the VNC connection demo
    echo "Running VNC connection demo..." | tee -a "$LOG_FILE"
    "$SCRIPT_DIR/src/agents/demo_vnc.py"
    
    # Let the user know how to access the frontend
    echo "=================================" | tee -a "$LOG_FILE"
    echo "Frontend is running at: $FRONTEND_URL" | tee -a "$LOG_FILE"
    echo "You can also connect directly to VNC on port $VNC_PORT" | tee -a "$LOG_FILE"
    echo "=================================" | tee -a "$LOG_FILE"
    
    # Ask if user wants to run the Google Sheets demo
    read -p "Do you want to run the Google Sheets demo? (requires real Google credentials) [y/N] " run_sheets
    if [[ "$run_sheets" =~ ^[Yy]$ ]]; then
        # Prompt for real credentials if not set
        if [[ "$GOOGLE_EMAIL" == "demo@example.com" ]]; then
            read -p "Enter your Google email: " GOOGLE_EMAIL
            read -sp "Enter your Google password: " GOOGLE_PASSWORD
            echo ""
            export GOOGLE_EMAIL
            export GOOGLE_PASSWORD
        fi
        
        echo "Running Shaun agent demo with VNC..." | tee -a "$LOG_FILE"
        "$SCRIPT_DIR/src/agents/shaun/demo_shaun_vnc.py"
    fi
}

# Function for cleanup
cleanup() {
    echo "Cleaning up..." | tee -a "$LOG_FILE"
    
    # Kill the frontend server
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID > /dev/null 2>&1 || true
    fi
    
    # Stop the container
    docker stop $CONTAINER_NAME > /dev/null 2>&1 || true
    
    echo "Cleanup completed" | tee -a "$LOG_FILE"
}

# Set up trap to handle interruptions
trap cleanup EXIT

# Main execution
check_docker
stop_existing_containers
start_vnc_container
start_frontend
run_demos

# Let the server run until user stops it
echo "Press Ctrl+C to stop the demo" | tee -a "$LOG_FILE"
wait $FRONTEND_PID 