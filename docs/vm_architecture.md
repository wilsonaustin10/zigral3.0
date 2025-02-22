# Zigral VM Architecture

## Overview

The Zigral VM serves as a dedicated environment for browser automation and VNC-based visual interaction. This document outlines the architectural decisions, component structure, and rationale behind our VM setup.

## Architecture Components

### 1. Core Services

#### 1.1 Display and Remote Access
- **Xvfb (X Virtual Framebuffer)**
  - Provides headless X11 server
  - Resolution: 1920x1080x24
  - Purpose: Creates virtual display for browser automation
  - Benefits: Enables GUI applications without physical display

- **x11vnc**
  - Shares Xvfb display
  - Port: 5900 (VNC)
  - Features: Password protection, shared sessions
  - Purpose: Enables remote viewing of virtual display

- **noVNC**
  - Port: 6080 (Web)
  - Provides browser-based VNC access
  - WebSocket proxy for VNC connection
  - Benefits: No VNC client required, works through firewalls

#### 1.2 Browser Automation
- **Chromium**
  - Version: 133.0.6943.126
  - Remote debugging port: 9222
  - Flags: --no-sandbox, --start-maximized
  - Purpose: Core browser for automation tasks

- **Playwright**
  - Version: 1.41.2
  - Connects to existing Chromium instance
  - Benefits: Robust automation API, better stability

### 2. Process Management

#### 2.1 Supervisor Configuration
```ini
[program:xvfb]
command=/usr/bin/Xvfb :0 -screen 0 %(ENV_RESOLUTION)s
priority=100

[program:x11vnc]
command=/usr/bin/x11vnc -display :0 -forever -shared
priority=200

[program:chromium]
command=/usr/bin/chromium --no-sandbox --remote-debugging-port=9222
priority=400

[program:lincoln]
command=python3 -m agents.lincoln.agent
priority=500

[program:shaun]
command=python3 -m agents.shaun.agent
priority=500
```

#### 2.2 Nginx Configuration
- Proxies noVNC web interface
- WebSocket support for VNC streaming
- Static file serving for noVNC client

### 3. Directory Structure

```
/app/
├── src/
│   ├── agents/           # Agent implementations
│   │   ├── base/         # Shared automation code
│   │   ├── vnc/          # VNC-specific components
│   │   ├── lincoln/      # LinkedIn automation
│   │   └── shaun/        # Google Sheets automation
│   ├── common/           # Shared utilities
│   └── context_manager/  # Context management
├── captures/             # Browser interaction artifacts
│   ├── screenshots/      # Visual captures
│   └── html/            # Page snapshots
└── shared/              # Shared resources
```

## Design Decisions

### 1. Single VM vs Container Approach
- **Decision**: Run services directly on VM rather than in containers
- **Rationale**:
  - Reduced complexity in process communication
  - Better performance for GUI operations
  - Simpler resource sharing between components
  - VM itself is containerized at host level

### 2. Process Management
- **Decision**: Use Supervisor for process control
- **Rationale**:
  - Reliable process monitoring
  - Automatic restart on failure
  - Clear dependency ordering
  - Centralized logging

### 3. Browser Integration
- **Decision**: Single persistent Chromium instance
- **Rationale**:
  - Resource efficiency
  - Faster agent operations
  - Shared browser state when needed
  - Consistent debugging interface

### 4. VNC Architecture
- **Decision**: Xvfb + x11vnc + noVNC stack
- **Rationale**:
  - Universal accessibility via web browsers
  - Secure WebSocket communication
  - Efficient screen updates
  - Support for multiple viewers

## Security Considerations

### 1. Browser Security
- Chromium runs with reduced privileges
- Remote debugging limited to localhost
- Separate user context for browser process

### 2. VNC Security
- Password protection available
- WebSocket encryption
- Access control through Nginx
- Session isolation

### 3. Process Isolation
- Service-specific user contexts
- Limited file system access
- Controlled inter-process communication

## Resource Management

### 1. Memory Allocation
- 4GB RAM total
- Managed through systemd limits
- Monitoring via Prometheus

### 2. Storage
- 10GB total disk space
- Automatic cleanup of old captures
- Log rotation enabled

## Monitoring and Logging

### 1. Log Locations
```
/var/log/
├── supervisor/          # Process control logs
├── nginx/              # Web proxy logs
└── agents/             # Agent-specific logs
```

### 2. Metrics Collection
- Process status
- Resource usage
- Browser performance
- VNC connection stats

## Integration Points

### 1. External Services
- Context Manager API
- RabbitMQ messaging
- Redis state cache
- Prometheus metrics

### 2. Agent Communication
- WebSocket updates
- Status reporting
- Command processing
- Error handling

## Future Considerations

### 1. Scalability
- Multiple VM instances
- Load balancing
- Session management
- Resource pooling

### 2. Monitoring
- Enhanced metrics
- Automated recovery
- Performance optimization
- Usage analytics

### 3. Security
- Enhanced access control
- Session encryption
- Audit logging
- Vulnerability scanning

## Conclusion

The VM architecture is designed to provide a robust, maintainable, and secure environment for browser automation and remote visualization. The chosen structure prioritizes reliability, performance, and ease of maintenance while enabling future scalability and enhancement. 