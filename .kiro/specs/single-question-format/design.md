# Single-Question Format Bugfix Design

## Overview

The agent produces compound questions — alternatives joined by "or" in prose form — in its general conversational output, despite existing rules in `conversation-protocol.md` and enforcement in the `write-policy-gate` hook. The enforcement gap exists because the `write-policy-gate` only validates questions written to `config/.question_pending`, while compound questions appear in the agent's direct response text which bypasses this gate entirely. The fix must close this enforcement gap by ensuring single-question format is validated across all output paths, not just `.question_pending` writes.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when the agent's output contains two or more alternatives joined by "or" (or equivalent conjunctions) in prose form within a 👉 question
- **Property (P)**: The desired behavior — multi-alternative questions are formatted as numbered lists preceded by a single neutral question; single-action questions contain no appended alternatives
- **Preservation**: Existing behaviors that must remain unchanged — simple yes/no questions stay as inline prose, "or" within numbered list item descriptions remains allowed, informational prose is not restructured
- **conversation-protocol.md**: The steering file in `senzing-bootcamp/steering/` that defines turn-taking, question handling, and the One Question Rule
- **write-policy-gate**: The `preToolUse` hook in `senzing-bootcamp/hooks/` that validates `.question_pending` writes for compound questions (Check 2)
- **ask-bootcamper**: The `agentStop` hook that generates closing questions when no question is already pending
- **Compound question**: A question that joins two or more distinct alternatives using conjunctions ("or", "alternatively", "or would you rather") in prose form, making "yes"/"no" ambiguous

## Bug Details

### Bug Condition

The bug manifests when the agent presents two or more alternatives to the bootcamper using "or" (or equivalent conjunctions) in prose form within its conversational output. The `write-policy-gate` hook only intercepts writes to `config/.question_pending`, so compound questions that appear directly in the agent's response text are never validated. Additionally, the `ask-bootcamper` hook generates closing questions without compound-question validation.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentOutput (a complete agent response turn)
  OUTPUT: boolean
  
  RETURN input.contains👉Question()
         AND input.questionText HAS multipleAlternatives()
         AND alternativesJoinedByProse(input.questionText)
         AND NOT formattedAsNumberedList(input.questionText)
END FUNCTION

FUNCTION multipleAlternatives(questionText)
  // Detects prose-joined alternatives via conjunctions
  RETURN questionText MATCHES pattern:
    "[action/option A], or [action/option B]"
    OR "[question]? Or [alternative question]?"
    OR "[question], or would you [alternative]?"
    OR "[question]? Anything [follow-up]?"
    OR "[confirmation]? Or should we [alternative]?"
END FUNCTION
```

### Examples

- **Compound either/or**: "👉 Would you like me to create a one-page executive summary you can share with your team or manager? Or shall we skip that and move on to Module 3?" → Bug: two alternatives joined by "Or" as sentence starter. Expected: numbered list with neutral lead question.
- **Appended alternative**: "👉 Does that look right? Or would you like me to adjust it?" → Bug: confirmation with appended alternative. Expected: only the confirmation question; handle corrections in next turn.
- **Prose-joined choices**: "👉 Would you like to proceed with Python or Java?" → Bug: alternatives joined by "or" in prose. Expected: numbered list ("Which language would you like to use? 1. Python 2. Java").
- **Simple yes/no (NOT a bug)**: "👉 Ready to move on to Module 3?" → Correct: single action, no alternatives, unambiguous yes/no.
- **"Or" inside list item (NOT a bug)**: "1. Share with your team or manager" → Correct: "or" within a list item description is allowed.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Simple yes/no questions with a single clear action must continue to use inline prose format (e.g., "👉 Ready to move on to Module 3?")
- Informational content without questions must continue to be presented as normal prose without restructuring into lists
- "Or" within numbered list option descriptions must continue to be allowed (e.g., "1. Share with your team or manager")
- The `write-policy-gate` hook must continue to enforce single-question rules at `.question_pending` write time
- Single-option confirmations must continue to use the simple "👉 [question]?" format without a numbered list
- The `ask-bootcamper` hook must continue to generate closing questions when no question is pending

**Scope:**
All agent outputs that do NOT contain a 👉 question with multiple prose-joined alternatives should be completely unaffected by this fix. This includes:
- Informational prose and explanations
- Code blocks and file content
- Simple yes/no questions with a single action
- Questions that already use numbered list format
- Non-question content that happens to contain the word "or"

## Hypothesized Root Cause

Based on the bug analysis, the most likely issues are:

1. **Enforcement Gap in Output Path**: The `write-policy-gate` hook only triggers on `preToolUse` for write operations targeting `config/.question_pending`. Questions embedded directly in the agent's response text are never intercepted by any validation hook. The `conversation-protocol.md` steering file contains the rules but relies on the agent's self-check compliance, which is insufficient.

2. **No Post-Generation Validation**: There is no `agentStop` or post-output hook that validates the agent's response for compound questions before it reaches the bootcamper. The `ask-bootcamper` hook generates questions but does not validate them against the single-question rule.

3. **Steering File Compliance Decay**: The rules in `conversation-protocol.md` are comprehensive but purely instructional. Over long sessions or after context compaction, the agent may lose adherence to these rules because there is no mechanical enforcement on the output itself.

4. **ask-bootcamper Hook Lacks Validation**: The `ask-bootcamper` hook generates closing questions in its Phase 1 output but has no compound-question validation logic. It can produce "Would you like X, or shall we Y?" without any check.

## Correctness Properties

Property 1: Bug Condition - Compound Questions Are Reformatted

_For any_ agent output where the bug condition holds (a 👉 question contains two or more alternatives joined by prose conjunctions), the enforcement mechanism SHALL either block the output and require reformatting as a numbered list preceded by a neutral question, or the steering/hook system SHALL prevent the compound question from being generated in the first place.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Non-Compound Output Unchanged

_For any_ agent output where the bug condition does NOT hold (simple yes/no questions, informational prose, questions already using numbered lists, or content without 👉 questions), the enforcement mechanism SHALL produce no interference, allowing the output to pass through unchanged and preserving all existing formatting behaviors.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/conversation-protocol.md`

**Section**: "One Question Rule" and "Choice Formatting"

**Specific Changes**:
1. **Strengthen Self-Check Section**: Add an explicit pre-output validation checklist that the agent must execute before every turn containing a 👉 question. Make the compound-question check the FIRST item (fail-fast).

2. **Add Explicit Rewrite Instructions**: Add a "Rewrite Protocol" subsection that provides step-by-step instructions for converting a compound question into the correct format (numbered list or single yes/no).

---

**File**: `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`

**Section**: Phase 1 closing question generation

**Specific Changes**:
3. **Add Compound-Question Validation to Phase 1**: Before outputting a closing question, the hook prompt must validate that the generated question does not contain prose-joined alternatives. If it does, the hook must reformat as a numbered list.

---

**File**: `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`

**Section**: Check 2 (Single-Question Enforcement)

**Specific Changes**:
4. **Expand Trigger Scope**: Modify the hook description and/or create a complementary `postToolUse` or `agentStop` hook that validates the agent's full response text (not just `.question_pending` writes) for compound questions. This closes the enforcement gap on the output path.

---

**New File**: `senzing-bootcamp/hooks/question-format-gate.kiro.hook`

**Specific Changes**:
5. **Create a New agentStop Validation Hook**: Create a dedicated `agentStop` hook that inspects the agent's most recent output for compound 👉 questions. If detected, it instructs the agent to rewrite the question before the turn is finalized. This provides mechanical enforcement on the output path that currently has none.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that generate agent-style output strings containing various question patterns and verify whether the current steering/hook system would catch compound questions. Run these tests against the current hook prompt logic to observe which patterns slip through.

**Test Cases**:
1. **Either/Or Prose Test**: Generate output with "👉 Would you like X, or shall we Y?" — verify this is NOT caught by current enforcement (will pass through unfixed code)
2. **Appended Alternative Test**: Generate output with "👉 Does that look right? Or would you like me to adjust it?" — verify this is NOT caught (will pass through unfixed code)
3. **Sentence-Starter Or Test**: Generate output with "👉 [question]? Or [alternative]?" — verify this is NOT caught (will pass through unfixed code)
4. **question_pending Write Test**: Generate the same compound question as a `.question_pending` write — verify this IS caught by the existing `write-policy-gate` (confirms the gap is output-path-only)

**Expected Counterexamples**:
- Compound questions in direct agent output pass through with no validation
- The same compound questions written to `.question_pending` are correctly blocked
- Possible causes: no hook intercepts general output text, only `.question_pending` writes are validated

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed system produces the expected behavior.

**Pseudocode:**
```
FOR ALL output WHERE isBugCondition(output) DO
  result := applyEnforcement(output)
  ASSERT result.questionFormat == NUMBERED_LIST
         OR result.questionFormat == SINGLE_YES_NO
  ASSERT NOT result.containsProseJoinedAlternatives()
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed system produces the same result as the original system.

**Pseudocode:**
```
FOR ALL output WHERE NOT isBugCondition(output) DO
  ASSERT applyEnforcement(output) == output  // unchanged
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many output strings automatically across the input domain (simple yes/no questions, informational prose, already-formatted numbered lists)
- It catches edge cases where "or" appears in non-question contexts that should not trigger reformatting
- It provides strong guarantees that non-compound outputs are never modified

**Test Plan**: Observe behavior on UNFIXED code first for non-compound outputs (simple questions, prose, lists), then write property-based tests capturing that behavior.

**Test Cases**:
1. **Simple Yes/No Preservation**: Verify "👉 Ready to move on to Module 3?" passes through unchanged after fix
2. **Informational Prose Preservation**: Verify prose paragraphs containing "or" but no 👉 question pass through unchanged
3. **Numbered List Preservation**: Verify questions already formatted as numbered lists are not double-reformatted
4. **List-Internal Or Preservation**: Verify "or" within numbered list item descriptions (e.g., "1. Share with your team or manager") is not flagged
5. **Non-Question Or Preservation**: Verify sentences like "You can use Python or Java for this step" without 👉 prefix are not affected

### Unit Tests

- Test compound question detection regex/logic against known violation patterns from `conversation-protocol.md`
- Test that the detection correctly identifies "or" as sentence starter ("Or shall we...")
- Test that the detection correctly ignores "or" inside numbered list items
- Test that simple yes/no questions are not flagged as compound
- Test the rewrite logic produces valid numbered-list format

### Property-Based Tests

- Generate random agent output strings with various "or" placements and verify the detection function correctly classifies compound vs. non-compound questions
- Generate random simple yes/no questions and verify they are never flagged
- Generate random numbered-list questions containing "or" in item descriptions and verify they are never flagged
- Generate random informational prose with "or" and verify it is never modified

### Integration Tests

- Test full hook pipeline: agent generates compound question → `question-format-gate` hook fires → agent rewrites as numbered list
- Test that `write-policy-gate` Check 2 continues to work for `.question_pending` writes alongside the new hook
- Test that `ask-bootcamper` hook Phase 1 output respects the new validation rules
- Test session-resume scenario: after context reload, compound question enforcement remains active
