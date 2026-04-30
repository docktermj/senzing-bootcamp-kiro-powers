# File Storage Policy

## Overview

This document defines where different types of files should be stored in the Senzing Bootcamp project structure. Never use system temporary directories for project files.

## Core Principle

**All project files must be stored in appropriate project directories, never in system temporary directories.**

## Core Rules

1. **Never use system temp directories** (`/tmp` on Linux/macOS, `%TEMP%` on Windows) for project files
2. **Source code goes in `src/`** - never in project root
3. **Use project-specific directories** for all file types

## File Storage Rules

### Source Code Files

**Rule**: All source code files (`.py`, `.java`, `.cs`, `.rs`, etc.) must be stored in the `src/` directory.

**Structure**:

```text
src/
├── quickstart_demo/     # Module 3 demo code
├── transform/           # Transformation programs (Module 5)
├── load/                # Loading programs (Module 6)
├── query/               # Query programs (Module 8)
└── utils/               # Shared utilities
```

**Examples**:

```text
# ✅ CORRECT
src/transform/transform_customers.[ext]
src/load/load_customers.[ext]
src/query/find_duplicates.[ext]
src/utils/data_quality_checker.[ext]

# ❌ WRONG (system temp or home directories)
# /tmp/transform.[ext]          (Linux/macOS)
# %TEMP%\transform.[ext]        (Windows)
# ~/Downloads/loader.[ext]
# transform_customers.[ext]     (in project root)
```

### Automation Scripts

**Rule**: All automation scripts (`.py`) must be stored in the `scripts/` directory.

**Structure**:

```text
scripts/
├── backup_project.py    # Project backup
├── restore_project.py   # Project restore
├── status.py            # Bootcamp status
├── check_prerequisites.py # Prerequisites check
├── install_hooks.py     # Hook installer
└── validate_commonmark.py # Markdown validation
```

**Examples**:

```text
# ✅ CORRECT
scripts/backup_project.py
scripts/status.py

# ❌ WRONG
# /tmp/deploy.py
# src/deploy.py           (scripts don't go in src/)
# deploy.py               (in project root)
```

### Documentation Files

**Rule**: All markdown files (`.md`) must be stored in the `docs/` directory or project root (for POWER.md and README.md only).

**Structure**:

```text
docs/
├── guides/              # User-facing guides
├── modules/             # Module documentation
├── policies/            # Policy documents (like this file)
└── feedback/            # User feedback templates
```

**Examples**:

```text
# ✅ CORRECT
docs/guides/QUICK_START.md
docs/modules/MODULE_1_BUSINESS_PROBLEM.md
docs/policies/FILE_STORAGE_POLICY.md
POWER.md                # Exception: required in root
README.md               # Exception: required in root

# ❌ WRONG
# /tmp/guide.md  or  %TEMP%\guide.md
# ~/Documents/module.md
# my_notes.md             (in project root)
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

```text
# ✅ CORRECT
data/raw/customers.csv
data/transformed/customers.jsonl
data/samples/test_data.json
data/backups/senzing_backup_20260317.sql

# ❌ WRONG
# /tmp/customers.csv  or  %TEMP%\customers.csv
# ~/Downloads/data.json
# customers.csv           (in project root)
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

```text
# ✅ CORRECT
database/G2C.db
database/test.db

# ❌ WRONG
# /var/opt/senzing/sqlite/G2C.db
# /tmp/G2C.db  or  %TEMP%\G2C.db
# G2C.db                  (in project root)
# data/G2C.db             (data/ is for data files, not databases)
```

**Note**: Add `database/*.db` to `.gitignore` to exclude database files from version control:

```gitignore
# Database files
database/*.db
database/*.db-journal
!database/.gitkeep
```

**Concurrent bootcamp instances**: Using project-relative paths (`database/G2C.db`) allows multiple bootcamp projects to run on the same machine without conflicts. Never use `/tmp/sqlite/G2C.db` or system-wide paths — if the Senzing MCP server recommends `/tmp/sqlite`, override with the project-local path.

**ExampleEnvironment helper override**: The Senzing SDK's `ExampleEnvironment` helper class creates SQLite databases in `/tmp/` by default (e.g., `/tmp/senzing_test_*.db`). When using `ExampleEnvironment` or any MCP-generated scaffold code, always override the database path to `database/G2C.db`. If the generated code uses `ExampleEnvironment`, replace it with explicit engine configuration pointing to `database/G2C.db`.

**Module 3 demo code**: All code generated during Module 3 (Quick Demo) goes in `src/quickstart_demo/`. Demo scripts use the naming convention `demo_[dataset_name].[ext]` and sample data uses `sample_data_[dataset_name].jsonl`. This keeps demo code separate from production code in `src/transform/`, `src/load/`, and `src/query/`.

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

```text
# ✅ CORRECT
config/senzing_config.json
config/database_config.yaml
.env                    # Exception: in root
.env.example            # Exception: in root

# ❌ WRONG
# /tmp/config.json  or  %TEMP%\config.json
# ~/config.yaml
# senzing_config.json     (in project root, should be in config/)
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

```text
# ✅ CORRECT
licenses/g2.lic
licenses/g2_dev.lic
licenses/g2_prod.lic

# ❌ WRONG
# /etc/opt/senzing/g2.lic
# /tmp/g2.lic  or  %TEMP%\g2.lic
# g2.lic                  (in project root)
# config/g2.lic           (config/ is for configuration, not licenses)
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

### Downloaded Files

**Rule**: Downloaded installation files should be stored in the user's home directory, not system temp directories.

**Examples**:

```text
# ✅ CORRECT - Download to home directory
# Linux/macOS: ~/package.deb
# Windows: %USERPROFILE%\package.msi

# ❌ WRONG - Don't use system temp
# /tmp/package.deb  or  %TEMP%\package.msi
```

### Temporary Working Files

**Rule**: If you need temporary working files during processing, use a project-specific temporary directory.

**Structure**:

```text
data/
└── temp/                # Project temporary files (gitignored)
```

**Examples**:

```text
# ✅ CORRECT
# Use data/temp/ for project-local temporary files

# ❌ WRONG
# Using /tmp or %TEMP% as temp directory violates project organization
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

```text
# ✅ CORRECT
backups/senzing-bootcamp-backup_20260326_143022.zip
backups/senzing-bootcamp-backup_20260325_091500.zip

# ❌ WRONG
# /tmp/backup.zip  or  %TEMP%\backup.zip
# ~/Downloads/project-backup.zip
# backup.zip              (in project root)
# data/backups/           (data/backups/ is for database exports, not project backups)
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
- ❌ Language-specific cache/build artifacts (e.g., `__pycache__/`, `*.pyc`, `target/`, `bin/`, `obj/`, `node_modules/`)
- ❌ `venv/` - Virtual environments / dependencies

**Creating Backups**:

```text
python3 scripts/backup_project.py
```

Creates: `backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip`

**Restoring Backups**:

```text
# Restore to current location
python3 scripts/restore_project.py backups/senzing-bootcamp-backup_20260326_143022.zip

# Restore to new location
python3 scripts/restore_project.py backups/senzing-bootcamp-backup_20260326_143022.zip ~/new-project
```

**Note**: Add `backups/*.zip` to `.gitignore` to exclude backup files from version control:

```gitignore
# Backup files
backups/*.zip
!backups/.gitkeep
!backups/README.md
```

## Rationale

### Why Not Use System Temp Directories?

1. **Persistence**: Files in `/tmp` or `%TEMP%` may be deleted on system reboot
2. **Permissions**: Temp directories may have different permissions than project directories
3. **Organization**: Project files should stay within project structure
4. **Portability**: Paths like `/tmp` are platform-specific and don't exist on Windows
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

```text
# ✅ DO THIS — use project-relative paths
# src/transform/transform.[ext]
# scripts/backup_project.py

# ❌ DON'T DO THIS — never use system temp directories
# /tmp/transform.[ext]  or  %TEMP%\transform.[ext]
```

### For Code Examples

When providing code examples:

```text
# ✅ DO THIS
# Write output to a project-relative path, e.g.:
#   output_file = "data/transformed/output.jsonl"
#   Open the file for writing and append each JSON record followed by a newline.

# ❌ DON'T DO THIS
# Write output to a system temporary path, e.g.:
#   output_file = "/tmp/output.jsonl"
#   Temporary directories are not persistent and violate project organization.
```

### For Agent Instructions

When the agent generates code or provides commands:

1. **Always use project directories** for file storage
2. **Never suggest system temp directories** (`/tmp`, `%TEMP%`) for any file operations
3. **Use appropriate subdirectories** based on file type
4. **Create directories if needed** using `os.makedirs(path, exist_ok=True)` or equivalent
5. **Follow the structure** defined in this policy
6. **Use `os.path.join()`** or `pathlib.Path` for cross-platform path construction

## Directory Creation

Always create directories before using them (cross-platform Python):

```python
import os
dirs = [
    "data/raw", "data/transformed", "data/samples", "data/backups", "data/temp",
    "database", "licenses", "backups",
    "src/transform", "src/load", "src/query", "src/utils",
    "scripts", "config",
    "docs/guides", "docs/modules", "docs/policies", "docs/development",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Create .gitkeep files to preserve empty directories in git
for d in ["data/raw", "data/transformed", "database", "licenses", "backups"]:
    open(os.path.join(d, ".gitkeep"), "a").close()
```

## Exceptions

The only files that should be in the project root are:

1. **POWER.md** - Required by Kiro
2. **README.md** - GitHub convention
3. **.env** - Environment variables (gitignored)
4. **.env.example** - Environment template
5. **.gitignore** - Git ignore rules
6. **LICENSE** - License file
7. **requirements.txt** / **pom.xml** / **Cargo.toml** / **package.json** - Language-specific dependencies (if applicable)
8. **Cargo.toml** - Rust dependencies (if applicable)

## Verification

To verify compliance with this policy, search for system temp directory references:

```python
# Quick check for /tmp or %TEMP% references in documentation
import os
for root, dirs, files in os.walk("senzing-bootcamp"):
    dirs[:] = [d for d in dirs if d not in (".git", ".history", "node_modules")]
    for f in files:
        if f.endswith(".md"):
            path = os.path.join(root, f)
            with open(path) as fh:
                for i, line in enumerate(fh, 1):
                    if "/tmp" in line.lower() or "%temp%" in line.lower():
                        print(f"{path}:{i}: {line.rstrip()}")
```

## Related Policies

- [DEPENDENCY_MANAGEMENT_POLICY.md](DEPENDENCY_MANAGEMENT_POLICY.md) - Dependency management
- [CODE_QUALITY_STANDARDS.md](CODE_QUALITY_STANDARDS.md) - Coding standards
- [SENZING_INFORMATION_POLICY.md](SENZING_INFORMATION_POLICY.md) - MCP-only Senzing facts

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
8. **Database file?** → `database/`
9. **Temporary?** → `data/temp/` (not `/tmp` or `%TEMP%`)

When in doubt, ask: "Does this file belong to the project?" If yes, it goes in a project directory. Never use system temp directories.
