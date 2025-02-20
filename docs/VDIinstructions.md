# VDI Setup Instructions

This document provides instructions for setting up and testing the Virtual Desktop Infrastructure (VDI) environment for Zigral using noVNC with Chrome browser.

## Prerequisites

1. Docker and Docker Compose installed
2. Git repository cloned locally
3. `.env` file configured with VNC settings

## Setup Steps

1. **Build the VDI Container**
   ```bash
   docker-compose -f docker-compose.vdi.yml build
   ```

2. **Start the VDI Services**
   ```bash
   docker-compose -f docker-compose.vdi.yml up -d
   ```

3. **Verify Container Status**
   ```bash
   docker-compose -f docker-compose.vdi.yml ps
   ```

4. **Check Container Logs**
   ```bash
   docker-compose -f docker-compose.vdi.yml logs -f
   ```

5. **Access the noVNC Interface**
   - Open your browser and navigate to: `http://34.174.193.245:6080/vnc.html`
   - The VNC viewer will connect automatically

## Testing the Setup

1. **Basic Connectivity Test**
   - Verify the noVNC web interface is accessible at `http://34.174.193.245:6080/vnc.html`
   - Confirm you can see the Chrome browser
   - Test mouse and keyboard interaction

2. **Browser Automation Test**
   - Open Chrome in the VNC session
   - Navigate to a test URL
   - Verify that browser automation commands work

3. **Integration Test**
   - Test the connection between the orchestrator and VNC
   - Verify that agents can control the browser
   - Check that screenshots and recordings work

## Troubleshooting

1. **Connection Issues**
   - Check if the VNC server is running
   - Verify port 6080 is accessible
   - Check container logs for errors

2. **Performance Issues**
   - Adjust screen resolution if needed
   - Check CPU and memory usage
   - Verify network connectivity

## Additional Resources

- [noVNC Documentation](https://novnc.com/docs/index.html)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)

## Security Notes

- Change default passwords in production
- Use proper SSL certificates in production
- Configure resource limits based on actual needs
- Follow principle of least privilege for container permissions

## Resource Limits

Current default limits per container:
- CPU: 2 cores
- Memory: 4GB
- These can be adjusted in `docker-compose.vdi.yml`

## Next Steps

1. Configure production environment
2. Set up monitoring and logging
3. Implement backup strategy
4. Configure auto-scaling (if needed)

## References

- [Kasm Workspaces Documentation](https://www.kasmweb.com/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [Phase 3 Implementation Plan](phase3.md) 