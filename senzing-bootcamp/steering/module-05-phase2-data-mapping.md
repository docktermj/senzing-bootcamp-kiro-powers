---
inclusion: manual
---
## Phase 2 — Data Mapping

**Iterative process:** Users can jump between steps. Goal is a working transformation program, not strict sequence.

**Before starting:** Confirm which data source. Track multi-source progress (In Progress / Complete / Pending).

### Mapping Verbosity Check

> **Agent instruction — before starting the mapping workflow:**
>
> Read `config/bootcamp_preferences.yaml` and check the `mapping_verbosity` key.
>
> - **If `mapping_verbosity` is `null` or absent:** Present the following question:
>
>   👉 "Before we start mapping, would you like **verbose mode** (I'll show each mapping step in detail — field detection, attribute selection rationale, transformation preview) or **concise mode** (I'll map quickly and show only the final mapped record and any warnings)?"
>
>   🛑 STOP — Wait for the bootcamper's answer. Persist their choice (`verbose` or `concise`) to `mapping_verbosity` in `config/bootcamp_preferences.yaml`.
>
>   If the bootcamper skips or doesn't answer directly: default to `verbose`, persist it, and say: "Defaulting to verbose mode — say 'switch to concise' anytime if you want less detail."
>
> - **If `mapping_verbosity` is already set to `verbose` or `concise`:** Say "Using your [verbose/concise] mapping preference from last time — say 'switch to [other]' if you'd prefer [less detail/more detail]" and proceed without waiting.

### Mid-Mapping Verbosity Switch

> **Agent instruction — honor verbosity changes at any point during the mapping workflow:**
>
> If the bootcamper says "switch to verbose", "switch to concise", "more detail", "less detail", or any natural variant indicating they want to change mapping verbosity:
>
> 1. Update `mapping_verbosity` in `config/bootcamp_preferences.yaml` to the requested mode (`verbose` or `concise`)
> 2. Apply the new mode immediately to all subsequent presentation output
> 3. Confirm briefly: "Switched to [verbose/concise] mode." — then continue the workflow without interruption

### Workflow (per data source)

1. **Start:** Call `mapping_workflow(action='start')` with source file from `data/raw/` or `data/samples/`. Override any `/tmp/` paths to project-local. Tell user: "Starting mapping for [source]. I'll walk through each step and explain what I find."

   > **Agent instruction — Data Source Registry:** Update the source's `mapping_status` to `in_progress` in `config/data_sources.yaml` and set `updated_at`.

   > **🔒 Agent Instruction — Per-Source Mapping Requirement**
   >
   > Each data source **must** complete its own full `mapping_workflow` run from start to finish. Do NOT reuse the mapping output, field mappings, or mapping specification from one source for another source — even if the schemas appear similar. Every source gets its own independent `mapping_workflow` execution and its own mapping specification markdown (`docs/{source_name}_mapper.md`). Mapper code may be shared across sources if schemas are identical, but mapping documentation is always per-source.

   **Checkpoint:** Write step 8 to `config/bootcamp_progress.json`.

2. **Profile:** Run profiler, summarize columns/types/completeness/quality. Advance with `action='profile_summary'`.

   > **Presentation (conditional on `mapping_verbosity`):**
   >
   > - **Verbose:** Present a full column table with types, sample values, completeness %, and what each means for mapping (maps to Senzing / will skip / needs attention). Explain the key takeaway.
   > - **Concise:** Present one summary line: N columns detected, X% overall completeness, and key issues only (e.g., "12 columns, 94% complete, 2 fields need attention").

   **Checkpoint:** Write step 9 to `config/bootcamp_progress.json`.

3. **Plan:** Identify entity type (person/org/both), structure (flat/nested), relationships. Advance with `action='entity_plan'`. **Tell user:** Explain entity type decision, which fields map vs. skip and why.

   > **Presentation (conditional on `mapping_verbosity`):**
   >
   > - **Verbose:** Explain the entity type decision and rationale. For each field, state whether it maps or is skipped and why (e.g., "phone maps to PHONE_NUMBER — standard contact attribute" / "internal_id skipped — no Senzing attribute match, not useful for resolution").
   > - **Concise:** State the entity type and a count of mapped vs. skipped fields without per-field rationale (e.g., "Entity type: Person. 8 fields mapped, 3 skipped.").

   **Checkpoint:** Write step 10 to `config/bootcamp_progress.json`.

4. **Map:** Map fields to Senzing attributes via `mapping_workflow(action='schema_mappings')`. Never guess attribute names. For non-Latin data: `search_docs(query="globalization")`. **Tell user:** Show mapping table with reasoning for each decision and confidence score.

   > **Presentation (conditional on `mapping_verbosity`):**
   >
   > - **Verbose:** Show the full mapping table with a rationale column explaining the reasoning for each mapping decision and a confidence score per field (e.g., "first_name → NAME_FIRST — standard given name field, confidence: high").
   > - **Concise:** Show the mapping table with source field → Senzing attribute only, no rationale column or confidence scores (e.g., "first_name → NAME_FIRST").

   **Checkpoint:** Write step 11 to `config/bootcamp_progress.json`.

5. **Generate starter code:** Advance with `action='paths'`. **Tell user:** Show a sample target JSON record so they see the output format.

   > **Presentation (conditional on `mapping_verbosity`):**
   >
   > - **Verbose:** Show a sample target JSON record with annotations explaining the structure (e.g., which fields became which Senzing attributes, how DATA_SOURCE and RECORD_ID are set, nested vs. flat layout).
   > - **Concise:** State the output file path and format only (e.g., "Output: data/transformed/customers.jsonl — one JSON record per line").

   **Checkpoint:** Write step 12 to `config/bootcamp_progress.json`.

   > **Agent instruction — Organize mapping output files:**
   >
   > After `mapping_workflow` generates output files into the workspace directory,
   > run the organizer script to sort them into the correct project subdirectories:
   >
   > ```bash
   > python3 senzing-bootcamp/scripts/organize_mapping_files.py \
   >   --source <workspace_dir> \
   >   --project-root <bootcamper_project_root>
   > ```
   >
   > Where `<workspace_dir>` is the directory passed to `mapping_workflow` as
   > `workspace_dir` and `<bootcamper_project_root>` is the bootcamper's project
   > root directory. Review the output summary to confirm files landed correctly.

6. **Build transformation program:** Use `generate_scaffold` or mapping workflow output as foundation. Handle: input reading, field mapping, type conversion, cleansing, `DATA_SOURCE`/`RECORD_ID`, error handling. Save to `src/transform/transform_[name].[ext]`. **Tell user:** File path, what it reads/writes, what it handles.

   **Checkpoint:** Write step 13 to `config/bootcamp_progress.json`.

7. **Test:** Run on 10-100 records from `data/samples/`. Validate with `analyze_record`. **Tell user:** Pass/fail, output file path, sample record, any observations.

   > **Presentation (conditional on `mapping_verbosity`):**
   >
   > - **Verbose:** Show pass/fail result, the output file path, a sample transformed record, and any observations about the test run (e.g., warnings, skipped records, format issues).
   > - **Concise:** Show pass/fail result and the output file path only (e.g., "✅ Pass — output: data/transformed/customers_sample.jsonl").

   **Checkpoint:** Write step 14 to `config/bootcamp_progress.json`.

8. **Quality analysis:** Run on 1000+ records. Evaluate feature distribution, coverage, quality scores. Advance with `action='verdict'`. **Tell user:** Overall score, per-feature coverage with what it means for matching, any issues found.

   > **Presentation (conditional on `mapping_verbosity`):**
   >
   > - **Verbose:** Show the overall quality score, per-feature coverage breakdown with matching implications (e.g., "NAME coverage 98% — strong for matching" / "ADDR coverage 42% — may reduce match accuracy"), and all issues found with explanations.
   > - **Concise:** Show the overall quality score, a count of mapped vs. unmapped fields, and warnings only (e.g., "Quality: 85/100. 8 mapped, 3 unmapped. ⚠️ Low address coverage may affect matching.").

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

    **Per-source mapping specification:** Save a mapping specification markdown to `docs/{source_name}_mapper.md` for this data source. This file is always per-source, even when the transformation program is shared. Use the following structure:

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

    > **🚫 MANDATORY GATE — Do NOT Write Module Completion Checkpoint Until This Passes:**
    >
    > **BEFORE writing the module completion checkpoint:** List ALL files in `data/transformed/` and verify that EACH has a corresponding `docs/{source_name}_mapper.md`. If any are missing, create them NOW. Do NOT write the module completion checkpoint until all mapping specs exist. This is a hard requirement — the module is not complete without per-source mapping specifications for every transformed data source.

    **Per-source completion checkpoint:** Before marking a source as complete, verify that `docs/{source_name}_mapper.md` exists for that source. Do not proceed to the next source or mark the current source as done until its mapping specification markdown is saved. When all sources are mapped, confirm that every completed source has its own `docs/{source_name}_mapper.md` file.

    **Checkpoint:** Write step 19 to `config/bootcamp_progress.json`.

13. **Transition** to Module 2 (SDK Setup) once all sources mapped.

    **Checkpoint:** Write step 20 to `config/bootcamp_progress.json`.

---
