# Implementation Plan & Checklist for Frontend–Backend Integration

## 1. Overview

- [x] **Goal:** Connect the frontend chat UI with the backend orchestrator and agent modules, enabling real-time command processing, status updates, and HITL feedback through a secure API and WebSocket channels.
- [ ] **Key Components to Integrate:**
  - [x] **Frontend Chat Interface:** Already built using a modern framework with state management.
  - [x] **Backend Orchestrator:** Exposes REST/WebSocket endpoints to process commands and dispatch tasks.
  - [ ] **Kasm Iframe:** Embedded in the frontend to display live agent operations.
  - [ ] **HITL and RL Feedback Endpoints:** Allow users to provide feedback and guide agent actions.

---

## 2. Detailed Step-by-Step Process

### 2.1 Finalize API Endpoints on the Backend

**2.1.A. Command Endpoint**
- [x] Validate JSON input with Pydantic.
- [x] Ensure error handling returns meaningful error messages.
- [x] Log incoming commands and responses for debugging.

**2.1.B. Feedback Endpoint**
- [ ] Validate feedback payload.
- [ ] Update context manager with feedback.
- [ ] Log feedback for RL purposes.

**2.1.C. Real-Time Communication via WebSockets**
- [x] Set up WebSocket endpoint.
- [x] Integrate with messaging queue for pushing updates.
- [ ] Test secure connection and error handling.

---

### 2.2 Connect Frontend to Backend

**2.2.A. Integrate Chat Box with Command Endpoint**
- [x] Ensure API URL is correctly configured.
- [x] Handle error responses gracefully (show error messages to the user).
- [x] Log commands and responses in the frontend for debugging.

**2.2.B. Integrate WebSocket for Real-Time Updates**
- [x] Verify WebSocket connection and reconnection logic.
- [ ] Test secure connection (TLS, proper origin checks).

---

### 2.3 Iframe Embedding of Kasm

**2.3.A. Embed the Kasm VDI**
- [ ] Confirm the iframe's source URL is served over HTTPS.
- [ ] Set appropriate sandbox attributes.
- [ ] Use postMessage for secure communication if needed.

---

### 2.4 Dashboard Integration

**2.4.A. Agent Manager Dashboard**
- [x] Connect the agent manager dashboard to backend updates.
- [ ] Display the list of agents, activity stream, and configuration toggles.

---

### 2.5 Reinforcement Learning and HITL Feedback

**2.5.A. Backend Integration for Feedback**
- [ ] Test the feedback loop (simulate a user confirming an action).
- [ ] Verify feedback is stored for reinforcement learning.

---

## 3. Final Checklist

- [x] Verify that the frontend chat UI sends commands to the orchestrator endpoint and displays responses.
- [x] Ensure the orchestrator validates commands, updates context, and dispatches tasks to agents.
- [x] Confirm that the WebSocket (or polling) mechanism pushes real-time updates to the frontend.
- [ ] Embed the Kasm VDI securely in an iframe and verify communication via `postMessage` if needed.
- [ ] Integrate the Agent Manager Dashboard to display agent status, activity streams, and video streaming toggles.
- [ ] Implement the feedback loop in the frontend to capture HITL responses and send them to the `/feedback` endpoint.
- [ ] Test the complete integration locally using Docker Compose and monitor logs.
- [ ] Ensure all endpoints are secured with HTTPS and proper authentication mechanisms.
- [x] Document all configuration changes and update the README with instructions for running the integrated system.

---

## 4. Running in Development

- [x] **Step 4.A:** Launch the backend (orchestrator, context manager) and frontend services locally.
- [ ] **Step 4.B:** Use your Docker Compose setup (e.g., `docker-compose -f docker-compose.vdi.yml up -d`) to spin up the full stack.
- [ ] **Step 4.C:** Access the frontend chat UI in your browser, interact with the chat, and observe updates in the Agent Manager Dashboard.
- [ ] **Step 4.D:** Test the credential input and 2FA flow by logging in through the frontend.
- [ ] **Step 4.E:** Validate that feedback prompts appear as configured and that feedback is recorded.

---

## Recent Implementations (2025-02-12)

### 1. Authentication Setup
- Implemented temporary auth token system for development
- Added `TEMP_AUTH_TOKEN=zigral_dev_token_123` to `.env` file
- Frontend API client configured to use dev token by default
- Token automatically included in all API requests via Authorization header

### 2. WebSocket Integration
- Added WebSocket support to backend using `uvicorn[standard]`
- Implemented real-time updates for:
  - Command reception
  - Action sequence generation
  - Execution progress
  - Error handling
- Added reconnection logic with exponential backoff
- Fixed error handling for OpenAI API rate limits
- Updated error response format to match FastAPI standards
- Added proper HTTP status code propagation

### 3. Frontend Components
#### API Client (`frontend/js/api-client.js`)
- Implemented `ZigralAPI` class with:
  - REST endpoints for commands
  - WebSocket connection for real-time updates
  - Automatic token handling
  - Error handling and reconnection logic

#### Chat Interface (`frontend/js/chat.js`)
- Added status indicator for connection state
- Implemented message handling for different update types
- Added error display and recovery
- Integrated with API client for seamless communication

### 4. Status Indicators and Styling (`frontend/css/chat.css`)
- Added visual indicators for:
  - Connection status (connected, error, processing)
  - Message types (user, assistant, error, update)
- Implemented animations for processing state

### 5. Development Environment
- Frontend served on port 3000 (http://localhost:3000)
- Backend API on port 8000 (http://localhost:8000)
- WebSocket connection at ws://localhost:8000/ws/updates/

---

## Conclusion

This implementation plan and checklist provide a clear, step-by-step process to connect the Zigral frontend with the backend services. The plan ensures that user commands from the chat UI are processed by the orchestrator, agent actions are displayed via the Kasm iframe, and real-time updates and HITL feedback are integrated into the Agent Manager Dashboard. By following this guide, you'll be well positioned to complete the MVP by 2/15. 