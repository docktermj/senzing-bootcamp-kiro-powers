# Database Migration Guide: SQLite to PostgreSQL

## Overview

This guide walks you through migrating your Senzing entity resolution database from SQLite to PostgreSQL. The migration is recommended when your data volume exceeds SQLite's practical limits or when you need concurrent access for production workloads.

The migration process preserves your existing SQLite database (it is never modified) and re-loads your data into a fresh PostgreSQL instance using the Senzing JSON files you already produced during the bootcamp.

## Prerequisites

Before starting the migration, ensure you have:

- **PostgreSQL installed and running** — Version 12 or later recommended
- **Database creation privileges** — Ability to create databases and users in PostgreSQL
- **Existing Senzing JSON files** — The transformed JSON records produced in Modules 5/6 (these are your source of truth for re-loading)
- **Senzing SDK configured** — A working Senzing installation (already set up from Module 2)
- **Sufficient disk space** — PostgreSQL requires more disk space than SQLite (indexes, WAL, overhead)

## Why Migrate

### SQLite Limitations

SQLite is excellent for learning and small-scale work, but it has fundamental limitations that become problematic as your data grows:

- **Single-writer constraint** — Only one process can write at a time. All concurrent writes are serialized, creating a bottleneck for loading and redo processing.
- **No network access** — SQLite databases are local files. Multiple machines or containers cannot share the same database.
- **Performance ceiling at ~100K records** — Throughput degrades significantly beyond 100K records. Loading rates drop from 200+ rec/sec to under 100 rec/sec as the database grows.
- **No multi-threaded loading benefit** — Because of the single-writer lock, adding threads does not improve loading throughput.

### PostgreSQL Advantages

PostgreSQL removes these limitations and provides capabilities required for production Senzing deployments:

- **Concurrent access** — Multiple processes and threads can read and write simultaneously without blocking each other.
- **Production-grade reliability** — ACID compliance, crash recovery, streaming replication, and point-in-time recovery.
- **Required for multi-process loading** — Multi-threaded and multi-process loading scales near-linearly with PostgreSQL (2-10x throughput improvement depending on thread count).
- **Network accessible** — Multiple applications, containers, or machines can connect to the same database instance.
- **Better performance at scale** — Maintains consistent throughput even with millions of records, especially when properly tuned.

### When to Migrate

Migrate to PostgreSQL when any of these apply:

- Data volume exceeds 100K records
- Loading throughput with SQLite is insufficient for your timeline
- You need concurrent access from multiple processes or users
- You are preparing for production deployment (Module 11)
- Multi-threaded loading is required to meet performance targets

## Step 1: Create PostgreSQL Database

Create a dedicated database and user for Senzing:

```sql
-- Connect to PostgreSQL as a superuser
CREATE USER senzing WITH PASSWORD 'your-secure-password';
CREATE DATABASE senzing OWNER senzing;
GRANT ALL PRIVILEGES ON DATABASE senzing TO senzing;
```

Verify connectivity:

```bash
psql -h localhost -U senzing -d senzing -c "SELECT version();"
```

**Security note:** Use a strong password and restrict access via `pg_hba.conf`. For production, consider using environment variables or a secrets manager for credentials.

## Step 2: Initialize Senzing Schema

The Senzing schema must be initialized in your new PostgreSQL database before loading data. The agent will retrieve the current PostgreSQL engine configuration for your chosen language:

<!-- AGENT INSTRUCTION BLOCK -->
<!-- The following block is executed by the Kiro agent when assisting the user interactively -->

> **Agent:** Call `sdk_guide(topic='configure', language='<chosen_language>')` to retrieve the PostgreSQL engine configuration for the user's chosen language. Present the connection parameters and initialization code.

<!-- END AGENT INSTRUCTION BLOCK -->

The engine configuration specifies how Senzing connects to PostgreSQL. Key parameters include:

- **BACKEND** — Set to `SQL`
- **CONNECTION** — PostgreSQL connection string (e.g., `postgresql://senzing:password@localhost:5432/senzing`)

After configuring the engine, initialize the database schema. This creates all required tables, indexes, and stored procedures that Senzing needs for entity resolution.

## Step 3: Re-load Data

Re-load your existing Senzing JSON files into the new PostgreSQL database. You do **not** need to re-map your raw data — the JSON files produced during Modules 5/6 are already in Senzing format and can be loaded directly.

<!-- AGENT INSTRUCTION BLOCK -->
<!-- The following block is executed by the Kiro agent when assisting the user interactively -->

> **Agent:** Call `search_docs(query='PostgreSQL database setup', version='current')` to retrieve authoritative guidance on loading data into a PostgreSQL-backed Senzing instance. Present the recommended loading approach.

<!-- END AGENT INSTRUCTION BLOCK -->

### Re-loading Process

1. **Point your loading program at PostgreSQL** — Update the engine configuration to use the PostgreSQL connection string from Step 2
2. **Run your existing loading program** — Use the same loading code from Module 6, but with the new engine configuration
3. **Load from your Senzing JSON files** — These are the files in your project (typically under `data/` or `output/`) that contain transformed records
4. **Process redo records** — After the initial load completes, process any redo records to finalize entity resolution

**Important:** This is a re-load from existing JSON files, not a re-mapping of raw source data. Your transformation work from Module 5 is preserved.

### Performance Tips for Loading

- Use multi-threaded loading to take advantage of PostgreSQL's concurrent write support
- Start with 4 threads and increase based on your hardware (see [PERFORMANCE_BASELINES.md](PERFORMANCE_BASELINES.md) for scaling guidance)
- Monitor PostgreSQL during loading: check for lock contention, disk I/O, and memory usage

## Step 4: Verify Migration

After loading completes, verify that the migration was successful:

### Record Count Verification

Compare the number of records loaded into PostgreSQL against your SQLite database:

- Total records loaded should match (or exceed, if you added data)
- Entity count may differ slightly due to improved resolution with redo processing

### Entity Resolution Validation

Spot-check a sample of entities to confirm resolution quality:

- Query known entities by record ID and verify they resolved correctly
- Compare entity composition between SQLite and PostgreSQL for a sample set
- Check that relationships and disclosed links are preserved

### Query Comparison

Run representative queries against both databases and compare results:

- Search by attributes (name, address, phone)
- Get entity by ID
- Get entity by record

Response times should be equal or better with PostgreSQL, especially for larger datasets.

## Rollback

If the migration encounters problems, rolling back is straightforward because **the SQLite database remains completely intact throughout the migration process**.

### Why Rollback Is Safe

- The original SQLite database file (`database/G2C.db`) is never modified during migration
- All migration work happens in the new PostgreSQL database
- Your Senzing JSON source files are unchanged
- No data is deleted or altered in the original environment

### How to Rollback

1. **Revert engine configuration** — Point your programs back to the SQLite database connection
2. **Update preferences** — Set `database_type` back to `sqlite` in `config/bootcamp_preferences.yaml`
3. **Optionally drop PostgreSQL database** — If you want to clean up: `DROP DATABASE senzing;`

Your SQLite environment is immediately usable again with no data loss.

### When to Rollback

Consider rolling back if:

- Schema initialization fails and cannot be resolved
- Loading produces unexpected errors that require investigation
- Entity resolution results differ significantly from SQLite (investigate before deciding)
- PostgreSQL performance is worse than expected (likely a tuning issue — see [PERFORMANCE_BASELINES.md](PERFORMANCE_BASELINES.md))

## Update Preferences

After a successful migration, update your bootcamp preferences to reflect the new database backend:

In `config/bootcamp_preferences.yaml`, set:

```yaml
database_type: postgresql
```

Valid values for the `database_type` field:

- `sqlite` — Default. File-based database, suitable for learning and small datasets
- `postgresql` — Production-grade database, required for large datasets and concurrent access

This field is informational — it tells the agent and scripts which database backend is active so they can provide appropriate guidance (e.g., multi-threading recommendations, tuning parameters, troubleshooting steps).

## Related Resources

- [PERFORMANCE_BASELINES.md](PERFORMANCE_BASELINES.md) — Throughput benchmarks, hardware requirements, SQLite vs PostgreSQL comparison, and tuning parameters
- [Module 8 Phase C: Optimization](../../steering/module-08-phaseC-optimization.md) — Database tuning steps and performance optimization workflow
- [AFTER_BOOTCAMP.md](AFTER_BOOTCAMP.md) — Production maintenance and scaling guidance

### MCP Tools

- `sdk_guide(topic='configure', language='<chosen_language>')` — PostgreSQL engine configuration for your language
- `search_docs(query='PostgreSQL database setup', version='current')` — Authoritative PostgreSQL setup documentation
- `search_docs(query='database tuning', category='configuration', version='current')` — Database tuning guidance
- `explain_error_code(code='<error_code>')` — Troubleshoot Senzing errors during migration
