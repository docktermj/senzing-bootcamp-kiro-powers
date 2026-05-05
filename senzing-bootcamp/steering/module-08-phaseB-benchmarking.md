---
inclusion: manual
---

# Module 8 Phase B: Benchmarking (Steps 4–7)

## Step 4: Benchmark Transformation

Use `find_examples(query='performance testing')` for patterns. Generate a timed benchmark script that tests transformation throughput at multiple sample sizes (100, 1K, 10K). Save to `tests/performance/bench_transform.[ext]`.

**Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

## Step 5: Benchmark Loading (Critical)

Call `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` for the loading pattern. If the generated scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths. Build a benchmark that measures records/sec at multiple sample sizes with fresh DB each run. Save to `tests/performance/bench_load.[ext]`.

**Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

## Step 6: Benchmark Query Latency

Benchmark all query patterns from Module 7 (Query and Visualize): search by name, search by name+address, get entity by ID, get entity by record, why entity, how entity. Measure p50/p95/p99 over 100 iterations with warm-up. Save to `tests/performance/bench_query.[ext]`.

**Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

## Step 7: Profile Resources

Monitor CPU, memory, disk I/O during a loading run. Identify bottleneck: CPU-bound → multi-thread or faster hardware. Memory-bound → reduce batch size or add RAM. I/O-bound → SSD or PostgreSQL tuning. Save to `tests/performance/profile_resources.[ext]`.

**Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.
