# Zigral 3.0 Quick Start Guide

This guide provides the quickest path to get Zigral up and running for development purposes.

## Prerequisites

- Python 3.12 or higher
- Poetry package manager
- Docker Desktop
- Git
- gcloud CLI (for VM interaction)

## Local Development Setup

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/your-org/zigral.git
cd zigral/zigral-vnc

# Install dependencies
poetry install --with test

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration
```

### 2. Start the Application

#### Option A: Run with Docker (Recommended)

```bash
# Start all services with Docker
docker-compose up -d

# Check service status
docker-compose ps
```

#### Option B: Run Services Individually

```bash
# Start all services
./start_all_services.sh

# Or start services individually
cd src
python -m uvicorn orchestrator.orchestrator:app --host 0.0.0.0 --port 8000 &
python -m uvicorn context_manager.main:app --host 0.0.0.0 --port 8001 &
python -m uvicorn agents.vnc.main:app --host 0.0.0.0 --port 8080 &
```

### 3. Start the noVNC Environment

```bash
# Start the development environment with noVNC
./scripts/start_dev_environment.sh
```

### 4. Access the Application

- **Frontend UI**: http://localhost:8090
- **noVNC Desktop**: http://localhost:8901/vnc.html?autoconnect=true
- **API Documentation**: http://localhost:8000/docs

## Working with the VM

### Set Up SSH Tunnels

```bash
# For noVNC (Browser Desktop)
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8901:localhost:6081 -N &

# For UI Server (Vite)
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8090:localhost:5173 -N &
```

### Sync Code with VM

```bash
# Push changes to VM
./scripts/sync-to-vm.sh [optional_file_or_directory]

# Pull changes from VM
./scripts/sync-from-vm.sh [optional_file_or_directory]
```

## Common Tasks

### Run Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific tests
python -m pytest tests/unit/
python -m pytest tests/integration/
```

### Lint Code

```bash
# Lint all code
python scripts/lint.py
```

### Reset Environment

```bash
# Stop and remove all containers
docker-compose down

# Remove volumes (caution: this will delete data)
docker-compose down -v
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using the port
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### VNC Connection Issues

```bash
# Check if VNC server is running
docker-compose logs agent-vm

# Restart VNC services
docker-compose restart agent-vm
```

### Docker Issues

```bash
# Rebuild containers from scratch
docker-compose build --no-cache
docker-compose up -d
```

## Further Documentation

For more detailed information, see:

- [Local Development Guide](local_development.md)
- [noVNC Integration Guide](novnc_integration_guide.md)
- [VM Architecture](vm_architecture.md) 