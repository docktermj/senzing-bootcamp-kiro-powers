# Senzing Boot Camp - Quick Reference Card

**Version**: 1.0 | **Last Updated**: 2026-03-17

---

## Boot Camp Modules (13 Total)

| Module | Name | Time | Key Output |
|--------|------|------|------------|
| 0 | Quick Demo | 10 min | See ER in action |
| 1 | Business Problem | 30 min | Problem statement |
| 2 | Collect Data | 15 min/source | Data files |
| 3 | Evaluate Quality | 20 min/source | Quality report |
| 4 | Map Data | 1-2 hrs/source | Transform program |
| 5 | SDK Setup | 30-60 min | Senzing installed |
| 6 | Load Data | 30 min/source | Data loaded |
| 7 | Multi-Source | 1-2 hrs | Orchestration |
| 8 | Query & Validate | 1-2 hrs | Query programs |
| 9 | Performance | 1-2 hrs | Benchmarks |
| 10 | Security | 1-2 hrs | Hardened config |
| 11 | Monitoring | 1-2 hrs | Dashboards |
| 12 | Deploy | 2-3 hrs | Production ready |

---

## Essential Commands

### Validation
```bash
# Check schema
python templates/validate_schema.py --database sqlite \
  --connection database/G2C.db

# Check performance
python templates/performance_baseline.py \
  --config-json '{"SQL":{"CONNECTION":"sqlite3://na:na@database/G2C.db"}}'

# Troubleshoot
python templates/troubleshoot.py
```

### Data Collection
```bash
# CSV
python templates/collect_from_csv.py --input data.csv --output sample.csv

# JSON
python templates/collect_from_json.py --input data.json --output sample.json

# API
python templates/collect_from_api.py --url "https://api.example.com/data" \
  --output data.json

# Database
python templates/collect_from_database.py --db-type postgresql \
  --connection "postgresql://user:pass@host:5432/db" \
  --query "SELECT * FROM customers" --output data.csv
```

### Backup & Restore
```bash
# Backup
python templates/backup_database.py --db-type sqlite \
  --database database/G2C.db --auto-name

# Restore
python templates/restore_database.py --db-type sqlite \
  --backup data/backups/G2C_backup_20260317_120000.db \
  --database database/G2C.db
```

### Cost Estimation
```bash
python templates/cost_calculator.py --interactive
```

---

## Common Senzing Attributes

### Names
- `NAME_FULL` - Full name
- `NAME_FIRST` - First name
- `NAME_LAST` - Last name
- `NAME_MIDDLE` - Middle name
- `NAME_PREFIX` - Mr., Mrs., Dr.
- `NAME_SUFFIX` - Jr., Sr., III
- `NAME_ORG` - Organization name

### Addresses
- `ADDR_FULL` - Complete address
- `ADDR_LINE1` - Street address
- `ADDR_CITY` - City
- `ADDR_STATE` - State/Province
- `ADDR_POSTAL_CODE` - ZIP/Postal code
- `ADDR_COUNTRY` - Country

### Contact
- `PHONE_NUMBER` - Phone
- `EMAIL_ADDRESS` - Email
- `WEBSITE_ADDRESS` - Website

### Identifiers
- `SSN_NUMBER` - Social Security Number
- `PASSPORT_NUMBER` - Passport
- `DRIVERS_LICENSE_NUMBER` - Driver's license
- `NATIONAL_ID_NUMBER` - National ID
- `TAX_ID_NUMBER` - Tax ID (EIN, VAT)

### Dates
- `DATE_OF_BIRTH` - Birth date
- `DATE_OF_DEATH` - Death date
- `REGISTRATION_DATE` - Registration

### Required Fields
- `DATA_SOURCE` - Source identifier (required)
- `RECORD_ID` - Record identifier (required)

---

## Python SDK Quick Reference

### Initialize
```python
from senzing import G2Engine
import json

g2_engine = G2Engine()
config_json = json.dumps({
    "SQL": {"CONNECTION": "sqlite3://na:na@database/G2C.db"}
})
g2_engine.init("MyApp", config_json, False)
```

### Load Record
```python
record = {
    "DATA_SOURCE": "CUSTOMERS",
    "RECORD_ID": "1001",
    "NAME_FULL": "John Smith",
    "PHONE_NUMBER": "555-1234"
}
g2_engine.addRecord(
    record['DATA_SOURCE'],
    record['RECORD_ID'],
    json.dumps(record)
)
```

### Get Entity by Record
```python
response = bytearray()
g2_engine.getEntityByRecordID("CUSTOMERS", "1001", response)
entity = json.loads(response.decode())
```

### Search by Attributes
```python
search_json = json.dumps({
    "NAME_FULL": "John Smith",
    "PHONE_NUMBER": "555-1234"
})
response = bytearray()
g2_engine.searchByAttributes(search_json, response)
results = json.loads(response.decode())
```

### Why Records Matched
```python
response = bytearray()
g2_engine.whyEntityByRecordID("CUSTOMERS", "1001", response)
why_result = json.loads(response.decode())
```

### Export All Entities
```python
flags = G2_EXPORT_INCLUDE_ALL_ENTITIES
export_handle = g2_engine.exportJSONEntityReport(flags)

while True:
    response = bytearray()
    g2_engine.fetchNext(export_handle, response)
    if not response:
        break
    entity = json.loads(response.decode())
    # Process entity
```

### Cleanup
```python
g2_engine.destroy()
```

---

## Common Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| SENZ0001 | Init failed | Check config, database connection |
| SENZ0002 | Invalid JSON | Validate JSON syntax |
| SENZ0003 | Database error | Check database status, permissions |
| SENZ0004 | Record not found | Verify DATA_SOURCE and RECORD_ID |
| SENZ0005 | Invalid attribute | Use correct attribute names |
| SENZ1001 | Schema error | Run validate_schema.py |

Use `explain_error_code` tool for detailed help.

---

## Database Connections

### SQLite
```json
{
  "SQL": {
    "CONNECTION": "sqlite3://na:na@database/G2C.db"
  }
}
```

### PostgreSQL
```json
{
  "SQL": {
    "CONNECTION": "postgresql://user:password@host:5432/database"
  }
}
```

---

## Performance Tips

### Loading
- Batch size: 1,000-10,000 records
- Use PostgreSQL for >1M records
- Enable parallel loading
- Disable indexes during bulk load

### Queries
- Use specific flags (don't request unnecessary data)
- Limit result set size
- Cache frequently accessed entities
- Add database indexes

### Memory
- Use generators for large files
- Process in batches
- Clear objects explicitly
- Monitor memory usage

---

## File Organization

```
my-project/
├── data/
│   ├── raw/          # Original data
│   ├── transformed/  # Senzing JSON
│   ├── samples/      # Test samples
│   └── backups/      # Database backups
├── database/         # SQLite files
├── src/
│   ├── transform/    # Transformation programs
│   ├── load/         # Loading programs
│   └── query/        # Query programs
├── docs/             # Documentation
├── config/           # Configuration
├── docker/           # Docker files
└── scripts/          # Shell scripts
```

---

## Useful Tools

### MCP Tools (via agent)
- `get_capabilities` - List all tools
- `mapping_workflow` - Interactive mapping
- `generate_scaffold` - Generate code
- `search_docs` - Search documentation
- `explain_error_code` - Error diagnosis
- `get_sample_data` - Sample datasets

### Templates
- `validate_schema.py` - Schema validation
- `performance_baseline.py` - Performance test
- `troubleshoot.py` - Interactive troubleshooting
- `cost_calculator.py` - Cost estimation
- `collect_from_*.py` - Data collection
- `backup_database.py` - Database backup

---

## Quick Troubleshooting

**Problem**: Loading is slow  
**Solution**: Increase batch size, use PostgreSQL, enable parallel loading

**Problem**: Records not matching  
**Solution**: Check data quality, verify attribute mapping, use analyze_record

**Problem**: Schema validation failed  
**Solution**: Run validate_schema.py, check column names (sys_create_dt)

**Problem**: Out of memory  
**Solution**: Use generators, process in smaller batches, increase RAM

**Problem**: Query timeout  
**Solution**: Add indexes, limit result size, optimize search criteria

---

## Resources

- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory
- **Templates**: `templates/` directory
- **Troubleshooting**: `docs/guides/TROUBLESHOOTING_INDEX.md`
- **FAQ**: `docs/guides/FAQ.md`
- **Performance**: `docs/guides/PERFORMANCE_TUNING.md`

---

## Support

- **Agent**: Ask questions anytime
- **Senzing Support**: support@senzing.com
- **Documentation**: https://senzing.com/docs
- **Community**: Senzing community forums

---

**Print this card for quick reference during the boot camp!**
