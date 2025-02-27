# Zigral 3.0 System Architecture

This document describes the high-level architecture of the Zigral 3.0 platform, including the relationships between services, data flow, and component responsibilities.

## System Overview

Zigral is a platform that integrates AI agents with a virtual desktop environment (VDI) through noVNC technology, allowing AI to interact with web applications through a Chrome browser in a controlled environment.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Zigral 3.0 Platform                             │
│                                                                     │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────────────┐  │
│  │             │      │             │      │                     │  │
│  │  Frontend   │◄────►│ Orchestrator│◄────►│  Context Manager    │  │
│  │  (UI)       │      │  Service    │      │                     │  │
│  │             │      │             │      │                     │  │
│  └─────────────┘      └──────┬──────┘      └─────────┬───────────┘  │
│         ▲                    │                       │              │
│         │                    ▼                       │              │
│         │             ┌─────────────┐                │              │
│         │             │             │                │              │
│         └─────────────┤  VNC Agent  │◄───────────────┘              │
│                       │  Service    │                               │
│                       │             │                               │
│                       └──────┬──────┘                               │
│                              │                                      │
│                              ▼                                      │
│                       ┌─────────────┐                               │
│                       │ noVNC Server │                              │
│                       │ (Browser VM) │                              │
│                       │             │                               │
│                       └─────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Service Components

### 1. Frontend (UI)

The user interface for interacting with the Zigral platform.

**Responsibilities:**
- Provide interface for user interaction
- Display noVNC viewer
- Handle chat interface for communicating with AI agents
- Manage authentication and session handling

**Technologies:**
- Vite + JavaScript/HTML/CSS
- Running on port 5173 (development) or 80 (production)

### 2. Orchestrator Service

Coordinates the overall system operation and serves as the central communication hub.

**Responsibilities:**
- Route requests between components
- Manage workflow execution
- Handle API endpoints for external integration
- Coordinate AI agent activities

**Technologies:**
- FastAPI Python service
- Running on port 8000

### 3. Context Manager

Maintains session context and manages conversation history.

**Responsibilities:**
- Store and retrieve conversation history
- Manage context windows for LLM interactions
- Track session state
- Handle memory management for long-running sessions

**Technologies:**
- FastAPI Python service
- Redis for state management
- Running on port 8001

### 4. VNC Agent Service

Controls the VNC environment and executes browser actions.

**Responsibilities:**
- Translate AI commands into browser actions
- Execute browser automation tasks
- Manage VNC session state
- Provide browser state feedback

**Technologies:**
- FastAPI Python service
- Running on port 8080

### 5. noVNC Server (Browser VM)

Virtual environment running Chrome browser with noVNC access.

**Responsibilities:**
- Provide isolated browser environment
- Run web applications securely
- Support VNC protocol for remote viewing/control
- Host the Chrome browser instance

**Technologies:**
- Linux with X11 server
- noVNC/websockify for browser access
- x11vnc server
- Google Chrome browser
- Running VNC server on port 5900
- WebSocket proxy on port 6081

## Data Flow

```
┌─────────┐          ┌─────────────┐          ┌────────────────┐
│         │  HTTP    │             │  HTTP    │                │
│   UI    │◄────────►│Orchestrator │◄────────►│Context Manager │
│         │          │             │          │                │
└────┬────┘          └──────┬──────┘          └────────────────┘
     │                      │                           ▲
     │                      │                           │
     │                      ▼                           │
     │               ┌─────────────┐              ┌─────┴─────┐
     │  WebSocket   │  VNC Agent   │  API Calls   │           │
     └──────────────►   Service    │◄─────────────┤   Redis   │
                    │             │              │           │
                    └──────┬──────┘              └───────────┘
                           │
                           │ VNC Protocol
                           ▼
                    ┌─────────────┐
                    │   noVNC     │
                    │  (Browser)  │
                    │             │
                    └─────────────┘
```

## Deployment Topology

### Docker Container Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Docker Host                                    │
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────┐  │
│  │   Frontend  │   │Orchestrator │   │   Context   │   │         │  │
│  │  Container  │   │  Container  │   │  Container  │   │  Redis  │  │
│  │             │   │             │   │             │   │         │  │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────┘  │
│                                                                     │
│                          ┌─────────────┐                            │
│                          │  VNC Agent  │                            │
│                          │  Container  │                            │
│                          │             │                            │
│                          └─────────────┘                            │
│                                                                     │
│                          ┌─────────────┐                            │
│                          │ noVNC/VM    │                            │
│                          │ Container   │                            │
│                          │             │                            │
│                          └─────────────┘                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Network Configuration

Default ports used by each service:

| Service         | Internal Port | External Port | Protocol |
|-----------------|---------------|---------------|----------|
| Frontend (UI)   | 5173/80       | 8090          | HTTP     |
| Orchestrator    | 8000          | 8000          | HTTP     |
| Context Manager | 8001          | 8001          | HTTP     |
| VNC Agent       | 8080          | 8080          | HTTP     |
| Redis           | 6379          | Not exposed   | TCP      |
| noVNC WebSocket | 6081          | 8901          | WS       |
| VNC Server      | 5900          | Not exposed   | VNC      |

## Security Considerations

- All inter-service communication occurs within the Docker network
- External endpoints should be protected with authentication
- API keys and secrets are stored in environment variables
- noVNC connections may be secured with TLS
- Session tokens should have appropriate expiration settings

## Development vs. Production

Key differences between development and production deployments:

**Development:**
- Services run individually or in containers
- SSH tunnels for local development with remote VM
- Environment variables from `.env` file
- Hot reloading enabled

**Production:**
- All services containerized
- Proper network security groups
- Managed database services
- Load balancing for high availability
- TLS termination and proper certificates

## Scaling Considerations

- Orchestrator and Context Manager can be horizontally scaled
- Redis can be configured as a cluster for high availability
- Browser VM instances can be created dynamically based on demand
- Consider session affinity for load balancing 