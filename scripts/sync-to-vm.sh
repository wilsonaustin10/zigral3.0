#!/bin/bash

# Script to sync local changes to the VM
# Usage: ./sync-to-vm.sh [file_or_directory_path]

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
  echo "Syncing entire zigral-vnc directory (excluding .git, node_modules, .venv)"
  
  # Create a temporary exclude file
  EXCLUDE_FILE="$(mktemp)"
  echo ".git/" > "$EXCLUDE_FILE"
  echo "node_modules/" >> "$EXCLUDE_FILE"
  echo ".venv/" >> "$EXCLUDE_FILE"
  echo "frontend_backup_*/" >> "$EXCLUDE_FILE"
  
  # Use rsync to sync the directory, excluding specified patterns
  gcloud compute ssh "$VM_USER@$VM_NAME" --zone="$VM_ZONE" --command="mkdir -p $VM_DIR"
  rsync -avz --exclude-from="$EXCLUDE_FILE" -e "gcloud compute ssh $VM_USER@$VM_NAME --zone=$VM_ZONE --command=" "$LOCAL_DIR/" "$VM_DIR/"
  
  # Clean up
  rm "$EXCLUDE_FILE"
else
  # Sync specific file or directory
  FILE_PATH="$1"
  RELATIVE_PATH=$(realpath --relative-to="$LOCAL_DIR" "$FILE_PATH")
  
  if [ ! -e "$FILE_PATH" ]; then
    echo "Error: File or directory does not exist: $FILE_PATH"
    exit 1
  fi
  
  echo "Syncing $RELATIVE_PATH to VM"
  
  if [ -d "$FILE_PATH" ]; then
    # It's a directory
    TARGET_DIR="$VM_DIR/$(dirname "$RELATIVE_PATH")"
    gcloud compute ssh "$VM_USER@$VM_NAME" --zone="$VM_ZONE" --command="mkdir -p $TARGET_DIR"
    gcloud compute scp -r "$FILE_PATH" "$VM_USER@$VM_NAME:$VM_DIR/$RELATIVE_PATH" --zone="$VM_ZONE"
  else
    # It's a file
    TARGET_DIR="$VM_DIR/$(dirname "$RELATIVE_PATH")"
    gcloud compute ssh "$VM_USER@$VM_NAME" --zone="$VM_ZONE" --command="mkdir -p $TARGET_DIR"
    gcloud compute scp "$FILE_PATH" "$VM_USER@$VM_NAME:$VM_DIR/$RELATIVE_PATH" --zone="$VM_ZONE"
  fi
fi

echo "Sync completed!" 