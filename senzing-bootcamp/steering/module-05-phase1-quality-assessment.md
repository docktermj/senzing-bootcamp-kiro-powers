---
inclusion: manual
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

3. **Understand the Senzing Generic Entity Specification**: Call `download_resource(filename="senzing_entity_specification.md")` to retrieve the current Senzing Generic Entity Specification. Use this as the authoritative reference for all attribute names, types, and structures in this step and subsequent steps.

   **Checkpoint:** Write step 3 to `config/bootcamp_progress.json`.

4. **Compare each data source with the Entity Specification**: Using the Entity Specification retrieved in Step 3 as the reference, compare each data source's fields against the specification's attribute names. For each data source provided:
   - Identify which fields map directly to attributes defined in the Entity Specification
   - Identify fields that need transformation (e.g., combining or splitting fields to match the specification's expected structure)
   - Identify fields with non-standard names that correspond to attributes in the Entity Specification
   - Note any missing critical fields defined in the Entity Specification
   - Check if `DATA_SOURCE` and `RECORD_ID` are present or can be derived

   **Checkpoint:** Write step 4 to `config/bootcamp_progress.json`.

5. **Categorize each data source** (using the Entity Specification retrieved in Step 3 as the source of truth for what constitutes compliant attribute names):
   - **Entity Specification-compliant**: Data already uses attribute names and structures that match the Entity Specification. Can proceed directly to Module 2 (SDK setup) and Module 6 (loading).
   - **Needs mapping**: Data uses different field names or structures than those defined in the Entity Specification. Continue to Phase 2 (data mapping) below.
   - **Needs enrichment**: Data is missing critical attributes. Discuss with user whether additional data sources can provide missing information.

   **Checkpoint:** Write step 5 to `config/bootcamp_progress.json`.

5a. **CORD Readiness Check and Fast-Path Offer** (CORD sources only):

   > **Agent instruction — CORD Fast-Path Assessment:**
   >
   > For each source where `provenance` is `cord` in `config/data_sources.yaml`
   > (that is, a source obtained via the `get_sample_data` MCP tool in Module 4):
   >
   > 1. **Obtain the Senzing schema definition**: Reuse the Senzing Generic Entity
   >    Specification already retrieved in Step 3 of this phase — do not download it
   >    again. From that same MCP-sourced specification, extract the list of required
   >    top-level structural indicators for a Senzing-loadable record (e.g., presence
   >    of FEATURES array, DATA_SOURCE, RECORD_ID).
   >
   > 2. **Perform the Readiness Check**: Examine up to 100 sample records from the
   >    source file. For each record, verify:
   >    - The record is valid JSON
   >    - The record contains the structural indicators identified from the Entity
   >      Specification (top-level keys, array structures)
   >    - DATA_SOURCE and RECORD_ID are present or derivable
   >
   >    If ALL sampled records pass, classify as Senzing_Ready.
   >    If ANY sampled record fails, classify as not Senzing_Ready.
   >
   >    Optionally, use the helper script:
   >
   >    ```bash
   >    python senzing-bootcamp/scripts/check_cord_readiness.py \
   >      --file <source_file_path> \
   >      --schema-keys DATA_SOURCE,RECORD_ID,FEATURES \
   >      --max-records 100
   >    ```
   >
   > 3. **Record the result**: Set the source's `senzing_ready` field in
   >    `config/data_sources.yaml` to `true` or `false` and update `updated_at`.
   >
   > 4. **If Senzing_Ready — Present the Fast-Path offer:**
   >
   >    👉 **"Your CORD source [SOURCE_NAME] is already in Senzing-loadable form
   >    (it has the correct JSON structure with DATA_SOURCE, RECORD_ID, and
   >    properly structured features). Would you like to skip the mapping phase
   >    and proceed directly to loading in Module 6?"**
   >
   >    🛑 STOP — Wait for the bootcamper's answer.
   >
   >    - **If confirmed**: Set `mapping_status: complete` and `fast_pathed: true`
   >      in the registry. Keep `file_path` pointing at the original `data/raw/`
   >      file. Record a data-lineage entry (see the **Fast-Path Data-Lineage
   >      Entry** instruction below). Route the source to Module 6.
   >    - **If declined**: Continue through the normal quality assessment and
   >      mapping workflow for this source.
   >
   > 5. **If NOT Senzing_Ready or MCP unavailable**: Continue through the normal
   >    quality assessment and mapping workflow. Do NOT present the fast-path offer.
   >
   > 6. **Non-CORD sources**: Skip this step entirely. Never present the fast-path
   >    offer for sources with provenance other than `cord`.

   > **Agent instruction — Fast-Path Data-Lineage Entry:**
   >
   > Record a data-lineage entry ONLY for a source that was explicitly
   > fast-pathed (the bootcamper confirmed the offer above). Never record a
   > fast-path lineage entry for a source that went through normal mapping or
   > that was never offered the fast-path.
   >
   > Add the entry to the `transformations` section of `docs/data_lineage.yaml`,
   > keyed by the source's DATA_SOURCE name. Because no transformation occurred,
   > the entry records the original `data/raw/` file as both input and output
   > with equal record counts:
   >
   > ```yaml
   > transformations:
   >   CORD_LAS_VEGAS:
   >     source_file: data/raw/cord-las-vegas.jsonl
   >     transformation_script: null  # No transformation — fast-pathed
   >     output_file: data/raw/cord-las-vegas.jsonl  # Same file
   >     records_in: 8421
   >     records_out: 8421
   >     records_rejected: 0
   >     quality_score: null  # Quality assessment skipped
   >     fast_pathed: true
   >     fast_path_reason: "CORD source already in Senzing-loadable form"
   > ```
   >
   > **Invariants** — every fast-path lineage entry MUST satisfy:
   >
   > - `source_file == output_file` (the original `data/raw/` file, unchanged)
   > - `records_in == records_out` (equal before-and-after record counts)
   > - `records_rejected: 0`
   > - `transformation_script: null`
   > - `fast_pathed: true`
   >
   > **Non-blocking:** If writing the data-lineage entry fails, allow the
   > fast-path to proceed anyway — route the source to Module 6 and log the
   > lineage failure so it can be retried later. A lineage write failure MUST
   > NOT block the fast-path.

   **Checkpoint:** Write step 5a to `config/bootcamp_progress.json`.

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

   **Visualization checkpoint:** Follow the Visualization Protocol.
   Load `visualization-guide.md` and execute the offer for checkpoint `m5_quality_assessment`.

7. **Summarize findings and save evaluation report**: Create `docs/data_source_evaluation.md`:

   ```markdown
   # Data Source Evaluation Report

   **Date:** [Current date]
   **Project:** [Project name]

   ## Summary
   - Total data sources: [count]
   - Entity Specification-compliant: [count]
   - Needs mapping: [count]
   - Needs enrichment: [count]

   ## Data Source Details

   ### Data Source 1: [Name]
   **Status:** [Entity Specification-compliant / Needs mapping / Needs enrichment]
   **Location:** `data/raw/[filename]`
   **Records:** ~[count]
   **Fields:** [count] columns

   **Evaluation:**
   - [Field analysis]
   - [Entity Specification compliance notes]

   **Reason:** [Why it needs mapping or is compliant]

   **Next step:** [Phase 2 (mapping) / Module 6 (loading)]

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

**Success indicator:** ✅ All data sources categorized + `docs/data_source_evaluation.md` created

**Checkpoint:** Write step 7 to `config/bootcamp_progress.json`.

---
