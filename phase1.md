Below is the Phase 1 plan that now incorporates setting up the basic Model Context Protocol (i.e. the Context Manager microservice) along with the rest of the initial project setup and Orchestrator Prototype work.

---

## Phase 1: Project Setup, Orchestrator Prototype, & Basic Model Context Protocol

### 1. Define Requirements & MVP Scope
- **Scope:** Focus on developing the core Orchestrator and two MVP agents (Lincoln and Shaun) plus a basic Context Manager.
- **Objective:** The Orchestrator receives user commands (with optional manual context), sends them (and any available context) to the LLM to produce a JSON action sequence, and routes commands to the agents.  
- **Context Manager Purpose:** To store and retrieve job-specific context (e.g., search parameters, GUI states, and initial user feedback) that will enrich LLM prompts. This module is built as a dedicated microservice.

---

### 2. Environment Setup
- **Version Control:**  
  - Create the project root folder (e.g., `zigral/`), initialize Git, and set up a `.gitignore` for files like virtual environments, logs, and `.env`.
- **Virtual Environment & Dependencies:**  
  - Create a dedicated Python virtual environment.
  - Install core dependencies using `requirements.txt` (include FastAPI, Playwright, Asyncio, OpenAI API, and later database drivers for PostgreSQL, etc.).
- **Basic Files:**  
  - Create initial files such as `README.md`, `.env`, and `requirements.txt`.

---

### 3. Create the Project Structure and File Setup

#### **Directory Structure Example:**

```
zigral/
├── .gitignore
├── .env
├── README.md
├── requirements.txt
├── Dockerfile               # (for containerizing later)
├── docker-compose.yml       # (optional, for multi-container setup)
├── src/
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── orchestrator.py       # Core orchestrator logic
│   │   ├── llm_integration.py    # Wrapper for LLM API calls
│   │   ├── logger.py             # Structured logging functionality
│   │   └── checkpoint.py         # Checkpoint and fallback functions
│   ├── context_manager/          # New module for Model Context Protocol
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI entry point for the Context Manager
│   │   ├── models.py             # Pydantic models for context data
│   │   ├── database.py           # Database connection with Tortoise ORM
│   │   ├── crud.py               # CRUD operations for context entries
│   │   └── config.py             # Configuration settings (e.g., DB URI)
│   └── main.py                   # Main entry point for launching the Orchestrator API
└── tests/
    ├── __init__.py
    ├── test_orchestrator.py
    ├── test_llm_integration.py
    ├── test_logger.py
    ├── test_checkpoint.py
    └── test_context_manager.py   # Tests for context manager endpoints
```

---

### 4. Implement the Core Modules

#### **4.1 Orchestrator Module (src/orchestrator/)**
- **orchestrator.py:**  
  - Set up a basic FastAPI application.
  - Create endpoints (e.g., `/command`) to receive user commands.
  - Stub functionality to call `llm_integration.py` and return a dummy JSON action sequence.
- **llm_integration.py:**  
  - Implement a function (e.g., `generate_action_sequence(command, context)`) that initially returns a fixed JSON structure.
- **logger.py & checkpoint.py:**  
  - Implement basic logging functions and checkpoint logic to capture system state and errors.

#### **4.2 Context Manager Module (src/context_manager/)**
- **main.py:**  
  - Create a FastAPI application exposing RESTful endpoints for context management.
- **models.py:**  
  - Define Pydantic models for context data, for example:
    ```python
    from pydantic import BaseModel
    from typing import Optional, Dict

    class ContextEntry(BaseModel):
        job_id: str
        job_type: str
        context_data: Dict  # Contains search parameters, GUI snapshots, etc.
        timestamp: Optional[str]
    ```
- **database.py:**  
  - Set up the database connection using Tortoise ORM with PostgreSQL.
- **crud.py:**  
  - Write functions to create, read, update, and delete context entries.
- **config.py:**  
  - Centralize configuration (e.g., database URI, secret keys).
- **Testing:**  
  - In `tests/test_context_manager.py`, write tests for each endpoint (POST, GET, PUT, DELETE).

#### **4.3 Main Entry Point (src/main.py)**
- **Purpose:**  
  - Import the orchestrator and run the API server. This file serves as the entry point for development and testing.
  
---

### 5. Set Up Testing Infrastructure
- **Directory:** Create the `tests/` directory with relevant test files for each module.
- **Testing Tools:**  
  - Use pytest for unit tests.
  - Write unit tests for orchestrator functions, LLM integration, logger, checkpoint functionality, and Context Manager endpoints.
- **CI/CD Setup (Optional for Phase 1):**  
  - Create a GitHub Actions workflow file (e.g., `.github/workflows/ci.yml`) to run tests on every commit.

---

### 6. Version Control & Commit Strategy
- **Frequent Commits:**  
  - Commit each small, working unit (e.g., a new function with tests) to feature branches.
- **Milestone Merges:**  
  - Merge feature branches into main after integration testing and peer review (using ChatGPT for code reviews, if desired).
- **Commit Documentation:**  
  - Write descriptive commit messages to track changes.

---

### 7. Summary of Phase 1 Deliverables
- **Core Files & Modules:**
  - `.gitignore`, `.env`, `README.md`, `requirements.txt`
  - Orchestrator module (`orchestrator.py`, `llm_integration.py`, `logger.py`, `checkpoint.py`)
  - Basic Context Manager microservice (`main.py`, `models.py`, `database.py`, `crud.py`, `config.py`)
  - Entry point (`src/main.py`)
  - Test suite files (`tests/test_*`)
- **Key Objectives:**
  - A basic orchestrator that receives user commands and generates dummy JSON action sequences.
  - A Context Manager microservice with RESTful endpoints for storing and retrieving context.
  - A file structure that supports further development and containerization.
  - Automated tests for the orchestrator and context modules.
- **Deployment:**  
  - The initial prototype is designed for local development; future steps will containerize and deploy on a virtual desktop/headless environment.

---

By following this updated Phase 1 plan, you'll set up a solid foundation that includes the essential Context Manager module. This allows Zigral to store and retrieve context, enriching the LLM prompts and enabling agents to learn from prior tasks—a critical step toward making Zigral smarter and more autonomous over time.


Below is a detailed, step-by-step "order of file creation" breakdown for Phase 1, based on the plan outlined above. This guide will help you create the files in a logical order so that you build the foundation for the Orchestrator, the basic Model Context Protocol (Context Manager), and the testing infrastructure. Follow these steps sequentially:

### Order of File Creation

### Step 1: Initialize the Project Root

1. **Create the Root Folder and Initialize Git:**
   - Create a directory called `zigral/`.
   - Inside `zigral/`, initialize Git:
     ```bash
     cd zigral
     git init
     ```
2. **Create Basic Configuration Files:**
   - **`.gitignore`:**  
     Create a file named `.gitignore` with content similar to:
     ```plaintext
     venv/
     __pycache__/
     *.pyc
     *.log
     .env
     ```
   - **`.env`:**  
     Create a file named `.env` for storing secrets (e.g., API keys). You can leave it empty for now but plan to add your environment variables later.
   - **`README.md`:**  
     Create a `README.md` file with a brief project overview.
   - **`requirements.txt`:**  
     Create a `requirements.txt` file listing your initial dependencies (e.g., FastAPI or Flask, Playwright, Asyncio, OpenAI, SQLAlchemy or Tortoise ORM, pytest).

---

### Step 2: Set Up the Base Directory Structure

3. **Create the `src/` Directory:**
   - Inside `zigral/`, create a directory named `src/`.

4. **Create Subdirectories for Orchestrator and Context Manager:**
   - Inside `src/`, create two directories:
     - `orchestrator/`
     - `context_manager/`
     
5. **Create the `tests/` Directory:**
   - At the same level as `src/`, create a directory named `tests/`.

---

### Step 3: Build the Orchestrator Module

6. **Inside `src/orchestrator/`:**
   - **`__init__.py`:**  
     Create an empty file named `__init__.py` to mark this directory as a Python package.
   - **`orchestrator.py`:**  
     Create `orchestrator.py`. Start by setting up a basic FastAPI app with an endpoint (e.g., `/command`) that accepts a user command and returns a dummy JSON action sequence.
   - **`llm_integration.py`:**  
     Create `llm_integration.py` with a stub function:
     ```python
     def generate_action_sequence(command, context):
         # For now, return a fixed JSON structure as a dummy response
         return {
             "objective": command,
             "steps": [
                 {"agent": "LinkedIn", "action": "navigate", "target": "LinkedIn Sales Navigator"},
                 {"agent": "LinkedIn", "action": "search", "criteria": {"title": "CTO", "location": "User Territory"}},
                 {"agent": "LinkedIn", "action": "collect", "fields": ["name", "company", "contact_info"]},
                 {"agent": "GoogleSheets", "action": "update", "target": "prospect_list"}
             ]
         }
     ```
   - **`logger.py`:**  
     Create `logger.py` to set up a basic logging function (use Python's built-in logging module for now).
   - **`checkpoint.py`:**  
     Create `checkpoint.py` with stub functions to create and validate checkpoints. For example:
     ```python
     def create_checkpoint(state):
         # Save the current state to a log or file (stub)
         pass

     def validate_checkpoint(state):
         # Validate state; return True if successful, otherwise False (stub)
         return True
     ```

7. **Create Main Entry for Orchestrator:**
   - **`src/main.py`:**  
     Create `main.py` to serve as the entry point that imports and runs your orchestrator app:
     ```python
     from orchestrator.orchestrator import app  # if using FastAPI, for example

     if __name__ == "__main__":
         import uvicorn
         uvicorn.run(app, host="0.0.0.0", port=8000)
     ```

---

### Step 4: Build the Context Manager Module

8. **Inside `src/context_manager/`:**
   - **`__init__.py`:**  
     Create an empty `__init__.py`.
   - **`main.py`:**  
     Create `main.py` to set up a basic FastAPI application for the Context Manager:
     ```python
     from fastapi import FastAPI
     from . import crud, models, config

     app = FastAPI()

     @app.post("/context")
     async def create_context(context_entry: models.ContextEntry):
         return await crud.create_context(context_entry)

     @app.get("/context/{job_id}")
     async def read_context(job_id: str):
         return await crud.get_context(job_id)
     ```
   - **`models.py`:**  
     Create `models.py` with both Pydantic and Tortoise models:
     ```python
     from pydantic import BaseModel
     from typing import Optional, Dict
     from tortoise import fields, models

     # Pydantic model for API
     class ContextEntry(BaseModel):
         job_id: str
         job_type: str
         context_data: Dict
         timestamp: Optional[str] = None

     # Tortoise ORM model
     class ContextEntryDB(models.Model):
         id = fields.IntField(pk=True)
         job_id = fields.CharField(max_length=255)
         job_type = fields.CharField(max_length=255)
         context_data = fields.JSONField()
         timestamp = fields.DatetimeField(auto_now_add=True)

         class Meta:
             table = "context_entries"
     ```
   - **`database.py`:**  
     Create `database.py` to establish a connection to PostgreSQL using Tortoise ORM:
     ```python
     from tortoise import Tortoise

     async def init_db():
         await Tortoise.init(
             db_url=os.getenv("DATABASE_URL", "postgres://user:password@localhost/zigral"),
             modules={'models': ['context_manager.models']}
         )
         # Generate the schema
         await Tortoise.generate_schemas()
     ```
   - **`crud.py`:**  
     Create `crud.py` with basic CRUD operations for context entries:
     ```python
     from . import models
     from typing import Optional

     async def create_context(context_entry: models.ContextEntry):
         db_context = await models.ContextEntryDB.create(**context_entry.dict())
         return db_context

     async def get_context(job_id: str) -> Optional[models.ContextEntryDB]:
         return await models.ContextEntryDB.filter(job_id=job_id).first()
     ```
   - **`config.py`:**  
     Create `config.py` to store configuration settings (e.g., database URI, secret keys).

9. **Set Up Testing for Context Manager:**
   - **`tests/test_context_manager.py`:**  
     Create tests for the Context Manager endpoints using pytest and FastAPI's TestClient.

---

### Step 5: Build the Testing Infrastructure

10. **Inside the `tests/` Directory:**
    - **`__init__.py`:**  
      Create an empty `__init__.py` to mark the directory as a package.
    - **Other Test Files:**  
      Create the following files with basic test stubs:
      - `test_orchestrator.py` – Test endpoints and functionality in `orchestrator.py`.
      - `test_llm_integration.py` – Test the dummy LLM integration function.
      - `test_logger.py` – Test logging outputs.
      - `test_checkpoint.py` – Test checkpoint creation/validation functions.
      - `test_context_manager.py` – Test the CRUD operations and endpoints in the Context Manager.

---

### Step 6: (Optional) Set Up Containerization and CI/CD

11. **Create a Dockerfile in the Root Directory (Optional for Phase 1):**
    - Write a simple Dockerfile to containerize the orchestrator:
      ```dockerfile
      FROM python:3.9-slim
      WORKDIR /app
      COPY requirements.txt .
      RUN pip install --no-cache-dir -r requirements.txt
      COPY src/ /app/src/
      CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
      ```
12. **Create a `docker-compose.yml` (Optional):**
    - If you wish to run multiple containers (e.g., orchestrator and context manager) simultaneously.
13. **Set Up a CI/CD Workflow:**
    - Create a file such as `.github/workflows/ci.yml` for GitHub Actions to run tests automatically on each commit.

---

### Summary of Order of File Creation

1. **Project Initialization:**  
   - Create `zigral/` folder, `.gitignore`, `.env`, `README.md`, `requirements.txt`.
2. **Directory Structure:**  
   - Create `src/` and `tests/` directories; inside `src/`, create `orchestrator/` and `context_manager/`.
3. **Orchestrator Module:**  
   - In `src/orchestrator/`: Create `__init__.py`, `orchestrator.py`, `llm_integration.py`, `logger.py`, `checkpoint.py`.
4. **Main Entry Point:**  
   - Create `src/main.py`.
5. **Context Manager Module:**  
   - In `src/context_manager/`: Create `__init__.py`, `main.py`, `models.py`, `database.py`, `crud.py`, `config.py`.
6. **Testing Infrastructure:**  
   - In `tests/`: Create `__init__.py` and test files for each module (`test_orchestrator.py`, `test_llm_integration.py`, `test_logger.py`, `test_checkpoint.py`, `test_context_manager.py`).
7. **Optional Containerization and CI/CD Files:**  
   - Create `Dockerfile`, `docker-compose.yml`, and CI/CD workflow file.

---

Following this order will help you methodically build out the essential components for Phase 1, ensuring a solid foundation that includes the basic model context protocol. This structure is designed to be incrementally extended in later phases.


