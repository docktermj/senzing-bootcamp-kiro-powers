---
inclusion: manual
---

# Common Pitfalls Quick Reference

Load on errors, when user is stuck, or preventively at module start. For visual diagnostics, load `troubleshooting-decision-tree.md` instead.

## Quick Navigation

Jump to the relevant module section instead of scanning the entire file:

- [Module 0: SDK Setup](#module-0)
- [Module 1: Quick Demo](#module-1)
- [Module 2: Business Problem](#module-2)
- [Module 3: Data Collection](#module-3)
- [Module 4: Data Quality](#module-4)
- [Module 5: Data Mapping](#module-5)
- [Module 6: Single Source Loading](#module-6)
- [Module 7: Multi-Source Orchestration](#module-7)
- [Module 8: Query and Validation](#module-8)
- [Modules 9-12: Production Readiness](#modules-9-12)
- [General Pitfalls](#general-pitfalls)
- [MCP Server Unavailable](#mcp-unavailable)
- [Recovery Quick Reference](#recovery)
- [Pre-Module Checklist](#pre-module-checklist)

## Guided Troubleshooting — Ask Before Scanning

When the user says "I'm stuck" or reports an error, don't just present the tables below. Ask these diagnostic questions first (one at a time, WAIT for each):

1. "What module are you working on?" (narrows to the right section below)
2. "What were you trying to do when the problem happened?" (narrows to the specific step)
3. "Did you see an error message? If so, what did it say?" (if SENZ error → use `explain_error_code`; if other → check the pitfall tables)

Then use their answers to jump to the relevant section and present only the matching pitfall/fix — not the entire table.

**Navigation tip:** Once you know the module number, use the [Quick Navigation](#quick-navigation) anchor links above to jump directly to that module's section. Present only the matching pitfall and fix to the bootcamper — do not present pitfalls from other modules.

<a id="module-0"></a>

## Module 0: SDK Setup

| Pitfall                                      | Fix                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------- |
| Installing over existing SDK                 | Check first: `ls -la /opt/senzing` or language-appropriate import check      |
| SQLite for production                        | SQLite for evaluation only (<1M records). PostgreSQL for production          |
| Skipping anti-pattern check                  | Always call `search_docs(category='anti_patterns')`                          |
| Wrong platform commands                      | Use `sdk_guide` with correct `platform` parameter                            |
| Missing `SENZING_ENGINE_CONFIGURATION_JSON`  | Follow `sdk_guide` configuration exactly                                     |

### SQLite → PostgreSQL Migration

When to migrate: >100K records and slow, need multi-threading, preparing for Modules 9-12.

Steps: Install PostgreSQL (Linux: `apt install postgresql`, macOS: `brew install postgresql`, Windows: download from postgresql.org) → `sdk_guide(topic='configure')` for new config → Reload data from JSONL (SQLite data doesn't transfer) → Update `bootcamp_preferences.yaml` → Re-validate queries.

What carries forward: all code, transformed data, docs, config. What doesn't: the SQLite DB file.

<a id="module-1"></a>

## Module 1: Quick Demo

| Pitfall                                  | Fix                                                                              |
| ---------------------------------------- | -------------------------------------------------------------------------------- |
| Using `get_stats()` for record counts    | `get_stats()` tracks per-process stats, not totals. Use a counter during loading |

<a id="module-2"></a>

## Module 2: Business Problem

| Pitfall                              | Fix                                                                  |
| ------------------------------------ | -------------------------------------------------------------------- |
| Problem too vague ("clean my data")  | Ask: what issue, which systems, desired outcome, success metric      |
| Too many data sources (10+)          | Prioritize 1-2 sources, expand later                                 |
| Unrealistic expectations             | Set clear expectations about what ER can/cannot do                   |

<a id="module-3"></a>

## Module 3: Data Collection

| Pitfall                            | Fix                                                          |
| ---------------------------------- | ------------------------------------------------------------ |
| Not documenting data locations     | Document all sources in `docs/data_source_locations.md`      |
| Mixing raw and transformed data    | Raw → `data/raw/`, transformed → `data/transformed/`         |
| Loading entire large datasets      | Create representative samples (1K-10K records)               |

<a id="module-4"></a>

## Module 4: Data Quality

| Pitfall                                  | Fix                                                                              |
| ---------------------------------------- | -------------------------------------------------------------------------------- |
| Insufficient sample data (2-3 records)   | Request 100-1000 records minimum                                                 |
| Skipping quality scoring                 | Always run automated scoring for objective metrics                               |
| Ignoring quality issues                  | Address during mapping (Module 5)                                                |
| Proceeding with low quality              | Use the three-tier gate: ≥80% proceed, 70-79% warn and let user decide, <70% recommend fixing first |

<a id="module-5"></a>

## Module 5: Data Mapping

| Pitfall                                          | Fix                                                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Hand-coding attribute names                      | ALWAYS use `mapping_workflow` — never guess. Use `search_docs(query="entity specification")` for reference   |
| Missing `DATA_SOURCE` or `RECORD_ID`             | Every record MUST have both fields                                                                           |
| Running transformation on full dataset first     | Test on 10-100 records first                                                                                 |
| Skipping `analyze_record` after transform        | Always validate output quality                                                                               |
| Generated files in project root                  | Relocate: scripts→`src/transform/`, JSONL→`data/transformed/`, docs→`docs/`, shell→`scripts/`                |

### Mapping Workflow State Loss

State cannot be reconstructed — you must restart. Recover quickly by:

1. Check `docs/mapping_specifications.md` for documented mappings
2. Check `src/transform/` and `data/transformed/` for existing artifacts
3. Restart `mapping_workflow` with `action='start'` and same source file
4. Use documented mappings to fast-track through steps
5. If transform program exists and works, just validate with `analyze_record`

Prevention: warn user before long mapping sessions that state doesn't persist across sessions.

<a id="module-6"></a>

## Module 6: Single Source Loading

| Pitfall                                          | Fix                                                                          |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| No database backup                               | ALWAYS backup before loading (use backup hook)                               |
| Loading without testing                          | Test with 100 records first                                                  |
| Loading 5,000+ records on SQLite                 | Start with ≤1,000 records. Single-threaded ER slows as DB grows. Use PostgreSQL for larger volumes. |
| Ignoring error codes                             | Use `explain_error_code` for every error, fix root cause                     |
| Wrong DATA_SOURCE name                           | Verify matches Module 0 configuration                                        |
| Duplicate RECORD_IDs                             | Ensure unique within each DATA_SOURCE. Append sequence number if needed      |
| Poor DATA_SOURCE naming (`file1`, `data`)        | Use descriptive uppercase: `CUSTOMERS_CRM`, `VENDORS_ERP`                    |
| No progress monitoring                           | Add progress logging to loading programs                                     |
| Manual multi-source loading                      | Use Module 7 orchestration instead                                           |

<a id="module-7"></a>

## Module 7: Multi-Source Orchestration

| Pitfall                                  | Fix                                                          |
| ---------------------------------------- | ------------------------------------------------------------ |
| Wrong load order                         | Define order based on dependencies                           |
| No per-source error handling             | Implement per-source error handling, continue on failure     |
| Not tracking multi-source progress       | Use orchestration dashboard or logging                       |

<a id="module-8"></a>

## Module 8: Query and Validation

| Pitfall                                      | Fix                                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Guessing SDK method names                    | Use `generate_scaffold` or `get_sdk_reference` — never guess. Use `get_sdk_reference(topic='migration')` for V3→V4       |
| Wrong query flags                            | Use `get_sdk_reference(topic='flags')`                                                                                   |
| "These shouldn't have matched"               | Use SDK "why" method via `get_sdk_reference` for match details                                                           |
| Expecting perfect results immediately        | Iterate: adjust mappings, confidence scores, add attributes                                                              |
| Skipping UAT                                 | Always conduct UAT with business users before production                                                                 |

<a id="modules-9-12"></a>

## Modules 9-12: Production Readiness

| Pitfall                          | Fix                                                      |
| -------------------------------- | -------------------------------------------------------- |
| Skipping performance testing     | Complete Module 9 before production                      |
| No security hardening            | Complete Module 10 checklist                             |
| No monitoring                    | Complete Module 11 setup                                 |
| No disaster recovery plan        | Complete Module 12 DR planning and test backups          |

<a id="general-pitfalls"></a>

## General Pitfalls

| Pitfall                              | Fix                                                                                                      |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Corporate proxy blocking MCP         | Allowlist `mcp.senzing.com:443`. Set `HTTPS_PROXY` if behind proxy. Modules 2-4 work without MCP         |
| Not reading error messages           | Read carefully, use `explain_error_code`                                                                 |
| Guessing instead of searching docs   | Use `search_docs` liberally                                                                              |
| Not committing to git                | Commit after each module completion                                                                      |
| Working in production first          | Always develop locally or in dev environment                                                             |
| Not documenting decisions            | Document in `docs/` as you go                                                                            |
| Rushing through modules              | Complete each module fully before proceeding                                                             |

<a id="mcp-unavailable"></a>

## MCP Server Unavailable

Load `mcp-offline-fallback.md` for detailed blocked/continuable operation tables, per-operation fallback instructions, reconnection procedures, and connectivity troubleshooting.

<a id="recovery"></a>

## Recovery Quick Reference

| Problem                  | Recovery                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Loaded wrong data        | `python scripts/restore_project.py backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip`                      |
| Wrong transformation     | Delete `data/transformed/bad_output.jsonl`, fix program, re-run on sample, validate with `analyze_record`    |
| Lost mapping state       | Restart workflow, reuse artifacts from `docs/` and `src/transform/`                                          |
| Corrupted git file       | `git checkout HEAD -- src/transform/program.[ext]`                                                           |

<a id="pre-module-checklist"></a>

## Pre-Module Checklist

- [ ] Previous module complete and validated
- [ ] Documentation up to date
- [ ] Code committed to git
- [ ] Backup created (if applicable)
- [ ] Sample data tested
- [ ] Error handling in place
