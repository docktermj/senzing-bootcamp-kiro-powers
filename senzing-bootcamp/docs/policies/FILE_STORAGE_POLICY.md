# File Storage Policy

## Overview

This document defines where different types of files should be stored in the Senzing Boot Camp project structure. Never use temporary directories like `/tmp` for project files.

## Core Principle

**All project files must be stored in appropriate project directories, never in system temporary directories.**

## Core Rules

1. **Never use `/tmp`** for project files
2. **Docker files go in `docker/`** - never in project root
3. **Source code goes in `src/`** - never in project root
4. **Use project-specific directories** for all file types

## File Storage Rules

### Source Code Files

**Rule**: All source code files (`.py`, `.java`, `.cs`, `.rs`, etc.) must be stored in the `src/` directory.

**Structure**:

```text
src/
├── quickstart_demo/     # Module 0 demo code
├── transform/           # Transformation programs (Module 4)
├── load/                # Loading programs (Module 6)
├── query/               # Query programs (Module 8)
└── utils/               # Shared utilities
```

**Examples**:

```bash
# ✅ CORRECT
src/transform/transform_customers.py
src/load/load_customers.py
src/query/find_duplicates.py
src/utils/data_quality_checker.py

# ❌ WRONG
/tmp/transform.py
~/Downloads/loader.py
transform_customers.py  # (in project root)
```

### Shell Scripts

**Rule**: All shell scripts (`.sh`) must be stored in the `scripts/` directory.

**Structure**:

```text
scripts/
├── deploy.sh            # Deployment automation
├── backup.sh            # Database backup
├── migrate_db.sh        # Database migration
├── run_pipeline.sh      # Pipeline execution
├── health_check.sh      # Health checks
└── setup_env.sh         # Environment setup
```

**Examples**:

```bash
# ✅ CORRECT
scripts/deploy.sh
scripts/backup.sh
scripts/run_pipeline.sh

# ❌ WRONG
/tmp/deploy.sh
src/deploy.sh           # Shell scripts don't go in src/
deploy.sh               # (in project root)
```

### Documentation Files

**Rule**: All markdown files (`.md`) must be stored in the `docs/` directory or project root (for POWER.md and README.md only).

**Structure**:

```text
docs/
├── guides/              # User-facing guides
├── modules/             # Module documentation
├── policies/            # Policy documents (like this file)
└── development/         # Internal documentation
```

**Examples**:

```bash
# ✅ CORRECT
docs/guides/QUICK_START.md
docs/modules/MODULE_1_BUSINESS_PROBLEM.md
docs/policies/FILE_STORAGE_POLICY.md
POWER.md                # Exception: required in root
README.md               # Exception: required in root

# ❌ WRONG
/tmp/guide.md
~/Documents/module.md
my_notes.md             # (in project root)
```

### Data Files

**Rule**: All data files (`.json`, `.jsonl`, `.csv`, etc.) must be stored in the `data/` directory.

**Structure**:

```text
data/
├── raw/                 # Original source data
├── transformed/         # Senzing-formatted JSON
├── samples/             # Sample data for testing
└── backups/             # Database backups
```

**Examples**:

```bash
# ✅ CORRECT
data/raw/customers.csv
data/transformed/customers.jsonl
data/samples/test_data.json
data/backups/senzing_backup_20260317.sql

# ❌ WRONG
/tmp/customers.csv
~/Downloads/data.json
customers.csv           # (in project root)
```

### Database Files

**Rule**: SQLite database files (`.db`, `.sqlite`, `.sqlite3`) must be stored in the `database/` directory.

**Structure**:

```text
database/
├── G2C.db               # Main Senzing database
├── G2C.db-journal       # SQLite journal file (auto-generated)
└── .gitkeep             # Keep directory in git
```

**Examples**:

```bash
# ✅ CORRECT
database/G2C.db
database/test.db

# ❌ WRONG
/var/opt/senzing/sqlite/G2C.db
/tmp/G2C.db
G2C.db                  # (in project root)
data/G2C.db             # (data/ is for data files, not databases)
```

**Note**: Add `database/*.db` to `.gitignore` to exclude database files from version control:

```gitignore
# Database files
database/*.db
database/*.db-journal
!database/.gitkeep
```

### Configuration Files

**Rule**: Configuration files (`.json`, `.yaml`, `.yml`, `.env`, `.ini`) should be stored in the `config/` directory or project root (for `.env` files).

**Structure**:

```text
config/
├── senzing_config.json
├── database_config.yaml
└── app_settings.ini

# Root level (exceptions)
.env                     # Environment variables (not in git)
.env.example             # Environment template (in git)
```

**Examples**:

```bash
# ✅ CORRECT
config/senzing_config.json
config/database_config.yaml
.env                    # Exception: in root
.env.example            # Exception: in root

# ❌ WRONG
/tmp/config.json
~/config.yaml
senzing_config.json     # (in project root, should be in config/)
```

### License Files

**Rule**: Senzing license files must be stored in the `licenses/` directory.

**Structure**:

```text
licenses/
├── g2.lic               # Senzing license file
├── .gitkeep             # Keep directory in git
└── README.md            # Instructions on obtaining/placing license
```

**Examples**:

```bash
# ✅ CORRECT
licenses/g2.lic
licenses/g2_dev.lic
licenses/g2_prod.lic

# ❌ WRONG
/etc/opt/senzing/g2.lic
/tmp/g2.lic
g2.lic                  # (in project root)
config/g2.lic           # (config/ is for configuration, not licenses)
```

**Note**: Add `licenses/*.lic` to `.gitignore` to exclude license files from version control:

```gitignore
# License files
licenses/*.lic
!licenses/.gitkeep
!licenses/README.md
```

**License Priority**: Senzing SDK checks for licenses in this order:

1. Project-specific license: `licenses/g2.lic`
2. System-wide license: `/etc/opt/senzing/g2.lic` or `SENZING_LICENSE_PATH` environment variable

If users already have a system-wide Senzing license, they don't need to place one in the project. The `licenses/` directory is for bootcampers who want a project-specific license.

### Docker Files

**Rule**: All Docker-related files must be stored in the `docker/` directory.

**Structure**:

```text
docker/
├── Dockerfile           # Main Dockerfile
├── Dockerfile.dev       # Development Dockerfile
├── Dockerfile.prod      # Production Dockerfile
├── docker-compose.yml   # Docker Compose configuration
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .dockerignore        # Docker ignore rules
└── scripts/             # Docker-specific scripts
    ├── entrypoint.sh
    └── healthcheck.sh
```

**Examples**:

```bash
# ✅ CORRECT
docker/Dockerfile
docker/docker-compose.yml
docker/.dockerignore
docker/scripts/entrypoint.sh

# ❌ WRONG
Dockerfile              # (in project root)
docker-compose.yml      # (in project root)
/tmp/Dockerfile
deployment/Dockerfile   # (wrong directory)
```

**Note**: Docker-related files should NEVER be in the project root or other directories.

### Downloaded Files

**Rule**: Downloaded installation files should be stored in the user's home directory, not `/tmp`.

**Examples**:

```bash
# ✅ CORRECT - Download to home directory
wget -qO - https://example.com/package.deb -O ~/package.deb
sudo apt install ~/package.deb

# ❌ WRONG - Don't use /tmp
wget -qO - https://example.com/package.deb -O /tmp/package.deb
sudo apt install /tmp/package.deb
```

### Temporary Working Files

**Rule**: If you need temporary working files during processing, use a project-specific temporary directory.

**Structure**:

```text
data/
└── temp/                # Project temporary files (gitignored)
```

**Examples**:

```bash
# ✅ CORRECT
mkdir -p data/temp
python process.py --temp-dir data/temp

# ❌ WRONG
python process.py --temp-dir /tmp
```

**Note**: Add `data/temp/` to `.gitignore`:

```gitignore
# Temporary working files
data/temp/*
!data/temp/.gitkeep
```

### Backup Files

**Rule**: Project backup archives must be stored in the `backups/` directory at the project root.

**Structure**:

```text
backups/
├── senzing-bootcamp-backup_20260326_143022.zip
├── senzing-bootcamp-backup_20260325_091500.zip
└── README.md            # Backup/restore instructions
```

**Examples**:

```bash
# ✅ CORRECT
backups/senzing-bootcamp-backup_20260326_143022.zip
backups/senzing-bootcamp-backup_20260325_091500.zip

# ❌ WRONG
/tmp/backup.zip
~/Downloads/project-backup.zip
backup.zip              # (in project root)
data/backups/           # (data/backups/ is for database exports, not project backups)
```

**Backup Contents**: Backups include all user data and project files:

- ✅ `database/` - SQLite database files
- ✅ `data/` - All data files (raw, transformed, samples)
- ✅ `licenses/` - Senzing license files
- ✅ `config/` - Configuration files
- ✅ `src/` - Source code
- ✅ `scripts/` - Scripts
- ✅ `docs/` - Documentation

**Backup Exclusions**: Backups automatically exclude:

- ❌ `backups/` - Backup files themselves (prevents recursion)
- ❌ `.git/` - Git repository (use git for version control)
- ❌ `.env` - Environment secrets (use .env.example as template)
- ❌ `data/temp/` - Temporary files
- ❌ `__pycache__/`, `*.pyc` - Python cache files
- ❌ `node_modules/`, `venv/` - Dependencies

**Creating Backups**:

```bash
# Use the backup script
./scripts/backup_project.sh

# Creates: backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip
```

**Restoring Backups**:

```bash
# Restore to current location
./scripts/restore_project.sh backups/senzing-bootcamp-backup_20260326_143022.zip

# Restore to new location
./scripts/restore_project.sh backups/senzing-bootcamp-backup_20260326_143022.zip ~/new-project
```

**Note**: Add `backups/*.zip` to `.gitignore` to exclude backup files from version control:

```gitignore
# Backup files
backups/*.zip
!backups/.gitkeep
!backups/README.md
```

## Rationale

### Why Not Use /tmp?

1. **Persistence**: Files in `/tmp` may be deleted on system reboot
2. **Permissions**: `/tmp` may have different permissions than project directories
3. **Organization**: Project files should stay within project structure
4. **Portability**: Paths like `/tmp` are system-specific
5. **Debugging**: Easier to find and debug files in project directories
6. **Version Control**: Project directories can be properly gitignored
7. **Cleanup**: Easier to clean up project-specific temporary files

### Benefits of Project Directories

1. **Organization**: Clear structure for different file types
2. **Discoverability**: Easy to find files
3. **Version Control**: Proper gitignore rules
4. **Portability**: Works across different systems
5. **Persistence**: Files persist across reboots
6. **Permissions**: Consistent with project permissions
7. **Cleanup**: Clear ownership and cleanup responsibility

## Implementation Guidelines

### For Documentation Writers

When writing documentation that includes file operations:

```bash
# ✅ DO THIS
wget https://example.com/file.deb -O ~/file.deb
python src/transform/transform.py
./scripts/deploy.sh

# ❌ DON'T DO THIS
wget https://example.com/file.deb -O /tmp/file.deb
python /tmp/transform.py
/tmp/deploy.sh
```

### For Code Examples

When providing code examples:

```python
# ✅ DO THIS
output_file = "data/transformed/output.jsonl"
with open(output_file, 'w') as f:
    f.write(json.dumps(record) + '\n')

# ❌ DON'T DO THIS
output_file = "/tmp/output.jsonl"
with open(output_file, 'w') as f:
    f.write(json.dumps(record) + '\n')
```

### For Agent Instructions

When the agent generates code or provides commands:

1. **Always use project directories** for file storage
2. **Never suggest `/tmp`** for any file operations
3. **Use appropriate subdirectories** based on file type
4. **Create directories if needed** with `mkdir -p`
5. **Follow the structure** defined in this policy

## Directory Creation

Always create directories before using them:

```bash
# Create project directories
mkdir -p data/{raw,transformed,samples,backups,temp}
mkdir -p database
mkdir -p licenses
mkdir -p backups
mkdir -p src/{transform,load,query,utils}
mkdir -p scripts
mkdir -p config
mkdir -p docker/scripts
mkdir -p docs/{guides,modules,policies,development}

# Create .gitkeep files to preserve empty directories in git
touch data/raw/.gitkeep
touch data/transformed/.gitkeep
touch database/.gitkeep
touch licenses/.gitkeep
touch backups/.gitkeep
touch docker/.gitkeep
```

## Exceptions

The only files that should be in the project root are:

1. **POWER.md** - Required by Kiro
2. **README.md** - GitHub convention
3. **.env** - Environment variables (gitignored)
4. **.env.example** - Environment template
5. **.gitignore** - Git ignore rules
6. **LICENSE** - License file
7. **requirements.txt** - Python dependencies (if applicable)
8. **package.json** - Node dependencies (if applicable)
9. **pom.xml** / **build.gradle** - Java dependencies (if applicable)
10. **Cargo.toml** - Rust dependencies (if applicable)

**Note**: Docker files (Dockerfile, docker-compose.yml) should NEVER be in the project root - they belong in `docker/`.

## Verification

To verify compliance with this policy:

```bash
# Check for /tmp references in documentation
grep -r "/tmp" senzing-bootcamp/**/*.md

# Check for Docker files in wrong locations
find . -maxdepth 1 -name "Dockerfile*" -o -name "docker-compose*.yml"

# Should return no results - all Docker files should be in docker/
```

## Related Policies

- [MODULE_0_CODE_LOCATION.md](MODULE_0_CODE_LOCATION.md) - Module 0 code placement
- [SHELL_SCRIPT_LOCATIONS.md](SHELL_SCRIPT_LOCATIONS.md) - Shell script placement
- [PYTHON_REQUIREMENTS_POLICY.md](PYTHON_REQUIREMENTS_POLICY.md) - Python package management

## Version History

- **v1.2.0** (2026-03-26): Added `backups/` directory for project backup archives
- **v1.1.0** (2026-03-26): Added `licenses/` directory for Senzing license files
- **v1.0.0** (2026-03-17): Initial file storage policy created

## Enforcement

This policy is enforced through:

1. **Documentation review** - All documentation must follow this policy
2. **Code review** - All code examples must follow this policy
3. **Agent instructions** - Agent is instructed to follow this policy
4. **Automated checks** - Grep searches for policy violations

## Questions?

If you're unsure where to place a file:

1. **Source code?** → `src/`
2. **Shell script?** → `scripts/`
3. **Documentation?** → `docs/`
4. **Data file?** → `data/`
5. **Configuration?** → `config/` or root (for .env)
6. **License file?** → `licenses/`
7. **Backup file?** → `backups/`
8. **Docker file?** → `docker/`
9. **Database file?** → `database/`
10. **Temporary?** → `data/temp/` (not `/tmp`)

When in doubt, ask: "Does this file belong to the project?" If yes, it goes in a project directory. Never use `/tmp`.
