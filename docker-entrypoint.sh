#!/bin/bash
set -e

# Function to start the orchestrator service
start_orchestrator() {
    echo "Starting Orchestrator service..."
    exec python -m src.main
}

# Function to start the context manager service
start_context_manager() {
    echo "Starting Context Manager service..."
    exec uvicorn src.context_manager.main:app --host 0.0.0.0 --port 8001
}

# Check which service to start based on the SERVICE_NAME environment variable
case "${SERVICE_NAME}" in
    "orchestrator")
        start_orchestrator
        ;;
    "context-manager")
        start_context_manager
        ;;
    *)
        echo "Error: SERVICE_NAME must be either 'orchestrator' or 'context-manager'"
        exit 1
        ;;
esac 