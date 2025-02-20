"""Integration tests for noVNC setup."""

import os
import pytest
import docker
import requests
import yaml
from pathlib import Path
import sys
import time
import urllib3

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_docker_compose_file_exists():
    """Test that docker-compose.vnc.yml exists and is valid YAML."""
    compose_file = Path("docker-compose.vnc.yml")
    assert compose_file.exists(), "docker-compose.vnc.yml file not found"
    
    # Try to parse the YAML
    with open(compose_file) as f:
        try:
            yaml_content = yaml.safe_load(f)
            assert isinstance(yaml_content, dict), "Invalid YAML structure"
            assert "services" in yaml_content, "No services defined in docker-compose file"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML format: {str(e)}")

def test_dockerfile_exists():
    """Test that Dockerfile.vnc exists and contains required components."""
    dockerfile = Path("Dockerfile.vnc")
    assert dockerfile.exists(), "Dockerfile.vnc not found"
    
    with open(dockerfile) as f:
        content = f.read()
        # Check for required components
        assert "FROM ubuntu:20.04" in content, "Base image not correctly specified"
        assert "novnc" in content, "noVNC not installed"
        assert "chromium-browser" in content, "Chrome browser not installed"

def test_required_ports_in_compose():
    """Test that required ports are exposed in docker-compose.vnc.yml."""
    with open("docker-compose.vnc.yml") as f:
        compose = yaml.safe_load(f)
        vnc_service = compose["services"]["vnc"]
        
        # Check VNC port mapping
        ports = vnc_service.get("ports", [])
        assert any("6080:6080" in port for port in ports), "VNC web interface port (6080) not properly mapped"

def test_required_environment_variables():
    """Test that required environment variables are defined."""
    with open("docker-compose.vnc.yml") as f:
        compose = yaml.safe_load(f)
        vnc_service = compose["services"]["vnc"]
        env = vnc_service.get("environment", [])
        
        # Convert list of env vars to dict if necessary
        if isinstance(env, list):
            env = dict(var.split("=") for var in env if "=" in var)
        
        assert "DISPLAY=:0" in env, "Display not set"
        assert "RESOLUTION=1920x1080x24" in env, "Resolution not set"

@pytest.mark.integration
def test_vnc_endpoint():
    """Test that noVNC endpoint is accessible."""
    try:
        # Try to connect to the web interface
        print("Attempting to connect to noVNC web interface...")
        response = requests.get("http://34.174.193.245:6080/vnc.html")
        
        print(f"Response status: {response.status_code}")
        assert response.status_code == 200, "VNC web interface not responding"
        print("Successfully connected to VNC web interface")
            
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to connect to VNC: {str(e)}")

@pytest.mark.integration
def test_orchestrator_vnc_integration():
    """Test that orchestrator can connect to VNC service."""
    with open("docker-compose.vnc.yml") as f:
        compose = yaml.safe_load(f)
        
        # Verify orchestrator service configuration
        orchestrator = compose["services"]["orchestrator"]
        assert "vnc" in orchestrator.get("depends_on", []), "Orchestrator should depend on VNC service"
        
        # Check VNC service configuration
        vnc_service = compose["services"]["vnc"]
        
        # Check resource limits
        deploy = vnc_service.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})
        
        assert "cpus" in limits, "CPU limits not set"
        assert "memory" in limits, "Memory limits not set" 