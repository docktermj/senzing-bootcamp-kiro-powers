---
inclusion: manual
---
## Phase 3 — Test Load and Validate (Optional)

> **This phase is optional.** Bootcampers who prefer to write custom loading programs can skip Phase 3 and proceed directly to Module 6. Phase 3 uses `mapping_workflow` steps 5–8 to give immediate feedback on entity resolution quality without leaving Module 5.

**Before starting Phase 3:** The Senzing SDK must be installed and configured (Module 2). If the SDK is not yet set up, inform the bootcamper: "Phase 3 requires the Senzing SDK (Module 2). You can skip Phase 3 and proceed to Module 6, or complete Module 2 first and return here." If the bootcamper chooses to skip, update the Data Source Registry with `test_load_status: skipped` for each source and proceed to Module 6.

### Workflow (per data source that completed Phase 2)

21. **SDK environment detection:** Call `mapping_workflow(action='advance')` to advance to step 5 (SDK environment detection). The workflow checks whether the Senzing SDK is installed and a database is configured. If detection fails, offer to skip Phase 3 or return to Module 2.

    **Checkpoint:** Write step 21 to `config/bootcamp_progress.json`.

22. **Test data loading:** Advance through `mapping_workflow` step 6 — load test data into a fresh SQLite database. This uses the transformation output from Phase 2 and loads a representative sample to verify the mapping produces valid Senzing records.

    **Checkpoint:** Write step 22 to `config/bootcamp_progress.json`.

23. **Validation report generation:** Advance through `mapping_workflow` step 7 — generate a validation report covering record counts, feature coverage, and data quality metrics for the test load.

    **Checkpoint:** Write step 23 to `config/bootcamp_progress.json`.

24. **Entity resolution evaluation:** Advance through `mapping_workflow` step 8 — evaluate entity resolution results from the test load. Present match counts, entity counts, and quality assessment to the bootcamper. Explain what the numbers mean: how many records resolved into how many entities, what the deduplication rate suggests about data quality, and whether the mapping is producing good results.

    **Checkpoint:** Write step 24 to `config/bootcamp_progress.json`.

    #### 24a. Capture ER Statistics

    After evaluating entity resolution results, capture the current statistics to a JSON file for comparison tracking. Use the Senzing SDK (via `generate_scaffold` or `find_examples`) to query the following counts:

    - **entity_count** — total resolved entities
    - **record_count** — total records loaded
    - **match_count** — number of matches (records that resolved together)
    - **possible_match_count** — number of possible matches flagged
    - **relationship_count** — number of disclosed relationships

    Save the statistics to `config/er_current_{datasource}.json` in this format:

    ```json
    {
      "datasource": "CUSTOMERS",
      "entity_count": 847,
      "record_count": 1000,
      "match_count": 153,
      "possible_match_count": 12,
      "relationship_count": 45,
      "captured_at": "2026-04-20T14:30:00Z"
    }
    ```

    > **Agent instruction:** Use `generate_scaffold` or `find_examples` to produce SDK code that queries these counts from the Senzing engine. Run the generated code and write the results to the JSON file. Use the datasource name (lowercased) in the filename.

    #### 24b. Baseline Detection

    Check whether a baseline file exists at `config/er_baseline_{datasource}.json` (where `{datasource}` is the lowercase datasource name).

    - **If no baseline exists:** This is the first test load for this data source. Save the current statistics as the baseline:

      ```text
      No baseline found for {DATASOURCE}. Saving current statistics as your first baseline.
      ```

      Copy `config/er_current_{datasource}.json` to `config/er_baseline_{datasource}.json`. Inform the bootcamper that future test loads will compare against this baseline so they can see how mapping changes affect entity resolution quality.

    - **If a baseline exists:** Proceed to step 24c (comparison).

    #### 24c. Compare Against Baseline

    When a baseline exists, run the comparison script to show the bootcamper how their mapping changes affected entity resolution:

    ```bash
    python3 senzing-bootcamp/scripts/compare_results.py \
      --baseline config/er_baseline_{datasource}.json \
      --current config/er_current_{datasource}.json
    ```

    Present the diff output to the bootcamper. The report shows per-metric deltas (entities gained/lost, matches gained/lost) and an overall quality assessment (improved, degraded, or unchanged). Explain what the changes mean:

    - **Fewer entities + more matches** → better deduplication, mapping improvement
    - **More entities + fewer matches** → less deduplication, possible mapping regression
    - **Unchanged** → mapping change had no measurable impact on ER quality

    #### 24d. Accept or Reject New Baseline

    Ask the bootcamper whether they want to accept the current results as the new baseline:

    > "Your mapping change resulted in [quality_assessment]. Would you like to accept these results as your new baseline for future comparisons, or would you prefer to iterate on the mapping and try again?"

    - **If accepted:** Copy `config/er_current_{datasource}.json` to `config/er_baseline_{datasource}.json`. Confirm: "New baseline saved. Future test loads will compare against these results."
    - **If rejected:** Keep the existing baseline unchanged. Inform the bootcamper they can return to Phase 2 to adjust their mapping and re-run Phase 3 to see updated results.

    > **Agent instruction:** Only present the accept/reject gate when a prior baseline existed (i.e., this is not the first test load). On the first test load, the baseline is saved automatically in step 24b without asking.

25. **Present results and decision gate:** Present the Phase 3 results summary for this data source. Include: records loaded, entities created, deduplication rate, quality assessment, and any issues found. Ask the bootcamper to review the results before proceeding.

    > **Agent instruction — Data Source Registry:** Update the source's `test_load_status` to `complete` and `test_entity_count` to the entity count from the test load in `config/data_sources.yaml`. Set `updated_at`.

    **Checkpoint:** Write step 25 to `config/bootcamp_progress.json`.

26. **Shortcut path decision:** After all sources have completed (or skipped) Phase 3, present the decision gate:

    - **Shortcut path (→ Module 7):** For simple use cases — single data source, small dataset (≤1000 records), no production requirements — the Phase 3 test load results may be sufficient. The bootcamper can proceed directly to Module 7 (Query & Visualize) and skip Module 6.
    - **Full path (→ Module 6):** For production requirements, multiple data sources, datasets exceeding 1000 records, or when the bootcamper wants to learn production-quality loading patterns — recommend the full Module 6 path.

    > **Agent instruction:** When the bootcamper chooses the shortcut path, update `config/bootcamp_progress.json` to mark Module 6 as skipped with reason `shortcut_path`:
>
    > ```json
    > {
    >   "modules_skipped": {
    >     "6": { "reason": "shortcut_path", "skipped_at": "<timestamp>" }
    >   }
    > }
    > ```

    > **Agent instruction — Data Source Registry:** If Phase 3 was skipped for any source, update that source's `test_load_status` to `skipped` in `config/data_sources.yaml`. Set `updated_at`.

    **Checkpoint:** Write step 26 to `config/bootcamp_progress.json`.

---

## Mapping State Checkpointing

Save checkpoint to `config/mapping_state_[datasource].json` after each step:

```json
{"data_source":"CUSTOMERS","source_file":"data/raw/customers.csv","current_step":3,"completed_steps":["profile","plan","map"],"decisions":{"entity_type":"PERSON","field_mappings":{"full_name":"NAME_FULL"}},"last_updated":"2026-04-14T10:30:00Z"}
```

On session resume: read checkpoint, show user where they left off, restart `mapping_workflow`, fast-track through decided steps, resume from first incomplete step. Delete checkpoint when mapping complete.

**Phase 3 session resume:** On session resume during Phase 3, read both the mapping state checkpoint (`config/mapping_state_[datasource].json`) and `config/bootcamp_progress.json` to determine which Phase 3 steps (21–26) have been completed. Restart `mapping_workflow` and fast-track through completed steps (5–8). If the test load (step 22) completed but evaluation (step 24) did not, the agent can re-run evaluation without reloading. If the session was interrupted before the decision gate (step 26), present the Phase 3 results again and resume from the decision gate.

## Rules

- NEVER hand-code attribute names — use `mapping_workflow`
- NEVER guess method signatures — use `generate_scaffold`/`get_sdk_reference`
- NEVER save to `/tmp/` — all files project-relative per `docs/policies/FILE_STORAGE_POLICY.md`
- Always validate with `analyze_record` before loading

## Success Criteria

- ✅ Test load completed for each data source (or explicitly skipped)
- ✅ Entity resolution results reviewed (deduplication rate, quality assessment)
- ✅ Decision gate completed (shortcut path or proceed to Module 6)

## Interpreting `analyze_record` Results

If `analyze_record` returns structural errors (e.g., flat format instead of FEATURES array, missing required fields), it may also show an empty Feature Analysis table with headers but no rows. This is not a bug — feature analysis is skipped when structural errors prevent feature extraction. Tell the user: "The Feature Analysis table is empty because there are structural issues with the record format — let's fix those first, then the feature analysis will populate." Focus on the structural errors listed above the table, fix the transformation program, and re-validate.

## Encoding

- Detect encoding in profiling step. Convert to UTF-8 in transformation program.
- Non-Latin scripts: `search_docs(query="globalization", category="globalization")`
- Strip UTF-8 BOM from Windows CSV files. JSON libraries handle special character escaping.

## Workflow: Install Senzing Bootcamp Hooks

**Note**: Hooks are installed automatically during onboarding — no user action needed. The agent copies all `.kiro.hook` files from `senzing-bootcamp/hooks/` to `.kiro/hooks/` when the bootcamp starts. Hooks can also be reinstalled at any time by saying "install hooks" or running `python3 scripts/install_hooks.py`.
