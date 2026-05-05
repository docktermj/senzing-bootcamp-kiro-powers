---
inclusion: manual
---
## Phase C: Multi-Source Orchestration (Conditional — 2+ Data Sources)

> **Agent instruction:** Read `config/data_sources.yaml` and count the number of data sources with `mapping_status: complete`. If there is only ONE data source, skip Phase C entirely and proceed to Phase D (Validation). Only present multi-source orchestration steps when the bootcamper has 2 or more data sources to load.

11. **Inventory all data sources:**

    > **Agent instruction:** Read `config/data_sources.yaml` for `quality_score`, `mapping_status`, and `load_status` per source.

    Enumerate every data source. For each: source name/DATA_SOURCE identifier, record count, quality score, mapping status, loaded status. Present a summary table so the bootcamper can review the data sources and confirm the list is complete.

    **Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

12. **Analyze dependencies:**

    Ask about data source dependencies.

    Common patterns: parent-child (load parents first), reference data first, temporal ordering, or no dependencies. If circular dependency detected, explain that Senzing resolves entities as records arrive — load the higher-quality source first. Save dependency map to `docs/loading_strategy.md`.

    **Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

13. **Determine load order:**

    > **Agent instruction:** Use `quality_score` from `config/data_sources.yaml` to rank sources. Update `load_status` as loading progresses.

    Apply ordering heuristics (priority order): (1) reference before transactional, (2) quality-first for strong entity baseline, (3) attribute-density-first, (4) volume-first when quality is similar.

    Present the recommended load order with reasons for the bootcamper to review.

    **Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

14. **Select loading strategy:**

    Present the loading strategy options: **Sequential** (safer, easier to debug), **Parallel** (faster, more resources), **Hybrid** (sequential for dependent, parallel for independent).

    **Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

15. **Pre-load validation checklist:**

    Verify before orchestration: all JSONL files exist in `data/transformed/` and are non-empty; unique DATA_SOURCE names match Module 2 config; RECORD_IDs unique within each source; database backup exists; sufficient disk space (~2x per source); Module 6 loading program works as template. Fix failures before proceeding.

    **Checkpoint:** Write step 15 to `config/bootcamp_progress.json`.

16. **Create orchestrator program:**

    > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` and `find_examples(query="multi-source")` for patterns.

    **CRITICAL**: Override any `/tmp/` or `ExampleEnvironment` paths to `database/G2C.db`.

    Save to `src/load/orchestrator.[ext]`. Must handle: ordered loading with dependency enforcement, parallel execution if selected, per-source progress/error tracking with error isolation, statistics aggregation, and completion summary.

    **Production orchestration patterns to include:**
    - **Retry with exponential backoff:** When a source fails to load, retry with increasing delays (1s, 2s, 4s, 8s) up to a configurable maximum. Log each retry attempt.
    - **Partial success handling:** If some sources succeed and others fail, mark successful sources as loaded and report failed sources with error details. The orchestrator should not roll back successful loads when one source fails.
    - **Error isolation:** Errors in one source's loading must not affect other sources. Each source loads in its own error boundary.
    - **Orchestrator health monitoring:** Track overall orchestration health — elapsed time, sources completed vs. remaining, error rate across all sources. Log periodic health summaries.

    **Checkpoint:** Write step 16 to `config/bootcamp_progress.json`.

17. **Test orchestrator with sample data:**

    Test orchestrator with 10–100 records per source. Verify: sources load without errors, dependencies respected, progress tracking works, error handling triggers correctly.

    Report the sample data test results and let the bootcamper know the orchestrator is ready for the full dataset.

    **Checkpoint:** Write step 17 to `config/bootcamp_progress.json`.

18. **Run full orchestration:**

    Run on complete dataset. Monitor per-source progress, error rates, overall completion, elapsed/estimated time. If slow, suggest reducing parallelism.

    **⚠️ SQLite note:** If total records exceed 1,000, recommend loading a subset first to validate cross-source matching, then load more or switch to PostgreSQL (Module 8).

    **Checkpoint:** Write step 18 to `config/bootcamp_progress.json`.

19. **Coordinated redo queue processing:**

    Drain the redo queue — critical after multi-source loading for cross-source match refinement. Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')`. **CRITICAL**: Override paths to `database/G2C.db`.

    **Production redo patterns:**
    - Process redos after all sources are loaded (not between sources) to minimize redundant re-evaluations
    - Monitor redo queue depth during processing — a growing queue may indicate data quality issues
    - Log redo processing statistics: total redos processed, duration, entities affected

    Tell bootcamper: "Processing the redo queue now. This refines cross-source entity resolution — without it, some matches between your sources would be incomplete."

    **Checkpoint:** Write step 19 to `config/bootcamp_progress.json`.

---
