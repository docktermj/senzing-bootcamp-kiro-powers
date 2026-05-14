# Disambiguate Language Prompt Bugfix Design

## Overview

The onboarding language-selection step (Step 2 in `onboarding-flow.md`) uses the bare word "language" in its prompt without the qualifier "programming." This creates ambiguity — a bootcamper could interpret the question as asking about a natural/spoken language rather than a programming language. The fix is minimal and textual: replace "language" with "programming language" in the Step 2 prompt wording within the steering file. No logic changes are required; only the user-facing text is affected.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — the language-selection prompt at onboarding Step 2 uses the word "language" without the qualifier "programming"
- **Property (P)**: The desired behavior — the prompt explicitly says "programming language" so the question is unambiguous
- **Preservation**: Existing behaviors that must remain unchanged — MCP language list display, discouraged-language warnings, config persistence, and mandatory gate behavior
- **onboarding-flow.md**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines the onboarding sequence
- **Step 2 (Language Selection)**: The onboarding step where the bootcamper chooses their programming language for the bootcamp
- **Mandatory Gate**: A step marked with ⛔ where the agent must stop and wait for real user input

## Bug Details

### Bug Condition

The bug manifests when the agent presents the language-selection question at onboarding Step 2. The prompt text uses "language" without "programming," making it ambiguous whether the question refers to a programming language or a natural/spoken language.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type PromptText (the rendered language-selection prompt at Step 2)
  OUTPUT: boolean

  RETURN input.stepNumber == 2
         AND input.promptType == "language_selection"
         AND input.promptText CONTAINS "language"
         AND input.promptText DOES NOT CONTAIN "programming language"
END FUNCTION
```

### Examples

- **Example 1**: Prompt says "Which language would you like to use?" → Ambiguous. A bootcamper unfamiliar with the context could think it means English, Spanish, etc. **Expected**: "Which programming language would you like to use?"
- **Example 2**: Prompt says "Select your preferred language:" → Ambiguous without seeing the option list. **Expected**: "Select your preferred programming language:"
- **Example 3**: Prompt says "What language do you want for the bootcamp?" → Still ambiguous. **Expected**: "What programming language do you want for the bootcamp?"
- **Edge case**: If the option list (Python, Java, C#, Rust, TypeScript) is visible, the ambiguity is reduced but not eliminated — the prompt text itself should still be unambiguous for accessibility and clarity.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The system must continue to display the MCP-returned list of supported languages for the bootcamper's platform
- The system must continue to relay the MCP server's warning and suggest alternatives when a discouraged or unsupported language is detected
- The system must continue to persist the language selection to `config/bootcamp_preferences.yaml` and load the corresponding language steering file
- The system must continue to stop and wait for real input at the mandatory gate without assuming or fabricating a choice

**Scope:**
All behaviors other than the prompt wording at Step 2 should be completely unaffected by this fix. This includes:
- MCP tool calls to retrieve supported languages
- Platform detection logic
- Warning/suggestion logic for discouraged languages
- Config file persistence
- Language steering file loading
- Mandatory gate enforcement
- All other onboarding steps (0–5)

## Hypothesized Root Cause

Based on the bug description, the root cause is straightforward:

1. **Missing qualifier in prompt text**: The Step 2 section of `onboarding-flow.md` uses the word "language" in its heading ("Language Selection") and in the instructional text without consistently qualifying it as "programming language." The agent follows this steering file verbatim when generating prompts, so the ambiguity propagates to the bootcamper-facing output.

2. **Implicit context assumption**: The original author assumed the option list (Python, Java, C#, Rust, TypeScript) would always be visible alongside the prompt, making the qualifier unnecessary. However, the prompt text should be self-contained and unambiguous even without the option list visible.

3. **No explicit wording constraint**: The steering file lacks a directive requiring the agent to use "programming language" in the prompt. Without this constraint, the agent may paraphrase using just "language."

## Correctness Properties

Property 1: Bug Condition - Programming Language Qualifier Present

_For any_ rendering of the language-selection prompt at onboarding Step 2, the system SHALL use the phrase "programming language" in the prompt text, ensuring the question is unambiguous regardless of whether the option list is visible.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Unchanged Onboarding Behaviors

_For any_ interaction at the language-selection step that does NOT involve the prompt wording (MCP list display, discouraged-language warnings, config persistence, mandatory gate enforcement), the fixed steering file SHALL produce exactly the same behavior as the original, preserving all existing functionality for non-prompt aspects of Step 2.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Section**: Step 2 (Language Selection)

**Specific Changes**:
1. **Update section heading**: Change "## 2. Language Selection" to "## 2. Programming Language Selection" to set unambiguous context from the heading level.

2. **Add explicit wording directive**: Add a clear instruction that the agent MUST use the phrase "programming language" (not just "language") when presenting the selection question to the bootcamper.

3. **Update example prompt text**: Change the example/instructional text from patterns like "present the MCP-returned language list" to "present the MCP-returned programming language list" where it describes what to show the bootcamper.

4. **Add disambiguation constraint**: Add a constraint line such as: "When presenting this question, always use the phrase 'programming language' — never the bare word 'language' alone — to avoid ambiguity with natural/spoken languages."

5. **Preserve all other content**: The MCP call instructions, warning relay logic, config persistence, mandatory gate marker, and all other Step 2 content must remain exactly as-is.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Parse the Step 2 section of `onboarding-flow.md` and check whether the prompt-facing text contains "programming language." Run these tests on the UNFIXED file to observe failures and confirm the root cause.

**Test Cases**:
1. **Heading Check**: Verify the Step 2 heading contains "programming language" (will fail on unfixed code — heading says "Language Selection")
2. **Directive Check**: Verify an explicit wording directive exists requiring "programming language" (will fail on unfixed code — no such directive exists)
3. **Prompt Example Check**: Verify any example prompt text uses "programming language" (will fail on unfixed code — uses bare "language")
4. **Disambiguation Constraint Check**: Verify a disambiguation constraint is present (will fail on unfixed code — no constraint exists)

**Expected Counterexamples**:
- The heading "Language Selection" lacks the "programming" qualifier
- No explicit directive constrains the agent to say "programming language"
- Possible cause: original text assumed context from the option list would disambiguate

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL prompt_text WHERE isBugCondition(prompt_text) DO
  result := parseStep2Section(onboarding_flow_fixed)
  ASSERT "programming language" IN result.promptDirectives
  ASSERT result.headingText CONTAINS "programming language"
         OR result.bodyText CONTAINS explicit disambiguation constraint
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL behavior WHERE NOT isBugCondition(behavior) DO
  ASSERT onboarding_flow_original(behavior) = onboarding_flow_fixed(behavior)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate many variations of onboarding state and verify non-prompt behaviors are unchanged
- It catches edge cases where a text change might accidentally alter parsing or logic
- It provides strong guarantees that MCP calls, config persistence, and gate behavior are preserved

**Test Plan**: Parse the unfixed `onboarding-flow.md` to capture the baseline behavior for MCP calls, config persistence, warning relay, and mandatory gate. Then write property-based tests verifying these behaviors are identical in the fixed version.

**Test Cases**:
1. **MCP Call Preservation**: Verify the fixed file still instructs the agent to call `get_capabilities` or `sdk_guide` on the Senzing MCP server
2. **Warning Relay Preservation**: Verify the fixed file still contains the discouraged-language warning relay instruction
3. **Config Persistence Preservation**: Verify the fixed file still instructs persisting selection to `config/bootcamp_preferences.yaml`
4. **Mandatory Gate Preservation**: Verify the fixed file still contains the ⛔ mandatory gate marker and stop instruction

### Unit Tests

- Parse Step 2 heading and assert it contains "programming language" or "Programming Language"
- Parse Step 2 body and assert a disambiguation directive is present
- Parse Step 2 and assert MCP call instructions are unchanged from baseline
- Parse Step 2 and assert mandatory gate text is unchanged from baseline

### Property-Based Tests

- Generate random substrings of the Step 2 section and verify "programming language" appears in prompt-facing contexts
- Generate variations of the section structure and verify preservation requirements (MCP call, config persistence, gate) are always present
- Verify that no other sections of `onboarding-flow.md` are modified by the fix (diff-based property)

### Integration Tests

- Run a simulated onboarding flow through Step 2 and verify the agent output contains "programming language"
- Verify the full onboarding sequence (Steps 0–5) still completes without errors after the fix
- Verify that `config/bootcamp_preferences.yaml` is correctly written after language selection in the fixed flow
