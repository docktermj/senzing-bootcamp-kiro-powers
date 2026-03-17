# Troubleshooting Decision Tree

Visual flowchart for diagnosing common issues.

## Start Here: What's the Problem?

```
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

```
Installation failing?
│
├─→ Platform mismatch?
│   └─→ Use sdk_guide with correct platform parameter
│       (linux_apt, linux_yum, macos_arm, windows, docker)
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

```
Transformation not working?
│
├─→ Program crashes?
│   ├─→ Check input file exists
│   ├─→ Check file format (CSV, JSON, etc.)
│   ├─→ Test with small sample (10 records)
│   └─→ Check error message in logs/transform.log
│
├─→ Output validation fails?
│   ├─→ Run lint_record on output
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
            └─→ Common mistakes:
                • BUSINESS_NAME_ORG → NAME_ORG
                • PHONE → PHONE_NUMBER
                • EMAIL → EMAIL_ADDRESS
```

## Section C: Loading Issues

```
Loading failing?
│
├─→ Connection errors?
│   └─→ Verify SDK configuration from Module 5
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
│       └─→ ./src/utils/rollback.sh data/backups/G2C_*.db
│
└─→ Partial load failure?
    ├─→ Check which records failed
    ├─→ Fix data quality issues
    ├─→ Restore from backup
    └─→ Reload with fixed data
```

## Section D: Query Issues

```
Queries not working?
│
├─→ Method not found?
│   └─→ NEVER guess method names
│       └─→ Use generate_scaffold or get_sdk_reference
│           └─→ Common mistakes:
│               • close_export → closeExport
│               • whyEntityByEntityID → whyEntities (V4)
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
│   │   • getEntityByEntityID for known IDs
│   │   • searchByAttributes for searches
│   └─→ Check search_docs(category="performance")
│
└─→ No results found?
    ├─→ Verify data was loaded
    │   └─→ Check loading statistics
    ├─→ Verify DATA_SOURCE name matches
    └─→ Check query parameters
```

## Section E: Performance Issues

```
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

```
Poor matching results?
│
├─→ Review data quality from Module 4
│   └─→ Run analyze_record on transformed data
│       └─→ Quality score < 70%?
│           └─→ Go back to Module 4
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

```bash
# Check if Senzing is installed
python -c "import senzing; print(senzing.__version__)"

# Check database connection (SQLite)
ls -lh database/G2C.db

# Check database connection (PostgreSQL)
psql -h localhost -U senzing -d senzing -c "SELECT 1"

# Check transformation output
head -n 5 data/transformed/output.jsonl | python -m json.tool

# Check loading logs
tail -n 50 logs/load.log

# Check system resources
df -h  # Disk space
free -h  # Memory
top  # CPU and processes
```

## When All Else Fails

1. **Read the error message carefully**
   - Error messages usually explain the problem
   
2. **Use explain_error_code**
   - For any SENZ error codes
   
3. **Search documentation**
   - Use search_docs with relevant query
   
4. **Check common pitfalls**
   - Load steering/common-pitfalls.md
   
5. **Start fresh**
   - Restore from backup
   - Go back to last working state
   - Proceed more carefully
   
6. **Ask for help**
   - Senzing support
   - Community forums
   - Documentation

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
