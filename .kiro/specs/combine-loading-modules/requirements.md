# Requirements Document

## Introduction

The Senzing Bootcamp Power currently has two separate modules for data loading: Module 6 (Single Source Loading) and Module 7 (Multi-Source Orchestration). For use cases with multiple data sources (e.g., M&A customer consolidation with 3 sources), the distinction is artificial — the loading pattern is identical for each source, and Module 7's "orchestration" is essentially repeating the same load process for additional sources. The cross-source validation that Module 7 adds could be a step within a single loading module rather than a separate module.

This feature combines Modules 6 and 7 into a single "Load Data" module (new Module 6) that: (1) builds the loading program, (2) loads all sources sequentially, (3) processes redo records, and (4) validates cross-source entity resolution results. Modules currently numbered 8–12 are renumbered to 7–11 to close the gap.

A related spec at `.kiro/specs/mapping-workflow-integration/` refocuses the old Modules 6 and 7 on production concerns by integrating `mapping_workflow` steps 5–8 into Module 5. That spec and this one must be coordinated: the mapping-workflow-integration spec assumes two separate loading modules exist and refocuses their content, while this spec merges them into one. If both specs are implemented, the combined module should incorporate the production-quality focus from the mapping-workflow-integration spec.

## Glossary

- **Module_6**: The current "Single Source Loading" bootcamp module, covering loading of individual data sources into Senzing.
- **Module_7**: The current "Multi-Source Orchestration" bootcamp module, covering coordinated loading of multiple data sources.
- **Combined_Module**: The new merged "Load Data" module that replaces both Module_6 and Module_7, numbered as Module 6 in the updated bootcamp.
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that provides step-by-step workflow instructions for the AI agent during a specific bootcamp module.
- **Module_Documentation**: A markdown file in `senzing-bootcamp/docs/modules/` that provides user-facing reference documentation for a specific bootcamp module.
- **Bootcamp_Progress**: The JSON file at `config/bootcamp_progress.json` that tracks the bootcamper's current step and module completion state.
- **Data_Source_Registry**: The YAML file at `config/data_sources.yaml` that tracks each data source's quality score, mapping status, and load status.
- **Redo_Queue**: Senzing's deferred re-evaluation queue that refines entity resolution results after loading.
- **POWER_MD**: The `senzing-bootcamp/POWER.md` file that serves as the bootcamp's main overview and configuration document.
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file that provides a machine-readable mapping of steering files for agent file selection.
- **Module_Transitions**: The `senzing-bootcamp/steering/module-transitions.md` file that defines journey maps, before/after framing, and module boundary guidance.
- **UAT**: User Acceptance Testing — structured validation of entity resolution results with business stakeholders.

## Requirements

### Requirement 1: Create Combined Loading Steering File

**User Story:** As a bootcamper, I want a single loading module that walks me through building a loading program, loading all my data sources, processing redo records, and validating results, so that I do not repeat the same loading pattern across two separate modules.

#### Acceptance Criteria

1. THE Combined_Module Steering_File SHALL include a phase that helps the bootcamper build a loading program using `generate_scaffold` with the `add_records` workflow for the bootcamper's chosen language.
2. THE Combined_Module Steering_File SHALL include a phase that loads all data sources sequentially, reusing the same loading program (or a per-source variant) for each data source.
3. WHEN a data source finishes loading, THE Combined_Module Steering_File SHALL instruct the agent to process the Redo_Queue for that source before proceeding to the next source.
4. WHEN all data sources are loaded and redo records are processed, THE Combined_Module Steering_File SHALL include a validation phase that covers single-source match accuracy review, cross-source entity resolution validation, false positive and false negative review, and UAT with stakeholder sign-off.
5. WHEN the bootcamper has only one data source, THE Combined_Module Steering_File SHALL skip the cross-source validation steps and proceed directly from single-source validation to module completion.
6. THE Combined_Module Steering_File SHALL retain the error handling, progress tracking, and loading statistics documentation from the current Module_6 Steering_File.
7. THE Combined_Module Steering_File SHALL retain the dependency analysis, load order optimization, and orchestration strategy selection from the current Module_7 Steering_File, presenting these steps only when the bootcamper has two or more data sources.
8. THE Combined_Module Steering_File SHALL write checkpoint data to Bootcamp_Progress for each completed step, continuing the sequential step numbering convention used by other modules.
9. IF loading fails partway through, THEN THE Combined_Module Steering_File SHALL include recovery guidance covering wipe-and-restart, resume-from-checkpoint, and database restore options.

### Requirement 2: Create Combined Loading Module Documentation

**User Story:** As a bootcamper, I want reference documentation for the combined loading module that explains the full loading workflow from program creation through cross-source validation, so that I can understand what the module does before starting it.

#### Acceptance Criteria

1. THE Combined_Module Module_Documentation SHALL describe the module as covering the complete data loading lifecycle: program creation, source loading, redo processing, and result validation.
2. THE Combined_Module Module_Documentation SHALL list learning objectives that combine the current Module_6 and Module_7 objectives: building loading programs, loading records, error handling, progress tracking, redo processing, dependency management, load order optimization, cross-source matching, and UAT.
3. THE Combined_Module Module_Documentation SHALL describe the conditional workflow: single-source path (no orchestration or cross-source steps) and multi-source path (includes dependency analysis, load ordering, and cross-source validation).
4. THE Combined_Module Module_Documentation SHALL include validation gates that combine the current Module_6 and Module_7 gates into a single checklist.
5. THE Combined_Module Module_Documentation SHALL document all output files produced by the module (loading programs, statistics, validation results, UAT results, orchestration strategy).
6. THE Combined_Module Module_Documentation SHALL include the file location map showing where loading programs, logs, statistics, and validation documents are saved.

### Requirement 3: Remove Old Module 6 and Module 7 Files

**User Story:** As a bootcamp maintainer, I want the old separate Module 6 and Module 7 steering files and documentation removed after the combined module is created, so that there are no conflicting or redundant instructions.

#### Acceptance Criteria

1. WHEN the Combined_Module Steering_File is created, THE old `steering/module-06-single-source.md` file SHALL be removed.
2. WHEN the Combined_Module Steering_File is created, THE old `steering/module-07-multi-source.md` file SHALL be removed.
3. WHEN the Combined_Module Module_Documentation is created, THE old `docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md` file SHALL be removed.
4. WHEN the Combined_Module Module_Documentation is created, THE old `docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md` file SHALL be removed.
5. WHEN the old Module 7 steering file is removed, THE `steering/module-07-reference.md` file SHALL be evaluated for content that should be preserved in the Combined_Module Steering_File or a new reference file, and removed if all content is incorporated.

### Requirement 4: Renumber Modules 8–12 to 7–11

**User Story:** As a bootcamper, I want the module numbering to be sequential with no gaps after the merge, so that the bootcamp progression is clear and intuitive.

#### Acceptance Criteria

1. WHEN Modules 6 and 7 are combined, THE modules currently numbered 8 through 12 SHALL be renumbered to 7 through 11 respectively (8→7, 9→8, 10→9, 11→10, 12→11).
2. THE renumbering SHALL update all steering file names: `module-08-query-validation.md` → `module-07-query-validation.md`, `module-09-performance.md` → `module-08-performance.md`, `module-10-security.md` → `module-09-security.md`, `module-11-monitoring.md` → `module-10-monitoring.md`, `module-12-deployment.md` → `module-11-deployment.md`.
3. THE renumbering SHALL update all module documentation file names: `MODULE_8_QUERY_VALIDATION.md` → `MODULE_7_QUERY_VALIDATION.md`, and so on through `MODULE_12_DEPLOYMENT_PACKAGING.md` → `MODULE_11_DEPLOYMENT_PACKAGING.md`.
4. THE renumbering SHALL update all internal cross-references within steering files and documentation that refer to modules by number (e.g., "Module 8" becomes "Module 7", "proceed to Module 8" becomes "proceed to Module 7").
5. THE renumbering SHALL update the Steering_Index entries for the affected steering files.

### Requirement 5: Update POWER.md

**User Story:** As a bootcamper reading the bootcamp overview, I want POWER.md to accurately reflect the combined module and updated numbering, so that I can make informed decisions about which track to follow.

#### Acceptance Criteria

1. THE POWER_MD module table SHALL replace the separate Module 6 and Module 7 rows with a single row for the Combined_Module describing it as covering data loading, redo processing, and result validation for one or more data sources.
2. THE POWER_MD module table SHALL update the numbering for all modules after the Combined_Module (old 8→7, 9→8, 10→9, 11→10, 12→11).
3. THE POWER_MD overview text SHALL describe the bootcamp as an "11-module curriculum (Modules 1–11)" instead of "12-module curriculum (Modules 1–12)".
4. THE POWER_MD track descriptions SHALL update module references to use the new numbering (e.g., Track B becomes "Modules 5 → 6 → 7" instead of "Modules 5 → 6 → 8", Track C becomes "Modules 1 → 4 → 5 → 6 → 7").
5. THE POWER_MD "Available Steering Files" section SHALL update the module workflow list to reflect the combined module and renumbered files.
6. THE POWER_MD "Bootcamp Modules" table SHALL reflect the combined module and renumbered modules, showing 11 modules total.
7. THE POWER_MD skip-ahead guidance SHALL update references (e.g., "single source (skip 7)" is no longer applicable; production modules become "skip 8–11" instead of "skip 9–12").

### Requirement 6: Update Module Transitions and Cross-References

**User Story:** As a bootcamper, I want the module transition guidance, journey maps, and cross-references throughout the bootcamp to reflect the combined module and new numbering, so that navigation between modules is consistent and correct.

#### Acceptance Criteria

1. THE Module_Transitions file SHALL update any references to Module 6, Module 7, or Modules 8–12 to use the new numbering scheme.
2. WHEN the Combined_Module completes, THE Module_Transitions guidance SHALL direct single-source bootcampers to Module 7 (old Module 8: Query & Visualize) and multi-source bootcampers to Module 7 after cross-source validation is complete.
3. THE `steering/module-05-data-quality-mapping.md` file SHALL update its transition guidance to reference the Combined_Module (new Module 6) instead of the old separate Module 6.
4. THE `steering/module-prerequisites.md` file SHALL update prerequisites for the Combined_Module and all renumbered modules.
5. THE `steering/onboarding-flow.md` file SHALL update track definitions and module references to use the new numbering.
6. THE `steering/module-completion.md` file SHALL update any module-specific completion guidance that references the old Module 6, Module 7, or Modules 8–12.

### Requirement 7: Update Steering Index

**User Story:** As an AI agent, I want the steering index to accurately map the combined module steering file and renumbered files, so that I can load the correct steering file for each module.

#### Acceptance Criteria

1. THE Steering_Index SHALL remove entries for `module-06-single-source.md` and `module-07-multi-source.md`.
2. THE Steering_Index SHALL add an entry for the Combined_Module steering file with accurate token count and size category.
3. THE Steering_Index SHALL update entries for all renumbered steering files (old 08→07, 09→08, 10→09, 11→10, 12→11) with correct file names.
4. THE Steering_Index SHALL update the `module-07-reference.md` entry if the file is retained, or remove it if the content is incorporated into the Combined_Module.

### Requirement 8: Update Scripts and Configuration References

**User Story:** As a bootcamper, I want the bootcamp scripts and configuration files to work correctly with the combined module and new numbering, so that progress tracking, validation, and status reporting remain accurate.

#### Acceptance Criteria

1. THE `scripts/validate_module.py` script SHALL recognize the Combined_Module as a valid module and apply the combined validation gates.
2. THE `scripts/status.py` script SHALL display the Combined_Module correctly in progress output and handle the renumbered modules.
3. THE `scripts/rollback_module.py` script SHALL support rolling back the Combined_Module and the renumbered modules.
4. IF any script contains hardcoded module numbers or module name mappings, THEN those mappings SHALL be updated to reflect the combined module and renumbered modules.
5. THE `config/bootcamp_progress.json` schema documentation SHALL note that module numbers 6 and 7 are now a single module, and modules 7–11 correspond to the old 8–12.

### Requirement 9: Preserve Module 7 Reference Material

**User Story:** As a bootcamper working with multiple data sources, I want the advanced orchestration reference material (source ordering examples, conflict resolution, error handling patterns) to remain accessible within the combined module, so that I do not lose access to useful guidance.

#### Acceptance Criteria

1. THE Combined_Module Steering_File or a linked reference file SHALL preserve the source ordering heuristics from the current Module_7 (reference before transactional, quality-first, attribute-density-first, volume-first).
2. THE Combined_Module Steering_File or a linked reference file SHALL preserve the orchestration patterns from the current Module_7 (sequential, parallel, dependency-aware, pipeline).
3. THE Combined_Module Steering_File or a linked reference file SHALL preserve the error handling strategies from the current Module_7 (fail fast, continue on error, retry with backoff, partial success).
4. WHEN the bootcamper has only one data source, THE Combined_Module Steering_File SHALL not present the multi-source orchestration reference material.

### Requirement 10: Coordinate with Mapping Workflow Integration Spec

**User Story:** As a bootcamp maintainer, I want clear documentation of how this spec interacts with the mapping-workflow-integration spec, so that both can be implemented without conflicts.

#### Acceptance Criteria

1. THE Combined_Module Steering_File SHALL include conditional logic that checks whether Module 5 Phase 3 (test load from mapping-workflow-integration spec) was completed, and adjusts the loading workflow accordingly (skip basic test loading if Phase 3 was done, include it if Phase 3 was skipped).
2. THE Combined_Module Module_Documentation SHALL reference the mapping-workflow-integration spec's Phase 3 shortcut path and explain how it interacts with the combined loading module.
3. IF the mapping-workflow-integration spec has not been implemented when this spec is implemented, THEN THE Combined_Module SHALL function correctly without the Phase 3 conditional logic, treating all bootcampers as needing the full loading workflow.
