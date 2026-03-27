---
inclusion: manual
---

# Module 5: SDK Installation and Configuration

## Workflow: Quick SDK Test Load — Part A: SDK Installation and Configuration (Module 5)

**IMPORTANT**: Before installing, verify Senzing is not already installed to avoid conflicts or duplicate installations.

1. **Check if Senzing is already installed**:

   **Python check**:

   ```bash
   python -c "import senzing; print('Senzing version:', senzing.__version__)" 2>/dev/null
   ```

   **System check (Linux/macOS)**:

   ```bash
   # Check for Senzing installation directory
   ls -la /opt/senzing 2>/dev/null
   ls -la /etc/opt/senzing 2>/dev/null

   # Check for Senzing Python package
   pip list | grep senzing
   ```

   **If Senzing is already installed**:
   - Ask user if they want to use the existing installation
   - Verify the version is V4.0
   - Skip to step 4 (verify installation)
   - If version is not V4.0 or installation is broken, proceed with reinstallation

2. **Determine the user's platform** (if not already installed):

   Ask: "What platform are you using? Linux, macOS, Windows, or would you prefer to use Docker?"

   WAIT for their response before proceeding to installation.

3. **Install Senzing** (if not already installed):
   - Call `sdk_guide` with `topic='install'` and the detected platform for installation commands
   - Follow platform-specific installation steps
   - Accept EULA during installation

   **If user chooses Docker deployment**:
   - Explain that Docker runtime images do NOT include PostgreSQL schema files
   - For PostgreSQL, must use two-stage initialization pattern:
     1. Create minimal SQL schema with CORRECT column names:
        - sys_cfg must use `sys_create_dt` (NOT sys_create_date)
        - sys_codes_used must include `code_id BIGSERIAL` column
        - sys_vars structure: (var_group, var_code, var_value)
     2. Insert sys_vars: VERSION='4.2.1', SCHEMA_VERSION='4.0'
     3. Use SDK's `set_default_config()` to create remaining tables
   - **Critical**: Wrong column names cause SENZ1001 errors that block initialization
   - Container CMD should be `tail -f /dev/null` to keep running
   - Use `docker exec` to run initialization and loading commands
   - All Docker files must be created in `docker/` directory
   - Reference `steering/docker-deployment.md` for complete verified schema examples

4. **Verify the installation is working correctly**:

   ```python
   # Test script to verify Senzing installation
   import senzing
   from senzing import G2Engine

   print(f"Senzing version: {senzing.__version__}")

   # Try to initialize engine
   try:
       engine = G2Engine()
       print("✅ Senzing engine initialized successfully")
       engine.destroy()
   except Exception as e:
       print(f"❌ Error initializing engine: {e}")
   ```

5. **Configure the engine**:
   - Call `sdk_guide` with `topic='configure'` for engine configuration
   - Ask: "Which database would you like to use? SQLite is good for evaluation, PostgreSQL is recommended for production."
   - WAIT for their response
   - Register data sources identified in Module 1
   - Create engine configuration JSON

6. **Test database connection**:

   ```python
   # Test database connectivity
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

   # Try a simple operation
   stats = engine.getStats()
   print("✅ Database connection successful")
   print(f"Stats: {stats}")

   engine.destroy()
   ```

**Success criteria**:

- ✅ Senzing installed (or existing installation verified)
- ✅ Engine initializes without errors
- ✅ Database connection works
- ✅ Data sources registered

**Agent behavior**:

- Always check for existing installation first
- Don't reinstall if compatible version exists
- Verify installation before proceeding to Module 6
- If installation fails, check common pitfalls guide
