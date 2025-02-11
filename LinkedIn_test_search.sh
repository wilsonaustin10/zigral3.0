#!/bin/bash
# LinkedIn Test Search
# This script calls the orchestrator API to search LinkedIn for CTOs in San Francisco.

# Set the endpoint URL (using Docker container name)
endpoint="http://zigral30-orchestrator-1:8000/command"

# Define the JSON payload for the command
payload='{
  "command": "execute",
  "steps": [{
    "agent": "lincoln",
    "action": "search",
    "parameters": {
      "search_params": {
        "title": "CTO",
        "location": "San Francisco"
      }
    }
  }]
}'

# Send the POST request with curl
curl -X POST -H "Content-Type: application/json" -d "$payload" "$endpoint" 