#!/bin/bash

PROJECT_ROOT=/home/wilson_austin10/zigral-vnc
cd $PROJECT_ROOT || exit 1

source .venv/bin/activate || exit 1

export PYTHONPATH=$PROJECT_ROOT/src:$PYTHONPATH
mkdir -p logs

cd src || exit 1

# Kill any existing services
pkill -f "uvicorn.*:8000" || true
pkill -f "uvicorn.*:8001" || true
pkill -f "uvicorn.*:8080" || true

# Start services
nohup uvicorn orchestrator.orchestrator:app --host 0.0.0.0 --port 8000 > ../logs/orchestrator.log 2>&1 &
nohup uvicorn context_manager.main:app --host 0.0.0.0 --port 8001 > ../logs/context_manager.log 2>&1 &
nohup uvicorn agents.vnc.main:app --host 0.0.0.0 --port 8080 > ../logs/vnc_agent.log 2>&1 &

echo "Services started. Check logs directory for output."
