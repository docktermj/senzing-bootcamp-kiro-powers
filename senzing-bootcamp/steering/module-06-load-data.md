---
inclusion: manual
---


# Module 6: Load Data

**🚀 First:** Read `config/bootcamp_progress.json` and follow `module-transitions.md` — display the module start banner, journey map, and before/after framing before proceeding.

> **User reference:** For detailed background on this module, see `docs/modules/MODULE_6_LOAD_DATA.md`.

**Purpose:** Build production-quality loading programs, load all data sources into Senzing, process redo records, and validate entity resolution results — from first load through cross-source validation.

**Before/After:** You have Senzing-formatted JSON files (and possibly test load results from Module 5 Phase 3). After this module, all your data is loaded, redo records are processed, and entity resolution results are validated — duplicates matched, cross-source connections found.

**Prerequisites:** Module 5 complete (at least one transformed data source in `data/transformed/`), SDK installed and configured (Module 2), database configured (SQLite or PostgreSQL), transformation validated with linter.

## Conditional Workflow: Check Phase 3 Status

> **Agent instruction:** Before starting any loading, read `config/data_sources.yaml` and check the `test_load_status` field for each data source.
>
> - **If `test_load_status: complete`** — Phase 3 was completed in Module 5. Acknowledge the test load results: "You already test-loaded this source in Module 5 Phase 3 and saw [entity_count] entities. Module 6 builds on those results with production-quality loading — error handling, progress tracking, throughput optimization, redo processing, and incremental loading strategies." Skip the basic test loading steps and proceed directly to the production loading workflow below.
> - **If `test_load_status: skipped` or missing** — Phase 3 was not completed. Include a brief test load step: run `mapping_workflow` steps 5–8 (or a quick manual load of 10–100 records) to verify the data loads correctly before proceeding to production concerns. Update `test_load_status` to `complete` after the test load succeeds.
>
> Also check for anti-patterns before starting: `search_docs(query="loading", category="anti_patterns", version="current")`.

> **Agent instruction — Phase 3 Results Integration:** Read `config/data_sources.yaml` and check `test_load_status` and `test_entity_count` for each source. If Phase 3 was completed for multiple sources, reference the test load results when planning load order and dependency management:
>
> - Use `test_entity_count` values to estimate total entity volume and plan resource allocation
> - Use quality assessments from Phase 3 to inform which sources to load first (higher quality → stronger entity baseline)
> - Note any issues discovered during Phase 3 test loading that may affect production orchestration

## Pre-Load Data Freshness Check

> **Agent instruction:** Before starting any loading workflow, run the CORD data freshness check to verify data files haven't changed since download (CORD data is downloaded via `get_sample_data`).
>
> Run: `python senzing-bootcamp/scripts/cord_metadata.py check`
>
> Handle the result based on the output:
>
> - **Fresh** (output contains "✅"): Tell the bootcamper "Your CORD data is up to date — proceeding with loading." and continue to the next section.
> - **Stale** (output contains "⚠️"): Present the warning to the bootcamper exactly as shown in the output, including the three options: (a) re-download fresh data via `get_sample_data`, (b) proceed with current files, (c) check what changed. Wait for the bootcamper to choose before proceeding. This is advisory only — never block loading regardless of their choice.
> - **Skipped** (no metadata found, or output mentions "Skipping"): Proceed silently without mentioning freshness to the bootcamper. This means either the bootcamper is using their own data (not CORD) or metadata was not captured during Module 4.

## Agent Workflow

> **Agent instruction:** Before starting, call `search_docs(query="loading", category="anti_patterns", version="current")`. Key pitfalls: bulk loading issues, threading problems, redo processing, load order dependencies.

**Success indicator:** ✅ All data sources loaded into Senzing + redo records processed + no critical errors + entity resolution results validated

---

## Error Handling

When the bootcamper encounters an error during this module:

1. **Check for SENZ error code** — if the error message contains a code matching `SENZ` followed by digits (e.g., `SENZ2027`):
   - Call `explain_error_code(error_code="<code>", version="current")`
   - Present the explanation and recommended fix to the bootcamper
   - If `explain_error_code` returns no result, continue to step 2
2. **Load `common-pitfalls.md`** — navigate to this module's section and present only the matching pitfall and fix
3. **Check cross-module resources** — if no match in the module section, check the Troubleshooting by Symptom table and General Pitfalls section

## Phase Sub-Files

- **Phase A: Build Loading Program** (steps 1–3): `module-06-phaseA-build-loading.md`
- **Phase B: Load First Source** (steps 4–10): `module-06-phaseB-load-first-source.md`
- **Phase C: Multi-Source Orchestration (Conditional — 2+ Data Sources)** (steps 11–19): `module-06-phaseC-multi-source.md`
- **Phase D: Validation** (steps 20–27): `module-06-phaseD-validation.md`

## Advanced Reading

> **After completing Module 6**, ask the agent about record updates, deletions, entity re-evaluation, and redo processing — the agent will use `search_docs` and `get_sdk_reference` to provide current guidance relevant for production systems where source data changes over time.

> For production systems that receive ongoing data, ask the agent about incremental loading patterns — the agent will use `search_docs` and `generate_scaffold` to provide current guidance on adding new records to an existing database, processing redo records after incremental loads, and monitoring pipeline health over time.
