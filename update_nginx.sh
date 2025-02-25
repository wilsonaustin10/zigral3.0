#!/bin/bash
echo "Creating nginx configuration for noVNC with WebSocket and CORS support..."
cat > novnc_config.conf << EOF
server {
    listen 6080;
