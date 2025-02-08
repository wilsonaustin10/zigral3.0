Below is the Zigral Requirements Document with a new "Model Context Protocol" section. This section describes a dedicated Context Manager microservice that stores and retrieves context (job parameters, historical action sequences, GUI states, and user feedback) to enrich LLM prompts and help agents learn over time. I've also indicated that an initial, basic version of the Context Manager should be built in Phase 1, with further refinements (e.g., reinforcement learning integration) added in Phase 3.

---

# Zigral Requirements Document (Comprehensive & Detailed)

## 1. Overview

**Zigral** is an autonomous sales development application that acts as your virtual sales development representative. Using a modular, microservice-based architecture, Zigral coordinates multiple specialized agents to perform tasks such as prospecting and data management. For the MVP, the focus is on two agents:  
- **Lincoln (LinkedIn Agent):** Automates prospecting on LinkedIn/LinkedIn Sales Navigator.  
- **Shaun (Google Sheets Agent):** Manages and updates prospect lists in Google Sheets.

The application is built incrementally with robust error handling, detailed logging, automated testing, and a structured version control process. Containerization, asynchronous messaging, centralized persistent storage, caching, a real-time dashboard, and a dedicated model context protocol ensure the system is scalable, maintainable, and cost-effective. Future production deployments will run in a virtual desktop (or headless browser) environment.

---

## 2. High-Level Architecture

### 2.1 Core Components

- **Orchestrator (Project Manager):**
  - **Role & Function:**  
    - Receives high-level user commands (e.g., "find all CTOs…"), leverages an LLM (with Retrieval Augmented Generation) to convert commands plus contextual data into a structured JSON action sequence, and coordinates tasks among agents.
  - **Processes & Methodologies:**  
    - **Checkpointing & Fallback Handling:** Periodically pauses to validate outcomes and, if errors occur, triggers fallback LLM calls.
  - **Testing:** Unit tests (using pytest) for orchestration functions and end-to-end integration tests.

- **Agent Modules (Microservices):**
  - **Containerization:**  
    - Each agent is deployed in its own Docker container for isolation and independent scalability.
  - **For MVP:**  
    - **Lincoln (LinkedIn Agent):** Uses Playwright to automate LinkedIn interactions (login, search, data collection) and captures GUI states (screenshots/HTML) for validation.
    - **Shaun (Google Sheets Agent):** Uses an API (e.g., gspread) to connect to and update Google Sheets with data received from Lincoln.
  - **Inter-Agent Communication:**  
    - Agents exchange standardized JSON messages asynchronously over RabbitMQ.

- **User Interface (UI) & Dashboard:**
  - **Dashboard:**  
    - A web-based, real-time dashboard displays Zigral's progress, agent statuses, logs, and performance metrics.
    - **Solution:** Grafana is used along with Prometheus for metrics and Grafana Loki for log aggregation and alerting.

- **Data Persistence & Logging:**
  - **Database:**  
    - PostgreSQL stores user reference data, prospect details, action sequences, logs, and later, context information.
    - **Backup & Recovery:** Regular backups are scheduled.
  - **Caching:**  
    - Redis caches frequently accessed data and successful action sequences to reduce redundant LLM calls.
  - **Message Broker:**  
    - RabbitMQ handles asynchronous messaging between the orchestrator and agents.
  - **Logging & Observability:**  
    - Logs are collected in Grafana Loki and key metrics in Prometheus, with visualization in Grafana.

- **LLM Integration:**
  - **Modular Design:**  
    - The LLM integration is abstracted to allow easy switching between providers (e.g., OpenAI, Deepseek R1, Claude) or using different models for specific tasks.
  - **Fallback Guidance:**  
    - The LLM is used for both generating action sequences and providing corrective steps when agents encounter errors.

- **RPA Tools:**
  - **Playwright:**  
    - Drives human-like browser automation on LinkedIn to ensure reliability and avoid detection.

- **Virtual Desktop Environment:**
  - **Production Support:**  
    - The architecture supports deployment into a virtual desktop or headless browser environment, allowing browser-based agents to run in the background without interfering with user operations.
  - **Resource Isolation:**  
    - Container resource limits and proper orchestration ensure efficient operation in a virtual desktop setting.

- **Model Context Protocol (Context Manager):**  
  - **Purpose:**  
    - Enhances agent performance and learning by storing and retrieving contextual information for each job, such as search parameters, successful action sequences, GUI snapshots, and user feedback.
  - **Integration:**  
    - **Location in Architecture:**  
      - Sits alongside the Orchestrator as a dedicated microservice.
      - The Orchestrator queries the Context Manager before generating LLM prompts, and agents update context as tasks progress.
    - **Implementation Approach:**  
      - **Custom Microservice:** Build using FastAPI in Python.
      - **Data Storage:** Use PostgreSQL to store structured context data (with optional Redis caching for frequently accessed entries).
      - **API Endpoints:**  
        - **POST /context:** Create a new context entry.
        - **GET /context/{job_id}:** Retrieve context for a given job.
        - **PUT /context/{job_id}:** Update context with new data (e.g., successful steps, error snapshots, user feedback).
        - **DELETE /context/{job_id}:** Remove obsolete context.
    - **Development Phase:**  
      - Build an initial, basic Context Manager module in **Phase 1** to support essential context storage and retrieval.  
      - Further enhancements (such as reinforcement learning integration and deeper context analytics) are planned for **Phase 3**.

---

## 3. Functional Requirements

### 3.1 User Input & Contextual Data

- **Command Input:**  
  - Users submit high-level commands (e.g., "find all CTOs in territory") via a web UI or CLI/API.
- **Contextual Data:**  
  - **MVP:** Default or manually entered context is used.
  - **Future Enhancement:**  
    - During setup, prompt users to upload their account list via CSV (including segmentation details like headcount or revenue).  
    - Store this contextual data in PostgreSQL and provide it to the LLM and agents.
- **Action Sequence Generation:**  
  - The orchestrator uses the LLM, enriched with contextual data from the Context Manager, to generate a JSON action sequence.
  - **Example:**
    ```json
    {
      "objective": "Find all CTOs in territory",
      "steps": [
        {"agent": "LinkedIn", "action": "navigate", "target": "LinkedIn Sales Navigator"},
        {"agent": "LinkedIn", "action": "search", "criteria": {"title": "CTO", "location": "User Territory"}},
        {"agent": "LinkedIn", "action": "collect", "fields": ["name", "company", "contact_info"]},
        {"agent": "GoogleSheets", "action": "update", "target": "prospect_list"}
      ]
    }
    ```

### 3.2 Agent Module Operations

- **Lincoln (LinkedIn Agent):**  
  - Automates login, search, and data collection on LinkedIn using Playwright.
  - Captures and sends current GUI state (screenshot/HTML snippet) for validation.
- **Shaun (Google Sheets Agent):** ✅ 
  - Connects to Google Sheets using gspread library ✅
  - Creates and manages prospect spreadsheets ✅
  - Shares spreadsheets with specified users ✅
  - Validates and formats prospect data before insertion ✅
  - Handles batch operations for multiple prospects ✅
  - Supports multiple spreadsheets and worksheets ✅
  - Implements proper error handling and validation ✅
  - Uses OAuth2 for secure authentication ✅
  - Provides detailed operation logging ✅
- **Inter-Agent Communication:**  
  - Uses RabbitMQ to exchange standardized JSON messages asynchronously.

### 3.3 Error Handling & Human-In-The-Loop Feedback

- **Self-Reporting & Fallback:**  
  - Agents monitor their operational state and report errors or unexpected changes to the orchestrator.
  - The orchestrator triggers a fallback LLM call for corrective guidance (e.g., "retry action" or "click X").
- **Human-In-The-Loop (HITL):**  
  - The system includes periodic checkpoints where the orchestrator pauses to request human feedback.
  - **Methodology:**  
    - Prompt users to validate outputs and, if necessary, manually adjust or override the generated action sequence.
    - Store validated feedback in PostgreSQL to inform future LLM calls and reinforce learning.
- **Reinforcement Learning:**  
  - Validated action sequences and outcomes are stored for continuous improvement and reduced redundant LLM calls.

---

## 4. Development Phases

### Phase 1: Project Setup and Orchestrator Prototype

1. **Define Requirements & MVP Scope:**  
   - Focus on developing Lincoln (LinkedIn Agent) and Shaun (Google Sheets Agent) with a basic Context Manager.
2. **Environment Setup:**  
   - Set up Git version control, a dedicated virtual environment, and install core dependencies (Python, Playwright, Asyncio, OpenAI API, Flask/FastAPI).
3. **Orchestrator Development:**  
   - Create an API/CLI that accepts user commands and contextual data.
   - Integrate LLM calls to convert inputs (with context) into JSON action sequences.
   - Implement logging (with PostgreSQL and Grafana Loki) and checkpointing.
   - **Testing:** Write unit tests using pytest for each new function.
4. **Context Manager Module (Model Context Protocol):**  
   - **Build Basic Version in Phase 1:**  
     - Create a dedicated microservice using FastAPI.
     - Define API endpoints (POST, GET, PUT, DELETE) for context management.
     - Set up PostgreSQL (with optional Redis caching) for storage.
     - Write initial tests for the context endpoints.
   - **Future Enhancements (Phase 3):**  
     - Expand reinforcement learning capabilities and deeper context analytics.
5. **Version Control & Commit Strategy:**  
   - **Frequent Commits:** Commit each atomic, test-passing unit of work to feature branches.
   - **Milestone Merges:** Merge feature branches into the main branch after integration testing and review.
   - **Detailed Commit Messages:** Document each commit clearly.

### Phase 2: Building and Integrating Individual Agents

1. **Lincoln (LinkedIn Agent):**  
   - Containerize the agent with Docker.
   - Implement Playwright scripts for LinkedIn login, search, and data capture.
   - Capture and report GUI states via RabbitMQ.
   - **Testing:** Develop unit tests for each core functionality.
2. **Shaun (Google Sheets Agent):**  
   - Containerize with Docker.
   - Implement Google Sheets integration using gspread.
   - Update prospect lists based on data received from Lincoln.
   - **Testing:** Write tests for data insertion, updates, and error handling.
3. **Inter-Agent Communication:**  
   - Set up RabbitMQ as the asynchronous messaging broker.
   - Define and test standardized JSON messaging formats.
4. **Error Handling & LLM Assistance:**  
   - Integrate error reporting and fallback mechanisms.
   - Write tests simulating error conditions and verifying fallback responses.

### Phase 3: Extending Functionality and Reinforcement Learning

1. **Caching & Persistence:**  
   - Integrate Redis for caching successful action sequences.
   - Continue to use PostgreSQL for persistent storage of prospect data, logs, and context.
   - **Testing:** Write tests for caching behavior and database operations.
2. **Multi-Agent Coordination & Data Handoffs:**  
   - Automate data transfers (e.g., from Lincoln to Shaun).
   - Build integration tests simulating end-to-end workflows.
3. **User Feedback & HITL Process:**  
   - Enhance the orchestrator to include regular human-in-the-loop checkpoints.
   - Implement the feedback override capability and store feedback data.
   - **Testing:** Validate the feedback loop and override process through simulated scenarios.
4. **Reinforcement Learning Integration:**  
   - Use the stored context and user feedback to adjust future LLM calls and improve performance.

### Phase 4: Virtual Desktop, Dashboard & Deployment

1. **Virtual Desktop/Headless Environment:**  
   - Package Zigral to run in a virtual desktop or headless environment, ensuring browser-based agents run in isolation.
2. **Real-Time Monitoring Dashboard:**  
   - Deploy Grafana (with Prometheus and Grafana Loki) for real-time monitoring.
   - Configure alerting thresholds and notification channels.
3. **Scalability & Continuous Operation:**  
   - Refine microservices for long-duration tasks with automatic retries and self-healing.
   - Conduct load and stress tests and write end-to-end tests for extended operation scenarios.

---

## 5. Technical Dependencies & Tools (Cost-Conscious Selections)

- **Programming Language:** Python (with Asyncio)
- **Containerization:** Docker
- **Message Broker:** RabbitMQ
- **Database:** PostgreSQL
- **Caching:** Redis
- **Automation/RPA:** Playwright
- **LLM Integration:** OpenAI API (with a modular interface to allow easy switching between providers)
- **API Framework:** Flask or FastAPI
- **Testing:** pytest (unit, integration, and end-to-end tests)
- **Logging & Observability:**  
  - **Log Aggregation:** Grafana Loki  
  - **Metrics:** Prometheus  
  - **Dashboard:** Grafana
- **Web UI:** Initially using Flask templates or Streamlit

---

## 6. Best Practices, Risk Management & Change Control

- **Modularity & Incremental Development:**  
  - Develop each component as an independent, containerized microservice with clear APIs.
- **Risk Management:**  
  - Regularly review external dependencies (e.g., LinkedIn UI, API updates) and document potential risks.
  - Establish a change control process using Git feature branches and pull requests, with reviews (aided by ChatGPT and static analysis tools).
- **Security & Privacy:**  
  - Use secure vaults or environment variable managers (e.g., python-dotenv) to protect credentials.
  - Enforce HTTPS and mTLS for secure inter-service communication and use RBAC for internal APIs.
- **DevOps & CI/CD Pipeline:**  
  - Set up a CI/CD pipeline (using GitHub Actions) to run automated tests on every commit and merge.
  - Monitor deployment metrics and costs with the observability stack.
- **User Feedback & Human-In-The-Loop:**  
  - Incorporate periodic checkpoints where the orchestrator requests human feedback.
  - Allow manual overrides and store validated feedback for reinforcement learning.

---

## 7. Version Control & Commit Strategy

- **Frequent Commits:**  
  - Commit each small, logical change that passes unit tests to feature branches.
- **Milestone Merges:**  
  - Merge into the main branch after integration testing and review.
- **Documentation:**  
  - Use detailed commit messages to maintain a clear change history.
- **Code Review:**  
  - Use ChatGPT as a supplementary tool for code reviews along with automated static analysis.

---

## 8. User Acceptance Testing (UAT) & Human-In-The-Loop (HITL) Feedback

- **UAT Planning:**  
  - After MVP completion, simulate real user scenarios and gather structured feedback.
- **HITL Process:**  
  - Implement periodic checkpoints where the orchestrator pauses for human validation.
  - Allow users to override or adjust the action sequence manually.
  - Store feedback in PostgreSQL to inform future reinforcement learning.
- **Testing:**  
  - Automate feedback and override simulations in end-to-end tests.

---

## 9. Project Management and Schedule

- **Daily Commitment:**
  - **Weekdays:** 2 hours per day for development, testing, and commits.
  - **Weekends:** 4 hours per day for integration, extended testing, and deployment tasks.
- **MVP Launch Target:** February 15, 2025.
- **Milestone Planning:**
  - **Phase 1 (Orchestrator, Basic Setup & Context Manager):** Complete by February 5, 2025.
  - **Phase 2 (Lincoln & Shaun Integration):** Complete by February 10, 2025.
  - **Phase 3 (Extended Testing, Feedback & Reinforcement Learning):** Complete by February 13, 2025.
  - **Final Integration & Dashboard Deployment:** Complete by February 14, 2025.
- **Agile/Sprint Planning:**
  - Self-managed daily stand-ups and a maintained sprint backlog.
  - Regular progress reviews via commit history and sprint retrospectives.

---

## 10. Future Enhancements

- **Contextual Data for Target Accounts:**  
  - Implement a setup process for CSV account list uploads in future phases.
- **Additional Agents:**  
  - Extend coordination to include Phylicia (phone agent) and Amelia (email agent).
- **Advanced Multi-Agent Coordination & Reinforcement Learning:**  
  - Leverage stored context and user feedback to further optimize action sequences.
- **Enhanced Dashboard:**  
  - Upgrade the UI for deeper analytics and a more user-friendly experience.
- **Scalability Improvements:**  
  - Continue refining microservices for sustained, long-duration operation.
- **Modular LLM Integration:**  
  - Enhance the abstraction layer to easily switch between or combine LLM providers for specialized tasks.
- **Production Deployment:**
  - Deploy Zigral in a virtual desktop or headless environment.
- **User-Created Agents:**
  - Allow users to create their own agents and share them with others.
  - Deploy functionality to support agents that are generated from a prompt.

---

## 11. Conclusion

This comprehensive requirements document outlines a detailed, cost-effective, and modular approach to building Zigral's MVP—initially focusing on Lincoln (LinkedIn Agent) and Shaun (Google Sheets Agent). The architecture supports production deployment in a virtual desktop or headless environment. With a dedicated Context Manager implementing the model context protocol, along with robust methodologies for risk management, security, CI/CD, testing, human-in-the-loop feedback, and modular LLM integration, Zigral is positioned to meet its functional and business objectives. The project is scheduled to launch its MVP on February 15, 2025.

---

### Summary of the Model Context Protocol Implementation

- **What It Does:**  
  - Stores context data (e.g., search parameters, successful action sequences, GUI snapshots, user feedback) to enrich LLM prompts.
- **Where It Sits:**  
  - As a dedicated microservice (Context Manager) alongside the Orchestrator.
- **How to Build It:**  
  - Use FastAPI to implement RESTful endpoints (POST, GET, PUT, DELETE) for context management.
  - Persist context data in PostgreSQL (with optional Redis caching).
  - Develop unit tests for each endpoint.
- **When to Build It:**  
  - Build an initial, basic version in **Phase 1** (to support essential context retrieval and updates).
  - Expand and refine the module (e.g., integrate reinforcement learning) in **Phase 3**.

---
