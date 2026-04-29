---
inclusion: manual
---

# Module 5: Data Quality & Mapping

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`.
>
> **Quality Scoring Methodology:** For a full explanation of how quality scores are calculated, what each dimension measures, and what thresholds mean, see `docs/guides/QUALITY_SCORING_METHODOLOGY.md`. When a user asks how their score was calculated or what their score means, direct them to this guide.

**Before/After:** You have raw data files but don't know if Senzing can use them directly. After this module, each source is scored for quality, categorized, and transformed into Senzing JSON — validated and ready to load.

**Prerequisites:** ✅ Module 4 complete (data sources collected, files in `data/raw/`)

---

## Phase 1 — Quality Assessment

### Workflow: Verify Data Sources Against the Entity Specification

1. **List the agreed-upon data sources**: Recap the data sources identified during the business problem discussion. Review `docs/business_problem.md` for the list.

   **Checkpoint:** Write step 1 to `config/bootcamp_progress.json`.

2. **Request sample data**: For each data source, ask the user to place sample files in `data/raw/` or `data/samples/`:
   - CSV files (first 10-20 rows)
   - JSON samples
   - Database schema with sample values
   - Screenshots of data tables
   - Text descriptions of fields and data types

   **Checkpoint:** Write step 2 to `config/bootcamp_progress.json`.

3. **Understand the Senzing Generic Entity Specification**: Call `search_docs` with query "generic entity specification" or "Entity Specification format" to retrieve current documentation about the standard format. Key Entity Specification attributes include:
   - **Identity attributes**: `NAME_FULL`, `NAME_FIRST`, `NAME_LAST`, `NAME_ORG`, `DATE_OF_BIRTH`, `PASSPORT_NUMBER`, `DRIVERS_LICENSE_NUMBER`, `SSN_NUMBER`, `NATIONAL_ID_NUMBER`
   - **Contact attributes**: `ADDR_FULL`, `ADDR_LINE1`, `ADDR_CITY`, `ADDR_STATE`, `ADDR_POSTAL_CODE`, `PHONE_NUMBER`, `EMAIL_ADDRESS`, `WEBSITE_ADDRESS`
   - **Required fields**: `DATA_SOURCE`, `RECORD_ID`
   - **Relationship attributes**: `REL_ANCHOR_DOMAIN`, `REL_ANCHOR_KEY`, `REL_POINTER_DOMAIN`, `REL_POINTER_KEY`, `REL_POINTER_ROLE`

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

4. **Compare each data source with the Entity Specification**: For each data source provided:
   - Identify which fields map directly to Entity Specification attributes (e.g., "full_name" → `NAME_FULL`)
   - Identify fields that need transformation (e.g., separate "first_name" and "last_name" → `NAME_FULL`)
   - Identify fields with non-standard names (e.g., "company" → `NAME_ORG`)
   - Note any missing critical fields
   - Check if `DATA_SOURCE` and `RECORD_ID` are present or can be derived

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Categorize each data source**:
   - **Entity Specification-compliant**: Data already uses standard Senzing attribute names and structure. Can proceed directly to Module 2 (SDK setup) and Module 6 (loading).
   - **Needs mapping**: Data uses different field names or structures. Continue to Phase 2 (data mapping) below.
   - **Needs enrichment**: Data is missing critical attributes. Discuss with user whether additional data sources can provide missing information.

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

6. **Assess data quality and apply thresholds**:

   For each data source, compute a quality score based on field completeness, format consistency, and duplicate rate. Use these thresholds to guide the decision:

   - **≥80% quality score** → Proceed to Phase 2 (mapping). Data quality is strong enough for meaningful entity resolution.
   - **70-79% quality score** → Warn the user. Quality gaps exist — suggest specific fixes (fill nulls, standardize formats, deduplicate within source). Proceed to Phase 2 if the user accepts the risk, but document the quality gaps. See `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for details on what each score range means.
   - **<70% quality score** → Strongly recommend fixing data quality before mapping. Entity resolution results will be poor. Help the user identify the biggest quality issues and create a remediation plan. Only proceed if the user explicitly chooses to continue. Direct the user to `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for guidance on improving each dimension.

   Present the assessment clearly:

   ```text
   Data Quality Assessment:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Source: CUSTOMERS_CRM
     Field completeness:  82%  (name: 99%, phone: 75%, email: 68%)
     Format consistency:  90%
     Duplicate rate:       3%
     Overall quality:     78%  ✅ Ready for mapping

   Source: VENDORS_LEGACY
     Field completeness:  45%  (name: 90%, phone: 20%, email: 15%)
     Format consistency:  55%
     Duplicate rate:      12%
     Overall quality:     42%  ⚠ Recommend fixing before mapping
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

   > **Agent instruction — Data Source Registry:** After computing the quality score, update the source's `quality_score` field in `config/data_sources.yaml` and set `updated_at`. If the score is below 70, add an `issues` list entry describing the quality concern.

   **Checkpoint:** Write step 6 to `config/bootcamp_progress.json`.

7. **Summarize findings and save evaluation report**: Create `docs/data_source_evaluation.md`:

   ```markdown
   # Data Source Evaluation Report

   **Date**: [Current date]
   **Project**: [Project name]

   ## Summary
   - Total data sources: [count]
   - Entity Specification-compliant: [count]
   - Needs mapping: [count]
   - Needs enrichment: [count]

   ## Data Source Details

   ### Data Source 1: [Name]
   **Status**: [Entity Specification-compliant / Needs mapping / Needs enrichment]
   **Location**: `data/raw/[filename]`
   **Records**: ~[count]
   **Fields**: [count] columns

   **Evaluation**:
   - [Field analysis]
   - [Entity Specification compliance notes]

   **Reason**: [Why it needs mapping or is compliant]

   **Next step**: [Phase 2 (mapping) / Module 6 (loading)]

   ### Data Source 2: [Name]
   [Same structure]

   ## Mapping Priority
   1. [Data source] - [Reason for priority]
   2. [Data source] - [Reason for priority]
   ```

### Quality Gate — Iterate vs. Proceed

After presenting the quality assessment, guide the user's decision:

- **Quality ≥80%:** "Your data quality is strong. Let's continue to mapping."
- **Quality 70-79%:** "Your data quality is acceptable but has some gaps. You can continue to mapping now — or if you'd like to improve the weakest fields first, we can work on that. See `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for details on what each dimension means. What would you prefer?"
- **Quality <70%:** "Your data quality needs attention before mapping will produce good results. I'd recommend focusing on [specific issues — e.g., filling missing phone numbers, standardizing address formats]. See `docs/guides/QUALITY_SCORING_METHODOLOGY.md` for a full breakdown of how scores are calculated and what to improve. Would you like to work on improving the data, or proceed anyway knowing the results may be limited?"

**Success indicator**: ✅ All data sources categorized + `docs/data_source_evaluation.md` created

**Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

---

## Phase 2 — Data Mapping

**Iterative process:** Users can jump between steps. Goal is a working transformation program, not strict sequence.

**Before starting:** Confirm which data source. Track multi-source progress (In Progress / Complete / Pending).

### Workflow (per data source)

1. **Start:** Call `mapping_workflow(action='start')` with source file from `data/raw/` or `data/samples/`. Override any `/tmp/` paths to project-local. Tell user: "Starting mapping for [source]. I'll walk through each step and explain what I find."

   > **Agent instruction — Data Source Registry:** Update the source's `mapping_status` to `in_progress` in `config/data_sources.yaml` and set `updated_at`.

   > **🔒 Agent Instruction — Per-Source Mapping Requirement**
   >
   > Each data source **must** complete its own full `mapping_workflow` run from start to finish. Do NOT reuse the mapping output, field mappings, or mapping specification from one source for another source — even if the schemas appear similar. Every source gets its own independent `mapping_workflow` execution and its own mapping specification markdown (`scripts/{source_name}_mapper.md`). Mapper code may be shared across sources if schemas are identical, but mapping documentation is always per-source.

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

2. **Profile:** Run profiler, summarize columns/types/completeness/quality. Advance with `action='profile_summary'`. **Tell user:** Present a table of columns with types, sample values, completeness %, and what each means for mapping (maps to Senzing / will skip / needs attention). Explain the key takeaway.

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

3. **Plan:** Identify entity type (person/org/both), structure (flat/nested), relationships. Advance with `action='entity_plan'`. **Tell user:** Explain entity type decision, which fields map vs. skip and why.

   **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

4. **Map:** Map fields to Senzing attributes via `mapping_workflow(action='schema_mappings')`. Never guess attribute names. For non-Latin data: `search_docs(query="globalization")`. **Tell user:** Show mapping table with reasoning for each decision and confidence score.

   **Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

5. **Generate starter code:** Advance with `action='paths'`. **Tell user:** Show a sample target JSON record so they see the output format.

   **Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

6. **Build transformation program:** Use `generate_scaffold` or mapping workflow output as foundation. Handle: input reading, field mapping, type conversion, cleansing, `DATA_SOURCE`/`RECORD_ID`, error handling. Save to `src/transform/transform_[name].[ext]`. **Tell user:** File path, what it reads/writes, what it handles.

   **Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

7. **Test:** Run on 10-100 records from `data/samples/`. Validate with `analyze_record`. **Tell user:** Pass/fail, output file path, sample record, any observations.

   **Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

8. **Quality analysis:** Run on 1000+ records. Evaluate feature distribution, coverage, quality scores. Advance with `action='verdict'`. **Tell user:** Overall score, per-feature coverage with what it means for matching, any issues found.

   **Offer visualization:** "Would you like me to create a web page showing the quality analysis? It'll have coverage charts and the field mapping summary." If yes, generate HTML and save to `docs/mapping_[name]_quality.html`.

   **Checkpoint:** Write step 15 to `config/bootcamp_progress.json`.

9. **Review:** Confirm with user: output format correct, quality acceptable, ready for production or needs adjustment.

   **Iterate vs. Proceed Decision Gate:** After presenting quality results, guide the decision:
   - **Quality ≥80% and all critical fields mapped:** "Quality looks strong. Ready to proceed to loading (Module 6)."
   - **Quality 70-79%:** "Quality is acceptable. You can proceed to loading now, or iterate to improve [specific weak areas]. What would you prefer?"
   - **Quality <70%:** "Quality needs improvement before loading will produce meaningful results. I'd recommend going back to [Step 2/3/4] to address [specific issues]. Would you like to iterate, or proceed knowing results may be limited?"

   **Checkpoint:** Write step 16 to `config/bootcamp_progress.json`.

10. **Iterate:** If issues found, go back to relevant step. Retest after changes.

    **Checkpoint:** Write step 17 to `config/bootcamp_progress.json`.

    > **Agent instruction — Data Source Registry:** Update the source's `mapping_status` to `complete` in `config/data_sources.yaml` and set `updated_at`. If a transformed file was created, update `file_path` to the `data/transformed/` output.

11. **Save and document:** Program in `src/transform/`, docs in `docs/mapping_[name].md` (field mappings, logic, quality, how to run), sample output in `data/transformed/[name]_sample.jsonl`. **Transformation lineage:** Have the bootcamper copy the transformation lineage template (#[[file:senzing-bootcamp/templates/transformation_lineage.md]]) to `docs/transformation_lineage_[name].md` and fill it in for this data source — covering source file info, transformation program, output file info, field mappings, format changes, filters, quality improvements, and before/after record counts.

    **Per-source mapping specification:** Save a mapping specification markdown to `scripts/{source_name}_mapper.md` for this data source. This file is always per-source, even when the transformation program is shared. Use the following structure:

    ```markdown
    # Mapping Specification: {SOURCE_NAME}

    **Source file:** data/raw/{source_file}
    **Data source name:** {DATA_SOURCE}
    **Entity type:** Person / Organization / Both
    **Generated by:** mapping_workflow

    ## Field Mappings

    | Source Field | Senzing Attribute | Transformation | Notes |
    |---|---|---|---|
    | ... | ... | ... | ... |

    ## Mapping Decisions

    - [Key decisions made during mapping]

    ## Quality Notes

    - [Quality observations specific to this source]
    ```

    **Checkpoint:** Write step 18 to `config/bootcamp_progress.json`.

12. **Repeat** for remaining data sources. Each gets its own transformation program.

    **Per-source completion checkpoint:** Before marking a source as complete, verify that `scripts/{source_name}_mapper.md` exists for that source. Do not proceed to the next source or mark the current source as done until its mapping specification markdown is saved. When all sources are mapped, confirm that every completed source has its own `scripts/{source_name}_mapper.md` file.

    **Checkpoint:** Write step 19 to `config/bootcamp_progress.json`.

13. **Transition** to Module 2 (SDK Setup) once all sources mapped.

    **Checkpoint:** Write step 20 to `config/bootcamp_progress.json`.

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

25. **Present results and decision gate:** Present the Phase 3 results summary for this data source. Include: records loaded, entities created, deduplication rate, quality assessment, and any issues found. Ask the bootcamper to review the results before proceeding.

    > **Agent instruction — Data Source Registry:** Update the source's `test_load_status` to `complete` and `test_entity_count` to the entity count from the test load in `config/data_sources.yaml`. Set `updated_at`.

    **Checkpoint:** Write step 25 to `config/bootcamp_progress.json`.

26. **Shortcut path decision:** After all sources have completed (or skipped) Phase 3, present the decision gate:

    - **Shortcut path (→ Module 7):** For simple use cases — single data source, small dataset (≤1000 records), no production requirements — the Phase 3 test load results may be sufficient. The bootcamper can proceed directly to Module 7 (Query & Visualize) and skip Module 6.
    - **Full path (→ Module 6):** For production requirements, multiple data sources, datasets exceeding 1000 records, or when the bootcamper wants to learn production-quality loading patterns — recommend the full Module 6 path.

    > **Agent instruction:** When the bootcamper chooses the shortcut path, update `config/bootcamp_progress.json` to mark Module 6 as skipped with reason `shortcut_path`:
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

## Interpreting `analyze_record` Results

If `analyze_record` returns structural errors (e.g., flat format instead of FEATURES array, missing required fields), it may also show an empty Feature Analysis table with headers but no rows. This is not a bug — feature analysis is skipped when structural errors prevent feature extraction. Tell the user: "The Feature Analysis table is empty because there are structural issues with the record format — let's fix those first, then the feature analysis will populate." Focus on the structural errors listed above the table, fix the transformation program, and re-validate.

## Encoding

- Detect encoding in profiling step. Convert to UTF-8 in transformation program.
- Non-Latin scripts: `search_docs(query="globalization", category="globalization")`
- Strip UTF-8 BOM from Windows CSV files. JSON libraries handle special character escaping.

## Workflow: Install Senzing Bootcamp Hooks

**Note**: Hooks are installed automatically during onboarding — no user action needed. The agent copies all `.kiro.hook` files from `senzing-bootcamp/hooks/` to `.kiro/hooks/` when the bootcamp starts. Hooks can also be reinstalled at any time by saying "install hooks" or running `python scripts/install_hooks.py`.
