# Missing Pointer Marker Bugfix Design

## Overview

The agent omits the 👉 prefix marker when presenting the Step 4c comprehension check question during onboarding. The root cause is that the `onboarding-flow.md` steering file places the 👉 marker outside a quoted string (`👉 "That was a lot of ground to cover..."`), which the agent interprets as a structural annotation rather than a literal output requirement. The fix restructures the Step 4c instruction to make the 👉 prefix an unambiguous, mandatory part of the output text.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — when the agent executes Step 4c and formats the comprehension check question without the 👉 prefix
- **Property (P)**: The desired behavior — the comprehension check question output MUST begin with "👉 " followed by the question text
- **Preservation**: All other onboarding behaviors (informational content without 👉, other steps' 👉 questions, acknowledgment/clarification handling, single-question enforcement) must remain unchanged
- **onboarding-flow.md**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines the onboarding sequence including Step 4c
- **Step 4c**: The Comprehension Check substep where the agent asks if the bootcamper understands the overview before proceeding to track selection
- **👉 marker**: The pointer emoji prefix required on all questions directed at the bootcamper to signal that input is expected

## Bug Details

### Bug Condition

The bug manifests when the agent executes Onboarding Step 4c (Comprehension Check) and presents the question to the bootcamper. The current steering file format places the 👉 marker as a line-level annotation before a quoted string, which the agent treats as descriptive prose rather than a literal output format requirement.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type SteeringFileInstruction
  OUTPUT: boolean

  RETURN input.step == "4c"
         AND input.action == "present_comprehension_question"
         AND input.markerFormat == "annotation_before_quoted_string"
         AND agent_output_lacks_pointer_prefix(input.renderedOutput)
END FUNCTION
```

### Examples

- **Example 1**: Agent outputs `"That was a lot of ground to cover — does everything so far make sense?"` — DEFECTIVE (missing 👉 prefix)
- **Example 2**: Agent outputs `"👉 That was a lot of ground to cover — does everything so far make sense?"` — CORRECT (has 👉 prefix)
- **Example 3**: Agent paraphrases as `"Does everything make sense so far?"` — DEFECTIVE (missing 👉 prefix even on paraphrase)
- **Example 4**: Agent paraphrases as `"👉 Does everything make sense so far?"` — CORRECT (👉 prefix present on paraphrase)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Informational content during Step 4 (overview, module table, track descriptions) must continue to omit the 👉 prefix
- Other onboarding steps with 👉 questions (Steps 2, 3a, 3b, 4b, 5) must continue to include the 👉 prefix as currently specified
- Acknowledgment handling (bootcamper says "makes sense" → proceed to Step 5) must remain unchanged
- Clarification handling (bootcamper asks a question → answer using verbosity settings → check for more questions) must remain unchanged
- The enforce-single-question hook must continue to validate the question written to `config/.question_pending`

**Scope:**
All onboarding content and behavior outside of the Step 4c question formatting should be completely unaffected by this fix. This includes:
- All Step 4 informational content (overview, module table, entity resolution intro, verbosity selection)
- All other steps' question formatting (Steps 2, 3a, 3b, 4b, 5)
- Post-question response handling logic (acknowledgment vs. clarification branching)
- Hook behavior (ask-bootcamper, enforce-single-question)

## Hypothesized Root Cause

Based on the bug description and analysis of `onboarding-flow.md`, the most likely issue is:

1. **Ambiguous Marker Placement**: The current Step 4c instruction reads:
   ```
   👉 "That was a lot of ground to cover — does everything so far make sense?"
   ```
   The 👉 appears as a line-level annotation before the quoted string. The agent interprets this as "this line is a question prompt" (structural meaning) rather than "output the 👉 character as part of the text" (literal meaning).

2. **Inconsistent Pattern with Other Steps**: Other steps in the file (e.g., Step 2, Step 4b) use the same `👉` pattern but with longer instructional text following the marker. In those cases, the agent may still produce the 👉 because the surrounding instruction explicitly says "present" or "ask" with the marker included in the template. Step 4c's brevity (just a quoted string after the marker) makes it more susceptible to the agent treating the marker as metadata.

3. **Lack of Explicit Output Format Instruction**: The steering file does not include an explicit instruction like "Your output MUST begin with 👉" at the Step 4c level. The general protocol note at the top of the file mentions the `ask-bootcamper` hook generates 👉 closing questions, which may further confuse the agent about whether it needs to manually include the marker.

4. **Quoted String Interpretation**: When the agent sees `👉 "text..."`, it may parse the quotes as indicating the exact text to output (without the prefix) and the 👉 as a structural label indicating "this is a question." Removing the ambiguity requires either placing the 👉 inside the quotes or adding an explicit formatting instruction.

## Correctness Properties

Property 1: Bug Condition - Step 4c Output Includes Pointer Prefix

_For any_ execution of Step 4c where the agent presents the comprehension check question to the bootcamper, the agent's output SHALL begin with the "👉 " prefix followed by the question text, regardless of whether the question is quoted verbatim or paraphrased.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Non-Question Content Omits Pointer Prefix

_For any_ informational content presented during Step 4 that does not require bootcamper input (overview text, module table, track descriptions, entity resolution intro), the agent's output SHALL NOT include the 👉 prefix, preserving the existing distinction between informational content and questions.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Section**: Step 4c (Comprehension Check)

**Specific Changes**:

1. **Add Explicit Output Format Instruction**: Add a clear directive stating that the agent's output MUST begin with "👉 " before the question text. This removes ambiguity about whether the marker is structural or literal.

2. **Restructure the Template Text**: Change from the current format where 👉 is outside the quoted string to a format where the complete expected output (including 👉) is shown as a single verbatim block:
   - **Before**: `👉 "That was a lot of ground to cover — does everything so far make sense?"`
   - **After**: Use a code block or explicit "Output exactly:" directive showing the full output including the 👉 prefix

3. **Add Paraphrase Constraint**: Add an explicit instruction that if the agent paraphrases the question, the 👉 prefix is still mandatory. This addresses requirement 2.2.

4. **Preserve Surrounding Context**: Keep the 🛑 STOP instruction, acknowledgment handling, clarification handling, and the note about the step not being a mandatory gate exactly as they are.

5. **Maintain Consistency with Other Steps**: Ensure the fix pattern is consistent with how other steps (2, 3a, 3b, 4b) successfully produce the 👉 prefix, reinforcing the pattern rather than introducing a novel format.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Parse the Step 4c section of `onboarding-flow.md` and verify that the instruction format unambiguously requires the 👉 prefix in the output. Run structural analysis on the UNFIXED steering file to confirm the ambiguous pattern exists.

**Test Cases**:
1. **Marker Position Test**: Verify that in the unfixed file, the 👉 marker appears outside the quoted string in Step 4c (will confirm bug condition on unfixed code)
2. **Explicit Instruction Test**: Verify that in the unfixed file, there is no explicit "output must begin with 👉" instruction in Step 4c (will confirm missing enforcement on unfixed code)
3. **Pattern Comparison Test**: Compare Step 4c's marker format with other steps that successfully produce 👉 output (will identify the structural difference)
4. **Paraphrase Constraint Test**: Verify that in the unfixed file, there is no instruction requiring 👉 on paraphrased output (will confirm gap on unfixed code)

**Expected Counterexamples**:
- Step 4c uses `👉 "quoted text"` format where the marker is outside the quotes
- No explicit output format instruction exists for Step 4c
- Possible causes: ambiguous marker placement, missing explicit format directive

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed steering file produces unambiguous instructions requiring the 👉 prefix.

**Pseudocode:**
```
FOR ALL step4c_instruction WHERE isBugCondition(step4c_instruction) DO
  result := parse_fixed_steering_file(step4c_instruction)
  ASSERT result.has_explicit_pointer_requirement == true
  ASSERT result.pointer_inside_output_template == true
  ASSERT result.paraphrase_constraint_present == true
END FOR
```

### Preservation Checking

**Goal**: Verify that for all content outside Step 4c's question formatting, the fixed steering file produces the same instructions as the original.

**Pseudocode:**
```
FOR ALL section WHERE NOT isBugCondition(section) DO
  ASSERT parse_original_file(section) == parse_fixed_file(section)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate many variations of steering file content to verify only Step 4c is changed
- It catches unintended side effects on other steps' 👉 markers
- It provides strong guarantees that non-Step-4c behavior is unchanged

**Test Plan**: Parse both the original and fixed `onboarding-flow.md` files, extract all sections, and verify that only the Step 4c section differs. Verify all other 👉 markers remain in their original positions.

**Test Cases**:
1. **Other Steps Preservation**: Verify that Steps 2, 3a, 3b, 4b, and 5 retain their 👉 markers in the same format after the fix
2. **Informational Content Preservation**: Verify that Step 4 overview content (module table, track descriptions) remains unchanged
3. **Response Handling Preservation**: Verify that acknowledgment and clarification handling instructions remain unchanged
4. **Stop Instructions Preservation**: Verify that 🛑 STOP directives remain in place and unchanged

### Unit Tests

- Test that the fixed Step 4c section contains an explicit output format requirement including 👉
- Test that the 👉 marker appears inside the output template (not as an external annotation)
- Test that a paraphrase constraint is present requiring 👉 on any reformulation
- Test that the Step 4c section still contains the 🛑 STOP instruction
- Test that acknowledgment and clarification handling text is unchanged

### Property-Based Tests

- Generate random steering file section identifiers and verify only Step 4c differs between original and fixed versions
- Generate random question phrasings and verify the instruction format requires 👉 prefix on all of them
- Parse all 👉 occurrences in the fixed file and verify count and positions match expectations (same as original except for the restructured Step 4c marker)

### Integration Tests

- Validate the fixed `onboarding-flow.md` passes CommonMark validation (`validate_commonmark.py`)
- Validate the fixed file's YAML frontmatter is intact and parseable
- Validate the fixed file's token count remains within the budget defined in `steering-index.yaml`
- End-to-end: simulate agent reading the fixed Step 4c and verify the output instruction is unambiguous
