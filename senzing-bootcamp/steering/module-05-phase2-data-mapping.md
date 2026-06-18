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
   > Each data source **must** complete its own full `mapping_workflow` run from start to finish. Do NOT reuse the mapping output, field mappings, or mapping specification from one source for another source — even if the schemas appear similar. Every source gets its own independent `mapping_workflow` execution and its own mapping specification markdown (`docs/mapping/{source_name}_mapper.md`). Mapper code may be shared across sources if schemas are identical, but mapping documentation is always per-source.

   > **Agent instruction — Organize downloaded resources immediately after download:**
   >
   > As soon as `mapping_workflow(action='start')` finishes downloading its
   > workflow resources into the workspace directory — and **before any further
   > mapping work proceeds** (profiling, planning, mapping) — run the organizer
   > to relocate the just-downloaded reusable resources (the workflow `.py`
   > scripts and the reference `.md`/`.json` files) to their policy-correct
   > project locations:
   >
   > ```bash
   > python3 senzing-bootcamp/scripts/organize_mapping_files.py \
   >   --source <workspace_dir> \
   >   --project-root <bootcamper_project_root>
   > ```
   >
   > Where `<workspace_dir>` is the directory passed to `mapping_workflow` as
   > `workspace_dir` and `<bootcamper_project_root>` is the bootcamper's project
   > root directory.
   >
   > Review the organizer summary output to confirm files landed at the expected
   > locations: `.py` scripts → `src/`, the entity specification
   > (`senzing_entity_specification.md`) → `docs/reference/`, and reference
   > `.md`/`.json` files → their policy-correct homes. Only then continue with
   > the rest of the mapping workflow.

   > **Agent instruction — Rely on the organizer's existing routing; handle
   > unrouted files and blocked writes gracefully:**
   >
   > This guidance relies entirely on the organizer's **existing routing rules**
   > to place reusable resources. Do **NOT** introduce alternative placement
   > destinations or force a file to a location the organizer did not choose —
   > the organizer already routes each file to its policy-correct home (`.py` →
   > `src/`, the entity specification → `docs/reference/`, non-README `.md` →
   > `docs/`, data → `data/`, config JSON → `config/`).
   >
   > When reviewing the organizer summary, handle these two cases by deferring to
   > the summary rather than overriding the outcome:
   >
   > - **Unrouted files:** If a downloaded file matches no routing rule, the
   >   organizer leaves it in `<workspace_dir>` and reports it as a warning in the
   >   summary. Surface that warning to the bootcamper and leave the file where it
   >   is — do **NOT** invent a destination for it.
   > - **Blocked writes:** If the `write-policy-gate` blocks a write during the
   >   organize step, the organizer leaves the affected file in `<workspace_dir>`
   >   and reports the blocked destination as an error in the summary. Treat this
   >   as a signal to review the summary — do **NOT** retry the write against a
   >   different location to force the file through.
   >
   > In both cases the file simply stays in `<workspace_dir>`; review the summary
   > and report the outcome rather than working around the organizer.

   > **Agent instruction — Leave transient run artifacts in the workspace:**
   >
   > The post-download organizer relocates only the **reusable resources** that
   > exist at download time. Later steps (profiling, planning, mapping,
   > transformation) produce **transient run artifacts** that the workflow reads
   > and writes for its own use during the run. These are NOT reusable resources
   > and must stay in `<workspace_dir>`:
   >
   > - `profile_report.md`
   > - `schema_hints.md`
   > - `JOURNAL.md`
   > - generated JSONL output
   >
   > While the `mapping_workflow` run is in progress, do **NOT** relocate, delete,
   > or redirect these transient artifacts out of `<workspace_dir>` — the workflow
   > needs them in place to keep functioning. Because they are produced *after*
   > the post-download organize step, they are not present when the organizer runs
   > and are therefore left untouched in the workspace by design.

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

   > **Agent instruction — Availability-aware mapping validation (Step 4):**
   >
   > `mapping_workflow` advertises three validation scripts. Run them by availability — do NOT treat any one of them as a hard blocking gate that the bootcamper cannot clear.
   >
   > 1. **`sz_json_analyzer.py` (primary validation):** This is the primary mapping validation — structural + Entity-Specification validation — and is currently hosted (HTTP 200). When it is available, run it and use its result as the authoritative check. It is **sufficient to proceed**: when the verbatim/routing scripts below are unavailable, a passing `sz_json_analyzer.py` result lets you continue the mapping workflow.
   >
   > 2. **`sz_verbatim_check.py` (verbatim-fidelity, optional/best-effort):**
   >    - **If available:** run the verbatim-fidelity check as before and report its result.
   >    - **If unavailable** (HTTP 404 / no working inline fallback): tell the bootcamper the verbatim-fidelity check is being **skipped because the script is unavailable**, treat it as **optional/best-effort**, and **proceed** — do NOT block on it.
   >
   > 3. **`sz_routing_report.py` (routing-coverage, optional/best-effort):**
   >    - **If available:** run the routing-coverage report as before and report its result.
   >    - **If unavailable** (HTTP 404 / no working inline fallback): tell the bootcamper the routing-coverage report is being **skipped because the script is unavailable**, treat it as **optional/best-effort**, and **proceed** — do NOT block on it.
   >
   > In short: anchor validation on `sz_json_analyzer.py`; degrade the verbatim and routing checks to optional/best-effort when their scripts are unavailable, and never leave the bootcamper blocked at Step 4 because of a 404.

   > **Agent instruction — Step 5 `detect_environment` menu handling (after Step 4 approval):**
   >
   > After a source's mapping is approved at Step 4, `mapping_workflow` returns Step 5 (`detect_environment`) with a four-option menu. Do NOT stop here — explain the menu and relay a recommendation so the bootcamper never hits a dead end.
   >
   > **Steps 5–8 are optional sandbox validation.** They let you trial-load the mapped source into a throwaway sandbox to preview entity resolution. They are NOT the production load — the real load happens in **Module 6**. The four `detect_environment` options are:
   >
   > - **skip** — skip the per-source sandbox test load and move on. **Recommended when one or more unmapped sources remain.**
   > - **test_load** — run the optional sandbox test load (enters Phase 3, Steps 5–8) for this source.
   > - **load+resolve** — run the optional sandbox test load and resolve entities (enters Phase 3, Steps 5–8) for this source.
   > - **done** — finish the mapping workflow for this source without a sandbox test load.
   >
   > **Multi-source continuation (recommended path):** When one or more unmapped data sources remain, recommend the **skip** option — note that the real load is deferred to **Module 6**, so a per-source sandbox test load adds little here — and automatically continue to the next unmapped source by starting its own `mapping_workflow` run. Tell the bootcamper: "Steps 5–8 are an optional sandbox preview; since you still have sources to map and the real load happens in Module 6, I'll skip the per-source test load and move on to the next unmapped source."
   >
   > **Explicit choice is preserved:** If the bootcamper explicitly chooses **test_load** or **load+resolve**, follow that path into Phase 3 (Steps 5–8) unchanged — see #[[file:senzing-bootcamp/steering/module-05-phase3-test-load.md]]. The real production load still happens in Module 6 regardless.

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

   > **Agent instruction — Refresh the docs index:**
   >
   > After running the organizer, regenerate the documentation index so the
   > bootcamper's `docs/README.md` lists every document under `docs/`:
   >
   > ```bash
   > python3 senzing-bootcamp/scripts/generate_docs_index.py \
   >   --project-root <bootcamper_project_root>
   > ```
   >
   > This creates or refreshes `docs/README.md`. Regenerate the index whenever
   > documents are added across modules so it stays current.

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

   **Offer visualization:** "Would you like me to create a web page showing the quality analysis? It'll have coverage charts and the field mapping summary." If yes, generate HTML and save to `docs/mapping/mapping_[name]_quality.html`.

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

11. **Save and document:** Program in `src/transform/`, docs in `docs/mapping/mapping_[name].md` (field mappings, logic, quality, how to run), sample output in `data/transformed/[name]_sample.jsonl`. **Transformation lineage:** Have the bootcamper copy the transformation lineage template (#[[file:senzing-bootcamp/templates/transformation_lineage.md]]) to `docs/mapping/transformation_lineage_[name].md` and fill it in for this data source — covering source file info, transformation program, output file info, field mappings, format changes, filters, quality improvements, and before/after record counts.

    **Entity specification reference:** The Senzing entity specification reference is written only to `docs/reference/senzing_entity_specification.md` — a single canonical copy. Do NOT create a copy in the `docs/` root; if one already exists there, remove it (or leave it to the organizer's dedup pass, which keeps the single `docs/reference/` copy).

    **Per-source mapping specification:** Save a mapping specification markdown to `docs/mapping/{source_name}_mapper.md` for this data source. This file is always per-source, even when the transformation program is shared. Use the following structure:

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
    > **BEFORE writing the module completion checkpoint:** List ALL files in `data/transformed/` and verify that EACH has a corresponding `docs/mapping/{source_name}_mapper.md`. If any are missing, create them NOW. Do NOT write the module completion checkpoint until all mapping specs exist. This is a hard requirement — the module is not complete without per-source mapping specifications for every transformed data source.

    **Per-source completion checkpoint:** Before marking a source as complete, verify that `docs/mapping/{source_name}_mapper.md` exists for that source. Do not proceed to the next source or mark the current source as done until its mapping specification markdown is saved. When all sources are mapped, confirm that every completed source has its own `docs/mapping/{source_name}_mapper.md` file.

    **Checkpoint:** Write step 19 to `config/bootcamp_progress.json`.

13. **Transition** to Module 2 (SDK Setup) once all sources mapped.

    **Checkpoint:** Write step 20 to `config/bootcamp_progress.json`.

---
