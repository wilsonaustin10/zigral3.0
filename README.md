# Zigral 3.0

An autonomous sales development application that acts as your virtual sales development representative.

## Project Structure

```
zigral/
├── src/
│   ├── orchestrator/       # Project Manager component
│   ├── context_manager/    # Context Manager microservice
│   └── agents/            # Agent modules
│       ├── lincoln/       # LinkedIn Agent
│       │   ├── agent.py
│       │   ├── browser.py
│       │   ├── search.py
│       │   └── data_collector.py
│       └── shaun/         # Google Sheets Agent
├── tests/
│   ├── agents/           # Agent-specific tests
│   │   ├── lincoln/      # LinkedIn Agent tests
│   │   └── shaun/        # Google Sheets Agent tests
│   ├── integration/      # Integration tests
│   └── unit tests       # Individual component tests
└── scripts/             # Development and utility scripts
    └── lint.py         # Linting and formatting tools
```

## Development Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run tests:
   ```bash
   poetry run pytest tests/ -v --cov=src --cov-report=xml
   ```

## Code Quality Tools

The project uses multiple tools to ensure code quality:

1. **Black** - Code formatting:
   ```bash
   poetry run black .  # Format code
   poetry run black . --check  # Check formatting
   ```

2. **isort** - Import sorting:
   ```bash
   poetry run isort .  # Sort imports
   poetry run isort . --check-only --diff  # Check import sorting
   ```

3. **Flake8** - Linting:
   ```bash
   poetry run flake8  # Run linter
   ```

4. **Combined Commands**:
   ```bash
   poetry run lint    # Run all checks (black, isort, flake8)
   poetry run format  # Format code (black, isort)
   ```

### Configuration Files

- `.flake8` - Flake8 configuration
- `pyproject.toml` - Black and isort configuration
- `scripts/lint.py` - Combined linting tools

### Code Style Guidelines

1. **Line Length**: Maximum 88 characters (Black default)
2. **Import Ordering**:
   - Standard library imports
   - Third-party imports
   - First-party imports (orchestrator, context_manager, agents)
   - Local imports
3. **Docstrings**: Required for all public modules, functions, classes, and methods
4. **Type Hints**: Used throughout the codebase

## Test Coverage

Current test coverage: 82%

Key components:
- Orchestrator: 86%
- Context Manager: 74%
- Database Layer: 50%
- Agent Modules: In development

## Running the Application

1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. Access the API at `http://localhost:8000`

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure code quality:
   ```bash
   poetry run lint  # Run all linting checks
   poetry run format  # Format code if needed
   ```
4. Run tests:
   ```bash
   poetry run pytest tests/ -v --cov=src --cov-report=xml
   ```
5. Submit a pull request

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
   - Coverage reporting

3. **Docker Builds**:
   - Builds container images
   - Pushes to GitHub Container Registry

## License

Proprietary - All rights reserved

## Features

- **Intelligent Orchestration**: Central orchestrator that coordinates multiple AI agents
- **Context Management**: Dedicated microservice for managing and persisting task context
- **Modular Architecture**: Extensible design allowing easy addition of new agents and capabilities
- **Smart Decision Making**: LLM-powered action planning and execution

## Architecture

### Context Protocol
The Context Manager is a dedicated microservice that maintains the state and history of all operations:

- **Purpose**: Stores and manages contextual information for tasks, enabling agents to:
  - Access historical data
  - Make informed decisions
  - Learn from past interactions
  - Maintain state across sessions

- **Data Model**:
  ```python
  {
    "job_id": str,          # Unique identifier for the task
    "job_type": str,        # Type of operation (e.g., "prospecting")
    "context_data": dict,   # Flexible JSON structure for context
    "created_at": datetime, # Creation timestamp
    "updated_at": datetime  # Last update timestamp
  }
  ```

- **API Endpoints**:
  - `POST /context`: Create new context entry
  - `GET /context/{job_id}`: Retrieve specific context
  - `PUT /context/{job_id}`: Update existing context
  - `DELETE /context/{job_id}`: Remove context
  - `GET /contexts`: List contexts with pagination

### Command Protocol
The Orchestrator provides a command interface for task execution and coordination:

- **Purpose**: Processes user commands and generates action sequences by:
  - Validating command structure
  - Interpreting command intent
  - Generating appropriate action steps
  - Coordinating with agents

- **Command Model**:
  ```python
  {
    "command": str,         # User command to execute
    "context": {           # Command context (flat structure)
      "job_id": str,       # Associated job identifier
      "target_industry": str,  # Domain-specific fields
      "target_location": str,
      ...                  # Additional context fields
    }
  }
  ```

- **Response Model**:
  ```python
  {
    "objective": str,      # High-level goal of the action sequence
    "steps": [            # List of action steps
      {
        "agent": str,     # Agent to execute the step
        "action": str,    # Specific action to take
        "parameters": dict # Action parameters
      }
    ]
  }
  ```

- **API Endpoints**:
  - `POST /command`: Process a command and generate action sequence
  - `GET /health`: Health check endpoint

### Orchestrator-Context Manager Interaction
The orchestrator interacts with the Context Manager to:

1. **Task Initialization**:
   - Creates new context entries for tasks
   - Stores initial parameters and requirements

2. **State Management**:
   - Updates context as tasks progress
   - Tracks completion status and results

3. **Decision Making**:
   - Retrieves historical context to inform LLM decisions
   - Uses past interactions to improve future operations

4. **Error Handling**:
   - Maintains checkpoint data for recovery
   - Stores error states for debugging

## Development

### Context Manager Validation

The Context Manager implements robust validation and error handling:

1. **Data Validation**:
   ```python
   class ContextEntryBase(BaseModel):
       job_id: str = Field(..., min_length=1)
       job_type: str = Field(..., min_length=1)
       context_data: Dict = Field(...)

       @field_validator('job_type')
       def validate_job_type(cls, v):
           if not v.strip():
               raise ValueError("job_type cannot be empty")
           return v.strip()
   ```

2. **Error Responses**:
   - `422 Validation Error`: Invalid or missing required fields
   - `400 Bad Request`: Job ID mismatch in update operations
   - `404 Not Found`: Resource doesn't exist
   - `500 Internal Error`: Unexpected server errors

3. **ID Consistency**:
   ```python
   @app.put("/context/{job_id}")
   async def update_context_entry(job_id: str, context: ContextEntryCreate):
       if job_id != context.job_id:
           raise HTTPException(
               status_code=400,
               detail=f"Job ID mismatch: URL has '{job_id}' but payload has '{context.job_id}'"
           )
   ```

4. **Best Practices**:
   - Strong type validation with Pydantic
   - Consistent error response format
   - Detailed error messages for debugging
   - Input sanitization (e.g., stripping whitespace)
   - Comprehensive logging of errors

### OpenAI API Integration and Testing

The project uses OpenAI's GPT models for intelligent decision making. Here's how we structure and test the integration:

#### Client Setup Pattern
```python
# Global client instance
_client = None

def get_openai_client() -> AsyncOpenAI:
    """Get or create the OpenAI client instance"""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

async def generate_action_sequence(
    command: str, 
    context: Optional[Dict] = None, 
    client: Optional[AsyncOpenAI] = None
) -> Union[ActionSequence, ErrorResponse]:
    """
    Main function that uses OpenAI API with dependency injection for testing
    """
    try:
        # Use provided client or get default
        openai_client = client or get_openai_client()
        
        # API call and response handling
        response = await openai_client.chat.completions.create(...)
        return ActionSequence(**json.loads(response.choices[0].message.content))
    except APIStatusError as e:
        if e.status_code == 429:
            return ErrorResponse(error=str(e))
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise
```

#### Rate Limiting
The system implements two levels of rate limiting:

1. **Application-Level Rate Limiting**:
   - Uses `slowapi` to limit requests per IP address
   - Default limit: 5 requests per minute
   - Returns 429 status code when exceeded
   - Automatically resets after the time window

2. **OpenAI API Rate Limiting**:
   - Handles OpenAI's quota and rate limit errors
   - Returns 200 status with error response when exceeded
   - Allows client-side handling of rate limit errors
   - Preserves API contract for error responses

#### Testing Pattern
1. **Mock Response Fixture**:
```python
@pytest.fixture
def mock_openai_response():
    """Mock response from OpenAI API"""
    content = {
        "objective": "Test objective",
        "steps": [{"agent": "Test", "action": "test"}]
    }
    return AsyncMock(
        choices=[
            AsyncMock(
                message=AsyncMock(
                    content=json.dumps(content)
                )
            )
        ]
    )
```

2. **Rate Limit Error Testing**:
```python
@pytest.fixture
def mock_rate_limited_client():
    """Mock OpenAI client that simulates a rate limit error"""
    mock_client = AsyncMock()
    error_response = {
        "error": {
            "message": "You exceeded your current quota",
            "type": "insufficient_quota",
            "code": "insufficient_quota"
        }
    }
    
    mock_response = httpx.Response(
        status_code=429,
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions"),
        content=json.dumps(error_response).encode()
    )
    
    mock_client.chat.completions.create.side_effect = APIStatusError(
        message="You exceeded your current quota",
        response=mock_response,
        body=error_response
    )
    return mock_client
```

3. **Test Cases**:
```python
def test_openai_rate_limit_handling(mock_rate_limited_client):
    """Test handling of OpenAI rate limit errors"""
    response = client.post("/command", json={"command": "Test command"})
    assert response.status_code == 200
    error_data = response.json()
    assert "error" in error_data
    assert "exceeded your current quota" in error_data["error"]

def test_api_rate_limit_reset():
    """Test rate limit window reset"""
    # First batch (5 successful requests)
    for _ in range(5):
        response = client.post("/command", json={"command": "Test"})
        assert response.status_code == 200
    
    # 6th request (rate limited)
    response = client.post("/command", json={"command": "Test"})
    assert response.status_code == 429
    
    # After window reset
    with patch('slowapi.extension.time.time', return_value=time.time() + 61):
        response = client.post("/command", json={"command": "Test"})
        assert response.status_code == 200
```

#### Key Testing Principles
1. **Dependency Injection**: Pass mock clients to functions for testing
2. **Response Structure**: Mock the exact OpenAI API response structure
3. **Error Handling**: Test both success and error scenarios
4. **No Real Calls**: Ensure tests never make actual API calls
5. **Rate Limits**: Test both API-level and application-level rate limiting
6. **Response Models**: Use proper response models for both success and error cases
7. **Window Reset**: Verify rate limit windows reset correctly

### Logging System

The project uses Loguru for structured logging across all components. Here's how the logging system works:

#### Logger Configuration
```python
def get_logger(name: str):
    """Configure and return a module-specific logger instance"""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create a new logger instance with module context
    new_logger = logger.opt(depth=1)
    new_logger.remove()  # Remove default handler
    
    # Get log level from environment (defaults to INFO)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Configure handlers with consistent format
    format_string = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[module]} | {message}"
    
    # Console output
    new_logger.add(sys.stderr, format=format_string, level=log_level)
    
    # Error log file (ERROR and above)
    new_logger.add(
        "logs/error.log",
        format=format_string,
        level="ERROR",
        rotation="1 day",
        retention="7 days"
    )
    
    # All logs file
    new_logger.add(
        "logs/zigral.log",
        format=format_string,
        level=log_level,
        rotation="1 day",
        retention="7 days"
    )
    
    return new_logger.bind(module=name)
```

#### Usage
```python
# In your module
logger = get_logger(__name__)

# Log messages with different levels
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Warning messages for potentially problematic situations")
logger.error("Error messages for serious problems")
logger.critical("Critical messages for fatal errors")
```

#### Features
1. **Module Context**: Each logger is bound with its module name for easy tracking
2. **Log Rotation**: Daily rotation with 7-day retention for log files
3. **Environment Configuration**: Log level configurable via `LOG_LEVEL` environment variable
4. **Structured Output**: Consistent format across console and file outputs
5. **Error Tracking**: Separate error log file for easy monitoring
6. **Automatic Directory Creation**: Creates logs directory if it doesn't exist

#### Testing
The logging system includes comprehensive tests that verify:
- Logger creation and configuration
- Log file creation and content
- Module name binding
- Log level configuration
- File cleanup and rotation

### Dependency Management
This project uses Poetry for dependency management:

1. **Installation**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Key Files**:
   - `pyproject.toml`: Primary configuration and dependency specification
   - `poetry.lock`: Locked dependency versions for reproducible builds

3. **Common Commands**:
   ```bash
   poetry install            # Install dependencies
   poetry add package-name   # Add new dependency
   poetry shell             # Activate virtual environment
   poetry run python script.py  # Run script in virtual environment
   ```

4. **For Deployment**:
   ```bash
   poetry export -f requirements.txt --output requirements.txt
   ```

### Rate Limiting
The orchestrator implements rate limiting to prevent abuse:

- 5 requests per minute per IP address
- Returns 429 (Too Many Requests) when limit exceeded
- Configurable through the `slowapi` package

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment:

1. **Automated Tests**:
   - Runs on every push and pull request
   - Executes unit and integration tests
   - Generates coverage reports

2. **Code Quality**:
   - Linting with flake8
   - Formatting with black
   - Import sorting with isort

3. **Docker Builds**:
   - Builds container images for both services
   - Pushes to GitHub Container Registry
   - Tags with commit SHA and 'latest'

4. **Deployment**:
   - Automated deployment to staging
   - Manual approval for production
   - Health check verification

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

## Testing

### Test Configuration

The project uses pytest for testing with comprehensive coverage reporting. Key testing components include:

1. **Test Structure**:
   - Database tests (`tests/test_database.py`): Verify database connections and operations
   - Context Manager tests (`tests/test_context_manager.py`): Test context CRUD operations
   - Orchestrator tests (`tests/test_orchestrator.py`): Validate orchestration logic
   - LLM Integration tests (`tests/test_llm_integration.py`): Test AI model interactions
   - Logger tests (`tests/test_logger.py`): Verify logging functionality
   - Checkpoint tests (`tests/test_checkpoint.py`): Test state persistence

2. **Coverage Configuration**:
   ```ini
   [run]
   source = src

   [report]
   exclude_lines =
       pragma: no cover
       def __repr__
       if self.debug:
       raise NotImplementedError
       if __name__ == .__main__.:
       pass
       raise ImportError
       except ImportError:
       def main

   omit =
       src/main.py
       tests/*
       */__init__.py
   ```

3. **Coverage Standards**:
   - Entry points (e.g., `main.py`) are excluded from coverage
   - Focus on testing business logic and application behavior
   - Current coverage: >80% across core modules

4. **Test Database**:
   - Uses a dedicated test database (`zigral_test`)
   - Separate configuration from production database
   - Automatic schema creation and cleanup

5. **Running Tests**:
   ```bash
   # Run all tests with coverage report
   pytest -v --cov=src --cov-report=term-missing

   # Run specific test file
   pytest tests/test_database.py -v

   # Run tests matching a pattern
   pytest -v -k "database"
   ```

## License

[License terms to be determined] 