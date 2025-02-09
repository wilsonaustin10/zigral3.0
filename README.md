# Zigral 3.0

Zigral is an AI-powered sales prospecting and outreach automation platform.

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
   - Open `https://localhost:6901` in your browser
   - Use the default credentials (change in production):
     - Username: kasm_user
     - Password: password123

## Development

1. **Run Tests**
   ```bash
   # Run all tests
   poetry run pytest
   
   # Run VDI integration tests
   poetry run pytest tests/integration/test_vdi_setup.py -v
   ```

2. **Code Style**
   ```bash
   # Format code
   poetry run black .
   
   # Sort imports
   poetry run isort .
   
   # Lint
   poetry run flake8
   ```

## Documentation

- [VDI Setup Instructions](docs/VDIinstructions.md)
- [Phase 3 Implementation Plan](docs/phase3.md)
- [Development Guide](docs/development.md)

## Architecture

Zigral consists of several components:
- VDI Environment (Kasm Workspaces)
- Orchestrator Service
- Context Manager
- Agent Services (Lincoln, Shaun)
- PostgreSQL Database

## Security

- Change default passwords in production
- Use proper SSL certificates
- Follow security best practices in [VDI Instructions](docs/VDIinstructions.md)

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here] 