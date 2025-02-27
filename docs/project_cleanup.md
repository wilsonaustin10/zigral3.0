# Zigral 3.0 Project Cleanup Plan

This document provides an analysis of the current Zigral 3.0 project structure and outlines a cleanup plan to ensure a more organized, efficient codebase without redundancies.

## Current Structure Analysis

The project currently has two parallel structures:
1. The root directory (`/Users/austinwilson/Zigral 3.0/`)
2. The `zigral-vnc` subdirectory (`/Users/austinwilson/Zigral 3.0/zigral-vnc/`)

Based on our analysis, the `zigral-vnc` directory contains the most up-to-date code and should be treated as the primary source of truth. Many files and directories are duplicated between the root and the `zigral-vnc` directory.

## Identified Redundancies

### 1. Duplicate Directories

The following directories exist in both locations with similar or identical content:
- `src/` - Core application code
- `tests/` - Testing files
- `config/` - Configuration files
- `docs/` - Documentation
- `scripts/` - Utility scripts
- `docker/` - Docker configurations
- `frontend/` - Frontend code

### 2. Duplicate Files

Several key files are duplicated:
- `README.md` - Project overview
- `requirements.txt` and `requirements-vnc.txt` - Python dependencies
- `start_all_services.sh` - Service startup script
- `start_context_manager.sh` - Context manager startup
- `start_uvicorn.sh` - Uvicorn server startup
- `.env` and `.env.example` - Environment configurations
- `Dockerfile` and `Dockerfile.vm` - Docker configurations
- `docker-compose.yml` - Docker Compose configuration
- `setup_vnc.sh` - VNC setup script
- Various configuration files for linting, testing, etc.

### 3. Obsolete Files

The root directory contains some obsolete files related to the abandoned Kasm approach:
- `kasm_install.sh`
- `kasm_release_1.16.1.tar.gz`
- References to Kasm in the `docker/kasm/` directory

## Cleanup Plan

### 1. Backup First

Before making any changes:
```bash
# Create a timestamp for the backup
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Archive the entire project excluding large directories
cd /Users/austinwilson/Zigral\ 3.0/
tar -czf zigral_backup_$TIMESTAMP.tar.gz --exclude='*.venv*' --exclude='*node_modules*' --exclude='*__pycache__*' .
```

### 2. Consolidate Environment Variables

1. Compare `.env` files and merge any unique variables from the root `.env` into `zigral-vnc/.env`
2. Ensure `.env.example` in `zigral-vnc` is up-to-date with all required variables (without sensitive values)

### 3. Update Documentation

1. Ensure all documentation in `zigral-vnc/docs/` is current
2. Copy any unique/additional documentation from root `docs/` to `zigral-vnc/docs/`

### 4. Consolidate Scripts

1. Compare sync scripts in `zigral-vnc/scripts/` with any related scripts in root `scripts/`
2. Update paths and references in scripts to match the consolidated structure

### 5. Clean Up Redundant Files

After ensuring all unique content is preserved, remove redundant files from the root directory:

```bash
# List of directories to remove (after ensuring content is preserved)
rm -rf src/
rm -rf tests/
rm -rf config/
rm -rf scripts/
rm -rf docker/
rm -rf frontend/
rm -rf workspace/

# List of specific files to remove (after ensuring content is preserved)
rm Dockerfile
rm Dockerfile.vm
rm docker-compose.yml
rm start_all_services.sh
rm start_context_manager.sh
rm start_uvicorn.sh
rm setup_vnc.sh
rm requirements.txt
rm requirements-vnc.txt
rm kasm_install.sh
rm kasm_release_1.16.1.tar.gz
```

### 6. Create a Clean Project Structure

After cleanup, the project structure should be:

```
/Users/austinwilson/Zigral 3.0/
├── .git/                    # Git repository 
├── .github/                 # GitHub configurations
├── docs/                    # Project-level documentation (consider moving to zigral-vnc/docs)
├── zigral-vnc/              # Main project directory
│   ├── config/              # Configuration files
│   ├── docker/              # Docker configurations
│   ├── docs/                # Project documentation
│   ├── logs/                # Log files
│   ├── scripts/             # Utility scripts
│   ├── src/                 # Application source code
│   ├── tests/               # Test files
│   ├── .env                 # Environment variables
│   ├── .env.example         # Example environment variables
│   ├── docker-compose.yml   # Docker compose configuration
│   ├── Dockerfile           # Docker configuration
│   ├── pyproject.toml       # Poetry configuration
│   ├── requirements.txt     # Python dependencies
│   └── README.md            # Project overview
├── .gitignore               # Git ignore file
├── LICENSE                  # License file
├── pyproject.toml           # Root Poetry configuration (consider consolidating)
└── README.md                # Root README (consider updating to point to zigral-vnc)
```

### 7. Update Git Configuration

Ensure Git is tracking the correct files and directories:

```bash
# Update .gitignore to reflect the new structure
# Add any patterns for files that should not be tracked
```

### 8. Containerization Updates

1. Review and update `zigral-vnc/Dockerfile` to ensure all dependencies are properly containerized
2. Update `zigral-vnc/docker-compose.yml` to use environment variables rather than hardcoded values

## Implementation Plan

1. **Phase 1: Backup and Analysis**
   - Create complete backup
   - Analyze files for unique content

2. **Phase 2: Consolidation**
   - Merge environment variables
   - Update documentation
   - Consolidate scripts
   - Update configuration files

3. **Phase 3: Cleanup**
   - Remove redundant files
   - Update Git configuration
   - Test build and deployment

4. **Phase 4: Verification**
   - Verify all services start correctly
   - Verify all tests pass
   - Verify documentation is accurate

## Recommendations for Future Development

1. **Single Source of Truth**: Maintain `zigral-vnc` as the primary project directory
2. **Clear Documentation**: Keep documentation updated with every significant change
3. **Environment Variables**: Use environment variables for configuration rather than hardcoded values
4. **Containerization**: Ensure all dependencies are properly containerized for consistent deployment
5. **Modular Design**: Continue to design components that can be plugged together with clear interfaces
6. **Automated Testing**: Maintain and expand test coverage to ensure reliability

## Conclusion

This cleanup will result in a more organized, maintainable codebase by eliminating redundancies and establishing a clear structure. The `zigral-vnc` directory will serve as the primary project location, with all necessary files properly organized within it. 