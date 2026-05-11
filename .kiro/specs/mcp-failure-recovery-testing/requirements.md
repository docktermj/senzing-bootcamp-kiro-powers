# Requirements Document

## Introduction

The senzing-bootcamp Kiro power depends on the Senzing MCP server (`mcp.senzing.com`) for SDK code generation, documentation lookup, data mapping workflows, and error diagnosis. The power has a `mcp-offline-fallback.md` steering file that defines recovery behavior when MCP tools are unavailable, but this behavior is untested. The existing `test_mcp_health_check.py` validates that the health check mechanism exists in steering files, but no tests verify the completeness or correctness of the failure recovery instructions themselves.

This feature adds tests that verify: the offline fallback steering file is complete and actionable, MCP-dependent modules have appropriate failure handling instructions, error classification and retry logic are properly specified, and the reconnection procedure is well-defined.

## Glossary

- **Offline_Fallback_Steering**: The `senzing-bootcamp/steering/mcp-offline-fallback.md` file that defines agent behavior when MCP tools are unavailable, including blocked operations, continuable operations, fallback instructions, and reconnection procedures.
- **MCP_Tool**: A tool provided by the Senzing MCP server at `mcp.senzing.com`, including `sdk_guide`, `mapping_workflow`, `generate_scaffold`, `get_sdk_reference`, `search_docs`, `explain_error_code`, `get_sample_data`, `get_capabilities`, `analyze_record`, `find_examples`, `reporting_guide`, and `download_resource`.
- **MCP_Dependent_Module**: A bootcamp module whose steering file references one or more MCP_Tools for core operations. Modules 2, 3, 5, 6, and 7 are MCP-dependent.
- **Fallback_Instruction**: A specific set of numbered steps in the Offline_Fallback_Steering that tells the agent what to do when a particular MCP_Tool is unavailable.
- **Reconnection_Procedure**: The ordered sequence of steps in the Offline_Fallback_Steering that defines how the agent detects MCP recovery and resumes normal operations.
- **Blocked_Operation**: An operation listed in the Offline_Fallback_Steering that cannot proceed without a working MCP connection.
- **Continuable_Operation**: An operation listed in the Offline_Fallback_Steering that can proceed without MCP.
- **Module_Steering_File**: A Markdown file in `senzing-bootcamp/steering/` that guides the agent through a specific bootcamp module.
- **Error_Handling_Section**: A section within a Module_Steering_File that defines how the agent should respond to errors, typically referencing `explain_error_code`.
- **MCP_Tool_Decision_Tree**: The `senzing-bootcamp/steering/mcp-tool-decision-tree.md` file that maps bootcamp tasks to the correct MCP tool.
- **Test_Suite**: The collection of pytest test files in `senzing-bootcamp/tests/` that validate power behavior.

## Requirements

### Requirement 1: Offline Fallback Steering Completeness

**User Story:** As a power maintainer, I want tests that verify the offline fallback steering file covers all MCP tools used by the bootcamp, so that no tool failure goes unaddressed.

#### Acceptance Criteria

1. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that every MCP_Tool listed in `mcp-tool-decision-tree.md` has a corresponding entry in the Blocked_Operation table of the Offline_Fallback_Steering.
2. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that every Blocked_Operation in the Offline_Fallback_Steering has a non-empty Fallback_Instruction section with at least two numbered steps.
3. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that no Fallback_Instruction contains phrases that violate the "do not guess" principle (such as "guess", "assume", "probably", or "might be").
4. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that every Fallback_Instruction references at least one concrete alternative resource (a URL, a local file path, or a command).
5. FOR ALL MCP_Tools that appear in the Blocked_Operation table, parsing the tool name from the table and checking for a matching Fallback_Instruction section SHALL produce a one-to-one correspondence (round-trip property).

### Requirement 2: Module Steering MCP Failure Handling

**User Story:** As a power maintainer, I want tests that verify each MCP-dependent module steering file has inline failure handling or references the offline fallback, so that the agent knows what to do when MCP fails mid-module.

#### Acceptance Criteria

1. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that Module 2 steering (`module-02-sdk-setup.md`) contains either an inline MCP fallback instruction or a reference to `mcp-offline-fallback.md` for each MCP_Tool it uses.
2. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that Module 3 steering (`module-03-quick-demo.md`) contains an inline MCP fallback instruction for `get_sample_data` that provides an alternative data source.
3. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that Module 5 Phase 2 steering (`module-05-phase2-data-mapping.md`) contains either an inline MCP fallback instruction or a reference to `mcp-offline-fallback.md` for `mapping_workflow`.
4. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that Module 6 steering files contain either an inline MCP fallback instruction or a reference to `mcp-offline-fallback.md` for `generate_scaffold`.
5. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that Module 7 steering (`module-07-query-validation.md`) contains either an inline MCP fallback instruction or a reference to `mcp-offline-fallback.md` for each MCP_Tool it uses.
6. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that every Error_Handling_Section in MCP_Dependent_Modules references `explain_error_code` and includes a fallback path for when that tool is unavailable.

### Requirement 3: Reconnection Procedure Verification

**User Story:** As a power maintainer, I want tests that verify the reconnection procedure is complete and ordered correctly, so that the agent can reliably detect MCP recovery and resume operations.

#### Acceptance Criteria

1. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the Reconnection_Procedure contains exactly six ordered steps: initial failure retry, enter offline mode, periodic retry, verify recovery, resume operations, and re-query stale data.
2. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the Reconnection_Procedure specifies a concrete retry interval (a number followed by "minutes").
3. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the Reconnection_Procedure references `get_capabilities` as the verification call after recovery.
4. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the Reconnection_Procedure references `agent-instructions.md` for reuse rules governing stale data re-query.
5. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the six reconnection steps appear in the correct sequential order within the document (step N appears before step N+1).

### Requirement 4: Connectivity Troubleshooting Completeness

**User Story:** As a power maintainer, I want tests that verify the connectivity troubleshooting section covers common failure modes, so that bootcampers can self-diagnose MCP connection issues.

#### Acceptance Criteria

1. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the Offline_Fallback_Steering contains a troubleshooting table with at least five distinct failure scenarios.
2. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that each troubleshooting entry has both an "Issue" column value and a "Fix" column value that is non-empty.
3. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the troubleshooting section includes entries for: corporate proxy, network connectivity, MCP server not started, intermittent timeouts, and DNS resolution failure.
4. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that at least one troubleshooting entry contains a diagnostic command (a code-formatted string the bootcamper can run).

### Requirement 5: Bootcamper Communication Template

**User Story:** As a power maintainer, I want tests that verify the offline communication template contains all required elements, so that the agent provides consistent and helpful messaging when MCP is down.

#### Acceptance Criteria

1. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the Offline_Fallback_Steering contains a "What to Tell the Bootcamper" section with a message template.
2. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the message template mentions what the bootcamper can continue working on during the outage.
3. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the message template mentions what operations are blocked and will resume when MCP returns.
4. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the message template indicates the agent will retry periodically.
5. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the message template offers fallback steps for blocked operations.

### Requirement 6: Continuable Operations Coverage

**User Story:** As a power maintainer, I want tests that verify the continuable operations list is comprehensive and organized, so that the agent can guide bootcampers productively during MCP outages.

#### Acceptance Criteria

1. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the Offline_Fallback_Steering lists at least four categories of continuable operations.
2. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that each continuable operation category includes a "Modules" column indicating which modules it applies to.
3. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that each continuable operation category includes a "What to do" column with actionable instructions.
4. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the continuable operations include at least one entry for data preparation, documentation, and code maintenance activities.
5. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that no continuable operation references an MCP_Tool as a required dependency.

### Requirement 7: MCP Tool Decision Tree Consistency

**User Story:** As a power maintainer, I want tests that verify the MCP tool decision tree is consistent with the offline fallback steering, so that tools referenced in one document are addressed in the other.

#### Acceptance Criteria

1. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that every MCP_Tool with a "Call Pattern Example" in the MCP_Tool_Decision_Tree has a corresponding entry in either the Blocked_Operation table or the Fallback_Instruction sections of the Offline_Fallback_Steering.
2. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the MCP_Tool_Decision_Tree anti-patterns table references at least three MCP_Tools that also appear in the Offline_Fallback_Steering Blocked_Operation table.
3. WHEN the Test_Suite runs, THE Test_Suite SHALL verify that the `get_capabilities` tool referenced in the MCP_Tool_Decision_Tree as a session-start check is also referenced in the Reconnection_Procedure as the recovery verification call.
4. FOR ALL MCP_Tools extracted from the decision tree call pattern examples, the set of tools SHALL be a superset of the tools listed in the Offline_Fallback_Steering Blocked_Operation table (every blocked tool is documented in the decision tree).

### Requirement 8: Property-Based Validation of Fallback Instruction Structure

**User Story:** As a power maintainer, I want property-based tests that validate structural invariants of the fallback instructions across arbitrary tool names and failure scenarios, so that the steering file maintains consistent quality as new tools are added.

#### Acceptance Criteria

1. FOR ALL Fallback_Instructions in the Offline_Fallback_Steering, each instruction SHALL contain at least two and no more than ten numbered steps.
2. FOR ALL Fallback_Instructions in the Offline_Fallback_Steering, no instruction SHALL contain a step that references calling an MCP_Tool (since the fallback assumes MCP is unavailable).
3. FOR ALL Blocked_Operations in the Offline_Fallback_Steering, the tool name in the Blocked_Operation table SHALL appear in backtick-formatted code within the corresponding Fallback_Instruction heading.
4. FOR ALL entries in the Continuable_Operations tables, the "What to do" column SHALL contain at least one actionable verb (such as "check", "run", "read", "create", "copy", "update", "review", "write", "document", or "commit").
