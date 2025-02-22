#!/bin/bash
set -e

# Change directory to the project folder on the VM
cd /home/wilson_austin10/zigral-vnc

# Check if the virtual environment exists; if not, create it and install dependencies
if [ ! -d ".venv" ]; then
    echo ".venv not found, creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
    pip install -r requirements-vnc.txt
else
    echo ".venv exists, activating..."
    source .venv/bin/activate
fi

# Start uvicorn servers without the --reload flag for production stability
cd src
export PYTHONPATH=$(pwd)
nohup /home/wilson_austin10/zigral-vnc/.venv/bin/uvicorn orchestrator.orchestrator:app --host 0.0.0.0 --port 8000 > /tmp/orchestrator.log 2>&1 &
nohup /home/wilson_austin10/zigral-vnc/.venv/bin/uvicorn context_manager.main:app --host 0.0.0.0 --port 8001 > /tmp/context_manager.log 2>&1 &

echo "Uvicorn servers started." 