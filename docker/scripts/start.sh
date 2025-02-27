#!/bin/bash

# Set up environment
export DISPLAY=:0
export PYTHONPATH=/app/src:$PYTHONPATH

# Create directories if they don't exist
mkdir -p /var/log/supervisor /shared /var/log/agents /app/captures/screenshots /app/captures/html

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf 