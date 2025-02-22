# VM Connection Guide

## VM Details
- **Instance Name**: zigral-chrome-embed
- **Zone**: us-south1-c
- **External IP**: 34.174.193.245
- **Internal IP**: 10.206.0.2
- **Machine Type**: e2-standard-2
- **Path To Our Project**: /home/wilson.austin10/zigral-chrome-embed and /home/wilson_austin10/zigral-vnc

## Deployment Log

### February 22, 2025
1. Virtual Environment Setup
   - Created Python virtual environment in `/home/wilson_austin10/zigral-vnc/.venv`
   - Installed dependencies from `requirements.txt` and `requirements-vnc.txt`
   - Configured `start_uvicorn.sh` for automated service startup

2. Service Configuration
   - Orchestrator running on port 8000
   - Context Manager running on port 8001
   - Services configured to run with host 0.0.0.0 for external access

3. Firewall Rules
   - Added network tag 'zigral-chrome-embed' to VM instance
   - Created firewall rule 'zigral-uvicorn' allowing TCP ports 8000,8001
   - Source ranges: 0.0.0.0/0 (allowing external access)

4. Service Status
   - Both services running via start_uvicorn.sh
   - OpenAPI documentation accessible at http://34.174.193.245:8000/openapi.json
   - Health endpoints configured at /health for both services

### Service Management
```bash
# Start services
cd /home/wilson_austin10/zigral-vnc && ./start_uvicorn.sh

# Check service status
curl http://localhost:8000/health
curl http://localhost:8001/health

# View logs
tail -f /tmp/orchestrator.log
tail -f /tmp/context_manager.log
```

## Connection Methods

### 1. Using gcloud CLI (Recommended)
```bash
# Connect to VM
gcloud compute ssh zigral-chrome-embed --zone=us-south1-c

# If you need to specify a user
gcloud compute ssh wilson.austin10@zigral-chrome-embed --zone=us-south1-c
```

### 2. Direct SSH
```bash
ssh wilson.austin10@34.174.193.245
```

## SSH Key Setup

### Automatic Setup (via gcloud)
The gcloud CLI will automatically:
1. Generate SSH keys if they don't exist
2. Store them in `~/.ssh/google_compute_engine` (private) and `~/.ssh/google_compute_engine.pub` (public)
3. Upload the public key to the VM's metadata

### Manual Key Verification
- **Private Key Location**: `~/.ssh/google_compute_engine`
- **Public Key Location**: `~/.ssh/google_compute_engine.pub`
- **Project SSH Keys**: Can be viewed in Google Cloud Console under:
  - Compute Engine > Metadata > SSH Keys

## Troubleshooting

### Common Issues
1. **"Could not fetch resource" Error**
   - Verify the correct zone (us-south1-c)
   - Check instance name spelling (zigral-chrome-embed)

2. **Permission Denied**
   - Ensure gcloud is authenticated: `gcloud auth login`
   - Verify you have the correct IAM permissions

3. **SSH Keys Issues**
   ```bash
   # Regenerate SSH keys
   rm ~/.ssh/google_compute_engine*
   gcloud compute ssh zigral-chrome-embed --zone=us-south1-c
   ```

### Verifying Connection
```bash
# Test connection
gcloud compute ssh zigral-chrome-embed --zone=us-south1-c --command="echo 'Connection successful'"
```

## Security Notes
- Keep private SSH keys secure and never share them
- Use gcloud's built-in key management when possible
- Regularly rotate SSH keys for security
- Use IAM roles and service accounts for additional security layers

## Additional Resources
- [Google Cloud SSH Documentation](https://cloud.google.com/compute/docs/connect/ssh)
- [Managing Instance Access](https://cloud.google.com/compute/docs/instances/managing-instance-access)
- [Troubleshooting SSH](https://cloud.google.com/compute/docs/troubleshooting/troubleshooting-ssh) 