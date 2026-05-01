# Requirements Document

## Introduction

The senzing-bootcamp power exposes 12 MCP tools through the Senzing MCP server, but agent-instructions.md provides only a compressed one-liner mapping and POWER.md lists tools without structured decision guidance. When the agent encounters a bootcamper task, it must infer which tool to call from scattered hints. This leads to incorrect tool selection (e.g., hand-coding JSON instead of calling `mapping_workflow`, or guessing SDK signatures instead of calling `generate_scaffold`). A dedicated decision tree steering file will map common bootcamp tasks to the correct MCP tool, include "when NOT to use" anti-patterns, and provide call-pattern examples for each tool — giving the agent a single, authoritative lookup for tool selection.

## Glossary

- **Decision_Tree_File**: A Markdown steering file at `senzing-bootcamp/steering/mcp-tool-decision-tree.md` that contains structured decision logic mapping bootcamp tasks to the correct MCP tool. Loaded on demand by the agent when selecting MCP tools.
- **MCP_Tool**: One of the 12 tools exposed by the Senzing MCP server: `get_capabilities`, `mapping_workflow`, `generate_scaffold`, `get_sample_data`, `search_docs`, `explain_error_code`, `analyze_record`, `sdk_guide`, `find_examples`, `get_sdk_reference`, `reporting_guide`, `download_resource`.
- **Task_Category**: A grouping of related bootcamp activities that share a common MCP tool selection path (e.g., "data mapping tasks", "SDK code generation tasks", "error diagnosis tasks").
- **Decision_Node**: A question or condition in the Decision_Tree_File that guides the agent toward the correct MCP_Tool based on the bootcamper's current task.
- **Anti_Pattern_Entry**: A "when NOT to use" directive in the Decision_Tree_File that warns the agent against a specific incorrect tool selection or manual approach.
- **Call_Pattern_Example**: A concrete example in the Decision_Tree_File showing the correct invocation of an MCP_Tool with representative parameters for a given task.
- **Steering_Index**: The YAML file at `senzing-bootcamp/steering/steering-index.yaml` that maps keywords and filenames to steering files and tracks token counts.
- **Agent_Instructions**: The always-loaded steering file at `senzing-bootcamp/steering/agent-instructions.md` that contains core agent rules including MCP usage guidance.

## Requirements

### Requirement 1: Decision Tree Steering File Creation

**User Story:** As a power maintainer, I want a dedicated steering file that contains a structured decision tree for MCP tool selection, so that the agent has a single authoritative reference for choosing the correct tool.

#### Acceptance Criteria

1. THE Decision_Tree_File SHALL be located at `senzing-bootcamp/steering/mcp-tool-decision-tree.md`
2. THE Decision_Tree_File SHALL contain YAML frontmatter with `inclusion: manual` so that it is loaded on demand rather than consuming context budget by default
3. THE Decision_Tree_File SHALL begin with a summary section explaining its purpose: mapping bootcamp tasks to the correct MCP_Tool
4. THE Decision_Tree_File SHALL organize Decision_Nodes into a hierarchical structure where the top-level question identifies the Task_Category and subsequent questions narrow to a specific MCP_Tool

### Requirement 2: Complete MCP Tool Coverage

**User Story:** As a power maintainer, I want the decision tree to cover every MCP tool available from the Senzing MCP server, so that no tool is overlooked when the agent selects a tool for a task.

#### Acceptance Criteria

1. THE Decision_Tree_File SHALL contain at least one Decision_Node path leading to each of the 12 MCP_Tools: `get_capabilities`, `mapping_workflow`, `generate_scaffold`, `get_sample_data`, `search_docs`, `explain_error_code`, `analyze_record`, `sdk_guide`, `find_examples`, `get_sdk_reference`, `reporting_guide`, `download_resource`
2. WHEN a new session begins, THE Decision_Tree_File SHALL direct the agent to call `get_capabilities` first before using any other MCP_Tool
3. THE Decision_Tree_File SHALL group MCP_Tools into Task_Categories that reflect common bootcamp workflows (e.g., data preparation, SDK development, troubleshooting, reference lookup)

### Requirement 3: Task-to-Tool Decision Nodes

**User Story:** As a power maintainer, I want the decision tree to contain clear question-based decision nodes, so that the agent can follow a deterministic path from a bootcamper's task to the correct MCP tool.

#### Acceptance Criteria

1. WHEN the agent needs to determine which MCP_Tool to use, THE Decision_Tree_File SHALL provide a top-level Decision_Node that asks "What is the bootcamper trying to do?" with branches for each Task_Category
2. WHEN the Task_Category is "data preparation", THE Decision_Tree_File SHALL provide Decision_Nodes that distinguish between mapping raw data (`mapping_workflow`), validating mapped records (`analyze_record`), downloading sample datasets (`get_sample_data`), and downloading workflow resources (`download_resource`)
3. WHEN the Task_Category is "SDK development", THE Decision_Tree_File SHALL provide Decision_Nodes that distinguish between generating code scaffolds (`generate_scaffold`), getting installation guidance (`sdk_guide`), looking up method signatures (`get_sdk_reference`), and finding working code examples (`find_examples`)
4. WHEN the Task_Category is "troubleshooting", THE Decision_Tree_File SHALL provide Decision_Nodes that distinguish between diagnosing error codes (`explain_error_code`) and searching documentation for solutions (`search_docs`)
5. WHEN the Task_Category is "reference and reporting", THE Decision_Tree_File SHALL provide Decision_Nodes that distinguish between searching documentation (`search_docs`), getting reporting guidance (`reporting_guide`), and discovering available tools (`get_capabilities`)

### Requirement 4: Anti-Pattern Guidance

**User Story:** As a power maintainer, I want the decision tree to include "when NOT to use" directives, so that the agent avoids common mistakes like hand-coding Senzing JSON or guessing SDK method names.

#### Acceptance Criteria

1. THE Decision_Tree_File SHALL contain an Anti_Pattern_Entry stating that the agent SHALL use `mapping_workflow` instead of hand-coding Senzing JSON mappings
2. THE Decision_Tree_File SHALL contain an Anti_Pattern_Entry stating that the agent SHALL use `generate_scaffold` or `sdk_guide` instead of guessing SDK method names or signatures
3. THE Decision_Tree_File SHALL contain an Anti_Pattern_Entry stating that the agent SHALL use `get_sdk_reference` instead of relying on training data for SDK method signatures and flags
4. THE Decision_Tree_File SHALL contain an Anti_Pattern_Entry stating that the agent SHALL call `search_docs` with category `anti_patterns` before recommending approaches for Senzing integration
5. THE Decision_Tree_File SHALL contain an Anti_Pattern_Entry stating that the agent SHALL use `explain_error_code` instead of guessing the meaning of Senzing error codes
6. THE Decision_Tree_File SHALL contain an Anti_Pattern_Entry stating that the agent SHALL use `get_sample_data` instead of fabricating sample datasets
7. WHEN an Anti_Pattern_Entry is violated, THE Decision_Tree_File SHALL describe the consequence of the incorrect approach (e.g., "hand-coded mappings use wrong attribute names and produce silent data loss")

### Requirement 5: Call Pattern Examples

**User Story:** As a power maintainer, I want the decision tree to include concrete call-pattern examples for each MCP tool, so that the agent knows the correct invocation syntax and representative parameters.

#### Acceptance Criteria

1. THE Decision_Tree_File SHALL contain at least one Call_Pattern_Example for each of the 12 MCP_Tools
2. WHEN a Call_Pattern_Example is provided, THE Decision_Tree_File SHALL show the tool name, required parameters, and representative parameter values that match a common bootcamp scenario
3. WHEN an MCP_Tool accepts optional parameters, THE Decision_Tree_File SHALL show at least one Call_Pattern_Example that includes the optional parameters with an explanation of when to use them
4. THE Decision_Tree_File SHALL present Call_Pattern_Examples in a consistent format using code blocks with the tool name and parameters clearly labeled

### Requirement 6: Steering Index Registration

**User Story:** As a power maintainer, I want the decision tree file to be registered in the steering index, so that the agent can discover and load it using the standard file selection mechanism.

#### Acceptance Criteria

1. WHEN the Decision_Tree_File is created, THE Steering_Index SHALL be updated to include `mcp-tool-decision-tree.md` in the `file_metadata` section with accurate `token_count` and `size_category` values
2. WHEN the Decision_Tree_File is created, THE Steering_Index SHALL be updated to include keyword entries in the `keywords` section that map relevant terms (e.g., `mcp tool`, `tool selection`, `which tool`, `decision tree`) to `mcp-tool-decision-tree.md`
3. THE Steering_Index keyword entries SHALL enable the agent to locate the Decision_Tree_File when a bootcamper asks questions like "which tool should I use" or "how do I map data"

### Requirement 7: Agent Instructions Cross-Reference

**User Story:** As a power maintainer, I want agent-instructions.md to reference the decision tree file, so that the agent knows to load it when making MCP tool selection decisions.

#### Acceptance Criteria

1. WHEN the Decision_Tree_File is created, THE Agent_Instructions MCP Rules section SHALL include a directive to load `mcp-tool-decision-tree.md` when the agent is uncertain which MCP_Tool to use for a task
2. THE Agent_Instructions cross-reference SHALL not duplicate the decision tree content but instead point to the Decision_Tree_File as the authoritative source for tool selection logic
3. THE Agent_Instructions existing one-liner tool mapping (the `Attribute names → mapping_workflow | SDK code → generate_scaffold` line) SHALL remain as a quick-reference summary, with the Decision_Tree_File serving as the detailed reference

### Requirement 8: Structural Consistency with Steering Conventions

**User Story:** As a power maintainer, I want the decision tree file to follow the same structural conventions as other steering files, so that it integrates cleanly into the existing power.

#### Acceptance Criteria

1. THE Decision_Tree_File SHALL use Markdown formatting consistent with other steering files in `senzing-bootcamp/steering/`
2. THE Decision_Tree_File SHALL include YAML frontmatter with an `inclusion` key set to `manual`
3. THE Decision_Tree_File SHALL use heading levels consistent with other steering files (H1 for the file title, H2 for major sections, H3 for subsections)
4. IF the Decision_Tree_File exceeds 5000 tokens, THEN the file SHALL be reviewed for splitting per the `split_threshold_tokens` policy in the Steering_Index budget section
