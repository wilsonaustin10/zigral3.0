#!/bin/bash

# Update package list
sudo apt-get update

# Install required packages
sudo apt-get install -y x11vnc xvfb chromium-browser

# Create directory for VNC password
mkdir -p ~/.vnc

# Create Xvfb service
sudo tee /etc/systemd/system/xvfb.service << EOF
[Unit]
Description=X Virtual Frame Buffer Service
After=network.target

[Service]
ExecStart=/usr/bin/Xvfb :0 -screen 0 1920x1080x24
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create x11vnc service
sudo tee /etc/systemd/system/x11vnc.service << EOF
[Unit]
Description=X11 VNC Server
After=xvfb.service
Requires=xvfb.service

[Service]
Environment=DISPLAY=:0
ExecStart=/usr/bin/x11vnc -display :0 -forever -shared -nopw
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create Chrome autostart service
sudo tee /etc/systemd/system/chrome.service << EOF
[Unit]
Description=Chrome Browser Service
After=x11vnc.service
Requires=x11vnc.service

[Service]
Environment=DISPLAY=:0
ExecStart=/usr/bin/chromium-browser --no-sandbox --start-maximized --disable-gpu
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable xvfb.service
sudo systemctl enable x11vnc.service
sudo systemctl enable chrome.service

sudo systemctl start xvfb.service
sudo systemctl start x11vnc.service
sudo systemctl start chrome.service

# Check service status
echo "Checking service status..."
sudo systemctl status xvfb.service
sudo systemctl status x11vnc.service
sudo systemctl status chrome.service
sudo systemctl status novnc.service 