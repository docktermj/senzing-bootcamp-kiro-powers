# Troubleshooting Index

Quick reference for common issues and solutions across all boot camp modules.

## Quick Links

- [Installation Issues](#installation-issues)
- [Data Quality Issues](#data-quality-issues)
- [Transformation Errors](#transformation-errors)
- [Loading Errors](#loading-errors)
- [Query Issues](#query-issues)
- [Performance Problems](#performance-problems)
- [Configuration Issues](#configuration-issues)
- [Database Issues](#database-issues)
- [Error Codes](#error-codes)

## Installation Issues

### Senzing Not Found

**Symptom**: `ModuleNotFoundError: No module named 'senzing'`

**Solutions**:
1. Check if Senzing is installed:
   ```bash
   pip list | grep senzing
   ```

2. Install Senzing:
   ```bash
   pip install senzing
   ```

3. Verify Python version (3.8+ required):
   ```bash
   python --version
   ```

**Related**: [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md)

---

### Permission Denied During Installation

**Symptom**: `Permission denied` when installing Senzing

**Solutions**:
1. Use `sudo` for system installation:
   ```bash
   sudo apt install senzingapi-runtime
   ```

2. Or use virtual environment (no sudo needed):
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install senzing
   ```

**Related**: [environment-setup.md](../../steering/environment-setup.md)

---

### Wrong Senzing Version

**Symptom**: Boot camp expects V4.0 but different version installed

**Solutions**:
1. Check installed version:
   ```bash
   python -c "import senzing; print(senzing.__version__)"
   ```

2. Upgrade to V4.0:
   ```bash
   pip install --upgrade senzing
   ```

**Related**: [COMPATIBILITY_MATRIX.md](COMPATIBILITY_MATRIX.md)

---

## Data Quality Issues

### Low Completeness Score

**Symptom**: Data quality score < 60%, many missing fields

**Solutions**:
1. Identify missing fields:
   ```python
   df.isnull().sum()
   ```

2. Options:
   - Fill missing values from other sources
   - Use default values where appropriate
   - Document limitations
   - Proceed with caution

**Related**: [MODULE_3_DATA_QUALITY_SCORING.md](../modules/MODULE_3_DATA_QUALITY_SCORING.md)

---

### High Duplicate Rate

**Symptom**: Many duplicate records in source data

**Solutions**:
1. Deduplicate before transformation:
   ```python
   df.drop_duplicates(subset=['id'], keep='first')
   ```

2. Or let Senzing resolve duplicates (recommended)

3. Document duplicate handling strategy

**Related**: [common-pitfalls.md](../../steering/common-pitfalls.md)

---

### Inconsistent Data Formats

**Symptom**: Dates, phones, addresses in multiple formats

**Solutions**:
1. Standardize in transformation:
   ```python
   # Standardize phone numbers
   phone = re.sub(r'[^0-9]', '', phone)
   
   # Standardize dates
   date = pd.to_datetime(date).strftime('%Y-%m-%d')
   ```

2. Use data cleaning libraries (phonenumbers, usaddress)

**Related**: [MODULE_4_DATA_MAPPING.md](../modules/MODULE_4_DATA_MAPPING.md)

---

## Transformation Errors

### JSON Decode Error

**Symptom**: `JSONDecodeError: Expecting value`

**Solutions**:
1. Check for empty lines:
   ```python
   if line.strip():  # Skip empty lines
       record = json.loads(line)
   ```

2. Check for invalid JSON:
   ```python
   try:
       record = json.loads(line)
   except json.JSONDecodeError as e:
       print(f"Invalid JSON on line {line_num}: {e}")
   ```

3. Validate JSON format

**Related**: [transform_csv_template.py](../../templates/transform_csv_template.py)

---

### Missing Required Fields

**Symptom**: Records missing DATA_SOURCE or RECORD_ID

**Solutions**:
1. Ensure all records have required fields:
   ```python
   if not record.get('DATA_SOURCE'):
       record['DATA_SOURCE'] = 'YOUR_SOURCE'
   
   if not record.get('RECORD_ID'):
       record['RECORD_ID'] = generate_id()
   ```

2. Validate before writing:
   ```python
   def validate_record(record):
       required = ['DATA_SOURCE', 'RECORD_ID']
       for field in required:
           if not record.get(field):
               return f"Missing {field}"
       return None
   ```

**Related**: [MODULE_4_DATA_MAPPING.md](../modules/MODULE_4_DATA_MAPPING.md)

---

### Wrong Attribute Names

**Symptom**: Senzing doesn't recognize attribute names

**Solutions**:
1. Use correct Senzing attribute names:
   - ✅ `PRIMARY_NAME_FIRST` not `FIRST_NAME`
   - ✅ `EMAIL_ADDRESS` not `EMAIL`
   - ✅ `PHONE_NUMBER` not `PHONE`

2. Use MCP tool `mapping_workflow` for correct names

3. Check [Senzing attribute reference](https://senzing.zendesk.com/hc/en-us/articles/231925448-Generic-Entity-Specification)

**Related**: [steering.md](../../steering/steering.md#module-4-data-mapping)

---

## Loading Errors

### Database Connection Failed

**Symptom**: `Unable to connect to database`

**Solutions**:

**For SQLite**:
1. Check database directory exists:
   ```bash
   mkdir -p database
   ```

2. Check file permissions:
   ```bash
   ls -la database/
   ```

3. Verify connection string:
   ```json
   "CONNECTION": "sqlite3://na:na@database/G2C.db"
   ```

**For PostgreSQL**:
1. Check PostgreSQL is running:
   ```bash
   systemctl status postgresql
   ```

2. Test connection:
   ```bash
   psql -h localhost -U senzing -d senzing
   ```

3. Verify credentials in connection string

**Related**: [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md)

---

### Slow Loading Performance

**Symptom**: Loading < 100 records/second

**Solutions**:
1. Switch from SQLite to PostgreSQL
2. Increase batch size:
   ```python
   BATCH_SIZE = 5000  # Increase from 1000
   ```

3. Use multiprocessing:
   ```python
   from multiprocessing import Pool
   with Pool(4) as pool:
       pool.map(load_batch, batches)
   ```

4. Optimize transformation code

**Related**: [MODULE_9_PERFORMANCE_TESTING.md](../modules/MODULE_9_PERFORMANCE_TESTING.md)

---

### Memory Errors

**Symptom**: `MemoryError` or system runs out of memory

**Solutions**:
1. Reduce batch size:
   ```python
   BATCH_SIZE = 100  # Reduce from 1000
   ```

2. Process in chunks:
   ```python
   for chunk in pd.read_csv(file, chunksize=1000):
       process_chunk(chunk)
   ```

3. Use streaming instead of loading all into memory

4. Increase system memory

**Related**: [performance-monitoring.md](../../steering/performance-monitoring.md)

---

### Data Source Not Registered

**Symptom**: `Data source 'XXX' not found`

**Solutions**:
1. Register data source:
   ```python
   from senzing import G2Config
   
   config = G2Config()
   config.init("RegisterDS", "{}", False)
   handle = config.create()
   
   config.addDataSource(handle, json.dumps({
       "DSRC_CODE": "YOUR_SOURCE"
   }))
   
   config_str = config.save(handle)
   # Apply config...
   ```

2. Or use MCP tool `sdk_guide` with topic='configure'

**Related**: [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md)

---

## Query Issues

### No Results Found

**Symptom**: Queries return empty results

**Solutions**:
1. Verify data was loaded:
   ```python
   stats = engine.stats()
   print(stats)  # Check record count
   ```

2. Check search criteria:
   ```python
   # Too specific?
   search = {"NAME_FULL": "John Smith", "EMAIL": "john@email.com"}
   
   # Try broader search
   search = {"NAME_FULL": "John Smith"}
   ```

3. Verify data source and record ID

**Related**: [MODULE_8_QUERY_VALIDATION.md](../modules/MODULE_8_QUERY_VALIDATION.md)

---

### Slow Query Performance

**Symptom**: Queries take > 1 second

**Solutions**:
1. Check database indexes (PostgreSQL)
2. Optimize search criteria (fewer fields)
3. Use entity ID instead of searching
4. Consider caching frequent queries
5. Check database resources (CPU, memory)

**Related**: [MODULE_9_PERFORMANCE_TESTING.md](../modules/MODULE_9_PERFORMANCE_TESTING.md)

---

### Unexpected Matches

**Symptom**: Records matched that shouldn't be

**Solutions**:
1. Review match keys and thresholds
2. Check data quality (garbage in = garbage out)
3. Use `explain_error_code` MCP tool
4. Review entity details:
   ```python
   entity = engine.getEntityByEntityID(entity_id)
   # Review why records matched
   ```

5. Consider adjusting matching rules (advanced)

**Related**: [MODULE_8_QUERY_VALIDATION.md](../modules/MODULE_8_QUERY_VALIDATION.md)

---

## Performance Problems

### High CPU Usage

**Symptom**: CPU at 100% during loading

**Solutions**:
1. This is normal during loading
2. Reduce parallel loaders if too high
3. Check for infinite loops in transformation code
4. Monitor with `top` or `htop`

**Related**: [performance-monitoring.md](../../steering/performance-monitoring.md)

---

### High Memory Usage

**Symptom**: Memory usage growing continuously

**Solutions**:
1. Check for memory leaks in transformation code
2. Reduce batch sizes
3. Use streaming instead of loading all data
4. Monitor with `free -h` or `htop`
5. Restart process periodically for long-running jobs

**Related**: [MODULE_9_PERFORMANCE_TESTING.md](../modules/MODULE_9_PERFORMANCE_TESTING.md)

---

### Disk Space Full

**Symptom**: `No space left on device`

**Solutions**:
1. Check disk usage:
   ```bash
   df -h
   ```

2. Clean up:
   ```bash
   # Remove old backups
   rm data/backups/*.db.old
   
   # Remove logs
   rm logs/*.log.old
   
   # Clean transformed files after loading
   rm data/transformed/*.jsonl
   ```

3. Increase disk space

**Related**: [recovery-procedures.md](../../steering/recovery-procedures.md)

---

## Configuration Issues

### Config File Not Found

**Symptom**: `FileNotFoundError: config/senzing_config.json`

**Solutions**:
1. Create config directory:
   ```bash
   mkdir -p config
   ```

2. Create config file (see MODULE_5_SDK_SETUP.md)

3. Check file path in code

**Related**: [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md)

---

### Invalid Configuration

**Symptom**: `Invalid configuration JSON`

**Solutions**:
1. Validate JSON syntax:
   ```bash
   python -m json.tool config/senzing_config.json
   ```

2. Check required fields:
   - PIPELINE.CONFIGPATH
   - PIPELINE.RESOURCEPATH
   - PIPELINE.SUPPORTPATH
   - SQL.CONNECTION

3. Use template from documentation

**Related**: [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md)

---

### Environment Variables Not Set

**Symptom**: Variables like `$DB_PASSWORD` not resolved

**Solutions**:
1. Create .env file:
   ```bash
   cp .env.example .env
   # Edit .env with actual values
   ```

2. Load environment variables:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   
   import os
   password = os.getenv('DB_PASSWORD')
   ```

3. Or export in shell:
   ```bash
   export DB_PASSWORD=your_password
   ```

**Related**: [environment-setup.md](../../steering/environment-setup.md)

---

## Database Issues

### SQLite Database Locked

**Symptom**: `database is locked`

**Solutions**:
1. Only one writer at a time for SQLite
2. Close other connections
3. Use PostgreSQL for concurrent access
4. Check for zombie processes:
   ```bash
   ps aux | grep python
   ```

**Related**: [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md)

---

### PostgreSQL Connection Refused

**Symptom**: `Connection refused` to PostgreSQL

**Solutions**:
1. Check PostgreSQL is running:
   ```bash
   systemctl status postgresql
   ```

2. Check port is correct (default 5432)

3. Check pg_hba.conf allows connections

4. Verify firewall rules

**Related**: [MODULE_5_SDK_SETUP.md](../modules/MODULE_5_SDK_SETUP.md)

---

### Database Corruption

**Symptom**: Database errors, crashes, inconsistent results

**Solutions**:
1. Stop all operations
2. Restore from backup:
   ```bash
   ./scripts/rollback.sh data/backups/G2C_20260317.db
   ```

3. If no backup, rebuild from source data

4. Implement regular backups going forward

**Related**: [disaster-recovery.md](../../steering/disaster-recovery.md)

---

### Schema Tables Not Found (SENZ1019) - Docker

**Symptom**: `SENZ1019: Schema tables not found` in Docker containers

**Cause**: Database not properly initialized (common in Docker deployments)

**Solutions**:

1. **Check if sys_vars table exists**:
   ```bash
   docker-compose exec postgres psql -U senzing -d senzing -c "SELECT * FROM sys_vars;"
   ```

2. **If table doesn't exist, initialize minimal schema**:
   ```sql
   CREATE TABLE sys_vars (
       var_group VARCHAR(50),
       var_code VARCHAR(50),
       var_value TEXT,
       PRIMARY KEY (var_group, var_code)
   );
   
   INSERT INTO sys_vars VALUES ('SYSTEM', 'VERSION', '4.2.1');
   INSERT INTO sys_vars VALUES ('SYSTEM', 'SCHEMA_VERSION', '4.0');
   ```

3. **Run SDK initialization**:
   ```bash
   docker-compose exec senzing python src/setup/init_database.py
   ```

4. **Verify sz_cfg_config table was created**:
   ```bash
   docker-compose exec postgres psql -U senzing -d senzing -c "\dt"
   ```

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

### Invalid Schema Version (SENZ7223) - Docker

**Symptom**: `SENZ7223: Invalid schema version` in Docker

**Cause**: Version mismatch in sys_vars table

**Solutions**:

1. **Check current version**:
   ```sql
   SELECT * FROM sys_vars WHERE var_group = 'SYSTEM';
   ```

2. **Update version for Senzing 4.2.1**:
   ```sql
   UPDATE sys_vars SET var_value = '4.2.1' 
   WHERE var_group = 'SYSTEM' AND var_code = 'VERSION';
   
   UPDATE sys_vars SET var_value = '4.0' 
   WHERE var_group = 'SYSTEM' AND var_code = 'SCHEMA_VERSION';
   ```

3. **Restart container**:
   ```bash
   docker-compose restart senzing
   ```

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

### Schema File Not Found - Docker

**Symptom**: Cannot find `/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql` in Docker

**Cause**: Runtime Docker images don't include schema files

**Solution**:

**DON'T** try to use schema files from runtime images - they don't exist!

**DO** use SDK-based initialization:

1. Create minimal schema (sys_vars, sys_cfg, sz_cfg_config)
2. Run SDK initialization to create remaining tables
3. See [docker-deployment.md](../../steering/docker-deployment.md) for complete example

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

## Docker Issues

### Column "sys_create_dt" Does Not Exist (SENZ1001)

**Symptom**: `SENZ1001|Critical Database Error '(7:42703ERROR: column "sys_create_dt" of relation "sys_cfg" does not exist`

**Cause**: sys_cfg table uses wrong column name (sys_create_date instead of sys_create_dt)

**Solutions**:

1. **Fix the column name**:
   ```sql
   ALTER TABLE sys_cfg RENAME COLUMN sys_create_date TO sys_create_dt;
   ```

2. **Or recreate table with correct name**:
   ```sql
   DROP TABLE IF EXISTS sys_cfg;
   CREATE TABLE sys_cfg (
       config_data_id BIGSERIAL PRIMARY KEY,
       config_data TEXT NOT NULL,
       config_comments TEXT,
       sys_create_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. **Verify the fix**:
   ```bash
   docker-compose exec postgres psql -U senzing -d senzing -c "\d sys_cfg"
   ```

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

### Column "code_id" Does Not Exist (SENZ1001)

**Symptom**: `SENZ1001|Critical Database Error '(7:42703ERROR: column "code_id" does not exist`

**Cause**: sys_codes_used table missing code_id column required by SDK

**Solutions**:

1. **Add missing column**:
   ```sql
   ALTER TABLE sys_codes_used ADD COLUMN code_id BIGSERIAL;
   ```

2. **Or recreate table with correct structure**:
   ```sql
   DROP TABLE IF EXISTS sys_codes_used;
   CREATE TABLE sys_codes_used (
       code_type VARCHAR(50),
       code VARCHAR(50),
       code_id BIGSERIAL,
       PRIMARY KEY (code_type, code)
   );
   ```

3. **Verify the fix**:
   ```bash
   docker-compose exec postgres psql -U senzing -d senzing -c "\d sys_codes_used"
   ```

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

### Version Reading Issue (SENZ7223) - Known Bug

**Symptom**: `SENZ7223: Invalid version number for datastore schema [version '']` even though version is correctly stored in sys_vars

**Cause**: SDK cannot read version from sys_vars table in Docker/PostgreSQL despite correct data

**Verification**:
```bash
# Verify version is in database
docker-compose exec postgres psql -U senzing -d senzing \
  -c "SELECT * FROM sys_vars WHERE var_code = 'VERSION';"
# Should show: SYSTEM | VERSION | 4.2.1

# But SDK reports empty version when loading records
```

**What's Been Tried**:
1. ✅ Fixed sys_cfg column name (sys_create_date → sys_create_dt)
2. ✅ Fixed sys_codes_used missing code_id column
3. ✅ Verified sys_vars table structure is correct
4. ✅ Verified version values: VERSION='4.2.1', SCHEMA_VERSION='4.0'
5. ✅ Configuration saves successfully to sys_cfg
6. ✅ Data sources can be queried
7. ❌ SDK still reads empty version string

**Workaround**:
- Use SQLite for local development (works 100%)
- Use direct PostgreSQL connection (not in Docker) which may work
- Wait for fix to this known issue

**Status**: Known bug under investigation. The schema is correct, configuration saves successfully, but version reading fails in Docker/PostgreSQL environment.

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

### Container Restarts Continuously

**Symptom**: Docker container keeps restarting

**Cause**: CMD exits immediately or fails

**Solutions**:

1. **Change CMD to keep container running**:
   ```dockerfile
   CMD ["tail", "-f", "/dev/null"]
   ```

2. **Use docker exec for commands**:
   ```bash
   docker exec senzing-app python src/query/run_queries.py
   ```

3. **Check container logs**:
   ```bash
   docker logs senzing-app
   docker logs --tail 50 senzing-app
   ```

4. **Implement proper entrypoint with error handling**

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

### Cannot Connect to PostgreSQL from Container

**Symptom**: Connection refused when connecting to PostgreSQL from Docker container

**Solutions**:

1. **Use service name, not localhost**:
   ```python
   # ❌ WRONG
   "CONNECTION": "postgresql://senzing:pass@localhost:5432/senzing"
   
   # ✅ CORRECT (in docker-compose)
   "CONNECTION": "postgresql://senzing:pass@postgres:5432/senzing"
   ```

2. **Add depends_on with health check**:
   ```yaml
   services:
     senzing:
       depends_on:
         postgres:
           condition: service_healthy
   ```

3. **Implement wait-for-postgres script**

4. **Check network**:
   ```bash
   docker network ls
   docker network inspect <network_name>
   ```

**Related**: [docker-deployment.md](../../steering/docker-deployment.md)

---

### Docker Build Context Issues

**Symptom**: Files not found during Docker build

**Cause**: Incorrect build context when Dockerfile is in docker/ folder

**Solutions**:

1. **Build with correct context**:
   ```bash
   # From project root
   docker build -f docker/Dockerfile -t myapp .
   ```

2. **In docker-compose.yml**:
   ```yaml
   build:
     context: ..              # Parent directory
     dockerfile: docker/Dockerfile
   ```

3. **Check .dockerignore location**: Should be `docker/.dockerignore`

**Related**: [DOCKER_FOLDER_POLICY.md](../development/DOCKER_FOLDER_POLICY.md)

---

## Database Issues

## Error Codes

### Common Senzing Error Codes

Use MCP tool `explain_error_code` for detailed explanations.

**SENZ0001**: Generic error
- Check logs for details
- Verify configuration

**SENZ0002**: Database error
- Check database connection
- Verify database permissions

**SENZ0003**: Configuration error
- Validate configuration JSON
- Check required fields

**SENZ0004**: Data source error
- Verify data source is registered
- Check data source code

**SENZ0005**: Record error
- Check record format
- Validate required fields

**Related**: Use `explain_error_code` MCP tool for any error code

---

## Getting More Help

### Use MCP Tools

- `explain_error_code` - Diagnose Senzing errors
- `search_docs` - Search Senzing documentation
- `find_examples` - Find code examples

### Check Documentation

- [troubleshooting-decision-tree.md](../../steering/troubleshooting-decision-tree.md) - Systematic troubleshooting
- [common-pitfalls.md](../../steering/common-pitfalls.md) - Common mistakes
- Module documentation in `docs/modules/`

### Ask the Agent

The agent can help troubleshoot issues:
- Describe the problem
- Share error messages
- Provide relevant code snippets

## Contributing

Found a solution to a common problem? Add it to this index!

## Version History

- **v1.0.0** (2026-03-17): Troubleshooting index created
