---
inclusion: auto
description: "Common mistakes and solutions by module — load on errors or when user is stuck"
---

# Common Pitfalls Quick Reference

Load on errors, when user is stuck, or preventively at module start. For visual diagnostics, load `troubleshooting-decision-tree.md` instead.

## Quick Navigation

[Symptoms](#troubleshooting-by-symptom) · Modules: [1](#module-1) · [2](#module-2) · [3](#module-3) · [4](#module-4) · [5](#module-5) · [6](#module-6) · [7](#module-7) · [8–11](#modules-8-11) | [Windows](#windows-pitfalls) · [General](#general-pitfalls) · [MCP Down](#mcp-unavailable) · [Recovery](#recovery) · [Pre-Module Checklist](#pre-module-checklist)

## Guided Troubleshooting — Ask Before Scanning

When the user says "I'm stuck" or reports an error, ask these diagnostic questions first (one at a time, WAIT for each):

1. "What module are you working on?" (narrows to the right section below)
2. "What were you trying to do when the problem happened?" (narrows to the specific step)
3. "Did you see an error message? If so, what did it say?" (if SENZ error → use `explain_error_code`; if other → check the pitfall tables)

Then jump to the relevant section and present only the matching pitfall/fix — not the entire table. Do not present pitfalls from other modules.

<a id="troubleshooting-by-symptom"></a>

## Troubleshooting by Symptom

| Symptom | Likely Cause | Diagnostic Steps |
| ------- | ------------ | ---------------- |
| Zero entities created | Incorrect data format, missing `DATA_SOURCE` or `RECORD_ID` fields, or loading program not processing records | Check input file format, verify `DATA_SOURCE` and `RECORD_ID` fields exist in every record, review loading program output, use `search_docs` to verify required fields |
| Loading hangs | Large record count with SQLite, threading misconfiguration, or insufficient system resources | Check record count and database type (SQLite vs PostgreSQL), review threading configuration, monitor system resources, use `search_docs` for performance tuning |
| Query returns no results | Invalid entity IDs, data not yet loaded, or incorrect query flags | Verify entity IDs exist, confirm data was loaded successfully, use `get_sdk_reference(topic='flags')` to check correct query flags |
| SDK initialization fails | Invalid `SENZING_ENGINE_CONFIGURATION_JSON`, incorrect CONFIGPATH/RESOURCEPATH/SUPPORTPATH, or missing Senzing installation | Verify `SENZING_ENGINE_CONFIGURATION_JSON` is valid JSON, check paths exist, use `explain_error_code` for the specific SENZ code |
| Database connection fails | Database file doesn't exist, incorrect connection string, permission issues, or PostgreSQL service not running | Check database file existence, verify connection string format, check file permissions, verify PostgreSQL service status |

<a id="module-2"></a>

## Module 2: SDK Setup

| Pitfall                                      | Fix                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------- |
| Installing over existing SDK                 | Check first: `ls -la /opt/senzing` or language-appropriate import check      |
| SQLite for production                        | SQLite for evaluation only (<1M records). PostgreSQL for production          |
| Skipping anti-pattern check                  | Always call `search_docs(category='anti_patterns')`                          |
| Wrong platform commands                      | Use `sdk_guide` with correct `platform` parameter                            |
| Missing `SENZING_ENGINE_CONFIGURATION_JSON`  | Follow `sdk_guide` configuration exactly                                     |

### SQLite → PostgreSQL Migration

When to migrate: >100K records and slow, need multi-threading, preparing for Modules 8-11.

Steps: Install PostgreSQL (Linux: `apt install postgresql`, macOS: `brew install postgresql`, Windows: download the installer from postgresql.org/download/windows/ or use `winget install PostgreSQL.PostgreSQL`) → `sdk_guide(topic='configure')` for new config → Reload data from JSONL (SQLite data doesn't transfer) → Update `bootcamp_preferences.yaml` → Re-validate queries.

What carries forward: all code, transformed data, docs, config. What doesn't: the SQLite DB file.

<a id="module-3"></a>

## Module 3: Quick Demo

| Pitfall                                  | Fix                                                                              |
| ---------------------------------------- | -------------------------------------------------------------------------------- |
| Using `get_stats()` for record counts    | `get_stats()` tracks per-process stats, not totals. Use a counter during loading |

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
| Hand-coding attribute names              | ALWAYS use `mapping_workflow` — never guess. Use `search_docs(query="entity specification")` for reference   |
| Missing `DATA_SOURCE` or `RECORD_ID`    | Every record MUST have both fields                                                                           |
| Running transformation on full dataset first | Test on 10-100 records first                                                                             |
| Skipping `analyze_record` after transform | Always validate output quality                                                                              |
| Generated files in project root          | Relocate: scripts→`src/transform/`, JSONL→`data/transformed/`, docs→`docs/`, shell→`scripts/`                |

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
| Loading 5,000+ records on SQLite                 | Start with ≤1,000 records. Single-threaded ER slows as DB grows. Use PostgreSQL for larger volumes. |
| Ignoring error codes                             | Use `explain_error_code` for every error, fix root cause                     |
| Wrong DATA_SOURCE name                           | Verify matches Module 2 configuration                                        |
| Duplicate RECORD_IDs                             | Ensure unique within each DATA_SOURCE. Append sequence number if needed      |
| Poor DATA_SOURCE naming (`file1`, `data`)        | Use descriptive uppercase: `CUSTOMERS_CRM`, `VENDORS_ERP`                    |
| No progress monitoring                           | Add progress logging to loading programs                                     |
| Wrong load order (multi-source)                  | Define order based on dependencies and data quality                          |
| No per-source error handling (multi-source)      | Implement per-source error handling, continue on failure                     |
| Not tracking multi-source progress               | Use orchestration dashboard or logging                                       |

<a id="module-7"></a>

## Module 7: Query and Visualize

| Pitfall                                      | Fix                                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Guessing SDK method names                    | Use `generate_scaffold` or `get_sdk_reference` — never guess. Use `get_sdk_reference(topic='migration')` for V3→V4       |
| Wrong query flags                            | Use `get_sdk_reference(topic='flags')`                                                                                   |
| "These shouldn't have matched"               | Use SDK "why" method via `get_sdk_reference` for match details                                                           |
| Expecting perfect results immediately        | Iterate: adjust mappings, confidence scores, add attributes                                                              |
| Skipping UAT                                 | Always conduct UAT with business users before production (see Module 6)                                              |

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
| Corporate proxy blocking MCP         | Allowlist `mcp.senzing.com:443`. Set `HTTPS_PROXY` if behind proxy. Modules 1-4 work without MCP         |
| Not reading error messages           | Read carefully, use `explain_error_code`                                                                 |
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
| Senzing DLLs not found at runtime | Add Senzing `lib` directory to `PATH` — check `sdk_guide` output for the exact path |
| Emoji/Unicode garbled in terminal | Use Windows Terminal or PowerShell 7 instead of `cmd.exe`. Install: `winget install Microsoft.WindowsTerminal` |
| `source` command not found | `source` is bash-only. Use `. .\scripts\senzing-env.ps1` (PowerShell) or `call scripts\senzing-env.bat` (cmd) |

## MCP Server Unavailable

Load `mcp-offline-fallback.md` for detailed blocked/continuable operation tables, per-operation fallback instructions, reconnection procedures, and connectivity troubleshooting.

<a id="recovery"></a>

## Recovery Quick Reference

- **Loaded wrong data** → `python3 scripts/restore_project.py backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip`
- **Wrong transformation** → Delete bad output, fix program, re-run on sample, validate with `analyze_record`
- **Lost mapping state** → Restart workflow, reuse artifacts from `docs/` and `src/transform/`
- **Corrupted git file** → `git checkout HEAD -- src/transform/program.[ext]`

<a id="pre-module-checklist"></a>

## Pre-Module Checklist

Before starting any module: previous module complete and validated · documentation up to date · code committed to git · backup created (if applicable) · sample data tested · error handling in place
