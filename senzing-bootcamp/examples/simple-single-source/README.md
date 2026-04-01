# Simple Single Source Example

> **Blueprint Project:** This directory contains a detailed README describing the project architecture, code patterns, and expected results. The actual source code files referenced below are generated during the boot camp using MCP tools (`generate_scaffold`, `mapping_workflow`). Use this README as an architectural reference when building your own project.

A minimal Senzing project demonstrating customer deduplication with a single data source.

## Overview

**Use case:** Deduplicate customer records from a CRM system
**Data source:** Single CSV file with 10,000 customer records
**Database:** SQLite (no setup required)
**Time to complete:** 2-3 hours
**Modules covered:** 2-6, 8

## What You'll Learn

- Basic project structure
- Simple data mapping
- Loading data into Senzing
- Querying for duplicates
- Understanding entity resolution results

## Project Structure

```text
simple-single-source/
├── README.md                          # This file
├── data/
│   ├── raw/
│   │   └── customers.csv              # Source data (10K records)
│   ├── transformed/
│   │   └── customers.jsonl            # Senzing format
│   └── samples/
│       └── customers_sample.csv       # Small sample (100 records)
├── src/
│   ├── transform/
│   │   └── transform_customers.py     # CSV → Senzing JSON
│   ├── load/
│   │   └── load_customers.py          # Load into Senzing
│   ├── query/
│   │   ├── find_duplicates.py         # Find duplicate customers
│   │   └── get_entity.py              # Get entity details
│   └── utils/
│       └── config.py                  # Shared configuration
├── tests/
│   └── test_transform.py              # Unit tests
├── docs/
│   ├── business_problem.md            # Problem statement
│   ├── data_quality_report.md         # Quality analysis
│   ├── mapping_customers.md           # Mapping documentation
│   └── results_analysis.md            # Results and findings
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
└── .gitignore                         # Git ignore rules
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for SQLite)
```

### 3. Transform Data

```bash
python src/transform/transform_customers.py
```

Output: `data/transformed/customers.jsonl`

### 4. Load Data

```bash
python src/load/load_customers.py
```

This loads all 10,000 records into Senzing.

### 5. Find Duplicates

```bash
python src/query/find_duplicates.py
```

This shows entities with multiple records (duplicates).

### 6. Examine Entity

```bash
python src/query/get_entity.py --entity-id 1
```

This shows all records that matched for a specific entity.

## Sample Data

The `customers.csv` file contains realistic customer data:

```csv
customer_id,full_name,address,city,state,zip,phone,email
CUST-00001,John Smith,123 Main St,Springfield,IL,62701,555-123-4567,john.smith@example.com
CUST-00002,J. Smith,123 Main Street,Springfield,IL,62701,5551234567,jsmith@example.com
CUST-00003,John R Smith,123 Main St Apt 1,Springfield,IL,62701,(555) 123-4567,john.smith@example.com
...
```

Notice records 1, 2, and 3 are the same person with variations.

## Expected Results

After loading 10,000 records:

- **Entities created:** ~7,500
- **Match rate:** ~25%
- **Average records per entity:** 1.33
- **Largest entity:** 5-8 records

This means about 2,500 records are duplicates.

## Key Files

### transform_customers.py

Converts CSV to Senzing JSON format:

```python
def transform_record(source_record):
    """Transform CSV record to Senzing format"""
    return {
        "DATA_SOURCE": "CUSTOMERS",
        "RECORD_ID": source_record["customer_id"],
        "NAME_FULL": source_record["full_name"],
        "ADDR_FULL": f"{source_record['address']}, {source_record['city']}, {source_record['state']} {source_record['zip']}",
        "PHONE_NUMBER": source_record["phone"],
        "EMAIL_ADDRESS": source_record["email"]
    }
```

### load_customers.py

Loads records into Senzing:

```python
def load_records(input_file):
    """Load records from JSONL file"""
    sz_factory = SzAbstractFactoryCore("LoadCustomers", get_config())
    engine = sz_factory.create_engine()

    with open(input_file, 'r') as f:
        for line in f:
            record = json.loads(line)
            engine.add_record(
                record["DATA_SOURCE"],
                record["RECORD_ID"],
                line
            )

    sz_factory.destroy()
```

### find_duplicates.py

Finds entities with multiple records:

```python
def find_duplicates():
    """Find entities with multiple records"""
    sz_factory = SzAbstractFactoryCore("FindDuplicates", get_config())
    engine = sz_factory.create_engine()

    # Export all entities
    export_handle = engine.exportJSONEntityReport(0)

    duplicates = []
    while True:
        entity_json = engine.fetchNext(export_handle)
        if not entity_json:
            break

        entity = json.loads(entity_json)
        if len(entity["RESOLVED_ENTITY"]["RECORDS"]) > 1:
            duplicates.append(entity)

    engine.close_export(export_handle)
    sz_factory.destroy()

    return duplicates
```

## Understanding Results

### Entity Structure

```json
{
  "RESOLVED_ENTITY": {
    "ENTITY_ID": 1,
    "RECORDS": [
      {
        "DATA_SOURCE": "CUSTOMERS",
        "RECORD_ID": "CUST-00001",
        "ENTITY_NAME": "John Smith",
        "RECORD_SUMMARY": [...]
      },
      {
        "DATA_SOURCE": "CUSTOMERS",
        "RECORD_ID": "CUST-00002",
        "ENTITY_NAME": "J. Smith",
        "RECORD_SUMMARY": [...]
      }
    ],
    "FEATURES": {
      "NAME": [
        {
          "FEAT_DESC": "John Smith",
          "USAGE_TYPE": "PRIMARY"
        }
      ],
      "ADDRESS": [...],
      "PHONE": [...],
      "EMAIL": [...]
    }
  }
}
```

### Match Reasons

Use `whyEntities` to understand why records matched:

```python
result = engine.whyEntities(
    "CUSTOMERS", "CUST-00001",
    "CUSTOMERS", "CUST-00002"
)
```

Output shows:

- Name similarity: 95%
- Address match: 100%
- Phone match: 100%
- Email match: 100%

## Customization

### Use Your Own Data

1. Replace `data/raw/customers.csv` with your CSV file
2. Update field mappings in `src/transform/transform_customers.py`
3. Adjust `DATA_SOURCE` name if desired
4. Re-run transformation and loading

### Change Database to PostgreSQL

1. Install PostgreSQL
2. Create database: `createdb senzing`
3. Update `.env`:

   ```text
   DATABASE_URL=postgresql://user:pass@localhost:5432/senzing
   ```

4. Re-run loading

### Add More Queries

Create new query programs in `src/query/`:

- Search by name
- Search by phone
- Search by email
- Get entity relationships

## Troubleshooting

### Issue: Import error for senzing

```bash
pip install senzing
```

### Issue: Database file not found

```bash
mkdir -p database
```

### Issue: No duplicates found

- Check that data loaded correctly
- Verify records have matching attributes
- Review data quality

### Issue: Too many/few matches

- This is normal - entity resolution is probabilistic
- Review match reasons with `whyEntities`
- Adjust matching thresholds (advanced)

## Next Steps

After completing this example:

1. **Understand the results:** Review entities and match reasons
2. **Try the multi-source example:** Learn orchestration
3. **Build your own project:** Apply to your data
4. **Explore advanced features:** Performance, security, monitoring

## Related Documentation

- `../../POWER.md` - Boot camp overview
- `../../docs/modules/` - Module documentation
- `../../docs/guides/QUICK_START.md` - Quick start guide

## Support

- Ask the agent for help with any step
- Use `search_docs` for Senzing documentation
- Review `docs/` for detailed explanations

## Version History

- **v3.0.0** (2026-03-17): Simple single source example created
