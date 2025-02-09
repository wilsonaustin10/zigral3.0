import os
import pytest
import docker
import requests
import yaml
from pathlib import Path
import sys
import time
import urllib3
import base64

# Disable SSL verification warnings since we're using self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize Docker client with error handling
try:
    docker_client = docker.from_env()
    DOCKER_AVAILABLE = True
except docker.errors.DockerException:
    DOCKER_AVAILABLE = False
    docker_client = None

def test_docker_compose_vdi_file_exists():
    """Test that docker-compose.vdi.yml exists and is valid YAML."""
    compose_file = Path("docker-compose.vdi.yml")
    assert compose_file.exists(), "docker-compose.vdi.yml file not found"
    
    # Try to parse the YAML
    with open(compose_file) as f:
        try:
            yaml_content = yaml.safe_load(f)
            assert isinstance(yaml_content, dict), "Invalid YAML structure"
            assert "services" in yaml_content, "No services defined in docker-compose file"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML format: {str(e)}")

def test_dockerfile_vdi_exists():
    """Test that Dockerfile.vdi exists and contains required components."""
    dockerfile = Path("Dockerfile.vdi")
    assert dockerfile.exists(), "Dockerfile.vdi not found"
    
    with open(dockerfile) as f:
        content = f.read()
        # Check for required components
        assert "FROM kasmweb/desktop:1.14.0" in content, "Base image not correctly specified"
        assert "python3.12" in content, "Python 3.12 not specified in dependencies"
        assert "WORKDIR /app" in content, "Working directory not set"
        assert "VOLUME /workspace" in content, "Workspace volume not defined"

def test_required_ports_in_compose():
    """Test that required ports are exposed in docker-compose.vdi.yml."""
    with open("docker-compose.vdi.yml") as f:
        compose = yaml.safe_load(f)
        kasm_service = compose["services"]["kasm"]
        
        # Check Kasm port mapping
        ports = kasm_service.get("ports", [])
        assert any("6901:6901" in port for port in ports), "Kasm web interface port (6901) not properly mapped"

def test_required_environment_variables():
    """Test that required environment variables are defined."""
    with open("docker-compose.vdi.yml") as f:
        compose = yaml.safe_load(f)
        kasm_service = compose["services"]["kasm"]
        env = kasm_service.get("environment", [])
        
        # Convert list of env vars to dict if necessary
        if isinstance(env, list):
            env = dict(var.split("=") for var in env if "=" in var)
        
        assert "VNC_PW" in env, "VNC password not set"
        assert "KASM_USER" in env, "Kasm user not set"

@pytest.mark.skipif(not DOCKER_AVAILABLE, reason="Docker is not available")
@pytest.mark.integration
def test_kasm_container_starts():
    """Test that Kasm container can start successfully."""
    container = None
    try:
        print("\nStarting Kasm container...")
        
        # Define credentials
        username = 'kasm_user'
        password = 'password123'
        
        # Start the container with explicit port mapping
        container = docker_client.containers.run(
            "kasmweb/desktop:1.14.0",
            detach=True,
            ports={'6901/tcp': 6901},  # Explicitly map to port 6901
            environment={
                'VNC_PW': password,
                'VNC_UN': username,
                'KASM_VNC_UN': username,
                'KASM_VNC_PW': password
            }
        )
        
        print("Container created, waiting for it to start...")
        
        # Wait for container to be ready
        max_wait = 30  # Maximum wait time in seconds
        start_time = time.time()
        ready = False
        last_error = None
        
        # Create basic auth header
        auth_header = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers = {
            'Authorization': f'Basic {auth_header}'
        }
        
        while time.time() - start_time < max_wait:
            try:
                # Reload container info
                container.reload()
                
                # Check container state
                state = container.attrs['State']
                status = state['Status']
                print(f"\nContainer status: {status}")
                
                if status != 'running':
                    print("Container not yet running, waiting...")
                    time.sleep(1)
                    continue
                
                # Try to connect to the web interface
                print("Attempting to connect to web interface...")
                response = requests.get(
                    'https://localhost:6901',
                    verify=False,
                    timeout=5,
                    headers=headers
                )
                
                print(f"Response status: {response.status_code}")
                if response.status_code in [200, 301, 302]:
                    ready = True
                    print("Successfully connected to Kasm web interface")
                    break
                else:
                    print(f"Received status code {response.status_code}")
                    print("Response headers:", response.headers)
                    
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                print(f"Connection attempt failed: {last_error}")
                
                # Print container logs
                print("\nContainer logs:")
                print(container.logs().decode('utf-8'))
                
                time.sleep(1)
                
        if not ready:
            logs = container.logs().decode('utf-8')
            raise AssertionError(
                f"Container did not become ready within {max_wait} seconds.\n"
                f"Last error: {last_error}\n"
                f"Container logs:\n{logs}"
            )
            
        # Final assertions
        assert container.status == "running", "Container should be running"
        response = requests.get(
            "https://localhost:6901",
            verify=False,
            headers=headers
        )
        assert response.status_code in [200, 301, 302], "Kasm web interface not responding"
        
    finally:
        if container:
            try:
                print("\nCleaning up container...")
                container.stop()
                container.remove()
            except Exception as e:
                print(f"Error during cleanup: {e}")

@pytest.mark.integration
def test_orchestrator_integration():
    """Test that orchestrator can connect to Kasm container."""
    with open("docker-compose.vdi.yml") as f:
        compose = yaml.safe_load(f)
        
        # Verify orchestrator service configuration
        orchestrator = compose["services"]["orchestrator"]
        assert "kasm" in orchestrator.get("depends_on", []), "Orchestrator should depend on kasm service"
        assert "VIRTUAL_DESKTOP_MODE" in str(orchestrator.get("environment", [])), "VIRTUAL_DESKTOP_MODE not set for orchestrator"

def test_resource_limits():
    """Test that resource limits are properly configured."""
    with open("docker-compose.vdi.yml") as f:
        compose = yaml.safe_load(f)
        kasm_service = compose["services"]["kasm"]
        
        # Check resource limits
        deploy = kasm_service.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})
        
        assert "cpus" in limits, "CPU limits not set"
        assert "memory" in limits, "Memory limits not set"
        assert limits["cpus"] == "2", "Incorrect CPU limit"
        assert limits["memory"] == "4G", "Incorrect memory limit" 