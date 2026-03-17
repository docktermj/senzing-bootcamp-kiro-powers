# Module 9: Performance Testing and Benchmarking

## Overview

Module 9 focuses on testing performance and scalability before production deployment. This module ensures your entity resolution solution can handle expected workloads.

## Purpose

After validating results in Module 8, Module 9 helps you:

1. **Benchmark transformation speed** (records/second)
2. **Benchmark loading performance** (records/second)
3. **Test query response times** (milliseconds)
4. **Profile resource utilization** (CPU, memory, disk)
5. **Test scalability** (10K, 100K, 1M records)
6. **Generate performance report** with recommendations

## Why Performance Testing Matters

- **Prevent production surprises**: Find bottlenecks before deployment
- **Capacity planning**: Understand resource requirements
- **Set expectations**: Know realistic throughput
- **Optimize**: Identify and fix performance issues
- **Validate**: Ensure solution meets SLAs

## Performance Benchmarks

### Transformation Performance

Test data transformation speed:

```python
# Benchmark transformation
import time

start = time.time()
records_transformed = 0

for record in read_source('data/raw/customers.csv'):
    transformed = transform(record)
    records_transformed += 1

duration = time.time() - start
throughput = records_transformed / duration

print(f"Transformation: {throughput:.0f} records/second")
```

**Typical Performance**:
- Simple transformations: 1,000-10,000 records/second
- Complex transformations: 100-1,000 records/second
- With validation: 50-500 records/second

### Loading Performance

Test Senzing loading speed:

```python
# Benchmark loading
start = time.time()
records_loaded = 0

for record in read_transformed('data/transformed/customers.jsonl'):
    engine.addRecord(DATA_SOURCE, record['RECORD_ID'], record)
    records_loaded += 1

duration = time.time() - start
throughput = records_loaded / duration

print(f"Loading: {throughput:.0f} records/second")
```

**Typical Performance**:
- SQLite: 20-50 records/second
- PostgreSQL (local): 100-500 records/second
- PostgreSQL (tuned): 500-2,000 records/second
- PostgreSQL (clustered): 2,000-10,000 records/second

### Query Performance

Test query response times:

```python
# Benchmark queries
import statistics

response_times = []

for i in range(100):
    start = time.time()
    result = engine.searchByAttributes(search_criteria)
    duration = time.time() - start
    response_times.append(duration * 1000)  # Convert to ms

print(f"Query response time:")
print(f"  Average: {statistics.mean(response_times):.1f} ms")
print(f"  Median: {statistics.median(response_times):.1f} ms")
print(f"  P95: {statistics.quantiles(response_times, n=20)[18]:.1f} ms")
print(f"  P99: {statistics.quantiles(response_times, n=100)[98]:.1f} ms")
```

**Typical Performance**:
- Simple queries: 10-50 ms
- Complex queries: 50-200 ms
- Large result sets: 200-1000 ms

### Resource Utilization

Monitor system resources during loading:

```python
import psutil
import time

def monitor_resources(duration=60):
    """Monitor CPU, memory, disk for specified duration"""
    samples = []
    
    for i in range(duration):
        sample = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_io': psutil.disk_io_counters(),
        }
        samples.append(sample)
    
    return samples
```

## Scalability Testing

Test with increasing data volumes:

```
Test 1: 10,000 records
  - Transformation: 5,000 records/sec
  - Loading: 200 records/sec
  - Query: 25 ms average

Test 2: 100,000 records
  - Transformation: 4,800 records/sec (-4%)
  - Loading: 180 records/sec (-10%)
  - Query: 35 ms average (+40%)

Test 3: 1,000,000 records
  - Transformation: 4,500 records/sec (-10%)
  - Loading: 150 records/sec (-25%)
  - Query: 75 ms average (+200%)
```

## Performance Testing Script

```python
#!/usr/bin/env python3
"""
Performance Testing and Benchmarking Script
Tests transformation, loading, and query performance
"""

import time
import statistics
import psutil
import json
from typing import Dict, List
from dataclasses import dataclass, asdict

@dataclass
class PerformanceMetrics:
    test_name: str
    record_count: int
    duration_seconds: float
    throughput_per_second: float
    cpu_avg_percent: float
    memory_avg_percent: float
    
    def to_dict(self):
        return asdict(self)

class PerformanceTester:
    def __init__(self):
        self.results = []
    
    def benchmark_transformation(self, input_file: str, sample_size: int = 10000):
        """Benchmark transformation performance"""
        print(f"\n{'='*60}")
        print(f"TRANSFORMATION BENCHMARK ({sample_size:,} records)")
        print(f"{'='*60}")
        
        # Monitor resources
        cpu_samples = []
        memory_samples = []
        
        start_time = time.time()
        records_processed = 0
        
        # TODO: Implement actual transformation
        # for record in read_source(input_file, limit=sample_size):
        #     transformed = transform(record)
        #     records_processed += 1
        
        # Simulate for now
        time.sleep(2)
        records_processed = sample_size
        
        duration = time.time() - start_time
        throughput = records_processed / duration
        
        metrics = PerformanceMetrics(
            test_name='transformation',
            record_count=records_processed,
            duration_seconds=duration,
            throughput_per_second=throughput,
            cpu_avg_percent=psutil.cpu_percent(),
            memory_avg_percent=psutil.virtual_memory().percent
        )
        
        self.results.append(metrics)
        
        print(f"Records processed: {records_processed:,}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Throughput: {throughput:.0f} records/second")
        print(f"CPU: {metrics.cpu_avg_percent:.1f}%")
        print(f"Memory: {metrics.memory_avg_percent:.1f}%")
        
        return metrics
    
    def benchmark_loading(self, input_file: str, sample_size: int = 1000):
        """Benchmark loading performance"""
        print(f"\n{'='*60}")
        print(f"LOADING BENCHMARK ({sample_size:,} records)")
        print(f"{'='*60}")
        
        start_time = time.time()
        records_loaded = 0
        
        # TODO: Implement actual loading
        # for record in read_transformed(input_file, limit=sample_size):
        #     engine.addRecord(DATA_SOURCE, record['RECORD_ID'], record)
        #     records_loaded += 1
        
        # Simulate for now
        time.sleep(5)
        records_loaded = sample_size
        
        duration = time.time() - start_time
        throughput = records_loaded / duration
        
        metrics = PerformanceMetrics(
            test_name='loading',
            record_count=records_loaded,
            duration_seconds=duration,
            throughput_per_second=throughput,
            cpu_avg_percent=psutil.cpu_percent(),
            memory_avg_percent=psutil.virtual_memory().percent
        )
        
        self.results.append(metrics)
        
        print(f"Records loaded: {records_loaded:,}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Throughput: {throughput:.0f} records/second")
        print(f"CPU: {metrics.cpu_avg_percent:.1f}%")
        print(f"Memory: {metrics.memory_avg_percent:.1f}%")
        
        return metrics
    
    def benchmark_queries(self, num_queries: int = 100):
        """Benchmark query performance"""
        print(f"\n{'='*60}")
        print(f"QUERY BENCHMARK ({num_queries} queries)")
        print(f"{'='*60}")
        
        response_times = []
        
        for i in range(num_queries):
            start = time.time()
            
            # TODO: Implement actual query
            # result = engine.searchByAttributes(search_criteria)
            
            # Simulate for now
            time.sleep(0.025)  # 25ms
            
            duration = (time.time() - start) * 1000  # Convert to ms
            response_times.append(duration)
        
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        p99_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
        
        print(f"Queries executed: {num_queries}")
        print(f"Average response time: {avg_time:.1f} ms")
        print(f"Median response time: {median_time:.1f} ms")
        print(f"P95 response time: {p95_time:.1f} ms")
        print(f"P99 response time: {p99_time:.1f} ms")
        
        return {
            'num_queries': num_queries,
            'avg_ms': avg_time,
            'median_ms': median_time,
            'p95_ms': p95_time,
            'p99_ms': p99_time
        }
    
    def scalability_test(self, sizes: List[int] = [1000, 10000, 100000]):
        """Test scalability with increasing data volumes"""
        print(f"\n{'='*60}")
        print(f"SCALABILITY TEST")
        print(f"{'='*60}")
        
        for size in sizes:
            print(f"\nTesting with {size:,} records...")
            self.benchmark_transformation('data/raw/test.csv', size)
            self.benchmark_loading('data/transformed/test.jsonl', min(size, 10000))
    
    def generate_report(self, output_file: str = 'docs/performance_report.json'):
        """Generate performance report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'platform': 'Linux'  # TODO: Get actual platform
            },
            'results': [r.to_dict() for r in self.results]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nPerformance report saved to: {output_file}")
        return report

if __name__ == '__main__':
    tester = PerformanceTester()
    
    # Run benchmarks
    tester.benchmark_transformation('data/raw/customers.csv', 10000)
    tester.benchmark_loading('data/transformed/customers.jsonl', 1000)
    tester.benchmark_queries(100)
    
    # Scalability test
    # tester.scalability_test([1000, 10000, 100000])
    
    # Generate report
    tester.generate_report()
```

## Performance Optimization Tips

### Transformation Optimization
- Use batch processing
- Minimize I/O operations
- Cache lookups
- Use efficient data structures
- Parallelize independent transformations

### Loading Optimization
- Use batch loading (1000 records/batch)
- Tune database parameters
- Use connection pooling
- Disable unnecessary indexes during load
- Use PostgreSQL instead of SQLite

### Query Optimization
- Add database indexes
- Use specific queries (not export all)
- Cache frequent queries
- Use appropriate flags
- Limit result set size

## Agent Behavior

When a user is in Module 9, the agent should:

1. **Create performance testing script** in `src/testing/`
2. **Run transformation benchmarks**
3. **Run loading benchmarks**
4. **Run query benchmarks**
5. **Test scalability** with increasing volumes
6. **Monitor resource utilization**
7. **Generate performance report**
8. **Provide optimization recommendations**
9. **Document results** in `docs/performance_report.md`

## Validation Gates

Before completing Module 9:

- [ ] Transformation benchmarked
- [ ] Loading benchmarked
- [ ] Queries benchmarked
- [ ] Scalability tested
- [ ] Resource utilization monitored
- [ ] Performance report generated
- [ ] Bottlenecks identified
- [ ] Optimization recommendations documented

## Success Indicators

Module 9 is complete when:

- Performance meets requirements
- Bottlenecks identified and addressed
- Scalability validated
- Resource requirements documented
- Optimization recommendations provided
- Ready for production workload

## Output Files

- `src/testing/performance_test.py` - Testing script
- `docs/performance_report.json` - Detailed metrics
- `docs/performance_report.md` - Summary and recommendations
- `docs/performance_dashboard.html` - Visual dashboard

## Related Documentation

- `POWER.md` - Module 9 overview
- `steering/steering.md` - Module 9 workflow (to be added)
- `steering/performance-monitoring.md` - Ongoing monitoring

## Version History

- **v3.0.0** (2026-03-17): Module 9 created for performance testing
