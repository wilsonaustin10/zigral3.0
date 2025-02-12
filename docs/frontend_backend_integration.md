# Implementation Plan & Checklist for Frontend–Backend Integration

## 1. Overview

- **Goal:** Connect the frontend chat UI with the backend orchestrator and agent modules, enabling real-time command processing, status updates, and HITL feedback through a secure API and WebSocket channels.
- **Key Components to Integrate:**
  - **Frontend Chat Interface:** Already built using a modern framework (e.g., React) with state management.
  - **Backend Orchestrator:** Exposes REST/WebSocket endpoints to process commands and dispatch tasks.
  - **Kasm Iframe:** Embedded in the frontend to display live agent operations.
  - **HITL and RL Feedback Endpoints:** Allow users to provide feedback and guide agent actions.

---

## 2. Detailed Step-by-Step Process

### 2.1 Finalize API Endpoints on the Backend

**2.1.A. Command Endpoint**
- **Task:** Create/verify the endpoint that accepts user commands.
- **Action:**
  - In your orchestrator (e.g., using FastAPI), ensure the endpoint (e.g., `POST /command`) validates input using Pydantic.
- **Code Example:**
  ```python
  from fastapi import FastAPI, HTTPException
  from pydantic import BaseModel

  app = FastAPI()

  class CommandRequest(BaseModel):
      command: str
      context: dict = {}

  @app.post("/command")
  async def command_endpoint(req: CommandRequest):
      try:
          result = await process_command(req.command, req.context)
          return result
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
  ```
- **Checklist:**
  - [ ] Validate JSON input with Pydantic.
  - [ ] Ensure error handling returns meaningful error messages.
  - [ ] Log incoming commands and responses for debugging.

**2.1.B. Feedback Endpoint**
- **Task:** Create an endpoint to receive human feedback from the frontend.
- **Action:**
  - Add a new endpoint (e.g., `POST /feedback`) to record HITL feedback.
- **Code Example:**
  ```python
  class FeedbackRequest(BaseModel):
      session_id: str
      action_id: str
      feedback: bool  # True for successful, False otherwise

  @app.post("/feedback")
  async def feedback_endpoint(feedback: FeedbackRequest):
      updated_context = await update_context_with_feedback(feedback.session_id, {"action_id": feedback.action_id, "success": feedback.feedback})
      return {"message": "Feedback recorded", "updated_context": updated_context}
  ```
- **Checklist:**
  - [ ] Validate feedback payload.
  - [ ] Update context manager with feedback.
  - [ ] Log feedback for RL purposes.

**2.1.C. Real-Time Communication via WebSockets (Optional but Recommended)**
- **Task:** Implement a WebSocket endpoint for real-time status updates.
- **Action:**
  - Create a WebSocket endpoint in the orchestrator.
- **Code Example:**
  ```python
  from fastapi import WebSocket

  @app.websocket("/ws/updates")
  async def websocket_endpoint(websocket: WebSocket):
      await websocket.accept()
      try:
          while True:
              update = await get_next_update()  # Implement to fetch latest agent updates
              await websocket.send_json(update)
      except Exception as e:
          await websocket.close()
  ```
- **Checklist:**
  - [ ] Set up WebSocket endpoint.
  - [ ] Integrate with your messaging queue (or agent update logic) for pushing updates.
  - [ ] Test secure connection and error handling.

---

### 2.2 Connect Frontend to Backend

**2.2.A. Integrate Chat Box with Command Endpoint**
- **Task:** Modify the chat UI so that it sends commands to the backend.
- **Action:**
  - Use REST (or WebSockets) to send commands.
- **Code Example (React with REST):**
  ```jsx
  import React, { useState, useEffect } from 'react';

  const ChatInterface = () => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');

    const sendMessage = async () => {
      const response = await fetch('https://your-backend-domain.com/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: input, context: {} }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { sender: 'orchestrator', text: data.message }]);
      setInput('');
    };

    return (
      <div className="chat-container">
        <div className="chat-history">
          {messages.map((msg, idx) => (
            <div key={idx} className={msg.sender}>{msg.text}</div>
          ))}
        </div>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your command..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    );
  };

  export default ChatInterface;
  ```
- **Checklist:**
  - [ ] Ensure API URL is correctly configured.
  - [ ] Handle error responses gracefully (show error messages to the user).
  - [ ] Log commands and responses in the frontend for debugging.

**2.2.B. Integrate WebSocket for Real-Time Updates (Optional)**
- **Task:** Connect the frontend to the backend WebSocket for live updates.
- **Action:**
  - Use a library like Socket.IO or native WebSocket API.
- **Code Example (React with Socket.IO):**
  ```jsx
  import React, { useState, useEffect } from 'react';
  import { io } from 'socket.io-client';

  const RealTimeUpdates = () => {
    const [updates, setUpdates] = useState([]);
    const socket = io('https://your-backend-domain.com');

    useEffect(() => {
      socket.on('agent_update', (data) => {
        setUpdates(prev => [...prev, data]);
      });
      return () => socket.disconnect();
    }, []);

    return (
      <div>
        {updates.map((update, index) => <p key={index}>{update.message}</p>)}
      </div>
    );
  };

  export default RealTimeUpdates;
  ```
- **Checklist:**
  - [ ] Verify WebSocket connection and reconnection logic.
  - [ ] Test secure connection (TLS, proper origin checks).

---

### 2.3 Iframe Embedding of Kasm

**2.3.A. Embed the Kasm VDI**
- **Task:** Ensure the Kasm VDI is embedded securely in the frontend.
- **Action:**
  - Embed an iframe that displays the Kasm interface.
- **Code Example (React):**
  ```jsx
  const KasmEmbed = () => {
    return (
      <iframe
        title="Kasm VDI for Agents"
        src="https://your-kasm-instance/lincoln"
        style={{ width: '100%', height: '600px', border: 'none' }}
        sandbox="allow-scripts allow-same-origin"
      />
    );
  };

  export default KasmEmbed;
  ```
- **Checklist:**
  - [ ] Confirm the iframe's source URL is served over HTTPS.
  - [ ] Set appropriate sandbox attributes.
  - [ ] Use postMessage for secure communication if needed.

---

### 2.4 Dashboard Integration

**2.4.A. Agent Manager Dashboard**
- **Task:** Connect the agent manager dashboard to backend updates.
- **Action:**
  - Ensure the dashboard receives real-time activity data (via WebSockets or periodic polling).
  - Display the list of agents, activity stream, and configuration toggles.
- **Code Example (React Component):**
  ```jsx
  const AgentManagerDashboard = () => {
    const agents = ['Lincoln', 'Shaun'];
    const [activityStream, setActivityStream] = useState([]);
    const [videoToggle, setVideoToggle] = useState({ Lincoln: false, Shaun: false });

    const toggleVideo = (agent) => {
      setVideoToggle(prev => ({ ...prev, [agent]: !prev[agent] }));
    };

    // Example: polling for updates (replace with WebSocket integration as needed)
    useEffect(() => {
      const interval = setInterval(async () => {
        const res = await fetch('https://your-backend-domain.com/updates');
        const data = await res.json();
        setActivityStream(data);
      }, 5000);
      return () => clearInterval(interval);
    }, []);

    return (
      <div className="dashboard">
        <div className="sidebar">
          <h3>Agents</h3>
          {agents.map(agent => (
            <div key={agent} className="agent-item">
              <span>{agent}</span>
              <button onClick={() => toggleVideo(agent)}>
                {videoToggle[agent] ? 'Hide Video' : 'Watch in Action'}
              </button>
              <button className="settings">⚙️</button>
            </div>
          ))}
        </div>
        <div className="activity-stream">
          <h3>Activity Stream</h3>
          {activityStream.map((act, idx) => (
            <div key={idx}>{act.message}</div>
          ))}
        </div>
        <div className="video-stream">
          {videoToggle['Lincoln'] && (
            <iframe
              title="Lincoln Video Stream"
              src="https://your-kasm-instance/lincoln"
              style={{ width: '100%', height: '400px', border: 'none' }}
              sandbox="allow-scripts allow-same-origin"
            />
          )}
        </div>
      </div>
    );
  };

  export default AgentManagerDashboard;
  ```
- **Checklist:**
  - [ ] Ensure real-time updates are reflected in the dashboard.
  - [ ] Test toggling video streaming.
  - [ ] Verify configuration controls (gear icons) work as intended.

---

### 2.5 Reinforcement Learning and HITL Feedback

**2.5.A. Backend Integration for Feedback**
- **Task:** Ensure the orchestrator records user feedback.
- **Action:**
  - Use the `/feedback` endpoint to capture HITL responses.
  - Update context in the Context Manager accordingly.
- **Code Example:** (See previous FastAPI endpoint in section 4.2.B above)
- **Checklist:**
  - [ ] Test the feedback loop (simulate a user confirming an action).
  - [ ] Verify feedback is stored for reinforcement learning.

---

## 3. Final Checklist

- **[ ]** Verify that the frontend chat UI sends commands to the orchestrator endpoint and displays responses.
- **[ ]** Ensure the orchestrator validates commands, updates context, and dispatches tasks to agents.
- **[ ]** Confirm that the WebSocket (or polling) mechanism pushes real-time updates to the frontend.
- **[ ]** Embed the Kasm VDI securely in an iframe and verify communication via `postMessage` if needed.
- **[ ]** Integrate the Agent Manager Dashboard to display agent status, activity streams, and video streaming toggles.
- **[ ]** Implement the feedback loop in the frontend to capture HITL responses and send them to the `/feedback` endpoint.
- **[ ]** Test the complete integration locally using Docker Compose (or your preferred method) and monitor logs.
- **[ ]** Ensure all endpoints are secured with HTTPS and proper authentication mechanisms.
- **[ ]** Document all configuration changes and update the README with instructions for running the integrated system.

---

## 4. Running in Development

- **Step 4.A:** Launch the backend (orchestrator, context manager) and frontend services locally.
- **Step 4.B:** Use your Docker Compose setup (e.g., `docker-compose -f docker-compose.vdi.yml up -d`) to spin up the full stack.
- **Step 4.C:** Access the frontend chat UI in your browser, interact with the chat, and observe updates in the Agent Manager Dashboard.
- **Step 4.D:** Test the credential input and 2FA flow by logging in through the frontend.
- **Step 4.E:** Validate that feedback prompts appear as configured and that feedback is recorded.

---

## Conclusion

This implementation plan and checklist provide a clear, step-by-step process to connect the Zigral frontend with the backend services. The plan ensures that user commands from the chat UI are processed by the orchestrator, agent actions are displayed via the Kasm iframe, and real-time updates and HITL feedback are integrated into the Agent Manager Dashboard. By following this guide, you'll be well positioned to complete the MVP by 2/15. 