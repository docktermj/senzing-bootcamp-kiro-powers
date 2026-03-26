# SQLite Database Location Update

## Overview

Updated all SQLite database references to use the project-local `database/` directory instead of system paths like `/var/opt/senzing/sqlite/`.

**Date**: 2026-03-17
**Change Type**: File Storage Policy Enhancement

## Rationale

### Why Change?

1. **Project Isolation**: Database files should be part of the project structure
2. **Portability**: Easier to move projects between systems
3. **Permissions**: No need for system-level permissions
4. **Consistency**: Aligns with file storage policy (no system directories)
5. **Backup Simplicity**: Database is in project directory for easy backup
6. **Development Workflow**: Easier to manage multiple projects

### Old Approach (System Path)

```bash
# Old SQLite path
/var/opt/senzing/sqlite/G2C.db

# Issues:
- Requires system permissions
- Not portable
- Shared across projects
- Hard to backup with project
```

### New Approach (Project Path)

```bash
# New SQLite path
database/G2C.db

# Benefits:
- No special permissions needed
- Portable with project
- Isolated per project
- Easy to backup
- Follows file storage policy
```

## Changes Made

### 1. Updated Connection Strings

Changed all SQLite connection strings from:

```json
"CONNECTION": "sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db"
```

To:

```json
"CONNECTION": "sqlite3://na:na@database/G2C.db"
```

### 2. Updated Backup Scripts

Changed backup scripts to use project paths:

```bash
# Old
cp /var/opt/senzing/sqlite/G2C.db "$BACKUP_DIR/G2C_$DATE.db"

# New
cp database/G2C.db "$BACKUP_DIR/G2C_$DATE.db"
```

### 3. Updated Documentation

Updated all documentation to reference `database/G2C.db` instead of system paths.

### 4. Added Database Directory to Project Structure

Updated project structure in POWER.md:

```text
my-senzing-project/
├── database/                      # SQLite database files
│   ├── G2C.db                     # Main Senzing database
│   └── .gitkeep                   # Keep directory in git
```

### 5. Updated .gitignore

Added database-specific gitignore rules:

```gitignore
# Database files
database/*.db
database/*.db-journal
!database/.gitkeep
```

### 6. Updated File Storage Policy

Added new section for database files:

- Rule: SQLite databases must be stored in `database/` directory
- Examples of correct and incorrect usage
- Gitignore guidance

### 7. Updated Agent Instructions

Added to Core Principles:

- SQLite databases → `database/`
- Never use system paths for SQLite databases

Added to Module 5 instructions:

- Create `database/` directory for SQLite
- Use `database/G2C.db` path in connection strings

## Files Modified

### Documentation Files

1. `senzing-bootcamp/docs/modules/MODULE_5_SDK_SETUP.md`
   - Updated SQLite configuration section
   - Updated verification script
   - Updated environment variables

2. `senzing-bootcamp/docs/policies/FILE_STORAGE_POLICY.md`
   - Added "Database Files" section
   - Added examples and gitignore rules
   - Updated directory creation commands

3. `senzing-bootcamp/POWER.md`
   - Updated project directory structure
   - Added database/ directory

### Steering Files

1. `senzing-bootcamp/steering/steering.md`
   - Updated all SQLite connection strings (3 occurrences)
   - Updated .env.example
   - Updated .gitignore template

2. `senzing-bootcamp/steering/agent-instructions.md`
   - Added database/ to Core Principles
   - Added Module 5 guidance for SQLite paths

3. `senzing-bootcamp/steering/environment-setup.md`
   - Updated .env.example
   - Updated .gitignore template

4. `senzing-bootcamp/steering/recovery-procedures.md`
   - Updated backup script
   - Updated rollback script

5. `senzing-bootcamp/steering/disaster-recovery.md`
   - Updated SQLite backup procedures
   - Updated restore procedures
   - Updated .gitignore example

6. `senzing-bootcamp/steering/troubleshooting-decision-tree.md`
   - Updated database path checks
   - Updated troubleshooting commands

### Example Files

1. `senzing-bootcamp/examples/simple-single-source/README.md`
    - Updated troubleshooting section

## Migration Guide

### For Existing Projects

If you have an existing project using the old system path:

1. **Create database directory**:

   ```bash
   mkdir -p database
   ```

2. **Copy existing database** (if it exists):

   ```bash
   cp /var/opt/senzing/sqlite/G2C.db database/G2C.db
   ```

3. **Update connection strings** in your code:

   ```python
   # Old
   "CONNECTION": "sqlite3://na:na@/var/opt/senzing/sqlite/G2C.db"

   # New
   "CONNECTION": "sqlite3://na:na@database/G2C.db"
   ```

4. **Update .gitignore**:

   ```gitignore
   # Database files
   database/*.db
   database/*.db-journal
   !database/.gitkeep
   ```

5. **Create .gitkeep**:

   ```bash
   touch database/.gitkeep
   ```

### For New Projects

New projects will automatically use the `database/` directory:

1. Directory is created during Module 1 setup
2. Connection strings use `database/G2C.db` by default
3. .gitignore includes database rules
4. Backup scripts use project paths

## Testing

To verify the changes work correctly:

1. **Create database directory**:

   ```bash
   mkdir -p database
   ```

2. **Test connection**:

   ```python
   import json
   from senzing import G2Engine

   config = {
       "PIPELINE": {
           "CONFIGPATH": "/etc/opt/senzing",
           "RESOURCEPATH": "/opt/senzing/g2/resources",
           "SUPPORTPATH": "/opt/senzing/data"
       },
       "SQL": {
           "CONNECTION": "sqlite3://na:na@database/G2C.db"
       }
   }

   engine = G2Engine()
   engine.init("TestApp", json.dumps(config), False)
   print("✅ Database connection successful")
   engine.destroy()
   ```

3. **Verify database file created**:

   ```bash
   ls -lh database/G2C.db
   ```

## Benefits

1. **Portability**: Projects can be moved between systems easily
2. **Isolation**: Each project has its own database
3. **Simplicity**: No system permissions needed
4. **Consistency**: Follows file storage policy
5. **Backup**: Database backed up with project
6. **Development**: Easier to manage multiple projects
7. **Git-friendly**: Database excluded but directory preserved

## Notes

- PostgreSQL connections are unchanged (still use network connection strings)
- System Senzing installation paths remain unchanged (`/opt/senzing`, `/etc/opt/senzing`)
- Only SQLite database file location changed
- Existing system databases can be copied to project directory

## Related Documentation

- [FILE_STORAGE_POLICY.md](../policies/FILE_STORAGE_POLICY.md) - Complete file storage rules
- [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md) - SDK setup with new paths
- [recovery-procedures.md](../../steering/recovery-procedures.md) - Backup with new paths
- [disaster-recovery.md](../../steering/disaster-recovery.md) - DR with new paths

## Version History

- **v1.0.0** (2026-03-17): Initial documentation of SQLite database location update
