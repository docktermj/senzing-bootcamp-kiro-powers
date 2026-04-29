# Missing Pointing Prefix Bugfix Design

## Overview

The onboarding system has a question-ownership architecture conflict: `onboarding-flow.md` contains inline 👉 closing questions with WAIT instructions at the end of steps 1b, 2, 4, and 5, while the `ask-bootcamper` hook (firing on every `agentStop`) is designed to be the single owner of all closing 👉 questions. This dual-source design causes three problems: dropped 👉 prefixes when the agent paraphrases inline questions, unreliable prompt-based suppression in the hook, and duplicate back-to-back questions when suppression fails. The fix removes inline closing 👉 questions and WAIT instructions from `onboarding-flow.md`, letting the `ask-bootcamper` hook be the sole source of closing questions — consistent with the existing ownership rule in `agent-instructions.md`.

## Glossary

- **Bug_Condition (C)**: An onboarding step in `onboarding-flow.md` that ends with an inline 👉 closing question and a WAIT instruction, creating a question-ownership conflict with the `ask-bootcamper` hook
- **Property (P)**: Onboarding steps present information and stop cleanly without inline closing questions or WAITs, allowing the `ask-bootcamper` hook to generate the single contextual 👉 closing question
- **Preservation**: The `ask-bootcamper` hook continues to fire on `agentStop` and generate contextual 👉 questions; the onboarding step sequence remains unchanged; `agent-instructions.md` ownership rule remains in place; informational content continues to omit the 👉 prefix
- **`onboarding-flow.md`**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines the onboarding sequence (setup → language → prerequisites → introduction → track selection)
- **`ask-bootcamper` hook**: The `agentStop` hook at `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` that recaps accomplishments and asks a contextual 👉 closing question
- **Closing question**: A question placed at the end of the agent's output that requires user input before proceeding — owned exclusively by the `ask-bootcamper` hook
- **WAIT instruction**: A directive in a steering file telling the agent to stop and wait for user input before continuing

## Bug Details

### Bug Condition

The bug manifests when the agent executes onboarding steps 1b, 2, 4, or 5 from `onboarding-flow.md`. Each of these steps ends with an inline 👉 closing question and a WAIT instruction, which conflicts with the `ask-bootcamper` hook's role as the single owner of closing questions. The agent either paraphrases the inline question (dropping the 👉 prefix), or outputs the inline question and then the hook appends a second 👉 question.

**Formal Specification:**

```
FUNCTION isBugCondition(step)
  INPUT: step of type OnboardingStep (a section of onboarding-flow.md)
  OUTPUT: boolean

  RETURN step.content CONTAINS inline 👉 closing question
         AND step.content CONTAINS WAIT instruction after the question
         AND ask-bootcamper hook IS active on agentStop
END FUNCTION
```

### Examples

- **Step 1b (Team Detection)**: Ends with `"👉 Which team member are you?"` followed by `WAIT for response.` — the hook will also fire and may generate a second question, or the agent may paraphrase and drop the 👉 prefix
- **Step 2 (Language Selection)**: Ends with `Ask: "👉 Which language would you like to use?" WAIT for response.` — same dual-question conflict
- **Step 4 (Bootcamp Introduction)**: Ends with `Ask: "👉 Does this outline make sense? Any questions before we choose a track?..." WAIT for response.` — same dual-question conflict
- **Step 5 (Track Selection)**: Ends with `Present tracks with: "👉 Which track sounds right for you?"` — same dual-question conflict (implicit WAIT at end of flow)
- **Step 0, 1, 3 (Setup, Directory, Prerequisites)**: These steps do NOT end with inline 👉 questions — they are not affected by the bug

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The `ask-bootcamper` hook continues to fire on every `agentStop` and generate contextual 👉 closing questions based on what the agent just accomplished
- The `ask-bootcamper` hook continues to skip the recap and just ask a contextual 👉 question when no files changed and no substantive work was done
- The `agent-instructions.md` closing-question ownership rule continues to be enforced ("Never end your turn with a closing question — the `ask-bootcamper` hook owns all closing questions")
- Informational content (module overviews, status updates, file listings) continues to omit the 👉 prefix
- The onboarding step sequence remains the same: setup preamble → directory structure → team detection → language selection → prerequisite check → bootcamp introduction → track selection
- The `ask-bootcamper` hook file (`senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`) is not modified
- The `agent-instructions.md` file is not modified

**Scope:**
All onboarding steps that do NOT currently have inline 👉 closing questions (steps 0, 1, 3) are completely unaffected by this fix. The fix only touches the trailing question/WAIT patterns in steps 1b, 2, 4, and 5. The informational content within those steps (language detection logic, prerequisite checks, welcome banner, track descriptions) remains unchanged.

## Hypothesized Root Cause

Based on the bug analysis, the root cause is an architectural contradiction in the steering file design:

1. **Dual-source closing questions**: `onboarding-flow.md` was written with inline 👉 closing questions and WAIT instructions before the `ask-bootcamper` hook existed (or before the closing-question ownership rule was established). The hook was added later as the canonical source of closing questions, but the steering file was never updated to remove its inline questions.

2. **Unreliable prompt-based suppression**: The hook's suppression logic ("If your previous output already ends with a 👉 question, do nothing") relies on the LLM correctly detecting an existing trailing 👉 question in its own output. This is a soft prompt instruction, not a deterministic check — LLMs do not reliably follow suppression paths, especially when the inline question was paraphrased or reformatted.

3. **Paraphrasing drops the prefix**: When the agent encounters an inline 👉 question embedded in prose, it may rephrase the question in its own words, dropping the 👉 prefix. The hook's structured prompt consistently applies the prefix because it generates the question from scratch rather than paraphrasing existing text.

4. **WAIT instructions conflict with hook-driven flow**: The WAIT instructions tell the agent to stop and wait, but the hook fires on `agentStop` regardless. The WAIT is redundant when the hook is the question owner — the agent should simply stop after presenting information, and the hook handles the question.

## Correctness Properties

Property 1: Bug Condition - Onboarding steps with inline closing questions have questions and WAITs removed

_For any_ onboarding step in `onboarding-flow.md` that previously contained an inline 👉 closing question and WAIT instruction (steps 1b, 2, 4, 5), the fixed steering file SHALL NOT contain that inline closing question or WAIT instruction; the step SHALL present its informational content and end without a closing question, allowing the `ask-bootcamper` hook to be the sole source of the closing 👉 question.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Non-question content and hook behavior unchanged

_For any_ content in `onboarding-flow.md` that is not an inline closing 👉 question or WAIT instruction (informational content, logic instructions, banners, tables, validation gates), the fixed steering file SHALL preserve that content unchanged. The `ask-bootcamper` hook SHALL continue to fire on `agentStop` and generate contextual 👉 questions, and the onboarding step sequence SHALL remain the same.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Specific Changes**:

1. **Remove the strict rule preamble**: Delete the `🚨 STRICT RULE` paragraph at the top that mandates inline questions with WAITs at the end of each section. This rule contradicts the hook-based architecture. Replace with a note that the `ask-bootcamper` hook handles closing questions.

2. **Step 1b (Team Detection)**: Remove the inline `"👉 Which team member are you?"` closing question and `WAIT for response.` instruction. Keep the instruction to present the member list. The hook will generate a contextual question asking the bootcamper to identify themselves.

3. **Step 2 (Language Selection)**: Remove the `Ask: "👉 Which language would you like to use?" WAIT for response.` line. Keep the language detection logic, MCP query instructions, and preference persistence logic. The hook will generate a contextual question about language choice.

4. **Step 4 (Bootcamp Introduction)**: Remove the `Ask: "👉 Does this outline make sense?..." WAIT for response.` line. Keep the welcome banner, overview content, and module table. The hook will generate a contextual question about the overview.

5. **Step 5 (Track Selection)**: Remove the `Present tracks with: "👉 Which track sounds right for you?"` line. Keep the module table, track descriptions, and response interpretation logic. The hook will generate a contextual question about track selection.

6. **No changes to other files**: The `ask-bootcamper` hook already generates contextual questions based on what the agent just presented. The `agent-instructions.md` already has the closing-question ownership rule. No changes needed to either file.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Since this is a steering file (natural language instructions for an LLM), testing focuses on structural analysis of the file content rather than runtime execution.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that `onboarding-flow.md` contains inline 👉 closing questions with WAIT instructions in steps 1b, 2, 4, and 5.

**Test Plan**: Parse the unfixed `onboarding-flow.md` and check each step section for the presence of inline 👉 closing questions and WAIT instructions. Run these tests on the UNFIXED file to confirm the bug condition exists.

**Test Cases**:
1. **Step 1b inline question**: Verify step 1b contains `"👉 Which team member are you?"` and `WAIT` (will find match on unfixed code)
2. **Step 2 inline question**: Verify step 2 contains `"👉 Which language would you like to use?"` and `WAIT` (will find match on unfixed code)
3. **Step 4 inline question**: Verify step 4 contains `"👉 Does this outline make sense?"` and `WAIT` (will find match on unfixed code)
4. **Step 5 inline question**: Verify step 5 contains `"👉 Which track sounds right for you?"` (will find match on unfixed code)

**Expected Counterexamples**:
- Each of the four steps contains at least one inline 👉 closing question
- Steps 1b, 2, and 4 contain explicit WAIT instructions; step 5 has an implicit WAIT at end of flow
- The preamble contains a `🚨 STRICT RULE` that mandates this pattern

### Fix Checking

**Goal**: Verify that for all onboarding steps where the bug condition holds, the fixed file no longer contains inline closing questions or WAIT instructions.

**Pseudocode:**

```
FOR ALL step WHERE isBugCondition(step) DO
  fixed_content := read_step_from_fixed_file(step)
  ASSERT NOT contains_inline_closing_question(fixed_content)
  ASSERT NOT contains_trailing_wait_instruction(fixed_content)
  ASSERT contains_informational_content(fixed_content)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all content where the bug condition does NOT hold, the fixed file preserves that content unchanged.

**Pseudocode:**

```
FOR ALL content WHERE NOT isBugCondition(content) DO
  ASSERT original_file(content) = fixed_file(content)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate random section selections and verify non-question content is preserved
- It catches edge cases where informational content might be accidentally removed
- It provides strong guarantees that the step sequence and logic instructions are unchanged

**Test Plan**: Parse both the unfixed and fixed versions of `onboarding-flow.md`. For each section, extract the informational content (excluding inline closing questions and WAIT instructions) and verify it is preserved in the fixed version.

**Test Cases**:
1. **Step sequence preservation**: Verify the fixed file contains the same step headings in the same order (0, 1, 1b, 2, 3, 4, 5)
2. **Informational content preservation**: Verify the welcome banner, module table, track descriptions, language detection logic, prerequisite check logic, and team detection logic are unchanged
3. **Non-affected steps preservation**: Verify steps 0, 1, and 3 are completely unchanged
4. **Hook file preservation**: Verify `ask-bootcamper.kiro.hook` is not modified
5. **Agent instructions preservation**: Verify `agent-instructions.md` is not modified

### Unit Tests

- Parse each affected step (1b, 2, 4, 5) in the fixed file and assert no inline 👉 closing questions exist
- Parse each affected step and assert no trailing WAIT instructions exist
- Parse each affected step and assert informational content is preserved
- Verify the preamble no longer mandates inline questions with WAITs

### Property-Based Tests

- Generate random step selections from the fixed file and verify none contain inline 👉 closing questions followed by WAIT instructions
- Generate random content sections and verify non-question content matches between unfixed and fixed versions
- Test that all step headings and their ordering are preserved across many random section samples

### Integration Tests

- Simulate the full onboarding flow with the fixed steering file and verify the agent presents information without inline closing questions
- Verify the `ask-bootcamper` hook generates appropriate contextual 👉 questions after each onboarding step
- Verify no duplicate questions appear when the hook fires after a step that previously had an inline question
