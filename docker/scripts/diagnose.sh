#!/bin/bash

# Script to diagnose supervisord issues
echo "===== DIAGNOSTIC INFORMATION ====="

# Check if supervisord and other critical binaries exist
echo "Checking for required binaries..."
which supervisord || echo "supervisord is missing!"
which Xvfb || echo "Xvfb is missing!"
which x11vnc || echo "x11vnc is missing!"
which nginx || echo "nginx is missing!"
which websockify || echo "websockify is missing!"
which chromium || echo "chromium is missing!"

# Check the supervisord.conf file
echo -e "\nChecking supervisord config file..."
if [ -f /etc/supervisor/conf.d/supervisord.conf ]; then
    echo "Config file exists at /etc/supervisor/conf.d/supervisord.conf"
    supervisord -c /etc/supervisor/conf.d/supervisord.conf -n -v 2>&1 | tee /tmp/supervisord_debug.log
else
    echo "Config file is missing!"
fi

# Check for permissions issues
echo -e "\nChecking permissions..."
ls -la /var/run/ /var/log/supervisor/ /etc/supervisor/conf.d/

# Check for VNC password issues
echo -e "\nChecking VNC environment variables..."
echo "VNC_PASSWORD: ${VNC_PASSWORD:-not set}"

# Try to run key processes manually to see what errors they might report
echo -e "\nTrying to start processes manually..."
Xvfb :0 -screen 0 ${RESOLUTION:-1920x1080x24} & 
PID_XVFB=$!
sleep 2
kill $PID_XVFB

echo -e "\nTrying VNC server..."
x11vnc -display :0 -forever -shared -rfbport 5900 & 
PID_VNC=$!
sleep 2
kill $PID_VNC

echo "===== END DIAGNOSTIC INFORMATION =====" 