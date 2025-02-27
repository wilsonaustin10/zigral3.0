# Zigral 3.0 VNC Integration Documentation

## Overview
This document outlines the integration of a VNC-based remote desktop solution for Zigral 3.0, using Docker containers, noVNC for browser-based access, and a Vite-based frontend.

## Connection Details
- **noVNC Direct URL**: http://localhost:6082/vnc.html
- **Frontend VNC UI**: http://localhost:8090/ui/
- **VNC Password**: `zigral`

## Architecture
The solution consists of:
1. **Docker Container**: Running Ubuntu with Xvfb, x11vnc, fluxbox, and websockify
2. **noVNC Client**: Browser-based VNC client library
3. **Frontend UI**: Custom Vite-based UI that embeds the VNC client

## Docker Container Setup
Our Docker container (`zigral-vnc-simple`) runs:
- **Xvfb**: Virtual framebuffer X server
- **x11vnc**: VNC server that shares the Xvfb display
- **fluxbox**: Lightweight window manager
- **websockify**: WebSocket-to-TCP proxy for noVNC communication

### Key Configurations
- **Display**: `:1` (DISPLAY=:1)
- **Resolution**: 1280x800 (VNC_RESOLUTION=1280x800)
- **Password**: `zigral` (VNC_PASSWORD=zigral)
- **VNC Port**: 5900 (mapped to host port 5902)
- **WebSocket Port**: 6080 (mapped to host port 6082)

## Common Issues & Solutions

### 1. Service Initialization & Dependencies
- **Problem**: Services starting in wrong order, causing failures
- **Solution**: 
  - Use supervisord priority settings (1 for Xvfb, 10 for x11vnc, etc.)
  - Implement wait scripts that check for X11 socket readiness
  - Use explicit dependencies in service configuration

### 2. Symbolic Link Issues
- **Problem**: `ELOOP: too many symbolic links encountered` when using novnc
- **Solution**:
  - Avoid symlinks by copying files directly
  - Maintain proper directory structure when copying noVNC files
  - Use absolute paths where possible

### 3. Port Conflicts
- **Problem**: Docker container port bindings failing
- **Solution**:
  - Check for running containers with `docker ps -a`
  - Use alternative port mappings (5902:5900, 6082:6080)
  - Update all references to ports in frontend code

### 4. noVNC Web Integration
- **Problem**: Files not found or incorrect paths
- **Solution**:
  - Ensure proper directory structure in public folder
  - Update paths in JS files to match actual file locations
  - Use direct imports rather than dynamic loading where possible

## Frontend Integration
The frontend integration uses:
- A custom VNC client wrapper in `js/vnc-client.js`
- Environmental configuration in `.env`
- HTML structure in `index.html`

### Key Files:
1. **vnc-client.js**: Connects to WebSocket and renders VNC display
2. **.env**: Contains connection parameters
3. **start_frontend.sh**: Sets up noVNC libraries and starts the Vite server

## Startup Procedure
1. Build the Docker image: `docker build -t zigral-vnc-simple -f Dockerfile.simple .`
2. Run the container: `docker run -d -p 5902:5900 -p 6082:6080 --name zigral-vnc zigral-vnc-simple`
3. Start the frontend: `./start_frontend.sh`

## Troubleshooting

### VNC Connection Issues
- Check container logs: `docker logs zigral-vnc`
- Verify ports are open: `curl -I http://localhost:6082`
- Check for port conflicts: `lsof -i :6082` or `lsof -i :5902`

### Frontend Issues
- Check for symbolic link errors in noVNC installation
- Verify correct WebSocket URL in vnc-client.js
- Confirm environment variables in .env match Docker port mappings

## Lessons Learned
1. **Process Order Matters**: X server must be fully initialized before VNC server
2. **Proper Port Mapping**: Ensure consistency across all configuration points
3. **File Structure**: Maintain correct paths without symlinks
4. **Diagnostic Scripts**: Include detailed logging for troubleshooting
5. **Container Health Checks**: Ensure services are actually running, not just started

## Future Improvements
1. Implement secure WebSocket (wss://) for production
2. Add authentication to noVNC access
3. Improve error handling and reconnection logic
4. Add container health monitoring
5. Consider using docker-compose for service orchestration 