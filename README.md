# Zigral 3.0

Zigral is an advanced automation platform that orchestrates multiple AI agents to perform complex, repetitive sales prospecting and outreach tasks. The system uses a combination of LLM-powered decision making and specialized agents to execute tasks efficiently and intelligently.

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

## Project Structure

```
zigral/
├── src/
│   ├── orchestrator/      # Core orchestration logic
│   ├── context_manager/   # Context management service
│   └── main.py           # Application entry point
├── tests/                # Test suite
└── [configuration files]
```

## Development

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

Run the test suite:
```bash
poetry run pytest
```

For coverage report:
```bash
poetry run pytest --cov=src --cov-report=term-missing
```

### Checkpoint Testing
The project includes comprehensive tests for the checkpoint system:

1. **Test Directory Management**:
   ```python
   @pytest.fixture
   def checkpoint_manager(tmp_path):
       """Create a checkpoint manager with temporary test directory"""
       checkpoint_dir = tmp_path / "test_checkpoints"
       manager = CheckpointManager(str(checkpoint_dir))
       yield manager
       # Cleanup happens automatically via pytest
   ```

2. **State Persistence Tests**:
   - Creating and loading checkpoints
   - Multiple checkpoints for the same job
   - Timestamp-specific checkpoint loading
   - Non-existent checkpoint handling

3. **Best Practices**:
   - Using `tmp_path` for isolated test directories
   - Ensuring unique timestamps for sequential checkpoints
   - Verifying checkpoint content and metadata
   - Testing both success and error cases

4. **Example Test Cases**:
   ```python
   def test_multiple_checkpoints_same_job(checkpoint_manager, test_state):
       """Test multiple checkpoints for the same job"""
       job_id = "test_job_123"
       
       # Create checkpoints with different states
       for i in range(3):
           modified_state = test_state.copy()
           modified_state["current_step"] = i
           checkpoint_manager.create_checkpoint(job_id, modified_state)
           time.sleep(1)  # Ensure unique timestamps
       
       # Verify checkpoints
       checkpoints = checkpoint_manager.list_checkpoints(job_id)
       assert len(checkpoints) == 3
   ```

## License

[License terms to be determined] 