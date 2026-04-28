---
inclusion: manual
---

# Module 7: Multi-Source Orchestration

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`.

**Purpose**: Coordinate loading of multiple data sources with dependencies, conflict resolution, and optimization.

**Before/After**: You have one source loaded. After this module, all your sources are loaded with cross-source matching — Senzing is finding connections between records from different systems.

**Prerequisites**: Module 6 complete, multiple sources mapped/transformed (Module 5), loading stats reviewed, redo queue drained for first source.

## Agent Workflow

> **Agent instruction:** Before starting, call `search_docs(query="multi-source loading orchestration", category="anti_patterns", version="current")`. Key pitfalls: threading issues, redo processing, load order dependencies.

1. **Check anti-patterns and prepare**: Call `search_docs` for anti-patterns, flag pitfalls relevant to the bootcamper's sources and language. **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Inventory all data sources**:

   > **Agent instruction:** Read `config/data_sources.yaml` for `quality_score`, `mapping_status`, and `load_status` per source.

   Enumerate every data source. For each: source name/DATA_SOURCE identifier, record count, quality score, mapping status, loaded status. Present a summary table.

   👉 "Here are all the data sources from your project. Are there any sources missing, or any changes to this list?" WAIT for response.

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Analyze dependencies**:

   👉 "Do any of your data sources depend on others being loaded first?" WAIT for response.

   Common patterns: parent-child (load parents first), reference data first, temporal ordering, or no dependencies. If circular dependency detected, explain that Senzing resolves entities as records arrive — load the higher-quality source first. Save dependency map to `docs/loading_strategy.md`.

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

4. **Determine load order**:

   > **Agent instruction:** Use `quality_score` from `config/data_sources.yaml` to rank sources. Update `load_status` as loading progresses.

   Apply ordering heuristics (priority order): (1) reference before transactional, (2) quality-first for strong entity baseline, (3) attribute-density-first, (4) volume-first when quality is similar.

   👉 "Based on your data, I recommend this load order: [order with reasons]. Does this look right?" WAIT for response.

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Select loading strategy**:

   👉 "How would you like to load the remaining sources?" Present: **Sequential** (safer, easier to debug), **Parallel** (faster, more resources), **Hybrid** (sequential for dependent, parallel for independent). WAIT for response.

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Pre-load validation checklist**:

   Verify before orchestration: all JSONL files exist in `data/transformed/` and are non-empty; unique DATA_SOURCE names match Module 2 config; RECORD_IDs unique within each source; database backup exists; sufficient disk space (~2x per source); Module 6 loading program works as template. Fix failures before proceeding.

   **Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

7. **Create orchestrator program**:

   > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` and `find_examples(query="multi-source")` for patterns.

   **CRITICAL**: Override any `/tmp/` or `ExampleEnvironment` paths to `database/G2C.db`.

   Save to `src/load/orchestrator.[ext]`. Must handle: ordered loading with dependency enforcement, parallel execution if selected, per-source progress/error tracking with error isolation, statistics aggregation, and completion summary.

   **Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

8. **Test with sample data**:

   Test orchestrator with 10-100 records per source. Verify: sources load without errors, dependencies respected, progress tracking works, error handling triggers correctly.

   👉 "The orchestrator ran successfully on sample data. Ready to run on the full dataset?" WAIT for response.

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

9. **Run full orchestration**:

   Run on complete dataset. Monitor per-source progress, error rates, overall completion, elapsed/estimated time. If slow, suggest reducing parallelism.

   **⚠️ SQLite note:** If total records exceed 1,000, recommend loading a subset first to validate cross-source matching, then load more or switch to PostgreSQL (Module 9).

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

10. **Process redo queue**:

    Drain the redo queue — critical after multi-source loading for cross-source match refinement. Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')`. **CRITICAL**: Override paths to `database/G2C.db`.

    Tell bootcamper: "Processing the redo queue now. This refines cross-source entity resolution — without it, some matches between your sources would be incomplete."

    **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

11. **Validate cross-source results**:

    Validate: record counts match expectations, cross-source entities exist, no unexpected data loss, error logs clean.

    > **Agent instruction:** Use `reporting_guide(topic='graph', version='current')` for network graph patterns.

    👉 "Would you like me to visualize the cross-source entity relationships as a web page?" WAIT for response. If yes, save to `docs/multi_source_results.html`.

    **Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

12. **Document results**:

    Update `docs/loading_strategy.md` with: final load order/rationale, per-source statistics, cross-source match summary, issues and resolutions, recommendations for future loads.

    **Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

13. **Validate cross-source results quality**:

    > **Agent instruction:** Use `reporting_guide(topic='evaluation', version='current')` for the 4-point ER evaluation framework and `reporting_guide(topic='quality', version='current')` for precision/recall metrics.

    Validate: match accuracy (query known records via `get_entity_by_record_id`), false positives (incorrect merges), false negatives (missed matches), data completeness. If accuracy is poor, revisit Module 5 mapping.

    **Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

14. **Execute UAT with business users**:

    👉 "Would you like to involve business users in testing the cross-source results?" WAIT for response.

    If yes: share cross-source match examples, collect feedback, document in `docs/uat_results.md`. If no: agent spot-checks 5-10 cross-source entities and documents findings in `docs/uat_results.md`.

    **Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

15. **Get stakeholder sign-off**:

    Create `docs/results_validation.md` with match quality metrics (true/false positive/negative rates) and business validation results (test cases passed, issues, resolution plan).

    > **⛔ MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD**
    > You MUST offer and WAIT for response before proceeding to the Decision Gate.

    👉 "Would you like me to create a web page showing cross-source results and validation metrics? Saved as `docs/results_dashboard.html`." WAIT for response. If yes, generate dashboard. If no/unsure, acknowledge and proceed.

    **Checkpoint:** Write step 15 to `config/bootcamp_progress.json`.

16. **Document validation results**:

    Save all findings to `docs/results_validation.md`: total records loaded, entities created, cross-source match rate, UAT results, stakeholder feedback/sign-off status. This becomes the validation baseline before Module 8.

    **Checkpoint:** Write step 16 to `config/bootcamp_progress.json`.

## Iterate vs. Proceed Decision Gate

After presenting validation results, guide the decision:

- **UAT ≥90% and match accuracy ≥90%:** "Results look strong. Ready to proceed to Module 8 or stop here if on Path B/C."
- **UAT 80-89%:** "Most tests pass but there are gaps. Iterate on failures or move forward?"
- **UAT <80%:** "Results need improvement — suggest going back to Module 5 or 6. Investigate or proceed anyway?"

WAIT for response.

## Stakeholder Summary

After validation, offer: "Would you like a one-page executive summary for your team or stakeholders?"

If yes, read the template: #[[file:senzing-bootcamp/templates/stakeholder_summary.md]] Follow the **MODULE 7** guidance block to fill placeholders with Module 7 context (validation results, match metrics, UAT outcomes, loaded record counts). Save to `docs/stakeholder_summary_module7.md`.

## Reference Material

For source ordering examples, conflict resolution, error handling, and troubleshooting: load `module-07-reference.md`.

## Success Criteria

- ✅ All sources loaded (or failures documented) with error rate < 1% per source
- ✅ Redo queue drained, dependencies respected, cross-source matches reviewed
- ✅ Loading statistics in `docs/loading_strategy.md`, orchestrator in `src/load/orchestrator.[ext]`
- ✅ Match accuracy validated (false positives/negatives reviewed)
- ✅ UAT executed, results in `docs/results_validation.md`, stakeholder sign-off obtained
