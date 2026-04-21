# Requirements Document

## Introduction

The Module 7 (Multi-Source Orchestration) steering file at `senzing-bootcamp/steering/module-07-multi-source.md` is currently ~100 lines — the thinnest steering file for one of the most complex modules in the bootcamp. Module 7 is where cross-source entity resolution happens, requiring orchestration of multiple data sources with dependency management, conflict resolution, source-specific error handling, and troubleshooting. The steering file needs to be expanded to 150+ lines to provide the AI agent with sufficient guidance to walk bootcampers through this critical module effectively.

This is a Kiro Power — the "code" is markdown steering files that guide AI agent behavior. Changes go in `senzing-bootcamp/steering/module-07-multi-source.md` (the distributed power file).

## Glossary

- **Steering_File**: A markdown file loaded by the AI agent at runtime that provides step-by-step workflow instructions, decision gates, and behavioral rules for guiding a bootcamper through a module
- **Agent**: The AI assistant that reads steering files and guides bootcampers through the Senzing Bootcamp
- **Bootcamper**: The human user working through the bootcamp modules
- **Orchestrator**: A program that coordinates loading of multiple data sources into Senzing in the correct order with error handling and progress tracking
- **Cross_Source_Matching**: The process by which Senzing identifies that records from different data sources refer to the same real-world entity
- **Redo_Queue**: A Senzing internal queue of deferred re-evaluations that refine entity resolution after records are loaded
- **Load_Order**: The sequence in which data sources are loaded into Senzing, which can affect resolution quality and performance
- **Dependency_Map**: A configuration that defines which data sources must be loaded before others
- **Source_Conflict**: A situation where records from different data sources contain contradictory information about the same entity (e.g., different addresses, different phone numbers)
- **SGES**: Senzing Generic Entity Specification — the JSON format Senzing requires for input records
- **MCP_Tool**: A tool provided by the Senzing MCP server that the agent calls to generate code, validate records, or retrieve documentation

## Requirements

### Requirement 1: Step-by-Step Orchestration Workflow

**User Story:** As an AI agent, I want a detailed step-by-step orchestration workflow in the steering file, so that I can guide bootcampers through the complete process of loading multiple data sources with clear WAIT points and decision gates.

#### Acceptance Criteria

1. THE Steering_File SHALL contain a numbered workflow with at least 10 distinct steps covering the full orchestration lifecycle from source inventory through final validation
2. WHEN the Agent reaches a step that requires bootcamper input, THE Steering_File SHALL include a WAIT directive with a specific question prefixed by the 👉 marker
3. THE Steering_File SHALL include a source inventory step that instructs the Agent to enumerate all data sources from previous modules with their record counts, quality scores, and mapping status
4. THE Steering_File SHALL include a step that instructs the Agent to create a dependency map documenting which sources depend on others and why
5. THE Steering_File SHALL include a strategy selection step where the Agent presents sequential, parallel, and hybrid options with trade-offs for each
6. THE Steering_File SHALL include a step for creating the orchestrator program using `generate_scaffold` and `find_examples` MCP tools with explicit instructions to override non-project paths
7. THE Steering_File SHALL include a sample-test step that instructs the Agent to run the orchestrator on a small subset before full execution
8. THE Steering_File SHALL include a full-run step with monitoring guidance covering progress per source, error rates, and resource utilization
9. THE Steering_File SHALL include a redo processing step with instructions to drain the redo queue after all sources are loaded using `generate_scaffold(workflow='redo')`
10. THE Steering_File SHALL include a cross-source validation step that instructs the Agent to verify matches across sources and present results to the bootcamper

### Requirement 2: Multi-Source Conflict Resolution Guidance

**User Story:** As an AI agent, I want guidance on how to explain and handle multi-source conflicts to bootcampers, so that I can help them understand how Senzing resolves contradictory information from different sources.

#### Acceptance Criteria

1. THE Steering_File SHALL include a conflict resolution section that describes at least three common conflict scenarios (e.g., different addresses, different phone numbers, different name spellings across sources)
2. THE Steering_File SHALL instruct the Agent to explain to the bootcamper how Senzing handles conflicting data using the concept of observation-based resolution rather than source-priority overrides
3. WHEN a bootcamper asks about conflicting records, THE Steering_File SHALL instruct the Agent to use `search_docs(query="entity resolution conflicts", version="current")` to retrieve current Senzing guidance
4. THE Steering_File SHALL include an example scenario showing how records from two sources with overlapping but contradictory fields resolve into a single entity
5. THE Steering_File SHALL instruct the Agent to offer visualization of cross-source entity relationships using `reporting_guide(topic='graph', version='current')`

### Requirement 3: Source-Specific Error Handling

**User Story:** As an AI agent, I want detailed source-specific error handling guidance in the steering file, so that I can help bootcampers diagnose and recover from failures that occur during multi-source loading.

#### Acceptance Criteria

1. THE Steering_File SHALL include an error handling section that covers per-source failure isolation — when one source fails, the Agent guides the bootcamper to continue loading remaining sources
2. THE Steering_File SHALL instruct the Agent to use `explain_error_code` for every Senzing error encountered during orchestration before deciding on a recovery action
3. THE Steering_File SHALL include guidance for at least four common per-source error scenarios: invalid records, duplicate RECORD_IDs across sources, DATA_SOURCE name mismatches, and transformation errors
4. THE Steering_File SHALL instruct the Agent to document each error and its resolution in `docs/loading_strategy.md` as part of the orchestration record
5. IF a source fails during orchestration, THEN THE Steering_File SHALL instruct the Agent to present three recovery options: skip the source and continue, retry the source after fixing the issue, or restore from backup and restart
6. THE Steering_File SHALL include a pre-load validation checklist that the Agent runs before starting orchestration to catch common errors early

### Requirement 4: Source Ordering and Dependency Guidance

**User Story:** As an AI agent, I want comprehensive guidance on source ordering and dependencies, so that I can help bootcampers determine the optimal load order for their specific data sources.

#### Acceptance Criteria

1. THE Steering_File SHALL include a decision framework with at least four ordering heuristics: load highest-quality source first, load reference data before transactional data, load largest source first for baseline, and load sources with the most identifying attributes first
2. THE Steering_File SHALL include at least two concrete ordering examples showing different dependency patterns (e.g., Customer 360 pattern and Compliance Screening pattern)
3. WHEN the bootcamper has sources with no dependencies, THE Steering_File SHALL instruct the Agent to recommend parallel loading and explain the performance benefits
4. THE Steering_File SHALL instruct the Agent to create a dependency map document at `docs/loading_strategy.md` that includes source names, load order, dependency rationale, and estimated durations
5. THE Steering_File SHALL include guidance for detecting and resolving circular dependencies between data sources
6. THE Steering_File SHALL instruct the Agent to use `search_docs(query="multi-source loading orchestration", category="anti_patterns", version="current")` before recommending a load order

### Requirement 5: Troubleshooting for Common Multi-Source Issues

**User Story:** As an AI agent, I want a troubleshooting reference for common multi-source issues embedded in the steering file, so that I can quickly diagnose and resolve problems without needing to load separate troubleshooting files.

#### Acceptance Criteria

1. THE Steering_File SHALL include a troubleshooting section with at least six common multi-source issues and their resolutions
2. THE Steering_File SHALL include troubleshooting guidance for: low cross-source match rates, unexpected entity merges across sources, slow loading performance with multiple sources, redo queue not draining, resource exhaustion during parallel loading, and source-ordering-related resolution quality issues
3. WHEN the bootcamper reports low cross-source match rates, THE Steering_File SHALL instruct the Agent to check data quality scores from Module 4, review mapping consistency across sources from Module 5, and use the SDK "why" method via `get_sdk_reference` to examine match details
4. THE Steering_File SHALL instruct the Agent to reference `common-pitfalls.md` Module 7 section for additional troubleshooting context when the embedded guidance is insufficient
5. THE Steering_File SHALL include performance benchmarks that help the Agent set expectations (e.g., SQLite limitations with multiple sources, when to recommend PostgreSQL migration)

### Requirement 6: Steering File Structure and Length

**User Story:** As a power developer, I want the expanded steering file to meet minimum length requirements while maintaining the established steering file conventions, so that it provides adequate guidance without breaking the power's structure.

#### Acceptance Criteria

1. THE Steering_File SHALL contain at least 150 lines of content
2. THE Steering_File SHALL retain the existing YAML front matter with `inclusion: manual`
3. THE Steering_File SHALL retain the existing reference to `docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`
4. THE Steering_File SHALL retain the existing Before/After framing, Prerequisites section, and Success Criteria section
5. THE Steering_File SHALL use the same formatting conventions as other steering files: agent instruction blockquotes, WAIT directives for user input, MCP tool call syntax, and 👉 markers for bootcamper questions
6. THE Steering_File SHALL include all MCP tool references using the exact tool names and parameter formats used in other steering files (e.g., `generate_scaffold`, `find_examples`, `search_docs`, `explain_error_code`, `reporting_guide`)
