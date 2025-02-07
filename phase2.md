# Phase 2: Building and Integrating Individual Agents

Below is a detailed plan for Phase 2 along with an "order of file creation" breakdown. In Phase 2 you will build and integrate the two key agents—Lincoln (the LinkedIn Agent) and Shaun (the Google Sheets Agent)—and set up their communication with the orchestrator. Running the application in a development environment is highly recommended throughout this phase so you can interactively test functionality and catch integration issues early.

## Progress Update

### Completed Tasks
- ✅ Set up agent directories and basic file structure
- ✅ Created Lincoln agent files and implemented core functionality
- ✅ Created Shaun agent files and implemented core functionality
- ✅ Implemented Google Sheets client with proper error handling
- ✅ Added comprehensive test suite for Shaun agent
- ✅ Set up mock credentials for testing
- ✅ Achieved 77% test coverage for Shaun's core functionality
- ✅ Implemented basic functionality in Shaun (connect, add/update prospects, error handling)
- ✅ Set up RabbitMQ dependency and configuration
- ✅ Implemented RabbitMQ message handlers for both agents
- ✅ Set up message queues for agent communication
- ✅ Added integration tests for RabbitMQ functionality
- ✅ Implemented Lincoln's RabbitMQ integration with 66% test coverage

### In Progress
- Integrating with orchestrator
- Testing full workflow with both agents

### Next Steps
1. Set up orchestrator hooks for agent commands
2. Add integration tests for full workflow
3. Test end-to-end communication between agents

---

## Phase 2 Plan: Building and Integrating Individual Agents

### Objectives
- **Implement Lincoln:**  
  Develop the LinkedIn Agent using Playwright to automate LinkedIn tasks (login, search, and data capture). Ensure it captures the GUI state (screenshots/HTML) ✅ and sends data (e.g., prospect information) to the next stage.
  
- **Implement Shaun:**  
  Develop the Google Sheets Agent using gspread to update a prospect list. Shaun should receive data (from Lincoln) and update the target spreadsheet accordingly.
  
- **Inter-Agent Communication:**  
  Integrate communication channels using RabbitMQ so that agents can receive commands and report status.  
- **Error Handling & Fallbacks:**  
  Ensure that each agent handles errors (e.g., unexpected UI changes, API issues) gracefully and reports errors back to the orchestrator, possibly triggering fallback guidance via the LLM.
  
- **Local Development Testing:**  
  Begin running the application in your dev environment as soon as new agent functionality is added. This hands-on testing is critical for catching integration issues early.

---

### Detailed Steps and Descriptions

#### Step 1: Set Up Agent Directories and Basic File Structure

1. **Create a New Directory for Agents:**  
   - Inside your `src/` directory, create a new folder called `agents/`.

2. **Create Subdirectories for Each Agent:**  
   - Inside `src/agents/`, create two directories:  
     - `lincoln/` for the LinkedIn Agent  
     - `shaun/` for the Google Sheets Agent

#### Step 2: Build the Lincoln (LinkedIn Agent)

3. **Create Files for Lincoln:** ✅
   - **`src/agents/lincoln/__init__.py`:** ✅
     An empty file to mark the package.
     
   - **`src/agents/lincoln/main.py`:** ✅
     This will be the entry point for the Lincoln agent. It should initialize the agent, set up its API endpoints (if it exposes any for inter-service communication), and start the event loop.
     
   - **`src/agents/lincoln/linkedin_client.py`:** ✅
     Implement the core Playwright-based functions for logging into LinkedIn, performing a search, and capturing data.  
     - *Example functions:* `login()` ✅, `search_sales_navigator()` ✅, and `capture_gui_state()` ✅
     
   - **`src/agents/lincoln/utils.py`:** ✅
     Helper functions that format or process data (e.g., converting HTML snapshots into structured data).

4. **Implement Basic Functionality in Lincoln:** ✅
   - Write a basic script in `linkedin_client.py` that simulates a login and search sequence ✅
   - Ensure that you include error handling (e.g., catching exceptions if elements are not found) and logging so that errors are reported back to the orchestrator ✅
   - Use test stubs to simulate data capture if the live API is not available ✅
   - Implement actual Sales Navigator search functionality ✅
   - Implement GUI state capture ✅
   - Implement profile data collection ✅

#### Step 3: Build the Shaun (Google Sheets Agent)

5. **Create Files for Shaun:**
   - **`src/agents/shaun/__init__.py`:** ✅
     An empty file to mark the package.
     
   - **`src/agents/shaun/main.py`:** ✅
     The entry point for the Shaun agent. This file will initialize the agent and expose any endpoints or functions required for updating spreadsheets.
     
   - **`src/agents/shaun/sheets_client.py`:** ✅
     Implement integration with Google Sheets using gspread.  
     - *Example functions:* `connect_to_sheet()`, `update_prospect_list(data)`.
     
   - **`src/agents/shaun/utils.py`:** ✅
     Helper functions for processing and formatting the prospect data before updating the spreadsheet.

6. **Implement Basic Functionality in Shaun:** ✅
   - Write the functions in `sheets_client.py` to connect to a Google Sheet, insert new rows, and update existing entries.
   - Add proper error handling to catch and log issues (e.g., if the sheet cannot be accessed).

#### Step 4: Integrate Inter-Agent Communication

7. **Set Up RabbitMQ Integration:**
   - In Phase 2, configure each agent to communicate with the orchestrator via RabbitMQ.
   - This may involve adding minimal code in both Lincoln and Shaun that subscribes to a messaging queue and publishes updates.
   - If you already have a common messaging helper library from Phase 1 (or a shared module), integrate it here.
  
8. **Update Orchestrator if Needed:**
   - Ensure that the orchestrator can dispatch commands to these new agents. If required, add new endpoints or messaging logic in your existing orchestrator code to accommodate agent responses.

#### Step 5: Testing and Local Development

9. **Local Testing:**
   - Run the application locally in development mode to ensure that the new agent functionality integrates correctly with the orchestrator and context manager.
   - Use your existing test framework to add new tests for Lincoln and Shaun.
   - Verify that:
     - Lincoln can log in, perform searches, and capture data (simulate with mocks if needed).
     - Shaun can connect to Google Sheets and update prospect lists.
     - Inter-agent messaging (via RabbitMQ) is functioning as expected.
     
10. **Add Tests:**
    - Create new test files (if necessary) for the agents under `tests/agents/lincoln/` and `tests/agents/shaun/`.
    - Write tests for happy paths and error conditions (e.g., login failure, inability to update a sheet).

---

## Order of File Creation (Phase 2)

1. **Create Directory Structure:**
   - `src/agents/`
   - `src/agents/lincoln/`
   - `src/agents/shaun/`
   - Optionally, create a `tests/agents/` directory with subdirectories for each agent.

2. **For Lincoln:**
   - Create `src/agents/lincoln/__init__.py`
   - Create `src/agents/lincoln/main.py`
   - Create `src/agents/lincoln/linkedin_client.py`
   - Create `src/agents/lincoln/utils.py`

3. **For Shaun:**
   - Create `src/agents/shaun/__init__.py`
   - Create `src/agents/shaun/main.py`
   - Create `src/agents/shaun/sheets_client.py`
   - Create `src/agents/shaun/utils.py`

4. **Integration Files:**
   - If needed, create or update common messaging helper files in a shared location (for example, `src/common/messaging.py`).
   - Update orchestrator files (if required) in `src/orchestrator/` to add hooks for dispatching commands to the new agents.

5. **Testing Files:**
   - Create `tests/agents/lincoln/test_lincoln.py`
   - Create `tests/agents/shaun/test_shaun.py`
   - Update existing tests (if necessary) in `tests/test_orchestrator.py` to include integration with the new agents.

### Running the Application in Development

Running the application in your development environment is crucial to:

- Validate that each new agent works correctly.
- Test the communication between the orchestrator and the agents.
- Catch integration issues early (e.g., environment variable misconfiguration, messaging errors).
- Monitor logs and performance as you simulate real-world scenarios.

You can start by running each microservice individually (using commands like uvicorn src/agents/lincoln/main.py --port 8002 and similar for Shaun) and then test the overall integration by running the orchestrator and sending commands through the UI or via API tools like Postman.

## Summary

Phase 2 focuses on building the individual agents (Lincoln and Shaun) and integrating them into the existing framework. Follow the detailed steps and order-of-file creation to maintain structure and clarity. Running the application in development throughout this phase is highly recommended to ensure that each component functions as expected and to catch issues early. 