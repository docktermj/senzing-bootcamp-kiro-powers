---
inclusion: manual
---

# Common Pitfalls and How to Avoid Them

Learn from common mistakes to save time and frustration.

## Module 1: Quick Demo

### Pitfall: Using `get_stats()` for Record Counts

**Symptom**: `get_stats()` returns `-1` for `loadedRecords` even though records loaded successfully
**Problem**: `get_stats()` tracks per-process workload statistics, not repository totals. It resets after each call.
**Solution**: Track record counts during loading with a simple counter. Use `get_stats()` only for monitoring ongoing operations (Module 9).

## Module 2: Business Problem

### Pitfall: Problem Too Vague

**Symptom**: "I want to clean my data"
**Problem**: Not specific enough to guide the bootcamp
**Solution**: Ask targeted questions:

- What specific data quality issue?
- Which systems have the data?
- What's the desired outcome?
- How will you measure success?

### Pitfall: Too Many Data Sources at Once

**Symptom**: User lists 10+ data sources
**Problem**: Overwhelming scope, long timeline
**Solution**: Prioritize 1-2 sources for initial bootcamp, expand later

### Pitfall: Unrealistic Expectations

**Symptom**: "This will solve all our data problems"
**Problem**: Entity resolution is powerful but not magic
**Solution**: Set clear expectations about what ER can and cannot do

## Module 3: Identify and Collect Data Sources

### Pitfall: Not Documenting Data Locations

**Symptom**: "Where did we get this file?"
**Problem**: Can't trace data lineage or refresh data
**Solution**: Document all data source locations in `docs/data_source_locations.md`

### Pitfall: Mixing Raw and Transformed Data

**Symptom**: Files scattered across directories
**Problem**: Hard to track what's been processed
**Solution**: Keep raw data in `data/raw/`, transformed in `data/transformed/`

### Pitfall: Loading Entire Large Datasets

**Symptom**: Uploading 10GB files
**Problem**: Slow, unnecessary for evaluation
**Solution**: Create representative samples (1000-10000 records)

## Module 4: Evaluate Data Quality

### Pitfall: Insufficient Sample Data

**Symptom**: User provides 2-3 sample records
**Problem**: Can't assess data quality or patterns
**Solution**: Request 100-1000 sample records minimum

### Pitfall: Skipping Quality Scoring

**Symptom**: "The data looks fine to me"
**Problem**: Subjective assessment, missing quality issues
**Solution**: Always run automated quality scoring to get objective metrics

### Pitfall: Ignoring Data Quality Issues

**Symptom**: "We'll fix the data later"
**Problem**: Poor quality = poor matching results
**Solution**: Address quality issues during mapping (Module 5)

### Pitfall: Accepting Low Quality Scores

**Symptom**: Quality score < 70% but proceeding anyway
**Problem**: Poor matching results, wasted effort
**Solution**: Improve data quality before mapping or adjust expectations

## Module 5: Map Your Data

### Pitfall: Hand-Coding Attribute Names

**Symptom**: Wrong attribute names cause loading failures or silent quality degradation
**Problem**: Training data and documentation may have outdated attribute names
**Solution**: ALWAYS use `mapping_workflow` — never guess attribute names

> **Agent instruction:** Do not list specific wrong/right attribute name pairs here.
> Use `search_docs(query="entity specification", version="current")` or
> `download_resource(filename="senzing_entity_specification.md")` for the current
> authoritative attribute reference.

### Pitfall: Forgetting Required Fields

**Symptom**: Mapping fails validation
**Problem**: Missing `DATA_SOURCE` or `RECORD_ID`
**Solution**: Every record MUST have:

- `DATA_SOURCE` - Unique identifier for this source
- `RECORD_ID` - Unique within the data source

### Pitfall: Not Testing Transformation

**Symptom**: Running transformation on full dataset first
**Problem**: Errors discovered after hours of processing
**Solution**: Always test on 10-100 records first

### Pitfall: Skipping Quality Analysis

**Symptom**: "The transformation ran, so it's good"
**Problem**: Low quality data = poor matching
**Solution**: Always run `analyze_record` and review metrics

### Pitfall: Losing Mapping Workflow State

**Symptom**: `mapping_workflow` errors about missing state
**Problem**: Not passing the `state` object between calls
**Solution**: Always pass the EXACT `state` JSON from previous response

### Pitfall: Generated Files Placed in Project Root

**Symptom**: Source code, data, and documentation files appear in project root after mapping
**Problem**: MCP tools may output files to the current directory instead of the proper subdirectory
**Solution**: Always relocate generated files immediately:

- Mapper scripts → `src/transform/`
- Transformed JSONL output → `data/transformed/`
- Mapping documentation → `docs/`
- Shell scripts → `scripts/`

If files land in the root, move them before proceeding.

## Module 0: Set Up SDK

### Pitfall: Installing Over Existing Installation

**Symptom**: Installation conflicts, version mismatches, broken configuration
**Problem**: Not checking if Senzing is already installed
**Solution**: Always check first:

```bash
# Check installation directory
ls -la /opt/senzing 2>/dev/null

# Check SDK availability (use the appropriate command for your language)
# Python:     python -c "import senzing; print(senzing.__version__)"
# Java:       check classpath for senzing JAR
# C#:         dotnet list package | grep -i senzing
# Rust:       cargo tree | grep senzing
# TypeScript: npm list | grep senzing
```

If already installed, verify version and use existing installation.

### Pitfall: Using SQLite for Production

**Symptom**: "SQLite is working fine for 10K records"
**Problem**: Doesn't scale, SQLite is limited to <1M records
**Solution**: SQLite for evaluation only, PostgreSQL for production

### Migrating from SQLite to PostgreSQL

If you started with SQLite and need to switch to PostgreSQL (common when reaching Modules 9-12 or when data exceeds 100K records):

**When to migrate**:

- Data volume exceeds 100K records and loading is slow
- You need multi-threaded loading (SQLite is single-writer)
- You're preparing for production deployment (Modules 9-12)
- Performance testing shows SQLite is the bottleneck

**Migration steps**:

1. **Install PostgreSQL** and create a database:

   ```bash
   # Linux (apt)
   sudo apt install postgresql
   sudo -u postgres createdb senzing

   # macOS (Homebrew)
   brew install postgresql
   createdb senzing
   ```

   ```powershell
   # Windows (PowerShell) — download from https://www.postgresql.org/download/windows/
   # After installation, PostgreSQL runs as a service automatically.
   # Use the bundled command-line tools:
   & "C:\Program Files\PostgreSQL\<version>\bin\createdb.exe" -U postgres senzing
   ```

2. **Reconfigure the Senzing engine** — use `sdk_guide(topic='configure', platform='<your_platform>', language='<chosen_language>', version='current')` to get the correct PostgreSQL engine configuration JSON. The key change is replacing the SQLite connection string with a PostgreSQL one.

3. **Reload your data** — PostgreSQL requires a fresh load. Your transformation programs and loading scripts from Modules 5-6 are reusable. Run them against the new database.

4. **Update your preferences** — update `config/bootcamp_preferences.yaml` and `config/bootcamp_progress.json` to reflect the database change.

5. **Re-run validation** — verify queries still work against the new database.

**What carries forward**: All source code (`src/`), transformed data (`data/transformed/`), documentation (`docs/`), and configuration. Only the database itself needs rebuilding.

**What doesn't carry forward**: The SQLite database file (`database/G2C.db`). Keep it as a backup until PostgreSQL is verified.

### Pitfall: Skipping Anti-Pattern Check

**Symptom**: Following outdated installation guides
**Problem**: Known issues, deprecated approaches
**Solution**: Always call `search_docs` with category `anti_patterns`

### Pitfall: Wrong Platform Commands

**Symptom**: Using apt commands on macOS
**Problem**: Installation fails
**Solution**: Use `sdk_guide` with correct platform parameter

### Pitfall: Missing Environment Variables

**Symptom**: SDK initialization fails
**Problem**: `SENZING_ENGINE_CONFIGURATION_JSON` not set
**Solution**: Follow `sdk_guide` configuration exactly

## Module 6: Load Single Data Source

### Pitfall: No Database Backup

**Symptom**: Loading fails halfway, database corrupted
**Problem**: No way to recover
**Solution**: ALWAYS backup before loading (use backup hook)

### Pitfall: Loading Without Testing

**Symptom**: Errors discovered after loading millions of records
**Problem**: Wasted time, need to rollback
**Solution**: Test load with 100 records first

### Pitfall: Ignoring Error Codes

**Symptom**: "Some records failed but most worked"
**Problem**: Errors indicate data quality or configuration issues
**Solution**: Use `explain_error_code` for every error, fix root cause

### Pitfall: Wrong DATA_SOURCE Name

**Symptom**: Records load but queries don't work
**Problem**: DATA_SOURCE doesn't match registered name
**Solution**: Verify DATA_SOURCE matches Module 0 configuration

### Pitfall: Duplicate RECORD_IDs Within a Source

**Symptom**: Record count after loading is lower than expected; some records seem to disappear
**Problem**: If two records in the same DATA_SOURCE have the same RECORD_ID, Senzing treats the second as an update — it overwrites the first, not adds alongside it
**Solution**: Ensure RECORD_IDs are unique within each DATA_SOURCE. Check for duplicates before loading:

```text
-- Count duplicate RECORD_IDs in your JSONL file
-- Read each line, extract RECORD_ID, count occurrences
-- Flag any RECORD_ID that appears more than once
```

If your source data naturally has duplicates, append a sequence number or use a composite key (e.g., `source_id + "_" + row_number`).

### Pitfall: Poor DATA_SOURCE Naming

**Symptom**: Confusing data source names like `file1`, `data`, `test`
**Problem**: Hard to identify sources in results, confusing in multi-source projects
**Solution**: Use descriptive, uppercase names with underscores. Include the system of origin:

```text
✅ Good names:
  CUSTOMERS_CRM
  VENDORS_ERP
  EMPLOYEES_HR
  CONTACTS_SALESFORCE

❌ Bad names:
  file1
  data
  test
  my_data
  customers (too generic if you have multiple customer sources)
```

Rules: uppercase, no spaces, no special characters beyond underscores, descriptive of the source system.

### Pitfall: Not Monitoring Progress

**Symptom**: "Is it still running?"
**Problem**: No visibility into loading status
**Solution**: Add progress logging to loading programs

### Pitfall: Loading Multiple Sources Without Orchestration

**Symptom**: Loading sources one by one manually
**Problem**: No dependency management, inefficient
**Solution**: Use Module 7 for multi-source orchestration

## Module 7: Multi-Source Orchestration

### Pitfall: Loading Sources in Wrong Order

**Symptom**: Reference data loaded after dependent data
**Problem**: Missing relationships, poor resolution
**Solution**: Define load order based on dependencies

### Pitfall: No Error Handling Across Sources

**Symptom**: One source fails, entire load stops
**Problem**: All-or-nothing approach
**Solution**: Implement per-source error handling and continue

### Pitfall: Not Tracking Multi-Source Progress

**Symptom**: "Which sources have loaded?"
**Problem**: No visibility into overall progress
**Solution**: Use orchestration dashboard or logging

## Module 8: Query and Validate Results

### Pitfall: Guessing SDK Method Names

**Symptom**: Method doesn't exist, code fails
**Problem**: Method names changed between V3 and V4
**Solution**: Use `generate_scaffold` or `get_sdk_reference` — never guess method names

> **Agent instruction:** Do not list specific wrong/right method name pairs here.
> Use `get_sdk_reference(topic='migration', version='current')` for V3→V4 method
> renames, or `get_sdk_reference(topic='functions', version='current')` for current signatures.

### Pitfall: Wrong Query Flags

**Symptom**: Results missing expected information
**Problem**: Incorrect or missing flags
**Solution**: Use `get_sdk_reference` with topic `flags`

### Pitfall: Not Understanding Why Records Matched

**Symptom**: "These shouldn't have matched"
**Problem**: Don't understand resolution behavior
**Solution**: Use `whyEntities` to see match details and scoring

### Pitfall: Expecting Perfect Results Immediately

**Symptom**: "The results aren't perfect"
**Problem**: First iteration rarely perfect
**Solution**: Iterate - adjust mappings, confidence scores, add attributes

### Pitfall: Skipping UAT

**Symptom**: "It looks good to me, let's deploy"
**Problem**: No stakeholder validation, surprises in production
**Solution**: Always conduct UAT with business users before production

## Modules 9-12: Production Readiness

### Pitfall: Skipping Performance Testing

**Symptom**: "It works on my laptop"
**Problem**: Production performance unknown
**Solution**: Complete Module 9 performance testing before production

### Pitfall: No Security Hardening

**Symptom**: Using default passwords, no encryption
**Problem**: Security vulnerabilities
**Solution**: Complete Module 10 security hardening checklist

### Pitfall: No Monitoring Setup

**Symptom**: "Is the system running?"
**Problem**: No visibility into production health
**Solution**: Complete Module 11 monitoring setup before deployment

### Pitfall: No Disaster Recovery Plan

**Symptom**: Data loss with no backup
**Problem**: Cannot recover from failures
**Solution**: Complete Module 12 DR planning and test backups

## General Pitfalls

### Pitfall: Corporate Proxy or Firewall Blocking MCP

**Symptom**: MCP tool calls time out or return connection errors; `mcp.senzing.com` is unreachable
**Problem**: Corporate firewalls or proxy servers block outbound HTTPS to `mcp.senzing.com:443`
**Solution**:

1. Verify connectivity: `curl -s https://mcp.senzing.com/mcp` — if this times out, the network is blocking it.
2. Ask your IT team to allowlist `mcp.senzing.com` on port 443 (HTTPS).
3. If you're behind an HTTP proxy, configure it in your environment:

   ```bash
   # Linux/macOS
   export HTTPS_PROXY=http://proxy.company.com:8080

   # Windows (PowerShell)
   $env:HTTPS_PROXY = "http://proxy.company.com:8080"
   ```

4. If the proxy requires authentication, include credentials: `http://user:password@proxy.company.com:8080`
5. While waiting for network access, you can still work on Modules 2-4 (business problem, data collection, data quality) which don't require MCP calls.

### Pitfall: Not Reading Error Messages

**Symptom**: "It's not working"
**Problem**: Error message explains the issue
**Solution**: Read error messages carefully, use `explain_error_code`

### Pitfall: Skipping Documentation

**Symptom**: Guessing how things work
**Problem**: Incorrect assumptions, wasted time
**Solution**: Use `search_docs` liberally

### Pitfall: Not Committing to Git

**Symptom**: Lost work after accidental deletion
**Problem**: No version control
**Solution**: Commit after each module completion

### Pitfall: Working in Production First

**Symptom**: Testing in production environment
**Problem**: Risk of data corruption, downtime
**Solution**: Always develop locally or in dev environment

### Pitfall: Not Documenting Decisions

**Symptom**: "Why did we do it this way?"
**Problem**: Lost context, hard to maintain
**Solution**: Document decisions in docs/ as you go

### Pitfall: Rushing Through Modules

**Symptom**: Skipping validation steps
**Problem**: Errors compound, harder to debug
**Solution**: Complete each module fully before proceeding

## Recovery from Common Mistakes

### Loaded Wrong Data

```text
# Restore from backup
python scripts/restore_project.py backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip
```

### Wrong Transformation

```bash
# Delete bad output
rm data/transformed/bad_output.jsonl
# Fix transformation program
# Re-run on sample first
# Validate with analyze_record
```

### Lost Mapping State

```bash
# Start mapping workflow over
# Or use saved mapping documentation from docs/
```

### Corrupted Git Repo

```bash
# Restore file from git
git checkout HEAD -- src/transform/program.[ext]
```

## Prevention Checklist

Before each module:

- [ ] Previous module complete and validated
- [ ] Documentation up to date
- [ ] Code committed to git
- [ ] Backup created (if applicable)
- [ ] Sample data tested
- [ ] Error handling in place

## When to Load This Guide

Load this steering file when:

- User encounters an error
- Starting any module (preventive)
- User says "it's not working"
- Troubleshooting issues
- User is stuck or frustrated

For a visual diagnostic flowchart, load `steering/troubleshooting-decision-tree.md` instead. The decision tree provides the diagnostic flow; this file provides detailed pitfall descriptions and solutions by module.
