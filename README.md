# Zigral 3.0

Zigral is an autonomous sales development application that acts as your virtual sales development representative, coordinating multiple specialized agents for tasks like prospecting and data management.

## Features

- Virtual Desktop Infrastructure (VDI) for real-time GUI interactions
- AI-powered sales prospecting
- Automated outreach campaigns
- Integration with LinkedIn and Google Sheets
- Reinforcement learning with human-in-the-loop feedback

## Prerequisites

- Python 3.12 or higher
- Poetry package manager
- Docker Desktop
- Git

## Quick Start

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
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start the VDI Environment**
   ```bash
   docker-compose -f docker-compose.vdi.yml up -d
   ```

5. **Access the VDI Interface**
   - Open `http://34.174.193.245:6080/vnc.html` in your browser
   - The VNC viewer will connect automatically to the Chrome environment

## noVNC Integration

Zigral includes a browser-based VNC client (noVNC) that allows users to view and interact with browser automation in real-time. 

### Quick Start with noVNC

1. Use the startup script to launch the development environment with noVNC:
   ```bash
   ./scripts/start_dev_environment.sh
   ```

2. Access the application:
   - Frontend: http://localhost:8090
   - Direct noVNC: http://localhost:8901/vnc.html?autoconnect=true

### Documentation

For detailed information about the noVNC integration, including setup, configuration, and troubleshooting, see the following documentation:

- [noVNC Integration Guide](docs/novnc_integration_guide.md)
- [VNC Setup](docs/vnc_setup.md)
- [VM Connection Guide](docs/vm_connection.md)

## Development

1. **Run Tests**
   ```