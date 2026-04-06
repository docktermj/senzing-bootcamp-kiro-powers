---
inclusion: manual
---

# Environment Setup

This guide covers setting up your development environment before starting the Senzing Bootcamp.

## Version Control

Initialize git for your project:

```bash
cd my-senzing-project
git init
git add .
git commit -m "Initial project setup"
```

## .gitignore Configuration

Create a `.gitignore` file that covers the bootcamper's chosen language plus common project exclusions:

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
*.log

# Database files
*.db
*.sqlite
*.sqlite3

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

Add language-specific entries based on the bootcamper's chosen language:

**Python:**

```gitignore
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/
```

**Java:**

```gitignore
target/
*.class
*.jar
*.war
.gradle/
build/
```

**C#:**

```gitignore
bin/
obj/
*.user
*.suo
packages/
```

**Rust:**

```gitignore
target/
Cargo.lock
```

**TypeScript / Node.js:**

```gitignore
node_modules/
dist/
npm-debug.log
```

## Language Environment

Set up the development environment for your chosen language:

### Python

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install senzing
pip freeze > requirements.txt
```

```powershell
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
pip install senzing
pip freeze > requirements.txt
```

### Java

```bash
# Use Maven or Gradle to manage dependencies
# Add senzing SDK dependency to pom.xml or build.gradle
```

### C-sharp

```bash
dotnet new console -n my-senzing-project
# Add Senzing NuGet package
```

### Rust

```bash
cargo init my-senzing-project
# Add senzing dependency to Cargo.toml
```

### TypeScript / Node.js

```bash
npm init -y
# Add senzing dependency to package.json
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

## When to Load This Guide

Load this steering file when:

- Starting Module 0 (initial project setup)
- User asks about version control setup
- User needs help with environment configuration

## Important Note on Source Code Location

All generated source code must be placed in the `src/` directory structure:

- Transformation programs → `src/transform/`
- Loading programs → `src/load/`
- Query programs → `src/query/`
- Utility scripts → `src/utils/`

Automation scripts go in `scripts/`. See `docs/policies/FILE_STORAGE_POLICY.md` for the complete policy.
