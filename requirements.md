Below is the comprehensive, updated Zigral Requirements Document that now includes detailed methodologies and processes for risk management, change control, security and privacy, CI/CD and automated testing, user acceptance testing (UAT) with human-in-the-loop feedback, and a modular LLM integration approach. Each section has been expanded to provide clear, concise instructions to help guide the development of Zigral.

---

# Zigral Requirements Document (Comprehensive & Detailed)

## 1. Overview

**Zigral** is an autonomous sales development application that acts as your virtual sales development representative. Using a modular, microservice-based architecture, Zigral coordinates multiple specialized agents to perform tasks such as prospecting and data management. For the MVP, the focus is on two agents:  
- **Lincoln (LinkedIn Agent):** Automates prospecting on LinkedIn/LinkedIn Sales Navigator.  
- **Shaun (Google Sheets Agent):** Manages and updates prospect lists in Google Sheets.

The application is built incrementally with robust error handling, detailed logging, automated testing, and a structured version control process. Containerization, an asynchronous messaging system, centralized persistent storage, caching, and a real-time dashboard ensure that the system is scalable, maintainable, and cost-effective. Future production deployments will run in a virtual desktop (or headless browser) environment.

---

## 2. High-Level Architecture

### 2.1 Core Components

- **Orchestrator (Project Manager):**
  - **Role & Function:**  
    - Receives high-level user commands (e.g., “find all CTOs…”).  
    - Leverages an LLM (with Retrieval Augmented Generation) to convert commands, along with any contextual data, into a structured JSON action sequence.  
    - Coordinates tasks among agents via a standardized messaging protocol.
  - **Processes & Methodologies:**  
    - **Checkpointing:** Periodically pauses to validate outcomes either automatically or by prompting human input.  
    - **Fallback Handling:** If an agent reports an error or unexpected state, the orchestrator initiates a fallback LLM call for corrective guidance.
  - **Testing:** Unit tests (using pytest) for each orchestration function and end-to-end integration tests.
  
- **Agent Modules (Microservices):**
  - **Containerization:**  
    - Each agent is deployed as an independent Docker container, ensuring isolation and independent scalability.
  - **MVP Focus:**  
    - **Lincoln (LinkedIn Agent):** Uses Playwright to automate browser tasks (login, search, data collection) on LinkedIn. Captures GUI states (screenshots or HTML snippets) for verification.
    - **Shaun (Google Sheets Agent):** Uses an API (e.g., gspread) to connect to and update Google Sheets with prospect data from Lincoln.
  - **Inter-Agent Communication:**  
    - Employs RabbitMQ as the message broker to exchange standardized JSON messages asynchronously.
  
- **User Interface (UI) & Dashboard:**
  - **Dashboard:**  
    - A web-based, real-time dashboard displays Zigral’s progress—including agent statuses, logs, and key performance metrics.
    - **Solution:** Grafana is used, with Prometheus for metrics collection and Grafana Loki for log aggregation.  
    - **Methodology:** Real-time alerts and visualization ensure that any issues are promptly identified.

- **Data Persistence & Logging:**
  - **Database:**  
    - PostgreSQL stores user reference data, prospect details, action sequences, and logs.  
    - **Backup & Recovery:** Regular backup schedules are defined and documented for PostgreSQL.
  - **Caching:**  
    - Redis caches frequently accessed data and successful action sequences to reduce repetitive LLM calls.
  - **Message Broker:**  
    - RabbitMQ provides asynchronous, decoupled communication between the orchestrator and agents.
  - **Logging & Observability:**  
    - Logs are collected in Grafana Loki and key metrics in Prometheus, with visual dashboards in Grafana.  
    - **Alerting:** Defined alert thresholds and notification channels (e.g., Slack/email) are set up for critical events.

- **LLM Integration:**
  - **Modular Design:**  
    - The integration layer is abstracted so that multiple providers (OpenAI, Deepseek R1, Claude, etc.) can be swapped or used for different tasks without changing the rest of the system.
  - **Fallback Guidance:**  
    - The LLM is used both for translating user commands into action sequences and for providing corrective steps when errors are detected.
  
- **RPA Tools:**
  - **Playwright:**  
    - Drives browser automation with human-like interactions to avoid detection and ensure reliability.

- **Virtual Desktop Environment:**
  - **Production Support:**  
    - The architecture supports deployment into a virtual desktop or headless browser environment, ensuring that agents can run in the background without interfering with user operations.
  - **Resource Isolation:**  
    - Strategies for resource management (e.g., container resource limits) ensure efficient use of the virtual desktop environment.

---

## 3. Functional Requirements

### 3.1 User Input & Contextual Data

- **Command Input:**  
  - Users submit high-level commands (e.g., “find all CTOs in territory”) via the web UI or CLI/API.
- **Contextual Data:**  
  - **MVP:** For the initial release, default or manually entered context will be used.  
  - **Future Enhancement:**  
    - Implement a setup prompt for users to upload their account list via CSV, including segmentation details (e.g., headcount, revenue).  
    - Store this contextual data in PostgreSQL and provide it to the LLM and agents as needed.
- **Action Sequence Generation:**  
  - The orchestrator uses the LLM to generate a JSON action sequence based on both the command and any contextual data.  
  - **Example JSON:**  
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
  - Captures and sends the current GUI state for validation.
- **Shaun (Google Sheets Agent):**  
  - Connects to Google Sheets (via gspread) to update prospect lists.  
  - Receives data from Lincoln and maintains data integrity.
- **Inter-Agent Communication:**  
  - Uses RabbitMQ for standardized JSON message passing.
  
### 3.3 Error Handling & Human-In-The-Loop Feedback

- **Self-Reporting & Fallback:**  
  - Each agent continuously monitors its operational state and reports errors or unexpected UI changes back to the orchestrator.  
  - The orchestrator then triggers a fallback LLM call for corrective guidance.
- **Human-In-The-Loop (HITL):**  
  - The system includes periodic checkpoints where the orchestrator pauses to request human feedback.  
  - **Methodology:**  
    - The user is prompted to validate outputs or override the current action sequence if necessary.  
    - All user feedback is stored (in PostgreSQL) for reinforcement learning.
- **Reinforcement Learning:**  
  - Validated outcomes and action sequences are recorded to reduce future LLM calls and improve performance.

---

## 4. Development Phases

### Phase 1: Project Setup and Orchestrator Prototype

1. **Define Requirements & MVP Scope:**  
   - Focus on developing Lincoln and Shaun initially.
2. **Environment Setup:**  
   - Set up Git version control, a dedicated virtual environment, and install core dependencies (Python, Playwright, Asyncio, OpenAI API, Flask/FastAPI).
3. **Orchestrator Development:**  
   - Build an API/CLI that accepts user commands and contextual data.  
   - Integrate the LLM to convert inputs into JSON action sequences.  
   - Implement logging (with PostgreSQL and Grafana Loki) and periodic checkpoints.
   - **Testing:** Write unit tests using pytest for every new function.
4. **Version Control & Commit Strategy:**  
   - **Commit Frequently:** Commit each atomic, test-passing unit of work to feature branches.
   - **Milestone Merges:** Merge into the main branch after integration testing and review.
   - **Documentation:** Use detailed commit messages.

### Phase 2: Building and Integrating Individual Agents

1. **Lincoln (LinkedIn Agent):**  
   - Containerize using Docker.
   - Implement Playwright scripts for LinkedIn login, search, and data capture.
   - Capture GUI states and report back via RabbitMQ.
   - **Testing:** Develop unit tests for login simulation, search, and GUI capture.
2. **Shaun (Google Sheets Agent):**  
   - Containerize using Docker.
   - Implement Google Sheets integration using gspread.
   - Update prospect lists based on data received from Lincoln.
   - **Testing:** Write tests for data insertion, updates, and error handling.
3. **Inter-Agent Communication:**  
   - Set up RabbitMQ as the messaging broker.
   - Define and test JSON messaging formats.
4. **Error Handling & LLM Assistance:**  
   - Integrate error reporting and fallback mechanisms.
   - Write tests simulating error conditions and verifying fallback responses.

### Phase 3: Extending Functionality and Reinforcement Learning

1. **Caching & Persistence:**  
   - Integrate Redis for caching successful action sequences.
   - Use PostgreSQL for long-term storage of prospect data, logs, and action sequences.
   - **Testing:** Develop tests for caching behavior and database operations.
2. **Multi-Agent Coordination & Data Handoffs:**  
   - Automate data transfer (e.g., from Lincoln to Shaun).
   - Create integration tests that simulate end-to-end workflows.
3. **User Feedback & HITL Process:**  
   - Enhance the orchestrator to include regular human-in-the-loop checkpoints.
   - Implement a feedback override capability and store feedback data.
   - **Testing:** Validate the feedback loop and override process through simulated scenarios.

### Phase 4: Virtual Desktop, Dashboard & Deployment

1. **Virtual Desktop/Headless Environment:**  
   - Package Zigral to run in a virtual desktop or headless environment, ensuring that browser-based agents run in isolation.
2. **Real-Time Monitoring Dashboard:**  
   - Deploy Grafana (with Prometheus and Grafana Loki) to create a real-time monitoring dashboard.
   - Configure alerting thresholds and notification channels.
3. **Scalability & Continuous Operation:**  
   - Refine microservices to support long-duration tasks with automatic retries and self-healing.
   - Conduct load and stress tests and write end-to-end tests to simulate prolonged operation.

---

## 5. Technical Dependencies & Tools (Cost-Conscious Selections)

- **Programming Language:** Python (with Asyncio for concurrency)
- **Containerization:** Docker
- **Message Broker:** RabbitMQ
- **Database:** PostgreSQL
- **Caching:** Redis
- **Automation/RPA:** Playwright
- **LLM Integration:** OpenAI API (with a modular abstraction for switching models, e.g., Deepseek R1, Claude)
- **API Framework:** Flask or FastAPI
- **Testing:** pytest (with unit, integration, and end-to-end tests)
- **Logging & Observability:**  
  - **Log Aggregation:** Grafana Loki  
  - **Metrics:** Prometheus  
  - **Dashboard:** Grafana
- **Web UI:** Initially implemented with Flask templates or Streamlit

---

## 6. Best Practices, Risk Management & Change Control

- **Modularity & Incremental Development:**  
  - Develop each component as an independent, containerized microservice with clear APIs.
  - Incrementally build and test features, starting with the MVP.
- **Risk Management:**  
  - **Risk Identification:** Regularly review dependencies (e.g., LinkedIn UI changes, API updates) and document potential risks.  
  - **Mitigation & Change Control:** Establish a process for handling changes via feature branches and using Git pull requests (with reviews aided by ChatGPT and static analysis tools).  
  - **Change Approval:** Even as a solo developer, document proposed changes and test extensively before merging.
- **Security & Privacy:**  
  - Use secure vaults or environment variable managers (e.g., python-dotenv or a secrets manager) to protect credentials.  
  - Enforce HTTPS and, where possible, mTLS for secure inter-service communication.  
  - Implement role-based access control (RBAC) for internal APIs and encrypt sensitive data at rest and in transit.
- **DevOps & CI/CD Pipeline:**  
  - Set up a CI/CD pipeline (e.g., GitHub Actions) to run automated tests on every commit and merge.  
  - Monitor deployment metrics and costs, using the observability stack (Prometheus, Loki, Grafana).

---

## 7. Version Control & Commit Strategy

- **Frequent Commits:**  
  - Commit each small, logical change that passes unit tests to feature branches.
- **Milestone Merges:**  
  - Merge into the main branch after integration testing and review.
- **Documentation:**  
  - Ensure every commit has a descriptive message to maintain clear change history.
- **Code Review:**  
  - Use ChatGPT as a supplementary tool to perform code reviews and provide suggestions alongside automated static analysis tools.

---

## 8. User Acceptance Testing (UAT) & Human-In-The-Loop (HITL) Feedback

- **UAT Planning:**  
  - After MVP completion, conduct a UAT phase where real user scenarios are simulated.
  - Gather structured feedback via the dashboard and direct user interactions.
- **HITL Process:**  
  - Implement periodic checkpoints where the orchestrator pauses and prompts for human validation.
  - Allow users to override or adjust action sequences manually.
  - Store all validated actions and user feedback in PostgreSQL to inform reinforcement learning and future iterations.

---

## 9. Project Management and Schedule

- **Daily Commitment:**
  - **Weekdays:** 2 hours per day for development, testing, and commits.
  - **Weekends:** 4 hours per day for integration, extended testing, and deployment tasks.
- **MVP Launch Target:** February 15, 2025.
- **Milestone Planning:**
  - **Phase 1 (Orchestrator & Basic Setup):** Complete by February 5, 2025.
  - **Phase 2 (Lincoln & Shaun Integration):** Complete by February 10, 2025.
  - **Phase 3 (Extended Testing & Feedback Loop):** Complete by February 13, 2025.
  - **Final Integration & Dashboard Deployment:** Complete by February 14, 2025.
- **Agile/Sprint Planning:**
  - Conduct daily stand-ups (self-managed) and maintain a sprint backlog.
  - Regularly review progress via commit history and adjust priorities as necessary.

---

## 10. Future Enhancements

- **Contextual Data for Target Accounts:**  
  - Implement a setup process for CSV account list uploads in future phases.
- **Additional Agents:**  
  - Extend coordination to include Phylicia (phone agent) and Amelia (email agent).
- **Advanced Multi-Agent Coordination & Reinforcement Learning:**  
  - Integrate reinforcement learning based on historical performance data to optimize action sequences.
- **Enhanced Dashboard:**  
  - Upgrade the UI for deeper analytics and improved usability.
- **Scalability Improvements:**  
  - Refine microservices architecture for sustained, long-duration operations.
- **Modular LLM Integration:**  
  - Continue refining the modular interface to easily switch between or combine different LLM providers for specialized tasks.

---

## 11. Conclusion

This comprehensive requirements document outlines a detailed, cost-effective, and modular approach to building Zigral’s MVP—initially focusing on Lincoln (LinkedIn Agent) and Shaun (Google Sheets Agent). The architecture supports future production deployment in a virtual desktop or headless environment. With detailed methodologies for risk management, security, CI/CD, testing, human-in-the-loop feedback, and modular LLM integration, along with a clear commit strategy and agile project management schedule, Zigral is positioned to meet its functional and business objectives by the MVP launch target of February 15, 2025.

---

