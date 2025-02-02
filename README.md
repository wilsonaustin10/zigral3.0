# Zigral 3.0

Zigral is an advanced automation platform that orchestrates multiple AI agents to perform complex, repetitive sales prospecting and outreach tasks. The system uses a combination of LLM-powered decision making and specialized agents to execute tasks efficiently and intelligently.

## Features

- **Intelligent Orchestration**: Central orchestrator that coordinates multiple AI agents
- **Context Management**: Dedicated microservice for managing and persisting task context
- **Modular Architecture**: Extensible design allowing easy addition of new agents and capabilities
- **Smart Decision Making**: LLM-powered action planning and execution

## Project Structure

```
zigral/
├── src/
│   ├── orchestrator/      # Core orchestration logic
│   ├── context_manager/   # Context management service
│   └── main.py           # Application entry point
├── tests/                # Test suite
└── [other configuration files]
```

## Setup

1. Clone the repository
2. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
3. Install dependencies:
   ```bash
   poetry install
   ```
4. Copy `.env.example` to `.env` and configure your environment variables
5. Activate the virtual environment:
   ```bash
   poetry shell
   ```
6. Run the application:
   ```bash
   python src/main.py
   ```

## Development

- Follow PEP 8 style guide for Python code
- Write tests for new features
- Update documentation as needed
- For deployment, generate requirements.txt:
  ```bash
  poetry export -f requirements.txt --output requirements.txt
  ```

## License

[License terms to be determined] 