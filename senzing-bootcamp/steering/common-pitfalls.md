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

## MCP Server Unavailable — What You Can Still Do

If the MCP server is down, slow, or unreachable (corporate proxy, network outage, etc.), don't stop working. Use this section to determine exactly what's blocked, what can continue, and what fallback to use for each blocked operation.

### Blocked Operations (Require MCP)

These operations depend on a specific MCP tool and cannot proceed without a working MCP connection.

| Operation                  | MCP Tool             | Affected Modules | Fallback Summary                                                  |
| -------------------------- | -------------------- | ---------------- | ----------------------------------------------------------------- |
| Attribute mapping          | `mapping_workflow`   | 5, 7             | Refer to docs.senzing.com entity specification; check `docs/mapping_*.md` |
| Code generation            | `generate_scaffold`  | 0, 1, 6, 8      | Check `src/` for existing scaffold code to adapt                  |
| Error diagnosis            | `explain_error_code` | Any              | Note error code; check docs.senzing.com; email support@senzing.com |
| SDK reference lookup       | `get_sdk_reference`  | 0, 6, 8          | Browse docs.senzing.com SDK docs; check `src/` for usage patterns |
| Documentation search       | `search_docs`        | Any              | Browse docs.senzing.com directly in browser                       |

### Continuable Operations (No MCP Needed)

These operations rely on local files, existing artifacts, or general knowledge — no MCP connection required.

#### Data Preparation

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| Define business problem  | 2       | Fully independent of MCP — document problem, identify sources, define success criteria |
| Collect data             | 3       | Copy/download data files into `data/raw/`, document locations                          |
| Profile data manually    | 4       | Read CSV/JSON files, count rows, check columns, assess quality by inspection           |

#### Documentation & Review

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| Write documentation      | Any     | Update `docs/`, write journal entries, create runbooks                                 |
| Review/edit existing code| Any     | Fix bugs, refactor, add comments, improve error handling                               |
| Check progress           | Any     | `python scripts/status.py`, `python scripts/validate_module.py`                        |

#### Code & Infrastructure Maintenance

| Activity                 | Modules | What to do                                                                             |
| ------------------------ | ------- | -------------------------------------------------------------------------------------- |
| Project structure setup  | Any     | Create directories, configure files, set up `config/` and `data/` layout               |
| Run existing programs    | 5-8     | Transformation, loading, and query programs that are already written still run          |
| Backup/restore           | Any     | `python scripts/backup_project.py` / `restore_project.py`                              |
| Git operations           | Any     | Commit, branch, review diffs                                                           |

### Fallback Instructions by Operation

When a bootcamper requests a blocked operation, use these specific fallback steps:

**Attribute mapping** (`mapping_workflow` unavailable):
1. Check `docs/mapping_specifications.md` and `docs/mapping_*.md` for mappings documented in previous sessions
2. Refer the bootcamper to the Senzing entity specification at <https://docs.senzing.com>
3. Do NOT guess attribute names — document what needs mapping and resume when MCP returns
4. Work on other data sources or documentation in the meantime

**Code generation** (`generate_scaffold` unavailable):
1. Check `src/` for existing scaffold code from previous modules that can be adapted
2. Check `senzing-bootcamp/examples/` for reference implementations
3. Review previously generated code for patterns to reuse
4. Do NOT hand-write Senzing SDK calls from memory — adapt only from existing verified code

**Error diagnosis** (`explain_error_code` unavailable):
1. Note the exact error code and full error message
2. Direct the bootcamper to search for the error code at <https://docs.senzing.com>
3. If unresolved, recommend emailing <support@senzing.com> with the error details
4. Document the error in `docs/` for follow-up when MCP reconnects

**SDK reference lookup** (`get_sdk_reference` unavailable):
1. Direct the bootcamper to the Senzing SDK documentation at <https://docs.senzing.com>
2. Check existing code in `src/` for usage patterns of the method in question
3. Do NOT guess method signatures or parameter names

**Documentation search** (`search_docs` unavailable):
1. Direct the bootcamper to browse <https://docs.senzing.com> directly in their browser
2. Check `senzing-bootcamp/docs/` for locally available documentation
3. Check `senzing-bootcamp/docs/guides/GLOSSARY.md` for term definitions

### What to Tell the Bootcamper

"The Senzing MCP server isn't responding right now. Here's what we can keep working on while we wait: [list applicable continuable activities from the tables above]. The things that need MCP — like generating new SDK code or starting a mapping workflow — we'll pick up once the connection is back. I'll retry periodically. In the meantime, I have specific fallback steps for each blocked operation if you need them."

### Reconnection Procedure

Follow these steps to detect MCP recovery and resume normal operations:

1. **Initial failure**: Retry the failed MCP call once (per `agent-instructions.md`)
2. **Enter offline mode**: If the retry fails, switch to fallback instructions above
3. **Periodic retry**: Attempt an MCP call approximately every 10 minutes, or when the bootcamper requests a retry
4. **Verify recovery**: On first successful MCP response, call `get_capabilities` to confirm full server functionality
5. **Resume operations**: Inform the bootcamper that MCP is available again and list any previously blocked operations that can now resume
6. **Re-query stale data**: If the outage spanned a module boundary, re-query MCP for fresh data per the reuse rules in `agent-instructions.md`

### Connectivity Troubleshooting

If MCP failures persist, check these common causes:

| Issue                        | Fix                                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------- |
| Corporate proxy blocking MCP | Allowlist `mcp.senzing.com:443`. Set `HTTPS_PROXY` environment variable if behind proxy  |
| Network connectivity         | Test: `curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443` (expect 200 or 403) |
| MCP server not started       | Restart the MCP server connection in the IDE (check Kiro Powers panel)                   |
| Intermittent timeouts        | Retry with a longer timeout; check if other network-dependent tools also fail            |
| DNS resolution failure       | Verify DNS can resolve `mcp.senzing.com`; try `nslookup mcp.senzing.com`                |

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
