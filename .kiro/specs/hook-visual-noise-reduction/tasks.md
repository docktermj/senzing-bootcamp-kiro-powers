# Implementation Plan: Hook Visual Noise Reduction

## Overview

Consolidate four `agentStop` hooks into a single `ask-bootcamper.kiro.hook` (v4.0.0) with four internal phases, strengthen the `write-policy-gate.kiro.hook` silence directives, delete obsolete hook files, update all registry/steering/documentation references, and migrate tests to validate the consolidated hook.

## Tasks

- [x] 1. Consolidate agentStop hooks into ask-bootcamper.kiro.hook
  - [x] 1.1 Build the consolidated ask-bootcamper.kiro.hook (v4.0.0) with four-phase prompt
    - Read existing `ask-bootcamper.kiro.hook`, `enforce-step-and-transition.kiro.hook`, `mcp-first-invariant.kiro.hook`, and `question-format-gate.kiro.hook`
    - Merge all prompt logic into a single `then.prompt` field with clearly marked PHASE 1 (Closing Question), PHASE 2 (Step Sequencing), PHASE 3 (MCP-First), PHASE 4 (Question Format with Silent Self-Correction) sections
    - Set version to `"4.0.0"`, preserve JSON schema (`name`, `version`, `description`, `when.type: agentStop`, `then.type: askAgent`)
    - Phase 4 must instruct regeneration of the entire last response with corrected question inline (Silent_Self_Correction) and suppress the original compound question
    - Phase 4 must preserve all three detection patterns: sentence-starter Or, inline prose or, appended alternative
    - Include explicit "no output" directive for Phase 4 when no compound question is detected
    - Include the default output rule: if ALL phases produce no output, complete response is `.`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 2.2, 2.3, 2.4, 9.1, 9.2, 9.3, 9.4_

  - [x] 1.2 Write property test for consolidated hook phase markers (Property 1)
    - **Property 1: Consolidated hook contains all four phase markers**
    - Verify `then.prompt` contains identifiable section markers for all four phases
    - **Validates: Requirements 1.1, 9.4**

  - [x] 1.3 Write property test for consolidated hook structural validity (Property 2)
    - **Property 2: Consolidated hook structural validity**
    - Verify valid JSON with all required keys, `when.type == "agentStop"`, `then.type == "askAgent"`, non-empty `then.prompt`
    - **Validates: Requirements 1.3, 9.1, 9.2, 9.3**

  - [x] 1.4 Write property test for step sequencing and MCP-first logic preservation (Property 3)
    - **Property 3: Step sequencing and MCP-first logic preservation**
    - Sample from sets of key detection phrases (transition patterns, affirmative phrases, SDK methods, attribute names, ER terms, MCP tool names) and assert each appears in the consolidated prompt
    - **Validates: Requirements 1.4, 1.5**

  - [x] 1.5 Write property test for question format detection patterns with silent self-correction (Property 4)
    - **Property 4: Question format detection patterns preserved with silent self-correction**
    - Verify all compound-question detection pattern descriptions appear in the prompt AND silent self-correction language (regeneration instruction) is present
    - **Validates: Requirements 1.6, 2.4**

  - [x] 1.6 Write property test for silent self-correction instructs regeneration (Property 5)
    - **Property 5: Silent self-correction instructs regeneration and suppression**
    - Verify Phase 4 section contains both regeneration instruction and suppression instruction
    - **Validates: Requirements 2.1, 2.2**

  - [x] 1.7 Write property test for non-compound case produces no phase output (Property 6)
    - **Property 6: Non-compound case produces no phase output**
    - Verify Phase 4 section contains explicit directive that no compound question → no output
    - **Validates: Requirements 2.3**

- [x] 2. Strengthen write-policy-gate silence directives
  - [x] 2.1 Update write-policy-gate.kiro.hook prompt with reinforced silence directives
    - Add front-loaded silence directive within first 200 characters of prompt text: `⚠️ SILENCE RULE: When all checks pass, produce ZERO tokens. No output. No acknowledgment.`
    - Add `"Fast path passes"` to the FORBIDDEN output list
    - Add closing OUTPUT FORMAT section reiterating zero-token directive and enumerating forbidden narration phrases
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 2.2 Write property test for write-policy-gate dual-reinforcement suppression (Property 8)
    - **Property 8: Write-policy-gate dual-reinforcement suppression structure**
    - Verify first 200 chars contain zero-output directive, OUTPUT FORMAT section exists with zero-token directive, and "Fast path passes" appears in FORBIDDEN list
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [x] 3. Checkpoint - Verify core hook changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Delete obsolete hook files and update registries
  - [x] 4.1 Delete the three obsolete hook files
    - Delete `senzing-bootcamp/hooks/question-format-gate.kiro.hook`
    - Delete `senzing-bootcamp/hooks/enforce-step-and-transition.kiro.hook`
    - Delete `senzing-bootcamp/hooks/mcp-first-invariant.kiro.hook`
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Update hook-categories.yaml to remove deleted hooks
    - Remove `question-format-gate`, `enforce-step-and-transition`, `mcp-first-invariant` from all categories
    - Ensure `ask-bootcamper` remains in the `critical` category
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 4.3 Update hooks.lock.yaml to remove deleted hooks and bump ask-bootcamper version
    - Remove entries for `question-format-gate`, `enforce-step-and-transition`, `mcp-first-invariant`
    - Update `ask-bootcamper` entry to version `"4.0.0"`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 4.4 Write property test for deleted hooks absent from categories file (Property 7)
    - **Property 7: Deleted hooks absent from categories file**
    - For each deleted hook ID, verify it does not appear in any category in `hook-categories.yaml`
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [x] 5. Update steering and documentation references
  - [x] 5.1 Update hook-registry-critical.md steering file
    - Remove standalone entries for `question-format-gate`, `enforce-step-and-transition`, `mcp-first-invariant`
    - Update `ask-bootcamper` entry with full four-phase prompt text
    - _Requirements: 7.1, 7.2_

  - [x] 5.2 Update hook-registry.md steering file
    - Remove rows for deleted hooks from the quick-reference table
    - _Requirements: 7.3_

  - [x] 5.3 Update hooks/README.md documentation
    - Remove entries for deleted hooks
    - _Requirements: 7.4_

  - [x] 5.4 Update POWER.md hook references
    - Remove references to deleted hooks and adjust the hook count
    - _Requirements: 7.5_

- [x] 6. Migrate tests to validate consolidated hook
  - [x] 6.1 Update test_mcp_first_invariant_properties.py to point at consolidated hook
    - Change `HOOK_PATH` from `mcp-first-invariant.kiro.hook` to `ask-bootcamper.kiro.hook`
    - Update `load_hook_prompt()` to extract the MCP_First_Phase section from the consolidated prompt
    - Update `TestCriticalOnlyRegistration` to check `ask-bootcamper` instead of `mcp-first-invariant`
    - _Requirements: 8.1_

  - [x] 6.2 Update test_single_question_format.py to point at consolidated hook
    - Change `QUESTION_FORMAT_GATE_HOOK` path to `ask-bootcamper.kiro.hook`
    - Update `enforcement_detects_compound()` to extract Question_Format_Phase from consolidated prompt
    - _Requirements: 8.2_

  - [x] 6.3 Update test_detect_transition_retry.py to point at consolidated hook
    - Change `_HOOK_FILE` path to `ask-bootcamper.kiro.hook`
    - _Requirements: 8.3_

  - [x] 6.4 Update hook_test_helpers.py CRITICAL_HOOKS list
    - Remove `enforce-step-and-transition`, `mcp-first-invariant`, `question-format-gate` from `CRITICAL_HOOKS`
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 8.4_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The programming language for all tests is Python 3.11+ with pytest + Hypothesis
- Hook files are JSON (`.kiro.hook`), registry files are YAML
- Tests live in repo-root `tests/` per project conventions

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "2.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "2.2"] },
    { "id": 2, "tasks": ["4.1", "4.2", "4.3"] },
    { "id": 3, "tasks": ["4.4", "5.1", "5.2", "5.3", "5.4"] },
    { "id": 4, "tasks": ["6.1", "6.2", "6.3", "6.4"] }
  ]
}
```
