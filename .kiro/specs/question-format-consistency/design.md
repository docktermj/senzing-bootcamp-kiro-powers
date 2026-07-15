# Question Format Consistency Bugfix Design

## Overview

Three related question-formatting defects cause the bootcamp's standard question convention (👉 prefix + bold question text) to be violated at two specific paths: (1) the session-recreation re-presentation path, where a pending question stored in `config/.question_pending` is echoed without formatting after a new session is created, and (2) the graduation/track-completion path, where the closing message either lacks a clearly marked question or omits the 👉 icon. The fix targets agent guidance in Markdown steering files and paired hook-prompt guidance, ensuring the formatting convention is upheld at these two previously uncovered paths.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the formatting violation — either a pending question re-presented across a session boundary without the standard renderer, or the bootcamp-completion turn ending without a properly formatted 👉 closing question
- **Property (P)**: The desired behavior — every question presented to the bootcamper (including re-presented pending questions and the bootcamp-completion question) carries the 👉 prefix at the start of the line with bold question text (`**...**`), with 👉 outside the bold span
- **Preservation**: All existing question-formatting behavior outside these two paths, the `.question_pending` write/delete lifecycle, and the graduation/track-completion artifact generation must remain unchanged
- **session-resume.md**: The steering file at `senzing-bootcamp/steering/session-resume.md` that governs session-recreation behavior including pending question re-presentation
- **module-completion-track.md**: The steering file at `senzing-bootcamp/steering/module-completion-track.md` that governs track-completion celebration and graduation offers
- **graduation.md**: The steering file at `senzing-bootcamp/steering/graduation.md` that governs the graduation workflow
- **agent-behavior-rules.md**: The steering file at `senzing-bootcamp/steering/agent-behavior-rules.md` that defines Rule 4 (Consistent Pointer Indicator) and the leading-question guarantee
- **conversation-protocol.md**: The steering file at `senzing-bootcamp/steering/conversation-protocol.md` that defines turn-taking, the One Question Rule, and the bold-question convention
- **Standard question renderer**: The formatting convention requiring 👉 at the start of the line, outside the bold span, followed by question text wrapped in `**...**`

## Bug Details

### Bug Condition

The bug manifests in two distinct paths:

**Path A — Session-recreation re-presentation:** When a pending question stored in `config/.question_pending` is re-presented to the bootcamper after a new session is created, the session-resume flow echoes the raw stored question text rather than re-rendering it through the standard question renderer, causing the 👉 prefix and bold styling to be lost.

**Path B — Graduation/track-completion closing:** When the track-completion or graduation workflow reaches its final yielding turn, either (a) no clearly marked question is presented (plain closing statements only), or (b) the bootcamp-completion question carries a celebratory emoji and bold text but omits the standard 👉 icon that prefaces every other decision-point question.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentTurn
  OUTPUT: boolean
  
  LET path_a = input.isSessionResumeTurn
               AND input.pendingQuestionExists
               AND input.pendingQuestionSource == "config/.question_pending"
               AND input.isNewSession
               AND NOT input.pendingQuestionRenderedWithPointerAndBold

  LET path_b = input.isTrackCompletionTurn OR input.isGraduationFinalTurn
               AND (NOT input.closingQuestionExists
                    OR (input.closingQuestionExists
                        AND NOT input.closingQuestionHasPointerPrefix))

  RETURN path_a OR path_b
END FUNCTION
```

### Examples

- **Path A example**: Bootcamper completes Module 3 step, agent asks "👉 **Ready to move on to Module 4 (Data Collection)?**" and writes `config/.question_pending`. Session ends. New session starts. Session-resume reads the pending file and re-presents the question as plain text "Ready to move on to Module 4 (Data Collection)?" — missing the 👉 prefix and bold styling.
- **Path B example (no question)**: Bootcamper finishes the Core track (Module 7). The track-completion celebration presents "You've completed the Core Bootcamp!" and various offers, but ends with a plain statement rather than a marked closing question.
- **Path B example (missing 👉)**: The bootcamp-completion question is presented as "🎉 **The Senzing Bootcamp is complete. Do you have anything else you'd like to discuss?**" — carries bold and a celebratory emoji but lacks the mandatory 👉 at the start of the line.
- **Path A edge case (same-session re-presentation)**: Within the same session, the pending question is re-surfaced after an intercept/retry cycle — this already works correctly because the agent re-emits the question with formatting intact; no fix needed here.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- All existing 👉 questions outside the session-recreation re-presentation path and the graduation-completion path (onboarding, module steps, module transitions, feedback, and the in-session resume welcome-back question) continue to render with 👉 prefix and bold question text
- The `.question_pending` write/delete lifecycle (structured format: type on first line, question text on subsequent lines) remains unchanged
- The One Question Rule (exactly one 👉 per yielding turn) continues to be enforced
- Informational content (banners, journey maps, summaries, status updates) continues to omit 👉
- The `write-policy-gate` hook validation on `.question_pending` writes continues unchanged
- The Treat-as-answer and Delete-and-process rules continue to apply when a bootcamper responds to a pending question
- The graduation/track-completion workflow's other artifacts (recap, PDF, transcript, certificate, indexes, graduation report) continue to be generated as today

**Scope:**
All inputs that do NOT involve (a) pending-question re-presentation across a new session or (b) the terminal track-completion/graduation closing question should be completely unaffected by this fix. This includes:
- Questions asked fresh within a single session
- Module-transition questions
- Questions re-surfaced after write-policy-gate intercepts (same session)
- Mid-graduation step-confirmation questions (already formatted correctly)
- The session-resume welcome-back question (already formatted correctly)

## Hypothesized Root Cause

Based on the bug description and analysis of the steering files, the most likely issues are:

1. **Missing re-rendering instruction in `session-resume.md`**: The Step 3 "Summarize and Confirm" section writes a new welcome-back question with proper formatting, but the path that handles an *existing* `.question_pending` file from a prior session does not instruct the agent to re-render the stored question through the standard formatting convention. The stored text in `.question_pending` uses the structured format (type on line 1, raw question text on subsequent lines) — the raw text lacks presentational formatting because formatting is applied at output time, not at storage time. The session-resume flow currently echoes this raw text directly.

2. **No explicit track-completion closing question in `module-completion-track.md`**: The track-completion celebration in `module-completion-track.md` presents a series of offers (export, record, analytics, certificate, graduation, feedback) and a "Load `lessons-learned.md` and offer the retrospective" instruction, but does not define an explicit, unconditional bootcamp-completion closing question that carries 👉 formatting. The flow assumes the graduation or retrospective offer will serve as the closing question, but those are conditional paths — when all offers are declined, no clearly marked final question remains.

3. **Missing 👉 on the implicit completion question**: Even when a closing question is implicitly present at track completion (e.g., through the graduation offer or lessons-learned retrospective offer), the text in `module-completion-track.md` does not explicitly require the 👉 prefix on the terminal question. The celebration section's phrasing uses emoji-prefixed offers ("🎓 Would you like to…") without the 👉 convention.

4. **No "re-render on session recreation" rule in `agent-behavior-rules.md`**: Rule 4 defines the formatting convention and the leading-question guarantee, but does not address the case where a previously stored question is re-surfaced from `.question_pending` after a session boundary. The rule implicitly assumes questions are always freshly composed.

## Correctness Properties

Property 1: Bug Condition - Pending Question Re-Presentation Formatting

_For any_ session-resume turn where `config/.question_pending` exists from a prior session and the agent re-presents the stored question to the bootcamper, the fixed session-resume guidance SHALL render the re-presented question with the 👉 prefix at the start of the line and the question text wrapped in bold (`**...**`), with 👉 outside the bold span, matching the standard question convention.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Bug Condition - Track-Completion Closing Question

_For any_ track-completion or graduation-final turn where the bootcamp has been completed, the fixed steering guidance SHALL ensure the turn ends with exactly one clearly marked 👉 closing question with bold question text that signals finality and invites final discussion.

**Validates: Requirements 2.4, 2.5, 2.6**

Property 3: Preservation - Existing Question Formatting Unchanged

_For any_ agent turn that does NOT involve pending-question re-presentation across a session boundary and does NOT involve the terminal track-completion/graduation closing question, the fixed steering guidance SHALL produce exactly the same question formatting behavior as the original guidance, preserving all existing 👉-prefixed, bold-wrapped questions and omitting 👉 from informational content.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/session-resume.md`

**Section**: Step 3 (Summarize and Confirm) — pending question re-presentation

**Specific Changes**:
1. **Add a "Pending Question Re-Rendering" subsection** before the welcome-back banner in Step 3 that instructs the agent: when `config/.question_pending` exists from a prior session, read the stored question text (lines 2+), re-render it with the standard 👉 prefix and bold formatting before presenting it, rather than echoing the raw stored text. The re-rendered question replaces the default "Ready to continue?" question so only one 👉 question closes the turn.
2. **Specify the re-rendering format explicitly**: "Present the stored question as: `👉 **{stored question text}**`" — with 👉 at the start of the line, outside the bold span, and the question text inside bold.
3. **Preserve the `.question_pending` lifecycle**: After re-rendering, the file remains in place (it was already written); the treat-as-answer and delete-and-process rules on the bootcamper's next turn remain unchanged.

---

**File**: `senzing-bootcamp/steering/module-completion-track.md`

**Section**: Path Completion Celebration — after all offers are resolved

**Specific Changes**:
1. **Add an explicit "Bootcamp-Completion Closing Question" subsection** at the end of the celebration flow, after the feedback reminder and before loading `lessons-learned.md`. This subsection defines the unconditional final question that closes the track-completion turn.
2. **Specify the exact format**: The closing question MUST use `👉 **{question text}**` format (e.g., `👉 **The Senzing Bootcamp is complete. Do you have anything else you would like to discuss?**`). The 👉 is at the start of the line, outside the bold span. Any celebratory emoji appears before or within the bold span but does NOT replace 👉.
3. **Enforce the leading-question guarantee for the terminal turn**: State that this closing question carries the same One Question Rule obligation as any other yielding turn — exactly one 👉, written to `config/.question_pending`, with the agent stopping immediately after.

---

**File**: `senzing-bootcamp/steering/agent-behavior-rules.md`

**Section**: Rule 4 (Consistent Pointer Indicator)

**Specific Changes**:
1. **Add a "Session-Recreation Re-Rendering" clause** to Rule 4 stating: "When re-presenting a pending question stored in `config/.question_pending` after a session boundary (new session creation), re-render the stored question text with the 👉 prefix and bold formatting. Do not echo raw stored text without presentational formatting."
2. **Add a "Track-Completion / Graduation Terminal Turn" clause** stating: "The track-completion and graduation-final turns are subject to the same 👉 + bold formatting convention as all other yielding turns. The terminal question closing the bootcamp carries the 👉 prefix regardless of any celebratory emoji present."

---

**File**: `senzing-bootcamp/steering/graduation.md`

**Section**: Mandatory Closing Step (end of graduation)

**Specific Changes**:
1. **Ensure the post-graduation announcement ends with a properly formatted closing question**: After the artifact announcement, the graduation turn must end with exactly one `👉 **{question text}**` question (e.g., `👉 **Is there anything else you would like to discuss or explore?**`).
2. **Make the requirement explicit in the "Mandatory Closing Step" section** so the agent cannot omit the 👉 from the graduation-final question.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse the relevant steering files and assert the presence of re-rendering instructions and properly formatted completion questions. Run these tests on the UNFIXED steering files to observe failures and confirm the guidance gaps.

**Test Cases**:
1. **Session-resume re-rendering test**: Assert that `session-resume.md` Step 3 contains an explicit instruction to re-render pending questions with 👉 + bold formatting when re-presenting across a session boundary (will fail on unfixed code)
2. **Track-completion closing question test**: Assert that `module-completion-track.md` contains an explicit, unconditional bootcamp-completion closing question with 👉 prefix (will fail on unfixed code)
3. **Graduation final question test**: Assert that `graduation.md` Mandatory Closing Step contains a 👉-prefixed closing question format (will fail on unfixed code)
4. **Rule 4 session-recreation clause test**: Assert that `agent-behavior-rules.md` Rule 4 contains a session-recreation re-rendering clause (will fail on unfixed code)

**Expected Counterexamples**:
- `session-resume.md` Step 3 echoes the stored question without any re-rendering instruction
- `module-completion-track.md` has no unconditional closing 👉 question after the celebration offers
- Possible causes: missing re-rendering guidance, missing terminal-question definition, missing Rule 4 clauses

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := applyFixedSteering(input)
  ASSERT expectedBehavior(result)
END FOR
```

Specifically:
- For Path A: assert that the re-presented pending question in `session-resume.md` carries the instruction to prefix with 👉 and wrap in bold
- For Path B: assert that the track-completion/graduation final turn includes exactly one 👉-prefixed, bold-wrapped closing question

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT originalSteering(input) = fixedSteering(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many steering-file scenarios automatically across the input domain (different module numbers, different pending question types, different session states)
- It catches edge cases where a formatting change might accidentally affect non-target paths
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED steering files first for non-target question paths (onboarding, module steps, module transitions, in-session resume), then write property-based tests capturing that behavior is preserved after the fix.

**Test Cases**:
1. **Onboarding question preservation**: Verify that onboarding flow questions retain their existing 👉 + bold formatting unchanged after the fix
2. **Module-step question preservation**: Verify that mid-module step questions continue to be formatted correctly
3. **Same-session pending preservation**: Verify that a pending question re-surfaced within the same session (after intercept/retry) is unaffected by the session-recreation re-rendering clause
4. **Informational content preservation**: Verify that banners, journey maps, and status updates continue to omit 👉
5. **Graduation artifact preservation**: Verify that recap PDF, transcript, certificates, and other graduation artifacts are generated unchanged

### Unit Tests

- Test that `session-resume.md` contains a pending-question re-rendering instruction with the canonical format `👉 **{text}**`
- Test that `module-completion-track.md` contains an unconditional closing 👉 question with proper formatting
- Test that `graduation.md` Mandatory Closing Step includes a properly formatted terminal question
- Test that `agent-behavior-rules.md` Rule 4 includes both the session-recreation and track-completion clauses
- Test that the `.question_pending` structured format (type + text) is referenced in the re-rendering path

### Property-Based Tests

- Generate random question texts and verify that the re-rendering instruction would produce `👉 **{text}**` format for any stored pending question content
- Generate random track-completion states (different tracks, different module counts) and verify the closing question is always present with 👉 + bold
- Generate random non-target steering paths and verify no formatting changes were introduced outside the two target paths

### Integration Tests

- Test full session-resume flow with a `.question_pending` file present: verify the re-rendered output matches the standard format
- Test track-completion flow end-to-end: verify the celebration ends with exactly one 👉 closing question
- Test graduation flow end-to-end: verify the Mandatory Closing Step ends with exactly one 👉 closing question
- Test that the One Question Rule is maintained at the session-recreation and track-completion paths (no duplicate 👉 questions)
