# Hook Prompt Guardrails Bugfix Design

## Overview

Two related bugs cause hook prompts to produce unwanted output when they should be silent. Bug 1: the `ask-bootcamper` agentStop hook has a weak "do nothing" guard — when the agent's output already contains a 👉 question, the hook generates a fabricated response that answers the question itself, role-playing as the bootcamper. Bug 2: three preToolUse hooks (`verify-senzing-facts`, `enforce-working-directory`, `enforce-feedback-path`) narrate their internal evaluation reasoning on every passing check, despite prompts saying "produce no output at all."

The fix strengthens prompt language in all affected hooks, synchronizes `hook-registry.md`, and reinforces the silent-processing rule in `agent-instructions.md`. The approach is purely textual — no code logic changes, only prompt engineering improvements to close the guardrail gaps.

## Glossary

- **Bug_Condition (C)**: The set of inputs/states where a hook should produce zero output but currently produces unwanted text
- **Property (P)**: The desired behavior — absolute silence (zero tokens emitted) when the hook's check passes with no corrective action needed
- **Preservation**: Existing action-required branches (recap, path correction, MCP verification, feedback redirection) that must remain functionally identical after the fix
- **ask-bootcamper**: The agentStop hook in `hooks/ask-bootcamper.kiro.hook` that recaps work and asks a closing 👉 question
- **preToolUse hooks**: The three write-gating hooks (`verify-senzing-facts`, `enforce-working-directory`, `enforce-feedback-path`) that fire before every write tool invocation
- **hook-registry.md**: The steering file in `steering/hook-registry.md` that mirrors all hook prompts for agent reference
- **agent-instructions.md**: The always-loaded steering file in `steering/agent-instructions.md` containing core agent rules
- **Silent-pass**: The no-action-needed code path where a hook check passes and the hook should emit zero output

## Bug Details

### Bug Condition

The bug manifests in two distinct but related patterns:

**Pattern A — ask-bootcamper fabrication**: When the agent's previous output already contains a 👉 question, the hook prompt says "do nothing" but the agent interprets this loosely. Instead of emitting zero tokens, it generates a full fabricated response — inventing use-case descriptions, record counts, and system names — effectively answering the bootcamper's question on their behalf.

**Pattern B — preToolUse narration**: When the three preToolUse hooks fire on a write operation and the check passes (no corrective action needed), the agent narrates its evaluation reasoning (e.g., "none of these files are feedback content... Proceeding with the writes") instead of producing zero output.

**Formal Specification:**

```pseudocode
FUNCTION isBugCondition(input)
  INPUT: input of type HookEvaluation { hookId: string, agentOutput: string, fileContent: string, isInFeedbackWorkflow: boolean }
  OUTPUT: boolean

  IF input.hookId == "ask-bootcamper" THEN
    RETURN "👉" IN input.agentOutput
  END IF

  IF input.hookId == "verify-senzing-facts" THEN
    RETURN NOT containsSenzingContent(input.fileContent)
           OR allSenzingContentVerified(input.fileContent)
  END IF

  IF input.hookId == "enforce-working-directory" THEN
    RETURN allPathsWithinWorkingDirectory(input.fileContent)
  END IF

  IF input.hookId == "enforce-feedback-path" THEN
    RETURN NOT input.isInFeedbackWorkflow
  END IF

  RETURN false
END FUNCTION
```

### Examples

- **ask-bootcamper fabrication**: Agent output ends with "👉 What data source would you like to work with?" → hook fires → instead of silence, generates "I'd like to work with customer records from our CRM system, about 50,000 records..." (fabricated answer role-playing as bootcamper)
- **verify-senzing-facts narration**: Agent writes a Python utility file with no Senzing content → hook fires → prints "This file contains no Senzing-specific content. No MCP verification needed. Proceeding with the write."
- **enforce-working-directory narration**: Agent writes to `src/transform/mapper.py` (valid path) → hook fires → prints "All paths are within the working directory. No path corrections needed. Proceeding."
- **enforce-feedback-path narration**: Agent writes to `docs/guides/GLOSSARY.md` (not feedback) → hook fires → prints "Not currently in the feedback workflow. No redirection needed."
- **Edge case — ask-bootcamper with 👉 mid-text**: Agent output contains "See the 👉 pointer in the UI" followed by more text (not a question) → hook should still detect 👉 and produce no output, since the current requirement keys on 👉 presence anywhere

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- `ask-bootcamper` recap behavior when no 👉 is present and files were changed (recap accomplishments, list files, end with 👉 question)
- `ask-bootcamper` skip-recap behavior when no 👉 is present and no substantive work was done (just ask a contextual 👉 question)
- `verify-senzing-facts` action branch when file contains unverified Senzing content (instruct agent to verify via MCP tools)
- `enforce-working-directory` action branch when paths reference `/tmp/`, `%TEMP%`, `~/Downloads`, or outside working directory (replace with project-relative equivalents)
- `enforce-feedback-path` action branch when agent IS in feedback workflow writing to wrong path (stop and redirect to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`)
- `capture-feedback` hook behavior — both trigger-phrase detection and silent-pass for non-trigger messages
- All non-affected hooks in `hook-registry.md` — their prompt text and metadata must remain identical
- All existing content in `agent-instructions.md` — new content may be added but nothing removed

**Scope:**
All inputs where the bug condition does NOT hold (action-required branches) should be completely unaffected by this fix. This includes:

- `ask-bootcamper` firing when no 👉 is present in agent output
- preToolUse hooks firing when corrective action IS needed
- All non-affected hooks (code-style-check, commonmark-validation, data-quality-check, etc.)
- All existing steering file content outside the Hooks section additions

## Hypothesized Root Cause

Based on the bug description and analysis of the current prompt text, the most likely issues are:

1. **Weak guard language in ask-bootcamper**: The prompt says "do nothing" which LLMs interpret as a soft suggestion rather than a hard constraint. The phrase lacks explicit prohibitions — it doesn't say "do not generate any text," "do not answer the question," or "do not role-play as the bootcamper." Without these negative examples, the model finds creative ways to "do something" while technically "doing nothing" (e.g., it considers generating a helpful response as not contradicting "do nothing").

2. **Missing reinforcement in preToolUse hooks**: The prompts say "produce no output at all — do not acknowledge, do not explain, do not print anything" which is good language, but it appears only once and is not reinforced. LLMs with long context windows can lose track of a single instruction when processing the full evaluation. The instruction also lacks a structural cue — it doesn't tell the model to STOP processing after determining no action is needed.

3. **No system-level reinforcement**: The `agent-instructions.md` Hooks section says "produce no output" but doesn't provide the explicit, emphatic framing needed to override the model's default helpfulness bias. A stronger system-level rule would reinforce the per-hook instructions.

4. **Registry drift potential**: While `hook-registry.md` currently mirrors the hook files, there's no structural guarantee. If hook files are updated but the registry isn't, the agent may read the weaker registry version and ignore the stronger hook-file version.

## Correctness Properties

Property 1: Bug Condition — ask-bootcamper Contains Strong Do-Nothing Guard

_For any_ evaluation of the `ask-bootcamper` hook where the agent's previous output contains a 👉 character, the hook prompt SHALL contain explicit prohibitions against generating any text — including prohibitions against answering questions meant for the bootcamper, role-playing as the user, and generating fabricated content — using language stronger than "do nothing."

**Validates: Requirements 2.1, 2.2**

Property 2: Bug Condition — preToolUse Hooks Contain Reinforced Silent-Pass Language

_For any_ preToolUse hook in the affected set (`verify-senzing-facts`, `enforce-working-directory`, `enforce-feedback-path`), the hook prompt SHALL contain reinforced silent-pass instructions that go beyond a single "produce no output" phrase — including an explicit STOP/return instruction and redundant emphasis that prevents the model from narrating its evaluation.

**Validates: Requirements 2.3, 2.4, 2.5**

Property 3: Synchronization — hook-registry.md Matches Hook Files

_For any_ affected hook, the prompt text in `hook-registry.md` SHALL be identical to the prompt text in the corresponding `.kiro.hook` file, ensuring the agent cannot read a weaker version from the registry.

**Validates: Requirements 2.6**

Property 4: Reinforcement — agent-instructions.md Contains Silent-Processing Rule

_For any_ hook evaluation where no corrective action is needed, the `agent-instructions.md` Hooks section SHALL contain an explicit silent-processing rule that forbids narrating, explaining, or acknowledging hook evaluations.

**Validates: Requirements 2.7**

Property 5: Preservation — Action-Required Branches Unchanged

_For any_ affected hook, the action-required branch (the code path where corrective action IS needed) SHALL contain all original keywords and instructions, preserving the hook's corrective functionality.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

Property 6: Preservation — Non-Affected Hooks and Content Unchanged

_For any_ non-affected hook in `hook-registry.md`, its section SHALL be identical to its baseline content. All existing content in `agent-instructions.md` SHALL be preserved.

**Validates: Requirements 3.8**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:

1. **Replace "do nothing" with explicit zero-output guard**: Change the 👉 detection branch from "do nothing" to an explicit multi-part prohibition: "produce absolutely no output — no text, no recap, no question, no fabricated response. Do NOT answer the question. Do NOT role-play as the bootcamper. Do NOT generate any content. STOP immediately and return nothing."
2. **Broaden 👉 detection scope**: Change "already ends with a 👉 question" to "already contains a 👉 character anywhere in the text" to match requirement 2.1.
3. **Add anti-fabrication examples**: Include explicit examples of what NOT to do (e.g., "Do not invent use-case descriptions, record counts, or system names").

**File**: `senzing-bootcamp/hooks/verify-senzing-facts.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:

1. **Add STOP instruction**: After the "produce no output at all" phrase, add "STOP processing and return immediately."
2. **Add redundant emphasis**: Reinforce with "Your response must be completely empty — zero tokens, zero characters."
3. **Restructure prompt**: Put the silent-pass check FIRST (before the action-required instructions) so the model encounters the exit condition early.

**File**: `senzing-bootcamp/hooks/enforce-working-directory.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:

1. **Add explicit silent-pass branch**: Add a clear "If all paths are within the working directory" check at the start with "produce no output at all — do not acknowledge, do not explain, do not print anything. STOP immediately and return an empty response."
2. **Add redundant emphasis**: "Your response must be completely empty — zero tokens."

**File**: `senzing-bootcamp/hooks/enforce-feedback-path.kiro.hook`

**Field**: `then.prompt`

**Specific Changes**:

1. **Add STOP instruction**: After the "produce no output at all" phrase, add "STOP processing and return immediately."
2. **Add redundant emphasis**: Reinforce with "Your response must be completely empty — zero tokens, zero characters."

**File**: `senzing-bootcamp/steering/hook-registry.md`

**Specific Changes**:

1. **Sync ask-bootcamper prompt**: Replace the Prompt text for `ask-bootcamper` with the exact updated prompt from the hook file.
2. **Sync verify-senzing-facts prompt**: Replace the Prompt text with the exact updated prompt from the hook file.
3. **Sync enforce-working-directory prompt**: Replace the Prompt text with the exact updated prompt from the hook file.
4. **Sync enforce-feedback-path prompt**: Replace the Prompt text with the exact updated prompt from the hook file.

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: `## Hooks`

**Specific Changes**:

1. **Strengthen existing silent-processing rule**: The current rule says "When a hook check passes with no action needed, produce no output." Strengthen it with explicit prohibitions: "Do not narrate your evaluation. Do not explain why no action is needed. Do not acknowledge the check. Do not print status messages. Your response must be completely empty — zero tokens."

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse each affected hook file's prompt text and check for the presence of strong guardrail language. Run these tests on the UNFIXED code to observe failures and confirm the prompts lack sufficient guard language.

**Test Cases**:

1. **ask-bootcamper weak guard test**: Parse `ask-bootcamper.kiro.hook` prompt and check for explicit prohibitions against generating text when 👉 is detected — beyond just "do nothing" (will fail on unfixed code because prompt only says "do nothing")
2. **verify-senzing-facts missing STOP test**: Parse `verify-senzing-facts.kiro.hook` prompt and check for a STOP/return instruction in the silent-pass branch (will fail on unfixed code because prompt lacks STOP instruction)
3. **enforce-working-directory missing silent-pass test**: Parse `enforce-working-directory.kiro.hook` prompt and check for an explicit silent-pass branch with "produce no output" (will fail on unfixed code because prompt lacks this branch)
4. **enforce-feedback-path missing STOP test**: Parse `enforce-feedback-path.kiro.hook` prompt and check for a STOP/return instruction (will fail on unfixed code because prompt lacks STOP instruction)
5. **hook-registry sync test**: Compare each affected hook's prompt in `hook-registry.md` against the hook file — check that registry contains the same strong language (will fail on unfixed code because registry mirrors weak prompts)
6. **agent-instructions reinforcement test**: Check `agent-instructions.md` Hooks section for explicit silent-processing prohibitions beyond the current minimal rule (will fail on unfixed code because rule is not emphatic enough)

**Expected Counterexamples**:

- `ask-bootcamper` prompt contains "do nothing" but lacks "do NOT answer," "do NOT role-play," "do NOT generate"
- preToolUse prompts contain "produce no output" but lack "STOP" or "return immediately"
- `enforce-working-directory` prompt has no explicit silent-pass branch at all
- `hook-registry.md` mirrors the weak prompt language
- `agent-instructions.md` Hooks section lacks emphatic silent-processing rule

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed prompts contain sufficiently strong guardrail language to prevent unwanted output.

**Pseudocode:**

```pseudocode
FOR ALL hook WHERE isBugCondition(hook) DO
  prompt := readFixedPrompt(hook)
  ASSERT containsStrongGuardLanguage(prompt)
  ASSERT containsExplicitProhibitions(prompt)
  ASSERT containsSTOPInstruction(prompt) OR containsZeroOutputEmphasis(prompt)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed prompts preserve all action-required functionality.

**Pseudocode:**

```pseudocode
FOR ALL hook WHERE NOT isBugCondition(hook) DO
  ASSERT actionRequiredKeywords(hook) ALL IN readFixedPrompt(hook)
  ASSERT hookRegistrySection(hook) == baselineRegistrySection(hook)  -- for non-affected hooks
  ASSERT agentInstructionsBaseline SUBSET OF agentInstructionsCurrent
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It generates many test cases automatically across the set of affected and non-affected hooks
- It catches edge cases where a keyword might be accidentally removed during prompt editing
- It provides strong guarantees that action-required branches are unchanged for all hooks

**Test Plan**: Observe behavior on UNFIXED code first — capture baseline content for all non-affected hooks, verify action-required keywords exist in affected hooks, snapshot `agent-instructions.md`. Then write property-based tests that assert these baselines are preserved after the fix.

**Test Cases**:

1. **ask-bootcamper recap preservation**: Verify prompt still contains "accomplished," "files created or modified," and "👉 question" instructions for the non-👉 branch
2. **ask-bootcamper skip-recap preservation**: Verify prompt still contains "skip the recap" and "no files changed" instructions
3. **verify-senzing-facts action preservation**: Verify prompt still contains MCP tool names (mapping_workflow, generate_scaffold, etc.) and SENZING_INFORMATION_POLICY reference
4. **enforce-working-directory action preservation**: Verify prompt still contains /tmp/, %TEMP%, ~/Downloads, project-relative, "Do NOT proceed"
5. **enforce-feedback-path action preservation**: Verify prompt still contains SENZING_BOOTCAMP_POWER_FEEDBACK.md and "STOP and redirect"
6. **capture-feedback preservation**: Verify prompt still contains all feedback trigger phrases and feedback-workflow.md reference
7. **Non-affected hooks unchanged**: Verify all 14 non-affected hook sections in registry match baselines
8. **agent-instructions existing content preserved**: Verify all baseline lines still present

### Unit Tests

- Test each affected hook file is valid JSON with correct metadata (name, version, when.type, then.type)
- Test ask-bootcamper prompt contains strong 👉 guard with explicit prohibitions
- Test each preToolUse hook prompt contains reinforced silent-pass language with STOP instruction
- Test hook-registry.md prompts match hook file prompts exactly for all affected hooks
- Test agent-instructions.md Hooks section contains emphatic silent-processing rule
- Test action-required keywords preserved in each affected hook prompt

### Property-Based Tests

- Generate random selections from affected hooks and verify all contain strong guard language (bug condition property)
- Generate random selections from affected hooks and verify all action-required keywords are preserved (preservation property)
- Generate random selections from non-affected hooks and verify registry sections match baselines (preservation property)
- Generate random selections from affected hooks and verify hook-file/registry prompt synchronization (sync property)

### Integration Tests

- Test full prompt text of each affected hook file against both bug-condition and preservation requirements simultaneously
- Test that hook-registry.md and hook files are fully synchronized for all 18 hooks
- Test that agent-instructions.md contains both the existing Hooks content and the new silent-processing reinforcement
