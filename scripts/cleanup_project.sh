#!/bin/bash

# Zigral 3.0 Project Cleanup Script
# This script implements the cleanup plan from project_cleanup.md
# WARNING: Always run this script from the Zigral 3.0 root directory!

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "zigral-vnc" ]; then
    echo -e "${RED}ERROR: This script must be run from the Zigral 3.0 root directory!${NC}"
    echo -e "${YELLOW}Please cd to /Users/austinwilson/Zigral\ 3.0/ and try again.${NC}"
    exit 1
fi

# Function to display section headers
section() {
    echo -e "\n${GREEN}=== $1 ===${NC}"
}

# 1. Backup step
section "Creating Backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="zigral_backup_$TIMESTAMP.tar.gz"

echo "Creating backup: $BACKUP_FILE"
tar -czf "$BACKUP_FILE" --exclude='*.venv*' --exclude='*node_modules*' --exclude='*__pycache__*' .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Backup created successfully!${NC}"
else
    echo -e "${RED}Backup failed! Aborting.${NC}"
    exit 1
fi

# 2. Environment Variables Consolidation
section "Consolidating Environment Variables"
echo "Please manually review and merge environment variables"
echo -e "${YELLOW}ACTION REQUIRED: Compare .env with zigral-vnc/.env and merge any unique variables${NC}"
echo "Press Enter to continue when done..."
read

# 3. Documentation Consolidation
section "Consolidating Documentation"
echo "Checking for unique documentation in root docs directory..."

# Create a list of docs that exist in root but not in zigral-vnc
for doc in docs/*.md; do
    basename=$(basename "$doc")
    if [ ! -f "zigral-vnc/docs/$basename" ]; then
        echo "Found unique doc: $basename"
        echo -e "${YELLOW}ACTION REQUIRED: Review and copy $basename to zigral-vnc/docs/ if needed${NC}"
    fi
done

echo "Press Enter to continue when done..."
read

# 4. Script Consolidation
section "Consolidating Scripts"
echo "Checking for unique scripts in root scripts directory..."

# Create a list of scripts that exist in root but not in zigral-vnc
for script in scripts/*; do
    basename=$(basename "$script")
    if [ ! -f "zigral-vnc/scripts/$basename" ]; then
        echo "Found unique script: $basename"
        echo -e "${YELLOW}ACTION REQUIRED: Review and copy $basename to zigral-vnc/scripts/ if needed${NC}"
    fi
done

echo "Press Enter to continue when done..."
read

# 5. Clean Up Redundant Files
section "Clean Up Redundant Files"
echo -e "${RED}WARNING: This will remove redundant files and directories.${NC}"
echo -e "${YELLOW}Make sure you've preserved all unique content before proceeding.${NC}"
echo -e "Type 'CONFIRM' to proceed with deletion:"
read confirmation

if [ "$confirmation" != "CONFIRM" ]; then
    echo "Cleanup aborted by user."
    exit 0
fi

# List directories to be removed
DIRS_TO_REMOVE="src tests config scripts docker frontend workspace"
echo "The following directories will be removed:"
for dir in $DIRS_TO_REMOVE; do
    echo "- $dir/"
done

# List files to be removed
FILES_TO_REMOVE="Dockerfile Dockerfile.vm docker-compose.yml start_all_services.sh start_context_manager.sh start_uvicorn.sh setup_vnc.sh requirements.txt requirements-vnc.txt kasm_install.sh kasm_release_1.16.1.tar.gz"
echo "The following files will be removed:"
for file in $FILES_TO_REMOVE; do
    echo "- $file"
done

echo -e "${RED}Last chance to abort. Press Ctrl+C to abort or Enter to continue...${NC}"
read

# Remove directories
for dir in $DIRS_TO_REMOVE; do
    if [ -d "$dir" ]; then
        echo "Removing directory: $dir/"
        rm -rf "$dir"
    fi
done

# Remove files
for file in $FILES_TO_REMOVE; do
    if [ -f "$file" ]; then
        echo "Removing file: $file"
        rm "$file"
    fi
done

# 6. Update Root README
section "Updating Root README"
echo -e "${YELLOW}ACTION REQUIRED: Update the root README.md to point to zigral-vnc as the main project directory${NC}"
echo "Press Enter to continue when done..."
read

# 7. Update .gitignore
section "Updating .gitignore"
echo -e "${YELLOW}ACTION REQUIRED: Review and update .gitignore for the new structure${NC}"
echo "Press Enter to continue when done..."
read

section "Cleanup Complete!"
echo -e "${GREEN}The project cleanup has been completed!${NC}"
echo "Backup file: $BACKUP_FILE"
echo ""
echo "Next steps:"
echo "1. Verify all services work correctly"
echo "2. Update containerization if needed"
echo "3. Push changes to version control"
echo ""
echo -e "${YELLOW}Remember: zigral-vnc is now your primary project directory.${NC}" 