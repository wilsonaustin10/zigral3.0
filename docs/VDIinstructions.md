# Virtual Desktop Infrastructure (VDI) Setup Instructions

## Overview

This document provides instructions for setting up and testing the Virtual Desktop Infrastructure (VDI) environment for Zigral using Kasm Workspaces.

## Prerequisites

- Docker Desktop installed and running
- Python 3.12 or higher
- Poetry package manager
- Git

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-org/zigral.git
   cd zigral
   ```

2. **Install Dependencies**
   ```bash
   poetry install --with test
   ```

3. **Configure Environment**
   - Copy `.env.example` to `.env`
   - Set required environment variables:
     ```bash
     VIRTUAL_DESKTOP_MODE=True
     ENABLE_VIDEO_STREAM=False
     ```

4. **Start the VDI Environment**
   ```bash
   docker-compose -f docker-compose.vdi.yml up -d
   ```

5. **Access the Kasm Web Interface**
   - Open `https://localhost:6901` in your browser
   - Default credentials:
     - Username: kasm_user
     - Password: password123
   - Note: The interface uses a self-signed certificate, so you'll need to accept the security warning

## Testing

1. **Run Integration Tests**
   ```bash
   poetry run pytest tests/integration/test_vdi_setup.py -v
   ```

   This will test:
   - Docker configuration files
   - Container startup
   - Web interface accessibility
   - Resource limits
   - Orchestrator integration

2. **Manual Testing**
   - Verify the Kasm web interface is accessible
   - Check container resource limits
   - Test orchestrator connectivity

## Troubleshooting

1. **Container Not Starting**
   - Check Docker logs: `docker logs <container_id>`
   - Verify port 6901 is not in use
   - Ensure Docker has sufficient resources

2. **Web Interface Not Accessible**
   - Verify Docker is running
   - Check container status: `docker ps`
   - Ensure correct credentials are being used

3. **Authentication Issues**
   - Verify environment variables are set correctly
   - Check container logs for authentication errors

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