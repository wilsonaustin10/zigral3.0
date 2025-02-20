# noVNC Implementation Guide

## 1. High-Level Architecture Overview

**Components:**

- **Preconfigured Compute Engine VM:**  
  A lightweight Linux VM that already runs a live Chrome/Chromium session with a full UI (no Xvfb/VNC setup needed on your end).

- **Live Browser Session:**  
  Chrome runs in "headful" mode so that its full UI is available for remote interaction.

- **Remote Desktop Embedding:**  
  A VNC server streams the Chrome UI. A browser-based VNC client (such as noVNC) is embedded in your web app's front end to let users interact with the live session.

- **Backend Services:**  
  A FastAPI server handles user authentication, secure session management, and (in the future) orchestration for scaling. The front end (built with Vite and JavaScript) communicates with FastAPI (via REST or WebSockets) to manage sessions and relay the embedded session URL.

- **Future Scaling:**  
  Although the MVP currently uses a single preconfigured VM, the design allows for scaling via ephemeral VMs or containerized browser sessions (e.g., Docker and Kubernetes) when needed.

*Diagram:*

```mermaid
flowchart TD
    A[User's Browser] -->|Loads Web App with noVNC Client| B[FastAPI Backend]
    B -->|Serves VNC session URL & manages auth| C[Preconfigured Compute Engine VM]
    C -->|Runs Chrome/Chromium (Live Browser)| D[Browser Session]
    subgraph "Remote Interaction"
      A <--> E[WebSocket/Secure Tunnel]
    end
```

---

## 2. Implementation Plan

### 2.1 noVNC Server Setup
- [ ] Install noVNC server package
- [ ] Configure WebSocket proxy
  - Port: 6080 (standard noVNC port)
  - Enable SSL/TLS
  - Configure proxy settings for existing Debian 12 VM
- [ ] Set up secure tunneling
  - Configure SSL certificates
  - Set up WebSocket secure (WSS) endpoint
- [ ] Implement session persistence
  - Configure VNC server to maintain session state
  - Set up automatic session recovery

### 2.2 Frontend Integration

#### 2.2.1 noVNC Viewer Container
- [ ] Update `frontend/index.html`:
  - Modify existing iframe container for noVNC viewer
  - Add connection status indicators
  - Maintain refresh/fullscreen controls
- [ ] Update `frontend/js/chat.js`:
  - Add connection status messages to chat interface
  - Implement status indicator updates
- [ ] Create `frontend/js/vnc-client.js`:
  - Implement noVNC client initialization
  - Handle connection lifecycle
  - Manage reconnection logic
    - Maximum 5 reconnection attempts
    - 5-second delay between attempts
    - Connection quality monitoring

#### 2.2.2 Status Indicators
- [ ] Implement the following status messages:
  ```javascript
  const VNC_STATUS = {
    CONNECTING: "Connecting...",
    CONNECTED: "Connected",
    RECONNECTING: "Connection lost - attempting reconnect ({attempt}/5)",
    POOR_QUALITY: "Connection quality poor",
    TERMINATED: "Connection terminated - refresh to reconnect"
  }
  ```
- [ ] Add visual indicators in the UI for each state
- [ ] Integrate status updates with chat interface

#### 2.2.3 Connection Management
- [ ] Implement auto-reconnect logic:
  - Track connection attempts (max 5)
  - Implement 5-second delay between attempts
  - Handle permanent failure after max attempts
- [ ] Add connection quality monitoring:
  - Track latency
  - Monitor frame rate
  - Trigger "poor quality" warning above 400ms latency
- [ ] Maintain existing refresh/fullscreen controls

### 2.3 Backend Updates

#### 2.3.1 FastAPI Integration
- [ ] Add VNC session management endpoints:
  ```python
  /api/vnc/session
  /api/vnc/status
  /api/vnc/reconnect
  ```
- [ ] Integrate with existing JWT authentication
- [ ] Implement session persistence storage
- [ ] Add WebSocket endpoints for real-time status updates

#### 2.3.2 Session Management
- [ ] Implement session tracking
- [ ] Add session recovery mechanisms
- [ ] Configure automatic session cleanup
- [ ] Implement connection monitoring

### 2.4 Monitoring & Debugging Setup

#### 2.4.1 Server-Side Monitoring
- [ ] Configure logging for:
  - noVNC server
  - WebSocket proxy
  - Connection events
  - Performance metrics
- [ ] Set up resource monitoring:
  - CPU usage
  - Memory utilization
  - Network bandwidth
  - Connection latency

#### 2.4.2 Client-Side Debugging
- [ ] Implement browser console logging
- [ ] Add performance monitoring
- [ ] Set up connection quality metrics
- [ ] Configure WebSocket debugging tools

### 2.5 Testing & Validation

#### 2.5.1 Connection Testing
- [ ] Test initial connection
- [ ] Verify auto-reconnect functionality
- [ ] Validate session persistence
- [ ] Check status indicator accuracy

#### 2.5.2 Performance Testing
- [ ] Measure connection latency
- [ ] Verify frame rate
- [ ] Test under various network conditions
- [ ] Validate resource usage

## 3. File Changes Checklist

### Frontend Files
- [ ] `frontend/index.html`
  - Update iframe container
  - Add status indicators
- [ ] `frontend/js/chat.js`
  - Add connection status handling
  - Implement chat notifications
- [ ] `frontend/js/vnc-client.js` (new file)
  - Implement noVNC client
  - Add connection management
- [ ] `frontend/css/styles.css`
  - Add styles for status indicators
  - Update iframe container styles

### Backend Files
- [ ] `src/api/vnc.py` (new file)
  - Add VNC session endpoints
  - Implement session management
- [ ] `src/api/websocket.py`
  - Add VNC status updates
  - Implement real-time monitoring

### Configuration Files
- [ ] `config/novnc.conf`
  - WebSocket proxy configuration
  - SSL/TLS settings
- [ ] `.env`
  - Add VNC-related environment variables
- [ ] `docker-compose.yml`
  - Update service configuration

## 4. Deployment Steps

1. **noVNC Server**
   - [ ] Install and configure noVNC
   - [ ] Set up WebSocket proxy
   - [ ] Configure SSL/TLS

2. **Backend Services**
   - [ ] Deploy updated FastAPI service
   - [ ] Configure WebSocket endpoints
   - [ ] Set up session management

3. **Frontend Deployment**
   - [ ] Build and deploy frontend changes
   - [ ] Verify noVNC integration
   - [ ] Test connection handling

4. **Validation**
   - [ ] Verify all status indicators
   - [ ] Test reconnection logic
   - [ ] Validate session persistence
   - [ ] Check monitoring and logging

## 5. Development Workflow

### Local Development
1. Run noVNC server locally
2. Use development environment variables
3. Test with local FastAPI server
4. Monitor WebSocket communication

### Debugging
1. Use browser DevTools for WebSocket inspection
2. Monitor server logs for connection issues
3. Track performance metrics
4. Use noVNC debugging tools

### Testing
1. Test connection scenarios
2. Verify reconnection logic
3. Validate status updates
4. Check performance metrics

---

## 3. Best Practices

### Security
- **Encrypt All Communication:**  
  Use HTTPS for all endpoints and secure your noVNC connection via a reverse proxy.
- **Robust Authentication:**  
  Implement strong user authentication (e.g., JWT) to ensure only authorized users access sessions.
- **Session Isolation:**  
  Maintain clear separation between user sessions, even if they share the same underlying VM.

### Performance
- **Resource Optimization:**  
  Since the browser session is live, optimize your server's resource allocation to maintain a responsive UI.
- **Monitoring:**  
  Use monitoring tools to track CPU, memory, and network usage, enabling proactive scaling decisions.

### Future Scaling
- **Containerization:**  
  Package your browser session environment into Docker containers to facilitate dynamic scaling.
- **Ephemeral Sessions:**  
  Design your architecture so sessions can be created and terminated dynamically in response to user demand.

---

## 4. Conclusion

This implementation plan focuses on embedding the preconfigured live Chrome session into your web app and securing user access, while omitting the details for setting up the VM (Xvfb, VNC) and Playwright automation—which you've already completed. The remaining steps ensure that your noVNC integration is robust, your user sessions are secure, and your system is ready to scale as needed.

Feel free to ask if you need additional details or further customization for your specific use case. 