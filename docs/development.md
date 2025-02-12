# Development Guide

## Environment Setup

1. **Python Environment**
   - Python 3.12 or higher is required
   - Use Poetry for dependency management
   ```bash
   poetry install --with test
   ```

2. **Credentials Setup**

   ### Google Sheets Credentials
   The application supports two methods for providing Google Sheets credentials:

   a. Base64 Encoded JSON (Recommended for production)
   ```bash
   # In .env file
   GOOGLE_SHEETS_CREDENTIALS_JSON=data:application/json;base64,<your_base64_encoded_credentials>
   ```

   b. File-based Credentials
   ```bash
   # In .env file
   GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json
   ```

   Note: Base64 encoded credentials take precedence over file-based credentials.

3. **Environment Variables**
   Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Testing

1. **Running Tests**
   ```bash
   # Run all tests
   poetry run pytest

   # Run specific test files
   poetry run pytest tests/agents/shaun/test_sheets.py
   poetry run pytest tests/agents/shaun/test_main.py

   # Run with coverage report
   poetry run pytest --cov=src --cov-report=term-missing
   ```

2. **Test Environment**
   - Tests use mock credentials by default
   - Integration tests require valid credentials
   - Set `TESTING=true` for test-specific behavior

3. **Mock Setup**
   - Use `mock_env_credentials` fixture for Google Sheets tests
   - Use `mock_rabbitmq_connection` fixture for RabbitMQ tests
   - Use `mock_sheets_client` fixture for Google Sheets client tests

## Code Style

1. **Formatting**
   ```bash
   # Format code
   poetry run black .

   # Sort imports
   poetry run isort .
   ```

2. **Linting**
   ```bash
   # Run flake8
   poetry run flake8
   ```

## Best Practices

1. **Credential Handling**
   - Never commit real credentials to version control
   - Use environment variables for sensitive data
   - Support both base64 and file-based credentials for flexibility

2. **Error Handling**
   - Always clean up resources in error cases
   - Use proper exception handling with specific error types
   - Log errors with appropriate context

3. **Testing**
   - Write both unit and integration tests
   - Use fixtures for common setup
   - Mock external services appropriately
   - Test both success and failure cases

4. **Async Code**
   - Use proper async/await syntax
   - Handle cleanup in both success and error cases
   - Use asynccontextmanager for resource management

5. **Logging**
   - Use structured logging
   - Include relevant context in log messages
   - Use appropriate log levels

## Common Issues

1. **Credentials Issues**
   - Ensure credentials are properly formatted
   - Check environment variables are set correctly
   - Verify credentials have required permissions

2. **Test Failures**
   - Check mock setup is correct
   - Ensure cleanup is properly handled
   - Verify async code is properly structured

## Contributing

1. **Pull Requests**
   - Write clear PR descriptions
   - Include test coverage
   - Follow code style guidelines
   - Update documentation as needed

2. **Code Review**
   - Review for security issues
   - Check error handling
   - Verify test coverage
   - Ensure documentation is updated

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
- Overall project: 80%+ coverage target
- Current coverage by component:
  - Lincoln Agent:
    - Core functionality: 91%
    - RabbitMQ integration: 83%
    - API endpoints: 75%
  - Shaun Agent:
    - Core functionality: 85%
    - Google Sheets integration: 80%
    - Credential handling: 100%
    - Error cases: 100%
    - Utility functions: 75%
  - Common Messaging: 59%
  - Context Manager: 72-100%
  - Orchestrator: 82-96%

### Test Improvements
The test suite for the Google Sheets client (`test_sheets_client.py`) has been enhanced to include:

1. **Credential Handling Tests**:
   - File-based credentials (explicit path, env var, default location)
   - Base64 encoded credentials
   - Direct JSON credentials
   - Invalid credential scenarios

2. **Error Case Coverage**:
   - Missing credentials file
   - Invalid credentials format
   - Empty credentials file
   - Invalid JSON/base64 content

3. **Mock Improvements**:
   - Enhanced credential mocking with proper error simulation
   - Realistic file system interaction simulation
   - Google API service mocking

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

## Agent Development

### Lincoln (LinkedIn Agent)

The Lincoln agent is responsible for automating LinkedIn interactions. It provides functionality for:
- Automated login to LinkedIn using environment variables or secure credentials
- Sales Navigator search operations
- Profile data collection and extraction
- GUI state capture for debugging and validation

#### Credentials Management

The agent supports LinkedIn credentials through:
1. Environment variables: `LINKEDIN_USERNAME` and `LINKEDIN_PASSWORD`
2. Interactive input during runtime (if environment variables are not set)
3. Command-based login through the API

#### Testing the Lincoln Agent

1. **Mock Browser Setup**:
   - Tests use Playwright's test context for browser simulation
   - Mock page and element interactions
   - Capture GUI states without real browser

2. **Test Coverage**:
   - Core functionality: 83%
   - RabbitMQ integration: 66%
   - API endpoints: 75%

3. **Test Structure**:
   ```
   tests/agents/lincoln/
   ├── test_linkedin_client.py  # Tests for LinkedIn automation
   ├── test_main.py            # Tests for FastAPI endpoints
   ├── test_rabbitmq.py        # Tests for message handling
   └── test_utils.py           # Tests for utility functions
   ```

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
   - A mock credentials file is provided for testing
   - Tests use a `DummyCredentials` class for simulating Google auth
   - The test suite validates all credential loading paths:
     - Explicit path
     - Environment variable
     - Default location

2. **Test Coverage**:
   - Core functionality: 85%
   - Google Sheets integration: 83%
   - Utility functions: 100%

3. **Test Structure**:
   ```
   tests/agents/shaun/
   ├── test_sheets_client.py  # Tests for Google Sheets client
   ├── test_main.py          # Tests for FastAPI endpoints
   ├── test_rabbitmq.py      # Tests for message handling
   └── test_utils.py         # Tests for utility functions
   ```

### Agent Communication

Both agents use RabbitMQ for asynchronous communication:

1. **Message Queues**:
   - `lincoln_commands`: Commands for LinkedIn operations
   - `lincoln_responses`: Results from LinkedIn operations
   - `shaun_commands`: Commands for Google Sheets operations
   - `shaun_responses`: Results from Google Sheets operations

2. **Command Format**:
   ```json
   {
       "command": "action_name",
       "data": {
           // Command-specific parameters
       }
   }
   ```

3. **Response Format**:
   ```json
   {
       "status": "success" | "error",
       "data": {
           // Response data
       },
       "error": "Error message if status is error"
   }
   ```

### Running Tests

```bash
# Run all agent tests
poetry run pytest tests/agents/ -v

# Run specific agent tests
poetry run pytest tests/agents/lincoln/ -v
poetry run pytest tests/agents/shaun/ -v

# Run with coverage
poetry run pytest tests/agents/ -v --cov=src/agents --cov-report=xml
```

### Best Practices

1. **Error Handling**:
   - All external operations (LinkedIn, Google Sheets) should have proper try/except blocks
   - Network errors should be caught and logged
   - Invalid data should be validated before processing

2. **Logging**:
   - Use the agent-specific logger
   - Log all important operations and errors
   - Include relevant context in log messages

3. **Testing**:
   - Mock external services in tests
   - Test both success and failure scenarios
   - Maintain high test coverage
   - Use appropriate fixtures for common setup

4. **Security**:
   - Never hardcode credentials
   - Use environment variables or secure vaults
   - Validate all input data
   - Handle sensitive data securely 

## Credential Management

### Google Sheets Credentials

For security reasons, Google Sheets credentials can be provided in two ways:

1. **Base64 Encoded JSON (Recommended for Production)**
   ```bash
   # Convert your credentials.json to base64
   base64 -i path/to/credentials.json | tr -d '\n'
   
   # Add the base64 string to your .env file
   GOOGLE_SHEETS_CREDENTIALS_JSON=base64_encoded_string_here
   ```

2. **File Path (Development/Testing)**
   ```bash
   # Add the path to your .env file
   GOOGLE_SHEETS_CREDENTIALS_PATH=/path/to/credentials.json
   ```

3. **Default Location**
   If neither of the above is provided, the system will look for credentials at:
   `~/.config/gspread/credentials.json`

### Converting Existing Credentials

To convert your existing credentials file to the new format:

1. **Generate Base64 String**
   ```bash
   base64 -i config/credentials/credentials.json | tr -d '\n'
   ```

2. **Update Environment**
   - Add the base64 string to your `.env` file
   - Remove the original credentials.json file
   - Update your .gitignore to exclude any credential files

### Security Best Practices

1. **Never commit credentials to version control**
2. **Use environment variables in production**
3. **Rotate credentials regularly**
4. **Use minimal scope permissions**
5. **Monitor credential usage** 

## Recent Updates

### Interactive 2FA Handling Improvements

- **LinkedIn Agent Updates:**
  - The LinkedIn client now supports interactive two-factor authentication.
  - Dummy page injection has been implemented to simulate both scenarios: tests where 2FA is not required and tests where a 2FA PIN is expected.
  - A new pytest fixture (`linkedin_client_with_success`) has been introduced to simulate a successful login along with interactive 2FA handling.
  - Inline comments in `src/agents/lincoln/linkedin_client.py` have been updated to document the new interactive 2FA flow, including extraction and verification steps.

### Testing Enhancements

- All tests in `tests/agents/lincoln/test_linkedin_client.py` now pass with the updated interactive 2FA handling.
- Minor runtime warnings related to asynchronous mocks are present but do not affect test outcomes.

## General Practices

- Run tests using `poetry run pytest --tb=short` before committing changes.
- Follow detailed commit and branch strategies as outlined in the project CHANGELOG and requirements. 