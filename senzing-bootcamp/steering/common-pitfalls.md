---
inclusion: manual
---

# Common Pitfalls Quick Reference

Load on errors, when user is stuck, or preventively at module start. For visual diagnostics, load `troubleshooting-decision-tree.md` instead.

## Module 0: SDK Setup

| Pitfall                                      | Fix                                                                          |
| -------------------------------------------- | ---------------------------------------------------------------------------- |
| Installing over existing SDK                 | Check first: `ls -la /opt/senzing` or language-appropriate import check      |
| SQLite for production                        | SQLite for evaluation only (<1M records). PostgreSQL for production           |
| Skipping anti-pattern check                  | Always call `search_docs(category='anti_patterns')`                          |
| Wrong platform commands                      | Use `sdk_guide` with correct `platform` parameter                            |
| Missing `SENZING_ENGINE_CONFIGURATION_JSON`  | Follow `sdk_guide` configuration exactly                                     |

### SQLite → PostgreSQL Migration

When to migrate: >100K records and slow, need multi-threading, preparing for Modules 9-12.

Steps: Install PostgreSQL (Linux: `apt install postgresql`, macOS: `brew install postgresql`, Windows: download from postgresql.org) → `sdk_guide(topic='configure')` for new config → Reload data from JSONL (SQLite data doesn't transfer) → Update `bootcamp_preferences.yaml` → Re-validate queries.

What carries forward: all code, transformed data, docs, config. What doesn't: the SQLite DB file.

## Module 1: Quick Demo

| Pitfall                                  | Fix                                                                              |
| ---------------------------------------- | -------------------------------------------------------------------------------- |
| Using `get_stats()` for record counts    | `get_stats()` tracks per-process stats, not totals. Use a counter during loading |

## Module 2: Business Problem

| Pitfall                              | Fix                                                                  |
| ------------------------------------ | -------------------------------------------------------------------- |
| Problem too vague ("clean my data")  | Ask: what issue, which systems, desired outcome, success metric      |
| Too many data sources (10+)          | Prioritize 1-2 sources, expand later                                 |
| Unrealistic expectations             | Set clear expectations about what ER can/cannot do                   |

## Module 3: Data Collection

| Pitfall                            | Fix                                                          |
| ---------------------------------- | ------------------------------------------------------------ |
| Not documenting data locations     | Document all sources in `docs/data_source_locations.md`      |
| Mixing raw and transformed data    | Raw → `data/raw/`, transformed → `data/transformed/`         |
| Loading entire large datasets      | Create representative samples (1K-10K records)               |

## Module 4: Data Quality

| Pitfall                                  | Fix                                                      |
| ---------------------------------------- | -------------------------------------------------------- |
| Insufficient sample data (2-3 records)   | Request 100-1000 records minimum                         |
| Skipping quality scoring                 | Always run automated scoring for objective metrics       |
| Ignoring quality issues                  | Address during mapping (Module 5)                        |
| Proceeding with score <70%               | Improve quality first or adjust expectations             |

## Module 5: Data Mapping

| Pitfall                                          | Fix                                                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Hand-coding attribute names                      | ALWAYS use `mapping_workflow` — never guess. Use `search_docs(query="entity specification")` for reference    |
| Missing `DATA_SOURCE` or `RECORD_ID`             | Every record MUST have both fields                                                                           |
| Running transformation on full dataset first     | Test on 10-100 records first                                                                                 |
| Skipping `analyze_record` after transform        | Always validate output quality                                                                               |
| Generated files in project root                  | Relocate: scripts→`src/transform/`, JSONL→`data/transformed/`, docs→`docs/`, shell→`scripts/`               |

### Mapping Workflow State Loss

State cannot be reconstructed — you must restart. Recover quickly by:

1. Check `docs/mapping_specifications.md` for documented mappings
2. Check `src/transform/` and `data/transformed/` for existing artifacts
3. Restart `mapping_workflow` with `action='start'` and same source file
4. Use documented mappings to fast-track through steps
5. If transform program exists and works, just validate with `analyze_record`

Prevention: warn user before long mapping sessions that state doesn't persist across sessions.

## Module 6: Single Source Loading

| Pitfall                                          | Fix                                                                          |
| ------------------------------------------------ | ---------------------------------------------------------------------------- |
| No database backup                               | ALWAYS backup before loading (use backup hook)                               |
| Loading without testing                          | Test with 100 records first                                                  |
| Ignoring error codes                             | Use `explain_error_code` for every error, fix root cause                     |
| Wrong DATA_SOURCE name                           | Verify matches Module 0 configuration                                       |
| Duplicate RECORD_IDs                             | Ensure unique within each DATA_SOURCE. Append sequence number if needed      |
| Poor DATA_SOURCE naming (`file1`, `data`)        | Use descriptive uppercase: `CUSTOMERS_CRM`, `VENDORS_ERP`                   |
| No progress monitoring                           | Add progress logging to loading programs                                     |
| Manual multi-source loading                      | Use Module 7 orchestration instead                                           |

## Module 7: Multi-Source Orchestration

| Pitfall                                  | Fix                                                          |
| ---------------------------------------- | ------------------------------------------------------------ |
| Wrong load order                         | Define order based on dependencies                           |
| No per-source error handling             | Implement per-source error handling, continue on failure     |
| Not tracking multi-source progress       | Use orchestration dashboard or logging                       |

## Module 8: Query and Validation

| Pitfall                                      | Fix                                                                                                                      |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Guessing SDK method names                    | Use `generate_scaffold` or `get_sdk_reference` — never guess. Use `get_sdk_reference(topic='migration')` for V3→V4      |
| Wrong query flags                            | Use `get_sdk_reference(topic='flags')`                                                                                   |
| "These shouldn't have matched"               | Use SDK "why" method via `get_sdk_reference` for match details                                                           |
| Expecting perfect results immediately        | Iterate: adjust mappings, confidence scores, add attributes                                                              |
| Skipping UAT                                 | Always conduct UAT with business users before production                                                                 |

## Modules 9-12: Production Readiness

| Pitfall                          | Fix                                                      |
| -------------------------------- | -------------------------------------------------------- |
| Skipping performance testing     | Complete Module 9 before production                      |
| No security hardening            | Complete Module 10 checklist                             |
| No monitoring                    | Complete Module 11 setup                                 |
| No disaster recovery plan        | Complete Module 12 DR planning and test backups          |

## General Pitfalls

| Pitfall                              | Fix                                                                                                      |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Corporate proxy blocking MCP         | Allowlist `mcp.senzing.com:443`. Set `HTTPS_PROXY` if behind proxy. Modules 2-4 work without MCP        |
| Not reading error messages           | Read carefully, use `explain_error_code`                                                                 |
| Guessing instead of searching docs   | Use `search_docs` liberally                                                                              |
| Not committing to git               | Commit after each module completion                                                                      |
| Working in production first          | Always develop locally or in dev environment                                                             |
| Not documenting decisions            | Document in `docs/` as you go                                                                            |
| Rushing through modules              | Complete each module fully before proceeding                                                             |

## MCP Server Unavailable — What You Can Still Do

If the MCP server is down, slow, or unreachable (corporate proxy, network outage, etc.), don't stop working. Here's what requires MCP and what doesn't:

### Works WITHOUT MCP (keep going)

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| Define business problem  | 2       | Fully independent of MCP — document problem, identify sources, define success criteria |
| Collect data             | 3       | Copy/download data files into `data/raw/`, document locations                          |
| Profile data manually    | 4       | Read CSV/JSON files, count rows, check columns, assess quality by inspection           |
| Review/edit existing code| Any     | Fix bugs, refactor, add comments, improve error handling                               |
| Write documentation      | Any     | Update `docs/`, write journal entries, create runbooks                                 |
| Run existing programs    | 5-8    | Transformation, loading, and query programs that are already written still run          |
| Git operations           | Any     | Commit, branch, review diffs                                                           |
| Backup/restore           | Any     | `python scripts/backup_project.py` / `restore_project.py`                             |
| Check progress           | Any     | `python scripts/status.py`, `python scripts/validate_module.py`                       |

### BLOCKED without MCP (wait or use fallbacks)

| Activity                   | Modules    | Fallback                                                                                                    |
| -------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------- |
| Get attribute names        | 5          | Check `docs/mapping_*.md` from previous sessions for documented mappings. Do NOT guess attribute names.     |
| Generate SDK code          | 0, 1, 6, 8| Use `find_examples` (may work if cached). Check `src/` for existing scaffold code to adapt.                 |
| Validate mapped records    | 5, 7       | Run transformation program and inspect output manually. Full validation waits for MCP.                      |
| Look up error codes        | Any        | Note the error code and message. Check docs.senzing.com or email <support@senzing.com>.                     |
| Search Senzing docs        | Any        | Go to docs.senzing.com directly in your browser.                                                            |
| Start new mapping workflow | 5          | Cannot start — `mapping_workflow` requires MCP. Work on other data sources or documentation instead.        |

### What to tell the user

"The Senzing MCP server isn't responding right now. Here's what we can keep working on while we wait: [list applicable activities from the table above]. The things that need MCP — like generating new SDK code or starting a mapping workflow — we'll pick up once the connection is back. I'll retry periodically."

## Recovery Quick Reference

| Problem                  | Recovery                                                                                                     |
| ------------------------ | ------------------------------------------------------------------------------------------------------------ |
| Loaded wrong data        | `python scripts/restore_project.py backups/senzing-bootcamp-backup_YYYYMMDD_HHMMSS.zip`                     |
| Wrong transformation     | Delete `data/transformed/bad_output.jsonl`, fix program, re-run on sample, validate with `analyze_record`    |
| Lost mapping state       | Restart workflow, reuse artifacts from `docs/` and `src/transform/`                                          |
| Corrupted git file       | `git checkout HEAD -- src/transform/program.[ext]`                                                           |

## Pre-Module Checklist

- [ ] Previous module complete and validated
- [ ] Documentation up to date
- [ ] Code committed to git
- [ ] Backup created (if applicable)
- [ ] Sample data tested
- [ ] Error handling in place
