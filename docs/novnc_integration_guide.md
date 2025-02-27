# noVNC Integration Guide

## Overview

This document details the process for integrating noVNC with the Zigral application, including configuration, troubleshooting, and maintenance procedures.

## Architecture

- **Server**: GCP VM instance (zigral-chrome-embed)
- **Components**:
  - Xvfb: Virtual framebuffer X server
  - x11vnc: VNC server sharing the virtual display
  - websockify: WebSocket to TCP proxy for VNC connections
  - noVNC: HTML5 VNC client
  - nginx: Web server and reverse proxy
  - Vite: Development server for the frontend application

## Installation and Configuration

### 1. Server Components Setup

These components should already be installed on the VM:

```bash
# Install required packages
sudo apt-get update
sudo apt-get install -y xvfb x11vnc novnc nginx

# Configure Xvfb to start a virtual display
sudo Xvfb :0 -screen 0 1920x1080x24 &

# Start VNC server sharing the virtual display
sudo x11vnc -display :0 -forever -shared &

# Start websockify to proxy VNC connections
sudo websockify --web /usr/share/novnc --heartbeat 30 --verbose 6081 localhost:5900 &
```

### 2. Nginx Configuration

The nginx configuration includes a server block for noVNC:

```
server {
    listen 6080;
    
    # Root directory for noVNC files
    root /usr/share/novnc;
    
    # Allow access from any origin
    add_header Access-Control-Allow-Origin *;
    
    # WebSocket proxy location
    location /websockify {
        proxy_pass http://localhost:6081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
        proxy_buffer_size 8k;
        proxy_buffering off;
    }
}
```

To apply changes to nginx:
```bash
sudo nginx -t  # Test configuration
sudo systemctl restart nginx  # Apply configuration
```

### 3. Frontend Integration

The frontend includes an iframe to embed the noVNC client:

```html
<iframe id="vnc-iframe"
    class="workspace-frame"
    src="http://localhost:8901/vnc.html?autoconnect=true"
    frameborder="0"
    allowfullscreen="true"
    title="VNC Workspace">
</iframe>
```

**Important**: Ensure the iframe has only one `src` attribute to avoid syntax errors.

## SSH Tunneling

To access the development server and noVNC from your local machine, use SSH tunneling:

```bash
# For Vite development server (adjust port as needed)
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8090:localhost:5173 -N &

# For direct noVNC access
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8901:localhost:6080 -N &
```

## Starting the Development Environment

1. Start the Vite development server:
```bash
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c --command="cd /home/wilson_austin10/zigral-vnc/src/ui && npm run dev -- --host 0.0.0.0"
```

2. Create SSH tunnels:
```bash
# Check which port Vite is using (it may choose 5173, 5174, etc.)
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8090:localhost:5173 -N &

# For noVNC
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8901:localhost:6080 -N &
```

3. Access the application:
   - Frontend: http://localhost:8090
   - Direct noVNC: http://localhost:8901/vnc.html?autoconnect=true

## Troubleshooting

### Common Issues

1. **502 Bad Gateway When Accessing noVNC**
   - Check if websockify is running: `ps aux | grep -v grep | grep websockify`
   - Verify nginx configuration
   - Ensure ports 6080 and 6081 are available

2. **Connection Refused for SSH Tunnels**
   - Verify the target port is active on the remote server
   - Check for conflicting local ports
   - Kill existing tunnels: `pkill -f "ssh.*:PORT"`

3. **HTML Parsing Errors**
   - Check for invalid HTML syntax, especially in the iframe element
   - Look for duplicate attributes (like multiple `src` attributes)

4. **Port Already in Use**
   - Find the process using the port: `sudo lsof -i :PORT`
   - Kill the process or use a different port

### Verification Commands

```bash
# Check if nginx is listening on port 6080
sudo netstat -tulpn | grep nginx

# Check nginx configuration
sudo nginx -t

# View nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: localhost:6080" -H "Origin: http://localhost:6080" http://localhost:6080/websockify

# View active SSH tunnels
ps aux | grep ssh
```

## Maintenance Procedures

### Restarting Services

```bash
# Restart Xvfb
sudo systemctl restart xvfb

# Restart x11vnc
sudo systemctl restart x11vnc

# Restart websockify
sudo systemctl restart websockify

# Restart nginx
sudo systemctl restart nginx

# Restart development server
cd /home/wilson_austin10/zigral-vnc/src/ui && npm run dev -- --host 0.0.0.0
```

### Updating Configuration

1. Edit nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/novnc
```

2. Create symbolic link (if it doesn't exist):
```bash
sudo ln -sf /etc/nginx/sites-available/novnc /etc/nginx/sites-enabled/
```

3. Test and apply:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

## References

- [noVNC Documentation](https://novnc.com/info.html)
- [WebSocket Protocol RFC6455](https://tools.ietf.org/html/rfc6455)
- [nginx WebSocket Proxy Documentation](https://nginx.org/en/docs/http/websocket.html) 