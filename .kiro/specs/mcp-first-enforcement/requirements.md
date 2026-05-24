# Requirements Document

## Introduction

The Module 5 steering file (`module-05-phase1-quality-assessment.md`) contains hardcoded Senzing Entity Specification attribute lists in Steps 3, 4, and 5. This violates the project's MCP-first principle: all Senzing facts must come from MCP tools, never from training data or static content embedded in steering files. Hardcoded lists become stale when the Entity Specification evolves and cause the agent to skip MCP calls entirely. This fix removes the hardcoded attributes and adds explicit `download_resource(filename="senzing_entity_specification.md")` call instructions so the agent always retrieves the current specification at runtime.

## Glossary

- **Steering_File**: A Markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that provides workflow instructions to the agent
- **Entity_Specification**: The Senzing Generic Entity Specification document defining all valid attribute names, types, and structures for entity resolution input records
- **MCP_Tool**: A tool provided by the Senzing MCP server (`mcp.senzing.com`) that the agent calls at runtime to retrieve authoritative Senzing information
- **download_resource**: An MCP tool that retrieves named workflow resources by filename, including `senzing_entity_specification.md`
- **Agent**: The AI assistant executing the bootcamp steering file instructions on behalf of the user
- **Hardcoded_Attribute_List**: A static enumeration of Entity Specification attribute names embedded directly in a steering file

## Requirements

### Requirement 1: Remove hardcoded attribute list from Step 3

**User Story:** As a bootcamp maintainer, I want Step 3 to contain no hardcoded Entity Specification attributes, so that the agent always retrieves the current specification from MCP rather than relying on potentially stale inline content.

#### Acceptance Criteria

1. THE Steering_File SHALL NOT contain any inline enumeration of Entity Specification attribute names in Step 3.
2. WHEN the Agent executes Step 3, THE Steering_File SHALL instruct the Agent to call `download_resource` with `filename="senzing_entity_specification.md"` to retrieve the current Entity Specification.
3. THE Steering_File SHALL instruct the Agent to use the downloaded Entity Specification content as the authoritative source for attribute names, types, and structures.

### Requirement 2: Remove hardcoded attribute references from Step 4

**User Story:** As a bootcamp maintainer, I want Step 4 to reference the MCP-retrieved Entity Specification rather than hardcoded attribute examples, so that field mapping guidance stays current with the specification.

#### Acceptance Criteria

1. THE Steering_File SHALL NOT contain hardcoded Entity Specification attribute names as mapping examples in Step 4.
2. THE Steering_File SHALL instruct the Agent to reference the Entity Specification retrieved via `download_resource` in Step 3 when comparing data source fields to valid attributes.
3. THE Steering_File SHALL retain the general mapping workflow structure (identify direct maps, transformations, non-standard names, missing fields, required fields) without embedding specific attribute names.

### Requirement 3: Remove hardcoded attribute references from Step 5

**User Story:** As a bootcamp maintainer, I want Step 5 to use generic Entity Specification references rather than hardcoded attribute names, so that categorization logic does not depend on a static attribute list.

#### Acceptance Criteria

1. THE Steering_File SHALL NOT contain hardcoded Entity Specification attribute names in Step 5.
2. THE Steering_File SHALL reference "standard Senzing attribute names" generically when describing the Entity Specification-compliant category, relying on the specification retrieved in Step 3 as the source of truth.

### Requirement 4: MCP call instruction placement and format

**User Story:** As a bootcamp maintainer, I want the `download_resource` call instruction to appear exactly once in Step 3 with clear formatting, so that the agent knows precisely which MCP tool to call and with what parameters.

#### Acceptance Criteria

1. THE Steering_File SHALL contain exactly one `download_resource` call instruction across Steps 3, 4, and 5.
2. THE Steering_File SHALL place the `download_resource` call instruction in Step 3 before any reference to Entity Specification content.
3. THE Steering_File SHALL specify the exact tool call as `download_resource(filename="senzing_entity_specification.md")`.
4. THE Steering_File SHALL instruct the Agent to use the retrieved content for all subsequent steps that reference the Entity Specification.

### Requirement 5: No inline fallback content

**User Story:** As a bootcamp maintainer, I want the steering file to contain zero inline fallback attribute lists, so that there is no path for the agent to bypass the MCP call.

#### Acceptance Criteria

1. THE Steering_File SHALL NOT contain any fallback, summary, or example list of Entity Specification attribute names in Steps 3, 4, or 5.
2. IF the `download_resource` call fails, THEN THE Steering_File SHALL NOT provide cached or inline attribute data as an alternative.
