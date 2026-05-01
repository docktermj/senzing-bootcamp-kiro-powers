---
inclusion: manual
---

# Module 8: Performance Testing

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** See `docs/modules/MODULE_8_PERFORMANCE_TESTING.md` for background.

Use the bootcamper's chosen language. Read `cloud_provider` from `config/bootcamp_preferences.yaml` — if AWS, tailor to RDS/Aurora and EC2 instance types. Also read `deployment_target` from `config/bootcamp_preferences.yaml`. When `deployment_target` is set but `cloud_provider` is not (e.g., container platform or local target), use the deployment target to inform performance target guidance — container platform targets (Kubernetes, Docker Swarm) differ from bare-metal or local targets in resource constraints, networking overhead, and scaling characteristics.

**Prerequisites:** Module 7 (Query and Visualize) complete, representative data loaded, cloud provider set at 7→8 gate.

**Before/After:** Entity resolution works but you don't know how it performs at scale. After this module, you'll have benchmarks, bottleneck analysis, and optimizations — confidence that it'll handle production volumes.

## Step 1: Define Performance Requirements

**Before setting targets**, direct the user to review `docs/guides/PERFORMANCE_BASELINES.md` for reference throughput, hardware requirements, and database comparison data at different data volumes. This helps them set realistic targets.

Ask ONE AT A TIME: loading throughput target, query latency target, concurrent users, data volume/growth, database choice (SQLite vs PostgreSQL).

Call `search_docs(query='performance benchmarks', version='current')` for current expectations. Document in `docs/performance_requirements.md`.

**Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

## Step 2: Check Anti-Patterns

Call `search_docs(query='loading performance', category='anti_patterns', version='current')`. Share relevant anti-patterns with user before benchmarking.

**Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

## Step 3: Baseline Environment

Capture system info (CPU, RAM, disk, OS, SDK version, DB version). Back up current database. Save to `docs/benchmark_environment.md`.

**Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

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

## Step 8: Database Tuning

Call `search_docs(query='database tuning', category='configuration', version='current')`.

- **SQLite:** Single-writer limitation, WAL mode, page size, cache size. Recommend PostgreSQL migration if >500K records or throughput insufficient.
- **PostgreSQL:** shared_buffers (25% RAM), effective_cache_size (75% RAM), work_mem, wal_buffers, checkpoint_completion_target, random_page_cost for SSD.

Document in `docs/database_tuning.md`.

**Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

## Step 9: Scalability Testing

Test with progressively larger datasets (1K → 5K → 10K → 50K → 100K). Measure throughput degradation curve. For >1M records: require PostgreSQL, test multi-threaded loading with `find_examples(query='multi-threaded loading')`, include redo processing via `generate_scaffold(workflow='redo')`. If the generated redo scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths.

**Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

## Step 10: Evaluate ER Quality at Scale

Use the 4-point framework — call `reporting_guide(topic='quality_metrics')`:

1. Precision: are matched records truly the same entity?
2. Recall: are all true matches found?
3. Over-linking: are unrelated records incorrectly merged?
4. Under-linking: are related records missed?

Sample 50-100 entities for manual review. Document in `docs/er_quality_evaluation.md`.

**Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

## Step 11: Identify Bottlenecks

Compare benchmarks against Step 1 requirements. Common optimizations: multi-threading (PostgreSQL only), batch size tuning, database parameter tuning, hardware upgrades, redo processing.

**Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

## Step 12: Apply Optimizations and Re-Benchmark

Apply one optimization at a time. Re-run the relevant benchmark after each change. Document before/after in `docs/optimization_results.md`.

**Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

## Step 13: Performance Report

Create `docs/performance_report.md` with: requirements vs actuals, benchmark results, bottleneck analysis, optimizations applied, scalability projections, recommendations.

**Offer visualization:** "Would you like me to create a web page showing the performance benchmarks? It'll have throughput charts, latency percentiles, and before/after comparisons." If yes, generate HTML and save to `docs/performance_dashboard.html`.

**Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

**Success:** Performance baselines captured, bottlenecks identified, optimizations documented, report complete.
