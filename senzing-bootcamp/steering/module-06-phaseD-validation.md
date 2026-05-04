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

If loading fails partway through:

1. **Check what loaded** — query known RECORD_IDs to see if they exist.
2. **Decide — wipe and restart vs. resume:**
   - **Wipe and restart**: Restore from backup (`python3 scripts/restore_project.py`), fix issue, re-run.
   - **Resume**: Modify loading program to skip already-loaded records.
3. **If database corrupted** — restore from backup. If no backup, delete `database/G2C.db` and re-run Module 2 config.
4. **Common causes:** Disk full, out of memory, invalid records, network timeout.

### Multi-Source Recovery (Phase C)

IF a source fails during orchestration, present three options:

1. **Skip and continue**: Mark failed, continue with remaining sources.
2. **Retry after fix**: Pause, fix issue, retry failed source.
3. **Restore and restart**: Restore from backup, fix, restart orchestration.

---

## Iterate vs. Proceed Decision Gate

- **UAT ≥90% and match accuracy ≥90%:** "Results look strong. Ready to proceed to Module 7."
- **UAT 80–89%:** "Most tests pass but there are gaps. Iterate or move forward?"
- **UAT <80%:** "Results need improvement — suggest going back to Module 5."

---

## Stakeholder Summary

After validation, offer: "Would you like a one-page executive summary for your team?"

If yes, read the template: #[[file:senzing-bootcamp/templates/stakeholder_summary.md]] Follow the **MODULE 6** guidance block. Save to `docs/stakeholder_summary_module6.md`.

---

## Success Criteria

- ✅ Loading program generated with production-quality error handling, progress tracking, and statistics
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

## Reference Material

For multi-source reference (source ordering, orchestration patterns, conflict resolution, troubleshooting, performance benchmarks), load:

#[[file:senzing-bootcamp/steering/module-06-reference.md]]
