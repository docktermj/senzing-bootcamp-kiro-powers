---
inclusion: manual
---

# Docker Deployment Guide

This guide covers deploying Senzing in Docker containers, based on real-world deployment experience.

## When to Use Docker

### Use Docker When

- Deploying to cloud platforms (AWS ECS, Azure Container Instances, GCP Cloud Run)
- Need consistent environments across dev/staging/prod
- Want easy scaling and orchestration (Kubernetes)
- Prefer containerized microservices architecture
- Need isolation from host system

### Use Local Installation When

- Maximum performance is critical
- Simple single-server deployment
- Direct system access required
- Learning/development on local machine

## Critical Docker Considerations

### 1. Runtime Image Limitations

**IMPORTANT**: The Senzing runtime Docker image (`senzing/senzingsdk-runtime:4.2.1`) does NOT include PostgreSQL schema files.

**What This Means**:

- You cannot use `/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql` (it doesn't exist in the image)
- You must use SDK-based initialization instead
- Schema files are only in full SDK installations, not runtime images

**Solution**: Use the SDK initialization approach (see below)

### 2. Database Initialization Pattern

For Docker deployments with PostgreSQL, use this two-stage initialization:

#### Stage 1: Minimal Schema (SQL)

```sql
-- Create just enough for SDK to work
-- CRITICAL: Use exact column names expected by SDK

CREATE TABLE sys_vars (
    var_group VARCHAR(50),
    var_code VARCHAR(50),
    var_value TEXT,
    sys_lstupd_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (var_group, var_code)
);

-- Set version info (CRITICAL - SDK checks these)
INSERT INTO sys_vars VALUES ('SYSTEM', 'VERSION', '4.2.1');
INSERT INTO sys_vars VALUES ('SYSTEM', 'SCHEMA_VERSION', '4.0');

-- Create config tables
-- CRITICAL: Column must be sys_create_dt (NOT sys_create_date)
CREATE TABLE sys_cfg (
    config_data_id BIGSERIAL PRIMARY KEY,
    config_data TEXT NOT NULL,
    config_comments TEXT,
    sys_create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Must be sys_create_dt
);

CREATE TABLE sz_cfg_config (
    config_id BIGINT PRIMARY KEY,
    config_data TEXT,
    config_comments TEXT,
    sys_create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CRITICAL: Must include code_id column for SDK queries
CREATE TABLE sys_codes_used (
    code_type VARCHAR(50),
    code VARCHAR(50),
    code_id BIGSERIAL,  -- Required by SDK
    PRIMARY KEY (code_type, code_value)
);
```

**Critical Schema Requirements**:

1. **sys_cfg.sys_create_dt** (NOT sys_create_date)
   - Error if wrong: `SENZ1001|Critical Database Error '(7:42703ERROR: column "sys_create_dt" of relation "sys_cfg" does not exist`
   - The SDK specifically looks for `sys_create_dt`

2. **sys_codes_used.code_id** (must be present)
   - Error if missing: `SENZ1001|Critical Database Error '(7:42703ERROR: column "code_id" does not exist`
   - The SDK queries: `SELECT CODE_TYPE,CODE,CODE_ID FROM SYS_CODES_USED`

3. **sys_vars structure** (var_group, var_code, var_value)
   - Must use this exact structure for version checking to work

#### Stage 2: SDK Initialization (Python)

```python
#!/usr/bin/env python3
"""Initialize Senzing database via SDK"""

import json
from senzing import SzConfigManager, SzConfig

def initialize_database():
    """Initialize Senzing database schema and configuration"""

    # Initialize config manager
    config_mgr = SzConfigManager()
    config_mgr.initialize(instance_name="InitDB", settings=ENGINE_CONFIG)

    try:
        # Create configuration from template
        # This creates all remaining tables automatically
        config = SzConfig()
        config.initialize(instance_name="InitConfig", settings=ENGINE_CONFIG)

        config_handle = config.create_config()
        config_json = config.export_config(config_handle)

        # Set as default configuration
        # This populates the database with initial config
        config_id = config_mgr.add_config(
            config_definition=config_json,
            config_comment="Initial Docker setup"
        )
        config_mgr.set_default_config_id(config_id=config_id)

        print(f"✅ Database initialized with config ID: {config_id}")

        config.close_config(config_handle)
        config.destroy()

    finally:
        config_mgr.destroy()

if __name__ == '__main__':
    initialize_database()
```

### 3. Container CMD Best Practices

**DON'T**: Set CMD to run a script that exits

```dockerfile
# ❌ BAD - Container will restart continuously if script fails
CMD ["python", "src/query/run_queries.py"]
```

**DO**: Keep container running for exec-based workflows

```dockerfile
# ✅ GOOD - Container stays running
CMD ["tail", "-f", "/dev/null"]

# Then execute commands via docker exec:
# docker exec senzing-app python src/query/run_queries.py
```

**OR**: Use proper entrypoint with error handling

```dockerfile
# ✅ GOOD - Entrypoint handles initialization
COPY docker/scripts/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
```

## Complete Docker Setup Example

### Directory Structure

```text
project/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .dockerignore
│   └── scripts/
│       ├── entrypoint.sh
│       └── wait-for-postgres.sh
├── src/
│   └── setup/
│       ├── init_database.py
│       └── register_sources.py
├── config/
│   └── senzing_config.json
└── sql/
    └── init-schema.sql
```

### Dockerfile

```dockerfile
FROM senzing/senzingsdk-runtime:4.2.1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Copy initialization scripts
COPY docker/scripts/entrypoint.sh /entrypoint.sh
COPY docker/scripts/wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /entrypoint.sh /wait-for-postgres.sh

# Keep container running
ENTRYPOINT ["/entrypoint.sh"]
CMD ["tail", "-f", "/dev/null"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: senzing
      POSTGRES_USER: senzing
      POSTGRES_PASSWORD: senzing_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init-schema.sql:/docker-entrypoint-initdb.d/01-init-schema.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U senzing"]
      interval: 10s
      timeout: 5s
      retries: 5

  senzing:
    build:
      context: ..
      dockerfile: docker/Dockerfile
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
      - ../database:/app/database
    ports:
      - "8080:8080"

volumes:
  postgres_data:
```

### Entrypoint Script

```bash
#!/bin/bash
# docker/scripts/entrypoint.sh

set -e

echo "Waiting for PostgreSQL..."
/wait-for-postgres.sh

echo "Checking if database is initialized..."
python3 -c "
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host='${DATABASE_HOST}',
        port='${DATABASE_PORT}',
        database='${DATABASE_NAME}',
        user='${DATABASE_USER}',
        password='${DATABASE_PASSWORD}'
    )
    cur = conn.cursor()
    cur.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_name='sz_cfg_config'\")
    count = cur.fetchone()[0]
    conn.close()

    if count == 0:
        print('Database needs initialization')
        sys.exit(1)
    else:
        print('Database already initialized')
        sys.exit(0)
except Exception as e:
    print(f'Error checking database: {e}')
    sys.exit(1)
"

if [ $? -eq 1 ]; then
    echo "Initializing Senzing database..."
    python3 /app/src/setup/init_database.py

    echo "Registering data sources..."
    python3 /app/src/setup/register_sources.py
fi

echo "Starting application..."
exec "$@"
```

### Wait for PostgreSQL Script

```bash
#!/bin/bash
# docker/scripts/wait-for-postgres.sh

set -e

host="${DATABASE_HOST:-postgres}"
port="${DATABASE_PORT:-5432}"
user="${DATABASE_USER:-senzing}"

until PGPASSWORD="${DATABASE_PASSWORD}" psql -h "$host" -p "$port" -U "$user" -c '\q' 2>/dev/null; do
  >&2 echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

>&2 echo "PostgreSQL is up"
```

## Usage

### Initial Setup

```bash
# Build and start containers
docker-compose -f docker/docker-compose.yml up -d

# Check logs
docker-compose -f docker/docker-compose.yml logs -f senzing

# Initialize database (if not auto-initialized)
docker-compose -f docker/docker-compose.yml exec senzing python src/setup/init_database.py

# Register data sources
docker-compose -f docker/docker-compose.yml exec senzing python src/setup/register_sources.py
```

### Loading Data

```bash
# Transform data
docker-compose -f docker/docker-compose.yml exec senzing \
    python src/transform/transform_customers.py

# Load data
docker-compose -f docker/docker-compose.yml exec senzing \
    python src/load/load_customers.py
```

### Querying

```bash
# Run queries
docker-compose -f docker/docker-compose.yml exec senzing \
    python src/query/find_duplicates.py
```

## Common Docker Issues

### Issue: "Column sys_create_dt does not exist" (SENZ1001)

**Cause**: sys_cfg table uses wrong column name (sys_create_date instead of sys_create_dt)

**Error Message**: `SENZ1001|Critical Database Error '(7:42703ERROR: column "sys_create_dt" of relation "sys_cfg" does not exist`

**Solution**:

```sql
-- Fix the column name in sys_cfg table
ALTER TABLE sys_cfg RENAME COLUMN sys_create_date TO sys_create_dt;

-- Or recreate table with correct name
DROP TABLE IF EXISTS sys_cfg;
CREATE TABLE sys_cfg (
    config_data_id BIGSERIAL PRIMARY KEY,
    config_data TEXT NOT NULL,
    config_comments TEXT,
    sys_create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Issue: "Column code_id does not exist" (SENZ1001)

**Cause**: sys_codes_used table missing code_id column

**Error Message**: `SENZ1001|Critical Database Error '(7:42703ERROR: column "code_id" does not exist`

**Solution**:

```sql
-- Add missing code_id column
ALTER TABLE sys_codes_used ADD COLUMN code_id BIGSERIAL;

-- Or recreate table with correct structure
DROP TABLE IF EXISTS sys_codes_used;
CREATE TABLE sys_codes_used (
    code_type VARCHAR(50),
    code VARCHAR(50),
    code_id BIGSERIAL,
    PRIMARY KEY (code_type, code_value)
);
```

### Issue: "Schema tables not found" (SENZ1019)

**Cause**: Database not properly initialized

**Solution**:

1. Check `sys_vars` table exists and has version info
2. Run SDK initialization: `python src/setup/init_database.py`
3. Verify `sz_cfg_config` table was created

### Issue: "Invalid schema version" (SENZ7223)

**Cause**: Version mismatch in `sys_vars` table

**Solution**:

```sql
-- Check current version
SELECT * FROM sys_vars WHERE var_group = 'SYSTEM';

-- Update if needed (for Senzing 4.2.1)
UPDATE sys_vars SET var_value = '4.2.1'
WHERE var_group = 'SYSTEM' AND var_code = 'VERSION';

UPDATE sys_vars SET var_value = '4.0'
WHERE var_group = 'SYSTEM' AND var_code = 'SCHEMA_VERSION';
```

**Known Issue**: In some Docker/PostgreSQL configurations, the SDK may report an empty version string even when sys_vars is correctly populated. This is a known bug under investigation. Workaround: Use SQLite for development or direct PostgreSQL connection (not in Docker).

### Issue: Container restarts continuously

**Cause**: CMD exits immediately or fails

**Solution**:

- Change CMD to `tail -f /dev/null`
- Use docker exec for running commands
- Or implement proper entrypoint with error handling

### Issue: Cannot connect to PostgreSQL

**Cause**: Network or timing issues

**Solution**:

1. Use `depends_on` with health checks in docker-compose
2. Implement wait-for-postgres script
3. Check network: `docker network inspect <network_name>`
4. Verify connection string uses service name, not localhost

### Issue: Schema file not found

**Cause**: Trying to use schema file from runtime image

**Solution**:

- Don't rely on schema files in runtime images
- Use SDK initialization approach instead
- Or download schema separately and mount as volume

## Production Considerations

### 1. Volume Management

```yaml
volumes:
  # Persistent data
  - ./data:/app/data:ro          # Read-only source data
  - postgres_data:/var/lib/postgresql/data  # Database persistence

  # Logs
  - ./logs:/app/logs             # Application logs
```

### 2. Resource Limits

```yaml
services:
  senzing:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 3. Health Checks

```yaml
services:
  senzing:
    healthcheck:
      test: ["CMD", "python", "-c", "import senzing; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 4. Secrets Management

```yaml
services:
  senzing:
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

## Kubernetes Deployment

For Kubernetes, adapt the patterns:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: senzing
spec:
  replicas: 1
  template:
    spec:
      initContainers:
      - name: init-db
        image: senzing/senzingsdk-runtime:4.2.1
        command: ["python", "/app/src/setup/init_database.py"]
        env:
        - name: DATABASE_HOST
          value: postgres-service

      containers:
      - name: senzing
        image: senzing/senzingsdk-runtime:4.2.1
        command: ["tail", "-f", "/dev/null"]
```

## Testing Docker Setup

```bash
# Test database connection
docker-compose -f docker/docker-compose.yml exec senzing \
    python -c "import psycopg2; conn = psycopg2.connect('postgresql://senzing:senzing_password@postgres:5432/senzing'); print('✅ Connected')"

# Test Senzing SDK
docker-compose -f docker/docker-compose.yml exec senzing \
    python -c "import senzing; print(f'✅ Senzing version: {senzing.__version__}')"

# Test database schema
docker-compose -f docker/docker-compose.yml exec postgres \
    psql -U senzing -d senzing -c "SELECT COUNT(*) FROM sz_cfg_config;"
```

## When to Load This Guide

Load this guide when:

- User mentions Docker or containers
- User asks about deployment
- User encounters Docker-specific errors
- Starting Module 5 with Docker
- Planning production deployment

## Related Documentation

- [DOCKER_FOLDER_POLICY.md](../docs/policies/DOCKER_FOLDER_POLICY.md) - File organization
- [MODULE_5_SDK_SETUP.md](../docs/modules/MODULE_5_SDK_SETUP.md) - SDK installation
- [MODULE_12_DEPLOYMENT_PACKAGING.md](../docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md) - Deployment

## Version History

- **v1.0.0** (2026-03-17): Docker deployment guide created from real-world feedback
