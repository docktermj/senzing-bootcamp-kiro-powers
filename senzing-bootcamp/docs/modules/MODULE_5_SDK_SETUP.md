# Module 5: Set Up SDK

## Overview

Module 5 installs and configures the Senzing SDK, setting up the foundation for loading data and performing entity resolution. You'll choose a database, configure the engine, and verify everything works.

**Time**: 30 minutes - 1 hour  
**Prerequisites**: ✅ Module 4 complete (data mapped) OR all sources are SGES-compliant  
**Output**: Installed SDK, configured database, verified installation

## Learning Objectives

By the end of this module, you will:
- Understand Senzing SDK components
- Install Senzing on your platform
- Configure a database (SQLite or PostgreSQL)
- Register data sources
- Verify the installation works

## What You'll Do

1. Check if Senzing is already installed
2. Choose your platform (if not installed)
3. Install Senzing SDK (if needed)
4. Choose and configure database
5. Register data sources
6. Test the installation
7. Create configuration documentation

## Senzing SDK Components

### Core Components

**G2Engine**: Main entity resolution engine
- Load records
- Resolve entities
- Query results
- Export data

**G2Config**: Configuration management
- Register data sources
- Configure matching rules
- Manage entity types

**G2Product**: Product information
- Version info
- License details
- Capabilities

**G2Diagnostic**: System diagnostics
- Check database
- Verify configuration
- Performance metrics

## Installation Check

Before installing, check if Senzing is already installed:

### Python Check
```bash
python -c "import senzing; print('Senzing version:', senzing.__version__)" 2>/dev/null
```

### System Check (Linux/macOS)
```bash
# Check installation directory
ls -la /opt/senzing 2>/dev/null
ls -la /etc/opt/senzing 2>/dev/null

# Check Python package
pip list | grep senzing
```

### Docker Check
```bash
docker images | grep senzing
```

If Senzing is found:
- Verify version is V4.0
- Skip to "Configure Database" section
- If version is not V4.0, proceed with installation

## Platform Selection

Choose your installation platform:

### Option 1: Docker (Recommended for Quick Start)
**Pros**:
- No system installation required
- Isolated environment
- Easy cleanup
- Cross-platform

**Cons**:
- Requires Docker installed
- Slightly slower than native
- Additional layer of complexity

**Best for**: Evaluation, development, testing

### Option 2: Linux (Native)
**Pros**:
- Best performance
- Direct system access
- Production-ready

**Cons**:
- Requires system permissions
- Platform-specific installation
- More complex setup

**Best for**: Production deployments, high-performance needs

### Option 3: macOS (Native)
**Pros**:
- Native performance
- Good for development

**Cons**:
- Limited to development use
- Not recommended for production

**Best for**: Development on Mac

### Option 4: Windows (WSL2)
**Pros**:
- Works on Windows
- Linux compatibility

**Cons**:
- Requires WSL2 setup
- Performance overhead

**Best for**: Development on Windows

## Installation Steps

### Docker Installation

```bash
# Pull Senzing image
docker pull senzing/senzing-tools:latest

# Verify installation
docker run senzing/senzing-tools:latest \
  python -c "import senzing; print(senzing.__version__)"

# Create persistent volume for data
docker volume create senzing-data
```

### Linux Installation (apt-based)

```bash
# Add Senzing repository
wget -qO - https://senzing-production-apt.s3.amazonaws.com/senzingrepo_1.0.0-1_amd64.deb \
  -O ~/senzingrepo_1.0.0-1_amd64.deb
sudo apt install ~/senzingrepo_1.0.0-1_amd64.deb

# Update package list
sudo apt update

# Install Senzing
sudo apt install senzingapi-runtime senzingapi-setup

# Accept EULA during installation
```

### Linux Installation (yum-based)

```bash
# Add Senzing repository
sudo yum install https://senzing-production-yum.s3.amazonaws.com/senzingrepo-1.0.0-1.x86_64.rpm

# Install Senzing
sudo yum install senzingapi-runtime senzingapi-setup

# Accept EULA during installation
```

### macOS Installation

```bash
# Install via Homebrew
brew tap senzing/senzingapi
brew install senzing-api

# Or download from Senzing website
# https://senzing.com/download/
```

### Python Package Installation

After system installation:

```bash
# Install Python SDK
pip install senzing

# Verify installation
python -c "import senzing; print(senzing.__version__)"
```

## Database Configuration

### Option 1: SQLite (Evaluation)

**Pros**:
- No setup required
- File-based (portable)
- Good for < 100K records

**Cons**:
- Limited performance (20-50 records/sec)
- Not suitable for production
- No concurrent writes

**Setup**:
```bash
# Create database directory
mkdir -p database
```

**Configuration**:
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

### Option 2: PostgreSQL (Production)

**Pros**:
- High performance (100-1000+ records/sec)
- Concurrent access
- Production-ready
- Scalable

**Cons**:
- Requires PostgreSQL installation
- More complex setup
- Additional cost

**Installation**:
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE senzing;
CREATE USER senzing WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE senzing TO senzing;
\q
```

**Configuration**:
```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "postgresql://senzing:your_password@localhost:5432/senzing"
  }
}
```

## Register Data Sources

Register each data source identified in Module 1:

```python
#!/usr/bin/env python3
"""
Register data sources with Senzing
"""

import json
from senzing import G2Config, G2ConfigMgr, G2Engine

def register_data_sources():
    """Register all data sources"""
    
    # Initialize config
    config = G2Config()
    config.init("RegisterDataSources", "{}", False)
    
    # Get current config
    config_handle = config.create()
    
    # Register data sources
    data_sources = [
        "CUSTOMERS",
        "VENDORS",
        "EMPLOYEES"
    ]
    
    for ds in data_sources:
        config.addDataSource(config_handle, json.dumps({
            "DSRC_CODE": ds
        }))
        print(f"Registered data source: {ds}")
    
    # Save config
    config_str = config.save(config_handle)
    
    # Apply config
    config_mgr = G2ConfigMgr()
    config_mgr.init("ConfigMgr", "{}", False)
    config_id = config_mgr.addConfig(config_str, "Initial config")
    config_mgr.setDefaultConfigID(config_id)
    
    print(f"Configuration saved with ID: {config_id}")
    
    # Cleanup
    config.close(config_handle)
    config.destroy()
    config_mgr.destroy()

if __name__ == '__main__':
    register_data_sources()
```

## Verify Installation

Create a test script to verify everything works:

```python
#!/usr/bin/env python3
"""
Verify Senzing installation
"""

import json
from senzing import G2Engine, G2Product

def verify_installation():
    """Test Senzing installation"""
    
    print("="*60)
    print("SENZING INSTALLATION VERIFICATION")
    print("="*60)
    
    # Check version
    product = G2Product()
    product.init("VerifyInstall", "{}", False)
    version = product.version()
    print(f"\n✅ Senzing version: {version}")
    product.destroy()
    
    # Test engine initialization
    engine = G2Engine()
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
    
    try:
        engine.init("VerifyInstall", json.dumps(config), False)
        print("✅ Engine initialized successfully")
        
        # Test database connection
        stats = engine.stats()
        print("✅ Database connection successful")
        print(f"   Stats: {stats}")
        
        # Test adding a record
        test_record = {
            "DATA_SOURCE": "TEST",
            "RECORD_ID": "TEST-001",
            "NAME_FULL": "Test Person"
        }
        
        engine.addRecord("TEST", "TEST-001", json.dumps(test_record))
        print("✅ Test record added successfully")
        
        # Test querying
        result = engine.getRecord("TEST", "TEST-001")
        print("✅ Test record retrieved successfully")
        
        # Cleanup test record
        engine.deleteRecord("TEST", "TEST-001")
        print("✅ Test record deleted successfully")
        
        engine.destroy()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✅")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n" + "="*60)
        print("TESTS FAILED ❌")
        print("="*60)
        return False

if __name__ == '__main__':
    verify_installation()
```

Run the verification:
```bash
python src/utils/verify_installation.py
```

## Configuration Documentation

Create `docs/sdk_configuration.md`:

```markdown
# Senzing SDK Configuration

**Date**: 2026-03-17
**Version**: 4.0.0
**Platform**: Linux (Ubuntu 22.04)
**Database**: PostgreSQL 14

## Installation Details

**Installation method**: apt package
**Installation path**: /opt/senzing
**Configuration path**: /etc/opt/senzing
**Data path**: /var/opt/senzing

## Database Configuration

**Type**: PostgreSQL
**Host**: localhost
**Port**: 5432
**Database**: senzing
**User**: senzing

**Connection string**:
```
postgresql://senzing:***@localhost:5432/senzing
```

## Registered Data Sources

1. CUSTOMERS (500,000 records)
2. VENDORS (50,000 records)
3. EMPLOYEES (10,000 records)

## Environment Variables

```bash
export SENZING_ENGINE_CONFIG_JSON='{"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing"},"SQL":{"CONNECTION":"postgresql://senzing:***@localhost:5432/senzing"}}'
```

## Performance Settings

- Max threads: 8
- Batch size: 1000
- Cache size: 2GB

## Verification

Installation verified on 2026-03-17:
- ✅ Version check passed
- ✅ Engine initialization passed
- ✅ Database connection passed
- ✅ Record operations passed
```

## Environment Variables

Create `.env` file (never commit to git):

```bash
# Senzing Configuration
SENZING_ENGINE_CONFIG_JSON='{"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing","RESOURCEPATH":"/opt/senzing/g2/resources","SUPPORTPATH":"/opt/senzing/data"},"SQL":{"CONNECTION":"postgresql://senzing:your_password@localhost:5432/senzing"}}'

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=senzing
DATABASE_USER=senzing
DATABASE_PASSWORD=your_password
SQLITE_DATABASE_PATH=database/G2C.db

# Paths
SENZING_CONFIG_PATH=/etc/opt/senzing
SENZING_RESOURCE_PATH=/opt/senzing/g2/resources
SENZING_SUPPORT_PATH=/opt/senzing/data
```

Create `.env.example` (safe to commit):

```bash
# Senzing Configuration
SENZING_ENGINE_CONFIG_JSON='{"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing"},"SQL":{"CONNECTION":"postgresql://senzing:PASSWORD@localhost:5432/senzing"}}'

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=senzing
DATABASE_USER=senzing
DATABASE_PASSWORD=your_password_here

# Paths
SENZING_CONFIG_PATH=/etc/opt/senzing
SENZING_RESOURCE_PATH=/opt/senzing/g2/resources
SENZING_SUPPORT_PATH=/opt/senzing/data
```

## Success Criteria

✅ Senzing SDK installed (or existing installation verified)  
✅ Database configured and tested  
✅ Data sources registered  
✅ Verification script passes all tests  
✅ Configuration documented  
✅ Environment variables set

## Common Issues

**Issue: Permission denied during installation**
- Use `sudo` for system installation
- Check user permissions

**Issue: Database connection fails**
- Verify PostgreSQL is running
- Check connection string
- Verify user permissions

**Issue: Import error in Python**
- Verify Python package installed: `pip list | grep senzing`
- Check Python version (3.8+)
- Verify PYTHONPATH if needed

**Issue: Configuration not found**
- Check CONFIGPATH in engine config
- Verify /etc/opt/senzing exists
- Run senzing-setup if needed

## Tips for Success

1. **Check first**: Always check if Senzing is already installed
2. **Start with SQLite**: Use SQLite for initial testing
3. **Upgrade to PostgreSQL**: Switch to PostgreSQL for production
4. **Document everything**: Save configuration details
5. **Test thoroughly**: Run verification script before proceeding

## Next Steps

After completing Module 5:
- **Proceed to Module 6**: Load your first data source
- **Review configuration**: Ensure all settings are correct

## Related Documentation

- `POWER.md` - Boot camp overview
- `steering/steering.md` - Module 5 detailed workflow
- `steering/environment-setup.md` - Environment setup guide
- Senzing installation docs (use `search_docs` MCP tool)

## Version History

- **v3.0.0** (2026-03-17): Module 5 documentation created
