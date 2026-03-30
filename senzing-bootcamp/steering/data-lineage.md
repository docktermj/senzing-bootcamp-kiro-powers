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
    transformation_script: src/transform/transform_customers_crm.py
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
    loading_script: src/load/load_customers_crm.py
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
    query_script: src/query/customer_360.py
    data_sources_used: [CUSTOMERS_CRM, CUSTOMERS_ECOMMERCE]
    query_type: searchByAttributes
    average_response_time: 45  # ms
    queries_per_day: 10000

  fraud_detection:
    query_script: src/query/fraud_detection.py
    data_sources_used: [CUSTOMERS_CRM, TRANSACTIONS]
    query_type: getEntityByRecordID
    average_response_time: 25  # ms
    queries_per_day: 50000
```

## Lineage Tracking Implementation

### Automatic Lineage Capture

```python
#!/usr/bin/env python3
"""
Data Lineage Tracker
Automatically captures lineage metadata
"""

import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

class LineageTracker:
    def __init__(self, lineage_file='docs/data_lineage.yaml'):
        self.lineage_file = lineage_file
        self.lineage = self.load_lineage()

    def load_lineage(self) -> Dict:
        """Load existing lineage or create new"""
        if Path(self.lineage_file).exists():
            with open(self.lineage_file) as f:
                return yaml.safe_load(f) or {}
        return {'sources': {}, 'transformations': {}, 'loading': {}, 'usage': {}}

    def save_lineage(self):
        """Save lineage to file"""
        with open(self.lineage_file, 'w') as f:
            yaml.dump(self.lineage, f, default_flow_style=False, sort_keys=False)

    def track_source(self, source_name: str, metadata: Dict):
        """Track data source"""
        if 'sources' not in self.lineage:
            self.lineage['sources'] = {}

        self.lineage['sources'][source_name] = {
            **metadata,
            'tracked_date': datetime.now().isoformat()
        }
        self.save_lineage()
        print(f"✅ Tracked source: {source_name}")

    def track_transformation(self, source_name: str, metadata: Dict):
        """Track transformation"""
        if 'transformations' not in self.lineage:
            self.lineage['transformations'] = {}

        self.lineage['transformations'][source_name] = {
            **metadata,
            'transformation_date': datetime.now().isoformat()
        }
        self.save_lineage()
        print(f"✅ Tracked transformation: {source_name}")

    def track_loading(self, source_name: str, metadata: Dict):
        """Track loading"""
        if 'loading' not in self.lineage:
            self.lineage['loading'] = {}

        self.lineage['loading'][source_name] = {
            **metadata,
            'loading_date': datetime.now().isoformat()
        }
        self.save_lineage()
        print(f"✅ Tracked loading: {source_name}")

    def track_usage(self, query_name: str, metadata: Dict):
        """Track data usage"""
        if 'usage' not in self.lineage:
            self.lineage['usage'] = {}

        self.lineage['usage'][query_name] = {
            **metadata,
            'tracked_date': datetime.now().isoformat()
        }
        self.save_lineage()
        print(f"✅ Tracked usage: {query_name}")

    def get_lineage_for_source(self, source_name: str) -> Dict:
        """Get complete lineage for a data source"""
        lineage = {
            'source': self.lineage.get('sources', {}).get(source_name),
            'transformation': self.lineage.get('transformations', {}).get(source_name),
            'loading': self.lineage.get('loading', {}).get(source_name),
            'usage': []
        }

        # Find all queries using this source
        for query_name, query_info in self.lineage.get('usage', {}).items():
            if source_name in query_info.get('data_sources_used', []):
                lineage['usage'].append({
                    'query_name': query_name,
                    **query_info
                })

        return lineage

    def generate_lineage_report(self, output_file='docs/lineage_report.md'):
        """Generate human-readable lineage report"""
        report = []
        report.append("# Data Lineage Report\n")
        report.append(f"Generated: {datetime.now().isoformat()}\n\n")

        # Sources
        report.append("## Data Sources\n\n")
        for source_name, source_info in self.lineage.get('sources', {}).items():
            report.append(f"### {source_name}\n\n")
            report.append(f"- **Type**: {source_info.get('type')}\n")
            report.append(f"- **Location**: {source_info.get('location')}\n")
            report.append(f"- **Extracted**: {source_info.get('extracted_date')}\n")
            report.append(f"- **Records**: {source_info.get('record_count'):,}\n")
            report.append(f"- **File**: `{source_info.get('file_location')}`\n\n")

        # Transformations
        report.append("## Transformations\n\n")
        for source_name, trans_info in self.lineage.get('transformations', {}).items():
            report.append(f"### {source_name}\n\n")
            report.append(f"- **Input**: `{trans_info.get('source_file')}`\n")
            report.append(f"- **Output**: `{trans_info.get('output_file')}`\n")
            report.append(f"- **Script**: `{trans_info.get('transformation_script')}`\n")
            report.append(f"- **Records In**: {trans_info.get('records_in'):,}\n")
            report.append(f"- **Records Out**: {trans_info.get('records_out'):,}\n")
            report.append(f"- **Quality Score**: {trans_info.get('quality_score')}\n\n")

        # Loading
        report.append("## Loading\n\n")
        for source_name, load_info in self.lineage.get('loading', {}).items():
            report.append(f"### {source_name}\n\n")
            report.append(f"- **Data Source**: {load_info.get('data_source')}\n")
            report.append(f"- **Records Loaded**: {load_info.get('records_loaded'):,}\n")
            report.append(f"- **Throughput**: {load_info.get('throughput')} records/sec\n")
            report.append(f"- **Duration**: {load_info.get('loading_duration')} seconds\n\n")

        # Usage
        report.append("## Data Usage\n\n")
        for query_name, usage_info in self.lineage.get('usage', {}).items():
            report.append(f"### {query_name}\n\n")
            report.append(f"- **Sources Used**: {', '.join(usage_info.get('data_sources_used', []))}\n")
            report.append(f"- **Query Type**: {usage_info.get('query_type')}\n")
            report.append(f"- **Queries/Day**: {usage_info.get('queries_per_day'):,}\n\n")

        # Write report
        with open(output_file, 'w') as f:
            f.writelines(report)

        print(f"✅ Lineage report generated: {output_file}")

# Example usage
if __name__ == '__main__':
    tracker = LineageTracker()

    # Track source (Module 3)
    tracker.track_source('customers_crm', {
        'type': 'database',
        'location': 'postgresql://prod-db/crm',
        'table': 'customers',
        'extracted_date': '2026-03-17',
        'extracted_by': 'john.doe@company.com',
        'record_count': 500000,
        'file_location': 'data/raw/customers_crm.csv'
    })

    # Track transformation (Module 5)
    tracker.track_transformation('customers_crm', {
        'source_file': 'data/raw/customers_crm.csv',
        'transformation_script': 'src/transform/transform_customers_crm.py',
        'output_file': 'data/transformed/customers_crm.jsonl',
        'records_in': 500000,
        'records_out': 498500,
        'records_rejected': 1500,
        'quality_score': 87.5
    })

    # Track loading (Module 6)
    tracker.track_loading('customers_crm', {
        'source_file': 'data/transformed/customers_crm.jsonl',
        'loading_script': 'src/load/load_customers_crm.py',
        'data_source': 'CUSTOMERS_CRM',
        'records_loaded': 498450,
        'throughput': 199
    })

    # Generate report
    tracker.generate_lineage_report()
```

## Integration with Transformation Scripts

Add lineage tracking to transformation scripts:

```python
from lineage_tracker import LineageTracker

def transform_customers(input_file, output_file):
    tracker = LineageTracker()

    # Track start
    start_time = time.time()
    records_in = 0
    records_out = 0
    records_rejected = 0

    # Transform data
    for record in read_csv(input_file):
        records_in += 1
        try:
            transformed = transform_record(record)
            write_jsonl(output_file, transformed)
            records_out += 1
        except Exception as e:
            records_rejected += 1

    # Track transformation
    tracker.track_transformation('customers_crm', {
        'source_file': input_file,
        'transformation_script': __file__,
        'output_file': output_file,
        'records_in': records_in,
        'records_out': records_out,
        'records_rejected': records_rejected,
        'duration': time.time() - start_time
    })
```

## Lineage Visualization

Generate visual lineage diagram:

```python
def generate_lineage_diagram(source_name: str):
    """Generate Mermaid diagram for lineage"""
    lineage = tracker.get_lineage_for_source(source_name)

    diagram = ["```mermaid", "graph LR"]

    # Source
    diagram.append(f"    A[Source: {source_name}]")

    # Transformation
    if lineage['transformation']:
        diagram.append(f"    B[Transform]")
        diagram.append(f"    A --> B")

    # Loading
    if lineage['loading']:
        diagram.append(f"    C[Load to Senzing]")
        diagram.append(f"    B --> C")

    # Usage
    for i, usage in enumerate(lineage['usage']):
        diagram.append(f"    D{i}[{usage['query_name']}]")
        diagram.append(f"    C --> D{i}")

    diagram.append("```")

    return "\n".join(diagram)
```

## Compliance Reporting

Generate compliance report showing data lineage:

```python
def generate_compliance_report(record_id: str):
    """Generate compliance report for a specific record"""
    report = {
        'record_id': record_id,
        'data_sources': [],
        'transformations': [],
        'access_log': []
    }

    # Find which sources contributed to this record
    # Track all transformations applied
    # Log all access to this record

    return report
```

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
- `steering/steering.md` - Module workflows
- `steering/security-privacy.md` - Compliance requirements

## Version History

- **v3.0.0** (2026-03-17): Data lineage tracking created for Modules 2 and 4
