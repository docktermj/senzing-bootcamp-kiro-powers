# Requirements Document

## Introduction

The Senzing Bootcamp Power's `common-pitfalls.md` steering file contains a detailed "MCP Server Unavailable" section (expanded in spec #2, mcp-failure-recovery) that provides agent-facing guidance during MCP outages. However, there is no standalone user-facing guide that bootcampers can read directly to understand what works without MCP, which modules are affected, and how to reconnect. When MCP is unavailable, bootcampers have no self-service resource — they depend entirely on the agent to relay information from the steering file.

This feature creates a new user-facing guide at `senzing-bootcamp/docs/guides/OFFLINE_MODE.md` that explains offline capabilities per module, references the agent-specific MCP failure details in `common-pitfalls.md`, includes reconnection steps, and is listed in the guides README.

## Glossary

- **Bootcamper**: The human user working through the Senzing Bootcamp modules
- **Offline_Mode**: The state in which the Senzing MCP server is unreachable and certain MCP-dependent operations cannot be performed
- **Guide**: A user-facing markdown document in `senzing-bootcamp/docs/guides/` that bootcampers read directly
- **Guides_README**: The index file at `senzing-bootcamp/docs/guides/README.md` that lists all available guides
- **MCP_Server**: The Senzing MCP server that provides tools for attribute mapping, code generation, error diagnosis, SDK reference lookup, and documentation search
- **Module**: A numbered unit of the Senzing Bootcamp curriculum (Modules 0 through 12)

## Requirements

### Requirement 1: Create Offline Mode Guide

**User Story:** As a bootcamper, I want a standalone guide explaining what I can do when MCP is unavailable, so that I can continue making progress without waiting for the agent to tell me what is and is not blocked.

#### Acceptance Criteria

1. THE Guide SHALL be created at the path `senzing-bootcamp/docs/guides/OFFLINE_MODE.md`
2. THE Guide SHALL include an introduction explaining what offline mode means and when it applies (MCP server unreachable due to network issues, proxy blocks, or server outage)
3. THE Guide SHALL be written for the bootcamper audience using clear, non-technical language where possible

### Requirement 2: Per-Module Offline Capability Summary

**User Story:** As a bootcamper, I want to know which modules work fully offline, which are partially blocked, and which specific activities are affected, so that I can plan my work during an outage.

#### Acceptance Criteria

1. THE Guide SHALL categorize modules into three tiers: fully offline (no MCP needed for any activity), partially blocked (some activities need MCP), and the fact that no module is completely blocked (all have some offline capability)
2. THE Guide SHALL list Modules 2, 3, and parts of Module 4 as fully offline capable
3. THE Guide SHALL list Modules 5, 6, and 8 as partially blocked, identifying which specific activities within each module require MCP
4. THE Guide SHALL list Modules 0, 1, 7, and 9 through 12 with their specific MCP dependencies and offline-capable activities
5. THE Guide SHALL present the per-module information in a scannable format (table or structured list) so bootcampers can quickly find their current module

### Requirement 3: Reconnection Steps

**User Story:** As a bootcamper, I want to know what steps I can try to restore MCP connectivity, so that I can attempt self-service recovery before asking for help.

#### Acceptance Criteria

1. THE Guide SHALL include a reconnection section with steps the bootcamper can try: checking network connectivity, verifying proxy settings, restarting the MCP server connection in the IDE, and contacting support if issues persist
2. THE Guide SHALL include the specific endpoint to verify connectivity against (`mcp.senzing.com:443`)
3. THE Guide SHALL include a command the bootcamper can run to test connectivity (e.g., `curl` command)

### Requirement 4: Cross-Reference to Agent-Specific Details

**User Story:** As a bootcamper, I want to know where the agent gets its offline behavior instructions, so that I understand the agent is following a defined procedure and can reference it if needed.

#### Acceptance Criteria

1. THE Guide SHALL reference the "MCP Server Unavailable" section in `steering/common-pitfalls.md` as the source of agent-specific fallback behavior
2. THE Guide SHALL explain that the agent automatically follows fallback procedures during MCP outages, so the bootcamper does not need to memorize the details

### Requirement 5: Update Guides README

**User Story:** As a bootcamper, I want the offline mode guide listed in the guides README, so that I can discover it when browsing available documentation.

#### Acceptance Criteria

1. THE Guides_README SHALL include an entry for `OFFLINE_MODE.md` with a brief description
2. THE Guides_README SHALL place the entry in the Troubleshooting section or a similarly appropriate section
3. THE Guides_README SHALL update the documentation structure tree to include `OFFLINE_MODE.md`
