# Docker Quick Start Guide

Get Senzing running in Docker with PostgreSQL in 10 minutes.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- 4GB RAM available
- 10GB disk space

## Quick Start (10 Minutes)

### Step 1: Create Project Directory (1 min)

```bash
mkdir my-senzing-docker
cd my-senzing-docker
mkdir -p docker sql data/raw src/load
```

### Step 2: Create Minimal Schema (2 min)

Create `sql/init-schema.sql`:

```sql
-- Senzing V4.2.1 Minimal Schema for PostgreSQL
-- CRITICAL: Use exact column names shown here

-- System variables (version tracking)
CREATE TABLE IF NOT EXISTS sys_vars (
    var_group VARCHAR(50) NOT NULL,
    var_code VARCHAR(50) NOT NULL,
    var_value TEXT,
    sys_lstupd_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (var_group, var_code)
);

-- Insert required version information
INSERT INTO sys_vars (var_group, var_code, var_value)
VALUES ('SYSTEM', 'VERSION', '4.2.1');

INSERT INTO sys_vars (var_group, var_code, var_value)
VALUES ('SYSTEM', 'SCHEMA_VERSION', '4.0');

-- Configuration table
-- CRITICAL: Column must be sys_create_dt (NOT sys_create_date)
CREATE TABLE IF NOT EXISTS sys_cfg (
    config_data_id BIGSERIAL PRIMARY KEY,
    config_data TEXT NOT NULL,
    config_comments TEXT,
    sys_create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data source tracking
-- CRITICAL: Must include code_id column
CREATE TABLE IF NOT EXISTS sys_codes_used (
    code_type VARCHAR(50) NOT NULL,
    code VARCHAR(50) NOT NULL,
    code_id BIGSERIAL,
    PRIMARY KEY (code_type, code)
);
```

**⚠️ CRITICAL**: Do NOT change column names. The SDK expects these exact names.

### Step 3: Create docker-compose.yml (2 min)

Create `docker/docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: senzing-postgres
    environment:
      POSTGRES_DB: senzing
      POSTGRES_USER: senzing
      POSTGRES_PASSWORD: senzing_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../sql/init-schema.sql:/docker-entrypoint-initdb.d/01-init-schema.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U senzing"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - senzing-network

  senzing:
    image: senzing/senzingsdk-runtime:4.2.1
    container_name: senzing-app
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - SENZING_ENGINE_CONFIGURATION_JSON={"PIPELINE":{"CONFIGPATH":"/etc/opt/senzing","RESOURCEPATH":"/opt/senzing/g2/resources","SUPPORTPATH":"/opt/senzing/data"},"SQL":{"CONNECTION":"postgresql://senzing:senzing_password@postgres:5432/senzing"}}
      - DATABASE_HOST=postgres
      - DATABASE_PORT=5432
      - DATABASE_NAME=senzing
      - DATABASE_USER=senzing
      - DATABASE_PASSWORD=senzing_password
    volumes:
      - ../data:/app/data
      - ../src:/app/src
    command: ["tail", "-f", "/dev/null"]
    networks:
      - senzing-network

volumes:
  postgres_data:

networks:
  senzing-network:
    driver: bridge
```

### Step 4: Start Containers (2 min)

```bash
cd docker
docker-compose up -d

# Wait for containers to be healthy
docker-compose ps

# Check logs
docker-compose logs -f
```

You should see:

```text
senzing-postgres  | database system is ready to accept connections
senzing-app       | (running tail -f /dev/null)
```

### Step 5: Initialize Senzing (2 min)

Create `src/init_database.py`:

```python
#!/usr/bin/env python3
"""Initialize Senzing database via SDK"""

import json
import os
from senzing import SzConfigManager, SzConfig

# Get connection from environment
ENGINE_CONFIG = os.getenv('SENZING_ENGINE_CONFIGURATION_JSON')

def initialize_database():
    """Initialize Senzing database schema and configuration"""

    print("Initializing Senzing database...")

    # Initialize config manager
    config_mgr = SzConfigManager()
    config_mgr.initialize(instance_name="InitDB", settings=ENGINE_CONFIG)

    try:
        # Create configuration from template
        config = SzConfig()
        config.initialize(instance_name="InitConfig", settings=ENGINE_CONFIG)

        config_handle = config.create_config()
        config_json = config.export_config(config_handle)

        # Set as default configuration
        config_id = config_mgr.add_config(
            config_definition=config_json,
            config_comment="Initial Docker setup"
        )
        config_mgr.set_default_config_id(config_id=config_id)

        print(f"✅ Database initialized with config ID: {config_id}")

        config.close_config(config_handle)
        config.destroy()

        return True

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

    finally:
        config_mgr.destroy()

if __name__ == '__main__':
    success = initialize_database()
    exit(0 if success else 1)
```

Run initialization:

```bash
docker-compose exec senzing python /app/src/init_database.py
```

### Step 6: Verify Installation (1 min)

```bash
# Test Senzing SDK
docker-compose exec senzing python -c "import senzing; print(f'Senzing version: {senzing.__version__}')"

# Test database connection
docker-compose exec postgres psql -U senzing -d senzing -c "SELECT * FROM sys_vars;"

# Validate schema
docker-compose exec senzing python /app/src/validate_schema.py \
  --database postgresql \
  --connection "postgresql://senzing:senzing_password@postgres:5432/senzing"
```

You should see:

```text
✅ SCHEMA VALIDATION PASSED!
```

## You're Ready! 🎉

Your Docker environment is now configured and ready for:

- Loading data (Module 6)
- Running queries (Module 8)
- Performance testing (Module 9)

## Next Steps

1. **Load sample data**:

   ```bash
   # Get sample data
   docker-compose exec senzing python -c "
   from senzing_mcp import get_sample_data
   data = get_sample_data('las-vegas', limit=100)
   # Save and load
   "
   ```

2. **Create a loader**:
   - Use MCP server: `generate_scaffold(language="python", workflow="add_records")`
   - Agent generates loading code in `src/load/`
   - Run: `docker-compose exec senzing python /app/src/load/loader.py`

3. **Query results**:
   - Use MCP server: `generate_scaffold(language="python", workflow="full_pipeline")`
   - Agent generates query code in `src/query/`
   - Run: `docker-compose exec senzing python /app/src/query/queries.py`

## Common Issues

### Issue: "Column sys_create_dt does not exist"

**Cause**: Schema has wrong column name (sys_create_date instead of sys_create_dt)

**Fix**:

```bash
docker-compose exec postgres psql -U senzing -d senzing -c \
  "ALTER TABLE sys_cfg RENAME COLUMN sys_create_date TO sys_create_dt;"
```

### Issue: "Column code_id does not exist"

**Cause**: sys_codes_used table missing code_id column

**Fix**:

```bash
docker-compose exec postgres psql -U senzing -d senzing -c \
  "ALTER TABLE sys_codes_used ADD COLUMN code_id BIGSERIAL;"
```

### Issue: Container restarts continuously

**Cause**: CMD exits immediately

**Fix**: Already handled with `tail -f /dev/null` in docker-compose.yml

### Issue: Cannot connect to PostgreSQL

**Cause**: Network or timing issues

**Fix**:

```bash
# Check network
docker network inspect docker_senzing-network

# Check PostgreSQL is ready
docker-compose exec postgres pg_isready -U senzing

# Restart if needed
docker-compose restart
```

### Issue: "Invalid version number"

**Cause**: sys_vars missing version data

**Fix**:

```bash
docker-compose exec postgres psql -U senzing -d senzing -c "
INSERT INTO sys_vars (var_group, var_code, var_value)
VALUES ('SYSTEM', 'VERSION', '4.2.1')
ON CONFLICT DO NOTHING;

INSERT INTO sys_vars (var_group, var_code, var_value)
VALUES ('SYSTEM', 'SCHEMA_VERSION', '4.0')
ON CONFLICT DO NOTHING;
"
```

## Troubleshooting Commands

```bash
# View logs
docker-compose logs -f senzing
docker-compose logs -f postgres

# Check container status
docker-compose ps

# Access PostgreSQL
docker-compose exec postgres psql -U senzing -d senzing

# Access Senzing container
docker-compose exec senzing bash

# Restart services
docker-compose restart

# Stop and remove everything
docker-compose down -v  # WARNING: Deletes data!
```

## Production Considerations

This quick start is for development. For production:

1. **Use secrets management** (not environment variables)
2. **Use persistent volumes** (already configured)
3. **Add resource limits** (CPU, memory)
4. **Add health checks** (already configured)
5. **Use proper networking** (not bridge)
6. **Add monitoring** (Prometheus, Grafana)
7. **Add backup strategy**
8. **Use TLS for PostgreSQL**

See `steering/docker-deployment.md` for production patterns.

## Files Created

After this quick start, you'll have:

```text
my-senzing-docker/
├── docker/
│   └── docker-compose.yml
├── sql/
│   └── init-schema.sql
├── src/
│   ├── init_database.py
│   └── load/
└── data/
    └── raw/
```

## Time Breakdown

- Step 1: Create directories (1 min)
- Step 2: Create schema (2 min)
- Step 3: Create docker-compose (2 min)
- Step 4: Start containers (2 min)
- Step 5: Initialize database (2 min)
- Step 6: Verify (1 min)

### Total: 10 minutes

## Related Documentation

- [docker-deployment.md](../../steering/docker-deployment.md) - Complete Docker guide
- [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md) - SDK installation
- [TROUBLESHOOTING_INDEX.md](TROUBLESHOOTING_INDEX.md) - Common issues

## Version History

- **v1.0.0** (2026-03-17): Docker quick start guide created
