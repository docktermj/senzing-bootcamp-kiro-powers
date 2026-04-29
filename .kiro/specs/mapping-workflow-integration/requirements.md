# Requirements Document

## Introduction

The Senzing Bootcamp Power's MCP server provides an 8-step `mapping_workflow` tool. Steps 1–4 are core mapping (profile, plan, map, generate/validate). Steps 5–8 are optional but cover SDK detection, test loading into a fresh SQLite DB, validation report generation, and entity resolution evaluation. Currently, Module 5 stops at step 4 and treats steps 5–8 as optional. Module 6 (Single Source Loading) and Module 7 (Multi-Source Orchestration) then repeat similar load-and-verify patterns independently.

This creates redundancy: a bootcamper could complete the full 8-step mapping workflow per source (including test loading and evaluation) and then move directly to production-quality loading — rather than going through separate modules that repeat the basic load-and-verify pattern.

This feature integrates `mapping_workflow` steps 5–8 into Module 5 as a "test load and validate" phase, then refocuses Module 6 on production-quality loading concerns (error handling, progress tracking, redo processing, incremental loading) and Module 7 on production-quality multi-source orchestration (dependency management, parallel loading, cross-source validation, stakeholder sign-off). The result is a streamlined bootcamp flow that eliminates redundant work while preserving all learning objectives.

## Glossary

- **Mapping_Workflow**: The MCP server's 8-step interactive data mapping tool (`mapping_workflow`), which profiles source data, plans entity mappings, maps fields to Senzing attributes, generates transformation code, and optionally performs test loading and evaluation.
- **Module_5**: The "Data Quality & Mapping" bootcamp module, covering quality assessment (Phase 1) and data mapping (Phase 2).
- **Module_6**: The "Single Source Loading" bootcamp module, covering loading of individual data sources into Senzing.
- **Module_7**: The "Multi-Source Orchestration" bootcamp module, covering coordinated loading of multiple data sources.
- **Test_Load_Phase**: The new Phase 3 of Module_5 that integrates `mapping_workflow` steps 5–8 to perform SDK detection, test data loading into a fresh SQLite database, validation report generation, and entity resolution evaluation.
- **Steering_File**: A markdown file in `senzing-bootcamp/steering/` that provides step-by-step workflow instructions for the AI agent during a specific bootcamp module.
- **Module_Documentation**: A markdown file in `senzing-bootcamp/docs/modules/` that provides user-facing reference documentation for a specific bootcamp module.
- **Bootcamp_Progress**: The JSON file at `config/bootcamp_progress.json` that tracks the bootcamper's current step and module completion state.
- **Data_Source_Registry**: The YAML file at `config/data_sources.yaml` that tracks each data source's quality score, mapping status, and load status.
- **SGES**: Senzing Generic Entity Specification — the JSON format Senzing requires for input records.
- **Redo_Queue**: Senzing's deferred re-evaluation queue that refines entity resolution results after loading.

## Requirements

### Requirement 1: Integrate mapping_workflow Steps 5–8 into Module 5 as Phase 3

**User Story:** As a bootcamper, I want to test-load and evaluate my mapped data within the mapping module, so that I get immediate feedback on entity resolution quality without waiting for a separate loading module.

#### Acceptance Criteria

1. WHEN a bootcamper completes Phase 2 (Data Mapping) for a data source, THE Module_5 Steering_File SHALL present a Phase 3 ("Test Load and Validate") that advances through `mapping_workflow` steps 5–8 for that data source.
2. WHEN Phase 3 begins for a data source, THE Module_5 Steering_File SHALL instruct the agent to call `mapping_workflow` with `action='advance'` to detect the SDK environment (step 5).
3. WHEN SDK detection succeeds, THE Module_5 Steering_File SHALL instruct the agent to advance through step 6 (load test data into a fresh SQLite database), step 7 (generate a validation report), and step 8 (evaluate entity resolution results).
4. IF the SDK is not configured during Phase 3, THEN THE Module_5 Steering_File SHALL instruct the agent to inform the bootcamper that Module 2 (SDK Setup) is required before test loading and offer to skip Phase 3.
5. WHEN Phase 3 completes for a data source, THE Module_5 Steering_File SHALL instruct the agent to present the entity resolution evaluation results including match counts, entity counts, and quality assessment.
6. THE Module_5 Steering_File SHALL mark Phase 3 as optional — bootcampers who prefer to skip test loading SHALL be able to proceed directly from Phase 2 to Module 6.
7. WHEN Phase 3 is completed or skipped, THE Module_5 Steering_File SHALL instruct the agent to write checkpoint data to Bootcamp_Progress for each completed step.

### Requirement 2: Update Module 5 Documentation to Include Phase 3

**User Story:** As a bootcamper, I want the Module 5 reference documentation to describe the test load and validate phase, so that I understand what the phase does and why it matters before I start it.

#### Acceptance Criteria

1. THE Module_5 Module_Documentation SHALL include a Phase 3 section titled "Test Load and Validate" that describes `mapping_workflow` steps 5–8.
2. THE Module_5 Module_Documentation SHALL explain that Phase 3 is optional and can be skipped if the bootcamper prefers to write custom loading programs in Module 6.
3. THE Module_5 Module_Documentation SHALL list the Phase 3 learning objectives: verifying mapping quality through test loading, observing entity resolution results on mapped data, and identifying mapping issues before production loading.
4. THE Module_5 Module_Documentation SHALL document the output files produced by Phase 3 (validation report, test database, evaluation results).
5. THE Module_5 Module_Documentation SHALL update the success criteria section to include Phase 3 completion indicators.

### Requirement 3: Refocus Module 6 on Production-Quality Loading

**User Story:** As a bootcamper, I want Module 6 to focus on production-quality loading concerns rather than repeating the basic load-and-verify pattern I already completed in Module 5, so that I learn new skills in each module.

#### Acceptance Criteria

1. THE Module_6 Steering_File SHALL focus on production-quality loading concerns: error handling per record, progress tracking with throughput reporting, loading statistics documentation, and redo queue processing.
2. THE Module_6 Steering_File SHALL remove or reduce the basic "test with sample data and verify results" steps that overlap with Module_5 Phase 3.
3. WHEN a bootcamper has completed Module_5 Phase 3 for a data source, THE Module_6 Steering_File SHALL instruct the agent to acknowledge the test load results and build on them rather than repeating test loading.
4. WHEN a bootcamper has skipped Module_5 Phase 3, THE Module_6 Steering_File SHALL instruct the agent to include a brief test load step before proceeding to production loading.
5. THE Module_6 Steering_File SHALL retain the match accuracy review and single-source validation steps as the production validation phase.
6. THE Module_6 Steering_File SHALL add guidance on incremental loading strategies as a production concern distinct from initial bulk loading.

### Requirement 4: Update Module 6 Documentation to Reflect Production Focus

**User Story:** As a bootcamper, I want the Module 6 reference documentation to clearly describe its production-quality loading focus, so that I understand how it builds on Module 5 rather than repeating it.

#### Acceptance Criteria

1. THE Module_6 Module_Documentation SHALL update the overview to describe Module 6 as focused on production-quality loading rather than basic load-and-verify.
2. THE Module_6 Module_Documentation SHALL describe the conditional workflow: abbreviated path for bootcampers who completed Phase 3, full path for bootcampers who skipped Phase 3.
3. THE Module_6 Module_Documentation SHALL list production-quality learning objectives: robust error handling, progress tracking, throughput optimization, redo processing, and incremental loading strategies.
4. THE Module_6 Module_Documentation SHALL update the "What You'll Do" section to reflect the production focus.

### Requirement 5: Refocus Module 7 on Production-Quality Multi-Source Orchestration

**User Story:** As a bootcamper, I want Module 7 to focus on production-quality orchestration concerns rather than repeating the basic multi-source load pattern, so that I learn dependency management, parallel loading, and cross-source validation as distinct skills.

#### Acceptance Criteria

1. THE Module_7 Steering_File SHALL focus on production-quality orchestration concerns: dependency management, load order optimization, parallel loading strategies, cross-source error isolation, and coordinated redo processing.
2. WHEN a bootcamper has completed Module_5 Phase 3 for multiple data sources, THE Module_7 Steering_File SHALL instruct the agent to reference the test load results when planning load order and dependency management.
3. THE Module_7 Steering_File SHALL retain the cross-source match accuracy validation, UAT, and stakeholder sign-off steps as the production validation phase.
4. THE Module_7 Steering_File SHALL add guidance on production orchestration patterns (retry with backoff, partial success handling, orchestrator health monitoring) that go beyond basic sequential loading.

### Requirement 6: Update Module 7 Documentation to Reflect Production Focus

**User Story:** As a bootcamper, I want the Module 7 reference documentation to clearly describe its production-quality orchestration focus, so that I understand how it builds on the test loading done in Module 5.

#### Acceptance Criteria

1. THE Module_7 Module_Documentation SHALL update the overview to describe Module 7 as focused on production-quality multi-source orchestration rather than basic multi-source loading.
2. THE Module_7 Module_Documentation SHALL describe how test load results from Module_5 Phase 3 inform the orchestration strategy.
3. THE Module_7 Module_Documentation SHALL list production orchestration learning objectives: dependency-aware loading, parallel execution, error isolation, coordinated redo processing, and cross-source validation.
4. THE Module_7 Module_Documentation SHALL update the "When to Use This Module" section to clarify that bootcampers with a single data source skip Module 7 regardless of whether they completed Phase 3.

### Requirement 7: Document the Shortcut Path for Simple Use Cases

**User Story:** As a bootcamper with a simple use case, I want clear documentation that completing mapping_workflow steps 5–8 in Module 5 can replace parts of Modules 6–7 for simple scenarios, so that I can choose the most efficient path through the bootcamp.

#### Acceptance Criteria

1. THE Module_5 Steering_File SHALL include a decision gate after Phase 3 that explains: for simple use cases (single source, small dataset, no production requirements), the test load results from Phase 3 may be sufficient and the bootcamper can proceed directly to Module 8 (Query & Visualize).
2. THE Module_5 Module_Documentation SHALL include a "Shortcut Path" section explaining when Phase 3 results are sufficient to skip Modules 6–7.
3. WHEN a bootcamper chooses the shortcut path, THE Module_5 Steering_File SHALL instruct the agent to update Bootcamp_Progress to mark Modules 6 and 7 as skipped with a reason.
4. THE Module_5 Steering_File SHALL instruct the agent to recommend the full Module 6–7 path for bootcampers with production requirements, multiple data sources, or datasets exceeding 1000 records.

### Requirement 8: Maintain Checkpoint and Registry Consistency

**User Story:** As a bootcamper, I want my progress and data source status to be tracked accurately across the restructured modules, so that session resume and status reporting work correctly.

#### Acceptance Criteria

1. WHEN Phase 3 test loading completes for a data source, THE Module_5 Steering_File SHALL instruct the agent to update the Data_Source_Registry with a `test_load_status` field set to `complete` and record the test entity count.
2. WHEN a bootcamper transitions from Module_5 to Module_6, THE Module_6 Steering_File SHALL instruct the agent to read the Data_Source_Registry to determine which sources have completed test loading.
3. THE Module_5 Steering_File SHALL assign step numbers to Phase 3 steps that continue sequentially from the existing Phase 2 step numbers in Bootcamp_Progress.
4. WHEN a bootcamper resumes a session during Phase 3, THE Module_5 Steering_File SHALL instruct the agent to read the mapping state checkpoint and Bootcamp_Progress to determine which Phase 3 steps have been completed.

### Requirement 9: Update POWER.md Module Table and Track Descriptions

**User Story:** As a bootcamper reading the bootcamp overview, I want the module descriptions to accurately reflect the restructured content, so that I can make informed decisions about which track to follow.

#### Acceptance Criteria

1. THE POWER.md module table SHALL update the Module 5 description to mention the optional test load and validate phase.
2. THE POWER.md module table SHALL update the Module 6 description to emphasize production-quality loading concerns.
3. THE POWER.md module table SHALL update the Module 7 description to emphasize production-quality orchestration concerns.
4. THE POWER.md track descriptions SHALL note that Track B (Fast Track) and Track C (Complete Beginner) benefit from the Phase 3 shortcut path for simple use cases.
