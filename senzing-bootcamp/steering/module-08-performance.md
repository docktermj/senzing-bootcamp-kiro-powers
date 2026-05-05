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

Call `search_docs(query='performance benchmarks', version='current')` for current expectations. Document in `docs/performance_requirements.md`.

Ask ONE AT A TIME:

### Step 1a: Loading Throughput Target

"What loading throughput do you need? (records per second)"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1a to `config/bootcamp_progress.json`.

### Step 1b: Query Latency Target

"What query latency target do you need? (milliseconds per query)"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1b to `config/bootcamp_progress.json`.

### Step 1c: Concurrent Users

"How many concurrent users or processes will query the system?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1c to `config/bootcamp_progress.json`.

### Step 1d: Data Volume and Growth

"What's your expected data volume and growth rate?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1d to `config/bootcamp_progress.json`.

### Step 1e: Database Choice

"Would you like to use SQLite (simpler, single-file) or PostgreSQL (better for production scale)?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next sub-step. Wait for the bootcamper's real input.

**Checkpoint:** Write step 1e to `config/bootcamp_progress.json`.

## Step 2: Check Anti-Patterns

Call `search_docs(query='loading performance', category='anti_patterns', version='current')`. Share relevant anti-patterns with user before benchmarking.

**Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

## Hardware Clarification (On-Premises Only)

**Condition:** `deployment_target == "on_premises"` AND `hardware_target` is NOT already stored in `config/bootcamp_preferences.yaml`.

If both conditions are true, ask the following question before proceeding to benchmarking:

👉 "Will you deploy to this machine, or a different on-premises server? If different, what are the specs (CPU cores, RAM, storage type, database server)?"

> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.

**After receiving the answer**, process the response as follows:

### Response: "This machine"

If the bootcamper indicates they will deploy to the current dev machine:

1. Store in `config/bootcamp_preferences.yaml`:

   ```yaml
   hardware_target: "current_machine"
   ```

2. Proceed with the current machine's specs for all benchmarking and recommendations in Steps 3–13.

### Response: Different server with specs provided

If the bootcamper says they will deploy to a different server AND provides hardware details:

1. Store in `config/bootcamp_preferences.yaml`:

   ```yaml
   hardware_target: "different_server"
   production_specs:
     cpu_cores: <provided value>
     ram_gb: <provided value>
     storage_type: "<provided value>"
     database: "<provided value>"
   ```

2. Use the provided `production_specs` when making performance recommendations and sizing guidance in Steps 3–13.
3. When presenting benchmark results, clearly note: "Benchmarks were run on your dev machine; recommendations target your production hardware (`<cpu_cores>` cores, `<ram_gb>` GB RAM, `<storage_type>`, `<database>`)."
4. If benchmark results on the dev machine differ significantly from what the production hardware would achieve, call that out and explain the expected difference.

### Response: Different server but specs unknown or incomplete

If the bootcamper says they will deploy to a different server but does NOT provide specs (or provides only partial specs), ask a follow-up:

👉 "To give you accurate performance recommendations, I need a few details about your production server:

- CPU cores (e.g., 8, 16, 32)?
- RAM in GB (e.g., 32, 64, 128)?
- Storage type (HDD, SATA SSD, NVMe SSD)?
- Database server (PostgreSQL version, or SQLite)?"

> **🛑 STOP — End your response here.** Wait for the bootcamper to provide the missing details before continuing.

Once the missing details are provided, store them as described in the "Different server with specs provided" section above and proceed.

---

If `deployment_target` is NOT "on_premises", or `hardware_target` is already stored, skip this entire Hardware Clarification section.

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

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

## Step 13: Performance Report

Create `docs/performance_report.md` with: requirements vs actuals, benchmark results, bottleneck analysis, optimizations applied, scalability projections, recommendations.

**Offer visualization:** "Would you like me to create a web page showing the performance benchmarks? It'll have throughput charts, latency percentiles, and before/after comparisons." If yes, generate HTML and save to `docs/performance_dashboard.html`.

**Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

**Success:** Performance baselines captured, bottlenecks identified, optimizations documented, report complete.
