# Bugfix Requirements Document: Enforce Per-Source Mapping Specification

## Introduction

Despite steering instructions in `module-05-phase2-data-mapping.md` (Step 1 "Per-Source Mapping Requirement" box, Step 11 "Per-source mapping specification" template, Step 12 "Per-source completion checkpoint"), the agent does not reliably create a per-source mapping specification markdown file (`docs/{source_name}_mapper.md`) for each data source during Module 5. The instructions exist but are not enforced — the agent can skip them just as it skips other steering instructions.

The fix adds a hook-based enforcement mechanism: a `fileCreated` hook that fires when transformed data appears in `data/transformed/` and blocks progression until the corresponding mapping spec exists, plus a `preToolUse` hook that prevents writing the Module 5 completion checkpoint without all mapping specs present.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent completes the mapping workflow for a data source and creates a transformed file in `data/transformed/` THEN the system does not verify that a corresponding `docs/{source_name}_mapper.md` file was created.

1.2 WHEN the agent proceeds to the next data source or marks Module 5 as complete THEN the system does not check whether all mapped sources have their per-source mapping specification files.

1.3 WHEN the steering instructions say "verify that `docs/{source_name}_mapper.md` exists" THEN the agent sometimes skips this verification step, just as it skips other steering instructions.

1.4 THE existing `analyze-after-mapping` hook fires when transformed data is created but only checks data quality — it does not check for the mapping specification file.

### Expected Behavior (Correct)

2.1 WHEN a new transformed file is created in `data/transformed/` THEN the system SHALL check whether a corresponding `docs/{source_name}_mapper.md` file exists. If it does not exist, the system SHALL instruct the agent to create it before proceeding.

2.2 WHEN the agent attempts to write the Module 5 completion checkpoint (marking the module as complete) THEN the system SHALL verify that every data source with a transformed file in `data/transformed/` has a corresponding mapping specification in `docs/`. If any are missing, the system SHALL block the completion and list the missing files.

2.3 WHEN the mapping specification file is created THEN it SHALL contain at minimum: source file path, data source name, entity type, and a field mappings table.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the `analyze-after-mapping` hook fires THEN it SHALL CONTINUE TO validate data quality via `analyze_record` — the new enforcement is additive, not a replacement.

3.2 WHEN the agent is in modules other than Module 5 THEN the new hooks SHALL NOT interfere with normal file creation or checkpoint writing.

3.3 WHEN the bootcamper has only one data source THEN the enforcement SHALL still apply — even a single source needs its mapping spec.

## Acceptance Criteria

1. A new hook SHALL fire when files are created in `data/transformed/` and verify the corresponding `docs/{source_name}_mapper.md` exists
2. If the mapping spec does not exist, the hook SHALL instruct the agent to create it immediately before proceeding to the next source or any other work
3. The hook SHALL extract the source name from the transformed filename (e.g., `data/transformed/customers.jsonl` → `docs/customers_mapper.md`)
4. A preToolUse hook (or enhancement to an existing hook) SHALL prevent writing the Module 5 completion checkpoint if any mapping specs are missing
5. The enforcement SHALL work regardless of how many data sources the bootcamper has (1 or many)
6. The mapping spec template from Step 11 of `module-05-phase2-data-mapping.md` SHALL be referenced in the hook prompt so the agent knows the expected structure

## Reference

- Source: `SENZING_BOOTCAMP_POWER_FEEDBACK.md` — "Externalize transformation spec as a language-agnostic markdown document" + "One mapping spec file per data source"
- Module: 5 (Data Quality & Mapping) | Priority: Medium | Category: Workflow
- Previous fix: `per-source-mapping` spec (steering instructions added but not enforced)
- Root cause: Steering instructions alone are insufficient — the agent skips them. Hook-based enforcement is needed.
