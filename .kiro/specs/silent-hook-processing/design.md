# Silent Hook Processing Bugfix Design

## Overview

Four hook prompts cause the agent to produce visible chat noise when their checks pass with no action needed. The `capture-feedback` hook (promptSubmit) prints "No feedback trigger phrases — continuing normally" on virtually every message, and three preToolUse hooks (`enforce-feedback-path`, `enforce-working-directory`, `verify-senzing-facts`) print internal reasoning on every write operation. The root cause is that hook prompts use phrases like "do nothing" or "let the write proceed normally" when checks pass, which the agent interprets as requiring an acknowledgment rather than truly producing zero output. The fix updates all four hook prompt files, mirrors the changes in `hook-registry.md`, and adds a general silent-processing rule to `agent-instructions.md` so that any future hooks follow the same pattern.

## Glossary

- **Bug_Condition (C)**: A hook fires and its check passes with no action needed, but the agent produces visible chat output acknowledging the pass instead of remaining silent
- **Property (P)**: When a hook check passes with no action needed, the agent produces zero visible output — no acknowledgment, no reasoning, no status message
- **Preservation**: When a hook check fails (action IS needed), the agent continues to produce the same visible output as before — feedback workflow initiation, path redirection, working-directory correction, Senzing fact verification prompts
- **Hook prompt**: The `prompt` field in a `.kiro.hook` JSON file that instructs the agent what to do when the hook fires
- **`hook-registry.md`**: The steering file at `senzing-bootcamp/steering/hook-registry.md` that documents all hook definitions; agents read this to create hooks via the `createHook` tool
- **`agent-instructions.md`**: The always-loaded steering file at `senzing-bootcamp/steering/agent-instructions.md` containing core agent rules
- **Silent processing**: The desired behavior where a hook check that passes with no action needed produces absolutely no visible output

## Bug Details

### Bug Condition

The bug manifests when any of the four affected hooks fire and their check passes with no action needed. The hook prompt tells the agent to "do nothing" or "let the write proceed normally," but the agent interprets this as requiring a visible acknowledgment. The agent outputs its internal reasoning (e.g., "No feedback trigger phrases," "Not in feedback workflow," "path is project-relative," "no Senzing SDK content") as visible chat text before proceeding.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input of type HookInvocation (hook_name, event_type, check_result)
  OUTPUT: boolean

  RETURN input.hook_name IN {"capture-feedback", "enforce-feedback-path",
                              "enforce-working-directory", "verify-senzing-facts"}
         AND input.check_result = PASS_NO_ACTION_NEEDED
END FUNCTION
```

### Examples

- **capture-feedback on normal message**: Bootcamper types "Let's start Module 3" → hook fires → agent prints "No feedback trigger phrases — continuing normally" → visible noise before the actual response
- **enforce-feedback-path on code write**: Agent writes `src/load/loader.py` → hook fires → agent prints "Not in feedback workflow. Proceeding with write." → visible noise before the file is written
- **enforce-working-directory on project file**: Agent writes `data/temp/sample.jsonl` → hook fires → agent prints "Path is project-relative. Proceeding." → visible noise before the file is written
- **verify-senzing-facts on non-Senzing file**: Agent writes `README.md` → hook fires → agent prints "No Senzing SDK content detected. Proceeding." → visible noise before the file is written
- **Multiple preToolUse hooks on single write**: Agent writes any file → all three preToolUse hooks fire → agent prints combined reasoning from all three checks → three lines of visible noise before the file is written

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When `capture-feedback` detects a feedback trigger phrase, it continues to initiate the feedback workflow with context capture and visible output guiding the bootcamper
- When `enforce-feedback-path` detects feedback content being written to the wrong path, it continues to block the write and redirect to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` with visible output
- When `enforce-working-directory` detects a path outside the working directory, it continues to block the write and suggest project-relative alternatives with visible output
- When `verify-senzing-facts` detects unverified Senzing-specific content, it continues to flag the facts and prompt verification with visible output
- All other hooks (`ask-bootcamper`, `code-style-check`, `data-quality-check`, etc.) continue to function exactly as designed
- The `hook-registry.md` descriptions, ids, names, event types, and toolTypes for all hooks remain unchanged — only the prompt text for the four affected hooks changes

**Scope:**
All hook invocations where the check result requires action (feedback phrase detected, wrong path, external directory, unverified Senzing facts) are completely unaffected by this fix. Only the "check passes, no action needed" code path changes. All hooks not in the affected set of four are completely unaffected.

## Hypothesized Root Cause

Based on the bug analysis, the root cause is ambiguous "do nothing" phrasing in hook prompts:

1. **Ambiguous "do nothing" instruction**: The `capture-feedback` prompt says "If NONE of these phrases appear in the message, do nothing — let the conversation continue normally." The agent interprets "do nothing" as "acknowledge that I checked and found nothing" rather than "produce zero output." The phrase "let the conversation continue normally" further implies the agent should say something to transition.

2. **Implicit acknowledgment expectation**: The `enforce-feedback-path` prompt says "If you are NOT in the feedback workflow, do nothing — let the write proceed normally." The agent reads "let the write proceed normally" as an instruction to announce that it is proceeding, rather than to silently proceed.

3. **Missing explicit silence instruction**: The `enforce-working-directory` and `verify-senzing-facts` prompts have no explicit "do nothing" path at all — they only describe what to do when a problem is found. The agent fills the gap by reporting its check results even when no problem exists.

4. **No global silent-processing rule**: `agent-instructions.md` has no rule telling the agent that hook checks passing with no action needed should produce zero output. Each hook prompt independently needs to handle the "no action" case, and all four fail to do so with sufficient explicitness.

## Correctness Properties

Property 1: Bug Condition - Silent processing when hook checks pass

_For any_ hook invocation where the hook is one of `capture-feedback`, `enforce-feedback-path`, `enforce-working-directory`, or `verify-senzing-facts` and the check passes with no action needed, the fixed hook prompt SHALL instruct the agent to produce absolutely no visible output — no acknowledgment, no reasoning, no status message — and silently allow the operation to proceed.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Property 2: Preservation - Action-required hook behavior unchanged

_For any_ hook invocation where the check result requires action (feedback phrase detected, wrong feedback path, external directory path, unverified Senzing facts), the fixed hook prompt SHALL produce the same visible output and take the same corrective action as the original hook prompt, preserving all existing error-handling and redirection behavior.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File 1**: `senzing-bootcamp/hooks/capture-feedback.kiro.hook`

**Change**: Replace "do nothing — let the conversation continue normally" with "produce no output at all — do not acknowledge, do not explain, do not print anything" in the no-match branch of the prompt.

**File 2**: `senzing-bootcamp/hooks/enforce-feedback-path.kiro.hook`

**Change**: Replace "do nothing — let the write proceed normally" with "produce no output at all — do not acknowledge, do not explain, do not print anything" in the not-in-feedback-workflow branch of the prompt.

**File 3**: `senzing-bootcamp/hooks/enforce-working-directory.kiro.hook`

**Change**: Add an explicit "If all paths are within the working directory, produce no output at all — do not acknowledge, do not explain, do not print anything" branch to the prompt so the agent knows to remain silent when no correction is needed.

**File 4**: `senzing-bootcamp/hooks/verify-senzing-facts.kiro.hook`

**Change**: Add an explicit "If the file contains no Senzing-specific content, or all Senzing content was already verified via MCP tools, produce no output at all — do not acknowledge, do not explain, do not print anything" branch to the prompt.

**File 5**: `senzing-bootcamp/steering/hook-registry.md`

**Change**: Mirror the updated prompt text for all four hooks in the registry so that hooks created via `createHook` from the registry use the fixed prompts. Only the `Prompt:` field for each of the four hooks changes — ids, names, descriptions, event types, and toolTypes remain identical.

**File 6**: `senzing-bootcamp/steering/agent-instructions.md`

**Change**: Add a new rule under the `## Hooks` section: "When a hook check passes with no action needed, produce no output. Do not acknowledge the check, do not explain your reasoning, do not print any status message. Only produce output when the hook requires corrective action."

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Since these are prompt/steering files (natural language instructions for an LLM), testing focuses on structural analysis of file content — verifying that the prompt text contains explicit silent-processing instructions and that action-required branches are preserved.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the four hook prompts lack explicit "produce no output" instructions for the no-action-needed case.

**Test Plan**: Parse each affected hook file and the hook-registry.md, and check whether the prompt text contains an explicit "produce no output" instruction for the pass/no-action case. Run these tests on the UNFIXED files to confirm the bug condition exists.

**Test Cases**:
1. **capture-feedback prompt**: Verify the prompt uses "do nothing" without explicit "produce no output" (will match on unfixed code)
2. **enforce-feedback-path prompt**: Verify the prompt uses "do nothing" without explicit "produce no output" (will match on unfixed code)
3. **enforce-working-directory prompt**: Verify the prompt has no explicit no-action branch at all (will match on unfixed code)
4. **verify-senzing-facts prompt**: Verify the prompt has no explicit no-action branch at all (will match on unfixed code)
5. **hook-registry.md prompts**: Verify the registry prompts mirror the same ambiguous phrasing (will match on unfixed code)

**Expected Counterexamples**:
- `capture-feedback` prompt contains "do nothing" but not "produce no output"
- `enforce-feedback-path` prompt contains "do nothing" but not "produce no output"
- `enforce-working-directory` prompt has no silent-processing instruction
- `verify-senzing-facts` prompt has no silent-processing instruction

### Fix Checking

**Goal**: Verify that for all hook prompts where the bug condition holds, the fixed prompts contain explicit "produce no output" instructions for the no-action-needed case.

**Pseudocode:**

```
FOR ALL hook WHERE isBugCondition(hook) DO
  prompt := read_hook_prompt(hook)
  ASSERT prompt CONTAINS explicit_silent_instruction
  // e.g., "produce no output" or equivalent
END FOR
```

### Preservation Checking

**Goal**: Verify that for all hook prompts, the action-required branches are preserved unchanged.

**Pseudocode:**

```
FOR ALL hook WHERE NOT isBugCondition(hook) DO
  ASSERT original_prompt(hook) = fixed_prompt(hook)
END FOR

FOR ALL hook IN affected_hooks DO
  ASSERT action_required_branch(original_prompt(hook))
         IS PRESERVED IN fixed_prompt(hook)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can verify that action-required instructions are preserved across all four hooks
- It catches edge cases where corrective-action text might be accidentally removed or altered
- It provides strong guarantees that non-affected hooks are completely unchanged

**Test Plan**: Parse both the unfixed and fixed versions of each affected hook file. Extract the action-required branch text and verify it is preserved in the fixed version. Verify all non-affected hooks in hook-registry.md are unchanged.

**Test Cases**:
1. **capture-feedback action branch**: Verify the feedback workflow initiation instructions are preserved
2. **enforce-feedback-path action branch**: Verify the path redirection instructions are preserved
3. **enforce-working-directory action branch**: Verify the path correction instructions are preserved
4. **verify-senzing-facts action branch**: Verify the MCP verification instructions are preserved
5. **Non-affected hooks**: Verify all other hooks in hook-registry.md are completely unchanged
6. **agent-instructions.md preservation**: Verify all existing content in agent-instructions.md is preserved (only a new rule is added)

### Unit Tests

- Parse each affected hook file and assert the prompt contains "produce no output" or equivalent explicit silent-processing instruction
- Parse each affected hook file and assert the action-required branch text is preserved
- Parse hook-registry.md and assert the four affected hook prompts match their corresponding hook files
- Parse agent-instructions.md and assert the new silent-processing rule exists under the Hooks section

### Property-Based Tests

- Generate random selections from the set of affected hooks and verify each contains explicit silent-processing instructions
- Generate random content sections from action-required branches and verify they match between unfixed and fixed versions
- Test that all non-affected hooks in hook-registry.md are byte-identical between unfixed and fixed versions

### Integration Tests

- Verify that hook-registry.md prompt text for each affected hook matches the corresponding .kiro.hook file prompt
- Verify that agent-instructions.md contains the new silent-processing rule and all pre-existing rules are intact
- Verify that the combination of hook prompts and agent-instructions.md rule provides defense-in-depth for silent processing
