# Local Development Environment Setup for Zigral

This document outlines how to set up a local development environment for the Zigral project that synchronizes with the VM.

## Overview

Zigral's core application is hosted on a Google Cloud VM (`zigral-chrome-embed`). For optimal development workflow, we maintain a local copy of the codebase that can be synchronized with the VM when needed. This approach offers several advantages:

- Better development tools and experience with your preferred IDE/editor
- Faster response time when editing files
- Integrated version control
- Ability to work offline
- Ability to use code search, navigation, and refactoring tools

## Initial Setup

### 1. Create Local Directory Structure

Create a `zigral-vnc` directory in your Zigral project folder:

```bash
cd ~/Zigral\ 3.0/
mkdir -p zigral-vnc
```

### 2. Copy Files from VM

Create a tar archive on the VM and download it:

```bash
# Create archive on VM (excluding large directories)
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c --command="cd /home/wilson_austin10 && tar -czf zigral-vnc-backup.tar.gz --exclude='*.venv*' --exclude='*node_modules*' zigral-vnc"

# Copy archive to local machine
gcloud compute scp wilson_austin10@zigral-chrome-embed:/home/wilson_austin10/zigral-vnc-backup.tar.gz ./zigral-vnc/ --zone=us-south1-c

# Extract archive
cd zigral-vnc && tar -xzf zigral-vnc-backup.tar.gz --strip-components=1 && rm zigral-vnc-backup.tar.gz
```

### 3. Sync Scripts Setup

Two scripts facilitate easy synchronization between local and VM environments:

- `scripts/sync-to-vm.sh`: Pushes local changes to the VM
- `scripts/sync-from-vm.sh`: Pulls changes from the VM to local environment

Make these scripts executable:

```bash
chmod +x ./scripts/sync-to-vm.sh ./scripts/sync-from-vm.sh
```

## Using the Sync Scripts

### Pushing Changes to VM

#### Sync a specific file:
```bash
cd ~/Zigral\ 3.0/zigral-vnc
./scripts/sync-to-vm.sh src/ui/index.html
```

#### Sync a directory:
```bash
cd ~/Zigral\ 3.0/zigral-vnc
./scripts/sync-to-vm.sh src/ui/
```

#### Sync the entire project:
```bash
cd ~/Zigral\ 3.0/zigral-vnc
./scripts/sync-to-vm.sh
```

### Pulling Changes from VM

#### Pull a specific file:
```bash
cd ~/Zigral\ 3.0/zigral-vnc
./scripts/sync-from-vm.sh src/ui/index.html
```

#### Pull a directory:
```bash
cd ~/Zigral\ 3.0/zigral-vnc
./scripts/sync-from-vm.sh src/ui/
```

#### Pull the entire project:
```bash
cd ~/Zigral\ 3.0/zigral-vnc
./scripts/sync-from-vm.sh
```

## SSH Tunnels for Testing

To test your changes, set up SSH tunnels to the VM:

### For noVNC (Browser Desktop):
```bash
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8901:localhost:6081 -N &
```
Access at: http://localhost:8901/vnc.html?autoconnect=true

### For UI Server (Vite):
```bash
gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8090:localhost:5173 -N &
```
Access at: http://localhost:8090

## Recommended Workflow

1. **Pull Latest Changes**: Start by pulling the latest changes from the VM
   ```bash
   ./scripts/sync-from-vm.sh
   ```

2. **Make Local Changes**: Edit files using your preferred IDE/editor

3. **Push Changes**: When ready to test, push your changes to the VM
   ```bash
   ./scripts/sync-to-vm.sh
   ```

4. **Set Up Tunnels**: Create SSH tunnels for testing
   ```bash
   gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8901:localhost:6081 -N &
   gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c -- -L 8090:localhost:5173 -N &
   ```

5. **Test Changes**: Access your applications through the tunnels
   - UI: http://localhost:8090
   - VNC: http://localhost:8901/vnc.html?autoconnect=true

6. **Iterate**: Make additional changes locally, sync, and test again

## Troubleshooting

### SSH Connection Issues

If you encounter SSH connectivity problems:

```bash
gcloud compute ssh zigral-chrome-embed --project=zigral --zone=us-south1-c --troubleshoot
```

### Sync Failures

If synchronization fails, try:

1. Verify the VM is running:
   ```bash
   gcloud compute instances describe zigral-chrome-embed --zone=us-south1-c --format="value(status)"
   ```

2. Check file permissions:
   ```bash
   gcloud compute ssh wilson_austin10@zigral-chrome-embed --zone=us-south1-c --command="ls -la /home/wilson_austin10/zigral-vnc"
   ```

3. Ensure paths exist on both sides before synchronizing

## Best Practices

1. **Regular Syncs**: Pull changes regularly to avoid conflicts
2. **Small Commits**: Make focused changes and sync frequently
3. **Directory-Specific Syncs**: For larger projects, sync specific directories to reduce transfer time
4. **Script Extensions**: Customize the sync scripts for project-specific requirements
5. **Testing Changes**: Always test changes after pushing to the VM

## Advanced: IDE Integration

### VSCode Remote-SSH Extension

For a more integrated experience, consider using VSCode with the Remote-SSH extension:

1. Install the Remote-SSH extension in VSCode
2. Configure a connection to the VM using gcloud credentials 
3. This allows direct editing of files on the VM with local-like performance

## Conclusion

This local development setup provides the best of both worlds:
- The power and flexibility of your local development environment
- The ability to quickly test changes in the actual VM environment

By following this workflow, you can develop efficiently while ensuring your code works correctly in the production-like VM environment. 