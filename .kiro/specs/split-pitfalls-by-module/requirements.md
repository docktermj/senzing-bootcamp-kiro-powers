# Requirements Document

## Introduction

The `common-pitfalls.md` steering file in the Senzing Bootcamp Power is 500+ lines and covers pitfalls for all 12 modules plus general pitfalls and MCP failure recovery. When the agent loads this file for a specific module issue (e.g., a Module 5 data mapping problem), it receives all 12 modules' pitfalls in context, wasting context window space.

Rather than splitting the file into separate per-module files (which would break the existing `agent-instructions.md` reference to "load `common-pitfalls.md`" and fragment the single source of truth), this feature adds in-file navigation to `common-pitfalls.md`. A Quick Navigation section with anchor links at the top of the file enables the agent to reference specific module sections directly. HTML anchor tags on each module section heading support direct linking. A note in the Guided Troubleshooting section reminds the agent to jump to the relevant module section rather than presenting the entire file.

All existing content in the file remains intact.

## Glossary

- **Agent**: The AI assistant that reads steering files and guides bootcampers through the Senzing Bootcamp
- **Steering_File**: A markdown file loaded by the AI agent at runtime that provides workflow instructions and behavioral rules
- **Quick_Navigation**: A table of contents section at the top of the steering file containing anchor links to each module section
- **Anchor_Tag**: An HTML `<a>` element with a `name` or `id` attribute placed at a section heading to enable direct linking
- **Module_Section**: A heading and its associated pitfall table within `common-pitfalls.md` corresponding to a specific bootcamp module
- **Context_Window**: The limited amount of text an AI agent can process at one time; reducing irrelevant content improves agent effectiveness

## Requirements

### Requirement 1: Quick Navigation Section

**User Story:** As an AI agent, I want a Quick Navigation section at the top of `common-pitfalls.md` with anchor links to each module section, so that I can jump directly to the relevant module pitfalls without scanning the entire file.

#### Acceptance Criteria

1. THE Steering_File SHALL contain a Quick Navigation section placed after the introductory paragraph and before the Guided Troubleshooting section
2. THE Quick_Navigation section SHALL contain anchor links to every module section in the file: Module 0 through Module 12, General Pitfalls, MCP Server Unavailable, and Recovery Quick Reference
3. THE Quick_Navigation section SHALL present the links in a compact, scannable format (e.g., a list or table of contents)

### Requirement 2: HTML Anchor Tags on Module Sections

**User Story:** As an AI agent, I want HTML anchor tags on each module section heading, so that the Quick Navigation links have valid targets to jump to.

#### Acceptance Criteria

1. THE Steering_File SHALL include an HTML anchor tag immediately before or within each module section heading (Module 0 through Module 12, General Pitfalls, MCP Server Unavailable, Recovery Quick Reference)
2. THE Anchor_Tag identifiers SHALL follow a consistent naming convention (e.g., `module-0`, `module-1`, `general-pitfalls`, `mcp-unavailable`, `recovery`)
3. THE Anchor_Tag identifiers SHALL match the href targets used in the Quick Navigation section

### Requirement 3: Guided Troubleshooting Navigation Reminder

**User Story:** As an AI agent, I want a reminder in the Guided Troubleshooting section to jump to the relevant module section after identifying the module, so that I present only the matching pitfalls instead of the entire file.

#### Acceptance Criteria

1. THE Guided Troubleshooting section SHALL include a note after the diagnostic questions reminding the Agent to navigate to the specific module section using the anchor links
2. THE note SHALL explicitly state that the Agent should present only the matching pitfall and fix, not the entire file content

### Requirement 4: Preserve Existing Content

**User Story:** As a power developer, I want all existing content in `common-pitfalls.md` to remain intact, so that the file continues to serve its current purpose while gaining navigation improvements.

#### Acceptance Criteria

1. THE Steering_File SHALL retain all existing sections, tables, and content without modification to their substance
2. THE Steering_File SHALL maintain the existing YAML front matter (`inclusion: manual`) and document structure
3. THE existing reference in `agent-instructions.md` to "load `common-pitfalls.md`" SHALL remain valid without any changes to that file
