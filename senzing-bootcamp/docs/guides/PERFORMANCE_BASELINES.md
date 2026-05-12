# Performance Baselines Guide

## Overview

This guide provides reference performance baselines for Senzing entity resolution workloads at different data volumes. Use these baselines to estimate time, resources, and database choices before running your own benchmarks in Module 9.

## Important Disclaimers

- All numbers are approximate ranges based on typical hardware and configurations
- Actual performance varies by hardware, Senzing version, data complexity, transformation logic, and entity resolution difficulty
- Use MCP `search_docs(query="performance benchmarks", version="current")` for the most current official benchmarks
- These baselines assume single-threaded operation unless noted otherwise
- Run your own benchmarks in Module 9 to establish baselines specific to your environment

## Data Volume Tiers

| Tier   | Record Count | Typical Use Case                        |
|--------|-------------|-----------------------------------------|
| Small  | <1K         | Bootcamp demos, learning, quick tests   |
| Medium | 1K - 100K   | Pilot projects, POCs, department-level   |
| Large  | 100K+       | Production workloads, enterprise-scale   |

## Transformation Throughput Baselines

Transformation converts raw source data (CSV, JSON, XML) into Senzing-compatible JSON records. This is typically CPU-bound and I/O-bound on the source file.

| Data Volume Tier | Record Count | Expected Throughput       | Estimated Wall-Clock Time |
|------------------|-------------|---------------------------|---------------------------|
| Small            | <1K         | 3,000 - 10,000 rec/sec   | < 1 second                |
| Medium           | 1K - 100K   | 2,500 - 8,000 rec/sec    | 1 second - 40 seconds     |
| Large            | 100K+       | 2,000 - 6,000 rec/sec    | 17 seconds - minutes      |

**Factors that affect transformation throughput:**

- Data complexity (number of fields, nested structures)
- Transformation logic (simple mapping vs complex parsing/normalization)
- Source file format (CSV is faster than XML)
- Disk I/O speed (SSD vs HDD)

## Loading Throughput Baselines

Loading sends transformed records to the Senzing engine for entity resolution. This is the most resource-intensive operation — performance depends heavily on database backend, hardware, and entity resolution complexity.

### SQLite Loading

| Data Volume Tier | Record Count | Expected Throughput      | Estimated Wall-Clock Time |
|------------------|-------------|--------------------------|---------------------------|
| Small            | <1K         | 100 - 300 rec/sec        | 3 - 10 seconds            |
| Medium           | 1K - 100K   | 80 - 250 rec/sec         | 4 seconds - 20 minutes    |
| Large            | 100K+       | 50 - 150 rec/sec         | 11 minutes - hours        |

SQLite is single-writer, so throughput degrades as the database grows. Multi-threading does not help with SQLite.

### PostgreSQL Loading

| Data Volume Tier | Record Count | Expected Throughput      | Estimated Wall-Clock Time  |
|------------------|-------------|--------------------------|----------------------------|
| Small            | <1K         | 150 - 500 rec/sec        | 2 - 7 seconds              |
| Medium           | 1K - 100K   | 120 - 400 rec/sec        | 3 seconds - 14 minutes     |
| Large            | 100K+       | 100 - 800 rec/sec        | 2 minutes - hours          |

PostgreSQL supports concurrent writes and multi-threaded loading, so throughput at the large tier can scale significantly with additional threads and tuned configuration.

**Factors that affect loading throughput:**

- Database backend (PostgreSQL scales better than SQLite)
- Entity resolution complexity (more features per record = slower)
- Data overlap (high match rates increase processing per record)
- Hardware (CPU cores, RAM, disk speed)
- Number of loading threads (PostgreSQL only)

## Query Response Time Baselines

Query performance depends on database size, query type, database backend, and whether the database cache is warm.

### SQLite Query Response Times

| Query Type              | Small (<1K) Avg / P95 | Medium (1K-100K) Avg / P95 | Large (100K+) Avg / P95   |
|-------------------------|------------------------|-----------------------------|---------------------------|
| Search by attributes    | 5 - 15 ms / 25 ms     | 15 - 50 ms / 80 ms         | 50 - 200 ms / 400 ms     |
| Get entity by ID        | 2 - 8 ms / 15 ms      | 5 - 20 ms / 40 ms          | 15 - 60 ms / 120 ms      |
| Get entity by record    | 2 - 10 ms / 18 ms     | 8 - 25 ms / 50 ms          | 20 - 80 ms / 150 ms      |

### PostgreSQL Query Response Times

| Query Type              | Small (<1K) Avg / P95 | Medium (1K-100K) Avg / P95 | Large (100K+) Avg / P95   |
|-------------------------|------------------------|-----------------------------|---------------------------|
| Search by attributes    | 3 - 10 ms / 20 ms     | 10 - 35 ms / 60 ms         | 30 - 120 ms / 250 ms     |
| Get entity by ID        | 1 - 5 ms / 10 ms      | 3 - 12 ms / 25 ms          | 8 - 35 ms / 70 ms        |
| Get entity by record    | 1 - 6 ms / 12 ms      | 5 - 15 ms / 30 ms          | 12 - 50 ms / 100 ms      |

**Factors that affect query response times:**

- Database size (more records = larger index scans)
- Query specificity (more search attributes = faster narrowing)
- Entity complexity (entities with many records take longer to assemble)
- Cache warmth (first queries are slower; repeated queries benefit from caching)
- Database backend tuning (PostgreSQL benefits from shared_buffers and effective_cache_size tuning)

## Hardware Requirements

### Minimum Specifications

| Data Volume Tier | CPU Cores | RAM   | Disk Type | Disk Space | Database       |
|------------------|-----------|-------|-----------|------------|----------------|
| Small (<1K)      | 2         | 4 GB  | HDD/SSD   | 5 GB       | SQLite         |
| Medium (1K-100K) | 4         | 8 GB  | SSD       | 20 GB      | SQLite or PostgreSQL |
| Large (100K+)    | 4         | 16 GB | SSD       | 50 GB+     | PostgreSQL     |

### Recommended Specifications

| Data Volume Tier | CPU Cores | RAM    | Disk Type | Disk Space | Database   |
|------------------|-----------|--------|-----------|------------|------------|
| Small (<1K)      | 2+        | 8 GB   | SSD       | 10 GB      | SQLite     |
| Medium (1K-100K) | 4-8       | 16 GB  | SSD       | 50 GB      | PostgreSQL |
| Large (100K+)    | 8+        | 32 GB+ | NVMe SSD  | 100 GB+    | PostgreSQL |

### Database Suitability by Tier

- **Small (<1K):** SQLite is sufficient. Simple setup, no external dependencies.
- **Medium (1K-100K):** SQLite works for single-user scenarios. PostgreSQL recommended for better throughput and concurrent access.
- **Large (100K+):** PostgreSQL required. SQLite single-writer limitation becomes a significant bottleneck at this scale.

## SQLite vs PostgreSQL Comparison

### Feature Comparison

| Dimension            | SQLite                              | PostgreSQL                                |
|----------------------|-------------------------------------|-------------------------------------------|
| Setup complexity     | None (file-based, built-in)         | Requires installation and configuration   |
| Loading throughput   | 50 - 300 rec/sec                    | 100 - 800+ rec/sec                        |
| Concurrent writes    | Single writer only                  | Multiple concurrent writers               |
| Multi-threaded load  | No benefit (single-writer lock)     | Near-linear scaling with threads          |
| Query performance    | Good for small/medium datasets      | Better at all scales, especially large    |
| Max practical size   | ~500K records                       | Millions of records                       |
| Disk usage           | Compact                             | Larger (indexes, WAL, overhead)           |
| Backup complexity    | Copy the file                       | pg_dump or streaming replication          |
| Best for             | Learning, demos, small pilots       | POCs, production, any concurrent access   |

### When to Migrate from SQLite to PostgreSQL

Migrate to PostgreSQL when any of these conditions apply:

- **Data volume exceeds 100K records** — SQLite throughput degrades significantly
- **Loading throughput is insufficient** — SQLite single-writer limitation caps throughput
- **Concurrent access is needed** — Multiple users or processes accessing the database
- **Multi-threaded loading is required** — Only PostgreSQL benefits from parallel loading
- **Production deployment** — PostgreSQL provides the reliability and scalability needed for production

### Migration Timing

- **Before Module 9** is ideal — benchmark both backends and compare
- **During Module 9** if SQLite benchmarks show insufficient throughput
- **Before Module 11 (Deployment)** at the latest — production should use PostgreSQL

Use `search_docs(query="database migration", category="configuration", version="current")` for migration guidance.

## Scaling Recommendations

### Multi-Threading (PostgreSQL Only)

Multi-threaded loading can significantly improve throughput with PostgreSQL:

| Threads | Expected Throughput Multiplier | Notes                                    |
|---------|-------------------------------|------------------------------------------|
| 1       | 1x (baseline)                 | Single-threaded baseline                 |
| 2       | 1.5x - 1.8x                  | Good improvement with minimal complexity |
| 4       | 2.5x - 3.5x                  | Sweet spot for most hardware             |
| 8       | 3.5x - 6x                    | Requires 8+ CPU cores and sufficient RAM |
| 16+     | 5x - 10x                     | Diminishing returns; tune carefully      |

Use `find_examples(query="multi-threaded loading")` for implementation patterns.

SQLite does not benefit from multi-threading due to its single-writer architecture.

### Database Tuning Parameters

#### SQLite Tuning (Small/Medium Tiers)

- **WAL mode:** Enable Write-Ahead Logging for better read concurrency
- **Page size:** 4096 bytes (default is usually fine)
- **Cache size:** Increase to 10,000 - 50,000 pages for medium datasets

```python
import sqlite3

conn = sqlite3.connect('database/G2C.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.execute('PRAGMA cache_size=-64000')  # 64MB cache
conn.execute('PRAGMA temp_store=MEMORY')
conn.execute('PRAGMA mmap_size=268435456')  # 256MB memory-mapped I/O
```

#### PostgreSQL Tuning (Medium/Large Tiers)

| Parameter                    | Recommended Value        | Purpose                          |
|------------------------------|--------------------------|----------------------------------|
| shared_buffers               | 25% of total RAM         | Database cache                   |
| effective_cache_size         | 75% of total RAM         | Query planner hint               |
| work_mem                     | 256 MB - 1 GB            | Per-operation sort/hash memory   |
| wal_buffers                  | 64 MB                    | WAL write buffer                 |
| checkpoint_completion_target | 0.9                      | Spread checkpoint I/O            |
| random_page_cost             | 1.1 (SSD) / 4.0 (HDD)   | Query planner disk cost estimate |
| max_connections              | 100 - 200                | Match thread count + overhead    |

```sql
-- postgresql.conf recommended settings for Senzing
shared_buffers = 4GB          -- 25% of RAM (adjust for your system)
effective_cache_size = 12GB   -- 75% of RAM
work_mem = 256MB
wal_buffers = 64MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
random_page_cost = 1.1        -- Use 4.0 for HDD
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

Use `search_docs(query="database tuning", category="configuration", version="current")` for version-specific tuning guidance.

### Redo Processing for Large-Scale Loads

When loading large datasets (100K+ records), redo processing is essential:

- **What:** After initial loading, Senzing queues re-evaluations as new relationships are discovered. These "redo records" must be processed to finalize entity resolution.
- **When:** Process redo records after the initial load completes, or periodically during very large loads.
- **Impact:** Redo processing can take 20-50% of the initial load time depending on data overlap and match complexity.
- **Recommendation:** For datasets over 100K records, include redo processing time in your total load time estimates.

Use `generate_scaffold(workflow="redo")` for redo processing implementation patterns.

### Scaling Summary by Tier

| Tier   | Key Scaling Actions                                                        |
|--------|----------------------------------------------------------------------------|
| Small  | No special tuning needed. SQLite with defaults is sufficient.              |
| Medium | Consider PostgreSQL. Enable SQLite WAL mode if staying with SQLite.        |
| Large  | Require PostgreSQL. Use multi-threaded loading. Tune database parameters. Plan for redo processing. |

## Profiling and Monitoring

Before optimizing, profile to identify the actual bottleneck. Senzing native SDK calls typically dominate runtime — optimize those first.

### Common Bottleneck Patterns

| Bottleneck | Symptoms | Resolution |
|------------|----------|------------|
| CPU-bound | High CPU usage (>80%), low disk I/O | Optimize per-record processing, reduce batch overhead |
| I/O-bound | Low CPU, high disk I/O or wait times | Increase batch size, use SSD/NVMe, optimize database |
| Memory-bound | High memory usage, swapping | Use generators/streaming, process in smaller batches, increase RAM |
| Network-bound | High network latency between app and database | Co-locate services, use connection pooling, batch operations |

### Language-Specific Profiling Tools

| Language | Profiling Tool | Command |
|----------|---------------|---------|
| Python | cProfile | `python -m cProfile -o profile.stats load_data.py` |
| Python | memory_profiler | `python -m memory_profiler load_data.py` |
| Java | async-profiler | Attach to running JVM |
| Java | jvisualvm | `jvisualvm` (included with JDK) |
| C# | dotnet-trace | `dotnet-trace collect --process-id <PID>` |
| Rust | cargo flamegraph | `cargo flamegraph` |
| TypeScript | clinic.js | `npx clinic doctor -- node src/loader.js` |

## Related Documentation

- [Module 8: Performance Testing](../modules/MODULE_8_PERFORMANCE_TESTING.md) — Hands-on benchmarking workflow
- [After the Bootcamp](AFTER_BOOTCAMP.md) — Production maintenance and scaling guidance
- `steering/module-08-performance.md` — Agent workflow for Module 8
- [Quality Scoring Methodology](QUALITY_SCORING_METHODOLOGY.md) — How data quality scores are calculated
- [Common Mistakes](COMMON_MISTAKES.md) — Common performance mistakes and how to avoid them

### MCP Resources

- `search_docs(query="performance benchmarks", version="current")` — Latest official benchmarks
- `search_docs(query="database tuning", category="configuration", version="current")` — Database tuning guidance
- `find_examples(query="multi-threaded loading")` — Multi-threaded loading patterns
- `generate_scaffold(workflow="redo")` — Redo processing implementation

---

**Last Updated:** 2026-04-17
**Version:** 1.0.0
