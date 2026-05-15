# Requirements Document

## Introduction

The Senzing Bootcamp Kiro Power currently maintains extensive offline/fallback infrastructure for when the Senzing MCP server is unavailable. This includes a dedicated offline mode guide, agent-facing fallback steering, graceful degradation logic in multiple steering files, and periodic reconnection procedures. The decision has been made that the Senzing MCP server is **required** for the bootcamp to function — there is no meaningful bootcamp experience without it.

This feature removes all offline mode handling, graceful degradation, and fallback logic. The MCP health check becomes a hard gate: if MCP is unreachable, the bootcamp blocks until the connection is fixed. This simplifies agent behavior, reduces token budget consumption, and eliminates dual-mode logic that added complexity without real value.

## Glossary

- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` that provides code generation, fact lookup, SDK references, mapping workflows, and sample data tools.
- **Health_Check**: A lightweight MCP tool call (`search_docs`) used to verify the MCP server is reachable before proceeding with the bootcamp.
- **Hard_Gate**: A blocking check that prevents the bootcamp from proceeding until the condition is met (MCP is reachable). Contrasted with the current "soft gate" that offers offline mode as an alternative.
- **Offline_Mode**: The current fallback behavior where the bootcamp continues with limited functionality when MCP is unavailable. To be removed.
- **Fallback_Logic**: Conditional code paths in steering files that provide alternative behavior when MCP tools are unavailable. To be removed.
- **MCP_Status_File**: The file `config/.mcp_status` currently used to track MCP server state across sessions. To be removed.
- **Connectivity_Troubleshooting**: Instructions for fixing MCP connection issues (proxy settings, DNS, firewall allowlisting). To be preserved in the health check failure message.

## Requirements

### Requirement 1: Delete offline mode documentation

**User Story:** As a power maintainer, I want the offline mode guide removed, so that bootcampers are not given the false impression that the bootcamp can function without MCP.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/docs/guides/OFFLINE_MODE.md` SHALL be deleted from the repository.
2. ALL references to `OFFLINE_MODE.md` in other files (including `senzing-bootcamp/POWER.md` and any "See also" links) SHALL be removed.
3. THE file `senzing-bootcamp/steering/mcp-offline-fallback.md` SHALL be deleted from the repository.
4. ALL references to `mcp-offline-fallback.md` in other files (including `senzing-bootcamp/steering/steering-index.yaml`, `senzing-bootcamp/steering/common-pitfalls.md`, and `senzing-bootcamp/steering/agent-instructions.md`) SHALL be removed.

### Requirement 2: Convert MCP health check to a hard gate

**User Story:** As a bootcamper, I want a clear error message and fix instructions when MCP is unreachable, so that I know exactly what to do instead of being offered a degraded experience.

#### Acceptance Criteria

1. THE onboarding flow (`senzing-bootcamp/steering/onboarding-flow.md` Step 0b) SHALL retain the MCP health check probe (`search_docs` call with timeout).
2. WHEN the health check probe succeeds, THE onboarding flow SHALL proceed silently (no change from current behavior).
3. WHEN the health check probe fails, THE onboarding flow SHALL NOT offer "offline mode" or ask whether to continue without MCP.
4. WHEN the health check probe fails, THE onboarding flow SHALL display a blocking error message that includes: (a) what the MCP server provides, (b) that the bootcamp cannot proceed without it, and (c) connectivity troubleshooting steps (check network, test endpoint with curl, check proxy/firewall for `mcp.senzing.com:443`, restart MCP connection in IDE, check DNS resolution).
5. WHEN the health check probe fails, THE onboarding flow SHALL instruct the bootcamper to retry after fixing the connection and SHALL NOT proceed to any subsequent onboarding step.
6. THE session resume flow (`senzing-bootcamp/steering/session-resume.md` Step 2d) SHALL apply the same hard gate behavior as the onboarding flow.

### Requirement 3: Remove MCP status file logic

**User Story:** As a power maintainer, I want the `config/.mcp_status` file tracking removed, so that there is no stale state management for a server that is always required.

#### Acceptance Criteria

1. THE onboarding flow SHALL NOT write to `config/.mcp_status` on health check success or failure.
2. THE session resume flow SHALL NOT write to or read from `config/.mcp_status`.
3. ALL "Mid-Session Recovery" logic that checks `config/.mcp_status` before MCP-dependent steps SHALL be removed.
4. NO steering file SHALL reference `config/.mcp_status` after this change.

### Requirement 4: Remove fallback logic from module steering files

**User Story:** As a power maintainer, I want all "if MCP unavailable" conditional paths removed from module steering files, so that the agent follows a single code path and steering files are simpler.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/steering/entity-resolution-intro.md` SHALL NOT contain any "If MCP unavailable" fallback comments or instructions.
2. THE file `senzing-bootcamp/steering/module-03-quick-demo.md` SHALL NOT contain an inline fallback dataset for when `get_sample_data` fails due to MCP unavailability.
3. THE file `senzing-bootcamp/steering/visualization-guide.md` SHALL NOT contain "Agent guidance — MCP unavailable" notes.
4. THE file `senzing-bootcamp/steering/agent-instructions.md` MCP Failure section SHALL be simplified to: "Retry once. If still failing, tell the bootcamper the MCP server is unreachable and they must fix their connection before continuing. Never fabricate Senzing facts."
5. THE file `senzing-bootcamp/steering/common-pitfalls.md` "MCP Server Unavailable" section SHALL be reduced to connectivity fix instructions only (proxy, DNS, firewall, IDE restart) without referencing offline mode or fallback operations.

### Requirement 5: Remove offline keyword routing from steering index

**User Story:** As a power maintainer, I want the steering index cleaned up so it does not route to a deleted file.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/steering/steering-index.yaml` SHALL NOT contain the keyword routing entry `offline: mcp-offline-fallback.md`.
2. THE file `senzing-bootcamp/steering/steering-index.yaml` SHALL NOT contain the metadata entry for `mcp-offline-fallback.md` (token count, size category).

### Requirement 6: Update POWER.md references

**User Story:** As a bootcamper reading the power overview, I want accurate information about MCP being required, so that I understand the bootcamp's dependencies upfront.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/POWER.md` SHALL NOT reference `OFFLINE_MODE.md` or `mcp-offline-fallback.md` in any section.
2. THE file `senzing-bootcamp/POWER.md` SHALL clearly state that the Senzing MCP server is required for the bootcamp to function.
3. THE file `senzing-bootcamp/POWER.md` troubleshooting section SHALL provide connection fix instructions (proxy, firewall, DNS) instead of referencing an offline mode guide.

### Requirement 8: Remove static glossary file

**User Story:** As a power maintainer, I want the static glossary removed, so that term definitions come from the authoritative MCP server rather than a file that can become stale.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/docs/guides/GLOSSARY.md` SHALL be deleted from the repository.
2. THE onboarding flow SHALL NOT copy `GLOSSARY.md` into the bootcamper's project during Step 1 (the "Copy glossary" step SHALL be removed).
3. THE onboarding flow Step 4 SHALL replace the glossary file reference with guidance to ask the agent to explain any unfamiliar term (the agent uses `search_docs` via MCP to provide definitions on demand).
4. ALL references to `GLOSSARY.md` in documentation files (`FAQ.md`, `GETTING_HELP.md`, `ONBOARDING_CHECKLIST.md`, `docs/README.md`, `docs/guides/README.md`) SHALL be replaced with guidance to ask the agent for term definitions.
5. THE `senzing-bootcamp/steering/agent-instructions.md` reference to `docs/guides/GLOSSARY.md` for first-term explanations SHALL be replaced with an instruction to use `search_docs` from the MCP server to define Senzing terms inline on first use.

### Requirement 9: Remove Senzing domain knowledge guides replaceable by MCP

**User Story:** As a power maintainer, I want static Senzing knowledge guides removed, so that bootcampers receive current, authoritative information from the MCP server rather than documentation that can become stale as the SDK evolves.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/docs/guides/DATA_UPDATES_AND_DELETIONS.md` SHALL be deleted because its content (record updates via `add_record` replace behavior, `delete_record`, entity re-evaluation, redo processing) is available on demand via MCP tools `search_docs`, `get_sdk_reference`, and `generate_scaffold`.
2. THE file `senzing-bootcamp/docs/guides/DESIGN_PATTERNS.md` SHALL be deleted because its content (entity resolution design patterns) is available via `search_docs` and the steering file `steering/design-patterns.md` already contains the full pattern gallery loaded on demand during Module 1.
3. THE file `senzing-bootcamp/docs/guides/INCREMENTAL_LOADING.md` SHALL be deleted because its content (adding records to an existing database, redo scheduling, pipeline monitoring) is available via MCP tools `search_docs`, `generate_scaffold`, and `find_examples`.
4. THE file `senzing-bootcamp/docs/guides/MULTI_LANGUAGE_DATA.md` SHALL be deleted because its content (non-Latin character support, UTF-8 encoding, cross-script matching, transliteration) is available via `search_docs(query="globalization")` and related MCP queries.
5. THE file `senzing-bootcamp/docs/guides/STREAMING_INTEGRATION.md` SHALL be deleted because its content (Kafka/RabbitMQ/SQS consumption patterns, backpressure handling, dead letter queues, delivery semantics) is available via MCP tools `search_docs` and `find_examples`.
6. ALL references to the deleted files in other documentation (including `docs/guides/README.md`, `docs/README.md`, `GETTING_HELP.md`, `COMMON_MISTAKES.md`, `PERFORMANCE_BASELINES.md`, `AFTER_BOOTCAMP.md`, and any "See also" links) SHALL be removed or replaced with guidance to use MCP tools for the relevant topic.
7. THE `senzing-bootcamp/steering/steering-index.yaml` SHALL NOT contain metadata entries for any of the deleted guide files if they are currently tracked there.

### Requirement 10: Preserve connectivity troubleshooting information

**User Story:** As a bootcamper whose MCP connection is failing, I want clear troubleshooting steps presented in the error message, so that I can fix the problem without needing a separate guide.

#### Acceptance Criteria

1. WHEN the MCP health check fails (in onboarding or session resume), THE error message SHALL include these troubleshooting steps: (a) verify general internet connectivity, (b) test the MCP endpoint with `curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443`, (c) check proxy settings and allowlist `mcp.senzing.com:443` if behind a corporate proxy, (d) restart the MCP server connection in the IDE Kiro Powers panel, (e) verify DNS resolution with `nslookup mcp.senzing.com`.
2. THE `senzing-bootcamp/steering/common-pitfalls.md` "MCP Server Unavailable" section SHALL retain the connectivity troubleshooting table (proxy, DNS, network, IDE restart fixes).
3. THE troubleshooting information SHALL NOT reference offline mode, fallback operations, or continuable activities.

### Requirement 11: Replace static Senzing content in steering files with live MCP lookups

**User Story:** As a power maintainer, I want steering files to instruct the agent to call MCP at the point of need rather than embedding hardcoded Senzing facts, so that bootcampers always receive current information and steering files do not go stale.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/steering/entity-resolution-intro.md` SHALL instruct the agent to call `search_docs` to retrieve Senzing-specific claims dynamically rather than presenting static content with a "verify later" fallback comment.
2. THE file `senzing-bootcamp/steering/design-patterns.md` SHALL instruct the agent to use `search_docs` to retrieve current pattern descriptions rather than embedding hardcoded pattern details that may become outdated.
3. WHEN a language steering file (`lang-python.md`, `lang-java.md`, etc.) references SDK method names or signatures, THE file SHALL instruct the agent to call `get_sdk_reference` for current method signatures rather than hardcoding them.
4. NO steering file SHALL contain hardcoded Senzing attribute lists, method signatures, error code tables, or SDK-specific facts that the MCP server can provide dynamically.

### Requirement 12: Remove the verify-senzing-facts hook

**User Story:** As a power maintainer, I want the `verify-senzing-facts` preToolUse hook removed, so that the agent has fewer hooks firing on every write operation while still maintaining the MCP-only rule through simpler means.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/hooks/verify-senzing-facts.kiro.hook` SHALL be deleted.
2. THE `senzing-bootcamp/hooks/hook-categories.yaml` SHALL NOT list `verify-senzing-facts` in the critical hooks section.
3. THE `senzing-bootcamp/steering/hook-registry.md` SHALL NOT contain an entry for `verify-senzing-facts`.
4. THE `senzing-bootcamp/steering/agent-instructions.md` SHALL retain the rule "All Senzing facts must come from MCP tools, never from training data" as a single directive without requiring a hook to enforce it.
5. THE onboarding flow hook failure impact table SHALL NOT contain an entry for `verify-senzing-facts`.
6. THE hook count in `senzing-bootcamp/steering/hook-registry.md` SHALL be decremented to reflect the removal.

### Requirement 13: Simplify onboarding language detection

**User Story:** As a power maintainer, I want the onboarding language detection step simplified now that MCP is guaranteed, so that there is no fallback logic cluttering the flow.

#### Acceptance Criteria

1. THE onboarding flow Step 2 (Language Selection) SHALL call `get_capabilities` or `sdk_guide` without any fallback or timeout-handling logic beyond the hard gate in Step 0b.
2. THE onboarding flow Step 2 SHALL NOT contain conditional paths for "if MCP is unavailable during language detection."
3. THE onboarding flow Step 2 SHALL present the MCP-returned language list directly without defensive checks for empty or error responses (the hard gate in Step 0b guarantees MCP is available).

### Requirement 14: Remove config/.mcp_status from the architecture

**User Story:** As a power maintainer, I want the `config/.mcp_status` file and all logic around it removed from the architecture, so that there is no stale state tracking for a server that is always available.

#### Acceptance Criteria

1. NO steering file SHALL write to, read from, or reference `config/.mcp_status`.
2. THE `senzing-bootcamp/docs/guides/ARCHITECTURE.md` SHALL NOT document `config/.mcp_status` in the configuration files table or data flow diagrams.
3. THE session resume flow SHALL NOT read `config/.mcp_status` as part of state restoration.
4. THE onboarding flow SHALL NOT write `config/.mcp_status` after the health check probe (the probe result is pass/fail only — pass proceeds, fail blocks).

### Requirement 15: Simplify the error-recovery-context hook

**User Story:** As a power maintainer, I want the `error-recovery-context` hook simplified now that MCP is guaranteed, so that it always calls `explain_error_code` for SENZ errors without defensive checks.

#### Acceptance Criteria

1. THE `error-recovery-context` hook prompt SHALL instruct the agent to call `explain_error_code` directly for any SENZ error code without first checking `config/.mcp_status` or verifying MCP availability.
2. THE `error-recovery-context` hook prompt SHALL NOT contain fallback instructions for when MCP is unavailable.
3. THE `error-recovery-context` hook SHALL retain its existing behavior of consulting `common-pitfalls.md` and `recovery-from-mistakes.md` for non-SENZ errors.

### Requirement 16: Remove mid-session MCP recovery patterns from steering files

**User Story:** As a power maintainer, I want all "before any step that requires MCP tools, check .mcp_status" patterns removed from steering files, so that module execution is simpler and does not contain dead code.

#### Acceptance Criteria

1. NO module steering file SHALL contain logic to check MCP availability before executing an MCP-dependent step.
2. NO steering file SHALL contain "Mid-Session Recovery" sections that re-probe MCP and update `.mcp_status`.
3. THE `senzing-bootcamp/steering/session-resume.md` SHALL NOT contain MCP re-probe logic within the resume flow (the hard gate at session start is sufficient).
4. ALL steering files SHALL assume MCP is available and issue MCP tool calls directly without pre-checks.

### Requirement 17: Trim AFTER_BOOTCAMP.md to bootcamp-specific content

**User Story:** As a power maintainer, I want `AFTER_BOOTCAMP.md` reduced to bootcamp-specific operational content only, so that Senzing knowledge is served fresh from MCP rather than a static file.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/docs/guides/AFTER_BOOTCAMP.md` SHALL retain the production maintenance cadence checklist (daily/weekly/monthly/quarterly tasks) because it is bootcamp-specific operational guidance.
2. THE file SHALL retain the "Adding New Data Sources" section that references bootcamp module workflows and iterate-vs-proceed gates.
3. THE file SHALL retain the MCP tool quick-reference table as a convenience index.
4. THE file SHALL remove or replace the "Scaling Your Deployment" section with a note to use `search_docs(query="performance tuning")` for current guidance.
5. THE file SHALL remove or replace the "Keeping Senzing Updated" section with a note to use `get_sdk_reference(topic='migration')` and `search_docs(query="release notes")` for current guidance.
6. THE file SHALL remove or replace the "Advanced Topics to Explore" section with a note to use `search_docs` for current information on custom matching, streaming, REST APIs, and data marts.

### Requirement 18: Trim common-pitfalls.md to bootcamp-operational content

**User Story:** As a power maintainer, I want `common-pitfalls.md` focused on bootcamp-operational pitfalls only, so that Senzing-specific troubleshooting comes from MCP dynamically rather than a static file that can go stale.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/steering/common-pitfalls.md` SHALL retain pitfalls related to bootcamp operations: wrong file paths, missing modules, hook issues, progress file problems, project structure mistakes.
2. THE file SHALL retain the connectivity troubleshooting table for MCP connection issues.
3. THE file SHALL remove or replace Senzing-specific pitfalls (attribute name errors, redo queue issues, SQLite limitations, SDK method signature errors) with instructions for the agent to call the appropriate MCP tool (`explain_error_code`, `search_docs`, `get_sdk_reference`) to diagnose the issue dynamically.
4. THE file SHALL NOT contain hardcoded Senzing SDK method names, attribute names, or error code explanations that may become outdated.

### Requirement 19: Remove inline sample dataset from Module 3

**User Story:** As a power maintainer, I want the hardcoded fallback dataset removed from Module 3's steering file, so that all demo data comes from the MCP server's `get_sample_data` tool.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/steering/module-03-quick-demo.md` SHALL NOT contain an inline fallback dataset (the 5-record sample used when `get_sample_data` was unavailable).
2. THE Module 3 steering file SHALL instruct the agent to call `get_sample_data` to obtain demo data without any fallback path for MCP unavailability.
3. THE Module 3 steering file SHALL NOT contain conditional logic for "if get_sample_data fails due to MCP unavailability."

### Requirement 20: Trim COMMON_MISTAKES.md and FAQ.md to bootcamp-operational content

**User Story:** As a power maintainer, I want the user-facing `COMMON_MISTAKES.md` and `FAQ.md` guides focused on bootcamp-operational content, so that Senzing-specific answers come from MCP rather than static text.

#### Acceptance Criteria

1. THE file `senzing-bootcamp/docs/guides/COMMON_MISTAKES.md` SHALL retain bootcamp-operational mistakes: wrong file locations, skipping modules, not running backup, using /tmp paths.
2. THE file `senzing-bootcamp/docs/guides/COMMON_MISTAKES.md` SHALL remove or replace Senzing-specific mistakes (guessing attribute names, SQLite performance limits, redo queue neglect, export API misuse) with guidance to ask the agent, which will use MCP tools to provide current information.
3. THE file `senzing-bootcamp/docs/guides/FAQ.md` SHALL retain bootcamp-operational questions: how to start, file locations, module navigation, hooks, backup/restore, feedback workflow.
4. THE file `senzing-bootcamp/docs/guides/FAQ.md` SHALL remove or replace Senzing-specific answers (license details, SENZ error handling, non-English data, MCP offline behavior) with guidance to ask the agent for current information via MCP.
5. THE file `senzing-bootcamp/docs/guides/FAQ.md` SHALL remove the reference to `GLOSSARY.md` (already covered by Requirement 8) and the reference to `OFFLINE_MODE.md` (already covered by Requirement 1).
