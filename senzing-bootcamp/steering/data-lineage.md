---
inclusion: manual
---

# Data Lineage Tracking

Track data flow from source to destination for compliance, debugging, and governance.

## Lineage File

Maintain `docs/data_lineage.yaml` with four sections updated as the bootcamp progresses:

| Section | When | What to Record |
| ------- | ---- | -------------- |
| `sources` | Module 3 | Type, location, extraction date, record count, file path |
| `transformations` | Module 4 | Input/output files, script path, records in/out/rejected, quality score, field mappings |
| `loading` | Module 5 | Data source name, records loaded/failed, throughput, duration, error codes |
| `usage` | Module 7 | Query script, data sources used, query type, response time |

## Example Entry

```yaml
sources:
  customers_crm:
    type: database
    location: postgresql://prod-db/crm
    extracted_date: 2026-03-17
    record_count: 500000
    file_location: data/raw/customers_crm.csv

transformations:
  customers_crm:
    source_file: data/raw/customers_crm.csv
    transformation_script: src/transform/transform_customers_crm.[ext]
    output_file: data/transformed/customers_crm.jsonl
    records_in: 500000
    records_out: 498500
    records_rejected: 1500
    quality_score: 87.5
```

## Lineage Tracker

Implement a simple utility in the bootcamper's chosen language that reads/writes `docs/data_lineage.yaml`:

- `track_source(name, metadata)` — record a data source
- `track_transformation(name, metadata)` — record a transformation
- `track_loading(name, metadata)` — record a loading operation
- `track_usage(name, metadata)` — record a query pattern
- `get_lineage_for_source(name)` — return full chain: source → transform → load → usage
- `generate_lineage_report(output_file)` — Markdown report of all lineage

No Senzing SDK dependency — just YAML read/write. Save to `src/utils/lineage_tracker.[ext]`.

## Integration

Add tracker calls at the end of transformation scripts (Module 5) and loading scripts (Module 6) to automatically capture lineage metadata.

## Compliance

For GDPR/CCPA: use `get_lineage_for_source` to show the complete data flow for any record — which sources contributed, what transformations were applied, when it was loaded, and who accessed it.

## Agent Behavior

- Create `docs/data_lineage.yaml` during Module 3
- Update it during Modules 5, 6, and 8
- Generate lineage report when user asks about compliance or data provenance
