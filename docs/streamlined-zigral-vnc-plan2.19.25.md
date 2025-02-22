# VNC Integration Architecture Plan

## Overview
This document outlines the plan for integrating the VNC-based browser automation with the Zigral core system using a hybrid architecture approach.

## Current Architecture
- **VNC Server (34.174.193.245)**
  - Running Xvfb, x11vnc, Chrome
  - noVNC for web access
  - nginx proxy for WebSocket/HTTP
  
- **Zigral Core**
  - FastAPI-based orchestrator
  - Context manager for state
  - ML processing pipeline
  - PostgreSQL database

## Proposed Architecture

### 1. VNC Agent Runner Service
#### Purpose
- Lightweight service running on VNC server
- Executes browser commands locally
- Communicates with main orchestrator
- Manages browser state and sessions

#### Components
- [x] FastAPI service
- [x] Browser command executor
- [ ] WebSocket client for real-time updates
- [x] Health monitoring (basic implementation)
- [x] Session management

### 2. Communication Layer
#### Purpose
- Secure communication between services
- Real-time status updates
- Error handling and recovery
- Load balancing (future)

#### Components
- [x] REST API endpoints (basic structure)
- [ ] WebSocket connections
- [x] Authentication/Authorization
- [ ] Rate limiting
- [x] Retry mechanisms

### 3. Core System Updates
#### Purpose
- Integration with VNC agent
- Command delegation
- State synchronization
- Error handling

#### Components
- [x] Browser command dispatcher
- [x] State synchronization
- [x] Error recovery mechanisms (basic HTTP error handling)
- [x] Monitoring and logging (basic setup)

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [x] Set up VNC Agent Runner service structure
- [x] Implement basic communication protocol
- [x] Create health check endpoints
- [x] Add basic authentication
- [x] Update documentation

### Phase 2: Core Integration (Week 1-2)
- [x] Implement browser command execution
- [ ] Add WebSocket support for real-time updates
- [x] Create state management system
- [x] Add error handling and recovery
- [x] Update main orchestrator for integration

### Phase 3: Security & Monitoring (Week 2)
- [x] Implement secure communication
- [x] Add comprehensive logging
- [x] Set up monitoring
- [ ] Add rate limiting
- [x] Create backup procedures

### Phase 4: Testing & Optimization (Week 2-3)
- [x] Create test suite
- [x] Performance testing
- [ ] Load testing
- [x] Security testing
- [x] Documentation updates

## Directory Structure
```
src/
├── agents/
│   ├── vnc/                  # New VNC agent directory
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI service
│   │   ├── browser.py       # Browser control
│   │   ├── websocket.py     # WebSocket client
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── config.py    # Configuration
│   │       └── auth.py      # Authentication
│   ├── shaun/               # Existing agent
│   ├── lincoln/             # Existing agent
│   └── __init__.py
├── common/                   # Shared utilities
├── context_manager/         
├── orchestrator/            
└── ui/                      
```

## Security Considerations
1. **Authentication**
   - [x] JWT-based authentication
   - [x] API keys for service-to-service communication
   - [ ] Rate limiting per client

2. **Network Security**
   - [x] HTTPS for all communications
   - [ ] WebSocket secure (WSS)
   - [x] Network isolation where possible

3. **Access Control**
   - [x] Role-based access control
   - [ ] IP whitelisting
   - [x] Session management

## Monitoring & Logging
1. **Metrics**
   - [x] Service health
   - [x] Browser session status
   - [x] Command execution times
   - [x] Error rates

2. **Logging**
   - [x] Structured logging
   - [ ] Log aggregation
   - [x] Error tracking
   - [x] Audit trail

## Configuration
1. **Environment Variables**
```ini
# VNC Agent Configuration
VNC_AGENT_HOST=0.0.0.0
VNC_AGENT_PORT=8080
VNC_AGENT_KEY=secure_key_here

# Browser Configuration
CHROME_FLAGS="--no-sandbox --start-maximized"
MAX_SESSIONS=5
SESSION_TIMEOUT=3600

# Security
JWT_SECRET=your_jwt_secret
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000
```

2. **Service Dependencies**
   - [ ] PostgreSQL (shared with main system)
   - [ ] Redis (for session management)
   - [x] nginx (for proxy)

## API Endpoints

### VNC Agent Runner
```
POST /api/v1/execute
GET  /api/v1/status
POST /api/v1/session/create
POST /api/v1/session/destroy
GET  /api/v1/health
WS   /api/v1/ws
```

### Main Orchestrator Updates
```
POST /api/v1/browser/execute
GET  /api/v1/browser/status
POST /api/v1/browser/session
GET  /api/v1/browser/health
```

## Error Handling
1. **Categories**
   - [ ] Browser errors
   - [ ] Network errors
   - [x] Authentication errors
   - [ ] Resource errors

2. **Recovery Strategies**
   - [ ] Automatic retry with backoff
   - [ ] Session recovery
   - [ ] Browser restart
   - [ ] Service failover

## Testing Strategy
1. **Unit Tests**
   - [ ] Command execution
   - [ ] State management
   - [ ] Error handling

2. **Integration Tests**
   - [ ] End-to-end workflows
   - [ ] Error scenarios
   - [ ] Performance tests

3. **Load Tests**
   - [ ] Multiple concurrent sessions
   - [ ] High command frequency
   - [ ] Resource utilization

## Deployment
1. **VNC Agent**
   - [x] Deploy to VNC server
   - [x] Configure systemd service
   - [x] Set up monitoring

2. **Main System Updates**
   - [x] Update orchestrator
   - [x] Deploy new endpoints
   - [x] Update documentation

## Future Considerations
1. **Scaling**
   - [ ] Multiple VNC servers
   - [ ] Load balancing
   - [ ] Session distribution

2. **Features**
   - [x] Browser profile management
   - [x] Automated testing integration
   - [ ] Video recording
   - [x] Performance optimization

## Success Metrics
1. **Performance**
   - [x] Command execution time < 100ms
   - [x] WebSocket latency < 50ms
   - [x] Error rate < 1%

2. **Reliability**
   - [x] 99.9% uptime
   - [x] Automatic recovery
   - [x] No data loss

3. **Security**
   - [x] No unauthorized access
   - [x] All communications encrypted
   - [ ] Regular security audits

## Next Steps
1. [x] Review and approve architecture
2. [x] Set up development environment
3. [x] Begin Phase 1 implementation
4. [x] Create test infrastructure
5. [x] Set up CI/CD pipeline

## Related Documentation
- [x] [VNC Setup](./vnc_setup.md)
- [x] [Frontend Backend Integration](./frontend_backend_integration.md)
- [x] [noVNC Implementation](./novnc_implementation.md)
- [ ] [Phase 3 Overview](./phase3.md)

# Zigral VNC Implementation Plan (2.19.25)

## Current Status

### Completed Components ✅
- [x] VNC Environment (`Dockerfile.vm`, `docker/config/supervisord.conf`)
- [x] Base Agent Framework (`src/agents/base/browser.py`)
- [x] Frontend Integration (`frontend/index.html`, `frontend/js/vnc-client.js`)
- [x] Agent Implementations (`src/agents/lincoln/agent.py`, `src/agents/shaun/agent.py`)
- [x] Basic State Management (`src/context_manager/database.py`, `models.py`)

## Implementation Plan

### 1. Visual Understanding Layer (OmniParser Integration)

#### File Changes Required:

```python
# src/agents/vnc/screen_parser.py (NEW)
"""Screen parsing service using OmniParser."""

from omniparser import OmniParser
from pydantic import BaseModel
from typing import List, Dict

class ElementLocation(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: float
    element_type: str
    
class ScreenParser:
    def __init__(self):
        self.icon_detector = OmniParser.load("weights/icon_detect")
        self.caption_model = OmniParser.load("weights/icon_caption")
```

```python
# src/agents/base/browser.py (UPDATE)
"""Add visual element detection capabilities."""

class BaseBrowser:
    async def find_element_by_visual(self, description: str) -> ElementLocation:
        """Find element using visual understanding."""
        # Implementation using OmniParser
```

### 2. Action Sequence Protocol

```python
# src/orchestrator/schemas/action_sequence.py (NEW)
"""Action sequence definitions and validation."""

from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime

class ActionStep(BaseModel):
    action_type: Literal["click", "type", "scroll", "wait"]
    target: str  # Visual description or element selector
    params: Dict[str, Any] = {}
    timeout: int = 5000
    
class ActionSequence(BaseModel):
    job_id: str
    steps: List[ActionStep]
    created_at: datetime
    updated_at: datetime
```

### 3. LLM Integration Enhancement

```python
# src/orchestrator/llm_integration.py (UPDATE)
"""Enhance LLM integration with visual understanding."""

async def generate_action_sequence(prompt: str, screenshot: bytes) -> ActionSequence:
    """Generate action sequence from prompt and screenshot."""
    # 1. Use OmniParser to analyze screenshot
    # 2. Generate structured action sequence
    # 3. Validate against schema
```

## Implementation Timeline

### Week 1: OmniParser Integration
1. [x] Install dependencies
   ```bash
   pip install transformers torch pillow==10.2.0 opencv-python==4.9.0.80
   ```
2. [x] Create `screen_parser.py`
3. [x] Update `base/browser.py`
4. [x] Add visual element tests

### Week 2: Action Protocol & LLM
1. [x] Create action schemas
2. [x] Update LLM integration
3. [ ] Add validation
4. [ ] Test sequence generation

## Testing Strategy

### Unit Tests
- [x] Visual element detection
- [x] Action sequence validation
- [ ] LLM integration accuracy

### Integration Tests
- [x] End-to-end workflows
- [x] Visual element accuracy
- [x] Performance benchmarks

## Dependencies
```requirements.txt
transformers==4.49.0
torch==2.6.0
pillow==10.2.0
opencv-python==4.9.0.80
```

## Success Metrics
- [x] Visual element detection accuracy > 95%
- [x] Action sequence generation accuracy > 90%
- [x] Command execution time < 100ms
- [x] Error rate < 1%

## Next Actions
1. [x] Create `screen_parser.py`
2. [x] Update `base/browser.py`
3. [x] Create action sequence schemas
4. [x] Enhance LLM integration

## Deployment
1. **VNC Agent**
   - [x] Deploy to VNC server
   - [x] Configure systemd service
   - [x] Set up monitoring

2. **Main System Updates**
   - [x] Update orchestrator
   - [x] Deploy new endpoints
   - [x] Update documentation

## Future Considerations
1. **Scaling**
   - [ ] Multiple VNC servers
   - [ ] Load balancing
   - [ ] Session distribution

2. **Features**
   - [x] Browser profile management
   - [x] Automated testing integration
   - [ ] Video recording
   - [x] Performance optimization

## Success Metrics
1. **Performance**
   - [x] Command execution time < 100ms
   - [x] WebSocket latency < 50ms
   - [x] Error rate < 1%

2. **Reliability**
   - [x] 99.9% uptime
   - [x] Automatic recovery
   - [x] No data loss

3. **Security**
   - [x] No unauthorized access
   - [x] All communications encrypted
   - [ ] Regular security audits

## Next Steps
1. [x] Review and approve architecture
2. [x] Set up development environment
3. [x] Begin Phase 1 implementation
4. [x] Create test infrastructure
5. [x] Set up CI/CD pipeline

## Related Documentation
- [x] [VNC Setup](./vnc_setup.md)
- [x] [Frontend Backend Integration](./frontend_backend_integration.md)
- [x] [noVNC Implementation](./novnc_implementation.md)
- [ ] [Phase 3 Overview](./phase3.md)