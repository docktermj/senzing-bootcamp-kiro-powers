---
inclusion: manual
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

