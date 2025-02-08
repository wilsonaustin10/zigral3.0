# Development Guide

## Overview

This guide covers development practices, tools, and workflows for the Zigral project.

## Development Environment Setup

1. **Prerequisites**:
   - Python 3.12+
   - Poetry (package manager)
   - Docker and Docker Compose
   - Git

2. **Initial Setup**:
   ```bash
   # Clone the repository
   git clone https://github.com/wilsonaustin10/zigral3.0.git
   cd zigral3.0

   # Install dependencies
   poetry install

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Code Quality Tools

The project enforces code quality through multiple tools:

### 1. Black (Code Formatter)
- Line length: 88 characters
- Python target version: 3.12
- Usage:
  ```bash
  poetry run black .  # Format code
  poetry run black . --check  # Check formatting
  ```

### 2. isort (Import Sorter)
- Profile: black (for compatibility)
- Import sections:
  1. FUTURE
  2. STDLIB
  3. THIRDPARTY
  4. FIRSTPARTY (orchestrator, context_manager, agents)
  5. LOCALFOLDER
- Usage:
  ```bash
  poetry run isort .  # Sort imports
  poetry run isort . --check-only --diff  # Check import sorting
  ```

### 3. Flake8 (Linter)
- Max line length: 88 (matching Black)
- Ignored rules:
  - E203: Whitespace before ':'
  - W503: Line break before binary operator
- Configuration in `.flake8`
- Usage:
  ```bash
  poetry run flake8  # Run linter
  ```

### 4. Combined Commands
```bash
poetry run lint    # Run all checks (black, isort, flake8)
poetry run format  # Format code (black, isort)
```

## Testing

### Test Structure
```
tests/
├── agents/           # Agent-specific tests
│   ├── lincoln/      # LinkedIn Agent tests
│   └── shaun/        # Google Sheets Agent tests
├── integration/      # Integration tests
└── unit tests       # Individual component tests
```

### Running Tests
```bash
# Run all tests with coverage
poetry run pytest tests/ -v --cov=src --cov-report=xml

# Run specific test file
poetry run pytest tests/test_database.py

# Run tests matching pattern
poetry run pytest -k "database"
```

### Coverage Requirements
- Overall project: 80%+ coverage
- Current coverage by component:
  - Orchestrator: 86%
  - Context Manager: 74%
  - Database Layer: 50%
  - Agent Modules: In development

## Git Workflow

1. **Branch Naming**:
   - Feature: `feature/description`
   - Bug fix: `fix/description`
   - Documentation: `docs/description`

2. **Commit Messages**:
   - Format: `type: description`
   - Types:
     - feat: New feature
     - fix: Bug fix
     - docs: Documentation changes
     - style: Code style changes
     - refactor: Code refactoring
     - test: Adding tests
     - chore: Maintenance tasks

3. **Pre-commit Checks**:
   ```bash
   # Format code
   poetry run format

   # Run linting
   poetry run lint

   # Run tests
   poetry run pytest tests/ -v --cov=src --cov-report=xml
   ```

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

1. **Code Quality**:
   - Black formatting check
   - isort import sorting
   - Flake8 linting
   - Line length validation

2. **Testing**:
   - Unit tests
   - Integration tests
   - Coverage reporting to Codecov

3. **Docker Builds**:
   - Builds container images
   - Pushes to GitHub Container Registry

### Configuration Files
- `.github/workflows/ci.yml`: CI/CD workflow
- `.flake8`: Flake8 configuration
- `pyproject.toml`: Black and isort configuration
- `scripts/lint.py`: Combined linting tools

## Documentation

1. **Code Documentation**:
   - Docstrings required for all public modules, functions, classes, and methods
   - Type hints used throughout the codebase
   - Example:
     ```python
     def function_name(param: type) -> return_type:
         """
         Brief description.

         Args:
             param: Parameter description

         Returns:
             Description of return value

         Raises:
             ExceptionType: Description of when this exception is raised
         """
     ```

2. **Project Documentation**:
   - README.md: Project overview and quick start
   - docs/: Detailed documentation
     - development.md: Development guide
     - api.md: API documentation
     - deployment.md: Deployment guide

## Best Practices

1. **Code Style**:
   - Follow PEP 8 guidelines
   - Use type hints
   - Write descriptive docstrings
   - Keep functions focused and small

2. **Testing**:
   - Write tests for new features
   - Maintain high coverage
   - Use meaningful test names
   - Test edge cases and error conditions

3. **Error Handling**:
   - Use appropriate exception types
   - Provide meaningful error messages
   - Log errors with context
   - Handle edge cases gracefully

4. **Logging**:
   - Use appropriate log levels
   - Include relevant context
   - Don't log sensitive information
   - Use structured logging

## Troubleshooting

1. **Common Issues**:
   - Poetry environment issues:
     ```bash
     poetry env remove python
     poetry install
     ```
   - Import errors:
     ```bash
     poetry run python -c "import sys; print(sys.path)"
     ```
   - Database connection issues:
     ```bash
     poetry run python -c "from context_manager.database import init_db; import asyncio; asyncio.run(init_db())"
     ```

2. **Debug Tools**:
   - pytest -vv for verbose output
   - pytest --pdb for debugger on failure
   - PYTHONPATH for import issues 

## Agent Development

### Shaun (Google Sheets Agent)

The Shaun agent is responsible for managing prospect data in Google Sheets. It provides functionality for:
- Connecting to Google Sheets using service account credentials
- Adding new prospects to sheets
- Updating existing prospect information
- Validating and formatting prospect data

#### Credentials Management

The agent supports multiple ways to provide Google Sheets credentials:
1. Explicit path via constructor: `GoogleSheetsClient(creds_path="path/to/credentials.json")`
2. Environment variable: Set `GOOGLE_SHEETS_CREDENTIALS` with the path
3. Default location: `~/.config/gspread/credentials.json`

The agent will check these locations in order and use the first valid credentials file found.

#### Testing the Shaun Agent

1. **Mock Credentials**:
   - A mock credentials file is provided at `tests/agents/shaun/test_creds.json`
   - Tests use a `DummyCredentials` class for simulating Google auth
   - The test suite validates all credential loading paths:
     - Explicit path
     - Environment variable
     - Default location

2. **Test Coverage**:
   - Initialization and cleanup: 100%
   - Credentials handling: 100%
   - Sheet operations: 83%
   - Error scenarios: Fully covered

3. **Test Structure**:
   ```
   tests/agents/shaun/
   ├── test_sheets_client.py  # Tests for Google Sheets client
   ├── test_utils.py         # Tests for utility functions
   └── test_creds.json      # Mock credentials for testing
   ```

4. **Running Shaun Tests**:
   ```bash
   poetry run pytest tests/agents/shaun/ -v
   ```

5. **Adding New Tests**:
   - Use the provided fixtures: `mock_credentials`, `mock_gspread`, etc.
   - Follow the existing pattern for mocking Google Sheets operations
   - Ensure proper cleanup in test functions 