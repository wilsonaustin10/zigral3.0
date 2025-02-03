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
) -> Dict:
    """
    Main function that uses OpenAI API with dependency injection for testing
    """
    try:
        # Use provided client or get default
        openai_client = client or get_openai_client()
        
        # API call and response handling
        response = await openai_client.chat.completions.create(...)
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise
```

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
async def test_rate_limit_handling(mock_rate_limited_client):
    """Test handling of OpenAI rate limit errors"""
    with pytest.raises(APIStatusError) as exc_info:
        await generate_action_sequence(command, client=mock_rate_limited_client)
    assert exc_info.value.status_code == 429

async def test_no_real_api_calls(mock_openai_client):
    """Test that no real API calls are made when using a mock"""
    result = await generate_action_sequence(command, client=mock_openai_client)
    mock_openai_client.chat.completions.create.assert_called_once()
```

#### Key Testing Principles
1. **Dependency Injection**: Pass mock clients to functions for testing
2. **Response Structure**: Mock the exact OpenAI API response structure
3. **Error Handling**: Test both success and error scenarios
4. **No Real Calls**: Ensure tests never make actual API calls
5. **Rate Limits**: Test both API-level and application-level rate limiting

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

## License

[License terms to be determined] 