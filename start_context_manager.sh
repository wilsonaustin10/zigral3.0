#!/bin/bash

# Set the project root directory
PROJECT_ROOT="/home/wilson_austin10/zigral-vnc"

# Navigate to project directory
cd "$PROJECT_ROOT" || exit 1

# Activate virtual environment
source .venv/bin/activate || exit 1

# Load environment variables from .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found"
    exit 1
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the context manager service
cd src || exit 1
exec uvicorn context_manager.main:app --host 0.0.0.0 --port 8001 --reload --log-level debug 2>&1 | tee ../logs/context_manager.log 