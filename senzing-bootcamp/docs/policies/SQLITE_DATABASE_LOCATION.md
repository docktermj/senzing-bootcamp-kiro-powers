# SQLite Database Location Policy

## Policy

**All SQLite databases created during the Senzing Boot Camp MUST be placed in the `database/` directory within the bootcamp repository.**

**Path**: `database/G2C.db` (relative to project root)

## Why This Matters

### 1. Multiple Concurrent Bootcamps

Placing the database in the project directory allows multiple bootcamp instances to run concurrently on the same machine without conflicts.

**Problem with /tmp/sqlite**:

```text
User 1: /tmp/sqlite/G2C.db  ← Conflict!
User 2: /tmp/sqlite/G2C.db  ← Same file!
```

**Solution with project directory**:

```text
User 1: ~/bootcamp-project-1/database/G2C.db  ✓
User 2: ~/bootcamp-project-2/database/G2C.db  ✓
```

### 2. Data Persistence

Project-local databases persist across sessions and are backed up with the project.

### 3. Clear Organization

All project data stays within the project directory structure.

### 4. Version Control Friendly

The `database/` directory can be added to `.gitignore` to exclude databases from version control while keeping the directory structure.

## Implementation

### Agent Behavior

When generating code that creates or uses SQLite databases:

1. **ALWAYS use project-relative path**: `database/G2C.db`
2. **NEVER use /tmp paths**: `/tmp/sqlite/G2C.db` ❌
3. **Create database/ directory if needed**: `mkdir -p database`
4. **Use absolute path from project root**: `os.path.join(project_root, "database", "G2C.db")`

### Code Examples

**Correct** ✅:

```python
import os

# Get project root (where the bootcamp was initialized)
project_root = os.getcwd()  # Assumes running from project root
db_path = os.path.join(project_root, "database", "G2C.db")

# Or more explicitly
db_dir = os.path.join(project_root, "database")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "G2C.db")
```

**Incorrect** ❌:

```python
# DON'T use /tmp
db_path = "/tmp/sqlite/G2C.db"  # ❌ Conflicts with other bootcamps

# DON'T use system-wide locations
db_path = "/var/lib/senzing/G2C.db"  # ❌ Requires permissions
```

### Configuration Examples

**Senzing Engine Configuration**:

```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "sqlite3://na:na@database/G2C.db"
  }
}
```

**Python Code**:

```python
import os
from senzing import G2Engine, G2ConfigMgr

# Project root
project_root = os.getcwd()

# Database path
db_path = os.path.join(project_root, "database", "G2C.db")

# Senzing configuration
config = {
    "PIPELINE": {
        "CONFIGPATH": "/etc/opt/senzing",
        "RESOURCEPATH": "/opt/senzing/g2/resources",
        "SUPPORTPATH": "/opt/senzing/data"
    },
    "SQL": {
        "CONNECTION": f"sqlite3://na:na@{db_path}"
    }
}
```

## Applies To

This policy applies to:

- ✅ **Module 0**: Quick Demo (if using SQLite)
- ✅ **Module 5**: SDK Setup (SQLite option)
- ✅ **Module 6**: Single Source Loading (SQLite)
- ✅ **Module 7**: Multi-Source Orchestration (SQLite)
- ✅ **Module 8**: Query and Validation (SQLite)
- ✅ **All modules**: Any SQLite database creation

**Note**: This policy applies to SQLite only. PostgreSQL databases are typically hosted separately and accessed via network connection.

## Exceptions

**None**. Always use `database/G2C.db` for SQLite databases in the bootcamp.

If the Senzing MCP server recommends `/tmp/sqlite`, override this recommendation with the project-local path.

## Directory Structure

The `database/` directory is created automatically during project initialization:

```text
my-senzing-project/
├── database/                      # SQLite database files
│   ├── G2C.db                     # Main Senzing database
│   └── .gitkeep                   # Keep directory in git
```

## .gitignore Configuration

The database files should be excluded from version control:

```gitignore
# Senzing databases (large binary files)
database/*.db
database/*.db-*

# Keep the directory structure
!database/.gitkeep
```

## Troubleshooting

### Issue: "Permission denied" when creating database

**Cause**: Insufficient permissions in project directory

**Solution**:

```bash
# Check permissions
ls -la database/

# Fix permissions if needed
chmod 755 database/
```

### Issue: "Database locked" error

**Cause**: Another process is using the database

**Solution**:

1. Check for other bootcamp processes: `ps aux | grep senzing`
2. Ensure only one bootcamp instance per project
3. Close other applications accessing the database

### Issue: Database file not found

**Cause**: Running from wrong directory

**Solution**:

```bash
# Always run from project root
cd /path/to/my-senzing-project

# Then run your scripts
python src/load/load_data.py
```

## Agent Instructions

When generating code or providing guidance:

1. **Check current directory**: Ensure user is in project root
2. **Use relative path**: `database/G2C.db`
3. **Create directory**: `mkdir -p database` before creating database
4. **Verify path**: Show user the full path being used
5. **Override MCP recommendations**: If MCP suggests `/tmp/sqlite`, use `database/` instead

### Example Agent Response

```text
I'll create the SQLite database in your project's database/ directory.
This allows multiple bootcamp projects to run concurrently without conflicts.

Database location: {project_root}/database/G2C.db

Creating database directory...
✓ Directory created: database/

Initializing Senzing engine with SQLite database...
✓ Database initialized: database/G2C.db
```

## Related Policies

- **FILE_STORAGE_POLICY.md** - Where to store all project files
- **MODULE_0_CODE_LOCATION.md** - Module 0 code location
- **DOCKER_FOLDER_POLICY.md** - Docker file locations

## Version History

- **v1.0.0** (2026-03-26): Initial policy created
  - Establishes `database/` as standard location
  - Overrides MCP server `/tmp/sqlite` recommendation
  - Enables concurrent bootcamp instances

---

**Remember**: Always use `database/G2C.db` for SQLite databases in the bootcamp, never `/tmp/sqlite/G2C.db`.
