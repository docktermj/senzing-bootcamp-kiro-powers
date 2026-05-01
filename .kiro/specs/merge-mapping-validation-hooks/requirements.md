# Requirements Document

## Introduction

The Senzing Bootcamp power has two Module 5 hooks that validate transformed data in `data/transformed/`: `analyze-after-mapping` (fires on fileCreated) and `validate-senzing-json` (fires on fileEdited). Both target the same file patterns (`data/transformed/*.jsonl`, `data/transformed/*.json`) and both ask the agent to use the `analyze_record` MCP tool. Since Kiro hooks support only one event type per hook, these cannot be combined into a single dual-trigger hook. The chosen strategy (Option A) keeps `analyze-after-mapping` as the sole hook, enhances its prompt to include the Senzing Generic Entity Specification conformance checks from `validate-senzing-json`, and removes `validate-senzing-json` entirely. The Module 5 steering workflow already covers re-validation after edits in its iterate step (Step 10), so the fileEdited trigger is redundant.

## Glossary

- **Analyze_After_Mapping_Hook**: The `analyze-after-mapping.kiro.hook` file — a fileCreated hook that fires when new Senzing JSON files appear in `data/transformed/`. This is the hook being kept and enhanced.
- **Validate_Senzing_JSON_Hook**: The `validate-senzing-json.kiro.hook` file — a fileEdited hook that fires when transformed files are modified. This is the hook being removed.
- **Hook_Registry**: The `senzing-bootcamp/steering/hook-registry.md` file — the canonical steering document listing all hook definitions, prompts, and metadata for the agent.
- **Hook_Categories**: The `senzing-bootcamp/hooks/hook-categories.yaml` file — a YAML file mapping hook IDs to their module categories, used by `sync_hook_registry.py`.
- **Hooks_README**: The `senzing-bootcamp/hooks/README.md` file — developer-facing documentation describing all available hooks.
- **Install_Script**: The `senzing-bootcamp/scripts/install_hooks.py` file — a Python script that installs hook files into `.kiro/hooks/`.
- **POWER_MD**: The `senzing-bootcamp/POWER.md` file — the power's main documentation listing available hooks.
- **Module_5_Steering**: The `senzing-bootcamp/steering/module-05-phase2-data-mapping.md` file — the Phase 2 steering file for Module 5 that guides the data mapping workflow.
- **Test_File**: The `senzing-bootcamp/tests/test_silent_hook_processing.py` file — the test file that references both hooks in its non-affected hook lists.
- **Sync_Script**: The `senzing-bootcamp/scripts/sync_hook_registry.py` file — a script that regenerates `hook-registry.md` from `.kiro.hook` files and `hook-categories.yaml`.
- **Analyze_Record**: The `analyze_record` MCP tool provided by the Senzing MCP server for validating mapped records against the Senzing Entity Specification.

## Requirements

### Requirement 1: Enhance the Analyze After Mapping Hook Prompt

**User Story:** As a bootcamp agent, I want the `analyze-after-mapping` hook prompt to cover both feature distribution/quality checks and Senzing Generic Entity Specification conformance, so that a single hook provides comprehensive validation when new transformed files are created.

#### Acceptance Criteria

1. THE Analyze_After_Mapping_Hook prompt SHALL instruct the agent to use the Analyze_Record MCP tool to validate a sample of records from the newly created file
2. THE Analyze_After_Mapping_Hook prompt SHALL instruct the agent to check feature distribution, attribute coverage, and data quality with a quality score threshold of greater than 70 percent
3. THE Analyze_After_Mapping_Hook prompt SHALL instruct the agent to verify that records conform to the Senzing Generic Entity Specification
4. THE Analyze_After_Mapping_Hook SHALL retain the fileCreated event type with patterns `data/transformed/*.jsonl` and `data/transformed/*.json`
5. THE Analyze_After_Mapping_Hook SHALL retain the askAgent action type

### Requirement 2: Remove the Validate Senzing JSON Hook File

**User Story:** As a power maintainer, I want the redundant `validate-senzing-json` hook file removed, so that there is a single source of truth for transformed-data validation.

#### Acceptance Criteria

1. WHEN the merge is complete, THE Validate_Senzing_JSON_Hook file SHALL no longer exist in the `senzing-bootcamp/hooks/` directory
2. WHEN the merge is complete, THE `senzing-bootcamp/hooks/` directory SHALL contain the Analyze_After_Mapping_Hook file with the enhanced prompt

### Requirement 3: Update the Hook Categories Configuration

**User Story:** As a power maintainer, I want the hook categories YAML to reflect the removal of `validate-senzing-json`, so that `sync_hook_registry.py` generates a correct registry.

#### Acceptance Criteria

1. THE Hook_Categories file SHALL list `analyze-after-mapping` under the Module 5 category
2. THE Hook_Categories file SHALL NOT list `validate-senzing-json` under any module category
3. THE Hook_Categories file SHALL preserve all other existing category entries unchanged

### Requirement 4: Update the Hook Registry

**User Story:** As a bootcamp agent, I want the hook registry to contain only the enhanced `analyze-after-mapping` entry and no `validate-senzing-json` entry, so that the agent creates the correct hooks during module startup.

#### Acceptance Criteria

1. THE Hook_Registry SHALL contain an entry for `analyze-after-mapping` with the enhanced prompt matching the Analyze_After_Mapping_Hook file
2. THE Hook_Registry SHALL NOT contain an entry for `validate-senzing-json`
3. THE Hook_Registry SHALL preserve all other existing hook entries unchanged
4. WHEN the Sync_Script is run with `--verify`, THE Sync_Script SHALL report that the Hook_Registry matches the hook files

### Requirement 5: Update the Hooks README

**User Story:** As a developer reviewing the power, I want the hooks README to document only the enhanced `analyze-after-mapping` hook and not reference the removed `validate-senzing-json` hook, so that documentation is accurate.

#### Acceptance Criteria

1. THE Hooks_README SHALL contain a section for `analyze-after-mapping` describing its enhanced validation scope covering both quality checks and Senzing Entity Specification conformance
2. THE Hooks_README SHALL NOT contain a section for `validate-senzing-json`
3. THE Hooks_README Module 5 recommended hooks list SHALL include `analyze-after-mapping` and SHALL NOT include `validate-senzing-json`
4. THE Hooks_README hook numbering SHALL be sequential with no gaps after the removal

### Requirement 6: Update the Install Script

**User Story:** As a bootcamp user running the install script, I want the script to install the enhanced `analyze-after-mapping` hook and not attempt to install the removed `validate-senzing-json` hook, so that installation succeeds without errors.

#### Acceptance Criteria

1. THE Install_Script HOOKS list SHALL contain an entry for `analyze-after-mapping.kiro.hook` with an updated description reflecting the enhanced validation scope
2. THE Install_Script HOOKS list SHALL NOT contain an entry for `validate-senzing-json.kiro.hook`

### Requirement 7: Update POWER.md Hook List

**User Story:** As a user reading the power documentation, I want the available hooks list to reflect the merge, so that I see accurate hook names.

#### Acceptance Criteria

1. THE POWER_MD available hooks list SHALL include `analyze-after-mapping`
2. THE POWER_MD available hooks list SHALL NOT include `validate-senzing-json`

### Requirement 8: Update Test References

**User Story:** As a developer running the test suite, I want tests to pass after the merge by removing references to the deleted hook, so that CI remains green.

#### Acceptance Criteria

1. THE Test_File non-affected hook ID list SHALL NOT contain `validate-senzing-json`
2. THE Test_File non-affected hook ID list SHALL contain `analyze-after-mapping`
3. WHEN the test suite is run, THE Test_File SHALL pass with no failures caused by references to the removed hook

### Requirement 9: Validate CI Pipeline Passes

**User Story:** As a power maintainer, I want the CI validation pipeline to pass after all changes, so that the merge does not introduce regressions.

#### Acceptance Criteria

1. WHEN `sync_hook_registry.py --verify` is run, THE Sync_Script SHALL exit with code 0
2. WHEN `pytest` is run on the test suite, THE test runner SHALL report no failures related to the hook merge
