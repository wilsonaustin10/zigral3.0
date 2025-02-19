# VNC Integration for Zigral 3.0

## Overview
This directory contains the VNC integration components for Zigral 3.0, enabling remote browser access through noVNC.

## Directory Structure
- `config/`: Configuration files
  - `chrome/`: Chrome browser preferences
  - `novnc.nginx.conf`: Nginx configuration for noVNC
  - `novnc.service`: systemd service file
  - `vnc.token`: VNC authentication token
- `docker/`: Docker-related files
  - `Dockerfile`: VNC container configuration
  - `kasm/`: Kasm-specific configurations
- `scripts/`: Management scripts
  - `start-desktop`: Starts the VNC desktop environment
  - `start-novnc`: Starts the noVNC WebSocket proxy
  - `lint.py`: Code linting utility
  - `validate_env.py`: Environment validation

## Configuration
- VNC Server Port: 5900
- noVNC WebSocket Port: 6081
- Nginx SSL Port: 6080
- Production IP: 34.174.193.245

## SSL Certificates
SSL certificates should be placed in `/etc/nginx/ssl/`:
- `/etc/nginx/ssl/novnc.crt`
- `/etc/nginx/ssl/novnc.key`

## Usage
1. Start the desktop environment:
   ```bash
   ./scripts/start-desktop
   ```

2. Start the noVNC service:
   ```bash
   ./scripts/start-novnc
   ```

3. Access via browser:
   ```
   https://34.174.193.245:6080
   ```

## Security Notes
- SSL/TLS is required for production use
- WebSocket connections are secured with SSL/TLS
- CORS is configured for development environment
