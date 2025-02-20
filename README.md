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
   - Open `http://34.174.193.245:6080/vnc.html` in your browser
   - The VNC viewer will connect automatically to the Chrome environment

## Development

1. **Run Tests**
   ```