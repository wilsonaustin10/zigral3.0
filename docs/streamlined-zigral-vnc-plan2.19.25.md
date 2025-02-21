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
- [ ] Browser command executor
- [ ] WebSocket client for real-time updates
- [x] Health monitoring (basic implementation)
- [ ] Session management

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
- [ ] Retry mechanisms

### 3. Core System Updates
#### Purpose
- Integration with VNC agent
- Command delegation
- State synchronization
- Error handling

#### Components
- [ ] Browser command dispatcher
- [ ] State synchronization
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
- [ ] Implement browser command execution
- [ ] Add WebSocket support for real-time updates
- [ ] Create state management system
- [ ] Add error handling and recovery
- [ ] Update main orchestrator for integration

### Phase 3: Security & Monitoring (Week 2)
- [ ] Implement secure communication
- [ ] Add comprehensive logging
- [ ] Set up monitoring
- [ ] Add rate limiting
- [ ] Create backup procedures

### Phase 4: Testing & Optimization (Week 2-3)
- [ ] Create test suite
- [ ] Performance testing
- [ ] Load testing
- [ ] Security testing
- [ ] Documentation updates

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

tests/
├── unit/
│   └── agents/
│       └── vnc/             # VNC agent tests
└── integration/
    └── agents/
        └── vnc/             # VNC integration tests
```

## Security Considerations
1. **Authentication**
   - [x] JWT-based authentication
   - [x] API keys for service-to-service communication
   - [ ] Rate limiting per client

2. **Network Security**
   - [ ] HTTPS for all communications
   - [ ] WebSocket secure (WSS)
   - [ ] Network isolation where possible

3. **Access Control**
   - [x] Role-based access control
   - [ ] IP whitelisting
   - [ ] Session management

## Monitoring & Logging
1. **Metrics**
   - [x] Service health
   - [ ] Browser session status
   - [ ] Command execution times
   - [ ] Error rates

2. **Logging**
   - [x] Structured logging
   - [ ] Log aggregation
   - [x] Error tracking
   - [ ] Audit trail

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
   - [ ] Deploy to VNC server
   - [ ] Configure systemd service
   - [ ] Set up monitoring

2. **Main System Updates**
   - [ ] Update orchestrator
   - [ ] Deploy new endpoints
   - [ ] Update documentation

## Future Considerations
1. **Scaling**
   - [ ] Multiple VNC servers
   - [ ] Load balancing
   - [ ] Session distribution

2. **Features**
   - [ ] Browser profile management
   - [ ] Automated testing integration
   - [ ] Video recording
   - [ ] Performance optimization

## Success Metrics
1. **Performance**
   - [ ] Command execution time < 100ms
   - [ ] WebSocket latency < 50ms
   - [ ] Error rate < 1%

2. **Reliability**
   - [ ] 99.9% uptime
   - [ ] Automatic recovery
   - [ ] No data loss

3. **Security**
   - [x] No unauthorized access
   - [ ] All communications encrypted
   - [ ] Regular security audits

## Next Steps
1. [x] Review and approve architecture
2. [x] Set up development environment
3. [ ] Begin Phase 1 implementation
4. [ ] Create test infrastructure
5. [ ] Set up CI/CD pipeline

## Related Documentation
- [VNC Setup](./vnc_setup.md)
- [Frontend Backend Integration](./frontend_backend_integration.md)
- [noVNC Implementation](./novnc_implementation.md)
- [Phase 3 Overview](./phase3.md) 