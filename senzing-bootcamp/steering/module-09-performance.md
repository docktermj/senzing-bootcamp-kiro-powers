---
inclusion: manual
---

# Module 9: Performance Testing and Benchmarking

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_9_PERFORMANCE_TESTING.md`.

## Workflow: Performance Testing and Optimization (Module 9)

Benchmark, profile, and optimize your Senzing entity resolution pipeline for production-grade performance. This module takes the working system from Modules 6-8 and ensures it meets real-world throughput, latency, and scalability requirements.

**Language**: Use the bootcamper's chosen programming language throughout. All code generation, scaffold calls, benchmark scripts, and examples must use `<chosen_language>`.

**Prerequisites**:

- ✅ Module 8 complete (queries working, results validated)
- ✅ Representative data loaded (at least one full data source)
- ✅ Test environment available (dedicated machine or container — not shared dev)
- ✅ Loading programs from Module 6/7 available in `src/load/`
- ✅ Query programs from Module 8 available in `src/query/`

## Step 1: Establish Performance Requirements

Before benchmarking, define what "good enough" means for this project.

Ask: "What are your performance requirements for production? Let's define targets for each area."

WAIT for response.

Walk through each category ONE AT A TIME. If the user is unsure, provide industry context to help them decide.

**Question 1: Loading throughput**
Ask: "How many records per second do you need to load? This depends on your data volume and how often you reload. For context, typical Senzing throughput ranges from hundreds to thousands of records/second depending on hardware and database."

> **Agent instruction:** Call `search_docs(query='performance benchmarks', version='current')` to get
> current performance expectations from official documentation. Use these numbers — not training data —
> when setting expectations with the user. Performance varies significantly by hardware, database choice,
> and data complexity.

WAIT for response.

### Question 2: Query latency

Ask: "What query response times do you need? For example: real-time search (<100ms), interactive queries (<1 second), or batch processing (minutes are acceptable)?"

WAIT for response.

### Question 3: Concurrent users

Ask: "How many concurrent users or processes will query the system? This affects connection pooling and resource allocation."

WAIT for response.

### Question 4: Data volume and growth

Ask: "What's your current data volume, and how fast is it growing? For example: 100K records now, growing 10K/month. This determines whether we need to plan for scale-out."

WAIT for response.

### Question 5: Database choice

Ask: "Are you using SQLite or PostgreSQL? This significantly affects performance characteristics and optimization strategies."

> **Agent instruction:** Call `search_docs(query='database tuning', category='configuration', version='current')`
> to get database-specific tuning guidance. SQLite and PostgreSQL have very different performance
> profiles and optimization approaches. Use this information to set realistic expectations.

WAIT for response.

Document the requirements in `docs/performance_requirements.md`:

```markdown
# Performance Requirements

**Date**: [Current date]
**Project**: [Project name]
**Database**: [SQLite / PostgreSQL]
**Hardware**: [CPU cores, RAM, disk type]

## Targets
| Metric                  | Target          | Priority   |
|-------------------------|-----------------|------------|
| Loading throughput      | [X] records/sec | [Critical] |
| Search latency (p95)    | [X] ms          | [High]     |
| Entity retrieval (p95)  | [X] ms          | [High]     |
| Concurrent users        | [X]             | [Medium]   |
| Max data volume         | [X] records     | [Critical] |
| Batch export time       | [X] minutes     | [Low]      |

## Constraints
- Database: [SQLite / PostgreSQL]
- Hardware: [Description]
- Network: [Local / Remote database]
- Budget: [Hardware/cloud budget if applicable]
```

## Step 2: Review Anti-Patterns Before Benchmarking

Before writing any benchmark code, check for known performance pitfalls.

> **Agent instruction:** Call `search_docs(query='loading performance', category='anti_patterns', version='current')`
> to retrieve known performance anti-patterns. Review these BEFORE recommending any optimization
> strategies. Common anti-patterns include:
>
> - Single-threaded loading when multi-threading is available
> - Not processing redo records
> - Using SQLite for large production workloads
> - Incorrect batch sizes
> - Missing database indexes
> - Not monitoring engine statistics
>
> Present relevant anti-patterns to the user so they can avoid them from the start.

Ask: "Before we start benchmarking, let me check for common performance pitfalls that apply to your setup. I'll review known anti-patterns for [their database choice] and [their data volume]."

Share the relevant anti-patterns with the user and discuss which ones apply to their situation.

## Step 3: Create Baseline Environment

Establish a clean, reproducible test environment before running benchmarks.

```text
function setup_benchmark_environment():
    -- Record system information for reproducibility
    capture CPU model, core count, and clock speed
    capture total RAM and available RAM
    capture disk type (SSD/HDD) and available space
    capture OS version and kernel
    capture Senzing SDK version
    capture database type and version

    -- Create a fresh database for benchmarking
    if using SQLite:
        copy database/G2C.db to database/G2C_backup_before_benchmark.db
    if using PostgreSQL:
        create a snapshot or backup of the current database

    -- Save environment info
    write system info to docs/benchmark_environment.md
```

Save the environment setup script to `tests/performance/setup_benchmark_env.[ext]`.

Document the environment in `docs/benchmark_environment.md`:

```markdown
# Benchmark Environment

**Date**: [Current date]
**Machine**: [Description]

## Hardware
- CPU: [Model, cores, clock]
- RAM: [Total GB]
- Disk: [Type, speed]
- Network: [If remote database]

## Software
- OS: [Version]
- Senzing SDK: [Version]
- Database: [SQLite / PostgreSQL version]
- Language runtime: [<chosen_language> version]

## Data Profile
- Total records: [Count]
- Data sources: [Count and names]
- Average record size: [Bytes]
- Feature complexity: [Low/Medium/High — based on number of features per record]
```

## Step 4: Benchmark Transformation Throughput

Measure how fast your transformation programs (from Module 5) convert raw data to Senzing JSON format.

> **Agent instruction:** Use `find_examples(query='performance testing')` to find real-world
> performance testing patterns from indexed Senzing GitHub repositories. Adapt these patterns
> to the bootcamper's chosen language and data sources.

Create `tests/performance/bench_transform.[ext]`:

```text
function benchmark_transformation(input_file, sample_sizes = [100, 1000, 10000]):
    print "=== Transformation Benchmark ==="
    print "Input: {input_file}"
    print ""

    results = empty list

    for each sample_size in sample_sizes:
        -- Read sample_size records from input_file
        records = read_records(input_file, limit=sample_size)

        -- Warm-up run (discard results)
        transform_batch(records)

        -- Timed runs (3 iterations for statistical significance)
        durations = empty list
        for iteration in 1 to 3:
            record start_time
            transformed = transform_batch(records)
            record end_time
            duration = end_time - start_time
            append duration to durations

        avg_duration = average(durations)
        rate = sample_size / avg_duration
        records_with_errors = count records that failed transformation

        print "Sample size: {sample_size}"
        print "  Average duration: {avg_duration:.2f} seconds"
        print "  Throughput: {rate:.0f} records/sec"
        print "  Error rate: {records_with_errors / sample_size * 100:.1f}%"
        print ""

        append {sample_size, avg_duration, rate, records_with_errors} to results

    return results
```

Run the benchmark and review results with the user:

Ask: "Here are the transformation throughput results. The transformation step is rarely the bottleneck — loading into Senzing is typically slower. Does this throughput meet your needs, or should we optimize the transformation code first?"

WAIT for response.

## Step 5: Benchmark Loading Throughput

This is the most critical benchmark. Measure how fast records are loaded into the Senzing engine and entity resolution is performed.

> **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`
> to get the current V4 loading pattern. Use this as the foundation for the benchmark script.
> Do NOT use V3 patterns (G2Engine, init/destroy). The scaffold provides correct initialization,
> record addition, and cleanup patterns.

Create `tests/performance/bench_load.[ext]`:

```text
function benchmark_loading(input_file, sample_sizes = [100, 1000, 5000, 10000]):
    print "=== Loading Benchmark ==="
    print "Input: {input_file}"
    print "Database: {database_type}"
    print ""

    results = empty list

    for each sample_size in sample_sizes:
        -- Create a fresh database or clean slate for each run
        initialize_fresh_database()

        -- Read sample_size records from the transformed JSONL file
        records = read_jsonl(input_file, limit=sample_size)

        -- Initialize Senzing engine
        engine = initialize_senzing_engine(engine_config)

        -- Timed loading
        record start_time
        success_count = 0
        error_count = 0
        errors = empty list

        for each record in records:
            try:
                engine.add_record(
                    data_source = record["DATA_SOURCE"],
                    record_id = record["RECORD_ID"],
                    record_definition = serialize(record)
                )
                success_count = success_count + 1
            catch error:
                error_count = error_count + 1
                append {record_id, error_message} to errors

            -- Print progress every 1000 records
            if success_count modulo 1000 == 0:
                elapsed = current_time - start_time
                current_rate = success_count / elapsed
                print "  Loaded {success_count}/{sample_size} — {current_rate:.0f} rec/sec"

        record end_time
        duration = end_time - start_time
        rate = success_count / duration

        print ""
        print "Sample size: {sample_size}"
        print "  Duration: {duration:.2f} seconds"
        print "  Throughput: {rate:.0f} records/sec"
        print "  Success: {success_count}, Errors: {error_count}"
        print "  Error rate: {error_count / sample_size * 100:.1f}%"
        print ""

        -- Clean up engine
        engine.destroy()

        append {sample_size, duration, rate, success_count, error_count} to results

    -- Print summary table
    print "=== Loading Benchmark Summary ==="
    print "Sample Size | Duration (s) | Rate (rec/s) | Errors"
    print "------------|-------------|-------------|-------"
    for each result in results:
        print "{result.sample_size:>11} | {result.duration:>11.2f} | {result.rate:>11.0f} | {result.error_count}"

    return results
```

Save to `tests/performance/bench_load.[ext]`.

Run the benchmark and discuss results:

Ask: "Here are the loading throughput results. Loading is where entity resolution happens, so this is the most important benchmark. How do these numbers compare to your requirements from Step 1?"

WAIT for response.

If throughput is below requirements, note it — optimization comes in Step 9.

## Step 6: Benchmark Query Latency

Measure response times for the query patterns established in Module 8.

Create `tests/performance/bench_query.[ext]`:

```text
function benchmark_queries(iterations = 100):
    print "=== Query Benchmark ==="
    print "Iterations per query: {iterations}"
    print ""

    -- Initialize Senzing engine
    engine = initialize_senzing_engine(engine_config)

    -- Define query benchmarks based on Module 8 query programs
    benchmarks = [
        {
            name: "search_by_name",
            description: "Search for entity by name",
            function: lambda -> engine.search_by_attributes(
                '{"NAME_FULL": "John Smith"}'
            )
        },
        {
            name: "search_by_name_address",
            description: "Search by name + address",
            function: lambda -> engine.search_by_attributes(
                '{"NAME_FULL": "John Smith", "ADDR_FULL": "123 Main St"}'
            )
        },
        {
            name: "get_entity_by_id",
            description: "Retrieve entity by entity ID",
            function: lambda -> engine.get_entity_by_entity_id(entity_id=1)
        },
        {
            name: "get_entity_by_record",
            description: "Retrieve entity by data source + record ID",
            function: lambda -> engine.get_entity_by_record_id(
                data_source_code="CUSTOMERS",
                record_id="1001"
            )
        },
        {
            name: "why_entity",
            description: "Get match explanation for an entity",
            function: lambda -> engine.why_entity_by_entity_id(entity_id=1)
        },
        {
            name: "how_entity",
            description: "Get resolution steps for an entity",
            function: lambda -> engine.how_entity_by_entity_id(entity_id=1)
        }
    ]

    results = empty list

    for each benchmark in benchmarks:
        latencies = empty list

        -- Warm-up (5 iterations, discard)
        for i in 1 to 5:
            benchmark.function()

        -- Timed iterations
        for i in 1 to iterations:
            record start_time
            benchmark.function()
            record end_time
            latency_ms = (end_time - start_time) * 1000
            append latency_ms to latencies

        -- Calculate percentiles
        sort latencies
        p50 = latencies[iterations * 0.50]
        p95 = latencies[iterations * 0.95]
        p99 = latencies[iterations * 0.99]
        avg = average(latencies)
        min_val = minimum(latencies)
        max_val = maximum(latencies)

        print "{benchmark.name}: {benchmark.description}"
        print "  p50: {p50:.1f} ms | p95: {p95:.1f} ms | p99: {p99:.1f} ms"
        print "  avg: {avg:.1f} ms | min: {min_val:.1f} ms | max: {max_val:.1f} ms"
        print ""

        append {name, p50, p95, p99, avg, min_val, max_val} to results

    engine.destroy()

    -- Print summary table
    print "=== Query Benchmark Summary ==="
    print "Query                  | p50 (ms) | p95 (ms) | p99 (ms)"
    print "-----------------------|----------|----------|--------"
    for each result in results:
        print "{result.name:<22} | {result.p50:>8.1f} | {result.p95:>8.1f} | {result.p99:>8.1f}"

    return results
```

Save to `tests/performance/bench_query.[ext]`.

Run the benchmark and discuss:

Ask: "Here are the query latency results. The p95 values are what matter most for user experience — 95% of queries complete within that time. Do these meet your latency requirements?"

WAIT for response.

## Step 7: Profile Resource Usage

Monitor system resources during loading and querying to identify hardware bottlenecks.

Create `tests/performance/profile_resources.[ext]`:

```text
function profile_resources_during_load(input_file, sample_size = 5000):
    print "=== Resource Profiling ==="
    print "Monitoring system resources during loading of {sample_size} records"
    print ""

    -- Start resource monitoring in a background thread/process
    monitor = start_resource_monitor(interval_seconds=1)

    -- Run the loading benchmark
    initialize_fresh_database()
    engine = initialize_senzing_engine(engine_config)

    record start_time
    records = read_jsonl(input_file, limit=sample_size)

    for each record in records:
        engine.add_record(record["DATA_SOURCE"], record["RECORD_ID"], serialize(record))

    record end_time
    engine.destroy()

    -- Stop monitoring and collect results
    resource_data = monitor.stop()

    -- Analyze resource usage
    print "Duration: {end_time - start_time:.1f} seconds"
    print ""
    print "CPU Usage:"
    print "  Average: {resource_data.cpu_avg:.1f}%"
    print "  Peak: {resource_data.cpu_peak:.1f}%"
    print "  Cores utilized: {resource_data.cpu_cores_active} / {resource_data.cpu_cores_total}"
    print ""
    print "Memory Usage:"
    print "  Starting: {resource_data.mem_start_mb:.0f} MB"
    print "  Peak: {resource_data.mem_peak_mb:.0f} MB"
    print "  Growth: {resource_data.mem_peak_mb - resource_data.mem_start_mb:.0f} MB"
    print ""
    print "Disk I/O:"
    print "  Read: {resource_data.disk_read_mb:.0f} MB"
    print "  Write: {resource_data.disk_write_mb:.0f} MB"
    print "  IOPS (avg): {resource_data.disk_iops_avg:.0f}"
    print ""

    -- Identify bottleneck
    if resource_data.cpu_avg > 80:
        print "⚠ CPU-bound: Consider multi-threaded loading or faster hardware"
    if resource_data.mem_peak_mb > resource_data.mem_total_mb * 0.8:
        print "⚠ Memory-bound: Reduce batch size or add RAM"
    if resource_data.disk_iops_avg > resource_data.disk_iops_max * 0.8:
        print "⚠ I/O-bound: Consider SSD upgrade or PostgreSQL with tuned I/O"

    return resource_data
```

Save to `tests/performance/profile_resources.[ext]`.

Ask: "I'll profile system resources during a loading run. This helps us identify whether the bottleneck is CPU, memory, or disk I/O. Ready to run the profiler?"

WAIT for response, then run the profiler.

## Step 8: Database-Specific Tuning

Apply optimizations specific to the user's database choice. SQLite and PostgreSQL have fundamentally different performance characteristics.

> **Agent instruction:** Call `search_docs(query='database tuning', category='configuration', version='current')`
> to get current database-specific tuning guidance. The recommendations below are general —
> always verify against the latest documentation.

### SQLite Tuning

SQLite is excellent for evaluation and small-to-medium workloads but has inherent limitations:

- **Single-writer limitation**: Only one process can write at a time. Multi-threaded loading does NOT help with SQLite — it can actually hurt performance due to lock contention.
- **WAL mode**: Ensure Write-Ahead Logging is enabled for better concurrent read performance.
- **Page size**: Larger page sizes (4096 or 8192) can improve throughput for large records.
- **Cache size**: Increase the SQLite cache size if RAM is available.
- **Synchronous mode**: For benchmarking (not production), `PRAGMA synchronous=NORMAL` can improve write speed at the cost of durability.

Ask: "You're using SQLite. This is great for evaluation, but it has a single-writer limitation that caps loading throughput. For your data volume of [X] records, SQLite should work fine. If you need higher throughput later, we can discuss migrating to PostgreSQL."

**When to recommend PostgreSQL migration**:

- Data volume exceeds 500K records
- Loading throughput requirements exceed what SQLite can deliver
- Multiple concurrent writers are needed
- Production deployment is planned

### PostgreSQL Tuning

PostgreSQL supports much higher throughput but requires tuning:

- **shared_buffers**: Set to 25% of available RAM (e.g., 4GB for a 16GB machine)
- **effective_cache_size**: Set to 75% of available RAM
- **work_mem**: Increase for complex queries (e.g., 256MB)
- **maintenance_work_mem**: Increase for index operations (e.g., 512MB)
- **wal_buffers**: Increase to 64MB for write-heavy workloads
- **max_connections**: Set based on concurrent loader count + query connections
- **checkpoint_completion_target**: Set to 0.9 for smoother I/O
- **random_page_cost**: Set to 1.1 for SSD storage (default 4.0 is for spinning disks)

> **Agent instruction:** These are general PostgreSQL tuning parameters. Always verify against
> `search_docs(query='PostgreSQL configuration', category='configuration', version='current')`
> for Senzing-specific recommendations. The Senzing engine may have specific requirements
> for connection pooling and transaction isolation.

Ask: "You're using PostgreSQL. Let me check the current tuning recommendations for your hardware profile. What are your PostgreSQL server specs (RAM, CPU cores, disk type)?"

WAIT for response, then provide specific tuning recommendations.

Document database tuning in `docs/database_tuning.md`:

```markdown
# Database Tuning

**Database**: [SQLite / PostgreSQL version]
**Date**: [Current date]

## Current Configuration
[List current settings]

## Applied Optimizations
| Parameter              | Before    | After     | Reason                    |
|------------------------|-----------|-----------|---------------------------|
| [parameter]            | [value]   | [value]   | [reason]                  |

## Performance Impact
| Metric                 | Before    | After     | Improvement               |
|------------------------|-----------|-----------|---------------------------|
| Loading throughput     | [X] rec/s | [X] rec/s | [X]% improvement          |
| Query latency (p95)    | [X] ms    | [X] ms    | [X]% improvement          |
```

## Step 9: Scalability Testing

Test how performance changes as data volume increases. This is critical for production planning.

> **Agent instruction:** Call `search_docs(query='performance benchmarks', version='current')` to get
> official scalability guidance. Different data volumes trigger different engine behaviors —
> entity resolution complexity grows as more potential matches exist.

### Small-Scale Testing (up to 100K records)

Test with progressively larger datasets to establish the performance curve:

```text
function scalability_test(input_file, test_sizes = [1000, 5000, 10000, 50000, 100000]):
    print "=== Scalability Test ==="
    print ""

    results = empty list

    for each size in test_sizes:
        -- Skip sizes larger than available data
        if size > total_records_in(input_file):
            print "Skipping {size} — only {total_records_in(input_file)} records available"
            continue

        print "Testing with {size} records..."

        -- Fresh database for each test
        initialize_fresh_database()
        engine = initialize_senzing_engine(engine_config)

        -- Load records and measure
        record start_time
        loaded = 0
        for each record in read_jsonl(input_file, limit=size):
            engine.add_record(record["DATA_SOURCE"], record["RECORD_ID"], serialize(record))
            loaded = loaded + 1
        record end_time

        load_duration = end_time - start_time
        load_rate = loaded / load_duration

        -- Measure query latency at this data volume
        query_latencies = empty list
        for i in 1 to 50:
            record query_start
            engine.search_by_attributes('{"NAME_FULL": "John Smith"}')
            record query_end
            append (query_end - query_start) * 1000 to query_latencies

        query_p95 = percentile(query_latencies, 95)

        -- Measure entity count
        -- (Use stats or per-entity queries to get entity count)

        engine.destroy()

        print "  Load rate: {load_rate:.0f} rec/sec"
        print "  Query p95: {query_p95:.1f} ms"
        print ""

        append {size, load_duration, load_rate, query_p95} to results

    -- Print scalability summary
    print "=== Scalability Summary ==="
    print "Records   | Load Time (s) | Load Rate (rec/s) | Query p95 (ms)"
    print "----------|--------------|-------------------|---------------"
    for each result in results:
        print "{result.size:>9} | {result.load_duration:>12.1f} | {result.load_rate:>17.0f} | {result.query_p95:>13.1f}"

    -- Analyze scaling behavior
    if results has at least 2 entries:
        first_rate = results[0].load_rate
        last_rate = results[last].load_rate
        degradation = (first_rate - last_rate) / first_rate * 100
        print ""
        if degradation < 10:
            print "✓ Near-linear scaling — throughput degradation is only {degradation:.1f}%"
        else if degradation < 30:
            print "⚠ Moderate scaling — throughput degraded {degradation:.1f}% at larger volumes"
        else:
            print "⚠ Significant scaling concern — throughput degraded {degradation:.1f}%"
            print "  Consider: PostgreSQL, multi-threading, or hardware upgrades"

    return results
```

Save to `tests/performance/bench_scalability.[ext]`.

### Large-Scale Testing (>1M records)

For datasets exceeding 1 million records, additional considerations apply:

Ask: "Your data volume is [X] records. Do you want to test scalability beyond your current volume to plan for growth? For large-scale testing (>1M records), we'll need to consider some additional factors."

WAIT for response.

If the user wants large-scale testing:

1. **Database requirement**: SQLite is not recommended for >500K records. If the user is on SQLite, discuss PostgreSQL migration before large-scale testing.

2. **Data generation**: If the user doesn't have enough real data, discuss options:
   - Duplicate existing data with synthetic variations
   - Use CORD sample datasets from `get_sample_data` for additional volume
   - Generate synthetic records that match the user's data profile

3. **Multi-threaded loading**: For large volumes, single-threaded loading is too slow.

   > **Agent instruction:** Call `find_examples(query='performance testing')` and
   > `find_examples(query='multi-threaded loading')` to find real-world patterns for
   > high-throughput loading from indexed Senzing GitHub repositories.

   ```text
   function benchmark_multithreaded_loading(input_file, thread_counts = [1, 2, 4, 8]):
       print "=== Multi-Threaded Loading Benchmark ==="
       print "NOTE: Multi-threading only benefits PostgreSQL. SQLite is single-writer."
       print ""

       results = empty list

       for each thread_count in thread_counts:
           initialize_fresh_database()

           -- Split input records into chunks for each thread
           all_records = read_jsonl(input_file)
           chunks = split_into_n_chunks(all_records, thread_count)

           -- Each thread gets its own engine instance
           record start_time
           threads = empty list
           for each chunk in chunks:
               thread = start_thread(load_chunk, chunk)
               append thread to threads

           -- Wait for all threads to complete
           for each thread in threads:
               thread.join()
           record end_time

           duration = end_time - start_time
           rate = length(all_records) / duration

           print "Threads: {thread_count}"
           print "  Duration: {duration:.1f} seconds"
           print "  Throughput: {rate:.0f} records/sec"
           print "  Per-thread rate: {rate / thread_count:.0f} records/sec/thread"
           print ""

           append {thread_count, duration, rate} to results

       -- Identify optimal thread count
       best = result with highest rate in results
       print "Optimal thread count: {best.thread_count} ({best.rate:.0f} rec/sec)"

       return results
   ```

4. **Redo processing**: At large scale, redo records become significant. Redo records are re-evaluations that Senzing queues when new data affects existing entity resolution decisions.

   > **Agent instruction:** Call `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')`
   > to get the current redo processing pattern. Redo processing is critical for large-scale
   > accuracy — skipping it means some entity resolution decisions may be stale.

   ```text
   function benchmark_with_redo(input_file, sample_size = 50000):
       print "=== Loading + Redo Processing Benchmark ==="

       initialize_fresh_database()
       engine = initialize_senzing_engine(engine_config)

       -- Phase 1: Load records
       record load_start
       for each record in read_jsonl(input_file, limit=sample_size):
           engine.add_record(record["DATA_SOURCE"], record["RECORD_ID"], serialize(record))
       record load_end
       load_duration = load_end - load_start

       -- Phase 2: Process redo records
       record redo_start
       redo_count = 0
       while engine.count_redo_records() > 0:
           redo_record = engine.get_redo_record()
           engine.process_redo_record(redo_record)
           redo_count = redo_count + 1
       record redo_end
       redo_duration = redo_end - redo_start

       total_duration = load_duration + redo_duration

       print "Loading: {load_duration:.1f}s ({sample_size / load_duration:.0f} rec/sec)"
       print "Redo: {redo_duration:.1f}s ({redo_count} redo records processed)"
       print "Total: {total_duration:.1f}s"
       print "Effective rate: {sample_size / total_duration:.0f} rec/sec (including redo)"

       engine.destroy()
   ```

5. **Memory planning**: Large datasets require more memory. As a rough guide:
   - 100K records: 2-4 GB RAM
   - 1M records: 8-16 GB RAM
   - 10M records: 32-64 GB RAM (PostgreSQL recommended)
   - These are estimates — actual usage depends on data complexity and feature count

## Step 10: Evaluate Entity Resolution Quality at Scale

Performance isn't just about speed — resolution quality can change at different data volumes. Use the 4-point ER evaluation framework to assess quality.

> **Agent instruction:** Call `reporting_guide(topic='evaluation', version='current')` to get the
> 4-point ER evaluation framework with evidence requirements. This framework provides a structured
> approach to evaluating entity resolution quality:
>
> 1. Entity count and distribution
> 2. Match quality (precision/recall)
> 3. Data source contribution
> 4. Resolution confidence
>
> Use this framework — not ad-hoc quality checks — to evaluate results at each scale point.

Ask: "Now let's evaluate the quality of entity resolution at your current data volume. I'll use the 4-point evaluation framework to give you a structured assessment. This checks entity counts, match quality, data source contribution, and resolution confidence."

WAIT for response.

### Run the Evaluation

> **Agent instruction:** Call `reporting_guide(topic='reports', language='<chosen_language>', version='current')`
> to get SQL analytics queries for aggregate reporting. These queries provide entity count
> distributions, match statistics, and data source contribution metrics.

```text
function evaluate_resolution_quality():
    print "=== Entity Resolution Quality Evaluation ==="
    print ""

    engine = initialize_senzing_engine(engine_config)

    -- Point 1: Entity count and distribution
    print "1. Entity Count and Distribution"
    -- Enumerate entities and count records per entity
    -- Use SQL analytics queries from reporting_guide
    total_records = count_total_records()
    total_entities = count_total_entities()
    compression_ratio = total_records / total_entities
    print "  Total records: {total_records}"
    print "  Total entities: {total_entities}"
    print "  Compression ratio: {compression_ratio:.2f}x"
    print "  (Higher ratio = more duplicates found)"
    print ""

    -- Point 2: Match quality (sample-based)
    print "2. Match Quality (sample-based review)"
    -- Select a random sample of multi-record entities
    -- Present to user for manual review
    sample_entities = get_random_multi_record_entities(count=10)
    true_positives = 0
    false_positives = 0
    for each entity in sample_entities:
        print "  Entity {entity.id}: {entity.record_count} records"
        for each record in entity.records:
            print "    - {record.data_source}: {record.name_full}"
        -- Ask user to verify
    print ""

    -- Point 3: Data source contribution
    print "3. Data Source Contribution"
    -- Show how each data source contributes to entity resolution
    for each source in data_sources:
        records_in_source = count_records(source)
        entities_with_source = count_entities_containing(source)
        cross_source_matches = count_cross_source_matches(source)
        print "  {source}: {records_in_source} records, {cross_source_matches} cross-source matches"
    print ""

    -- Point 4: Resolution confidence
    print "4. Resolution Confidence"
    -- Analyze match levels across resolved entities
    -- Use MATCH_LEVEL_CODE reference from reporting_guide
    print "  High confidence matches: {high_count} ({high_pct}%)"
    print "  Medium confidence matches: {medium_count} ({medium_pct}%)"
    print "  Low confidence matches: {low_count} ({low_pct}%)"

    engine.destroy()
```

Ask: "Here's the quality evaluation. Let me walk through each point. For Point 2 (match quality), I'll show you some sample entities so you can verify the matches are correct. Ready to review?"

WAIT for response. Walk through the sample entities one at a time, asking the user to confirm whether each match is correct (true positive) or incorrect (false positive).

### Build an Analytical Data Mart (Optional)

For ongoing performance monitoring and quality tracking, consider creating an analytical data mart.

> **Agent instruction:** Call `reporting_guide(topic='data_mart', version='current')` to get the
> analytical schema and incremental update patterns. This provides a structured approach to
> storing and querying entity resolution metrics over time.

Ask: "Would you like to set up an analytical data mart for ongoing performance and quality monitoring? This creates a separate database with pre-computed metrics that's easy to query and visualize."

WAIT for response. If yes, follow the data mart schema from `reporting_guide`.

## Step 11: Identify Bottlenecks and Optimize

Analyze all benchmark results to identify the primary bottleneck and apply targeted optimizations.

```text
function analyze_bottlenecks(transform_results, load_results, query_results, resource_data):
    print "=== Bottleneck Analysis ==="
    print ""

    bottlenecks = empty list

    -- Check transformation throughput
    if transform_results.rate < load_results.rate * 2:
        append "Transformation is close to loading speed — may become bottleneck" to bottlenecks

    -- Check loading throughput vs requirements
    if load_results.rate < required_load_rate:
        deficit = required_load_rate - load_results.rate
        print "⚠ Loading throughput: {load_results.rate} rec/sec (need {required_load_rate})"
        print "  Deficit: {deficit} rec/sec"

        -- Diagnose cause
        if resource_data.cpu_avg > 80:
            append "CPU-bound loading — consider multi-threaded loading (PostgreSQL only)" to bottlenecks
        if resource_data.disk_iops_avg > resource_data.disk_iops_max * 0.7:
            append "I/O-bound loading — consider SSD or PostgreSQL WAL tuning" to bottlenecks
        if resource_data.mem_peak_mb > resource_data.mem_total_mb * 0.8:
            append "Memory-bound — reduce batch size or add RAM" to bottlenecks

    -- Check query latency vs requirements
    if query_results.search_p95 > required_search_latency:
        append "Search latency exceeds requirements" to bottlenecks
    if query_results.get_entity_p95 > required_entity_latency:
        append "Entity retrieval latency exceeds requirements" to bottlenecks

    -- Print recommendations
    print ""
    print "Identified Bottlenecks:"
    for each bottleneck in bottlenecks:
        print "  ⚠ {bottleneck}"

    print ""
    print "Recommended Optimizations:"
    -- Generate specific recommendations based on bottlenecks
    for each bottleneck in bottlenecks:
        print "  → {recommendation_for(bottleneck)}"
```

### Common Optimizations

Present relevant optimizations based on the bottleneck analysis:

**Loading throughput optimizations**:

- Switch from SQLite to PostgreSQL for >500K records
- Use multi-threaded loading (PostgreSQL only — SQLite is single-writer)
- Optimize transformation to reduce record size (remove unnecessary fields)
- Increase available RAM for engine caching
- Use SSD storage for database files
- Process redo records in parallel with loading (advanced)

**Query latency optimizations**:

- Ensure database indexes are current
- Increase engine cache size
- Use connection pooling for concurrent queries
- Optimize query patterns (search by multiple attributes for faster narrowing)
- Consider read replicas for PostgreSQL (advanced)

**Resource optimizations**:

- CPU-bound: Add cores, use multi-threading
- Memory-bound: Increase RAM, reduce batch size, stream data
- I/O-bound: Use SSD, tune database I/O parameters, increase WAL buffers
- Network-bound (remote database): Move database closer, use connection pooling

Ask: "Based on the bottleneck analysis, here are the recommended optimizations. Which ones would you like to apply? We'll re-run benchmarks after each change to measure the impact."

WAIT for response.

## Step 12: Apply Optimizations and Re-Benchmark

For each optimization the user wants to apply:

1. **Document the current baseline** (from Steps 4-7)
2. **Apply the optimization** (code change, configuration change, or infrastructure change)
3. **Re-run the relevant benchmark** (loading, query, or resource profiling)
4. **Compare before/after results**
5. **Document the improvement**

```text
function optimization_cycle(optimization_name, benchmark_function):
    print "=== Optimization: {optimization_name} ==="

    -- Record baseline
    print "Baseline (before optimization):"
    baseline = benchmark_function()

    -- Apply optimization
    print ""
    print "Applying optimization: {optimization_name}..."
    apply_optimization()

    -- Re-benchmark
    print ""
    print "After optimization:"
    optimized = benchmark_function()

    -- Compare
    improvement = (optimized.rate - baseline.rate) / baseline.rate * 100
    print ""
    print "Result: {improvement:+.1f}% change"
    if improvement > 0:
        print "✓ Improvement confirmed"
    else:
        print "⚠ No improvement — consider reverting"

    return {optimization_name, baseline, optimized, improvement}
```

Repeat the optimization cycle until performance requirements are met or all viable optimizations have been applied.

## Step 13: Create Performance Report

Compile all benchmark results, optimizations, and recommendations into a comprehensive report.

Document in `docs/performance_report.md`:

```markdown
# Performance Report

**Date**: [Current date]
**Project**: [Project name]
**Environment**: See docs/benchmark_environment.md

## Executive Summary
[One paragraph: key findings, whether requirements are met, top recommendation]

### ## Performance Requirements vs Actuals

| Metric                  | Target          | Actual          | Status |
|-------------------------|-----------------|-----------------|--------|
| Loading throughput      | [X] rec/sec     | [X] rec/sec     | ✅/⚠  |
| Search latency (p95)    | [X] ms          | [X] ms          | ✅/⚠  |
| Entity retrieval (p95)  | [X] ms          | [X] ms          | ✅/⚠  |
| Concurrent users        | [X]             | [Tested]        | ✅/⚠  |
| Max data volume         | [X] records     | [Tested to X]   | ✅/⚠  |

## Transformation Benchmark
- Rate: [X] records/sec
- Bottleneck: [If any]
- Notes: [Transformation is rarely the bottleneck]

## Loading Benchmark
- Single-threaded rate: [X] records/sec
- Multi-threaded rate: [X] records/sec ([N] threads)
- Optimal thread count: [N]
- Redo processing overhead: [X]%
- Database: [SQLite / PostgreSQL]

## Query Benchmark
| Query Type             | p50 (ms) | p95 (ms) | p99 (ms) |
|------------------------|----------|----------|----------|
| Search by name         | [X]      | [X]      | [X]      |
| Search by name+address | [X]      | [X]      | [X]      |
| Get entity by ID       | [X]      | [X]      | [X]      |
| Get entity by record   | [X]      | [X]      | [X]      |
| Why entity             | [X]      | [X]      | [X]      |
| How entity             | [X]      | [X]      | [X]      |

## Scalability Analysis
| Records   | Load Rate (rec/s) | Query p95 (ms) | Notes              |
|-----------|-------------------|----------------|--------------------|
| 1,000     | [X]               | [X]            |                    |
| 10,000    | [X]               | [X]            |                    |
| 100,000   | [X]               | [X]            |                    |
| 1,000,000 | [X]               | [X]            | [If tested]        |

## Resource Profile
- CPU: [avg]% average, [peak]% peak
- Memory: [start] MB → [peak] MB (growth: [X] MB)
- Disk I/O: [read] MB read, [write] MB write
- Primary bottleneck: [CPU / Memory / I/O / None]

## Database Tuning Applied
| Parameter              | Before    | After     | Impact              |
|------------------------|-----------|-----------|---------------------|
| [parameter]            | [value]   | [value]   | [measured impact]   |

## Optimizations Applied
| Optimization           | Before (rec/s) | After (rec/s) | Improvement |
|------------------------|-----------------|---------------|-------------|
| [optimization]         | [X]             | [X]           | [X]%        |

## Entity Resolution Quality
- Total records: [X]
- Total entities: [X]
- Compression ratio: [X]x
- High confidence matches: [X]%
- Cross-source match rate: [X]%

## Recommendations
1. [Top recommendation with justification]
2. [Second recommendation]
3. [Third recommendation]

## Production Readiness
- [ ] Performance requirements met
- [ ] Scalability tested to [X]x current volume
- [ ] Database tuned for production
- [ ] Resource requirements documented
- [ ] Monitoring plan defined (see Module 11)
```

## Validation Gates

Before marking Module 9 as complete, verify ALL of the following:

### Required Gates (must pass)

- ✅ Performance requirements documented in `docs/performance_requirements.md`
- ✅ Benchmark environment documented in `docs/benchmark_environment.md`
- ✅ Transformation benchmark completed and results recorded
- ✅ Loading benchmark completed with at least 2 sample sizes
- ✅ Query benchmark completed for all query types from Module 8
- ✅ Resource profiling completed (CPU, memory, disk I/O measured)
- ✅ Database-specific tuning reviewed and applied where appropriate
- ✅ Scalability tested with at least 3 different data volumes
- ✅ Entity resolution quality evaluated using the 4-point framework
- ✅ Bottleneck analysis completed with specific recommendations
- ✅ Performance report created in `docs/performance_report.md`
- ✅ All benchmark scripts saved in `tests/performance/`

### Conditional Gates

- ✅ If requirements not met: optimization plan documented with specific steps
- ✅ If using SQLite with >500K records: PostgreSQL migration discussed
- ✅ If multi-threaded loading tested: optimal thread count identified
- ✅ If redo processing significant: redo benchmark included in report

### Quality Gates

- ✅ Benchmarks used warm-up runs (results are not skewed by cold starts)
- ✅ Multiple iterations used for statistical significance (minimum 3 for loading, 50+ for queries)
- ✅ Results are reproducible (environment documented, scripts saved)

## Troubleshooting

### Loading is slower than expected

- **Check database type**: SQLite caps at ~500-1500 rec/sec single-threaded. PostgreSQL can achieve much higher throughput with multi-threading.
- **Check disk type**: HDD is significantly slower than SSD for database writes. Verify with `resource_data.disk_iops_avg`.
- **Check record complexity**: Records with many features (names, addresses, phones, IDs) take longer to resolve than simple records.
- **Check for redo backlog**: A large redo queue means the engine is deferring resolution work. Process redo records to get accurate throughput numbers.
- **Check memory**: If the system is swapping to disk, performance drops dramatically. Monitor with resource profiler.

### Query latency is too high

- **Check entity size**: Entities with hundreds of records are slower to retrieve than entities with 2-3 records. This is expected.
- **Check database indexes**: Ensure indexes are up to date. For PostgreSQL, run `ANALYZE` after loading.
- **Check concurrent load**: If loading and querying simultaneously, loading takes priority and queries slow down.
- **Check cache**: First queries after engine startup are slower (cold cache). Warm-up runs are essential for accurate benchmarks.

### Scalability degrades rapidly

- **Expected behavior**: Some throughput degradation at larger volumes is normal because entity resolution complexity increases as more potential matches exist.
- **Linear degradation (<20%)**: Normal and acceptable for most use cases.
- **Significant degradation (>30%)**: May indicate database tuning issues, insufficient memory, or data quality problems (too many ambiguous matches).
- **Sudden cliff**: Usually indicates resource exhaustion (out of memory, disk full, connection pool exhausted).

### Multi-threaded loading doesn't help

- **SQLite**: Multi-threading does NOT help with SQLite. It's single-writer by design. Use PostgreSQL for multi-threaded loading.
- **Thread contention**: Too many threads can cause contention. Test with 2, 4, 8 threads and find the sweet spot.
- **I/O bottleneck**: If disk I/O is saturated, more threads won't help. Upgrade to SSD or tune database I/O.

### Redo processing takes too long

- **Normal behavior**: Redo records are re-evaluations triggered by new data. At large scale, redo can be 10-30% of loading time.
- **Excessive redo**: If redo count exceeds 50% of loaded records, data quality may be causing excessive re-evaluation. Review data for ambiguous names or addresses.
- **Process in parallel**: Redo can be processed by a separate thread/process while loading continues.

### Out of memory during benchmarking

- **Reduce batch size**: Load fewer records at a time.
- **Stream data**: Don't load all records into memory at once. Read from file line by line.
- **Increase RAM**: Senzing engine caches entity data in memory. Larger datasets need more RAM.
- **Check for memory leaks**: Ensure engine instances are properly destroyed after each benchmark run.

### Results differ between benchmark runs

- **Warm-up**: Always include warm-up runs. First runs are slower due to cold caches.
- **Background processes**: Ensure no other heavy processes are running during benchmarks.
- **Database state**: Use a fresh database for each benchmark run to ensure consistency.
- **System load**: Check for OS-level background tasks (updates, backups, indexing).

## Transition

Once Module 9 is complete, proceed to:

- **Module 10** (Security Hardening) — implement production-grade security measures including secrets management, authentication, authorization, encryption, and audit logging. Performance baselines from this module inform security overhead calculations.

Inform the user:

"Module 9 is complete. You now have a comprehensive performance profile of your entity resolution pipeline.

### Module 9 Complete ✅

- ✅ Performance requirements defined
- ✅ Transformation, loading, and query benchmarks completed
- ✅ Resource usage profiled
- ✅ Database tuning applied
- ✅ Scalability tested
- ✅ Entity resolution quality evaluated
- ✅ Bottlenecks identified and optimized
- ✅ Performance report documented

**Key Results**:

- Loading: [X] records/sec
- Query p95: [X] ms
- Scalability: [Linear/Moderate/Needs attention] up to [X] records

**What's Next**: Module 10 focuses on security hardening — secrets management, authentication, encryption, and audit logging. The performance baselines we established here will help us measure any security overhead.

Ready to move to Module 10?"

## Agent Behavior

- **Always use MCP tools for current information**: Never rely on training data for performance numbers, database tuning parameters, or SDK patterns. Call `search_docs`, `generate_scaffold`, `reporting_guide`, and `find_examples` for current guidance.
- **Ask and WAIT**: Every question in this module requires a user response before proceeding. Do not assume answers or skip ahead.
- **Use `<chosen_language>` consistently**: All benchmark scripts, scaffold calls, and code examples must use the bootcamper's chosen programming language. Never default to Python unless that is the chosen language.
- **Fresh databases for benchmarks**: Each benchmark run should start with a clean database to ensure reproducible results. Document the setup/teardown process.
- **Statistical rigor**: Use warm-up runs, multiple iterations, and percentile reporting (p50, p95, p99) — not just averages. Averages hide tail latency.
- **Don't guess performance numbers**: Use `search_docs(query='performance benchmarks', version='current')` for official expectations. Performance varies dramatically by hardware, database, and data complexity.
- **Check anti-patterns first**: Before recommending any optimization, call `search_docs(query='loading performance', category='anti_patterns', version='current')` to avoid known pitfalls.
- **Database-aware recommendations**: SQLite and PostgreSQL have fundamentally different performance characteristics. Never recommend multi-threaded loading for SQLite. Always check the user's database choice before making recommendations.
- **Iterative optimization**: Apply one optimization at a time and re-benchmark after each change. This isolates the impact of each change and prevents regressions.
- **Save all scripts**: Every benchmark script must be saved in `tests/performance/` with clear naming. These scripts are reusable for regression testing and CI/CD integration.
- **Connect to business requirements**: Always relate benchmark numbers back to the performance requirements defined in Step 1. Raw numbers without context are not useful.
- **Use the 4-point evaluation framework**: Call `reporting_guide(topic='evaluation', version='current')` for structured quality evaluation — not ad-hoc checks.
- **Use SQL analytics for reporting**: Call `reporting_guide(topic='reports', language='<chosen_language>', version='current')` for pre-built analytics queries rather than writing custom SQL.
