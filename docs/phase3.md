# Phase 3: Virtual Desktop (VDI) Setup and Deployment Implementation Plan

This phase focuses on deploying Zigral in a Virtual Desktop Infrastructure (VDI) environment, enabling real-world GUI interactions for our agents (primarily Lincoln for LinkedIn), and integrating reinforcement learning, advanced credential handling, robust rollback mechanisms, and a unified agent manager dashboard.

---

## 1. Overview

- **Objective:** Deploy Zigral in a VDI environment so that multiple users can have isolated virtual desktops. This allows you to see and interact with the LinkedIn GUI (and other agent UIs) in real time.
- **Key Features to Implement Now:**
  - Improved Reinforcement Learning (RL) with Human-In-The-Loop (HITL)
  - Advanced Credential Handling with interactive 2FA
  - Robustness and Automated Rollbacks
  - Unified Agent Manager Dashboard with video streaming toggles and configuration controls
- **Future Enhancements (Not in Phase 3):**
  - Enhanced resource and cost monitoring (dynamic scaling, detailed cost tracking)

---

## 2. Detailed Deployment and Integration Plan

### 2.1 VDI Environment Setup

**2.1.A. Select a VDI Solution**
- **Step A:** After evaluating cloud-based VDI options, we have selected Kasm Workspaces (Community Edition) for its:
  - Native Docker container support
  - Built-in browser streaming capabilities
  - Robust security features
  - Free community edition for initial development and testing
  - Easy upgrade path to paid tiers when needed
- **Step B:** Choose a solution that allows for isolated sessions per user.
  - Kasm provides isolated container-based workspaces per user
  - Each workspace runs in its own Docker container with resource limits

**2.1.B. Configure Virtual Desktop Instances**
- **Step A:** Provision a VDI instance with a minimal desktop environment that supports remote viewing.
  ```yaml
  # docker-compose.vdi.yml
  version: '3.8'
  services:
    kasm:
      image: kasmweb/core:1.14.0
      ports:
        - "6901:6901"  # Kasm web interface
      environment:
        - VNC_PW=password123
        - KASM_USER=zigral
      volumes:
        - ./workspace:/workspace
  ```
- **Step B:** Ensure the instance includes all necessary dependencies:
  ```dockerfile
  # Dockerfile.vdi
  FROM kasmweb/core:1.14.0
  
  # Install required packages
  RUN apt-get update && apt-get install -y \
      python3.12 \
      python3-pip \
      git
  
  # Install Python dependencies
  COPY requirements.txt /tmp/
  RUN pip3 install -r /tmp/requirements.txt
  
  # Copy application code
  COPY . /app
  WORKDIR /app
  
  # Set environment variables
  ENV VIRTUAL_DESKTOP_MODE=True
  ENV ENABLE_VIDEO_STREAM=False
  ```
- **Step C:** Set up orchestration using Docker Compose for initial development, with the ability to migrate to Kubernetes if needed for larger scale deployments in the future.
  ```yaml
  # docker-compose.vdi.yml (extended with orchestration)
  version: '3.8'
  services:
    kasm:
      image: kasmweb/core:1.14.0
      ports:
        - "6901:6901"
      environment:
        - VNC_PW=password123
        - KASM_USER=zigral
      volumes:
        - ./workspace:/workspace
      deploy:
        resources:
          limits:
            cpus: '2'
            memory: 4G
      restart: unless-stopped
      networks:
        - zigral_network

    orchestrator:
      build: .
      depends_on:
        - kasm
      environment:
        - VIRTUAL_DESKTOP_MODE=True
      networks:
        - zigral_network

  networks:
    zigral_network:
      driver: bridge
  ```

---

### 2.2 Application Integration and Code Enhancements

**2.2.A. Update Environment Configuration**
```bash
# .env additions
VIRTUAL_DESKTOP_MODE=True
ENABLE_VIDEO_STREAM=False
KASM_API_KEY=your_api_key_here
KASM_API_URL=https://kasm.your-domain.com
```

**2.2.B. Modify Agent Code for VDI**
```python
# src/agents/lincoln/linkedin_client.py

import os
from playwright.async_api import async_playwright

async def launch_browser():
    headless = os.getenv("VIRTUAL_DESKTOP_MODE", "False").lower() in ("true", "1", "yes")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=headless,
            args=['--no-sandbox'] if headless else []
        )
        return browser

class LinkedInClient:
    async def initialize(self):
        self._browser = await launch_browser()
        self._page = await self._browser.new_page()
        if os.getenv("ENABLE_VIDEO_STREAM", "False").lower() in ("true", "1", "yes"):
            await self._page.video.start(
                path=f"captures/videos/{datetime.now().strftime('%Y%m%d_%H%M%S')}.webm"
            )
```

**2.2.C. Implement Advanced Credential and 2FA Handling**
```python
# src/ui/credentials.py

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/login", response_class=HTMLResponse)
async def login_form():
    return """
    <form method="post">
        <input name="username" placeholder="LinkedIn Username">
        <input name="password" type="password" placeholder="Password">
        <button type="submit">Login</button>
    </form>
    """

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    # Store credentials securely for this session only
    return {"success": True}

@app.get("/2fa", response_class=HTMLResponse)
async def twofa_form():
    return """
    <form method="post">
        <input name="code" placeholder="Enter 2FA Code">
        <button type="submit">Verify</button>
    </form>
    """
```

**2.2.D. Implement Reinforcement Learning (RL) and HITL**
```python
# src/orchestrator/rl_manager.py

class RLManager:
    def should_prompt_feedback(self, action_count: int, hitl_disabled: bool) -> bool:
        if hitl_disabled:
            return False
        if action_count <= 5:
            return True
        elif action_count <= 25 and action_count % 5 == 0:
            return True
        elif action_count > 25 and action_count % 25 == 0:
            return True
        return False

    async def store_feedback(self, action_id: str, feedback: dict):
        # Store feedback in Context Manager
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{CONTEXT_MANAGER_URL}/context/{action_id}/feedback",
                json=feedback
            )
```

**2.2.E. Unified Agent Manager Dashboard**
```python
# src/ui/agent_manager.py

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.websocket("/ws/agent-status")
async def agent_status_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Stream agent status updates
            status = await get_agent_status()
            await websocket.send_json(status)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
```

---

### 2.3 Container Orchestration for Multi-User VDI

**2.3.A. Orchestration Settings**
```yaml
# docker-compose.vdi.yml
version: '3.8'
services:
  vdi:
    image: ghcr.io/your_repo/zigral-vdi:latest
    environment:
      - VIRTUAL_DESKTOP_MODE=True
      - ENABLE_VIDEO_STREAM=${ENABLE_VIDEO_STREAM}
    ports:
      - "6901:6901"  # Kasm web interface
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '2'
          memory: 4G
    volumes:
      - ./workspace:/workspace
      - ./logs:/app/logs

  orchestrator:
    image: ghcr.io/your_repo/zigral-orchestrator:latest
    depends_on:
      - vdi
    environment:
      - VIRTUAL_DESKTOP_MODE=True

  context_manager:
    image: ghcr.io/your_repo/zigral-context-manager:latest
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/zigral
```

---

### 2.4 Testing and Integration Considerations

**2.4.A. Integration Tests for VDI and UI**
```python
# tests/virtual_desktop/test_desktop_manager.py

import pytest
from src.virtual_desktop.desktop_manager import launch_virtual_desktop

@pytest.mark.asyncio
async def test_launch_virtual_desktop():
    page = await launch_virtual_desktop()
    assert page is not None
    # Verify browser launched in correct mode
    assert page.context.browser.is_connected()

@pytest.mark.asyncio
async def test_video_streaming():
    os.environ["ENABLE_VIDEO_STREAM"] = "true"
    page = await launch_virtual_desktop()
    # Verify video capture started
    video_path = Path("captures/videos")
    assert any(video_path.iterdir())
```

---

## 3. Order of File Creation (Phase 3)

1. Update configuration files:
   - `.env` and `.env.example`
   - `docker-compose.vdi.yml`
   - `Dockerfile.vdi`

2. Create virtual desktop integration:
   - `src/virtual_desktop/desktop_manager.py`
   - `src/virtual_desktop/utils.py`

3. Create UI enhancements:
   - `src/ui/agent_manager.py`
   - `src/ui/credentials.py`
   - `src/ui/feedback.py`

4. Update orchestrator code:
   - `src/orchestrator/orchestrator.py`
   - `src/orchestrator/rl_manager.py`

5. Create test files:
   - `tests/virtual_desktop/test_desktop_manager.py`
   - `tests/ui/test_credentials.py`
   - `tests/ui/test_feedback.py`

---

## 4. Running the Application in Development

1. Start the VDI environment:
```bash
docker-compose -f docker-compose.vdi.yml up -d
```

2. Access the Kasm web interface:
```bash
open http://localhost:6901
```

3. Monitor agent activity through the dashboard:
```bash
open http://localhost:8080/dashboard
```

---

## 5. Summary

This Phase 3 implementation plan provides:
- VDI deployment using Kasm Workspaces
- Reinforcement learning with human-in-the-loop feedback
- Advanced credential handling with 2FA support
- Unified agent manager dashboard
- Container orchestration for multi-user support
- Comprehensive testing strategy

The plan prioritizes:
- Security through isolated containers
- Scalability via Docker/Kubernetes
- User experience with real-time monitoring
- Cost-effectiveness using Kasm's community edition

---

## References

1. [Docker Container Security Best Practices](https://www.wiz.io/academy/docker-container-security-best-practices)
2. [Docker Technology Enables the Next Generation of Desktop-as-a-Service (DaaS)](https://www.docker.com/blog/docker-technology-enables-the-next-generation-of-desktop-as-a-service-daas/)
3. [Best VDI Solutions](https://thectoclub.com/tools/best-vdi-solutions/) 