# Implementation Plan: MCP-First Invariant

## Overview

Implement the MCP-First Invariant enforcement system through three artifacts: a new `agentStop` hook file (`mcp-first-invariant.kiro.hook`) with two-phase detection logic, strengthened MCP Rules in `agent-instructions.md` with explicit invariant language, registration in `hook-categories.yaml` as critical, and property-based tests validating all correctness properties.

## Tasks

- [x] 1. Create the MCP-First Invariant hook file
  - [x] 1.1 Create `senzing-bootcamp/hooks/mcp-first-invariant.kiro.hook` with hook JSON structure
    - Define hook with `name: "to verify MCP-first compliance"`, `version: "1.0.0"`, `when.type: "agentStop"`, `then.type: "askAgent"`
    - Write the `then.prompt` implementing Phase 1 (Senzing content detection) with all indicator sets: SDK method names, attribute names, config options, error code pattern `SENZ\d{4}`, and ER terms in technical context
    - Write Phase 2 (MCP tool call verification) checking for any MCP tool call in the same turn
    - Implement decision logic: no Senzing content → zero tokens; Senzing content + MCP tool called → zero tokens; Senzing content + no MCP tool → self-correction instructions
    - Include the self-correction output template mapping content categories to appropriate MCP tools
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 7.1, 7.2, 7.3_

- [x] 2. Strengthen MCP Rules in agent-instructions.md
  - [x] 2.1 Add MCP-First Invariant subsection to the MCP Rules section in `senzing-bootcamp/steering/agent-instructions.md`
    - Add invariant declaration with same absolute precedence as ⛔ mandatory gates
    - Add pre-response checklist (3-step numbered checklist evaluating Senzing content presence and MCP tool consultation)
    - Add violation examples showing concrete breaches (referencing `add_record` params, generating SDK code, explaining `NAME_FULL`, describing error codes, recommending thresholds)
    - Add no-bypass clause explicitly prohibiting context pressure, perceived simplicity, cached knowledge, session length, and token budget as justifications
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 3. Register hook as critical in hook-categories.yaml
  - [x] 3.1 Add `mcp-first-invariant` to the `critical` list in `senzing-bootcamp/hooks/hook-categories.yaml`
    - Insert alphabetically between `commonmark-validation` and `question-format-gate`
    - Verify the hook does NOT appear in any module-specific list
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 4. Checkpoint - Ensure hook file is valid JSON and steering changes are consistent
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Write property-based tests for MCP-First Invariant
  - [x] 5.1 Write property test for Senzing indicator detection coverage
    - **Property 1: Senzing indicator detection coverage**
    - **Validates: Requirements 1.3, 2.3, 3.1**
    - For any SDK method name, attribute name, config option, or ER term from the defined sets, verify the hook prompt contains that indicator

  - [x] 5.2 Write property test for silent fast-path directives
    - **Property 2: Silent fast-path for compliant scenarios**
    - **Validates: Requirements 3.3, 7.1, 7.2**
    - Verify the hook prompt contains explicit zero-output directives for both no-Senzing-content and compliant (MCP-called) scenarios

  - [x] 5.3 Write property test for MCP tool call verification coverage
    - **Property 3: MCP tool call verification coverage**
    - **Validates: Requirements 3.2**
    - For any MCP tool name from the defined set, verify the hook prompt references that tool in its detection logic

  - [x] 5.4 Write property test for self-correction instructions
    - **Property 4: Self-correction instructions on violation**
    - **Validates: Requirements 4.1, 4.2, 4.3**
    - For any Senzing content category, verify the hook prompt's violation output maps that category to appropriate MCP tool(s)

  - [x] 5.5 Write property test for no-bypass invariant language
    - **Property 5: No-bypass invariant language**
    - **Validates: Requirements 5.1, 5.4**
    - For any agent-internal bypass justification, verify `agent-instructions.md` explicitly prohibits it

  - [x] 5.6 Write property test for critical-only registration
    - **Property 6: Critical-only registration**
    - **Validates: Requirements 6.1, 6.3**
    - Verify `mcp-first-invariant` appears in `critical` category and NOT in any module-specific category

  - [x] 5.7 Write property test for agent-directed output only
    - **Property 7: Agent-directed output only**
    - **Validates: Requirements 7.3**
    - Verify the hook's violation output contains action verbs (Call, Regenerate, Do NOT) and no user-facing conversational language

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Tests go in repo-root `tests/test_mcp_first_invariant_properties.py` per project convention (hook tests validating real hook files)
- Hook file follows the project's `"to {verb phrase}"` naming convention
- The hook prompt uses the silent fast-path pattern established by `write-policy-gate.kiro.hook`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1", "3.1"] },
    { "id": 1, "tasks": ["5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7"] }
  ]
}
```
