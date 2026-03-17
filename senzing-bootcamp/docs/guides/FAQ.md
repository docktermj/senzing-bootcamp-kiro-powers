# Frequently Asked Questions (FAQ)

**Version**: 1.0  
**Last Updated**: 2026-03-17

---

## General Questions

### What is Senzing?

Senzing is an embeddable entity resolution engine that automatically resolves records about people and organizations across data sources. It matches, relates, and deduplicates entities without requiring manual rules or model training.

### What is entity resolution?

Entity resolution (ER) is the process of determining whether different records refer to the same real-world entity. For example, identifying that "John Smith" at "123 Main St" and "J. Smith" at "123 Main Street" are the same person.

### Do I need to be a data scientist to use Senzing?

No. Senzing is designed to be used by developers and data engineers. The boot camp guides you through the entire process step-by-step.

### How long does the boot camp take?

- Quick Demo (Module 0): 10-15 minutes
- Basic Project (Modules 1-6): 2-3 hours
- Complete Project (Modules 1-12): 10-18 hours

### What programming languages are supported?

Senzing SDKs are available for:
- Python (most common)
- Java
- C#
- Rust
- C/C++

The boot camp focuses on Python but concepts apply to all languages.

---

## Installation & Setup

### Which database should I use?

- **SQLite**: Good for evaluation, development, and small datasets (<1M records)
- **PostgreSQL**: Recommended for production and large datasets (>1M records)

### Do I need to install Senzing locally?

Not necessarily. You can use:
- Local installation (Linux, macOS)
- Docker containers
- Cloud deployment

### Can I use Senzing on Windows?

Yes, but Docker is recommended for Windows. Native Windows support is limited.

### How much disk space do I need?

- Senzing installation: ~2 GB
- Database: Varies by data volume
  - SQLite: ~2-3x source data size
  - PostgreSQL: ~3-5x source data size

### How much RAM do I need?

- Minimum: 4 GB
- Recommended: 8 GB
- Production: 16 GB+

---

## Data Mapping

### What is SGES?

SGES (Senzing Generic Entity Specification) is the JSON format that Senzing uses for input data. It defines standard attributes like NAME_FULL, ADDR_FULL, PHONE_NUMBER, etc.

### Do I need to map all my fields?

No. Map only the fields that are useful for entity resolution:
- Names
- Addresses
- Phone numbers
- Email addresses
- Identifiers (SSN, passport, etc.)
- Dates of birth

### What if my data doesn't have names?

Senzing can resolve entities using any combination of features. For example, devices can be resolved using IP addresses, MAC addresses, and device IDs.

### How do I handle multiple addresses per person?

Use arrays in your JSON:
```json
{
  "DATA_SOURCE": "CUSTOMERS",
  "RECORD_ID": "1001",
  "NAME_FULL": "John Smith",
  "ADDRESS_LIST": [
    {"ADDR_FULL": "123 Main St, Boston, MA"},
    {"ADDR_FULL": "456 Oak Ave, Cambridge, MA"}
  ]
}
```

### Can I use my own attribute names?

No. You must use Senzing's standard attribute names. Use the `mapping_workflow` tool to ensure correct names.

---

## Loading Data

### How fast can Senzing load data?

Typical speeds:
- SQLite: 100-500 records/second
- PostgreSQL: 500-2,000 records/second
- Optimized systems: 2,000-10,000+ records/second

### Can I load data incrementally?

Yes. Senzing supports:
- Initial bulk load
- Incremental updates
- Real-time streaming
- Change data capture (CDC)

### What happens if loading fails?

- Individual record errors don't stop the load
- Failed records are logged
- You can retry failed records
- Always backup before loading

### Can I delete records?

Yes, use `deleteRecord()` method. However, this doesn't "undo" entity resolution. Better to backup and restore if you need to rollback.

### How do I update existing records?

Just load the record again with the same DATA_SOURCE and RECORD_ID. Senzing will update it and re-resolve entities.

---

## Querying & Results

### How do I find duplicates?

Use `getEntityByRecordID()` to see which records resolved to the same entity:
```python
response = bytearray()
g2_engine.getEntityByRecordID("CUSTOMERS", "1001", response)
entity = json.loads(response.decode())
records = entity['RESOLVED_ENTITY']['RECORDS']
# If len(records) > 1, there are duplicates
```

### What's the difference between "resolved" and "related"?

- **Resolved**: Records that Senzing determined are the same entity (high confidence)
- **Related**: Entities that share some features but aren't the same (lower confidence)

### How do I search for a person?

Use `searchByAttributes()`:
```python
search_json = json.dumps({
    "NAME_FULL": "John Smith",
    "DATE_OF_BIRTH": "1980-01-15"
})
response = bytearray()
g2_engine.searchByAttributes(search_json, response)
```

### Can I export all resolved entities?

Yes, use `exportJSONEntityReport()`:
```python
export_handle = g2_engine.exportJSONEntityReport(flags)
while True:
    response = bytearray()
    g2_engine.fetchNext(export_handle, response)
    if not response:
        break
    entity = json.loads(response.decode())
    # Process entity
```

### How do I see why records matched?

Use `whyEntityByRecordID()`:
```python
response = bytearray()
g2_engine.whyEntityByRecordID("CUSTOMERS", "1001", response)
why_result = json.loads(response.decode())
# Shows matching features and scores
```

---

## Performance

### My loading is slow. How can I speed it up?

1. Increase batch size
2. Use PostgreSQL instead of SQLite
3. Enable parallel loading
4. Optimize database configuration
5. Use SSD storage
6. See `docs/guides/PERFORMANCE_TUNING.md`

### My queries are slow. What can I do?

1. Use specific query flags (don't request unnecessary data)
2. Limit result set size
3. Add database indexes
4. Cache frequently accessed entities
5. Optimize search criteria

### How much data can Senzing handle?

Senzing scales to billions of records. Practical limits depend on:
- Hardware resources
- Database configuration
- Data complexity
- Performance requirements

---

## Errors & Troubleshooting

### I'm getting "SENZ0001" error. What does it mean?

SENZ0001 is a generic initialization error. Common causes:
- Invalid configuration JSON
- Database connection failed
- Missing Senzing installation
- Incorrect file paths

Use `explain_error_code` tool for specific guidance.

### My schema validation failed. What's wrong?

Common schema issues:
- Wrong column names (sys_create_dt vs sys_create_date)
- Missing code_id column in sys_codes_used
- Incorrect sys_vars entries
- Wrong version numbers

Run `templates/validate_schema.py` for detailed diagnosis.

### Records aren't matching. Why?

Possible reasons:
1. Data quality issues (missing/incorrect data)
2. Incorrect attribute mapping
3. Data format inconsistencies
4. Insufficient matching features
5. Configuration issues

Use `analyze_record` tool to check data quality.

### How do I debug entity resolution?

1. Use `whyEntityByRecordID()` to see matching logic
2. Use `howEntityByEntityID()` to see resolution steps
3. Check data quality with `analyze_record`
4. Review matching features
5. Check configuration

---

## Best Practices

### Should I clean my data before loading?

Yes, basic cleaning helps:
- Trim whitespace
- Standardize formats (dates, phones)
- Remove duplicates within source
- Fix obvious errors

But don't over-clean - Senzing handles variations.

### How often should I backup?

- Before initial load
- Before major changes
- Daily in production
- Before version upgrades

### Should I use one DATA_SOURCE or multiple?

Use multiple DATA_SOURCE values when:
- Data comes from different systems
- You need to track data lineage
- Different sources have different quality levels
- You want source-specific reporting

### How do I handle PII?

1. Encrypt data at rest and in transit
2. Use secure credential management
3. Implement access controls
4. Anonymize/pseudonymize when possible
5. Follow regulatory requirements (GDPR, CCPA)
6. See `docs/modules/MODULE_10_SECURITY_HARDENING.md`

### Should I use Docker or native installation?

**Docker**:
- Pros: Easy setup, consistent environment, portable
- Cons: Slight performance overhead, complexity for production

**Native**:
- Pros: Better performance, simpler production deployment
- Cons: Platform-specific installation, more setup

---

## Licensing & Deployment

### Is Senzing free?

Senzing offers:
- Free evaluation license
- Development licenses
- Production licenses (contact Senzing)

### What's a DSR?

DSR (Data Source Record) is Senzing's licensing unit. One DSR = one input record from one data source.

### How do I estimate costs?

Use the cost calculator:
```bash
python templates/cost_calculator.py --interactive
```

### Can I use Senzing in the cloud?

Yes, Senzing works on:
- AWS
- Azure
- Google Cloud
- Private cloud
- On-premises

---

## Advanced Topics

### Can I customize matching rules?

Senzing uses machine learning, not rules. However, you can:
- Adjust configuration
- Set feature confidence scores
- Define custom features
- Tune thresholds

### How does Senzing handle relationships?

Senzing automatically discovers relationships through:
- Disclosed relationships (in data)
- Possible relationships (shared features)
- Relationship networks

### Can I integrate Senzing with my application?

Yes, Senzing provides:
- REST API
- Native SDKs (Python, Java, C#, etc.)
- Batch processing
- Streaming integration

### Does Senzing support real-time processing?

Yes, Senzing can:
- Process records in real-time
- Return resolution results immediately
- Handle streaming data
- Support event-driven architectures

---

## Getting Help

### Where can I find more documentation?

- Boot camp docs: `docs/` directory
- Senzing docs: https://senzing.com/docs
- API reference: Use `get_sdk_reference` tool
- Examples: `examples/` directory

### How do I report a bug?

1. Check `docs/guides/TROUBLESHOOTING_INDEX.md`
2. Use `templates/troubleshoot.py` for diagnosis
3. Contact Senzing support: support@senzing.com
4. Include: error message, steps to reproduce, environment details

### Can I get training?

Yes, Senzing offers:
- This boot camp (self-paced)
- Instructor-led training
- Custom workshops
- Consulting services

Contact Senzing for details.

### Where can I find code examples?

- Boot camp templates: `templates/` directory
- Example projects: `examples/` directory
- Senzing GitHub: Use `find_examples` tool
- Community examples: Senzing community forums

---

## Common "How Do I..." Questions

### How do I...

**...load data from a CSV file?**
```bash
python templates/collect_from_csv.py --input data.csv --output sample.csv
python templates/transform_csv_template.py
python templates/batch_loader_template.py
```

**...search for a person by name?**
```python
search_json = json.dumps({"NAME_FULL": "John Smith"})
response = bytearray()
g2_engine.searchByAttributes(search_json, response)
results = json.loads(response.decode())
```

**...find all duplicates?**
```python
# Export all entities with multiple records
export_handle = g2_engine.exportJSONEntityReport(flags)
while True:
    response = bytearray()
    g2_engine.fetchNext(export_handle, response)
    if not response:
        break
    entity = json.loads(response.decode())
    if len(entity['RESOLVED_ENTITY']['RECORDS']) > 1:
        # This is a duplicate
        print(entity)
```

**...backup my database?**
```bash
python templates/backup_database.py --db-type sqlite \
  --database database/G2C.db --auto-name
```

**...check my schema?**
```bash
python templates/validate_schema.py --database sqlite \
  --connection database/G2C.db
```

**...estimate project costs?**
```bash
python templates/cost_calculator.py --interactive
```

**...test performance?**
```bash
python templates/performance_baseline.py \
  --config-json '{"SQL":{"CONNECTION":"sqlite3://na:na@database/G2C.db"}}'
```

---

## Still Have Questions?

- Ask the agent: "How do I [your question]?"
- Check troubleshooting guide: `docs/guides/TROUBLESHOOTING_INDEX.md`
- Search documentation: Use `search_docs` tool
- Contact support: support@senzing.com

---

**Document Owner**: Boot Camp Team  
**Last Updated**: 2026-03-17  
**Contributions Welcome**: Submit questions to improve this FAQ
