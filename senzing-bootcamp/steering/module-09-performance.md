---
inclusion: manual
---

# Module 9: Performance Testing and Benchmarking

**Purpose**: Benchmark and optimize for production performance.

**Prerequisites**:

- ✅ Module 8 complete (queries working)
- ✅ Representative data loaded
- ✅ Test environment available

**Agent Workflow**:

1. **Define performance requirements**:

   Ask: "What are your performance requirements?"

   Common metrics:
   - Loading throughput (records/second)
   - Query latency (milliseconds)
   - Concurrent users
   - Data volume

   WAIT for response.

2. **Benchmark transformation**:

   Create `tests/performance/test_transform_performance.py`:

   ```python
   def benchmark_transformation(sample_size=10000):
       start = time.time()
       # Run transformation
       duration = time.time() - start
       rate = sample_size / duration
       print(f"Transformation rate: {rate:.1f} records/sec")
       return rate
   ```

3. **Benchmark loading**:

   Create `tests/performance/test_load_performance.py`:

   ```python
   def benchmark_loading(sample_size=10000):
       start = time.time()
       # Load records
       duration = time.time() - start
       rate = sample_size / duration
       print(f"Loading rate: {rate:.1f} records/sec")
       return rate
   ```

4. **Benchmark queries**:

   Create `tests/performance/test_query_performance.py`:

   ```python
   def benchmark_queries():
       queries = [
           ("search_by_name", lambda: search("John Smith")),
           ("get_entity", lambda: get_entity(12345)),
           ("find_duplicates", lambda: find_duplicates())
       ]

       for name, query_func in queries:
           start = time.time()
           query_func()
           duration = time.time() - start
           print(f"{name}: {duration*1000:.1f}ms")
   ```

5. **Profile resource usage**:

   Monitor:
   - CPU utilization
   - Memory usage
   - Disk I/O
   - Network I/O

   Use tools like `psutil`, `py-spy`, or system monitors.

6. **Scalability testing**:

   Test with increasing data volumes:
   - 10K records
   - 100K records
   - 1M records
   - 10M records (if applicable)

   Document how performance scales.

7. **Identify bottlenecks**:

   Common bottlenecks:
   - Slow transformations → Optimize code, use multiprocessing
   - Slow loading → Use PostgreSQL, increase batch size
   - Slow queries → Add indexes, optimize query logic
   - Memory issues → Reduce batch size, stream data

8. **Optimize and retest**:

   Apply optimizations and re-run benchmarks.

   Document improvements in `docs/performance_optimization.md`.

9. **Create performance report**:

   Document in `docs/performance_report.md`:

   ```markdown
   # Performance Report

   ## Transformation
   - Rate: 5,000 records/sec
   - Bottleneck: JSON parsing
   - Optimization: Used ujson library

   ## Loading
   - Rate: 1,200 records/sec
   - Database: PostgreSQL
   - Batch size: 1000

   ## Queries
   - Search by name: 45ms p95
   - Get entity: 12ms p95
   - Find duplicates: 2.3 seconds (100K entities)

   ## Scalability
   - Linear scaling up to 1M records
   - Recommend horizontal scaling beyond 5M records
   ```

**Success Criteria**:

- ✅ Performance benchmarks completed
- ✅ Requirements met or optimization plan created
- ✅ Bottlenecks identified and addressed
- ✅ Scalability tested
- ✅ Performance report documented
