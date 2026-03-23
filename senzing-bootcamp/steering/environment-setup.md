---
inclusion: manual
---

# Environment Setup

This guide covers setting up your development environment before starting the Senzing Boot Camp.

## Version Control

Initialize git for your project:

```bash
cd my-senzing-project
git init
git add .
git commit -m "Initial project setup"
```

## .gitignore Configuration

Create a `.gitignore` file to exclude sensitive data and large files:

```gitignore
# Sensitive data
.env
*.key
*.pem
config/*_credentials.json

# Data files (too large for git)
data/raw/*
data/transformed/*
!data/raw/.gitkeep
!data/transformed/.gitkeep

# Database files
database/*.db
database/*.db-journal
!database/.gitkeep

# Logs
logs/*.log
*.log

# Database files
*.db
*.sqlite
*.sqlite3

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/

# Node
node_modules/
npm-debug.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backups
data/backups/*.sql
```

## Python Environment

If using Python, set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install senzing
pip freeze > requirements.txt
```

## Environment Variables

Create `.env.example` as a template:

```bash
# Senzing Configuration
SENZING_ENGINE_CONFIG_JSON={"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing"}}
SENZING_DATABASE_URL=sqlite3://na:na@database/G2C.db

# Data Source Credentials (examples - replace with actual)
CRM_API_KEY=your_api_key_here
DATABASE_CONNECTION_STRING=postgresql://user:pass@localhost:5432/dbname

# Monitoring
ENABLE_MONITORING=true
LOG_LEVEL=INFO
```

Copy to `.env` and fill in actual values (never commit `.env` to git).

## Docker Environment (Optional)

Create `docker-compose.yml` in the project root for containerized setup:

```yaml
version: '3.8'
services:
  senzing:
    image: senzing/senzing-tools:latest
    volumes:
      - ./data:/data
      - ./config:/config
    environment:
      - SENZING_ENGINE_CONFIGURATION_JSON=${SENZING_ENGINE_CONFIG_JSON}
  
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=senzing
      - POSTGRES_USER=senzing
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

## When to Load This Guide

Load this steering file when:
- Starting Module 1 (initial project setup)
- User asks about version control setup
- User needs help with environment configuration
- Setting up Docker or containerized environments

## Important Note on Source Code Location

All generated source code, including utility scripts like backup and rollback scripts, must be placed in the `src/` directory structure:
- Transformation programs → `src/transform/`
- Loading programs → `src/load/`
- Query programs → `src/query/`
- Utility scripts → `src/utils/`

Never place source code files in the project root or in a separate `scripts/` directory.
