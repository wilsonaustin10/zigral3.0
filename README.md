# Zigral 3.0

**IMPORTANT: The main project code is now located in the `zigral-vnc` directory. Please navigate there for the most up-to-date codebase.**

Zigral is an autonomous sales development application that acts as your virtual sales development representative, coordinating multiple specialized agents for tasks like prospecting and data management.

## Project Structure

This repository has been reorganized for better maintainability:

- **Main Project Code**: Located in the [`zigral-vnc/`](./zigral-vnc/) directory
- **Documentation**: Available in [`zigral-vnc/docs/`](./zigral-vnc/docs/)
- **Local Development**: See [`zigral-vnc/docs/local_development.md`](./zigral-vnc/docs/local_development.md)

## Features

- Virtual Desktop Infrastructure (VDI) for real-time GUI interactions
- AI-powered sales prospecting
- Automated outreach campaigns
- Integration with LinkedIn and Google Sheets
- Reinforcement learning with human-in-the-loop feedback

## noVNC Integration

Zigral includes a browser-based VNC client (noVNC) that allows users to view and interact with browser automation in real-time.

### Quick Start with noVNC

1. Use the startup script to launch the development environment with noVNC:
   ```bash
   cd zigral-vnc
   ./scripts/start_dev_environment.sh
   ```

2. Access the application:
   - Frontend: http://localhost:8090
   - Direct noVNC: http://localhost:8901/vnc.html?autoconnect=true

### Documentation

For detailed information about the noVNC integration, including setup, configuration, and troubleshooting, see the following documentation:

- [noVNC Integration Guide](zigral-vnc/docs/novnc_integration_guide.md)
- [VNC Setup](zigral-vnc/docs/vnc_setup.md)
- [VM Connection Guide](zigral-vnc/docs/vm_connection.md)
- [Local Development](zigral-vnc/docs/local_development.md)
- [Project Cleanup Plan](zigral-vnc/docs/project_cleanup.md)

## Prerequisites

- Python 3.12 or higher
- Poetry package manager
- Docker Desktop
- Git

## Getting Started

Navigate to the main project directory and follow the setup instructions:

```bash
cd zigral-vnc
# See README.md in that directory for further instructions
```