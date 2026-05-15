---
inclusion: manual
---

# Troubleshooting Decision Tree

Visual flowchart for diagnosing common issues.

## Start Here: What's the Problem?

```text
What type of issue?
├─→ Installation/Setup   → Section A
├─→ Transformation       → Section B
├─→ Loading              → Section C
├─→ Query                → Section D
├─→ Performance          → Section E
├─→ Data Quality         → Section F
└─→ Database Corruption  → Section G
```

## Section A: Installation/Setup Issues

```text
Installation failing?
├─→ Platform mismatch?
│   └─→ Use sdk_guide with correct platform parameter
├─→ Missing dependencies?
│   └─→ Check error → Use search_docs(category="installation")
├─→ Permission errors?
│   └─→ Check file permissions → May need sudo for system-wide install
├─→ Database connection fails?
│   ├─→ SQLite: Check path exists → database/G2C.db
│   └─→ PostgreSQL: Verify host, port, credentials
└─→ Configuration errors?
    └─→ Use search_docs(category="anti_patterns")
```

## Section B: Transformation Issues

```text
Transformation not working?
├─→ Program crashes?
│   ├─→ Check input file exists and format (CSV, JSON, etc.)
│   ├─→ Test with small sample (10 records)
│   └─→ Check error message in logs/transform.log
├─→ Output validation fails?
│   ├─→ Run analyze_record → Fix attribute names via mapping_workflow
│   └─→ Missing required fields? → Add DATA_SOURCE and RECORD_ID
├─→ Low quality score?
│   ├─→ Run analyze_record → Check attribute coverage
│   │   └─→ < 70%? Add more field mappings
│   └─→ Check data completeness → Source data missing values?
└─→ Wrong attribute names?
    └─→ NEVER hand-code → Use mapping_workflow
        └─→ Use search_docs or download_resource for entity spec
```

## Section C: Loading Issues

```text
Loading failing?
├─→ Connection errors?
│   └─→ Verify SDK config from Module 2 → Test with simple add/get
├─→ Record errors?
│   ├─→ Get error code → Use explain_error_code(error_code="SENZXXXX")
│   └─→ Common: Invalid JSON, missing fields, wrong DATA_SOURCE, malformed values
├─→ Performance too slow?
│   ├─→ Use batch loading (1000 records/batch)
│   ├─→ SQLite slow for >100K records → Switch to PostgreSQL
│   └─→ Check system resources (CPU, memory, disk I/O)
├─→ Database corruption?
│   └─→ Restore: python3 scripts/restore_project.py <backup-file>
└─→ Partial load failure?
    └─→ Check failed records → Fix data → Restore from backup → Reload
```

## Section D: Query Issues

```text
Queries not working?
├─→ Method not found?
│   └─→ NEVER guess → Use generate_scaffold or get_sdk_reference
├─→ Wrong results?
│   ├─→ Too many matches?
│   │   ├─→ Use SDK "why" method (via get_sdk_reference)
│   │   ├─→ Lower confidence scores in mappings
│   │   └─→ Improve data quality
│   ├─→ Too few matches?
│   │   ├─→ Check data quality / Raise confidence scores
│   │   └─→ Add more matching attributes
│   └─→ Missing information?
│       └─→ Check query flags → get_sdk_reference(topic="flags")
├─→ Performance slow?
│   ├─→ Add database indexes
│   ├─→ Use appropriate query method
│   └─→ Check search_docs(category="performance")
└─→ No results found?
    ├─→ Verify data was loaded (check loading statistics)
    ├─→ Verify DATA_SOURCE name matches
    └─→ Check query parameters
```

## Section E: Performance Issues

```text
System too slow?
├─→ Transformation slow?
│   ├─→ Process in batches / Use multiprocessing
│   └─→ Check data source (DB query slow? API rate limited?)
├─→ Loading slow?
│   ├─→ SQLite: ~50 rec/sec │ PostgreSQL: 100-500 rec/sec
│   ├─→ Optimize batch size (try 100, 500, 1000)
│   ├─→ Check system resources (CPU, memory, disk I/O)
│   └─→ Use search_docs(category="performance")
├─→ Query slow?
│   ├─→ Add database indexes
│   ├─→ Use specific queries (not export all)
│   └─→ Check search_docs(category="database")
└─→ System resources maxed?
    ├─→ Check monitoring dashboard
    ├─→ Increase memory / more powerful hardware
    └─→ Consider distributed processing
```

## Section F: Data Quality Issues

```text
Poor matching results?
├─→ Review data quality from Module 5
│   └─→ Run analyze_record → Quality < 70%? → Back to Module 5
├─→ Missing critical attributes?
│   ├─→ Check attribute coverage / Add more field mappings
│   └─→ Consider additional data sources
├─→ Inconsistent data formats?
│   ├─→ Add cleansing: normalize phones, standardize addresses, clean names
│   └─→ Use confidence scores appropriately
└─→ Source data quality poor?
    ├─→ Document issues / Work with data owners
    └─→ Use anonymized test data / Set realistic expectations
```

## Section G: Database Corruption

```text
Database corruption suspected?
├─→ Database file missing?
│   ├─→ Run: python3 scripts/check_database.py --db-path database/G2C.db
│   ├─→ File never created? → Re-run Module 2 SDK setup to initialize database
│   └─→ File deleted accidentally? → Restore from backup or rebuild:
│       └─→ python3 scripts/restore_project.py <backup-file>
├─→ Connection fails?
│   ├─→ "database is locked" error?
│   │   ├─→ Close other processes accessing the database
│   │   └─→ Remove stale lock: rm database/G2C.db-wal database/G2C.db-shm
│   ├─→ "not a database" or "file is not a database" error?
│   │   └─→ File is corrupted beyond repair → Rebuild from scratch
│   └─→ Permission denied?
│       └─→ Check file permissions → chmod 644 database/G2C.db
├─→ Integrity check fails?
│   ├─→ Run: python3 scripts/check_database.py --repair
│   ├─→ Repair succeeded? → Re-run loading program to verify data
│   └─→ Repair failed?
│       ├─→ "database disk image is malformed"?
│       │   └─→ Database unrecoverable → Delete and rebuild from loading program
│       └─→ WAL corruption?
│           ├─→ Try: python3 scripts/check_database.py --repair (runs WAL checkpoint + vacuum)
│           └─→ Still failing? → Delete WAL file and rebuild
└─→ Entity count is zero?
    ├─→ Run: python3 scripts/check_database.py --db-path database/G2C.db
    ├─→ Load reported success but no entities?
    │   ├─→ Check for disk-full during load (df -h)
    │   └─→ Re-run loading program with fresh database
    └─→ Load was interrupted (process killed)?
        ├─→ Try: python3 scripts/check_database.py --repair
        └─→ If repair fails → Delete database/G2C.db and reload from scratch
```

## Diagnostic Commands

Load `troubleshooting-commands.md` for MCP diagnostic commands, system-level checks, and escalation procedures.
