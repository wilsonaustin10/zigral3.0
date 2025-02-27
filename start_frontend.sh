#!/bin/bash
# Start the Zigral Frontend Server with Docker VNC integration

set -e

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR"

# Clean and reinstall the noVNC library
echo "Cleaning previous noVNC installation..."
rm -rf src/ui/public/novnc src/ui/novnc tmp_novnc

echo "Installing noVNC library..."
# Create necessary directories
mkdir -p src/ui/public

# Clone noVNC repository to a temporary directory
git clone https://github.com/novnc/noVNC.git tmp_novnc --depth 1

# Create target directory and preserve the correct structure
mkdir -p src/ui/public/novnc
mkdir -p src/ui/public/novnc/core/util
mkdir -p src/ui/public/novnc/core/input
mkdir -p src/ui/public/novnc/vendor

# Copy core files (no symlinks)
echo "Copying core files..."
cp -r tmp_novnc/core/*.js src/ui/public/novnc/core/ || echo "Warning: Some core/*.js files might be missing"
cp -r tmp_novnc/core/util/*.js src/ui/public/novnc/core/util/ || echo "Warning: Some util/*.js files might be missing"
cp -r tmp_novnc/core/input/*.js src/ui/public/novnc/core/input/ || echo "Warning: Some input/*.js files might be missing"

# Copy vendor files correctly
echo "Copying vendor files..."
if [ -d "tmp_novnc/vendor/pako" ]; then
    mkdir -p src/ui/public/novnc/vendor/pako
    cp -r tmp_novnc/vendor/pako/*.js src/ui/public/novnc/vendor/pako/ || echo "Warning: No pako/*.js files found"
else
    # Try alternative paths
    mkdir -p src/ui/public/novnc/vendor
    cp -r tmp_novnc/vendor/* src/ui/public/novnc/vendor/ || echo "Warning: No vendor files found"
fi

# Copy the main HTML file
cp tmp_novnc/vnc.html src/ui/public/novnc/index.html || echo "Warning: vnc.html not found"

# Verify the copy was successful
echo "Verifying copied files:"
find src/ui/public/novnc -type f | wc -l

# Remove the temporary directory
rm -rf tmp_novnc

echo "NoVNC library installed successfully"

# Ensure Docker container is running before starting the frontend
echo "Checking if VNC Docker container is running..."
if ! docker ps | grep -q zigral-vnc; then
    echo "Starting VNC Docker container..."
    # Check if the container exists but is stopped
    if docker ps -a | grep -q zigral-vnc; then
        docker start zigral-vnc
    else
        docker run -d -p 5902:5900 -p 6082:6080 --name zigral-vnc zigral-vnc-simple
    fi
    echo "Waiting for container to initialize..."
    sleep 5
fi

# Set up environment variables for local Docker
export FRONTEND_PORT=${FRONTEND_PORT:-8090}
export VNC_HOST=${VNC_HOST:-localhost}
export VNC_PORT=${VNC_PORT:-6082}

# Change to the UI directory
cd src/ui

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start the frontend server
echo "Starting Zigral frontend server on port $FRONTEND_PORT..."
echo "VNC connection configured for $VNC_HOST:$VNC_PORT"

# Start server using Vite
npm run dev -- --port $FRONTEND_PORT

echo "Frontend server stopped" 