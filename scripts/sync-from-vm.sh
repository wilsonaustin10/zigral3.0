#!/bin/bash

# Script to sync changes from the VM to local environment
# Usage: ./sync-from-vm.sh [file_or_directory_path]

# Configuration
VM_NAME="zigral-chrome-embed"
VM_ZONE="us-south1-c"
VM_USER="wilson_austin10"
VM_DIR="/home/wilson_austin10/zigral-vnc"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure the script is run from Zigral 3.0/zigral-vnc directory
if [[ "$(basename "$LOCAL_DIR")" != "zigral-vnc" ]]; then
  echo "Error: This script must be run from within the zigral-vnc directory"
  exit 1
fi

# Check if a specific file or directory was provided
if [ $# -eq 0 ]; then
  echo "Syncing entire zigral-vnc directory from VM (excluding .git, node_modules, .venv)"
  
  # Create a temporary exclude file
  EXCLUDE_FILE="$(mktemp)"
  echo ".git/" > "$EXCLUDE_FILE"
  echo "node_modules/" >> "$EXCLUDE_FILE"
  echo ".venv/" >> "$EXCLUDE_FILE"
  echo "frontend_backup_*/" >> "$EXCLUDE_FILE"
  
  # Create a temporary script to run rsync on the remote machine
  TMP_SCRIPT="$(mktemp)"
  cat > "$TMP_SCRIPT" << EOF
#!/bin/bash
cd "$VM_DIR"
rsync -avz --exclude-from="\$1" . "$LOCAL_DIR/"
EOF
  chmod +x "$TMP_SCRIPT"
  
  # Copy the exclude file to the VM
  gcloud compute scp "$EXCLUDE_FILE" "$VM_USER@$VM_NAME:$VM_DIR/exclude_file.tmp" --zone="$VM_ZONE"
  
  # Run rsync from the VM to local
  gcloud compute ssh "$VM_USER@$VM_NAME" --zone="$VM_ZONE" -- "bash -s" < "$TMP_SCRIPT" "$VM_DIR/exclude_file.tmp"
  
  # Clean up
  gcloud compute ssh "$VM_USER@$VM_NAME" --zone="$VM_ZONE" --command="rm $VM_DIR/exclude_file.tmp"
  rm "$EXCLUDE_FILE" "$TMP_SCRIPT"
else
  # Sync specific file or directory
  REMOTE_PATH="$1"
  # Remove leading slash if present
  REMOTE_PATH="${REMOTE_PATH#/}"
  
  # Full path on VM
  FULL_REMOTE_PATH="$VM_DIR/$REMOTE_PATH"
  
  # Check if the remote path exists
  REMOTE_EXISTS=$(gcloud compute ssh "$VM_USER@$VM_NAME" --zone="$VM_ZONE" --command="[ -e '$FULL_REMOTE_PATH' ] && echo 'exists' || echo 'not exists'")
  
  if [ "$REMOTE_EXISTS" != "exists" ]; then
    echo "Error: File or directory does not exist on VM: $FULL_REMOTE_PATH"
    exit 1
  fi
  
  echo "Syncing $REMOTE_PATH from VM to local"
  
  # Check if it's a directory
  IS_DIR=$(gcloud compute ssh "$VM_USER@$VM_NAME" --zone="$VM_ZONE" --command="[ -d '$FULL_REMOTE_PATH' ] && echo 'dir' || echo 'file'")
  
  if [ "$IS_DIR" == "dir" ]; then
    # It's a directory
    mkdir -p "$LOCAL_DIR/$REMOTE_PATH"
    gcloud compute scp -r "$VM_USER@$VM_NAME:$FULL_REMOTE_PATH/*" "$LOCAL_DIR/$REMOTE_PATH/" --zone="$VM_ZONE"
  else
    # It's a file
    LOCAL_DIR_PATH=$(dirname "$LOCAL_DIR/$REMOTE_PATH")
    mkdir -p "$LOCAL_DIR_PATH"
    gcloud compute scp "$VM_USER@$VM_NAME:$FULL_REMOTE_PATH" "$LOCAL_DIR/$REMOTE_PATH" --zone="$VM_ZONE"
  fi
fi

echo "Sync completed!" 