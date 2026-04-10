---
inclusion: manual
---

# Environment Setup

## Version Control

```bash
git init
git add .
git commit -m "Initial project setup"
```

## .gitignore (Senzing Bootcamp Specific)

Create a `.gitignore` with these bootcamp-specific entries. Add standard language entries (Python `__pycache__`, Java `target/`, etc.) based on the chosen language — the LLM knows these.

```gitignore
# Sensitive data
.env
*.key
*.pem
config/*_credentials.json

# Data files (too large for git)
data/raw/*
data/transformed/*
data/temp/*
!data/raw/.gitkeep
!data/transformed/.gitkeep
!data/temp/.gitkeep

# Database files
database/*.db
database/*.db-journal
!database/.gitkeep

# Logs
logs/*.log

# Backups
data/backups/*.sql

# OS
.DS_Store
Thumbs.db
```

## Environment Variables

Use a project-local script instead of modifying global shell config:

Create `scripts/senzing-env.sh` (Linux/macOS) or `scripts/senzing-env.bat` (Windows):

```bash
# scripts/senzing-env.sh (Linux/macOS)
export SENZING_ROOT=/opt/senzing
export SENZING_ENGINE_CONFIG_JSON=$(cat config/engine_config.json)
export SENZING_DATABASE_URL=sqlite3://na:na@database/G2C.db
```

```bat
REM scripts/senzing-env.bat (Windows)
set SENZING_ROOT=C:\opt\senzing
set /p SENZING_ENGINE_CONFIG_JSON=<config\engine_config.json
set SENZING_DATABASE_URL=sqlite3://na:na@database/G2C.db
```

Create `.env.example` as a template for any additional variables. Copy to `.env` and fill in actual values (never commit `.env`).

## Language Setup

Use `sdk_guide(topic='install', language='<chosen_language>')` for current SDK binding installation. The MCP server provides the correct commands for each language.

## Source Code Location

All generated source code goes in `src/` subdirectories: `src/transform/`, `src/load/`, `src/query/`, `src/utils/`. Automation scripts go in `scripts/`.
