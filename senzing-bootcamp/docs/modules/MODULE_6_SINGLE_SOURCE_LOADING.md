# Module 6: Load Single Data Source

> **Agent workflow:** The agent follows `steering/module-06-single-source.md` for this module's step-by-step workflow.

## Overview

Module 6 focuses on loading ONE data source into Senzing and verifying the results. This module teaches the fundamentals of loading before tackling multi-source orchestration in Module 7.

**Focus:** Load a single data source successfully and understand the loading process.

## Prerequisites

- ✅ Module 0 complete (SDK installed and configured)
- ✅ Database configured (SQLite or PostgreSQL)
- ✅ At least one transformed data source in `data/transformed/`
- ✅ Transformation validated with linter

## Learning Objectives

By the end of this module, you will:

1. Understand Senzing loading concepts (data sources, records, entities)
2. Generate a loading program for your data
3. Load records into Senzing
4. Verify loading statistics
5. Understand incremental loading strategies
6. Handle loading errors

## Key Concepts

### Data Source

A **data source** is a named collection of records from a single system or file. Examples:

- `CUSTOMERS_CRM` - Customer records from CRM system
- `VENDORS_ERP` - Vendor records from ERP system
- `EMPLOYEES_HR` - Employee records from HR system

**Important:** Each data source must be registered with Senzing before loading.

### Record ID

Every record must have a unique `RECORD_ID` within its data source. The combination of `DATA_SOURCE` + `RECORD_ID` uniquely identifies a record in Senzing.

### Entity

An **entity** is Senzing's resolved view of a real-world person or organization. Multiple records may resolve to the same entity if they represent the same real-world thing.

## Quick Test Path: mapping_workflow Steps 5-8

> **Agent instruction:** Before the user writes custom loading and query programs,
> offer the `mapping_workflow` quick test path. Steps 5-8 of the mapping workflow can
> detect the SDK environment, load test data into a fresh SQLite DB, generate a
> validation report, and evaluate results — all without writing any code.
>
> Call `mapping_workflow` with `action='advance'` to continue from where Module 5 left off.
> This gives the user fast feedback on whether their mapping produces good entity resolution
> results before investing time in custom loading programs.
>
> If the user wants to proceed with the quick test path, advance through steps 5-8.
> If they prefer to write their own loading program, skip to the Workflow section below.

## Workflow

### Step 1: Choose Data Source to Load

Start with ONE data source:

- Choose the simplest or most important source first
- Verify the transformed file exists in `data/transformed/`
- Verify the file passed linting (Module 4)

### Step 2: Register Data Source

Before loading, register the data source name with Senzing.

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='configure', version='current')`
> to get the current data source registration pattern. Do not use the legacy code pattern below.

Use the `generate_scaffold` MCP tool with `workflow='configure'` to get the current SDK code for registering data sources.

### Step 3: Generate Loading Program

Generate a loading program using the Senzing MCP server:

```text
Use: generate_scaffold
Parameters:
  language: <chosen_language>
  workflow: add_records
  version: current
```

The scaffold will include:

- SDK initialization
- Data source registration
- Record loading loop
- Error handling
- Statistics tracking
- Proper cleanup

### Step 4: Customize Loading Program

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`
> to get the current record loading pattern. Customize the generated scaffold with:
>
> 1. The user's input file path
> 2. The user's data source name
> 3. Progress reporting every N records
> 4. Error logging for failed records
> 5. Statistics tracking (loaded, failed, duration)
>
> Do not use the example code below — it may use outdated SDK patterns.

The `generate_scaffold` tool with `workflow='add_records'` provides the current SDK loading pattern. Customize it with your file path, data source name, and progress reporting.

### Step 5: Run Loading Program

Execute the loading program using the appropriate command for your chosen language from the `src/load/` directory.

Monitor the output for:

- Progress updates
- Error messages
- Final statistics

### Step 6: Verify Loading

After loading, verify the results using SDK query methods.

> **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')`
> or `get_sdk_reference(topic='functions', filter='get_entity', version='current')` to get
> the current method signatures for verifying loaded data. Do not guess method names.

Expected output:

```json
{
  "CUSTOMERS_CRM": {
    "RECORDS": 10000,
    "ENTITIES": 9850
  }
}
```

**Interpretation**:

- 10,000 records loaded
- 9,850 unique entities created
- 150 records matched to existing entities (duplicates found)

## Incremental Loading

For production systems, you'll need to load only new or changed records instead of reloading everything. Use MCP `search_docs` with query "incremental loading" for current strategies.

### Quick Overview

**Full Reload** (Module 6 default):

```text
Load all records every time:
  For each record in the source file:
      Call engine.addRecord(DATA_SOURCE, record_id, record)
```

**Incremental Load** (Production):

```text
Load only records modified since last load:
  Determine last_load_time
  For each record in the source file:
      If record.modified_date > last_load_time:
          Call engine.addRecord(DATA_SOURCE, record_id, record)
```

**When to use**:

- Full reload: Small datasets (< 100K), infrequent updates
- Incremental: Large datasets, frequent updates, production systems

**Agent behavior**: For Module 6, generate full reload scripts. Mention incremental loading as a future enhancement. Use MCP `search_docs` if user asks about incremental loading.

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
          Call engine.addRecord(DATA_SOURCE, record_id, record_json)
      On error:
          Append { record_id, error_message, record } to error log

  Save error log to logs/loading_errors.json
```

## Loading Statistics

Track and document loading statistics:

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

Save this in `docs/loading_statistics_[data_source].md`.

## Validation Gates

Before proceeding to Module 7, verify:

- [ ] Loading program generated and customized
- [ ] Data source registered with Senzing
- [ ] Records loaded successfully (> 95% success rate)
- [ ] Loading statistics documented
- [ ] Errors reviewed and understood
- [ ] Entity counts make sense (not all records = entities)
- [ ] Sample queries work (test with a few record IDs)

## Success Indicators

Module 6 is complete when:

- At least one data source is fully loaded
- Loading statistics are documented
- Errors are minimal and understood
- You can query loaded records successfully
- Ready to load additional sources (Module 7) or query results (Module 8)

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
- Review data quality scores from Module 4

## Integration with Other Modules

- **From Module 0:** Uses installed SDK and configured database
- **From Module 5:** Loads transformed data files
- **To Module 7:** Single-source loading is foundation for multi-source orchestration
- **To Module 8:** Loaded data is queried and validated

## File Locations

```text
project/
├── src/
│   └── load/
│       ├── load_customers_crm.[ext]   # Generated loading program
│       ├── load_vendors_erp.[ext]     # Additional sources
│       └── utils.[ext]                # Shared loading utilities
├── data/
│   └── transformed/
│       ├── customers_crm.jsonl        # Input file
│       └── vendors_erp.jsonl
├── logs/
│   ├── loading_errors.json            # Error log
│   └── loading.log                    # Detailed log
└── docs/
    ├── loading_statistics_customers_crm.md  # Statistics
    └── loading_strategy.md                  # Strategy documentation
```

## Agent Behavior

When a user is in Module 6:

1. **Verify prerequisites:** Check Module 5 complete, transformed data exists
2. **Choose data source:** Help user select which source to load first
3. **Generate loading program:** Use `generate_scaffold` with `add_records` workflow
4. **Customize program:** Add file path, data source name, progress reporting
5. **Save program:** Save to `src/load/load_[data_source].[ext]`
6. **Guide execution:** Help user run the program
7. **Review statistics:** Analyze loading results
8. **Handle errors:** Help diagnose and fix any errors
9. **Document results:** Create loading statistics document
10. **Validate success:** Verify loading gates before proceeding

**If user asks about incremental loading:** Use MCP `search_docs` with query "incremental loading" and explain strategies.

**If user has multiple sources:** After first source succeeds, offer to continue with Module 6 for additional sources, or proceed to Module 7 for orchestration.

## Related Documentation

- `POWER.md` - Module 6 overview
- `steering/module-06-single-source.md` - Module 6 workflow
- `steering/agent-instructions.md` - Agent behavior for Module 6
- Use MCP: `search_docs(query="incremental loading")` for incremental loading strategies
- Use MCP: `search_docs(query="performance optimization")` for performance optimization
- Use MCP: `search_docs(query="backup and recovery")` for backup and recovery

## Version History

- **v3.0.0** (2026-03-17): Module 6 refocused on single-source loading with incremental loading enhancement
