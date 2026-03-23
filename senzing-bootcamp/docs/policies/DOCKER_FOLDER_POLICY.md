# Docker Folder Policy

**Date**: 2026-03-17  
**Policy**: All Docker-related files must be in `docker/` directory

## Overview

This policy ensures consistent organization of Docker-related files across all Senzing Boot Camp projects.

## Policy Statement

**All Docker-related files MUST be stored in the `docker/` directory, NEVER in the project root or other directories.**

## Rationale

### Why Not in Project Root?

1. **Organization**: Keeps root directory clean and focused
2. **Separation of Concerns**: Docker files are deployment-specific
3. **Multi-Environment**: Easier to manage dev/staging/prod Dockerfiles
4. **Consistency**: Matches other file organization (src/, docs/, config/)
5. **Discoverability**: All Docker files in one place
6. **Best Practice**: Industry standard for larger projects

### Benefits

- Clear project structure
- Easier to find Docker files
- Better separation of deployment concerns
- Supports multiple Docker configurations
- Consistent with file storage policy

## Directory Structure

```
project-root/
├── docker/
│   ├── Dockerfile                 # Main/production Dockerfile
│   ├── Dockerfile.dev             # Development Dockerfile
│   ├── Dockerfile.prod            # Production Dockerfile (if different)
│   ├── docker-compose.yml         # Development compose
│   ├── docker-compose.dev.yml     # Development compose (explicit)
│   ├── docker-compose.prod.yml    # Production compose
│   ├── docker-compose.test.yml    # Testing compose
│   ├── .dockerignore              # Docker ignore rules
│   └── scripts/                   # Docker-specific scripts
│       ├── entrypoint.sh          # Container entrypoint
│       ├── healthcheck.sh         # Health check script
│       └── init.sh                # Initialization script
└── [other project files]
```

## File Locations

### ✅ CORRECT

```bash
docker/Dockerfile
docker/Dockerfile.dev
docker/Dockerfile.prod
docker/docker-compose.yml
docker/docker-compose.dev.yml
docker/docker-compose.prod.yml
docker/.dockerignore
docker/scripts/entrypoint.sh
docker/scripts/healthcheck.sh
```

### ❌ WRONG

```bash
Dockerfile                          # In project root
docker-compose.yml                  # In project root
deployment/Dockerfile               # In wrong directory
src/Dockerfile                      # In wrong directory
.dockerignore                       # In project root (should be docker/.dockerignore)
```

## Building Docker Images

When Docker files are in `docker/`, adjust build commands:

### Single Dockerfile

```bash
# Build from docker/Dockerfile
docker build -f docker/Dockerfile -t myapp:latest .

# Or change to docker directory
cd docker
docker build -t myapp:latest ..
```

### Docker Compose

```bash
# Run docker-compose from project root
docker-compose -f docker/docker-compose.yml up

# Or change to docker directory
cd docker
docker-compose up
```

### Docker Compose with Context

In `docker/docker-compose.yml`, set build context correctly:

```yaml
version: '3.8'
services:
  app:
    build:
      context: ..              # Parent directory (project root)
      dockerfile: docker/Dockerfile
    ports:
      - "8080:8080"
```

## .dockerignore Location

The `.dockerignore` file should be in the `docker/` directory:

```bash
docker/.dockerignore
```

**Content example**:
```
# Exclude from Docker build context
.git
.github
.vscode
*.md
tests/
docs/
data/raw/*
data/transformed/*
database/*.db
logs/
*.pyc
__pycache__/
.env
```

## Multi-Environment Setup

### Development

`docker/Dockerfile.dev`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dev dependencies
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Enable hot reload
ENV FLASK_ENV=development

CMD ["python", "src/api_server.py"]
```

`docker/docker-compose.dev.yml`:
```yaml
version: '3.8'
services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dev
    volumes:
      - ../src:/app/src        # Mount source for hot reload
    environment:
      - DEBUG=true
```

### Production

`docker/Dockerfile.prod`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/

# Run as non-root user
RUN useradd -m appuser
USER appuser

CMD ["gunicorn", "src.api_server:app"]
```

`docker/docker-compose.prod.yml`:
```yaml
version: '3.8'
services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile.prod
    restart: always
    environment:
      - ENV=production
```

## CI/CD Integration

### GitHub Actions

`.github/workflows/docker-build.yml`:
```yaml
name: Docker Build

on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: |
          docker build -f docker/Dockerfile -t myapp:${{ github.sha }} .
      
      - name: Test Docker image
        run: |
          docker run myapp:${{ github.sha }} pytest tests/
```

### Deployment Scripts

`deployment/scripts/deploy.sh`:
```bash
#!/bin/bash
set -e

VERSION=$1

# Build from docker/ directory
docker build -f docker/Dockerfile.prod -t company/app:$VERSION .

# Push to registry
docker push company/app:$VERSION

# Deploy
kubectl set image deployment/app app=company/app:$VERSION
```

## Migration Guide

### For Existing Projects

If you have Docker files in the project root:

1. **Create docker directory**:
   ```bash
   mkdir -p docker/scripts
   ```

2. **Move Docker files**:
   ```bash
   mv Dockerfile docker/
   mv Dockerfile.* docker/
   mv docker-compose*.yml docker/
   mv .dockerignore docker/
   ```

3. **Update build commands** in:
   - README.md
   - CI/CD pipelines
   - Deployment scripts
   - Documentation

4. **Update docker-compose.yml** build context:
   ```yaml
   build:
     context: ..
     dockerfile: docker/Dockerfile
   ```

5. **Test builds**:
   ```bash
   docker build -f docker/Dockerfile -t test .
   docker-compose -f docker/docker-compose.yml up
   ```

6. **Commit changes**:
   ```bash
   git add docker/
   git commit -m "Move Docker files to docker/ directory"
   ```

## Exceptions

There are NO exceptions to this policy. All Docker-related files must be in `docker/`.

Even for simple projects with a single Dockerfile, use `docker/Dockerfile`.

## Enforcement

### Documentation Review

All documentation must reference Docker files in `docker/` directory.

### Code Review

Pull requests should be checked for Docker files in wrong locations.

### Automated Checks

Add to CI pipeline:

```bash
# Check for Docker files in wrong locations
if [ -f "Dockerfile" ] || [ -f "docker-compose.yml" ]; then
    echo "ERROR: Docker files must be in docker/ directory"
    exit 1
fi
```

## Related Policies

- [FILE_STORAGE_POLICY.md](FILE_STORAGE_POLICY.md) - Complete file storage rules
- [MODULE_0_CODE_LOCATION.md](MODULE_0_CODE_LOCATION.md) - Module 0 code placement

## Examples in Boot Camp

### Simple Single Source Example

```
examples/simple-single-source/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── src/
├── data/
└── README.md
```

### Production Deployment Example

```
examples/production-deployment/
├── docker/
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── Dockerfile.prod
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── .dockerignore
│   └── scripts/
│       ├── entrypoint.sh
│       └── healthcheck.sh
├── deployment/
│   └── kubernetes/
├── src/
└── README.md
```

## Questions?

**Q: Why not keep Dockerfile in root for simplicity?**  
A: Consistency and scalability. As projects grow, having Docker files in `docker/` keeps things organized.

**Q: What about .dockerignore?**  
A: It goes in `docker/.dockerignore`, not the project root.

**Q: Do I need docker/scripts/?**  
A: Only if you have Docker-specific scripts like entrypoint.sh or healthcheck.sh.

**Q: Can I have Dockerfile in root for simple projects?**  
A: No. Use `docker/Dockerfile` even for simple projects to maintain consistency.

## Version History

- **v1.0.0** (2026-03-17): Docker folder policy created

