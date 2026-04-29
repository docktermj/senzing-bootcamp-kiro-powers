---
inclusion: manual
---

# Module 6: Load Data

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_6_LOAD_DATA.md`.

**Purpose**: Build production-quality loading programs, load all data sources into Senzing, process redo records, and validate entity resolution results — from first load through cross-source validation.

**Before/After**: You have Senzing-formatted JSON files (and possibly test load results from Module 5 Phase 3). After this module, all your data is loaded, redo records are processed, and entity resolution results are validated — duplicates matched, cross-source connections found.

**Prerequisites**: Module 5 complete (at least one transformed data source in `data/transformed/`), SDK installed and configured (Module 2), database configured (SQLite or PostgreSQL), transformation validated with linter.

## Conditional Workflow: Check Phase 3 Status

> **Agent instruction:** Before starting any loading, read `config/data_sources.yaml` and check the `test_load_status` field for each data source.
>
> - **If `test_load_status: complete`** — Phase 3 was completed in Module 5. Acknowledge the test load results: "You already test-loaded this source in Module 5 Phase 3 and saw [entity_count] entities. Module 6 builds on those results with production-quality loading — error handling, progress tracking, throughput optimization, redo processing, and incremental loading strategies." Skip the basic test loading steps and proceed directly to the production loading workflow below.
> - **If `test_load_status: skipped` or missing** — Phase 3 was not completed. Include a brief test load step: run `mapping_workflow` steps 5–8 (or a quick manual load of 10–100 records) to verify the data loads correctly before proceeding to production concerns. Update `test_load_status` to `complete` after the test load succeeds.
>
> Also check for anti-patterns before starting: `search_docs(query="loading", category="anti_patterns", version="current")`.

> **Agent instruction — Phase 3 Results Integration:** Read `config/data_sources.yaml` and check `test_load_status` and `test_entity_count` for each source. If Phase 3 was completed for multiple sources, reference the test load results when planning load order and dependency management:
> - Use `test_entity_count` values to estimate total entity volume and plan resource allocation
> - Use quality assessments from Phase 3 to inform which sources to load first (higher quality → stronger entity baseline)
> - Note any issues discovered during Phase 3 test loading that may affect production orchestration

## Agent Workflow

> **Agent instruction:** Before starting, call `search_docs(query="loading", category="anti_patterns", version="current")`. Key pitfalls: bulk loading issues, threading problems, redo processing, load order dependencies.

---

## Phase A: Build Loading Program

1. **Identify the input data:** Determine where the Senzing-formatted JSON records are for the first data source:
   - Output from a transformation program (Module 5)
   - Direct Entity Specification-compliant data files
   - Database query results or API responses

   > **Agent instruction — Data Source Registry:** Update the source's `load_status` to `loading` in `config/data_sources.yaml` and set `updated_at`.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Create the production loading program:** Help the user build a complete, production-quality loading program for this data source.

   **IMPORTANT:** All generated code must follow the coding standards for the bootcamper's chosen language (see `docs/policies/CODE_QUALITY_STANDARDS.md`).

   > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')`
   > to get the current loading pattern. Do not use inline examples — they may use outdated SDK patterns. Customize the scaffold with the user's file path, data source name, and progress reporting.
   >
   > **CRITICAL:** If the generated scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db` and ensure all output files use project-relative paths. No files may be placed outside the working directory.

   The program must include production-quality features:
   - **Robust error handling:** Per-record error logging with record ID, error code, and error message. Failed records are logged to `logs/loading_errors.json` without stopping the load.
   - **Progress tracking with throughput reporting:** Display progress every N records (e.g., every 100 or 1000) showing records loaded, error count, elapsed time, and records/second throughput.
   - **Statistics reporting:** At completion, report total records attempted, loaded, failed, duration, throughput, and error summary.
   - SDK initialization, record loading loop, and proper cleanup.

   **Save the program:** Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]` using the appropriate file extension for the chosen language).

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Use MCP tools for code generation:** Call `generate_scaffold` with workflow `add_records` and the bootcamper's chosen language to get version-correct SDK code. Call `sdk_guide` with `topic='load'` for platform-specific loading patterns.

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

---

## Phase B: Load First Source

4. **Test with sample data (if Phase 3 was skipped):** If the bootcamper did not complete Phase 3 in Module 5, run the loading program on a small subset first:
   - Start with 10–100 records
   - Verify the program connects to the engine
   - Check that records are being added successfully
   - Observe any errors or warnings

   If Phase 3 was completed, skip this step — the test load already verified basic loading works. Proceed directly to production loading.

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Observe entity resolution in real time:** As records load, Senzing resolves entities automatically:
   - Watch the console output for resolution activity
   - Note how entities are being formed
   - See how new records match or create entities
   - This gives immediate feedback on data quality and matching behavior

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Load the full dataset:** Run the program on the complete data source with production-quality monitoring:
   - Monitor progress and throughput performance
   - Watch for error rate trends (increasing errors may indicate data issues)
   - Note loading statistics (time, throughput, error rate)
   - If errors exceed 5%, pause and investigate before continuing

   > **Agent instruction — Data Source Registry:** On success, update `load_status` to `loaded` and `record_count` to the actual loaded count in `config/data_sources.yaml`. On failure, set `load_status` to `failed` and add an `issues` entry describing the error. Update `updated_at` in either case.

   **⚠️ SQLite performance note:** On SQLite with single-threaded loading, entity resolution gets progressively slower as the database grows. For the bootcamp learning experience, recommend loading ≤1,000 records initially. This is enough to see meaningful entity resolution results without long waits. If the user has more data, suggest: "Let's start with the first 1,000 records so we can see results quickly. Once we validate the results here, we can load the full dataset — or switch to PostgreSQL for better performance with larger volumes (Module 8 covers this)."

   **Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

7. **Save and document the loading program:** Document and save the program:
   - Save in `src/load/` with a clear name (e.g., `src/load/load_customer_db.[ext]`)
   - All loading programs must be in the `src/load/` directory
   - Document how to run it (command line, configuration)
   - Note any prerequisites or dependencies
   - Keep it for future reloads or updates

   **Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

8. **Process redo records:** After loading completes, drain the redo queue. Redo records are deferred re-evaluations that refine the entity resolution graph — without processing them, results are incomplete.

   Use `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')` to get the redo processing pattern. The loading program (or a separate script) should sequentially process all pending redos until the queue is empty.

   **CRITICAL:** If the generated redo scaffold uses `/tmp/`, `ExampleEnvironment`, or any path outside the working directory, override the database path to `database/G2C.db`.

   Include a comment in the code explaining that in production, redos are typically handled by an always-running redo processor that wakes up, checks for pending redos, processes them, and sleeps when the queue is empty.

   Tell the bootcamper: "Processing the redo queue now. This refines entity resolution — without it, some matches would be incomplete."

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

9. **Incremental loading strategy:** Discuss incremental loading as a production concern distinct from the initial bulk load:
   - **Full reload** (what we just did): Load all records every time. Simple but slow for large datasets.
   - **Incremental load** (production pattern): Track which records are new or changed since the last load. Only load deltas. Requires a change detection mechanism (timestamps, sequence numbers, change data capture).
   - **Upsert pattern**: Use `add_record` with the same `RECORD_ID` to update existing records. Senzing re-evaluates entity resolution automatically.
   - Help the bootcamper understand when each strategy applies and document the choice in `docs/loading_strategy.md`.

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

10. **Mark first data source as loaded:** Once loading and redo processing are complete, mark this data source as loaded.

    **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

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

## Phase D: Validation

### Single-Source Validation (Always)

20. **Validate match accuracy:** Review the entity resolution results:
    - Query a sample of known records using `get_entity_by_record_id` to check how they resolved
    - Look for expected matches — are records that should match resolving to the same entity?
    - Look for false positives — are unrelated records being incorrectly merged?
    - Look for false negatives — are records that should match resolving to separate entities?
    - If match accuracy is poor, revisit data quality (Module 5) or mapping before proceeding

    > **Agent instruction:** Use `generate_scaffold(language='<chosen_language>', workflow='query', version='current')` to generate code that retrieves sample entities for review. Use `get_sdk_reference(topic='functions', filter='why_entities', version='current')` to explain why records matched.

    **Checkpoint:** Write step 20 to `config/bootcamp_progress.json`.

21. **Run basic UAT for single-source:** Validate that the loaded data meets business expectations:
    - Verify record counts — does the number of loaded records match expectations?
    - Spot-check entity resolution — pick 5–10 known entities and confirm they resolved correctly
    - Document any issues found in `docs/uat_results.md`
    - If critical issues are found, fix and reload before proceeding

    **Checkpoint:** Write step 21 to `config/bootcamp_progress.json`.

### Cross-Source Validation (Conditional — 2+ Sources Loaded)

> **Agent instruction:** Only present steps 22–26 when the bootcamper has loaded 2 or more data sources. For single-source bootcampers, skip directly to step 27 (Document results).

22. **Validate cross-source results:**

    Validate: record counts match expectations, cross-source entities exist, no unexpected data loss, error logs clean.

    > **Agent instruction:** Use `reporting_guide(topic='graph', version='current')` for network graph patterns.

    Sample 15–25 entities that contain records from multiple data sources and verify they represent the same real-world person or organization. Check cross-source matches and spot-check single-source entities to confirm no cross-source matches were missed.

    Offer to visualize the cross-source entity relationships as a web page. If accepted, save to `docs/multi_source_results.html`.

    **Checkpoint:** Write step 22 to `config/bootcamp_progress.json`.

23. **Validate cross-source results quality:**

    > **Agent instruction:** Use `reporting_guide(topic='evaluation', version='current')` for the 4-point ER evaluation framework and `reporting_guide(topic='quality', version='current')` for precision/recall metrics.

    Validate: match accuracy (query known records via `get_entity_by_record_id`), false positives (incorrect merges), false negatives (missed matches), data completeness. If accuracy is poor, revisit Module 5 mapping.

    **Checkpoint:** Write step 23 to `config/bootcamp_progress.json`.

24. **Execute UAT with business users:**

    Offer to involve business users in testing the cross-source results.

    If yes: share cross-source match examples, collect feedback, document in `docs/uat_results.md`. If no: agent spot-checks 5–10 cross-source entities and documents findings in `docs/uat_results.md`.

    **Checkpoint:** Write step 24 to `config/bootcamp_progress.json`.

25. **Get stakeholder sign-off:**

    Create `docs/results_validation.md` with match quality metrics (true/false positive/negative rates) and business validation results (test cases passed, issues, resolution plan).

    **Checkpoint:** Write step 25 to `config/bootcamp_progress.json`.

26. **Document validation results:**

    Save all findings to `docs/results_validation.md`: total records loaded, entities created, cross-source match rate, UAT results, stakeholder feedback/sign-off status. This becomes the validation baseline before Module 7.

    Update `docs/loading_strategy.md` with: final load order/rationale, per-source statistics, cross-source match summary, issues and resolutions, recommendations for future loads.

    **Checkpoint:** Write step 26 to `config/bootcamp_progress.json`.

### Document Results and Complete (Always)

27. **Document results and offer visualization:** Record the validation findings:
    - Save validation results to `docs/results_validation.md`
    - Include: total records loaded, entities created, match rate, any issues found and their resolution
    - This becomes the baseline for comparison

    > **⛔ MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD**
    > You MUST offer the results dashboard visualization before proceeding to the Decision Gate.

    Present the results dashboard offer to the bootcamper: a results dashboard showing entity resolution results with entity counts, match statistics, and sample resolved entities — saved as `docs/results_dashboard.html`.

    - If they say **yes**: Generate the HTML dashboard and save to `docs/results_dashboard.html`.
    - If they say **no** or **not now**: Acknowledge and proceed.
    - If they are **unsure**: Briefly explain the value, then wait for their decision.

    **Checkpoint:** Write step 27 to `config/bootcamp_progress.json`.

---

## Recovery from Failed Load

If loading fails partway through (crash, error, disk full, etc.):

1. **Check what loaded** — query a few known RECORD_IDs using `get_entity_by_record_id` to see if they exist. The loading program's progress counter tells you approximately how far it got.
2. **Decide — wipe and restart vs. resume:**
   - **Wipe and restart** (simpler): Restore the database from the backup created before loading (use `python scripts/restore_project.py`), fix the issue, and re-run the loading program from the beginning.
   - **Resume from where it stopped** (faster for large loads): Modify the loading program to skip records that are already loaded. The simplest approach is to track the last successfully loaded RECORD_ID and start from the next one.
3. **If the database is corrupted** — restore from backup. This is why the `backup-before-load` hook exists. If no backup exists, delete `database/G2C.db` and re-run Module 2's database configuration step, then reload.
4. **Common causes of mid-load failure:**
   - Disk full → free space or move database to a larger volume
   - Out of memory → reduce batch size or add RAM
   - Invalid records → check the error log, fix the transformation, and reload the bad records
   - Network timeout (remote database) → check connection and retry

### Multi-Source Recovery (Phase C)

IF a source fails during orchestration, THEN present these three options:

1. **Skip and continue**: Mark the source as failed, continue loading remaining sources. Come back to the failed source after fixing the issue. Best when other sources are independent.
2. **Retry after fix**: Pause orchestration, fix the issue (e.g., repair transformation), retry the failed source. Best when the fix is quick and obvious.
3. **Restore and restart**: Restore the database from backup (`python scripts/restore_project.py`), fix the issue, restart orchestration from the beginning. Best when the failure may have corrupted data.

Present the recovery options to the bootcamper: skip and continue with remaining sources, fix the issue and retry, or restore from backup and start over. Include the source name and error details.

---

## Iterate vs. Proceed Decision Gate

After presenting validation results, guide the decision:

- **UAT ≥90% and match accuracy ≥90%:** "Results look strong. Ready to proceed to Module 7 (Query & Visualize) or stop here if on Path B/C."
- **UAT 80–89%:** "Most tests pass but there are gaps. Iterate on failures or move forward?"
- **UAT <80%:** "Results need improvement — suggest going back to Module 5 or earlier steps in this module. Investigate or proceed anyway?"

---

## Stakeholder Summary

After validation, offer: "Would you like a one-page executive summary for your team or stakeholders?"

If yes, read the template: #[[file:senzing-bootcamp/templates/stakeholder_summary.md]] Follow the **MODULE 6** guidance block to fill placeholders with Module 6 context (validation results, match metrics, UAT outcomes, loaded record counts). Save to `docs/stakeholder_summary_module6.md`.

---

## Reference Material

> **Agent instruction:** Only present multi-source reference material (source ordering, orchestration patterns, conflict resolution, troubleshooting) when the bootcamper has 2 or more data sources. For single-source bootcampers, skip this section entirely.

### Source Ordering Heuristics

Apply ordering heuristics in priority order:
1. **Reference before transactional** — Load reference data (watchlists, product catalogs) before transactional data that screens against it
2. **Quality-first** — Load the highest-quality source first to establish a strong entity baseline
3. **Attribute-density-first** — Sources with more matching attributes (name + address + phone + email) create better initial entities
4. **Volume-first** — When quality is similar, load the larger source first for a broader baseline

### Source Ordering Examples

#### Customer 360 (Quality-First)

```text
Load order:
1. CUSTOMERS_CRM (50K records, 92% quality) — best data, establishes entity baseline
2. ECOMMERCE_ACCTS (35K records, 85% quality) — matches against CRM entities
3. SUPPORT_TICKETS (20K records, 78% quality) — links to existing entities

Why: CRM has the most complete records (name + email + phone + address). Loading it first means Senzing builds strong initial entities. Subsequent sources match against this high-quality baseline.
```

#### Compliance Screening (Reference-First)

```text
Load order:
1. WATCHLISTS (10K records) — reference data, must be present before screening
2. INTERNAL_CUSTOMERS (100K records) — screen against watchlists
3. THIRD_PARTY_DATA (50K records) — additional screening coverage

Why: Watchlists are reference data that other sources screen against. Loading them first ensures every subsequent record is checked against the complete watchlist.
```

### Orchestration Patterns

#### Pattern 1: Sequential Loading

Simple, predictable, but slow:

```text
sources = ["customers", "vendors", "products", "orders"]
For each source in sources:
    load_source(source)
```

#### Pattern 2: Parallel Loading (Independent Sources)

Fast for independent sources:

```text
independent_sources = ["customers", "vendors", "products"]
Run all of the following concurrently (up to 3 workers):
    For each source in independent_sources:
        load_source(source)
Wait for all to complete
```

#### Pattern 3: Dependency-Aware Loading

Respects dependencies:

```text
Function load_with_dependencies(source, dependencies, loaded_set):
    For each dep in dependencies[source]:
        If dep is NOT in loaded_set:
            load_with_dependencies(dep, dependencies, loaded_set)

    load_source(source)
    Add source to loaded_set
```

#### Pattern 4: Pipeline Loading

Streaming pipeline for large datasets:

```text
Producer-consumer pattern using a thread-safe queue:

Producer (one per source):
    For each record in source:
        transformed = transform(record)
        Put transformed record onto queue

Consumer (one or more):
    Loop:
        Take record from queue
        If record is a stop signal, exit loop
        load_record(record)
```

### Error Handling Strategies

1. **Fail Fast:** Stop all loading on first error
2. **Continue on Error:** Log errors, continue with other sources
3. **Retry with Backoff:** Retry failed sources with exponential backoff (1s, 2s, 4s, 8s up to configurable max)
4. **Partial Success:** Mark successful sources as loaded, retry only failed ones without rolling back successes

### Conflict Resolution

Senzing uses **observation-based resolution** — it retains all observations from all sources rather than picking a "winner." When records from different sources conflict, Senzing does not overwrite one with the other. Instead, the resolved entity contains all observations, and consuming applications decide which to use.

> **Agent instruction:** When a bootcamper asks about conflicting records, use
> `search_docs(query="entity resolution conflicts", version="current")` to retrieve current Senzing guidance.

**Common conflict scenarios:**

1. **Different addresses**: Customer has address A in CRM and address B in E-commerce. Senzing retains both addresses on the resolved entity. The entity has two address observations — neither is "wrong."

2. **Different phone numbers**: CRM has a work phone, Support has a mobile phone. Both are retained. The entity has multiple phone observations.

3. **Different name spellings**: "Robert Johnson" in CRM, "Bob Johnson" in E-commerce. Senzing matches on name features (it knows Robert/Bob are variants). Both name observations are retained on the entity.

**Example scenario:**

```text
Source 1 (CRM):     {"DATA_SOURCE":"CRM", "RECORD_ID":"C001", "NAME_FULL":"John Smith", "ADDR_FULL":"123 Main St", "PHONE_NUMBER":"555-0101"}
Source 2 (ECOM):    {"DATA_SOURCE":"ECOM", "RECORD_ID":"E001", "NAME_FULL":"John A Smith", "ADDR_FULL":"456 Oak Ave", "EMAIL_ADDRESS":"john@email.com"}

Resolved entity:    ENTITY_ID: 1
                    Records: CRM:C001, ECOM:E001
                    Names: "John Smith", "John A Smith"
                    Addresses: "123 Main St", "456 Oak Ave"
                    Phones: "555-0101"
                    Emails: "john@email.com"
```

Both records contribute to the entity. Nothing is lost or overwritten.

> **Agent instruction:** Offer visualization: "Would you like me to create a visualization showing how your entities connect across sources?" If yes, use `reporting_guide(topic='graph', version='current')` for the pattern.

### Troubleshooting Quick Reference

> **Agent instruction:** Use this section for quick diagnosis. If the issue is not covered here, load `common-pitfalls.md` for the full pitfall table.

| Issue | Diagnosis | Resolution |
| ----- | --------- | ---------- |
| Low cross-source match rates | Check Module 5 quality scores for each source. Review Module 5 mapping consistency — are the same fields mapped to the same Senzing attributes across sources? Use `get_sdk_reference(topic='why')` to examine match details for specific entities | Improve data quality in weak sources, align attribute mappings across sources, ensure name/address/phone/email fields are mapped consistently |
| Unexpected entity merges | Two entities from different sources merged that should not have. Use the SDK "why" method to see which features caused the match | Check for overly generic features (e.g., common names without other distinguishing attributes). Review data quality — are placeholder values ("N/A", "Unknown") causing false matches? |
| Slow loading with multiple sources | Check total record count, database type (SQLite vs PostgreSQL), and parallelism level | SQLite slows significantly beyond ~1,000 total records. Reduce parallelism to 1–2 workers. For larger volumes, recommend PostgreSQL migration (Module 8) |
| Redo queue not draining | Check for errors in redo processing output. Use `explain_error_code` for any error codes | Restart the redo processor. If errors persist, check for corrupted entities and consider restoring from backup |
| Resource exhaustion (out of memory, disk full) | Monitor system resources during parallel loading. Check database file size | Reduce max parallel loaders. Free disk space or move database to larger volume. Increase available memory |
| Source ordering affects resolution quality | Compare entity counts and match rates after loading in different orders | Apply the ordering heuristics from Step 13. In general, loading higher-quality sources first produces better results. If results are significantly different, the data quality gap between sources is large — address in Module 5 |
| Slow loading performance (< 50 records/second) | Check database type, batch size, and system resources | Use batch loading, optimize database (indexes, memory), use PostgreSQL instead of SQLite |
| High error rate (> 5% of records fail) | Review error messages, re-run linter on transformed data | Check for data quality issues, validate transformation logic |
| All records become one entity | Entity count = 1 | Check RECORD_ID is unique per record, verify records have distinguishing features |
| No duplicates found (entity count = record count) | Verify data actually has duplicates | Check matching features are present (names, addresses, etc.), review data quality scores from Module 5 |

### Performance Benchmarks

Set expectations based on database type:

- **SQLite (bootcamp default)**: ~50–200 records/second single-threaded. Slows as database grows. Suitable for ≤1,000 total records across all sources.
- **PostgreSQL**: ~500–2,000 records/second with multi-threading. Scales to millions of records. Recommend migration when total records exceed 1,000 or when loading takes more than a few minutes.

If the bootcamper is experiencing slow loading, suggest: "Loading is slow because SQLite doesn't handle concurrent writes well. For the bootcamp, let's work with a smaller subset. When you're ready for production volumes, Module 8 covers PostgreSQL migration."

### Common Issues

- **Dependency cycles**: Flag to bootcamper, explain that Senzing handles load order gracefully — load the higher-quality source first
- **Resource exhaustion**: Reduce parallelism, check disk space, consider PostgreSQL
- **Slow performance**: Optimize transformations, reduce record count for bootcamp, or use PostgreSQL
- **Missing sources**: Check Module 5 — all sources must be mapped before orchestration
- **Inconsistent mappings**: Different sources map the same real-world field to different Senzing attributes — re-run Module 5 for consistency

### Pre-Load Validation Checklist

Run this checklist before starting orchestration:

1. ✅ All JSONL files in `data/transformed/` are valid (non-empty, valid JSON per line)
2. ✅ Every record has `DATA_SOURCE` and `RECORD_ID` fields
3. ✅ DATA_SOURCE names match the Senzing engine configuration (from Module 2)
4. ✅ RECORD_IDs are unique within each DATA_SOURCE
5. ✅ Database backup exists (`python scripts/backup_project.py`)
6. ✅ No JSONL files contain records with mismatched DATA_SOURCE values

### Per-Source Failure Isolation

When one source fails during orchestration, the agent should:

1. Log the error with source name, record number, and error message
2. Use `explain_error_code(error_code="<code>", version="current")` to diagnose
3. Continue loading remaining sources (do not stop the entire orchestration)
4. Report the failure in the final summary
5. Document the error in `docs/loading_strategy.md`

### Common Error Scenarios

| Error | Diagnosis | Fix |
| ----- | --------- | --- |
| Invalid records (malformed JSON, missing required fields) | Use `analyze_record` on a sample record from the failing source | Fix the transformation program in `src/transform/`, re-run on the source, reload |
| Duplicate RECORD_IDs across sources | Two sources use the same RECORD_ID values (e.g., both start at "1") | RECORD_IDs only need to be unique within a DATA_SOURCE — this is usually not an error. If IDs collide within the same DATA_SOURCE, prefix with source identifier |
| DATA_SOURCE name mismatch | The DATA_SOURCE in records does not match the engine configuration | Verify DATA_SOURCE names against Module 2 setup. Fix in the transformation program |
| Transformation errors (wrong attribute names, missing mappings) | Use `analyze_record` to validate a sample record | Re-run Module 5 mapping workflow for the affected source |

---

## Success Criteria

- ✅ Loading program generated and customized with production-quality error handling, progress tracking, and statistics
- ✅ At least one data source fully loaded with error rate < 1%
- ✅ Redo queue drained after loading
- ✅ Loading statistics documented in `docs/loading_strategy.md`
- ✅ Match accuracy reviewed (sample entities checked for false positives/negatives)
- ✅ Results validation documented in `docs/results_validation.md`
- ✅ Loading program saved in `src/load/`

### Additional criteria when 2+ sources loaded:

- ✅ All sources loaded (or failures documented) with error rate < 1% per source
- ✅ Dependencies respected, cross-source matches reviewed
- ✅ Orchestrator program saved in `src/load/orchestrator.[ext]`
- ✅ Cross-source match accuracy validated
- ✅ UAT executed, results in `docs/uat_results.md`
- ✅ Stakeholder sign-off obtained
