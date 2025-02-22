# VM Connection Guide

## VM Details
- **Instance Name**: zigral-chrome-embed
- **Zone**: us-south1-c
- **External IP**: 34.174.193.245
- **Internal IP**: 10.206.0.2
- **Machine Type**: e2-standard-2

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