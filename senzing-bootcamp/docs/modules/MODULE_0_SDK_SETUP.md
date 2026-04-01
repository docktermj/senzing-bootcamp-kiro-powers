# Module 0: Set Up SDK

## Overview

Module 0 installs and configures the Senzing SDK natively on your machine. This is the first step of the boot camp — once the SDK is installed, all subsequent modules use it directly.

**Time:** 30 minutes - 1 hour
**Prerequisites:** None (this is the first module)
**Output:** Installed SDK, configured database, verified installation

## Learning Objectives

By the end of this module, you will:

- Install the Senzing SDK on your platform
- Configure a database (SQLite or PostgreSQL)
- Verify the installation works
- Create the project directory structure

## What You'll Do

1. Check if Senzing is already installed
2. Install Senzing SDK natively
3. Choose and configure database
4. Create project directory structure
5. Test the installation

## Installation Check

Before installing, check if Senzing is already present:

```bash
python3 -c "import senzing; print('Senzing version:', senzing.__version__)" 2>/dev/null
```

```bash
# Check installation directory (Linux/macOS)
ls -la /opt/senzing 2>/dev/null
ls -la /etc/opt/senzing 2>/dev/null

# Check Python package
pip list | grep senzing
```

If Senzing is found:

- Verify version is V4.0+
- Skip to "Database Configuration" section
- If version is incompatible, proceed with installation

## Senzing License Requirements

A valid Senzing license is required to install and use the SDK.

### Obtaining a License

**Evaluation License (Recommended for Boot Camp):**

- Email: <support@senzing.com>
- Mention: "Requesting evaluation license for Senzing Boot Camp"
- Response time: 1-2 business days
- Valid for 30-90 days

**Production License:**

- Email: <sales@senzing.com>
- Pricing based on data source records (DSRs)

**Install License:**

```bash
cp /path/to/downloaded/g2.lic licenses/g2.lic
chmod 644 licenses/g2.lic
```

Senzing checks licenses in order: `licenses/g2.lic` → `SENZING_LICENSE_PATH` env var → `/etc/opt/senzing/g2.lic`

See `licenses/README.md` for complete licensing information.

## Platform Installation

Use `sdk_guide` MCP tool with your platform for current installation commands.

### Linux (apt-based: Ubuntu/Debian)

```bash
# Add Senzing repository and install
# Use sdk_guide(topic='install', platform='linux_apt') for current commands
sudo apt update
sudo apt install senzingapi-runtime senzingapi-setup
```

### Linux (yum-based: RHEL/CentOS/Fedora)

```bash
# Use sdk_guide(topic='install', platform='linux_yum') for current commands
sudo yum install senzingapi-runtime senzingapi-setup
```

### macOS

```bash
# Use sdk_guide(topic='install', platform='macos_arm') for current commands
brew tap senzing/senzingapi
brew install senzing-api
```

### Python Package

After system installation:

```bash
pip install senzing
python3 -c "import senzing; print(senzing.__version__)"
```

## Database Configuration

### SQLite (Recommended for Boot Camp)

No setup required — SQLite is built in and file-based.

```bash
mkdir -p database
```

Configuration:

```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/er/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "sqlite3://na:na@database/G2C.db"
  }
}
```

### PostgreSQL (Production)

For production workloads with higher performance needs:

```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql
CREATE DATABASE senzing;
CREATE USER senzing WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE senzing TO senzing;
\q
```

Configuration:

```json
{
  "SQL": {
    "CONNECTION": "postgresql://senzing:your_password@localhost:5432/senzing"
  }
}
```

## Verify Installation

```python
#!/usr/bin/env python3
"""Verify Senzing installation."""

import json
from senzing import SzEngine

config = {
    "PIPELINE": {
        "CONFIGPATH": "/etc/opt/senzing",
        "RESOURCEPATH": "/opt/senzing/er/resources",
        "SUPPORTPATH": "/opt/senzing/data"
    },
    "SQL": {
        "CONNECTION": "sqlite3://na:na@database/G2C.db"
    }
}

try:
    engine = SzEngine()
    engine.initialize("VerifyInstall", json.dumps(config), False)
    print("✅ Engine initialized successfully")
    print("✅ Database connection successful")
    engine.destroy()
    print("\nAll tests passed ✅")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Success Criteria

- ✅ Senzing SDK installed natively
- ✅ `import senzing` works in Python
- ✅ Database configured and tested
- ✅ Project directory structure created
- ✅ Verification script passes

## Common Issues

- **Permission denied**: Use `sudo` for system installation
- **Database connection fails**: Verify database path exists (`mkdir -p database`)
- **Import error**: Verify `pip install senzing` completed, check Python 3.10+
- **Configuration not found**: Check CONFIGPATH, verify `/etc/opt/senzing` exists

## Next Steps

- **Module 1** (Quick Demo) — See the SDK in action with sample data
- **Module 2** (Business Problem) — Start working with your own data

## Related Documentation

- `licenses/README.md` — Licensing details
- `docs/policies/SQLITE_DATABASE_LOCATION.md` — Database path policy
- Use `sdk_guide` MCP tool for platform-specific instructions
