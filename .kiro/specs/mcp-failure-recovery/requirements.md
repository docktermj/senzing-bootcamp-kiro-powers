# Requirements Document

## Introduction

The `common-pitfalls.md` steering file in the Senzing Bootcamp Power contains an "MCP Server Unavailable" section that provides a high-level overview of what works without MCP and what is blocked. However, the current section lacks specificity: it does not clearly categorize operations by their MCP tool dependency, does not provide actionable fallback instructions for each blocked operation, and does not include reconnection procedures. The `agent-instructions.md` file references this section ("load `common-pitfalls.md` MCP Server Unavailable section for what's blocked vs. what can continue") but the section does not deliver enough detail for the agent to act autonomously during an outage.

This feature expands the existing "MCP Server Unavailable" section in `senzing-bootcamp/steering/common-pitfalls.md` with explicit tool-level categorization, per-operation fallback instructions, and reconnection procedures. All existing content in the file must be preserved.

## Glossary

- **Agent**: The AI assistant that reads steering files and guides bootcampers through the Senzing Bootcamp
- **Bootcamper**: The human user working through the bootcamp modules
- **MCP_Server**: The Senzing MCP server that provides tools for attribute mapping, code generation, error diagnosis, SDK reference lookup, and documentation search
- **Blocked_Operation**: An operation that cannot be performed without a functioning MCP server connection because it depends on an MCP tool
- **Continuable_Operation**: An operation that can proceed without MCP because it relies only on local files, existing code, or general knowledge
- **Fallback_Instruction**: A specific alternative action the agent should take when an MCP-dependent operation is requested but the MCP server is unavailable
- **Reconnection_Procedure**: A sequence of steps the agent follows to detect MCP server recovery and resume normal operations
- **Steering_File**: A markdown file loaded by the AI agent at runtime that provides workflow instructions and behavioral rules

## Requirements

### Requirement 1: Explicit Blocked Operations Categorization

**User Story:** As an AI agent, I want a clear list of operations that are blocked when the MCP server is unavailable with their specific MCP tool dependencies, so that I can immediately determine whether a requested action can proceed.

#### Acceptance Criteria

1. THE Steering_File SHALL list the following operations as blocked with their MCP tool dependency: attribute mapping (`mapping_workflow`), code generation (`generate_scaffold`), error diagnosis (`explain_error_code`), SDK reference lookup (`get_sdk_reference`), and documentation search (`search_docs`)
2. WHEN the Agent encounters a blocked operation during MCP unavailability, THE Steering_File SHALL provide the specific MCP tool name that is required so the agent can explain the dependency to the bootcamper
3. THE Steering_File SHALL indicate which bootcamp modules are most affected by each blocked operation

### Requirement 2: Explicit Continuable Operations Categorization

**User Story:** As an AI agent, I want a clear list of operations that can continue without MCP, so that I can keep the bootcamper productive during an outage.

#### Acceptance Criteria

1. THE Steering_File SHALL list the following operations as continuable without MCP: data collection (file operations), documentation writing, code review, project structure setup, database backup and restore, and running existing code
2. THE Steering_File SHALL explain why each continuable operation does not require MCP (e.g., relies on local files only, uses existing artifacts)
3. THE Steering_File SHALL group continuable operations by the type of work they support (e.g., data preparation, documentation, code maintenance)

### Requirement 3: Per-Operation Fallback Instructions

**User Story:** As an AI agent, I want specific fallback instructions for each blocked operation, so that I can provide the bootcamper with an alternative path instead of simply saying "wait for MCP."

#### Acceptance Criteria

1. WHEN attribute mapping is blocked, THE Steering_File SHALL instruct the Agent to refer the bootcamper to docs.senzing.com entity specification documentation and to check `docs/mapping_*.md` from previous sessions
2. WHEN code generation is blocked, THE Steering_File SHALL instruct the Agent to check `src/` for existing scaffold code that can be adapted and to reference previously generated examples
3. WHEN error diagnosis is blocked, THE Steering_File SHALL instruct the Agent to instruct the bootcamper to note the error code and message, check docs.senzing.com, or email support@senzing.com
4. WHEN SDK reference lookup is blocked, THE Steering_File SHALL instruct the Agent to direct the bootcamper to the Senzing SDK documentation at docs.senzing.com and to check existing code in `src/` for usage patterns
5. WHEN documentation search is blocked, THE Steering_File SHALL instruct the Agent to direct the bootcamper to browse docs.senzing.com directly in their browser
6. THE Steering_File SHALL present each fallback as an actionable step the agent can execute immediately, not as a general suggestion

### Requirement 4: Reconnection Procedures

**User Story:** As an AI agent, I want a defined reconnection procedure, so that I can detect when the MCP server is available again and resume normal operations smoothly.

#### Acceptance Criteria

1. THE Steering_File SHALL include a reconnection procedure that instructs the Agent to retry the MCP connection periodically after a failure
2. THE Steering_File SHALL instruct the Agent to call `get_capabilities` as the first MCP call after reconnection to verify full server functionality
3. WHEN the MCP server reconnects, THE Steering_File SHALL instruct the Agent to inform the bootcamper that MCP is available again and list any previously blocked operations that can now resume
4. THE Steering_File SHALL include common connectivity troubleshooting steps: checking proxy settings, verifying network access to `mcp.senzing.com:443`, and restarting the MCP connection

### Requirement 5: Preserve Existing Content

**User Story:** As a power developer, I want all existing content in `common-pitfalls.md` to remain intact, so that the file continues to serve its current purpose while gaining the new MCP failure detail.

#### Acceptance Criteria

1. THE Steering_File SHALL retain all existing sections, tables, and content outside the MCP Server Unavailable section without modification
2. THE expanded MCP Server Unavailable section SHALL replace the existing section in-place, preserving the section heading and expanding its content
3. THE Steering_File SHALL maintain the existing YAML front matter (`inclusion: manual`) and document structure
