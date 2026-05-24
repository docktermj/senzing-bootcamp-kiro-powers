# Requirements Document

## Introduction

The MCP-First Invariant feature enforces a strict rule that the agent must consult the Senzing MCP server before presenting any Senzing-related information or generating any Senzing-related code. This is implemented through two complementary mechanisms: strengthened steering rules in `agent-instructions.md` with explicit invariant language, and a new `agentStop` enforcement hook that audits responses post-hoc and triggers self-correction when violations are detected.

## Glossary

- **Agent**: The Kiro AI agent executing bootcamp workflows and responding to the bootcamper
- **MCP_Server**: The Senzing MCP server at `mcp.senzing.com` providing authoritative Senzing facts via tool calls
- **MCP_Tool**: Any tool provided by the Senzing MCP server (e.g., `search_docs`, `get_sdk_reference`, `generate_scaffold`, `sdk_guide`, `explain_error_code`, `find_examples`, `mapping_workflow`, `get_capabilities`)
- **Senzing_Content**: Any information about Senzing attribute names, SDK method signatures, API patterns, configuration options, error codes, mapping formats, or entity resolution concepts
- **Senzing_Code**: Any code that calls Senzing SDK methods, references Senzing configuration structures, or implements Senzing integration patterns
- **Invariant_Hook**: The `mcp-first-invariant` agentStop hook that audits agent responses for compliance with the MCP-first rule
- **Self_Correction**: The process by which the Agent redoes a response with proper MCP consultation after a violation is detected
- **Hook_Categories_Registry**: The `hook-categories.yaml` file that classifies hooks by criticality and module association
- **Silent_Fast_Path**: The hook execution pattern where compliant responses produce zero output tokens

## Requirements

### Requirement 1: MCP Consultation Before Senzing Information

**User Story:** As a bootcamper, I want the agent to always consult the MCP server before presenting Senzing information, so that I receive accurate, current facts rather than potentially outdated training data.

#### Acceptance Criteria

1. WHEN the Agent is about to present Senzing_Content in a response, THE Agent SHALL call at least one MCP_Tool to retrieve authoritative information before including that content in the response.
2. WHEN the Agent references a Senzing SDK method name, attribute name, or configuration option, THE Agent SHALL have called `get_sdk_reference`, `search_docs`, or another relevant MCP_Tool in the same turn prior to presenting the reference.
3. IF the Agent presents Senzing_Content without a preceding MCP_Tool call in the same turn, THEN THE Invariant_Hook SHALL detect this as a violation.

### Requirement 2: MCP Consultation Before Senzing Code Generation

**User Story:** As a bootcamper, I want the agent to always consult the MCP server before generating Senzing code, so that generated code uses correct method signatures, flags, and patterns.

#### Acceptance Criteria

1. WHEN the Agent is about to generate Senzing_Code, THE Agent SHALL call `generate_scaffold`, `sdk_guide`, `get_sdk_reference`, or another relevant MCP_Tool to retrieve current SDK patterns before producing the code.
2. WHEN the Agent generates code containing Senzing SDK method calls, THE Agent SHALL have verified method signatures via MCP_Tool consultation in the same turn.
3. IF the Agent generates Senzing_Code without a preceding MCP_Tool call in the same turn, THEN THE Invariant_Hook SHALL detect this as a violation.

### Requirement 3: agentStop Hook Auditing

**User Story:** As a power developer, I want an agentStop hook that audits every agent response for MCP-first compliance, so that violations are caught and corrected automatically.

#### Acceptance Criteria

1. WHEN the Agent completes a response, THE Invariant_Hook SHALL examine the response content for Senzing_Content indicators.
2. WHEN the Invariant_Hook detects Senzing_Content in the response, THE Invariant_Hook SHALL check whether at least one MCP_Tool was called during that turn.
3. WHILE the response contains no Senzing_Content indicators, THE Invariant_Hook SHALL produce zero output tokens (Silent_Fast_Path).
4. THE Invariant_Hook SHALL use the `agentStop` event type for post-response auditing.

### Requirement 4: Self-Correction on Violation

**User Story:** As a bootcamper, I want the agent to automatically redo responses that violated the MCP-first rule, so that I always receive MCP-verified information without manual intervention.

#### Acceptance Criteria

1. WHEN the Invariant_Hook detects a violation (Senzing_Content present without MCP_Tool consultation), THE Invariant_Hook SHALL instruct the Agent to redo the response with proper MCP consultation.
2. WHEN the Invariant_Hook instructs Self_Correction, THE Invariant_Hook SHALL specify which MCP_Tool categories are relevant to the detected Senzing_Content.
3. WHEN the Agent performs Self_Correction, THE Agent SHALL call the appropriate MCP_Tool before regenerating the response content.

### Requirement 5: Steering Rule Strengthening

**User Story:** As a power developer, I want the agent-instructions.md MCP rules strengthened with explicit invariant language, so that the agent treats MCP-first as an unconditional requirement rather than a guideline.

#### Acceptance Criteria

1. THE Agent SHALL treat MCP-first consultation as an unconditional invariant with the same precedence as mandatory gate rules in `agent-instructions.md`.
2. THE `agent-instructions.md` MCP Rules section SHALL include explicit violation examples showing what constitutes a breach of the MCP-first invariant.
3. THE `agent-instructions.md` MCP Rules section SHALL include a pre-response checklist that the Agent evaluates before presenting Senzing_Content.
4. THE `agent-instructions.md` MCP Rules section SHALL state that no agent-internal reasoning (context pressure, perceived simplicity, cached knowledge from training data) justifies bypassing MCP consultation.

### Requirement 6: Hook Registration as Critical

**User Story:** As a power developer, I want the mcp-first-invariant hook registered as critical in hook-categories.yaml, so that it is created during onboarding and active for all modules.

#### Acceptance Criteria

1. THE Hook_Categories_Registry SHALL list `mcp-first-invariant` in the `critical` category.
2. WHEN the bootcamper completes onboarding, THE Agent SHALL create the Invariant_Hook along with other critical hooks.
3. THE Invariant_Hook SHALL remain active across all modules without requiring per-module activation.

### Requirement 7: Silent Fast-Path Pattern

**User Story:** As a bootcamper, I want the enforcement hook to be invisible when the agent is compliant, so that it does not add noise to the conversation.

#### Acceptance Criteria

1. WHILE the Agent response contains no Senzing_Content, THE Invariant_Hook SHALL produce zero output tokens.
2. WHILE the Agent response contains Senzing_Content and MCP_Tool was consulted in the same turn, THE Invariant_Hook SHALL produce zero output tokens.
3. WHEN the Invariant_Hook produces output, THE Invariant_Hook SHALL produce only Self_Correction instructions directed at the Agent, not explanatory text visible to the bootcamper.
