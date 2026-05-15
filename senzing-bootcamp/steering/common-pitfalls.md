---
inclusion: manual
description: "Common mistakes and solutions by module — load on errors or when user is stuck"
---

# Common Pitfalls Quick Reference

Load on errors, when user is stuck, or preventively at module start. For visual diagnostics, load `troubleshooting-decision-tree.md` instead.

## Quick Navigation

[Symptoms](#troubleshooting-by-symptom) · Modules: [1](#module-1) · [2](#module-2) · [3](#module-3) · [4](#module-4) · [5](#module-5) · [6](#module-6) · [7](#module-7) · [8–11](#modules-8-11) | [Database Issues](#database-issues) · [Windows](#windows-pitfalls) · [TypeScript/Node.js](#typescriptnodejs-pitfalls) · [General](#general-pitfalls) · [MCP Down](#mcp-unavailable) · [Recovery](#recovery) · [Pre-Module Checklist](#pre-module-checklist)

## Guided Troubleshooting — Ask Before Scanning

When the user says "I'm stuck" or reports an error, ask these diagnostic questions first (one at a time, WAIT for each):

1. "What module are you working on?" (narrows to the right section below)
2. "What were you trying to do when the problem happened?" (narrows to the specific step)
3. "Did you see an error message? If so, what did it say?" (if SENZ error → use `explain_error_code`; if other → check the pitfall tables)

Then jump to the relevant section and present only the matching pitfall/fix — not the entire table. Do not present pitfalls from other modules.

<a id="troubleshooting-by-symptom"></a>

## Troubleshooting by Symptom

| Symptom | Diagnostic Action |
| ------- | ----------------- |
| Zero entities created | Check input file format and project structure. Verify `data/transformed/` contains valid JSONL. Call `search_docs(query="record format requirements")` for current field requirements |
| Loading hangs | Check system resources and record count. Call `search_docs(query="performance tuning loading")` for current guidance on database and threading configuration |
| Query returns no results | Verify data was loaded successfully and entity IDs exist. Call `get_sdk_reference(topic='flags')` for correct query flag usage |
| SDK initialization fails | Verify configuration JSON is valid and paths exist. Call `explain_error_code` with the specific SENZ code for diagnosis |
| Database connection fails | Check database file existence, verify connection string format, check file permissions, verify PostgreSQL service status |

<a id="module-2"></a>

## Module 2: SDK Setup

| Pitfall                                      | Fix                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------- |
| Installing over existing SDK                 | Check first: `ls -la /opt/senzing` or language-appropriate import check      |
| Skipping anti-pattern check                  | Always call `search_docs(category='anti_patterns')`                          |
| Wrong platform commands                      | Use `sdk_guide` with correct `platform` parameter                            |
| Missing configuration JSON                   | Follow `sdk_guide(topic='configure')` exactly                                |
| Database choice unclear                      | Call `search_docs(query="database configuration")` for current guidance on SQLite vs PostgreSQL tradeoffs |

### SQLite → PostgreSQL Migration

When to migrate: call `search_docs(query="database configuration scaling")` for current guidance on when to switch.

Steps: Install PostgreSQL (Linux: `apt install postgresql`, macOS: `brew install postgresql`, Windows: download the installer from postgresql.org/download/windows/ or use `winget install PostgreSQL.PostgreSQL`) → `sdk_guide(topic='configure')` for new config → Reload data from JSONL (SQLite data doesn't transfer) → Update `bootcamp_preferences.yaml` → Re-validate queries.

What carries forward: all code, transformed data, docs, config. What doesn't: the SQLite DB file.

<a id="module-3"></a>

## Module 3: System Verification

| Pitfall                                  | Fix                                                                              |
| ---------------------------------------- | -------------------------------------------------------------------------------- |
| Confusing per-process stats with totals  | Use a counter during loading for record counts. Call `get_sdk_reference` for current stats method behavior |
| Entity counts don't match TruthSet expectations | Check SDK config paths (CONFIGPATH, SUPPORTPATH), verify database was freshly initialized, call `search_docs(query="truthset")` for current expected results |

<a id="module-1"></a>

## Module 1: Business Problem

| Pitfall                              | Fix                                                                  |
| ------------------------------------ | -------------------------------------------------------------------- |
| Problem too vague ("clean my data")  | Ask: what issue, which systems, desired outcome, success metric      |
| Too many data sources (10+)          | Prioritize 1-2 sources, expand later                                 |
| Unrealistic expectations             | Set clear expectations about what ER can/cannot do                   |

<a id="module-4"></a>

## Module 4: Data Collection

| Pitfall                            | Fix                                                          |
| ---------------------------------- | ------------------------------------------------------------ |
| Not documenting data locations     | Document all sources in `docs/data_source_locations.md`      |
| Mixing raw and transformed data    | Raw → `data/raw/`, transformed → `data/transformed/`         |
| Loading entire large datasets      | Create representative samples (1K-10K records)               |

<a id="module-5"></a>

## Module 5: Data Quality & Mapping

| Pitfall                                  | Fix                                                                              |
| ---------------------------------------- | -------------------------------------------------------------------------------- |
| Insufficient sample data (2-3 records)   | Request 100-1000 records minimum                                                 |
| Skipping quality scoring                 | Always run automated scoring for objective metrics                               |
| Ignoring quality issues                  | Address during mapping (Phase 2 of Module 5)                                     |
| Proceeding with low quality              | Use the three-tier gate: ≥80% proceed, 70-79% warn and let user decide, <70% recommend fixing first |
| Guessing attribute names                 | ALWAYS use `mapping_workflow` — never guess. Call `search_docs(query="entity specification")` for current attribute reference |
| Running transformation on full dataset first | Test on 10-100 records first                                                  |
| Skipping validation after transform      | Always validate output with `analyze_record`                                     |
| Generated files in project root          | Relocate: scripts→`src/transform/`, JSONL→`data/transformed/`, docs→`docs/`, shell→`scripts/` |

### Mapping Workflow State Loss

State cannot be reconstructed — you must restart. Recover quickly by:

1. Check `docs/mapping_specifications.md` for documented mappings
2. Check `src/transform/` and `data/transformed/` for existing artifacts
3. Restart `mapping_workflow` with `action='start'` and same source file
4. Use documented mappings to fast-track through steps
5. If transform program exists and works, just validate with `analyze_record`

Prevention: warn user before long mapping sessions that state doesn't persist across sessions.

<a id="module-6"></a>

## Module 6: Load Data

| Pitfall                                          | Fix                                                                          |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| No database backup                               | ALWAYS backup before loading (use backup hook)                               |
| Loading without testing                          | Test with 100 records first                                                  |
| Ignoring error codes                             | Call `explain_error_code` for every SENZ error, fix root cause               |
| Poor data source naming (`file1`, `data`)        | Use descriptive uppercase names. Call `search_docs(query="data source naming")` for conventions |
| No progress monitoring                           | Add progress logging to loading programs                                     |
| No per-source error handling (multi-source)      | Implement per-source error handling, continue on failure                     |
| Not tracking multi-source progress               | Use orchestration dashboard or logging                                       |
| Data format or field issues                      | Call `search_docs(query="record format requirements")` for current required fields and format |

<a id="database-issues"></a>

## Database Issues

Database corruption typically occurs during Module 6 data loading. Run `python3 scripts/check_database.py` to diagnose, or add `--repair` to attempt automatic recovery.

| Pitfall | Symptoms | Fix |
| ------- | -------- | --- |
| Corruption after disk full | "database disk image is malformed" error during load or query | Free disk space, then run `python3 scripts/check_database.py --repair`. If repair fails, delete `database/G2C.db` and re-run the loading program from JSONL |
| Locked database | "database is locked" error, loading hangs indefinitely | Close all other processes accessing the database. Check for stale lock files. If the lock persists, restart the system or run `python3 scripts/check_database.py --repair` |
| Zero entities after load | Loading reports success but queries return no results, entity count is 0 | Run `python3 scripts/check_database.py` to verify entity count. If count is 0, check that the loading program used the correct data source file and that records had valid RECORD_ID fields |
| WAL file left behind | `-wal` or `-shm` files remain next to `G2C.db` after a crash | Run `python3 scripts/check_database.py --repair` to checkpoint and remove WAL files. Alternatively, run `sqlite3 database/G2C.db "PRAGMA wal_checkpoint(TRUNCATE);"` manually |

### Manual Recovery Steps

If `--repair` does not resolve the issue:

1. **Check integrity**: `sqlite3 database/G2C.db "PRAGMA integrity_check;"` — if result is not "ok", the database must be rebuilt
2. **Attempt WAL recovery**: `sqlite3 database/G2C.db "PRAGMA wal_checkpoint(TRUNCATE);"` — forces pending WAL transactions into the main database file
3. **Vacuum**: `sqlite3 database/G2C.db "VACUUM;"` — reclaims space and can fix minor inconsistencies
4. **Rebuild from scratch**: Delete `database/G2C.db` (and any `-wal`/`-shm` files), re-initialize the database, and re-run the loading program against your transformed JSONL in `data/transformed/`

For PostgreSQL: check for orphaned transactions (`SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction'`), run `VACUUM ANALYZE`, and re-run failed loads — Senzing's RECORD_ID-based loading is idempotent.

<a id="module-7"></a>

## Module 7: Query and Visualize

| Pitfall                                      | Fix                                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Guessing SDK method names                    | Call `get_sdk_reference` — never guess method names or signatures                                                        |
| Unexpected match results                     | Call `get_sdk_reference(topic='why')` for match explanation methods                                                      |
| Expecting perfect results immediately        | Iterate: adjust mappings, confidence scores, add attributes                                                              |
| Skipping UAT                                 | Always conduct UAT with business users before production (see Module 6)                                                  |
| Query flag confusion                         | Call `get_sdk_reference(topic='flags')` for current flag reference                                                       |

<a id="modules-8-11"></a>

## Modules 8–11: Production Readiness

- **Skipping performance testing** → Complete Module 8 before production
- **No security hardening** → Complete Module 9 checklist
- **No monitoring** → Complete Module 10 setup
- **No disaster recovery plan** → Complete Module 11 DR planning and test backups

<a id="general-pitfalls"></a>

## General Pitfalls

| Pitfall                              | Fix                                                                                                      |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| `python3` not found (Windows)        | Use `python` instead of `python3` on Windows. Ensure Python is on `PATH` via the installer checkbox      |
| Corporate proxy blocking MCP         | Allowlist `mcp.senzing.com:443`. Set `HTTPS_PROXY` if behind proxy                                       |
| Not reading error messages           | Read carefully, use `explain_error_code` for SENZ codes                                                  |
| Guessing instead of searching docs   | Use `search_docs` liberally                                                                              |
| Not committing to git                | Commit after each module completion                                                                      |
| Working in production first          | Always develop locally or in dev environment                                                             |
| Not documenting decisions            | Document in `docs/` as you go                                                                            |
| Rushing through modules              | Complete each module fully before proceeding                                                             |

<a id="mcp-unavailable"></a>

<a id="windows-pitfalls"></a>

## Windows-Specific Pitfalls

| Pitfall | Fix |
| ------- | --- |
| `python3` not recognized | Use `python` on Windows. Ensure "Add Python to PATH" was checked during installation |
| PowerShell blocks script execution | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once |
| `npm` not found in scripts | Windows uses `npm.cmd` — if running scripts manually, use `npm.cmd` or run from PowerShell/Windows Terminal |
| TypeScript SDK build fails (native addons) | Install Visual Studio Build Tools: `winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools"` |
| Senzing DLLs not found at runtime | Call `sdk_guide` for the correct path to add to `PATH` |
| Emoji/Unicode garbled in terminal | Use Windows Terminal or PowerShell 7 instead of `cmd.exe`. Install: `winget install Microsoft.WindowsTerminal` |
| `source` command not found | `source` is bash-only. Use `. .\scripts\senzing-env.ps1` (PowerShell) or `call scripts\senzing-env.bat` (cmd) |

<a id="typescriptnodejs-pitfalls"></a>

## TypeScript/Node.js Pitfalls

| Pitfall | Fix |
| ------- | --- |
| Unhandled promise rejections crash the process | Always `await` async SDK calls or attach `.catch()`. Add a global handler: `process.on('unhandledRejection', (err) => { /* log and exit */ })` |
| Blocking the event loop with large record loads | Use `setImmediate` or batch processing to yield between records. Never call synchronous SDK wrappers in a tight loop |
| Using `any` type for Senzing data structures | Define interfaces for records, entity results, and config objects. Use the SDK's exported types or create your own based on `search_docs(query="record format")` |
| TypeScript strict mode errors on SDK return values | Enable `strict: true` in `tsconfig.json` from the start. Add explicit null checks for optional fields returned by query methods |
| ESM `import` used but package expects `require` (CJS) | Set `"type": "module"` in `package.json` for ESM projects. If the SDK only ships CJS, use `import { createRequire } from 'module'` or dynamic `import()` |
| `require` used in an ESM project causes ERR_REQUIRE_ESM | Convert to `import` syntax or switch `package.json` to `"type": "commonjs"`. Do not mix module systems in the same package |

## MCP Server Unavailable

The Senzing MCP server is required for the bootcamp to function. If the connection fails, troubleshoot using the table below.

| Issue | Fix |
| ----- | --- |
| Corporate proxy blocking connection | Allowlist `mcp.senzing.com:443`. Set `HTTPS_PROXY` environment variable if behind a proxy |
| DNS resolution failure | Run `nslookup mcp.senzing.com` to verify DNS. Try alternate DNS (8.8.8.8) if resolution fails |
| Firewall blocking outbound HTTPS | Ensure outbound traffic to `mcp.senzing.com:443` is permitted |
| IDE MCP connection stale | Restart the MCP server connection in the Kiro Powers panel |
| General connectivity | Test with `curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443` — expect 200 |

After fixing the connection, say "retry" to re-run the MCP health check.

<a id="recovery"></a>

## Recovery Quick Reference

- **Loaded wrong data** → `python3 scripts/restore_project.py backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip`
- **Wrong transformation** → Delete bad output, fix program, re-run on sample, validate with `analyze_record`
- **Lost mapping state** → Restart workflow, reuse artifacts from `docs/` and `src/transform/`
- **Corrupted git file** → `git checkout HEAD -- src/transform/program.[ext]`

<a id="pre-module-checklist"></a>

## Pre-Module Checklist

Before starting any module: previous module complete and validated · documentation up to date · code committed to git · backup created (if applicable) · sample data tested · error handling in place
