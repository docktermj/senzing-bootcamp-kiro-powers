---
inclusion: manual
---

# Module 8 Phase C: Optimization & Reporting (Steps 8–13)

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

**Visualization checkpoint:** Follow the Visualization Protocol.
Load `visualization-protocol.md` and execute the offer for checkpoint `m8_performance_report`.

**Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

**Success:** Performance baselines captured, bottlenecks identified, optimizations documented, report complete.
