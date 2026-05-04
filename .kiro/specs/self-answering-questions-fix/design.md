# Self-Answering Questions Fix — Bugfix Design

## Overview

The senzing-bootcamp Power's agent asks questions to the bootcamper during interactive modules but then answers those questions itself in the same turn instead of stopping and waiting. The root cause is that existing stop-and-wait directives in steering files are structurally too weak — they read as soft suggestions that the model's conversational momentum overrides. The fix strengthens these directives across multiple steering files by introducing structurally harder-to-ignore patterns: dedicated stop blocks with visual separators, repeated directives at multiple structural levels, and upgraded hook prompt language that reinforces the stop boundary before the agent generates.

The fix targets six files: `agent-instructions.md` (core Communication rules), `hook-registry.md` (ask-bootcamper hook prompt), `module-01-business-problem.md` (Module 1 Phase 1 question points), `module-01-phase2-document-confirm.md` (Module 1 Phase 2 question points), `onboarding-flow.md` (onboarding mandatory gates), and other module steering files containing question points. The changes are purely textual — no code logic, no hook behavior changes, no new files.

## Glossary

- **Bug_Condition (C)**: A question point in a steering file where the agent is expected to stop and wait for bootcamper input, but the existing directives are structurally insufficient to prevent the model from continuing to generate
- **Property (P)**: Every question point has a structurally enforced hard-stop pattern that makes it difficult for the model to continue generating past the question
- **Preservation**: Non-question steps (informational content, file creation, parsing, code generation) must not gain stop-and-wait directives; the hook's recap/closing-question logic and silence rule must remain intact
- **Question point**: Any location in a steering file where the agent asks the bootcamper a question requiring their real input — identified by 👉 markers, ⛔ mandatory gates, or explicit "STOP and wait" instructions
- **Hard-stop block**: A visually distinct, structurally separated block containing a stop directive that is harder for the model to skip over than inline text — uses visual separators, bold formatting, and repeated directives
- **ask-bootcamper hook**: The `agentStop` hook that fires after every agent turn; it suppresses output when a 👉 question is pending and generates a closing question when no question is pending

## Bug Details

### Bug Condition

The bug manifests when the agent reaches a question point in any steering file and continues generating past it — answering the question on the bootcamper's behalf, fabricating business details, or proceeding to the next step without real input. The existing safeguards (inline "STOP and wait" text, 👉 markers, the ask-bootcamper hook) are not structurally strong enough to override the model's tendency to continue generating after posing a question.

**Formal Specification:**

```text
FUNCTION isBugCondition(input)
  INPUT: input of type SteeringFileQuestionPoint
  OUTPUT: boolean

  RETURN input.isQuestionPoint == true
         AND input.requiresBootcamperResponse == true
         AND (
           NOT hasHardStopBlock(input)
           OR NOT hasRepeatedStopDirective(input)
           OR NOT hasStructuralSeparation(input)
         )
END FUNCTION
```

Where:

- `hasHardStopBlock(input)`: The question point is followed by a visually distinct stop block with bold formatting and explicit "end your response" / "produce no further content" language
- `hasRepeatedStopDirective(input)`: The stop directive appears at multiple structural levels (in the step, in the Communication rules, in the hook prompt)
- `hasStructuralSeparation(input)`: The stop directive is on its own line or in its own block, not buried in a paragraph

### Examples

- **Module 1 Step 7 gap-filling**: Agent asks "Are you working with people records, organization records, or both?" then immediately answers "I'll assume you're working with people records" and continues to Step 8. Expected: agent stops after the question, waits for bootcamper to respond.
- **Onboarding Step 5 track selection**: Agent presents tracks A–D, then says "I'll go with Track C for you" and starts Module 1. Expected: agent stops after presenting tracks, waits for bootcamper to choose.
- **Module 1 Step 9 deployment target**: Agent asks about deployment target, then says "Let's go with AWS" and writes the preference file. Expected: agent stops after presenting options, waits for bootcamper to choose.
- **Module 1 Step 1 git init**: Agent asks "Would you like me to initialize a git repository?" then immediately initializes it without waiting. Expected: agent stops after the 👉 question, waits for response.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- Non-question steps (Step 2 data privacy reminder, Step 6 parsing, Step 10 visual explanations, Step 12 document creation, Step 14 solution approach) must continue to execute fully in a single turn without new stop points
- The ask-bootcamper hook's recap and closing-question logic (the SECOND branch) must remain functionally identical
- The hook silence rule in `agent-instructions.md` must remain intact — zero output when a hook check passes with no action needed
- YAML frontmatter in all steering files must remain unchanged
- Step numbering, checkpoint counts, and Phase 2 references must remain unchanged
- The hook file structure (`.kiro.hook` JSON files) must not be modified by this fix — only the hook prompt text in `hook-registry.md` changes

**Scope:**

All steering file content that does NOT involve a question point requiring bootcamper input should be completely unaffected by this fix. This includes:

- Informational steps and statements
- File creation and code generation instructions
- Checkpoint writing instructions
- Module transition logic
- MCP tool usage instructions
- Context budget management rules

## Hypothesized Root Cause

Based on the bug description and analysis of the steering files, the most likely issues are:

1. **Inline stop directives lack structural weight**: Current "STOP and wait" instructions are plain text within paragraphs. The model treats them as suggestions rather than hard boundaries because they blend into the surrounding instructional text. A structurally separated, visually distinct block is harder to skip.

2. **Communication rules in agent-instructions.md are too brief**: The current rule "STOP and wait at 👉 questions and ⛔ gates" is a single bullet point among many. It needs to be elevated to a dedicated subsection with explicit "end your response immediately" language and concrete examples of prohibited behavior.

3. **ask-bootcamper hook prompt lacks pre-generation framing**: The hook fires on `agentStop` (after generation), so it can only suppress output retroactively. However, the hook prompt text is loaded into context before the next turn, so strengthening its "NEVER answer on behalf of the bootcamper" language and adding structural emphasis can influence the model's behavior on subsequent turns.

4. **Module steering files lack consistent stop patterns**: Some question points have 👉 markers and "STOP and wait" text (e.g., Module 1 Step 1, Step 9), while others rely on the general Communication rules alone (e.g., Step 7 gap-filling questions). Every question point needs the same structural hard-stop pattern.

5. **No explicit "end your response" language**: Current directives say "STOP and wait" but don't explicitly say "end your response here" or "produce no further content." The model may interpret "STOP" as "pause briefly" rather than "terminate output."

## Correctness Properties

Property 1: Bug Condition — Question Points Have Hard-Stop Blocks

_For any_ question point in a steering file where the agent asks the bootcamper a question requiring their real input (identified by 👉 markers, ⛔ mandatory gates, or explicit stop-and-wait instructions), the fixed steering file SHALL contain a structurally distinct hard-stop block with explicit "end your response" / "produce no further content" language, ensuring the model cannot easily skip past the stop directive.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation — Non-Question Content Unchanged

_For any_ step or section in a steering file that does NOT contain a question point requiring bootcamper input (informational steps, file creation steps, parsing steps, code generation steps), the fixed steering file SHALL preserve the original content without adding stop-and-wait directives, ensuring non-interactive work continues uninterrupted.

**Validates: Requirements 3.1, 3.2, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/agent-instructions.md`

**Section**: Communication

**Specific Changes**:

1. **Elevate stop-and-wait rule to a dedicated subsection**: Replace the single bullet point with a dedicated `### Question Stop Protocol` subsection that uses bold formatting, explicit "end your response immediately" language, and a concrete list of prohibited behaviors (answering on behalf, fabricating responses, continuing to next step).
2. **Add explicit end-of-turn framing**: Include language like "Treat every 👉 question and ⛔ gate as an end-of-turn boundary. Your response MUST end after the question text. Produce no further tokens."
3. **Add prohibited behavior examples**: List concrete examples of what the agent must NOT do: "Do not answer the question. Do not assume a response. Do not say 'I'll go with X.' Do not proceed to the next step. Do not write checkpoints for the current step."

---

**File**: `senzing-bootcamp/steering/hook-registry.md`

**Section**: ask-bootcamper hook prompt

**Specific Changes**:

1. **Strengthen the FIRST branch language**: Add structural emphasis to the "produce no output" directive. Include explicit "This is a hard stop — the bootcamper's real input is required" framing.
2. **Add pre-generation warning**: Add language at the start of the prompt that reinforces the stop boundary: "If the previous turn ended with a question, the bootcamper has not yet answered. You MUST NOT generate any content."

---

**File**: `senzing-bootcamp/steering/module-01-business-problem.md`

**Section**: Steps 1, 5, 7, 8, 9 (all question points)

**Specific Changes**:

1. **Add hard-stop blocks to each question point**: After each 👉 question, add a visually distinct stop block using bold formatting and explicit "end your response" language. Pattern: `> **🛑 STOP — End your response here.** Do not answer this question. Do not assume a response. Do not continue to the next step. Wait for the bootcamper's real input.`
2. **Strengthen Step 7 gap-filling questions**: Step 7 currently says "Ask about only one undetermined item per turn" but lacks explicit stop directives after each question. Add hard-stop blocks after the gap-filling question instructions.
3. **Strengthen Step 9 deployment target**: Already has "STOP and wait" but needs the upgraded hard-stop block pattern for consistency.

---

**File**: `senzing-bootcamp/steering/module-01-phase2-document-confirm.md`

**Section**: Steps 16, 17 (question points)

**Specific Changes**:

1. **Add hard-stop blocks to confirmation and stakeholder questions**: Steps 16 and 17 ask questions but lack explicit stop directives. Add the same hard-stop block pattern.

---

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Section**: Steps 2 (language selection), 4b (verbosity), 5 (track selection)

**Specific Changes**:

1. **Strengthen mandatory gate stop blocks**: The ⛔ gates in Steps 2 and 5 already have stop language but need the upgraded structural pattern with explicit "end your response" and prohibited behavior lists.
2. **Add hard-stop block to verbosity preference question**: Step 4b asks a question but relies on the general Communication rules. Add a stop block.

---

**Other module steering files** containing 👉 question points:

1. **Apply consistent hard-stop pattern**: Any module steering file with 👉 questions (`module-03-quick-demo.md`, `module-07-query-validation.md`, `module-11-deployment.md`, deployment platform files, `visualization-guide.md`) should receive the same structural hard-stop block pattern for consistency.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Since this bug is in steering file text (not executable code), tests parse the markdown files and verify structural properties of the content.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Parse steering files and check that question points lack the structural hard-stop patterns defined in the fix. Run these tests on the UNFIXED code to observe failures and confirm the bug exists.

**Test Cases**:

1. **Missing hard-stop blocks in Module 1**: Parse `module-01-business-problem.md`, extract each question point (Steps 1, 5, 7, 8, 9), and assert each has a hard-stop block with "end your response" language (will fail on unfixed code)
2. **Missing hard-stop blocks in onboarding**: Parse `onboarding-flow.md`, extract mandatory gates (Steps 2, 5), and assert each has a hard-stop block (will fail on unfixed code)
3. **Weak Communication rules**: Parse `agent-instructions.md` Communication section and assert it contains a dedicated stop protocol subsection with explicit prohibited behaviors (will fail on unfixed code)
4. **Weak hook prompt**: Parse `hook-registry.md` ask-bootcamper prompt and assert it contains strengthened pre-generation warning language (will fail on unfixed code)

**Expected Counterexamples**:

- Question points in Module 1 Steps 5, 7, 8 lack any stop directive
- Communication rules contain only a single bullet point about stopping
- Hook prompt lacks explicit "end your response" framing

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**

```text
FOR ALL questionPoint WHERE isBugCondition(questionPoint) DO
  result := parseFixedSteeringFile(questionPoint.file)
  ASSERT hasHardStopBlock(result, questionPoint)
  ASSERT hasExplicitEndResponseLanguage(result, questionPoint)
  ASSERT hasProhibitedBehaviorList(result, questionPoint) OR hasStructuralSeparation(result, questionPoint)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**

```text
FOR ALL step WHERE NOT isQuestionPoint(step) DO
  ASSERT contentUnchanged(originalFile, fixedFile, step)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It generates many test cases automatically across the input domain (all non-question steps across all affected files)
- It catches edge cases that manual unit tests might miss (e.g., a non-question step accidentally gaining a stop directive)
- It provides strong guarantees that behavior is unchanged for all non-question content

**Test Plan**: Observe behavior on UNFIXED code first for non-question steps, then write property-based tests capturing that behavior.

**Test Cases**:

1. **Module 1 non-question steps preserved**: Observe that Steps 2, 3, 4, 6 content is unchanged between unfixed and fixed versions
2. **Module 1 Phase 2 non-question steps preserved**: Observe that Steps 10, 11, 12, 13, 14, 15, 18 content is unchanged
3. **Onboarding non-question steps preserved**: Observe that Steps 0, 1, 1b, 3, 4, 4c content is unchanged
4. **Hook recap logic preserved**: Observe that the SECOND branch of the ask-bootcamper hook prompt (recap + closing question) is functionally preserved
5. **YAML frontmatter preserved**: Observe that all affected files retain their original YAML frontmatter
6. **Step counts preserved**: Observe that step numbering and checkpoint counts remain unchanged in all affected files

### Unit Tests

- Test that each question point in `module-01-business-problem.md` has a hard-stop block after the 👉 question
- Test that each mandatory gate in `onboarding-flow.md` has a hard-stop block after the ⛔ marker
- Test that `agent-instructions.md` Communication section contains a dedicated stop protocol subsection
- Test that the ask-bootcamper hook prompt in `hook-registry.md` contains strengthened language
- Test edge cases: question points at end of file, question points before Phase 2 reference

### Property-Based Tests

- Generate random step numbers from the set of question-point steps and verify each has a hard-stop block (fix checking)
- Generate random step numbers from the set of non-question steps and verify content is unchanged from baseline (preservation checking)
- Generate random steering file paths from the set of affected files and verify YAML frontmatter is preserved (preservation checking)
- Test across all 👉 question points in all steering files to verify consistent hard-stop pattern (fix checking)

### Integration Tests

- Parse all affected steering files end-to-end and verify the total count of hard-stop blocks matches the total count of question points
- Verify that the Communication section, hook prompt, and module steering files all use consistent stop-directive language
- Verify that no non-question step in any affected file contains a hard-stop block (no false positives)
