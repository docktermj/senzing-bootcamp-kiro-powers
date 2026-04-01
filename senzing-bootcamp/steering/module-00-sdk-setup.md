---
inclusion: manual
---

# Module 0: SDK Installation and Configuration

Install and configure the Senzing SDK natively on your machine. This is the first step of the boot camp — once the SDK is installed, all subsequent modules use it directly.

**Time**: 30 minutes - 1 hour

**Prerequisites**: None (this is the first module)

## Step 1: Check for Existing Installation

Before installing, check if Senzing is already present:

```bash
python3 -c "import senzing; print('Senzing version:', senzing.__version__)" 2>/dev/null
```

If Senzing is found:

- Verify the version is compatible (V4.0+)
- If compatible, skip to Step 4 (verify installation)
- If incompatible or broken, proceed with installation

## Step 2: Determine Platform

Ask: "What platform are you using? Linux, macOS, or Windows?"

WAIT for response before proceeding.

Use `sdk_guide` with `topic='install'` and the user's platform to get current installation commands. The MCP server always has the latest instructions.

**Platform options for `sdk_guide`**:

- `platform='linux_apt'` — Ubuntu/Debian
- `platform='linux_yum'` — RHEL/CentOS/Fedora
- `platform='macos_arm'` — macOS (Apple Silicon)
- `platform='windows'` — Windows

## Step 3: Install Senzing SDK

Follow the platform-specific instructions from `sdk_guide`. The typical flow:

1. Add the Senzing package repository
2. Install the Senzing SDK package
3. Accept the EULA
4. Install the Python bindings: `pip install senzing`

**Before recommending any approach**, call `search_docs` with `category='anti_patterns'` to check for known pitfalls on the user's platform.

## Step 4: Verify Installation

Run a verification script:

```python
#!/usr/bin/env python3
"""Verify Senzing SDK installation."""

import senzing
from senzing import SzEngine

print(f"Senzing version: {senzing.__version__}")

try:
    engine = SzEngine()
    print("✅ Senzing engine initialized successfully")
    engine.destroy()
except Exception as e:
    print(f"❌ Error initializing engine: {e}")
```

If verification fails, use `explain_error_code` for any SENZ error codes and `search_docs` for troubleshooting.

## Step 5: Create Project Directory Structure

Follow the directory creation commands from the agent-instructions steering file. This creates the organized project layout (`data/`, `database/`, `src/`, `docs/`, etc.) that all subsequent modules use.

After creation, inform the user: "I've set up the project directory structure. All files will be organized properly throughout the boot camp."

## Step 6: Configure Database

Ask: "Which database would you like to use? SQLite is recommended for learning and evaluation. PostgreSQL is better for production."

WAIT for response.

**For SQLite** (recommended for boot camp):

- Create the database directory: `mkdir -p database`
- Database path: `database/G2C.db`
- No additional setup needed — SQLite is built in

**For PostgreSQL** (production):

- User needs PostgreSQL installed and running
- Create a database for Senzing
- Use `sdk_guide` with `topic='configure'` for PostgreSQL setup

## Step 7: Create Engine Configuration

> **Agent instruction:** Do not use the example JSON below. Use
> `sdk_guide(topic='configure', platform='<user_platform>', language='python', version='current')`
> to get the correct engine configuration for the user's platform. The MCP server provides
> correct paths and catches anti-patterns.

Use `sdk_guide` with `topic='configure'` to generate the correct engine configuration JSON for the user's platform and database choice. Save it to `config/engine_config.json`.

## Step 8: Test Database Connection

> **Agent instruction:** Use `generate_scaffold(language='python', workflow='initialize', version='current')`
> to get the current V4 initialization and connection test pattern.

Use the MCP-generated initialization code to verify the database connection works.

## Success Criteria

- ✅ Senzing SDK installed natively
- ✅ `import senzing` works in Python
- ✅ Engine initializes without errors
- ✅ Database connection works
- ✅ Project directory structure created

## Transition

Once the SDK is installed and verified, proceed to:

- **Module 1** (Quick Demo) — see the SDK in action with sample data
- **Module 2** (Business Problem) — start working with your own data

## Troubleshooting

- Installation fails? Use `explain_error_code` for SENZ errors
- Platform not supported? Use `search_docs` for alternative installation methods
- Database errors? Check `docs/policies/SQLITE_DATABASE_LOCATION.md` for path requirements
- Permission issues? Ensure you have admin/sudo access for installation
- Missing dependencies? Run `./scripts/check_prerequisites.sh`

## Agent Behavior

- Always check for existing installation first
- Do NOT offer alternatives — install the SDK natively
- Use `sdk_guide` MCP tool for current platform-specific instructions
- Use `search_docs` with `category='anti_patterns'` before recommending approaches
- Recommend SQLite for evaluation, PostgreSQL for production
- Always use `database/G2C.db` for SQLite (never `/tmp/sqlite`)
- Verify installation before proceeding to Module 1
