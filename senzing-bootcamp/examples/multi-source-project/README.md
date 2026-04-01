# Multi-Source Project Example: Customer 360

> **Blueprint Project:** This directory contains a detailed README describing the project architecture, code patterns, and expected results. The actual source code files referenced below are generated during the boot camp using MCP tools (`generate_scaffold`, `mapping_workflow`). Use this README as an architectural reference when building your own project.

## Overview

This example demonstrates a complete Customer 360 implementation using three data sources:

- CRM system (customers)
- E-commerce platform (orders/accounts)
- Support ticketing system (support contacts)

**Time to Complete:** 6-8 hours
**Difficulty:** Intermediate
**Modules Covered:** 2-8

## Business Problem

**Scenario:** A retail company has customer data scattered across three systems. They need a unified view to:

- Identify duplicate customers across systems
- Link customer interactions (purchases, support tickets)
- Enable personalized marketing
- Improve customer service

**Expected Outcomes:**

- Reduce duplicate customer records by 80%
- Link 95%+ of customer interactions to correct entities
- Enable single customer view for service reps

## Project Structure

```text
multi-source-customer360/
├── data/
│   ├── raw/
│   │   ├── crm_customers.csv           # 50,000 records
│   │   ├── ecommerce_accounts.csv      # 35,000 records
│   │   └── support_contacts.csv        # 20,000 records
│   ├── transformed/
│   │   ├── crm_customers.jsonl
│   │   ├── ecommerce_accounts.jsonl
│   │   └── support_contacts.jsonl
│   └── samples/
│       ├── crm_sample.csv              # 100 records for testing
│       ├── ecommerce_sample.csv
│       └── support_sample.csv
├── database/
│   └── G2C.db                          # SQLite database
├── src/
│   ├── transform/
│   │   ├── transform_crm.py
│   │   ├── transform_ecommerce.py
│   │   └── transform_support.py
│   ├── load/
│   │   ├── load_crm.py
│   │   ├── load_ecommerce.py
│   │   ├── load_support.py
│   │   └── orchestrator.py             # Multi-source orchestration
│   ├── query/
│   │   ├── find_duplicates.py
│   │   ├── customer_360_view.py
│   │   └── data_quality_report.py
│   └── utils/
│       ├── data_quality.py
│       └── senzing_config.py
├── docs/
│   ├── business_problem.md
│   ├── data_source_evaluation.md
│   ├── mapping_specifications.md
│   ├── loading_strategy.md
│   └── results_validation.md
├── config/
│   └── senzing_config.json
├── tests/
│   ├── test_transformations.py
│   └── test_queries.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md                           # This file
```

## Sample Data

### CRM Customers (crm_customers.csv)

```csv
customer_id,first_name,last_name,email,phone,address,city,state,zip,created_date
CRM-001,John,Smith,john.smith@email.com,555-0101,123 Main St,Boston,MA,02101,2023-01-15
CRM-002,Jane,Doe,jane.doe@email.com,555-0102,456 Oak Ave,Boston,MA,02102,2023-02-20
CRM-003,Bob,Johnson,bob.j@email.com,555-0103,789 Pine Rd,Cambridge,MA,02138,2023-03-10
```

### E-commerce Accounts (ecommerce_accounts.csv)

```csv
account_id,name,email,phone,shipping_address,city,state,postal_code,registration_date
EC-1001,John Smith,jsmith@email.com,5550101,123 Main Street,Boston,MA,02101,2023-01-20
EC-1002,Jane M Doe,jane.doe@email.com,555-0102,456 Oak Avenue,Boston,MA,02102,2023-02-25
EC-1003,Robert Johnson,robert.johnson@email.com,555-0199,321 Elm St,Somerville,MA,02144,2023-04-05
```

### Support Contacts (support_contacts.csv)

```csv
contact_id,full_name,email,phone,company,issue_date
SUP-5001,John Smith,john.smith@email.com,555-0101,Acme Corp,2023-06-15
SUP-5002,Jane Doe,j.doe@email.com,555-0102,Beta Inc,2023-07-20
SUP-5003,Bob Johnson,bob.j@email.com,555-0103,Gamma LLC,2023-08-10
```

## Step-by-Step Walkthrough

### Module 2: Define Business Problem

Create `docs/business_problem.md`:

```markdown
# Business Problem: Customer 360 View

## Problem Statement
We have customer data in three disconnected systems (CRM, E-commerce, Support).
This causes:
- Duplicate customer records
- Incomplete customer history
- Poor customer service experience
- Ineffective marketing campaigns

## Goals
1. Create unified customer view across all systems
2. Identify and merge duplicate customers
3. Link all customer interactions to correct entity
4. Enable 360-degree customer insights

## Data Sources
1. CRM System (50K customers)
2. E-commerce Platform (35K accounts)
3. Support System (20K contacts)

## Success Criteria
- 80%+ reduction in duplicates
- 95%+ interaction linkage accuracy
- Single customer view available in < 1 second
```

### Module 3: Collect Data Sources

Download sample data:

```bash
# Create directories
mkdir -p data/raw data/samples

# In real scenario, export from systems
# For this example, use provided sample files
```

### Module 4: Evaluate Data Quality

Run quality assessment:

```python
# src/utils/data_quality.py
import pandas as pd

def assess_quality(file_path, source_name):
    df = pd.read_csv(file_path)

    report = {
        'source': source_name,
        'total_records': len(df),
        'completeness': {},
        'duplicates': {}
    }

    # Check completeness
    for col in df.columns:
        non_null = df[col].notna().sum()
        report['completeness'][col] = (non_null / len(df)) * 100

    # Check for duplicates
    if 'email' in df.columns:
        dup_emails = df['email'].duplicated().sum()
        report['duplicates']['email'] = dup_emails

    return report

# Run for each source
crm_quality = assess_quality('data/raw/crm_customers.csv', 'CRM')
print(f"CRM Quality Score: {sum(crm_quality['completeness'].values()) / len(crm_quality['completeness']):.1f}%")
```

### Module 5: Map Data to Senzing Format

Create transformation programs for each source using `mapping_workflow`:

> **Note:** The transformation code below is illustrative. During the boot camp, the agent
> uses the `mapping_workflow` MCP tool to generate correct attribute names for your data.
> Do not copy these attribute names directly — they may not match the current Senzing
> Entity Specification. Always use `mapping_workflow` for your actual mappings.

**src/transform/transform_crm.py**:

```python
#!/usr/bin/env python3
"""Transform CRM customers to Senzing format"""

import json
import csv

def transform_crm_record(row):
    """Transform single CRM record.
    NOTE: Attribute names are generated by mapping_workflow.
    Use mapping_workflow MCP tool for your actual mappings.
    """
    return {
        "DATA_SOURCE": "CRM",
        "RECORD_ID": row['customer_id'],
        "RECORD_TYPE": "PERSON",
        "NAME_LAST": row['last_name'],
        "NAME_FIRST": row['first_name'],
        "EMAIL_ADDRESS": row['email'],
        "PHONE_NUMBER": row['phone'],
        "ADDR_FULL": row['address'],
        "ADDR_CITY": row['city'],
        "ADDR_STATE": row['state'],
        "ADDR_POSTAL_CODE": row['zip'],
    }

def transform_file(input_file, output_file):
    """Transform entire file"""
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        reader = csv.DictReader(infile)
        for row in reader:
            senzing_record = transform_crm_record(row)
            outfile.write(json.dumps(senzing_record) + '\n')

    print(f"✅ Transformed {input_file} -> {output_file}")

if __name__ == '__main__':
    transform_file('data/raw/crm_customers.csv', 'data/transformed/crm_customers.jsonl')
```

**src/transform/transform_ecommerce.py**:

```python
#!/usr/bin/env python3
"""Transform E-commerce accounts to Senzing format"""

import json
import csv

def transform_ecommerce_record(row):
    """Transform single e-commerce record.
    NOTE: Attribute names are generated by mapping_workflow.
    """
    name_parts = row['name'].split()

    return {
        "DATA_SOURCE": "ECOMMERCE",
        "RECORD_ID": row['account_id'],
        "RECORD_TYPE": "PERSON",
        "NAME_FULL": row['name'],
        "EMAIL_ADDRESS": row['email'],
        "PHONE_NUMBER": row['phone'],
        "ADDR_FULL": row['shipping_address'],
        "ADDR_CITY": row['city'],
        "ADDR_STATE": row['state'],
        "ADDR_POSTAL_CODE": row['postal_code'],
    }

def transform_file(input_file, output_file):
    """Transform entire file"""
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        reader = csv.DictReader(infile)
        for row in reader:
            senzing_record = transform_ecommerce_record(row)
            outfile.write(json.dumps(senzing_record) + '\n')

    print(f"✅ Transformed {input_file} -> {output_file}")

if __name__ == '__main__':
    transform_file('data/raw/ecommerce_accounts.csv', 'data/transformed/ecommerce_accounts.jsonl')
```

**src/transform/transform_support.py**:

```python
#!/usr/bin/env python3
"""Transform Support contacts to Senzing format"""

import json
import csv

def transform_support_record(row):
    """Transform single support record.
    NOTE: Attribute names are generated by mapping_workflow.
    """
    return {
        "DATA_SOURCE": "SUPPORT",
        "RECORD_ID": row['contact_id'],
        "RECORD_TYPE": "PERSON",
        "NAME_FULL": row['full_name'],
        "EMAIL_ADDRESS": row['email'],
        "PHONE_NUMBER": row['phone'],
        "NAME_ORG": row.get('company', ''),
    }

def transform_file(input_file, output_file):
    """Transform entire file"""
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        reader = csv.DictReader(infile)
        for row in reader:
            senzing_record = transform_support_record(row)
            outfile.write(json.dumps(senzing_record) + '\n')

    print(f"✅ Transformed {input_file} -> {output_file}")

if __name__ == '__main__':
    transform_file('data/raw/support_contacts.csv', 'data/transformed/support_contacts.jsonl')
```

### Module 0: Set Up SDK

```bash
# Install Senzing (if not already installed)
pip install senzing

# Create database directory
mkdir -p database

# Configure engine
cat > config/senzing_config.json << EOF
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/er/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "sqlite3://na:na@database/G2C.db"
  }
}
EOF
```

### Module 6-7: Load Data Sources with Orchestration

**src/load/orchestrator.py**:

```python
#!/usr/bin/env python3
"""Multi-source loading orchestrator"""

import json
import time
from senzing_core import SzAbstractFactoryCore

class LoadOrchestrator:
    def __init__(self, config_file='config/senzing_config.json'):
        with open(config_file) as f:
            self.config = json.dumps(json.load(f))

        self.sz_factory = SzAbstractFactoryCore(
            "Orchestrator", self.config
        )
        self.engine = self.sz_factory.create_engine()

    def load_source(self, data_source, input_file):
        """Load a single data source"""
        print(f"\n{'='*60}")
        print(f"Loading {data_source} from {input_file}")
        print(f"{'='*60}")

        start_time = time.time()
        success_count = 0
        error_count = 0

        with open(input_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line)
                    self.engine.addRecord(
                        data_source,
                        record['RECORD_ID'],
                        json.dumps(record)
                    )
                    success_count += 1

                    if line_num % 1000 == 0:
                        print(f"  Loaded {line_num:,} records...")

                except Exception as e:
                    error_count += 1
                    print(f"  Error on line {line_num}: {e}")

        duration = time.time() - start_time

        print(f"\n✅ {data_source} Loading Complete:")
        print(f"   Success: {success_count:,} records")
        print(f"   Errors: {error_count:,} records")
        print(f"   Duration: {duration:.1f} seconds")
        print(f"   Rate: {success_count/duration:.1f} records/sec")

        return {
            'data_source': data_source,
            'success': success_count,
            'errors': error_count,
            'duration': duration
        }

    def load_all(self):
        """Load all data sources in optimal order"""
        sources = [
            ('CRM', 'data/transformed/crm_customers.jsonl'),
            ('ECOMMERCE', 'data/transformed/ecommerce_accounts.jsonl'),
            ('SUPPORT', 'data/transformed/support_contacts.jsonl')
        ]

        results = []
        for data_source, input_file in sources:
            result = self.load_source(data_source, input_file)
            results.append(result)

        # Print summary
        print(f"\n{'='*60}")
        print("LOADING SUMMARY")
        print(f"{'='*60}")
        total_records = sum(r['success'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        total_duration = sum(r['duration'] for r in results)

        print(f"Total Records Loaded: {total_records:,}")
        print(f"Total Errors: {total_errors:,}")
        print(f"Total Duration: {total_duration:.1f} seconds")
        print(f"Overall Rate: {total_records/total_duration:.1f} records/sec")

        return results

    def cleanup(self):
        """Clean up resources"""
        self.sz_factory.destroy()

if __name__ == '__main__':
    orchestrator = LoadOrchestrator()
    try:
        orchestrator.load_all()
    finally:
        orchestrator.cleanup()
```

Run the orchestrator:

```bash
python src/load/orchestrator.py
```

### Module 8: Query and Validate Results

**src/query/customer_360_view.py**:

```python
#!/usr/bin/env python3
"""Generate Customer 360 view"""

import json
from senzing_core import SzAbstractFactoryCore

def get_customer_360(record_id, data_source):
    """Get complete 360 view of a customer"""

    # Initialize engine
    with open('config/senzing_config.json') as f:
        config = json.dumps(json.load(f))

    sz_factory = SzAbstractFactoryCore("Customer360", config)
    engine = sz_factory.create_engine()

    try:
        # Get entity for this record
        entity_json = engine.getEntityByRecordID(data_source, record_id)
        entity = json.loads(entity_json)

        print(f"\n{'='*60}")
        print(f"CUSTOMER 360 VIEW")
        print(f"{'='*60}")
        print(f"Entity ID: {entity['RESOLVED_ENTITY']['ENTITY_ID']}")
        print(f"\nResolved Identity:")
        print(f"  Name: {entity['RESOLVED_ENTITY']['ENTITY_NAME']}")

        # Show all records that resolved to this entity
        print(f"\nLinked Records ({len(entity['RESOLVED_ENTITY']['RECORDS'])} total):")
        for record in entity['RESOLVED_ENTITY']['RECORDS']:
            print(f"  - {record['DATA_SOURCE']}: {record['RECORD_ID']}")

        # Show contact information
        if 'PHONE' in entity['RESOLVED_ENTITY']:
            print(f"\nPhone Numbers:")
            for phone in entity['RESOLVED_ENTITY']['PHONE']:
                print(f"  - {phone['PHONE_NUMBER']}")

        if 'EMAIL' in entity['RESOLVED_ENTITY']:
            print(f"\nEmail Addresses:")
            for email in entity['RESOLVED_ENTITY']['EMAIL']:
                print(f"  - {email['EMAIL_ADDRESS']}")

        if 'ADDRESS' in entity['RESOLVED_ENTITY']:
            print(f"\nAddresses:")
            for addr in entity['RESOLVED_ENTITY']['ADDRESS']:
                print(f"  - {addr.get('ADDR_FULL', 'N/A')}")

        return entity

    finally:
        sz_factory.destroy()

if __name__ == '__main__':
    # Example: Get 360 view for CRM customer
    get_customer_360('CRM-001', 'CRM')
```

**src/query/find_duplicates.py**:

```python
#!/usr/bin/env python3
"""Find duplicate customers across sources"""

import json
from senzing_core import SzAbstractFactoryCore

def find_cross_source_duplicates():
    """Find entities with records from multiple sources"""

    with open('config/senzing_config.json') as f:
        config = json.dumps(json.load(f))

    sz_factory = SzAbstractFactoryCore("FindDuplicates", config)
    engine = sz_factory.create_engine()

    try:
        # Export all entities
        export_handle = engine.exportJSONEntityReport(0)

        multi_source_entities = []

        while True:
            entity_json = engine.fetchNext(export_handle)
            if not entity_json:
                break

            entity = json.loads(entity_json)
            records = entity['RESOLVED_ENTITY']['RECORDS']

            # Check if entity has records from multiple sources
            sources = set(r['DATA_SOURCE'] for r in records)
            if len(sources) > 1:
                multi_source_entities.append({
                    'entity_id': entity['RESOLVED_ENTITY']['ENTITY_ID'],
                    'name': entity['RESOLVED_ENTITY']['ENTITY_NAME'],
                    'sources': list(sources),
                    'record_count': len(records)
                })

        engine.closeExport(export_handle)

        # Print results
        print(f"\n{'='*60}")
        print(f"CROSS-SOURCE DUPLICATES FOUND")
        print(f"{'='*60}")
        print(f"Total entities with multiple sources: {len(multi_source_entities)}")

        print(f"\nTop 10 Examples:")
        for i, entity in enumerate(multi_source_entities[:10], 1):
            print(f"\n{i}. Entity {entity['entity_id']}: {entity['name']}")
            print(f"   Sources: {', '.join(entity['sources'])}")
            print(f"   Total records: {entity['record_count']}")

        return multi_source_entities

    finally:
        sz_factory.destroy()

if __name__ == '__main__':
    duplicates = find_cross_source_duplicates()
```

## Expected Results

After completing this example, you should see:

1. **Data Loading:**
   - CRM: 50,000 records loaded
   - E-commerce: 35,000 records loaded
   - Support: 20,000 records loaded
   - Total: 105,000 records

2. **Entity Resolution:**
   - Approximately 75,000-80,000 unique entities (25-30% reduction)
   - 15,000-20,000 entities with records from multiple sources
   - High-confidence matches based on name, email, phone, address

3. **Customer 360 Views:**
   - Complete customer history across all touchpoints
   - Linked interactions (purchases, support tickets)
   - Unified contact information

## Key Learnings

1. **Multi-Source Complexity:** Managing dependencies and load order
2. **Data Quality Impact:** Better quality = better matching
3. **Orchestration:** Coordinating multiple data sources
4. **Validation:** Verifying results across sources

## Next Steps

1. Add more data sources (loyalty program, social media)
2. Implement incremental loading for daily updates
3. Create customer 360 API for applications
4. Add monitoring and alerting
5. Deploy to production

## Troubleshooting

### Issue: Low match rates

- Check data quality scores
- Review mapping specifications
- Verify name/address standardization

### Issue: Slow loading

- Use PostgreSQL instead of SQLite
- Increase batch sizes
- Optimize transformation code

### Issue: Unexpected matches

- Review match keys and thresholds
- Check for data quality issues
- Use `explain_error_code` for diagnostics

## Related Documentation

- [POWER.md](../../POWER.md) - Boot camp overview
- [MODULE_7_MULTI_SOURCE_ORCHESTRATION.md](../../docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md)
- [simple-single-source](../simple-single-source/README.md) - Simpler example

## Version History

- **v1.0.0** (2026-03-17): Initial multi-source example created
