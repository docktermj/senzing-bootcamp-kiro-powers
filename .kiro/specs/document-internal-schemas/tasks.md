# Tasks: Document Internal Schemas

## Task 1: Create PROGRESS_FILE_SCHEMA.md

- [x] 1.1 Create `senzing-bootcamp/docs/guides/PROGRESS_FILE_SCHEMA.md` with a level-1 heading and introductory paragraph explaining what `config/bootcamp_progress.json` is and why it matters
- [x] 1.2 Add a Field Definitions section with a Markdown table documenting all 7 top-level fields (`modules_completed`, `current_module`, `current_step`, `step_history`, `data_sources`, `database_type`, `language`) with columns: Field, JSON Type, Required/Optional, Valid Values, Description
- [x] 1.3 Add a Step History Structure section documenting the nested `step_history` object: keys are string integers "1" through "11", values contain `last_completed_step` (integer) and `updated_at` (ISO 8601 UTC string); document that `current_step` accepts integers, null, and sub-step string identifiers (e.g., "5.3", "7a")
- [x] 1.4 Add a Validation Rules section documenting the rules enforced by `progress_utils.validate_progress_schema`: `current_step` must be int or null, `step_history` keys must be string integers in range 1–12, each entry must contain `last_completed_step` (int) and `updated_at` (valid ISO 8601)
- [x] 1.5 Add a Complete Example section with a fenced `json` code block showing a valid progress file with at least two completed modules, a current module with an active step, populated step_history entries, and at least one data source
- [x] 1.6 Add a Read By section listing: `status.py`, `validate_module.py`, `repair_progress.py`, `export_results.py`, `rollback_module.py`, `session-resume.md`, `agent-instructions.md`
- [x] 1.7 Add a Written By section listing: `progress_utils.py` (step checkpoints), `repair_progress.py --fix` (reconstruction), and the agent during onboarding and module transitions

## Task 2: Create DATA_SOURCE_REGISTRY.md

- [x] 2.1 Create `senzing-bootcamp/docs/guides/DATA_SOURCE_REGISTRY.md` with a level-1 heading and introductory paragraph explaining what `config/data_sources.yaml` is and why it matters
- [x] 2.2 Add a Top-Level Structure section documenting `version` (string, currently "2") and `sources` (mapping of DATA_SOURCE keys to entry objects), and document the key constraint: must match `^[A-Z][A-Z0-9_]*$`
- [x] 2.3 Add an Entry Field Definitions section with a Markdown table documenting all 13 entry fields (`name`, `file_path`, `format`, `record_count`, `file_size_bytes`, `quality_score`, `mapping_status`, `load_status`, `test_load_status`, `test_entity_count`, `added_at`, `updated_at`, `issues`) with columns: Field, YAML Type, Required/Optional, Valid Values, Description
- [x] 2.4 Add an Enum Values section documenting: `format` (csv, json, jsonl, xlsx, parquet, xml, other), `mapping_status` (pending, in_progress, complete), `load_status` (not_loaded, loading, loaded, failed), `test_load_status` (complete, skipped)
- [x] 2.5 Add a Complete Example section with a fenced `yaml` code block showing a valid registry with version "2" and at least two data source entries demonstrating different status combinations (e.g., one loaded source and one pending source)
- [x] 2.6 Add a Schema Migration section documenting that version "1" registries are automatically migrated to version "2" by `data_sources.py --migrate`, backfilling `test_load_status` and `test_entity_count` as null
- [x] 2.7 Add a Read By section listing: `data_sources.py` (CLI views and recommendations), `status.py` (dashboard integration via `render_data_sources_section`), and the agent during Modules 4–7
- [x] 2.8 Add a Written By section listing: the agent during data source registration (Modules 4–5), `data_sources.py --migrate` (schema migration), and the agent during loading status updates (Module 6)

## Task 3: Create STEERING_INDEX.md

- [x] 3.1 Create `senzing-bootcamp/docs/guides/STEERING_INDEX.md` with a level-1 heading and introductory paragraph explaining what `senzing-bootcamp/steering/steering-index.yaml` is and why it matters
- [x] 3.2 Add a Top-Level Sections overview documenting all six sections: `modules`, `keywords`, `languages`, `deployment`, `file_metadata`, `budget`
- [x] 3.3 Add a Modules section documenting the two entry formats: simple (module number → filename string) and split (module number → object with `root` key and `phases` mapping, where each phase has `file`, `token_count`, `size_category`, `step_range`)
- [x] 3.4 Add a Keywords section documenting the mapping of trigger words to steering filenames, used by the agent to load context-relevant files
- [x] 3.5 Add Languages and Deployment sections documenting the mappings of language names or deployment targets to their respective steering filenames
- [x] 3.6 Add a File Metadata section documenting: each key is a steering filename, each value contains `token_count` (integer, approximate tokens as characters ÷ 4) and `size_category` ("small", "medium", or "large")
- [x] 3.7 Add a Budget section documenting: `total_tokens`, `reference_window`, `warn_threshold_pct`, `critical_threshold_pct`, `split_threshold_tokens` with types and descriptions
- [x] 3.8 Add a Complete Example section with a fenced `yaml` code block showing a valid steering index with at least one simple module, one split module with phases, two keyword entries, one language entry, one deployment entry, two file_metadata entries, and a budget section
- [x] 3.9 Add a Read By section listing: the agent (module steering selection, keyword lookup, context budget tracking), `validate_power.py`, `measure_steering.py --check`, `lint_steering.py`
- [x] 3.10 Add a Written By section listing: `measure_steering.py` (updates file_metadata and budget), `split_steering.py` (adds phase entries), maintainers (manual edits to modules, keywords, languages, deployment)

## Task 4: Update Guides README

- [x] 4.1 Add entries for `PROGRESS_FILE_SCHEMA.md`, `DATA_SOURCE_REGISTRY.md`, and `STEERING_INDEX.md` to the "Reference Documentation" section of `senzing-bootcamp/docs/guides/README.md`, each with a Markdown link, bold title, and 2–3 line description
- [x] 4.2 Add the three new guide filenames to the Documentation Structure tree in the README under the `guides/` directory

## Task 5: Style and Consistency Verification

- [x] 5.1 Verify all three guides use level-1 heading with guide title, followed by introductory paragraph, and organize content under level-2 headings in the required order: overview/introduction, field definitions, complete example, Read By, Written By
- [x] 5.2 Verify all fenced code blocks use correct language identifiers (`json` for progress file, `yaml` for data source registry and steering index)
- [x] 5.3 Run `validate_commonmark.py` against the three new guide files to confirm valid Markdown formatting
