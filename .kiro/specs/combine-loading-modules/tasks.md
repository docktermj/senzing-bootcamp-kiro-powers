# Tasks: Combine Loading Modules

## Task 1: Create Combined Loading Steering File
- [x] 1.1 Create `senzing-bootcamp/steering/module-06-load-data.md` with YAML frontmatter (`inclusion: manual`)
- [x] 1.2 Add module header with start banner instructions, progress file read, and module-transitions reference
- [x] 1.3 Add Before/After framing: "You have Senzing-formatted JSON files. After this module, all your data is loaded, redo records are processed, and entity resolution results are validated."
- [x] 1.4 Add Phase A: Build Loading Program — instructions to use `generate_scaffold` with `add_records` workflow, anti-pattern check, data source registry update, and program save to `src/load/`
- [x] 1.5 Add Phase B: Load First Source — test with sample data (10-100 records), observe entity resolution, load full dataset, SQLite performance note (≤1,000 records), save loading program, process redo queue after loading
- [x] 1.6 Add Phase C (conditional, 2+ sources): Multi-Source Orchestration — inventory all data sources from `config/data_sources.yaml`, analyze dependencies, determine load order (reference before transactional, quality-first, attribute-density-first, volume-first), select loading strategy (sequential/parallel/hybrid), pre-load validation checklist, create orchestrator program, test with sample data, run full orchestration, process redo queue after each source
- [x] 1.7 Add Phase D: Validation — single-source match accuracy review, false positive/negative review, single-source UAT; then conditional cross-source validation (only when 2+ sources): cross-source match accuracy, cross-source UAT with business users, stakeholder sign-off, mandatory visualization offer
- [x] 1.8 Add conditional logic to check whether Module 5 Phase 3 (mapping-workflow-integration) was completed by reading `test_load_status` from `config/data_sources.yaml`; if completed, skip basic test loading; if not completed or field missing, include full loading workflow
- [x] 1.9 Add checkpoint instructions (`config/bootcamp_progress.json`) at every numbered step, continuing sequential step numbering
- [x] 1.10 Add Recovery from Failed Load section with wipe-and-restart, resume-from-checkpoint, and database restore options (preserved from old Module 6)
- [x] 1.11 Add Iterate vs. Proceed Decision Gate (preserved from old Module 7) with UAT threshold guidance
- [x] 1.12 Add inline Reference Material section preserving source ordering heuristics (Customer 360 quality-first, Compliance screening reference-first), orchestration patterns (sequential, parallel, dependency-aware, pipeline), error handling strategies (fail fast, continue on error, retry with backoff, partial success), conflict resolution guidance, and troubleshooting quick reference from old `module-07-reference.md` — with agent instruction to only present multi-source reference material when bootcamper has 2+ data sources
- [x] 1.13 Add Success Criteria section combining old Module 6 and Module 7 criteria
- [x] 1.14 Add Stakeholder Summary offer referencing `templates/stakeholder_summary.md`

## Task 2: Create Combined Loading Module Documentation
- [x] 2.1 Create `senzing-bootcamp/docs/modules/MODULE_6_LOAD_DATA.md` with module banner and overview describing the complete data loading lifecycle
- [x] 2.2 Add combined learning objectives from old Module 6 (building loading programs, loading records, error handling, progress tracking, redo processing) and old Module 7 (dependency management, load order optimization, cross-source matching, UAT)
- [x] 2.3 Add conditional workflow documentation: single-source path (no orchestration or cross-source steps) and multi-source path (includes dependency analysis, load ordering, cross-source validation)
- [x] 2.4 Add Key Concepts section covering data sources, record IDs, entities, redo queue, orchestration patterns
- [x] 2.5 Add combined Validation Gates checklist merging old Module 6 and Module 7 gates
- [x] 2.6 Add Output Files section documenting all artifacts (loading programs, statistics, validation results, UAT results, orchestration strategy)
- [x] 2.7 Add File Location Map showing where loading programs, logs, statistics, and validation documents are saved
- [x] 2.8 Add reference to mapping-workflow-integration Phase 3 shortcut path explaining how it interacts with the combined loading module
- [x] 2.9 Add note that standalone functionality works without Phase 3 conditional logic if mapping-workflow-integration is not implemented

## Task 3: Remove Old Module 6 and Module 7 Files
- [x] 3.1 Remove `senzing-bootcamp/steering/module-06-single-source.md`
- [x] 3.2 Remove `senzing-bootcamp/steering/module-07-multi-source.md`
- [x] 3.3 Remove `senzing-bootcamp/steering/module-07-reference.md` (content incorporated into combined steering file Task 1.12)
- [x] 3.4 Remove `senzing-bootcamp/docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md`
- [x] 3.5 Remove `senzing-bootcamp/docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`

## Task 4: Rename Steering Files (Modules 8–12 → 7–11)
- [x] 4.1 Rename `steering/module-08-query-validation.md` → `steering/module-07-query-validation.md` and update internal module number references (e.g., "Module 8" → "Module 7") and cross-references to other renumbered modules
- [x] 4.2 Rename `steering/module-09-performance.md` → `steering/module-08-performance.md` and update internal references
- [x] 4.3 Rename `steering/module-10-security.md` → `steering/module-09-security.md` and update internal references
- [x] 4.4 Rename `steering/module-11-monitoring.md` → `steering/module-10-monitoring.md` and update internal references
- [x] 4.5 Rename `steering/module-12-deployment.md` → `steering/module-11-deployment.md` and update internal references

## Task 5: Rename Module Documentation Files (Modules 8–12 → 7–11)
- [x] 5.1 Rename `docs/modules/MODULE_8_QUERY_VALIDATION.md` → `docs/modules/MODULE_7_QUERY_VALIDATION.md` and update internal module number references and cross-references
- [x] 5.2 Rename `docs/modules/MODULE_9_PERFORMANCE_TESTING.md` → `docs/modules/MODULE_8_PERFORMANCE_TESTING.md` and update internal references
- [x] 5.3 Rename `docs/modules/MODULE_10_SECURITY_HARDENING.md` → `docs/modules/MODULE_9_SECURITY_HARDENING.md` and update internal references
- [x] 5.4 Rename `docs/modules/MODULE_11_MONITORING_OBSERVABILITY.md` → `docs/modules/MODULE_10_MONITORING_OBSERVABILITY.md` and update internal references
- [x] 5.5 Rename `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` → `docs/modules/MODULE_11_DEPLOYMENT_PACKAGING.md` and update internal references

## Task 6: Update POWER.md
- [x] 6.1 Update overview text from "12-module curriculum (Modules 1-12)" to "11-module curriculum (Modules 1-11)"
- [x] 6.2 Update description field in YAML frontmatter from "12-module" to "11-module"
- [x] 6.3 Replace separate Module 6 and Module 7 rows in the "What This Bootcamp Does" table with a single row: "6 — Load Data | Loads all data sources, processes redo records, and validates entity resolution results | Your data is loaded and entity resolution is running — duplicates matched, cross-source connections found"
- [x] 6.4 Renumber old Modules 8–12 to 7–11 in the "What This Bootcamp Does" table
- [x] 6.5 Update Quick Start track descriptions: Track B → "Modules 5 → 6 → 7", Track C → "Modules 1 → 4 → 5 → 6 → 7", Track D → "All modules 1-11"
- [x] 6.6 Update skip-ahead guidance: remove "single source (skip 7)", update "not deploying to production (skip 8-11)" from old "skip 9-12"
- [x] 6.7 Update "Available Steering Files" module workflow list to reflect combined module and renumbered files
- [x] 6.8 Update "Bootcamp Modules" table to show 11 modules with combined Module 6 and renumbered 7–11
- [x] 6.9 Update "Advanced Topics" section: change `module-07-reference.md` reference to note content is now in `module-06-load-data.md`
- [x] 6.10 Update MCP Server Configuration section if it references module numbers
- [x] 6.11 Update any other references to "Module 7", "Module 8", etc. throughout POWER.md to use new numbering

## Task 7: Update Steering Index
- [x] 7.1 Remove entries for keys `6` and `7` in the `modules` section of `steering-index.yaml`
- [x] 7.2 Add entry `6: module-06-load-data.md` to the `modules` section
- [x] 7.3 Update entries for keys 7–11 to point to the renumbered steering files (7→`module-07-query-validation.md`, 8→`module-08-performance.md`, 9→`module-09-security.md`, 10→`module-10-monitoring.md`, 11→`module-11-deployment.md`)
- [x] 7.4 Remove the `references: module-07: module-07-reference.md` entry (content incorporated into combined module)
- [x] 7.5 Update `file_metadata` section: remove entries for `module-06-single-source.md`, `module-07-multi-source.md`, `module-07-reference.md`; add entry for `module-06-load-data.md` with estimated token count and size category; rename entries for renumbered files
- [x] 7.6 Update `budget.total_tokens` to reflect the new file set

## Task 8: Update Module Transitions and Cross-References
- [x] 8.1 Update `steering/module-transitions.md` to replace references to old Module 6, Module 7, and Modules 8–12 with new numbering
- [x] 8.2 Update `steering/module-05-data-quality-mapping.md` transition guidance at the end of the file to reference the combined Module 6 ("Load Data") instead of old separate Module 6
- [x] 8.3 Update `steering/module-prerequisites.md` prerequisites table: replace Module 6 and Module 7 rows with combined Module 6 row; renumber Module 8–12 prerequisites to 7–11; update the "Requires" and "Skip if" columns accordingly
- [x] 8.4 Update `steering/onboarding-flow.md`: update module table (show 11 modules), track definitions (use new numbering), validation gates table (combine gates 6→7 and 7→8 into single 6→7 gate, renumber remaining gates)
- [x] 8.5 Update `steering/module-completion.md` path completion detection table: Path D complete after Module 11 (was 12); update any module-specific references
- [x] 8.6 Update `docs/modules/README.md` if it lists modules — update to reflect 11-module structure

## Task 9: Update Scripts
- [x] 9.1 Update `scripts/validate_module.py`: replace `validate_module_6` and `validate_module_7` with a combined `validate_module_6` that checks for `src/load/` directory and `database/G2C.db` and `docs/loading_strategy.md`; renumber validators 8–12 to 7–11; update `VALIDATORS`, `MODULE_NAMES` dicts to 11-module scheme; update `argparse` choices from `range(1, 13)` to `range(1, 12)`
- [x] 9.2 Update `scripts/status.py`: update `MODULE_NAMES` dict to 11-module scheme (remove key 12, update key 6 to "Load Data", renumber 7–11); update `NEXT_STEPS` dict similarly; update `DashboardRenderer._render_module_cards` to iterate `range(1, 12)` instead of `range(1, 13)`; update `_load_completion_timestamps` range check from `1 <= mod_num <= 12` to `1 <= mod_num <= 11`; update completion percentage calculation from `// 12` to `// 11`
- [x] 9.3 Update `scripts/rollback_module.py`: merge `ARTIFACT_MANIFEST` entries for old 6 and 7 into combined entry for new 6; renumber entries 8–12 to 7–11; update `MODULE_NAMES` to 11-module scheme; update `PREREQUISITES` dict to reflect combined module and renumbered modules; update `argparse` choices from `range(1, 13)` to `range(1, 12)`; update module range validation

## Task 10: Verify and Test
- [x] 10.1 Run `python senzing-bootcamp/scripts/validate_power.py` to verify overall power integrity after all changes
- [x] 10.2 Run `python senzing-bootcamp/scripts/measure_steering.py` to update token counts in `steering-index.yaml` for the new and renamed files
- [x] 10.3 Verify no stale references to "Module 12" as a current module, old file names (`module-08-query-validation.md` etc.), or "12-module curriculum" exist in any steering or documentation file
- [x] 10.4 Verify all three scripts (`validate_module.py`, `status.py`, `rollback_module.py`) have consistent MODULE_NAMES for modules 1–11 and no entries for module 12
- [x] 10.5 Run existing test suite to verify no regressions: `python -m pytest senzing-bootcamp/tests/ -x`
