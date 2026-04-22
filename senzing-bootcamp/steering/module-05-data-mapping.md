---
inclusion: manual
---

# Module 5: Data Mapping

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** `docs/modules/MODULE_5_DATA_MAPPING.md`

**Before/After:** Raw data Senzing can't read → transformation programs that convert to Senzing JSON, validated and ready to load.

**Iterative process:** Users can jump between steps. Goal is a working transformation program, not strict sequence.

**Before starting:** Confirm which data source. Track multi-source progress (In Progress / Complete / Pending).

**Prerequisites:** ✅ Module 3 complete (sources evaluated)

## Workflow (per data source)

1. **Start:** Call `mapping_workflow(action='start')` with source file from `data/raw/` or `data/samples/`. Override any `/tmp/` paths to project-local. Tell user: "Starting mapping for [source]. I'll walk through each step and explain what I find."

2. **Profile:** Run profiler, summarize columns/types/completeness/quality. Advance with `action='profile_summary'`. **Tell user:** Present a table of columns with types, sample values, completeness %, and what each means for mapping (maps to Senzing / will skip / needs attention). Explain the key takeaway.

3. **Plan:** Identify entity type (person/org/both), structure (flat/nested), relationships. Advance with `action='entity_plan'`. **Tell user:** Explain entity type decision, which fields map vs. skip and why. WAIT for confirmation.

4. **Map:** Map fields to Senzing attributes via `mapping_workflow(action='schema_mappings')`. Never guess attribute names. For non-Latin data: `search_docs(query="globalization")`. **Tell user:** Show mapping table with reasoning for each decision and confidence score. WAIT for confirmation.

5. **Generate starter code:** Advance with `action='paths'`. **Tell user:** Show a sample target JSON record so they see the output format.

6. **Build transformation program:** Use `generate_scaffold` or mapping workflow output as foundation. Handle: input reading, field mapping, type conversion, cleansing, `DATA_SOURCE`/`RECORD_ID`, error handling. Save to `src/transform/transform_[name].[ext]`. **Tell user:** File path, what it reads/writes, what it handles.

7. **Test:** Run on 10-100 records from `data/samples/`. Validate with `analyze_record`. **Tell user:** Pass/fail, output file path, sample record, any observations.

8. **Quality analysis:** Run on 1000+ records. Evaluate feature distribution, coverage, quality scores. Advance with `action='verdict'`. **Tell user:** Overall score, per-feature coverage with what it means for matching, any issues found.

   **Offer visualization:** "Would you like me to create a web page showing the quality analysis? It'll have coverage charts and the field mapping summary." If yes, generate HTML and save to `docs/mapping_[name]_quality.html`.

9. **Review:** Confirm with user: output format correct, quality acceptable, ready for production or needs adjustment.

   **Iterate vs. Proceed Decision Gate:** After presenting quality results, guide the decision:
   - **Quality ≥80% and all critical fields mapped:** "Quality looks strong. Ready to proceed to loading (Module 6)."
   - **Quality 70-79%:** "Quality is acceptable. You can proceed to loading now, or iterate to improve [specific weak areas]. What would you prefer?"
   - **Quality <70%:** "Quality needs improvement before loading will produce meaningful results. I'd recommend going back to [Step 2/3/4] to address [specific issues]. Would you like to iterate, or proceed knowing results may be limited?"
   WAIT for response.

10. **Iterate:** If issues found, go back to relevant step. Retest after changes.

11. **Save and document:** Program in `src/transform/`, docs in `docs/mapping_[name].md` (field mappings, logic, quality, how to run), sample output in `data/transformed/[name]_sample.jsonl`. **Transformation lineage:** Have the bootcamper copy `templates/transformation_lineage.md` to `docs/transformation_lineage_[name].md` and fill it in for this data source — covering source file info, transformation program, output file info, field mappings, format changes, filters, quality improvements, and before/after record counts.

12. **Repeat** for remaining data sources. Each gets its own transformation program.

13. **Transition** to Module 0 (SDK Setup) once all sources mapped.

## Mapping State Checkpointing

Save checkpoint to `config/mapping_state_[datasource].json` after each step:

```json
{"data_source":"CUSTOMERS","source_file":"data/raw/customers.csv","current_step":3,"completed_steps":["profile","plan","map"],"decisions":{"entity_type":"PERSON","field_mappings":{"full_name":"NAME_FULL"}},"last_updated":"2026-04-14T10:30:00Z"}
```

On session resume: read checkpoint, show user where they left off, restart `mapping_workflow`, fast-track through decided steps, resume from first incomplete step. Delete checkpoint when mapping complete.

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
