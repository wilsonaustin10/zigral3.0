#!/bin/bash
set -e

# Create required directories
mkdir -p /var/log/nginx
mkdir -p /var/log/supervisor
mkdir -p /var/log/agents

# Set up VNC password if provided
if [ ! -z "$VNC_PASSWORD" ]; then
    mkdir -p /root/.vnc
    x11vnc -storepasswd "$VNC_PASSWORD" /root/.vnc/passwd
fi

# Ensure correct permissions
chown -R root:root /root/.vnc
chmod 600 /root/.vnc/passwd 2>/dev/null || true

# Start Xvfb and wait for it
Xvfb :0 -screen 0 $RESOLUTION &
sleep 2

# Check if Xvfb is running
if ! ps aux | grep -v grep | grep Xvfb > /dev/null; then
    echo "Failed to start Xvfb"
    exit 1
fi

# Set DISPLAY
export DISPLAY=:0

# Start supervisord
exec /usr/bin/supervisord -n -c /etc/supervisor/conf.d/supervisord.conf 