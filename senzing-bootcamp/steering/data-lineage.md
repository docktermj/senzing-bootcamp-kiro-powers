---
inclusion: manual
---

# Data Lineage Tracking

## Overview

Data lineage tracks the flow of data from source to destination, documenting transformations, quality checks, and usage. This is critical for compliance, debugging, and data governance.

## Why Data Lineage Matters

- **Compliance**: GDPR, CCPA require knowing where data came from
- **Debugging**: Trace issues back to source
- **Impact Analysis**: Understand downstream effects of changes
- **Data Governance**: Document data flows
- **Audit Trail**: Prove data handling compliance

## Lineage Levels

### 1. Source Lineage (Module 3)

Track where data came from:

```yaml
# docs/data_lineage.yaml
sources:
  customers_crm:
    type: database
    location: postgresql://prod-db.company.com/crm
    table: customers
    extracted_date: 2026-03-17
    extracted_by: john.doe@company.com
    record_count: 500000
    file_location: data/raw/customers_crm.csv

  customers_ecommerce:
    type: api
    location: https://api.ecommerce.com/v1/customers
    extracted_date: 2026-03-17
    extracted_by: automated_job
    record_count: 300000
    file_location: data/raw/customers_ecommerce.json
```

### 2. Transformation Lineage (Module 5)

Track how data was transformed:

```yaml
transformations:
  customers_crm:
    source_file: data/raw/customers_crm.csv
    transformation_script: src/transform/transform_customers_crm.[ext]
    transformation_date: 2026-03-17
    transformed_by: jane.smith@company.com
    output_file: data/transformed/customers_crm.jsonl
    records_in: 500000
    records_out: 498500
    records_rejected: 1500
    rejection_reasons:
      missing_required_fields: 1200
      invalid_format: 300
    quality_score: 87.5

    field_mappings:
      - source: customer_id
        target: RECORD_ID
        transformation: direct

      - source: [first_name, last_name]
        target: NAME_FULL
        transformation: concatenate

      - source: email
        target: EMAIL_ADDRESS
        transformation: lowercase + validate

      - source: phone
        target: PHONE_NUMBER
        transformation: normalize_phone
```

### 3. Loading Lineage (Module 6)

Track what was loaded into Senzing:

```yaml
loading:
  customers_crm:
    source_file: data/transformed/customers_crm.jsonl
    loading_script: src/load/load_customers_crm.[ext]
    loading_date: 2026-03-17
    loaded_by: automated_job
    data_source: CUSTOMERS_CRM
    records_attempted: 498500
    records_loaded: 498450
    records_failed: 50
    loading_duration: 2500  # seconds
    throughput: 199  # records/second

    errors:
      - error_code: SENZ0005
        count: 30
        sample_records: [12345, 12346, 12347]

      - error_code: SENZ0042
        count: 20
        sample_records: [23456, 23457]
```

### 4. Usage Lineage (Module 8)

Track how data is used:

```yaml
usage:
  customer_360_query:
    query_script: src/query/customer_360.[ext]
    data_sources_used: [CUSTOMERS_CRM, CUSTOMERS_ECOMMERCE]
    query_type: searchByAttributes
    average_response_time: 45  # ms
    queries_per_day: 10000

  fraud_detection:
    query_script: src/query/fraud_detection.[ext]
    data_sources_used: [CUSTOMERS_CRM, TRANSACTIONS]
    query_type: getEntityByRecordID
    average_response_time: 25  # ms
    queries_per_day: 50000
```

## Lineage Tracking Implementation

### Automatic Lineage Capture

The lineage tracker is a utility that automatically captures and persists metadata about data flow through the pipeline. It should be implemented in the bootcamper's chosen language.

#### Lineage Tracker — Design

The tracker manages a YAML file (`docs/data_lineage.yaml`) with four sections: `sources`, `transformations`, `loading`, and `usage`.

**Operations:**

- `track_source(source_name, metadata)` — Record a data source with its type, location, extraction date, record count, and file location
- `track_transformation(source_name, metadata)` — Record a transformation with input file, output file, script path, records in/out, rejected count, and quality score
- `track_loading(source_name, metadata)` — Record a loading operation with data source name, records loaded, throughput, and duration
- `track_usage(query_name, metadata)` — Record a query/usage pattern with data sources used, query type, and frequency
- `get_lineage_for_source(source_name)` — Return the complete lineage chain for a source (source → transformation → loading → usage)
- `generate_lineage_report(output_file)` — Generate a human-readable Markdown report of all lineage data

Each tracking operation appends a timestamp and persists the updated lineage file.

> **Agent instruction:** Implement the lineage tracker in the bootcamper's chosen language. The tracker is a simple YAML read/write utility — no Senzing SDK dependency required.

#### Example Lineage Data

```yaml
# Track source (Module 3)
customers_crm:
  type: database
  location: postgresql://prod-db/crm
  record_count: 500000
  file_location: data/raw/customers_crm.csv

# Track transformation (Module 5)
customers_crm:
  source_file: data/raw/customers_crm.csv
  transformation_script: src/transform/transform_customers_crm.[ext]
  output_file: data/transformed/customers_crm.jsonl
  records_in: 500000
  records_out: 498500
  quality_score: 87.5

# Track loading (Module 6)
customers_crm:
  loading_script: src/load/load_customers_crm.[ext]
  data_source: CUSTOMERS_CRM
  records_loaded: 498450
  throughput: 199
```

## Integration with Transformation Scripts

Add lineage tracking calls to your transformation scripts. After each transformation completes, call the tracker to record the input file, output file, record counts, and quality score.

## Integration with Loading Scripts

Add lineage tracking calls to your loading scripts. After each load completes, call the tracker to record the data source, records loaded, throughput, and duration.

```text
    tracker = create_lineage_tracker()

    -- Track start
    start_time = current_timestamp()
    records_in = 0
    records_out = 0
    records_rejected = 0

    -- Transform data
    for each record in read_csv(input_file):
        records_in = records_in + 1
        try:
            transformed = transform_record(record)
            write_jsonl(output_file, transformed)
            records_out = records_out + 1
        on error:
            records_rejected = records_rejected + 1

    -- Track transformation
    tracker.track_transformation("customers_crm", {
        source_file: input_file,
        transformation_script: current_script_path,
        output_file: output_file,
        records_in: records_in,
        records_out: records_out,
        records_rejected: records_rejected,
        duration: current_timestamp() - start_time
    })
```

## Lineage Visualization

Generate a visual lineage diagram using Mermaid syntax. The diagram should show the flow from source → transformation → loading → usage queries:

```text
Example Mermaid diagram for a source:

graph LR
    A[Source: customers_crm] --> B[Transform]
    B --> C[Load to Senzing]
    C --> D0[customer_360_query]
    C --> D1[fraud_detection]
```

The lineage tracker should have a function that reads the lineage data for a given source and generates this Mermaid diagram automatically.

## Compliance Reporting

Generate a compliance report showing the complete data lineage for a specific record. The report should include:

- Which data sources contributed to the record
- What transformations were applied
- When the record was loaded
- Who/what has accessed the record

This is useful for GDPR, CCPA, and other regulatory compliance requirements.

## Agent Behavior

### Module 3: Source Lineage

- Create `docs/data_lineage.yaml` if it doesn't exist
- Track each data source as it's collected
- Document source location, type, extraction date
- Save lineage after each source

### Module 5: Transformation Lineage

- Track transformation for each source
- Document field mappings
- Record quality metrics
- Track rejection reasons
- Update lineage file

### Module 6: Loading Lineage

- Track loading for each source
- Document loading statistics
- Record errors and their counts
- Update lineage file

### Module 8: Usage Lineage

- Track query programs
- Document which sources are used
- Record query patterns
- Update lineage file

## When to Load This Guide

Load this guide when:

- Starting Module 3 (data collection)
- Starting Module 5 (transformation)
- User asks about compliance
- User asks about data provenance
- Debugging data issues

## Related Documentation

- `POWER.md` - Modules 2, 4, 6, 8
- per-module steering files (`module-00-sdk-setup.md` through `module-12-deployment.md`)
- `steering/security-privacy.md` - Compliance requirements

## Version History

- **v3.0.0** (2026-03-17): Data lineage tracking created for Modules 2 and 4
