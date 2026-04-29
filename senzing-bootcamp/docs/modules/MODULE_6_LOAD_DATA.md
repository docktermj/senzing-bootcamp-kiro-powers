```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 6: LOAD DATA  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 6: Load Data

> **Agent workflow:** The agent follows `steering/module-06-load-data.md` for this module's step-by-step workflow.

## Overview

Module 6 covers the complete data loading lifecycle — from building production-quality loading programs through cross-source validation. Whether you have one data source or many, this module walks you through loading all your data into Senzing with robust error handling, progress tracking, redo processing, and result validation.

The module adapts to your situation:
- **Single source:** Build a loading program, load your data, process redo records, validate results, and proceed to Module 7 (Query & Visualize).
- **Multiple sources:** After loading the first source, the module adds dependency analysis, load order optimization, orchestration strategy selection, cross-source validation, UAT with business users, and stakeholder sign-off.

If you completed Phase 3 (Test Load and Validate) in Module 5, the agent acknowledges your test load results and skips basic test loading. If you skipped Phase 3, the module includes a brief test load before moving to production concerns.

## Prerequisites

- ✅ Module 2 complete (SDK installed and configured)
- ✅ Module 5 complete (at least one data source mapped and transformed)
- ✅ Database configured (SQLite or PostgreSQL)
- ✅ At least one transformed data source in `data/transformed/`
- ✅ Transformation validated with linter

## Learning Objectives

By the end of this module, you will:

1. Build production-quality loading programs with robust error handling
2. Implement progress tracking with throughput reporting
3. Optimize loading performance for your data volume
4. Process the redo queue to refine entity resolution results
5. Understand incremental loading strategies for ongoing data updates
6. Validate match accuracy and document loading results for single-source scenarios
7. Manage dependencies between multiple data sources (multi-source path)
8. Optimize load order based on data quality and source relationships (multi-source path)
9. Implement parallel loading with error isolation between sources (multi-source path)
10. Coordinate redo processing across all sources for complete cross-source resolution (multi-source path)
11. Handle partial failures with retry, backoff, and partial success patterns (multi-source path)
12. Validate cross-source entity resolution results with UAT and stakeholder sign-off (multi-source path)

## Key Concepts

### Data Source

A **data source** is a named collection of records from a single system or file. Examples:

- `CUSTOMERS_CRM` — Customer records from CRM system
- `VENDORS_ERP` — Vendor records from ERP system
- `EMPLOYEES_HR` — Employee records from HR system

**Important:** Each data source must be registered with Senzing before loading.

### Record ID

Every record must have a unique `RECORD_ID` within its data source. The combination of `DATA_SOURCE` + `RECORD_ID` uniquely identifies a record in Senzing.

### Entity

An **entity** is Senzing's resolved view of a real-world person or organization. Multiple records may resolve to the same entity if they represent the same real-world thing.

### Redo Queue

Senzing's deferred re-evaluation queue. After loading records, some entity resolution decisions are deferred for later processing. Draining the redo queue refines the entity resolution graph — without processing redos, results are incomplete.

### Orchestration Patterns (Multi-Source)

When loading multiple sources, you choose an orchestration strategy:
- **Sequential:** Load one source at a time. Safer, easier to debug.
- **Parallel:** Load independent sources concurrently. Faster, requires more resources.
- **Dependency-Aware:** Respects dependencies between sources (e.g., load customers before orders).
- **Pipeline:** Streaming producer-consumer pattern for large datasets.

## Conditional Workflow

### Single-Source Path

If you have only one data source:

1. **Phase A:** Build a production-quality loading program
2. **Phase B:** Load your data source, process redo records
3. **Phase D:** Validate match accuracy, run basic UAT, document results
4. Proceed to Module 7 (Query & Visualize)

No orchestration, dependency analysis, or cross-source validation steps are presented.

### Multi-Source Path

If you have two or more data sources:

1. **Phase A:** Build a production-quality loading program
2. **Phase B:** Load the first source, process redo records
3. **Phase C:** Inventory all sources, analyze dependencies, determine load order, select strategy, create orchestrator, load remaining sources
4. **Phase D:** Single-source validation + cross-source validation, UAT with business users, stakeholder sign-off
5. Proceed to Module 7 (Query & Visualize)

### Phase 3 Shortcut (mapping-workflow-integration)

If the `mapping-workflow-integration` spec has been implemented and you completed Phase 3 (Test Load and Validate) in Module 5:
- The agent reads `test_load_status` from `config/data_sources.yaml`
- If `test_load_status: complete`, the basic test loading step is skipped — you proceed directly to production loading
- If `test_load_status: skipped` or missing, the module includes a brief test load (10–100 records) before production loading

If the mapping-workflow-integration spec has NOT been implemented, the module functions as a standalone loading module — all bootcampers go through the full loading workflow including the test load step.

## What You'll Do

1. **Build loading program** — Create a production-quality loading program with error handling, progress tracking, and statistics
2. **Load first source** — Test with sample data (if needed), then load the full dataset
3. **Process redo records** — Drain the redo queue to refine entity resolution
4. **Orchestrate remaining sources** (multi-source only) — Analyze dependencies, determine load order, create orchestrator, load all sources
5. **Validate results** — Review match accuracy, check for false positives/negatives, run UAT
6. **Document results** — Save loading statistics, validation results, and strategy documentation

## Validation Gates

Before completing Module 6, verify:

### Always Required

- [ ] Loading program generated and customized
- [ ] Data source(s) registered with Senzing
- [ ] Records loaded successfully (> 95% success rate)
- [ ] Loading statistics documented
- [ ] Errors reviewed and understood
- [ ] Entity counts make sense (not all records = entities)
- [ ] Sample queries work (test with a few record IDs)
- [ ] Redo queue drained
- [ ] Match accuracy reviewed (sample entities checked)
- [ ] False positives and false negatives reviewed
- [ ] Results validation documented in `docs/results_validation.md`

### Additional Gates for Multi-Source (2+ sources)

- [ ] All data sources identified and inventoried
- [ ] Dependencies documented
- [ ] Load order determined
- [ ] Orchestration script created
- [ ] Error handling configured with error isolation
- [ ] Progress tracking implemented
- [ ] Tested with sample data
- [ ] All sources loaded successfully
- [ ] Cross-source match accuracy reviewed
- [ ] UAT test cases created and executed
- [ ] All critical UAT tests pass
- [ ] Issues documented and resolved
- [ ] Stakeholder sign-off obtained

## Output Files

| File | Description | When Created |
|------|-------------|--------------|
| `src/load/load_[source].[ext]` | Loading program for each data source | Phase A |
| `src/load/orchestrator.[ext]` | Multi-source orchestrator program | Phase C (multi-source only) |
| `docs/loading_strategy.md` | Loading strategy, load order, and statistics | Phase B/C |
| `docs/loading_statistics_[source].md` | Per-source loading statistics | Phase B |
| `docs/results_validation.md` | Match accuracy and validation results | Phase D |
| `docs/uat_results.md` | UAT execution results | Phase D |
| `docs/results_dashboard.html` | Results visualization dashboard | Phase D (if accepted) |
| `docs/multi_source_results.html` | Cross-source entity visualization | Phase D (multi-source, if accepted) |
| `docs/stakeholder_summary_module6.md` | Executive summary for stakeholders | Phase D (if requested) |
| `logs/loading_errors.json` | Error log for failed records | Phase B |
| `logs/loading.log` | Detailed loading log | Phase B |

## File Location Map

```text
project/
├── src/
│   └── load/
│       ├── load_customers_crm.[ext]   # Loading program (per source)
│       ├── load_vendors_erp.[ext]     # Additional sources
│       ├── orchestrator.[ext]         # Multi-source orchestrator (if 2+ sources)
│       └── utils.[ext]                # Shared loading utilities
├── data/
│   └── transformed/
│       ├── customers_crm.jsonl        # Input file
│       └── vendors_erp.jsonl
├── logs/
│   ├── loading_errors.json            # Error log
│   ├── loading.log                    # Detailed log
│   └── orchestration.log             # Orchestration log (multi-source)
├── docs/
│   ├── loading_statistics_customers_crm.md  # Per-source statistics
│   ├── loading_strategy.md                  # Strategy documentation
│   ├── uat_results.md                       # UAT execution results
│   ├── results_validation.md                # Match accuracy and validation results
│   ├── results_dashboard.html               # Results visualization (if accepted)
│   ├── multi_source_results.html            # Cross-source visualization (if accepted)
│   └── stakeholder_summary_module6.md       # Executive summary (if requested)
└── config/
    ├── bootcamp_progress.json         # Step-level progress tracking
    └── data_sources.yaml              # Data source registry
```

## Loading Statistics

Track and document loading statistics for each source:

```markdown
# Loading Statistics - CUSTOMERS_CRM

**Date:** 2026-03-17
**File:** data/transformed/customers_crm.jsonl
**Data Source:** CUSTOMERS_CRM

## Results

- **Records Attempted:** 10,000
- **Records Loaded:** 9,995
- **Records Failed:** 5
- **Duration:** 50.2 seconds
- **Throughput:** 199 records/second

## Entity Resolution

- **Entities Created:** 9,850
- **Duplicates Found:** 145
- **Deduplication Rate:** 1.5%

## Errors

- SENZ0005 (Invalid JSON): 3 records
- SENZ0042 (Missing RECORD_ID): 2 records

See `logs/loading_errors.json` for details.
```

## Error Handling

### Common Loading Errors

> **Agent instruction:** Do not hardcode error explanations. For any SENZ error code
> encountered during loading, use `explain_error_code(error_code="<code>", version="current")`
> to get current causes and resolution steps. The MCP server covers all 456 error codes.

Use `explain_error_code` tool for detailed error diagnosis on any error encountered during loading.

### Error Logging

Log failed records for review:

```text
Error logging pattern:
  Initialize an empty error log list
  For each record to load:
      Try:
          Call engine.add_record(DATA_SOURCE, record_id, record_json)
      On error:
          Append { record_id, error_message, record } to error log

  Save error log to logs/loading_errors.json
```

## Incremental Loading

For production systems, you'll need to load only new or changed records instead of reloading everything. Use MCP `search_docs` with query "incremental loading" for current strategies.

### Quick Overview

**Full Reload** (Module 6 default):

```text
Load all records every time:
  For each record in the source file:
      Call engine.add_record(DATA_SOURCE, record_id, record)
```

**Incremental Load** (Production):

```text
Load only records modified since last load:
  Determine last_load_time
  For each record in the source file:
      If record.modified_date > last_load_time:
          Call engine.add_record(DATA_SOURCE, record_id, record)
```

**When to use:**

- Full reload: Small datasets (< 100K), infrequent updates
- Incremental: Large datasets, frequent updates, production systems

## Common Issues

### Issue: Slow Loading Performance

**Symptoms:** < 50 records/second
**Solutions:**

- Use batch loading (load multiple records per call)
- Optimize database (indexes, memory)
- Use PostgreSQL instead of SQLite
- Use MCP: `search_docs(query="performance optimization", category="performance")`

### Issue: High Error Rate

**Symptoms:** > 5% of records fail to load
**Solutions:**

- Review error messages
- Re-run linter on transformed data
- Check for data quality issues
- Validate transformation logic

### Issue: All Records Become One Entity

**Symptoms:** Entity count = 1
**Solutions:**

- Check RECORD_ID is unique per record
- Verify records have distinguishing features
- Review entity resolution configuration

### Issue: No Duplicates Found

**Symptoms:** Entity count = record count
**Solutions:**

- Verify data actually has duplicates
- Check matching features are present (names, addresses, etc.)
- Review data quality scores from Module 5

## Integration with Other Modules

- **From Module 2:** Uses installed SDK and configured database
- **From Module 5:** Loads transformed data files; optionally uses Phase 3 test load results
- **To Module 7:** Loaded data is queried and visualized (old Module 8)
- **To Module 8:** Performance testing and optimization (old Module 9)
- **Validation:** Single-source validation (match accuracy, false positive/negative review) and cross-source validation (UAT, stakeholder sign-off) are performed within this module

## Success Indicators

Module 6 is complete when:

- At least one data source is fully loaded
- Loading statistics are documented
- Errors are minimal and understood
- Redo queue is drained
- You can query loaded records successfully
- Match accuracy reviewed and results validated
- Ready to query results (Module 7)

### Additional indicators for multi-source:

- All data sources loaded successfully (or failures documented)
- Dependencies respected
- Cross-source match accuracy validated
- UAT completed with acceptable pass rate
- Stakeholder sign-off obtained
- Results validation documented and approved

## Agent Behavior

When a user is in Module 6:

1. **Check Phase 3 status:** Read `config/data_sources.yaml` for `test_load_status`
2. **Verify prerequisites:** Check Module 5 complete, transformed data exists
3. **Choose data source:** Help user select which source to load first
4. **Generate loading program:** Use `generate_scaffold` with `add_records` workflow
5. **Customize program:** Add file path, data source name, progress reporting
6. **Save program:** Save to `src/load/load_[data_source].[ext]`
7. **Guide execution:** Help user run the program
8. **Review statistics:** Analyze loading results
9. **Handle errors:** Help diagnose and fix any errors
10. **Process redo queue:** Drain redos after loading
11. **Check for more sources:** If 2+ sources, proceed to Phase C orchestration
12. **Validate results:** Guide match accuracy review and UAT
13. **Document results:** Create loading statistics and validation documents

**If user asks about incremental loading:** Use MCP `search_docs` with query "incremental loading" and explain strategies.

**If user has multiple sources:** After first source succeeds, proceed to Phase C for orchestration.

**If user has one source:** Skip Phase C, proceed to Phase D validation, then transition to Module 7.

## Related Documentation

- `POWER.md` — Module 6 overview
- `steering/module-06-load-data.md` — Module 6 workflow
- `steering/agent-instructions.md` — Agent behavior for Module 6
- Use MCP: `search_docs(query="incremental loading")` for incremental loading strategies
- Use MCP: `search_docs(query="performance optimization")` for performance optimization
- Use MCP: `search_docs(query="backup and recovery")` for backup and recovery

## Version History

- **v3.0.0** (2026-03-17): Module 6 created for single-source loading
- **v4.0.0** (2026-04-17): Renumbered from Module 6 to Module 6 (merge of old Modules 4+5)
- **v5.0.0** (2026-05-17): Combined old Module 6 (Single Source Loading) and Module 7 (Multi-Source Orchestration) into unified Load Data module
