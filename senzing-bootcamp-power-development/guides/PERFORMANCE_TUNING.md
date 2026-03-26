# Performance Tuning Guide

**Version**: 1.0
**Last Updated**: 2026-03-17

Optimize your Senzing deployment for maximum performance.

---

## Table of Contents

1. [Performance Baseline](#performance-baseline)
2. [Database Optimization](#database-optimization)
3. [Loading Performance](#loading-performance)
4. [Query Performance](#query-performance)
5. [Memory Optimization](#memory-optimization)
6. [Parallel Processing](#parallel-processing)
7. [Monitoring and Profiling](#monitoring-and-profiling)
8. [Common Bottlenecks](#common-bottlenecks)

---

## Performance Baseline

### Establish Baseline Metrics

Before tuning, establish baseline performance:

```bash
python templates/performance_baseline.py \
  --config-json '{"SQL":{"CONNECTION":"sqlite3://na:na@database/G2C.db"}}'
```

**Key Metrics to Track**:

- Loading throughput (records/second)
- Query response time (milliseconds)
- Memory usage (MB)
- CPU utilization (%)
- Database size (GB)

### Typical Performance Ranges

| Metric     | SQLite          | PostgreSQL       |
|------------|-----------------|------------------|
| Load Speed | 100-500 rec/sec | 500-2000 rec/sec |
| Query Time | 10-100 ms       | 5-50 ms          |
| Memory     | 500 MB - 2 GB   | 1 GB - 8 GB      |

---

## Database Optimization

### PostgreSQL Tuning

**1. Connection Pool Settings**:

```sql
-- postgresql.conf
max_connections = 100
shared_buffers = 4GB  -- 25% of RAM
effective_cache_size = 12GB  -- 75% of RAM
maintenance_work_mem = 1GB
work_mem = 50MB
```

**2. Write Performance**:

```sql
-- For bulk loading
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
```

**3. Query Performance**:

```sql
-- Enable parallel queries
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

**4. Create Indexes**:

```sql
-- Critical indexes for Senzing
CREATE INDEX IF NOT EXISTS idx_dsrc_record
  ON dsrc_record(dsrc_id, record_id);

CREATE INDEX IF NOT EXISTS idx_obs_ent
  ON obs_ent(ent_id);

CREATE INDEX IF NOT EXISTS idx_res_ent_okey
  ON res_ent_okey(ent_id);
```

### SQLite Tuning

**1. Pragma Settings**:

```python
import sqlite3

conn = sqlite3.connect('database/G2C.db')
conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
conn.execute('PRAGMA cache_size=-64000')  # 64MB cache
conn.execute('PRAGMA temp_store=MEMORY')  # Temp tables in memory
conn.execute('PRAGMA mmap_size=268435456')  # 256MB memory-mapped I/O
```

**2. Batch Transactions**:

```python
# Wrap multiple inserts in transaction
conn.execute('BEGIN TRANSACTION')
for record in records:
    # Insert record
    pass
conn.execute('COMMIT')
```

---

## Loading Performance

### Batch Size Optimization

**Finding Optimal Batch Size**:

```python
# Test different batch sizes
batch_sizes = [100, 500, 1000, 5000, 10000]

for batch_size in batch_sizes:
    start = time.time()
    load_records(batch_size=batch_size)
    elapsed = time.time() - start
    print(f"Batch {batch_size}: {elapsed:.2f}s")
```

**Recommended Batch Sizes**:

- SQLite: 1,000 - 5,000 records
- PostgreSQL: 5,000 - 10,000 records
- High-performance systems: 10,000 - 50,000 records

### Loading Best Practices

**1. Disable Indexes During Bulk Load** (PostgreSQL):

```sql
-- Before loading
DROP INDEX IF EXISTS idx_dsrc_record;
DROP INDEX IF EXISTS idx_obs_ent;

-- Load data

-- After loading
CREATE INDEX idx_dsrc_record ON dsrc_record(dsrc_id, record_id);
CREATE INDEX idx_obs_ent ON obs_ent(ent_id);
```

**2. Use WITH_INFO Flag Sparingly**:

```python
# Faster (no info returned)
g2_engine.addRecord(data_source, record_id, json_data)

# Slower (returns resolution info)
g2_engine.addRecordWithInfo(data_source, record_id, json_data, flags)
```

**3. Pre-sort Data**:

```python
# Sort by entity-likely fields for better cache locality
df = df.sort_values(['NAME_LAST', 'NAME_FIRST', 'DATE_OF_BIRTH'])
```

**4. Optimize JSON Serialization**:

```python
import ujson  # Faster than standard json

# Use ujson for better performance
record_json = ujson.dumps(record)
```

### Parallel Loading

**Multi-threaded Loading**:

```python
from concurrent.futures import ThreadPoolExecutor
from senzing import G2Engine

def load_batch(batch):
    """Load a batch of records"""
    engine = G2Engine()
    engine.init("Loader", config_json, False)

    for record in batch:
        engine.addRecord(
            record['DATA_SOURCE'],
            record['RECORD_ID'],
            json.dumps(record)
        )

    engine.destroy()

# Split data into batches
batches = [records[i:i+1000] for i in range(0, len(records), 1000)]

# Load in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    executor.map(load_batch, batches)
```

**Optimal Thread Count**:

- CPU cores: Use 1-2x number of cores
- I/O bound: Use 2-4x number of cores
- Test to find optimal for your system

---

## Query Performance

### Query Optimization Techniques

**1. Use Specific Flags**:

```python
# Only get what you need
G2_ENTITY_INCLUDE_RECORD_DATA  # Include record details
G2_ENTITY_INCLUDE_RELATED_ENTITIES  # Include relationships
G2_ENTITY_INCLUDE_ENTITY_NAME  # Include resolved name

# Combine flags
flags = (G2_ENTITY_INCLUDE_RECORD_DATA |
         G2_ENTITY_INCLUDE_ENTITY_NAME)
```

**2. Cache Frequently Accessed Entities**:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_entity_cached(entity_id):
    """Cache entity lookups"""
    response = bytearray()
    g2_engine.getEntityByEntityID(entity_id, response)
    return json.loads(response.decode())
```

**3. Batch Queries**:

```python
# Instead of individual queries
for record_id in record_ids:
    get_entity_by_record_id(record_id)

# Use batch export
export_handle = g2_engine.exportJSONEntityReport(flags)
while True:
    response = bytearray()
    g2_engine.fetchNext(export_handle, response)
    if not response:
        break
    # Process entity
```

### Search Optimization

**1. Use Appropriate Search Flags**:

```python
# Fast search (less detail)
G2_SEARCH_BY_ATTRIBUTES_MINIMAL_ALL

# Detailed search (slower)
G2_SEARCH_BY_ATTRIBUTES_ALL
```

**2. Limit Search Results**:

```python
# Limit results for better performance
search_results = g2_engine.searchByAttributes(
    search_json,
    max_results=100  # Limit results
)
```

---

## Memory Optimization

### Memory Configuration

**1. Senzing Memory Settings**:

```json
{
  "PIPELINE": {
    "CONFIGPATH": "/etc/opt/senzing",
    "RESOURCEPATH": "/opt/senzing/g2/resources",
    "SUPPORTPATH": "/opt/senzing/data"
  },
  "SQL": {
    "CONNECTION": "postgresql://user:pass@host:5432/db",
    "BACKEND": "HYBRID"
  }
}
```

**2. Python Memory Management**:

```python
import gc

# Periodic garbage collection
if record_count % 10000 == 0:
    gc.collect()

# Clear large objects
del large_dataframe
gc.collect()
```

**3. Generator Pattern for Large Datasets**:

```python
def read_records_generator(filename):
    """Memory-efficient record reading"""
    with open(filename, 'r') as f:
        for line in f:
            yield json.loads(line)

# Use generator instead of loading all into memory
for record in read_records_generator('large_file.jsonl'):
    process_record(record)
```

### Memory Monitoring

```python
import psutil
import os

def check_memory():
    """Monitor memory usage"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    print(f"Memory: {mem_info.rss / 1024 / 1024:.2f} MB")

# Check periodically
if record_count % 1000 == 0:
    check_memory()
```

---

## Parallel Processing

### Multi-Process Loading

```python
from multiprocessing import Pool
import os

def load_file(filename):
    """Load a file in separate process"""
    # Each process gets its own engine instance
    engine = G2Engine()
    engine.init(f"Loader-{os.getpid()}", config_json, False)

    with open(filename, 'r') as f:
        for line in f:
            record = json.loads(line)
            engine.addRecord(
                record['DATA_SOURCE'],
                record['RECORD_ID'],
                json.dumps(record)
            )

    engine.destroy()

# Split data into files
files = ['data1.jsonl', 'data2.jsonl', 'data3.jsonl', 'data4.jsonl']

# Process in parallel
with Pool(processes=4) as pool:
    pool.map(load_file, files)
```

### Optimal Parallelism

**Guidelines**:

- Start with number of CPU cores
- Monitor CPU and I/O utilization
- Increase if I/O bound, decrease if CPU bound
- Test different configurations

**Example Testing Script**:

```python
import time
from concurrent.futures import ProcessPoolExecutor

def test_parallelism(num_workers):
    """Test different worker counts"""
    start = time.time()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        executor.map(load_file, files)

    elapsed = time.time() - start
    throughput = total_records / elapsed

    print(f"Workers: {num_workers}, "
          f"Time: {elapsed:.2f}s, "
          f"Throughput: {throughput:.0f} rec/s")

# Test different configurations
for workers in [1, 2, 4, 8, 16]:
    test_parallelism(workers)
```

---

## Monitoring and Profiling

### Performance Monitoring

**1. Loading Metrics**:

```python
import time

class LoadingMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.records_loaded = 0
        self.errors = 0

    def record_loaded(self):
        self.records_loaded += 1
        if self.records_loaded % 1000 == 0:
            self.print_stats()

    def print_stats(self):
        elapsed = time.time() - self.start_time
        rate = self.records_loaded / elapsed
        print(f"Loaded: {self.records_loaded:,}, "
              f"Rate: {rate:.0f} rec/s, "
              f"Errors: {self.errors}")
```

**2. Query Profiling**:

```python
import time
from functools import wraps

def profile_query(func):
    """Decorator to profile query performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"{func.__name__}: {elapsed*1000:.2f}ms")
        return result
    return wrapper

@profile_query
def get_entity(entity_id):
    # Query implementation
    pass
```

### Python Profiling

**1. cProfile**:

```bash
python -m cProfile -o profile.stats load_data.py
python -m pstats profile.stats
```

**2. line_profiler**:

```bash
pip install line_profiler
kernprof -l -v load_data.py
```

**3. memory_profiler**:

```bash
pip install memory_profiler
python -m memory_profiler load_data.py
```

---

## Common Bottlenecks

### Identifying Bottlenecks

**1. CPU Bound**:

- Symptoms: High CPU usage (>80%)
- Solutions: Optimize algorithms, reduce processing per record

**2. I/O Bound**:

- Symptoms: Low CPU, high disk I/O
- Solutions: Increase batch size, use SSD, optimize database

**3. Memory Bound**:

- Symptoms: High memory usage, swapping
- Solutions: Use generators, process in batches, increase RAM

**4. Network Bound**:

- Symptoms: High network latency
- Solutions: Batch operations, use connection pooling, co-locate services

### Performance Troubleshooting

**Slow Loading**:

1. Check batch size (too small?)
2. Check database configuration
3. Check disk I/O (use SSD)
4. Check for index overhead
5. Consider parallel loading

**Slow Queries**:

1. Check query flags (requesting too much data?)
2. Check database indexes
3. Check result set size (too large?)
4. Consider caching
5. Optimize search criteria

**High Memory Usage**:

1. Use generators instead of lists
2. Process in smaller batches
3. Clear objects explicitly
4. Check for memory leaks
5. Increase available RAM

---

## Performance Tuning Checklist

### Database

- [ ] Indexes created
- [ ] Connection pool configured
- [ ] Memory settings optimized
- [ ] WAL mode enabled (SQLite)
- [ ] Vacuum/analyze run regularly

### Loading

- [ ] Optimal batch size determined
- [ ] Parallel loading configured
- [ ] Progress monitoring implemented
- [ ] Error handling robust
- [ ] Memory usage monitored

### Queries

- [ ] Appropriate flags used
- [ ] Caching implemented
- [ ] Batch queries where possible
- [ ] Result limits set
- [ ] Query profiling done

### System

- [ ] Adequate CPU allocated
- [ ] Sufficient RAM available
- [ ] Fast storage (SSD)
- [ ] Network latency low
- [ ] Monitoring configured

---

## Performance Testing

### Load Testing Script

```python
import time
import random
from senzing import G2Engine

def performance_test(num_records=10000):
    """Test loading performance"""
    engine = G2Engine()
    engine.init("PerfTest", config_json, False)

    start = time.time()

    for i in range(num_records):
        record = {
            "DATA_SOURCE": "TEST",
            "RECORD_ID": str(i),
            "NAME_FULL": f"Person {i}",
            "PHONE_NUMBER": f"555-{random.randint(1000,9999)}"
        }

        engine.addRecord(
            record['DATA_SOURCE'],
            record['RECORD_ID'],
            json.dumps(record)
        )

        if (i + 1) % 1000 == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            print(f"Progress: {i+1:,}/{num_records:,} "
                  f"({rate:.0f} rec/s)")

    total_time = time.time() - start
    final_rate = num_records / total_time

    print(f"\nCompleted: {num_records:,} records in {total_time:.2f}s")
    print(f"Average rate: {final_rate:.0f} records/second")

    engine.destroy()

if __name__ == "__main__":
    performance_test()
```

---

## Resources

- [Senzing Performance Guide](https://senzing.com/performance)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [SQLite Performance](https://www.sqlite.org/performance.html)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)

---

**Document Owner**: Performance Team
**Last Review**: 2026-03-17
**Next Review**: 2026-06-17
