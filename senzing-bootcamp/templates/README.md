# Senzing Boot Camp Templates

Utility templates for database management, data collection, validation, and planning.

## Important: Use MCP Server for Transformation, Loading, and Query Code

**Do NOT hand-code transformation, loading, or query programs.** Instead, use the Senzing MCP server tools:

- **Transformation code** → Use `mapping_workflow` (interactive 7-step process)
- **Loading code** → Use `generate_scaffold(workflow="add_records")`
- **Query code** → Use `generate_scaffold(workflow="full_pipeline")`
- **SDK initialization** → Use `generate_scaffold(workflow="initialize")`

**Why?** MCP-generated code is:

- Always current with latest SDK version
- Available in 5 languages (Python, Java, C#, Rust, TypeScript)
- Follows current Senzing best practices
- Automatically updated when SDK changes

**The templates in this directory are utilities that MCP cannot generate.**

## Available Templates

### Quick Demo Templates

#### demo_quick_start.py ⭐ RECOMMENDED - Module 0

**Purpose**: Live demonstration of Senzing entity resolution with sample data
**Use when**: Module 0 (Quick Demo), first-time users, demonstrations
**Features**: Actually runs Senzing SDK, shows before/after, displays match explanations
**Complexity**: Beginner
**Prerequisites**: Senzing SDK installed (Module 0)
**Usage**:

```bash
# Run the demo
python templates/demo_quick_start.py
```

**What it does**:

- Displays 5 sample records with obvious duplicates
- Initializes Senzing with in-memory database
- Loads records and resolves entities
- Shows which records matched and WHY
- Displays confidence scores and match explanations
- Creates the "aha moment" for new users

#### demo_simulation.py ⭐ NEW - Module 0 Fallback

**Purpose**: Simulated demonstration when Senzing SDK is not available
**Use when**: Module 1 (Quick Demo), SDK not yet installed
**Features**: Pure Python simulation, no dependencies, shows entity resolution concepts
**Complexity**: Beginner
**Prerequisites**: Python 3.8+ only (no Senzing SDK required)
**Usage**:

```bash
# Run the simulation
python templates/demo_simulation.py
```

**What it does**:

- Displays 5 sample records with obvious duplicates
- Simulates entity resolution logic
- Shows which records would match and WHY
- Displays simulated confidence scores
- Explains entity resolution concepts
- Perfect fallback when SDK unavailable

**When to use each**:

- Use `demo_quick_start.py` when Senzing SDK is available (preferred)
- Use `demo_simulation.py` when SDK is not yet installed
- Agent automatically chooses based on environment

### Database Management Templates

#### backup_database.py ⭐ IMPORTANT

**Purpose**: Backup SQLite and PostgreSQL databases
**Use when**: Before loading data, before major changes
**Features**: Auto-generates timestamped backups, compression
**Complexity**: Beginner
**Usage**:

```bash
# SQLite
python templates/backup_database.py \
  --db-type sqlite \
  --database database/G2C.db \
  --auto-name

# PostgreSQL
python templates/backup_database.py \
  --db-type postgresql \
  --connection "postgresql://senzing:pass@localhost:5432/senzing" \
  --output data/backups/senzing_backup.sql
```

#### restore_database.py

**Purpose**: Restore databases from backups
**Use when**: Recovering from errors, rolling back changes
**Features**: Confirmation prompts, safety checks
**Complexity**: Beginner
**Usage**:

```bash
# SQLite
python templates/restore_database.py \
  --db-type sqlite \
  --backup data/backups/G2C_backup_20260317_120000.db \
  --database database/G2C.db

# PostgreSQL
python templates/restore_database.py \
  --db-type postgresql \
  --backup data/backups/senzing_backup.sql \
  --connection "postgresql://senzing:pass@localhost:5432/senzing"
```

#### rollback_load.py

**Purpose**: Guidance for rolling back data loads
**Use when**: Need to undo a data load
**Features**: Explains rollback strategies, recommends backup/restore
**Complexity**: Beginner
**Usage**:

```bash
python templates/rollback_load.py \
  --data-source CUSTOMERS \
  --backup data/backups/G2C_backup_20260317_120000.db
```

### Data Collection Templates

#### collect_from_csv.py

**Purpose**: Collect and sample CSV data sources
**Use when**: Module 2 (data collection), working with CSV files
**Features**: Auto-detects delimiter and encoding, creates samples
**Complexity**: Beginner
**Usage**:

```bash
python templates/collect_from_csv.py \
  --input data/raw/customers.csv \
  --output data/samples/customers_sample.csv \
  --sample 1000
```

#### collect_from_json.py

**Purpose**: Collect and sample JSON data sources
**Use when**: Module 2 (data collection), working with JSON files
**Features**: Handles JSON and JSON Lines formats, creates samples
**Complexity**: Beginner
**Usage**:

```bash
python templates/collect_from_json.py \
  --input data/raw/customers.json \
  --output data/samples/customers_sample.json \
  --sample 1000
```

#### collect_from_api.py

**Purpose**: Collect data from REST APIs with pagination
**Use when**: Module 2 (data collection), API data sources
**Features**: Pagination, authentication, rate limiting, retry logic
**Complexity**: Intermediate
**Usage**:

```bash
python templates/collect_from_api.py \
  --url "https://api.example.com/customers" \
  --output data/raw/customers.json \
  --auth-token "your-token" \
  --max-records 10000
```

#### collect_from_database.py

**Purpose**: Extract data from databases
**Use when**: Module 2 (data collection), database sources
**Features**: Supports PostgreSQL, MySQL, SQLite, SQL Server, Oracle
**Complexity**: Intermediate
**Usage**:

```bash
python templates/collect_from_database.py \
  --db-type postgresql \
  --connection "postgresql://user:pass@host:5432/db" \
  --query "SELECT * FROM customers" \
  --output data/raw/customers.csv
```

### Validation & Testing Templates

#### validate_schema.py ⭐ HIGH PRIORITY

**Purpose**: Validate PostgreSQL and SQLite database schemas
**Use when**: Before loading data, troubleshooting schema issues
**Features**: Checks required tables, validates column names, provides SQL fixes
**Complexity**: Beginner
**Usage**:

```bash
# PostgreSQL
python templates/validate_schema.py --database postgresql \
  --connection "postgresql://senzing:pass@localhost:5432/senzing"

# SQLite
python templates/validate_schema.py --database sqlite \
  --connection "database/G2C.db"
```

#### performance_baseline.py

**Purpose**: Quick performance testing and baseline metrics
**Use when**: After SDK setup, before production deployment
**Features**: Tests loading and query performance, provides interpretation
**Complexity**: Beginner
**Usage**:

```bash
python templates/performance_baseline.py \
  --config-json '{"SQL":{"CONNECTION":"sqlite3://na:na@database/G2C.db"}}'
```

#### troubleshoot.py

**Purpose**: Interactive troubleshooting wizard
**Use when**: Encountering errors, systematic problem diagnosis
**Features**: Guided questions, specific solutions, diagnostic checks
**Complexity**: Beginner
**Usage**:

```bash
python templates/troubleshoot.py
```

### Planning & Analysis Templates

#### cost_calculator.py

**Purpose**: Interactive cost estimation for Senzing projects
**Use when**: Module 1 (planning), stakeholder presentations
**Features**: DSR licensing, infrastructure costs, time estimates
**Complexity**: Beginner
**Usage**:

```bash
# Interactive mode
python templates/cost_calculator.py --interactive

# Command line
python templates/cost_calculator.py \
  --records 1000000 \
  --sources 3 \
  --frequency daily \
  --deployment cloud
```

## How to Generate Transformation, Loading, and Query Code

### Generate Transformation Code

Use the `mapping_workflow` MCP tool for interactive data mapping:

```text
Agent: Call mapping_workflow(action="start", file_paths=["data/raw/customers.csv"])
→ Follow the 7-step interactive workflow
→ Agent generates transformation code automatically
→ Validates with lint_record and analyze_record
```

**Supports**: CSV, JSON, database extracts, API responses
**Output**: Python transformation code with correct Senzing attribute names

### Generate Loading Code

Use the `generate_scaffold` MCP tool:

```text
Agent: Call generate_scaffold(
  language="python",
  workflow="add_records",
  version="current"
)
→ Returns complete loading code with error handling
```

**Supports**: Python, Java, C#, Rust, TypeScript
**Output**: Production-ready loading code with batch processing, error handling, and statistics

### Generate Query Code

Use the `generate_scaffold` MCP tool:

```text
Agent: Call generate_scaffold(
  language="python",
  workflow="full_pipeline",
  version="current"
)
→ Returns complete pipeline with loading and querying
```

**Supports**: Python, Java, C#, Rust, TypeScript
**Output**: Complete pipeline code with initialization, loading, and query examples

## Using Templates

### Option 1: Copy and Customize

```bash
# Copy template to your project
cp senzing-bootcamp/templates/backup_database.py src/utils/

# Edit the file to customize for your needs
```

### Option 2: Ask the Agent

```text
"Create a backup script for my SQLite database"
"Help me collect data from a REST API"
"Validate my PostgreSQL schema"
```

The agent will customize the template for your specific needs.

### Option 3: Use as Reference

Browse templates to understand:

- Code structure
- Best practices
- Error handling patterns
- Documentation style

## Template Structure

Each template includes:

- **Header comments**: Purpose and usage
- **Configuration section**: Easy-to-modify settings
- **Core logic**: Well-documented implementation
- **Error handling**: Robust error management
- **Logging**: Progress and debugging output
- **Usage examples**: How to run the program

## Best Practices

### When Using Templates

1. **Always customize**: Don't use templates as-is
2. **Test with samples**: Use small data samples first
3. **Add error handling**: Enhance for your specific needs
4. **Document changes**: Note what you modified
5. **Version control**: Commit template-based code

### Template Modifications

**Do**:

- ✅ Adjust file paths and connection strings
- ✅ Add custom validation
- ✅ Enhance error messages
- ✅ Add logging for your needs
- ✅ Customize for your environment

**Don't**:

- ❌ Remove error handling
- ❌ Skip logging
- ❌ Hard-code credentials
- ❌ Remove documentation
- ❌ Ignore safety checks

## Troubleshooting

**Template doesn't work**:

- Check you've customized all required sections
- Verify file paths are correct
- Ensure required tools are installed (pg_dump for PostgreSQL backups)

**Import errors**:

- Install required packages: `pip install -r requirements.txt`
- Check Python version (3.8+)
- Verify dependencies are available

**Permission errors**:

- Check file permissions
- Ensure database user has required privileges
- Verify backup directory is writable

## Support

- Ask the agent to help customize templates
- Review `docs/modules/` for detailed guidance
- Check `examples/` for complete implementations
- Use `search_docs` for Senzing-specific questions

## Version History

- **v4.0.0** (2026-03-23): Removed transformation, loading, and query templates (use MCP server instead)
- **v3.1.0** (2026-03-17): Added 10 new utility templates
- **v3.0.0** (2026-03-17): Templates directory created
