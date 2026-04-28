```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE 9: PERFORMANCE TESTING AND BENCHMARKING  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

# Module 9: Performance Testing and Benchmarking

> **Agent workflow:** The agent follows `steering/module-09-performance.md` for this module's step-by-step workflow.

## Overview

Module 9 focuses on testing performance and scalability before production deployment. This module ensures your entity resolution solution can handle expected workloads.

## Purpose

After building query programs and visualizations in Module 8, Module 9 helps you:

1. **Benchmark transformation speed** (records/second)
2. **Benchmark loading performance** (records/second)
3. **Test query response times** (milliseconds)
4. **Profile resource utilization** (CPU, memory, disk)
5. **Test scalability** (10K, 100K, 1M records)
6. **Generate performance report** with recommendations

## Why Performance Testing Matters

- **Prevent production surprises:** Find bottlenecks before deployment
- **Capacity planning:** Understand resource requirements
- **Set expectations:** Know realistic throughput
- **Optimize:** Identify and fix performance issues
- **Validate:** Ensure solution meets SLAs

## Performance Benchmarks

### Transformation Performance

Test data transformation speed:

```text
BENCHMARK: Transformation Throughput
─────────────────────────────────────
1. Record the current timestamp (start_time)
2. Set records_transformed = 0
3. For each record in source file (e.g., data/raw/customers.csv):
     a. Apply transformation logic to the record
     b. Increment records_transformed
4. Record the current timestamp (end_time)
5. Compute duration = end_time - start_time
6. Compute throughput = records_transformed / duration
7. Print "Transformation: {throughput} records/second"
```

**Typical Performance:**

Use `search_docs(query="transformation performance", version="current")` for current benchmarks.

### Loading Performance

Test Senzing loading speed:

```text
BENCHMARK: Loading Throughput
─────────────────────────────
1. Record the current timestamp (start_time)
2. Set records_loaded = 0
3. For each record in transformed file (e.g., data/transformed/customers.jsonl):
     a. Call engine.add_record(DATA_SOURCE, record.RECORD_ID, record)
     b. Increment records_loaded
4. Record the current timestamp (end_time)
5. Compute duration = end_time - start_time
6. Compute throughput = records_loaded / duration
7. Print "Loading: {throughput} records/second"
```

**Typical Performance:**

> **Agent instruction:** Do not state specific performance numbers. Use
> `search_docs(query="loading performance benchmarks", version="current")` to get
> current performance expectations for each database type. Performance varies by
> Senzing version, hardware, and configuration.

### Query Performance

Test query response times:

```text
BENCHMARK: Query Response Times
────────────────────────────────
1. Initialize an empty list: response_times
2. Repeat num_queries times (e.g., 100):
     a. Record start_time
     b. Call engine.search_by_attributes(search_criteria)
     c. Record end_time
     d. Append (end_time - start_time) in milliseconds to response_times
3. Compute and print:
     - Average:  mean(response_times)
     - Median:   median(response_times)
     - P95:      95th percentile of response_times
     - P99:      99th percentile of response_times
```

**Typical Performance:**

Use `search_docs(query="query response time benchmarks", version="current")` for current benchmarks.

### Resource Utilization

Monitor system resources during loading:

```text
BENCHMARK: Resource Utilization
────────────────────────────────
1. Set monitoring duration (e.g., 60 seconds)
2. Initialize an empty list: samples
3. Repeat once per second for the duration:
     a. Sample current CPU usage (percent)
     b. Sample current memory usage (percent)
     c. Sample current disk I/O counters
     d. Append {cpu_percent, memory_percent, disk_io} to samples
4. Compute averages and peaks across all samples
5. Report: avg CPU %, peak CPU %, avg memory %, peak memory %, total disk I/O
```

Use your language's profiling and resource monitoring tools (e.g., OS-level APIs, runtime profilers, or third-party monitoring libraries) to collect these metrics.

## Scalability Testing

Test with increasing data volumes:

```text
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

> **Agent instruction:** Generate performance testing code in the bootcamper's chosen
> language using `generate_scaffold(language=<chosen>, workflow="full_pipeline", version="current")`
> and `find_examples(query="performance benchmarking")`. The generated script should be
> saved to `src/testing/performance_test.[ext]`.

The performance tester should implement the following:

### Data Structure: PerformanceMetrics

Each benchmark run produces a metrics record containing:

| Field                  | Type    | Description                                                          |
|------------------------|---------|----------------------------------------------------------------------|
| test_name              | string  | Name of the benchmark (e.g., "transformation", "loading", "queries") |
| record_count           | integer | Number of records processed                                          |
| duration_seconds       | float   | Total elapsed time                                                   |
| throughput_per_second  | float   | Records processed per second                                         |
| cpu_avg_percent        | float   | Average CPU utilization during test                                  |
| memory_avg_percent     | float   | Average memory utilization during test                               |

### Benchmarks to Implement

#### 1. Transformation Benchmark

```text
benchmark_transformation(input_file, sample_size=10000):
─────────────────────────────────────────────────────────
1. Print header: "TRANSFORMATION BENCHMARK ({sample_size} records)"
2. Record start_time
3. For each record in input_file (up to sample_size):
     a. Apply transformation logic
     b. Increment records_processed
4. Record end_time
5. Compute duration and throughput
6. Sample current CPU and memory usage
7. Store PerformanceMetrics(test_name="transformation", ...)
8. Print: records processed, duration, throughput, CPU %, memory %
9. Return the metrics
```

#### 2. Loading Benchmark

```text
benchmark_loading(input_file, sample_size=1000):
─────────────────────────────────────────────────
1. Print header: "LOADING BENCHMARK ({sample_size} records)"
2. Record start_time
3. For each record in input_file (up to sample_size):
     a. Call engine.add_record(DATA_SOURCE, record.RECORD_ID, JSON(record))
     b. Increment records_loaded
4. Record end_time
5. Compute duration and throughput
6. Sample current CPU and memory usage
7. Store PerformanceMetrics(test_name="loading", ...)
8. Print: records loaded, duration, throughput, CPU %, memory %
9. Return the metrics
```

#### 3. Query Benchmark

```text
benchmark_queries(num_queries=100):
────────────────────────────────────
1. Print header: "QUERY BENCHMARK ({num_queries} queries)"
2. Initialize empty list: response_times
3. Repeat num_queries times:
     a. Record start_time
     b. Call engine.search_by_attributes(JSON(search_criteria))
     c. Compute elapsed time in milliseconds, append to response_times
4. Compute: average, median, P95, P99 from response_times
5. Print all statistics
6. Return the query metrics
```

#### 4. Scalability Test

```text
scalability_test(sizes=[1000, 10000, 100000]):
───────────────────────────────────────────────
1. Print header: "SCALABILITY TEST"
2. For each size in sizes:
     a. Print "Testing with {size} records..."
     b. Run benchmark_transformation(source_file, size)
     c. Run benchmark_loading(transformed_file, min(size, 10000))
3. Compare throughput degradation across sizes
```

#### 5. Report Generation

```text
generate_report(output_file="docs/performance_report.json"):
─────────────────────────────────────────────────────────────
1. Collect system info: CPU count, total memory (GB), platform
2. Build report object:
     {
       "timestamp": current datetime,
       "system_info": { cpu_count, memory_total_gb, platform },
       "results": [ each stored PerformanceMetrics as a dictionary ]
     }
3. Write report as JSON to output_file
4. Print "Performance report saved to: {output_file}"
```

### Main Entry Point

```text
main():
──────
1. Initialize the performance tester
2. Run benchmark_transformation("data/raw/customers.csv", 10000)
3. Run benchmark_loading("data/transformed/customers.jsonl", 1000)
4. Run benchmark_queries(100)
5. (Optional) Run scalability_test([1000, 10000, 100000])
6. Generate report
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

1. **Create performance testing script** in `src/testing/performance_test.[ext]`
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

- `src/testing/performance_test.[ext]` - Testing script
- `docs/performance_report.json` - Detailed metrics
- `docs/performance_report.md` - Summary and recommendations
- `docs/performance_dashboard.html` - Visual dashboard

## Related Documentation

- `POWER.md` - Module 9 overview
- `steering/module-09-performance.md` - Module 9 workflow
- Use MCP: `reporting_guide(topic="reports")` for SQL analytics queries on entity resolution results
- Use MCP: `reporting_guide(topic="data_mart")` for analytical schema and incremental update patterns
- Use MCP: `search_docs(query="performance monitoring", category="performance")` for ongoing monitoring

## Version History

- **v4.0.0** (2026-04-01): Rewritten to be language-agnostic; replaced Python code with pseudocode and agent scaffold instructions
- **v3.0.0** (2026-03-17): Module 9 created for performance testing
- **v5.0.0** (2026-04-17): Renumbered from Module 9 to Module 9 (merge of old Modules 4+5)
