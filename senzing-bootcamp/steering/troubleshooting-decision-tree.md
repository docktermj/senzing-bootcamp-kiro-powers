---
inclusion: manual
---

# Troubleshooting Decision Tree

Visual flowchart for diagnosing common issues.

## Start Here: What's the Problem?

```text
┌─────────────────────────────────────┐
│   What type of issue are you       │
│   experiencing?                     │
└─────────────────────────────────────┘
           │
           ├─→ Installation/Setup Issues → See Section A
           ├─→ Transformation Issues → See Section B
           ├─→ Loading Issues → See Section C
           ├─→ Query Issues → See Section D
           ├─→ Performance Issues → See Section E
           └─→ Data Quality Issues → See Section F
```

## Section A: Installation/Setup Issues

```text
Installation failing?
│
├─→ Platform mismatch?
│   └─→ Use sdk_guide with correct platform parameter
│       (linux_apt, linux_yum, macos_arm, windows)
│
├─→ Missing dependencies?
│   └─→ Check error message
│       └─→ Use search_docs(category="installation")
│
├─→ Permission errors?
│   └─→ Check file permissions
│       └─→ May need sudo for system-wide install
│
├─→ Database connection fails?
│   ├─→ SQLite: Check path exists
│   │   └─→ database/G2C.db
│   └─→ PostgreSQL: Check connection string
│       └─→ Verify host, port, credentials
│
└─→ Configuration errors?
    └─→ Use search_docs(category="anti_patterns")
        └─→ Check for known issues
```

## Section B: Transformation Issues

```text
Transformation not working?
│
├─→ Program crashes?
│   ├─→ Check input file exists
│   ├─→ Check file format (CSV, JSON, etc.)
│   ├─→ Test with small sample (10 records)
│   └─→ Check error message in logs/transform.log
│
├─→ Output validation fails?
│   ├─→ Run analyze_record on output
│   │   └─→ Fix attribute name errors
│   │       └─→ Use mapping_workflow (don't guess!)
│   └─→ Missing required fields?
│       └─→ Add DATA_SOURCE and RECORD_ID
│
├─→ Low quality score?
│   ├─→ Run analyze_record
│   ├─→ Check attribute coverage
│   │   └─→ < 70%? Add more field mappings
│   └─→ Check data completeness
│       └─→ Source data missing values?
│
└─→ Wrong attribute names?
    └─→ NEVER hand-code attribute names
        └─→ Use mapping_workflow
            └─→ Use search_docs or download_resource
                for the current entity specification
```

## Section C: Loading Issues

```text
Loading failing?
│
├─→ Connection errors?
│   └─→ Verify SDK configuration from Module 0
│       └─→ Test with simple add/get record
│
├─→ Record errors?
│   ├─→ Get error code from logs
│   ├─→ Use explain_error_code(error_code="SENZXXXX")
│   └─→ Common issues:
│       • Invalid JSON format
│       • Missing required fields
│       • Wrong DATA_SOURCE name
│       • Malformed attribute values
│
├─→ Performance too slow?
│   ├─→ Use batch loading (1000 records/batch)
│   ├─→ Check database performance
│   │   └─→ SQLite slow for >100K records
│   │       └─→ Switch to PostgreSQL
│   └─→ Check system resources
│       └─→ CPU, memory, disk I/O
│
├─→ Database corruption?
│   └─→ Restore from backup
│       └─→ python scripts/restore_project.py <backup-file>
│
└─→ Partial load failure?
    ├─→ Check which records failed
    ├─→ Fix data quality issues
    ├─→ Restore from backup
    └─→ Reload with fixed data
```

## Section D: Query Issues

```text
Queries not working?
│
├─→ Method not found?
│   └─→ NEVER guess method names
│       └─→ Use generate_scaffold or get_sdk_reference
│
├─→ Wrong results?
│   ├─→ Too many matches?
│   │   ├─→ Use whyEntities to see why they matched
│   │   ├─→ Lower confidence scores in mappings
│   │   └─→ Improve data quality
│   │
│   ├─→ Too few matches?
│   │   ├─→ Check data quality
│   │   ├─→ Raise confidence scores
│   │   └─→ Add more matching attributes
│   │
│   └─→ Missing information?
│       └─→ Check query flags
│           └─→ Use get_sdk_reference(topic="flags")
│
├─→ Performance slow?
│   ├─→ Add database indexes
│   ├─→ Use appropriate query method
│   └─→ Check search_docs(category="performance")
│
└─→ No results found?
    ├─→ Verify data was loaded
    │   └─→ Check loading statistics
    ├─→ Verify DATA_SOURCE name matches
    └─→ Check query parameters
```

## Section E: Performance Issues

```text
System too slow?
│
├─→ Transformation slow?
│   ├─→ Process in batches
│   ├─→ Use multiprocessing for large files
│   └─→ Check data source performance
│       └─→ Database query slow?
│       └─→ API rate limited?
│
├─→ Loading slow?
│   ├─→ Check database type
│   │   └─→ SQLite: Max ~50 records/sec
│   │   └─→ PostgreSQL: 100-500 records/sec
│   ├─→ Optimize batch size
│   │   └─→ Try 100, 500, 1000 records/batch
│   ├─→ Check system resources
│   │   └─→ CPU, memory, disk I/O
│   └─→ Use search_docs(category="performance")
│
├─→ Query slow?
│   ├─→ Add database indexes
│   ├─→ Use specific queries (not export all)
│   └─→ Check search_docs(category="database")
│
└─→ System resources maxed?
    ├─→ Check monitoring dashboard
    ├─→ Increase memory allocation
    ├─→ Use more powerful hardware
    └─→ Consider distributed processing
```

## Section F: Data Quality Issues

```text
Poor matching results?
│
├─→ Review data quality from Module 5
│   └─→ Run analyze_record on transformed data
│       └─→ Quality score < 70%?
│           └─→ Go back to Module 5
│               └─→ Improve mappings
│
├─→ Missing critical attributes?
│   ├─→ Check attribute coverage
│   ├─→ Add more field mappings
│   └─→ Consider additional data sources
│
├─→ Inconsistent data formats?
│   ├─→ Add data cleansing to transformation
│   │   • Normalize phone numbers
│   │   • Standardize addresses
│   │   • Clean name formats
│   └─→ Use confidence scores appropriately
│
└─→ Source data quality poor?
    ├─→ Document issues
    ├─→ Work with data owners to improve
    ├─→ Use anonymized test data
    └─→ Set realistic expectations
```

## Quick Diagnostic Commands

Use MCP tools for diagnosis:

- **Senzing error code**: `explain_error_code(error_code="SENZXXXX", version="current")`
- **Installation issues**: `search_docs(query="installation troubleshooting", category="troubleshooting", version="current")`
- **Performance issues**: `search_docs(query="performance", category="anti_patterns", version="current")`
- **Database issues**: `search_docs(query="database troubleshooting", category="troubleshooting", version="current")`
- **Mapping issues**: `analyze_record(file_paths=["data/transformed/output.jsonl"])` to validate output
- **SDK method questions**: `get_sdk_reference(topic="functions", filter="<method_name>", version="current")`

System-level checks (cross-platform):

```python
import os, shutil
# Check database connection (SQLite)
db = os.path.join("database", "G2C.db")
print(f"SQLite DB exists: {os.path.isfile(db)}")
if os.path.isfile(db):
    print(f"  Size: {os.path.getsize(db) / 1024:.0f} KB")

# Check disk space
usage = shutil.disk_usage(os.getcwd())
print(f"Disk free: {usage.free / (1024**3):.1f} GB")
```

For PostgreSQL:

```console
psql -h localhost -U senzing -d senzing -c "SELECT 1"
```

## When All Else Fails

1. **Read the error message carefully**
   - Error messages usually explain the problem

2. **Use explain_error_code**
   - For any SENZ error codes

3. **Search documentation**
   - Use search_docs with relevant query

4. **Check anti-patterns**
   - Use `search_docs(category="anti_patterns")` with a query describing your situation

5. **Start fresh**
   - Restore from backup
   - Go back to last working state
   - Proceed more carefully

6. **Ask for help**
   - Senzing support: <support@senzing.com>
   - Documentation: docs.senzing.com

## Related Resources

For detailed pitfall descriptions and prevention strategies by module, load `steering/common-pitfalls.md`. This decision tree provides the diagnostic flow; common-pitfalls provides the detailed context and solutions for each module.

## Prevention is Better Than Cure

✅ Test with small samples first
✅ Validate at each step
✅ Backup before major operations
✅ Use MCP tools (don't guess)
✅ Read error messages
✅ Document as you go
✅ Commit to git frequently

## When to Load This Guide

Load this steering file when:

- User says "it's not working"
- User encounters any error
- User is stuck or frustrated
- Need systematic troubleshooting approach
- Multiple issues occurring
