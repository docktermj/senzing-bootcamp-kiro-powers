# Incremental Loading Strategies

## Overview

Incremental loading loads only new or changed records instead of reloading entire datasets. This is essential for production systems with frequently updated data.

## Why Incremental Loading?

- **Efficiency**: Load only what changed (minutes vs hours)
- **Freshness**: Update data more frequently
- **Resource Savings**: Less CPU, memory, I/O
- **Minimal Downtime**: Faster updates mean less impact

## Loading Strategies

### 1. Full Reload (Baseline)

Load entire dataset every time:

```python
# Simple but inefficient
def full_reload(source_file):
    for record in read_source(source_file):
        engine.addRecord(DATA_SOURCE, record['RECORD_ID'], record)
```

**Pros**: Simple, guaranteed consistency
**Cons**: Slow, resource-intensive, doesn't scale
**Use when**: Small datasets (< 10K records), infrequent updates

### 2. Timestamp-Based Incremental

Load records modified since last load:

```python
def incremental_by_timestamp(source_file, last_load_time):
    """Load only records modified since last load"""
    for record in read_source(source_file):
        if record['modified_date'] > last_load_time:
            engine.addRecord(DATA_SOURCE, record['RECORD_ID'], record)
    
    # Save new timestamp
    save_last_load_time(datetime.now())
```

**Pros**: Efficient, simple to implement
**Cons**: Requires timestamp field, doesn't handle deletes
**Use when**: Source has reliable timestamp field

### 3. Change Data Capture (CDC)

Capture changes from database transaction log:

```python
def load_from_cdc(cdc_stream):
    """Load from CDC stream"""
    for change in cdc_stream:
        if change['operation'] == 'INSERT' or change['operation'] == 'UPDATE':
            engine.addRecord(DATA_SOURCE, change['RECORD_ID'], change['data'])
        elif change['operation'] == 'DELETE':
            engine.deleteRecord(DATA_SOURCE, change['RECORD_ID'])
```

**Pros**: Real-time, handles all operations (insert/update/delete)
**Cons**: Complex setup, requires CDC infrastructure
**Use when**: Real-time updates needed, database supports CDC

**CDC Tools**:
- Debezium (open source)
- AWS DMS
- Oracle GoldenGate
- SQL Server Change Tracking

### 4. Delta Files

Source system provides delta files:

```python
def load_delta_file(delta_file):
    """Load delta file with operation indicators"""
    for record in read_source(delta_file):
        operation = record.get('_operation', 'UPSERT')
        
        if operation in ['INSERT', 'UPDATE', 'UPSERT']:
            engine.addRecord(DATA_SOURCE, record['RECORD_ID'], record)
        elif operation == 'DELETE':
            engine.deleteRecord(DATA_SOURCE, record['RECORD_ID'])
```

**Pros**: Efficient, handles all operations
**Cons**: Requires source system support
**Use when**: Source system can generate delta files

### 5. Checksum/Hash-Based

Compare checksums to detect changes:

```python
import hashlib

def calculate_checksum(record):
    """Calculate record checksum"""
    record_str = json.dumps(record, sort_keys=True)
    return hashlib.md5(record_str.encode()).hexdigest()

def incremental_by_checksum(source_file, checksum_db):
    """Load only records with changed checksums"""
    for record in read_source(source_file):
        record_id = record['RECORD_ID']
        current_checksum = calculate_checksum(record)
        previous_checksum = checksum_db.get(record_id)
        
        if current_checksum != previous_checksum:
            engine.addRecord(DATA_SOURCE, record_id, record)
            checksum_db[record_id] = current_checksum
```

**Pros**: Detects any change, no timestamp needed
**Cons**: Requires storing checksums, more processing
**Use when**: No timestamp field, need to detect any change

### 6. Watermark-Based

Use high-water mark (e.g., max ID):

```python
def incremental_by_watermark(source, last_id):
    """Load records with ID > last_id"""
    query = f"SELECT * FROM {source} WHERE id > {last_id} ORDER BY id"
    
    for record in execute_query(query):
        engine.addRecord(DATA_SOURCE, record['RECORD_ID'], record)
        last_id = record['id']
    
    save_watermark(last_id)
```

**Pros**: Simple, efficient for append-only data
**Cons**: Doesn't handle updates or deletes
**Use when**: Append-only data (logs, transactions)

## Implementation Example

Complete incremental loading script:

```python
#!/usr/bin/env python3
"""
Incremental Loading Script
Supports multiple strategies
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path

class IncrementalLoader:
    def __init__(self, data_source, strategy='timestamp'):
        self.data_source = data_source
        self.strategy = strategy
        self.state_file = f'data/.state/{data_source}_state.json'
        self.state = self.load_state()
    
    def load_state(self):
        """Load previous loading state"""
        if Path(self.state_file).exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {
            'last_load_time': None,
            'last_watermark': 0,
            'checksums': {}
        }
    
    def save_state(self):
        """Save loading state"""
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def should_load_record(self, record):
        """Determine if record should be loaded"""
        if self.strategy == 'timestamp':
            return self._check_timestamp(record)
        elif self.strategy == 'checksum':
            return self._check_checksum(record)
        elif self.strategy == 'watermark':
            return self._check_watermark(record)
        else:
            return True  # Full reload
    
    def _check_timestamp(self, record):
        """Check if record modified since last load"""
        if not self.state['last_load_time']:
            return True
        
        modified_date = record.get('modified_date')
        if not modified_date:
            return True  # Load if no timestamp
        
        return modified_date > self.state['last_load_time']
    
    def _check_checksum(self, record):
        """Check if record checksum changed"""
        record_id = record['RECORD_ID']
        current_checksum = self._calculate_checksum(record)
        previous_checksum = self.state['checksums'].get(record_id)
        
        if current_checksum != previous_checksum:
            self.state['checksums'][record_id] = current_checksum
            return True
        return False
    
    def _check_watermark(self, record):
        """Check if record ID > watermark"""
        record_id = int(record.get('id', 0))
        if record_id > self.state['last_watermark']:
            self.state['last_watermark'] = record_id
            return True
        return False
    
    def _calculate_checksum(self, record):
        """Calculate record checksum"""
        # Remove metadata fields
        data = {k: v for k, v in record.items() if not k.startswith('_')}
        record_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(record_str.encode()).hexdigest()
    
    def load(self, source_file):
        """Load records incrementally"""
        records_loaded = 0
        records_skipped = 0
        
        print(f"Loading {self.data_source} using {self.strategy} strategy...")
        
        for record in self.read_source(source_file):
            if self.should_load_record(record):
                # TODO: Load to Senzing
                # engine.addRecord(self.data_source, record['RECORD_ID'], record)
                records_loaded += 1
            else:
                records_skipped += 1
        
        # Update state
        if self.strategy == 'timestamp':
            self.state['last_load_time'] = datetime.now().isoformat()
        
        self.save_state()
        
        print(f"✅ Loaded: {records_loaded:,} records")
        print(f"⏭️  Skipped: {records_skipped:,} records")
        
        return {
            'loaded': records_loaded,
            'skipped': records_skipped
        }
    
    def read_source(self, source_file):
        """Read source file"""
        # TODO: Implement actual file reading
        # For now, return empty list
        return []

# Example usage
if __name__ == '__main__':
    # Timestamp-based
    loader = IncrementalLoader('CUSTOMERS', strategy='timestamp')
    loader.load('data/raw/customers.csv')
    
    # Checksum-based
    loader = IncrementalLoader('VENDORS', strategy='checksum')
    loader.load('data/raw/vendors.csv')
    
    # Watermark-based
    loader = IncrementalLoader('TRANSACTIONS', strategy='watermark')
    loader.load('data/raw/transactions.csv')
```

## Handling Deletes

### Soft Deletes

Source marks records as deleted:

```python
def handle_soft_deletes(source_file):
    """Handle soft-deleted records"""
    for record in read_source(source_file):
        if record.get('is_deleted'):
            engine.deleteRecord(DATA_SOURCE, record['RECORD_ID'])
        else:
            engine.addRecord(DATA_SOURCE, record['RECORD_ID'], record)
```

### Hard Deletes

Compare current vs previous to find deletes:

```python
def detect_hard_deletes(current_ids, previous_ids):
    """Detect deleted records"""
    deleted_ids = previous_ids - current_ids
    
    for record_id in deleted_ids:
        engine.deleteRecord(DATA_SOURCE, record_id)
```

## Scheduling Incremental Loads

### Cron Job

```bash
# Load every hour
0 * * * * /usr/bin/python3 /app/src/load/incremental_load.py

# Load every 15 minutes
*/15 * * * * /usr/bin/python3 /app/src/load/incremental_load.py

# Load daily at 2 AM
0 2 * * * /usr/bin/python3 /app/src/load/incremental_load.py
```

### Airflow DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 3, 17),
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'senzing_incremental_load',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False
)

def load_customers():
    loader = IncrementalLoader('CUSTOMERS', strategy='timestamp')
    loader.load('data/raw/customers.csv')

load_task = PythonOperator(
    task_id='load_customers',
    python_callable=load_customers,
    dag=dag
)
```

## Best Practices

1. **Always test with full reload first** - Verify logic before incremental
2. **Monitor skipped records** - Sudden changes may indicate issues
3. **Keep state files backed up** - Loss means full reload
4. **Log all operations** - Track what was loaded when
5. **Handle failures gracefully** - Don't update state if load fails
6. **Validate incrementals periodically** - Full reload monthly to verify
7. **Document strategy choice** - Explain why this strategy was chosen

## Agent Behavior

When implementing incremental loading in Module 6:

1. **Assess data source characteristics**:
   - Has timestamp field?
   - Supports CDC?
   - Provides delta files?
   - Append-only or updates?

2. **Recommend strategy** based on assessment

3. **Generate incremental loading script** in `src/load/`

4. **Create state directory** `data/.state/`

5. **Test with small sample** first

6. **Document strategy** in `docs/loading_strategy.md`

7. **Set up scheduling** if automated

## When to Load This Guide

Load this guide when:
- Starting Module 6 (loading)
- User has frequently updated data
- User asks about incremental loading
- Planning production data pipeline

## Related Documentation

- `POWER.md` - Module 6 overview
- `steering/steering.md` - Module 6 workflow
- `MODULE_6_SINGLE_SOURCE_LOADING.md` - Single source loading

## Version History

- **v3.0.0** (2026-03-17): Incremental loading guide created for Module 6
