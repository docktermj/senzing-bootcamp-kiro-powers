# Module 2 License Question Bugfix Design

## Overview

Module 2 Step 5 (Configure License) in `senzing-bootcamp/steering/module-02-sdk-setup.md` has an inline question/WAIT structure that causes the agent to short-circuit the license step. When the agent checks for license files and finds none, it skips presenting the bootcamper's license options and immediately defaults to evaluation mode — removing the bootcamper's choice to provide a custom license. The root cause is that Step 5 uses inline questions with WAIT instructions (e.g., "Do you have a Senzing license file or BASE64 key?" WAIT for response), which conflict with the `ask-bootcamper` hook's closing-question ownership. The agent interprets the conditional check-then-ask structure as permission to short-circuit: it checks for licenses, finds none, and jumps straight to evaluation mode without presenting options. The fix restructures Step 5 so the agent always presents license information as content — evaluation limits, how to provide a custom license, where to obtain licenses — and then stops, letting the `ask-bootcamper` hook generate the contextual 👉 question about the bootcamper's license choice.

Note: The `module-closing-question-ownership` spec addresses WAITs across all module files, but this spec specifically fixes Step 5's content structure to ensure the agent always presents license options regardless of what it finds.

## Glossary

- **Bug_Condition (C)**: Step 5 of `module-02-sdk-setup.md` contains inline questions with WAIT instructions and a conditional structure that allows the agent to skip presenting license options when no license file is found
- **Property (P)**: Step 5 always presents license information as content (evaluation limits, custom license instructions, license acquisition details) regardless of whether a license file is found, and stops without an inline closing question
- **Preservation**: License check priority order, BASE64 decode instructions, engine config PIPELINE setup, preference recording, other Module 2 steps (1–4, 6–9), and the `ask-bootcamper` hook's closing-question behavior remain unchanged
- **`module-02-sdk-setup.md`**: The steering file at `senzing-bootcamp/steering/module-02-sdk-setup.md` that defines the Module 2 (SDK Installation and Configuration) step-by-step flow
- **`ask-bootcamper` hook**: The `agentStop` hook at `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` that recaps accomplishments and asks a contextual 👉 closing question
- **Step 5 (Configure License)**: The license configuration step that checks for existing licenses and presents options to the bootcamper
- **Evaluation license**: The built-in Senzing license with a 500-record limit, used when no custom license is provided

## Bug Details

### Bug Condition

The bug manifests when the agent executes Module 2 Step 5 and encounters the conditional check-then-ask structure. The current Step 5 instructs the agent to check three license locations, then conditionally ask different inline questions depending on what it finds. When no license is found, the agent short-circuits by defaulting to evaluation mode without presenting the bootcamper's options — because the inline question format is ambiguous about whether the agent or the hook should ask, and the conditional structure gives the agent an easy path to skip the question entirely.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input of type SteeringFileStep (Step 5 of module-02-sdk-setup.md)
  OUTPUT: boolean

  RETURN input.content CONTAINS inline question with WAIT instruction
         AND input.content USES conditional structure (if found/if not found)
         AND input.content ALLOWS agent to skip presenting license options
         AND ask-bootcamper hook IS active on agentStop
END FUNCTION
```

### Examples

- **No license found path (current)**: Agent checks `licenses/g2.lic`, `SENZING_LICENSE_PATH`, and system CONFIGPATH → finds nothing → steering file says `ask: "Do you have a Senzing license file or BASE64 key? If not, the SDK works with evaluation limits (500 records)." WAIT for response` → agent interprets the conditional check as "no license means evaluation" and skips the question entirely, defaulting to evaluation mode
- **License found path (current)**: Agent finds a license at one of the three locations → steering file says `confirm: "I found a license at [location]. Use this one?" WAIT for response` → agent either asks the inline question (violating hook ownership) or skips it and assumes yes
- **Expected behavior (no license)**: Agent checks all three locations → finds nothing → presents informational content: "No license file found. Here are your options: (1) evaluation license with 500-record limit, (2) provide a custom license file or BASE64 key, (3) how to obtain a license" → stops → hook generates 👉 question
- **Expected behavior (license found)**: Agent checks locations → finds license → presents: "Found a license at [location]" with details → stops → hook generates 👉 question

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The agent continues to check for licenses in the documented priority order: project-local `licenses/g2.lic` → `SENZING_LICENSE_PATH` env var → system CONFIGPATH → built-in evaluation
- When the bootcamper provides a BASE64 license key, the agent continues to direct them to decode it to `licenses/g2.lic` using the documented command, and never asks the user to paste a license key into chat
- When a project-local license exists, the agent continues to add `LICENSEFILE` to the engine config PIPELINE section and record `license: custom` in `config/bootcamp_preferences.yaml`
- When the bootcamper chooses the evaluation license, the agent continues to record `license: evaluation` in `config/bootcamp_preferences.yaml`
- The `ask-bootcamper` hook continues to fire after the agent completes Step 5 and generate a contextual 👉 question based on the license information presented
- All other Module 2 steps (Steps 1–4, 6–9) remain unchanged — the fix is scoped to Step 5 only

**Scope:**
All content outside of Step 5's inline questions, WAIT instructions, and conditional ask structure is completely unaffected by this fix. This includes:
- The license check priority order logic
- The BASE64 decode command and "never paste into chat" warning
- The engine config PIPELINE `LICENSEFILE` setup
- The `config/bootcamp_preferences.yaml` recording
- License acquisition contact information
- The checkpoint write at the end of Step 5
- All other Module 2 steps

## Hypothesized Root Cause

Based on the bug description and two separate feedback reports, the most likely issues are:

1. **Conditional check-then-ask structure enables short-circuiting**: Step 5 says "Check all three locations before asking the user. If found, confirm... If no license found, ask..." This conditional structure gives the agent a decision tree where it can skip the question. When no license is found, the agent treats the absence as a decision point and defaults to evaluation mode rather than presenting options.

2. **Inline questions with WAIT conflict with hook ownership**: The `agent-instructions.md` rule states the `ask-bootcamper` hook owns all closing questions. But Step 5 contains explicit inline questions ("Do you have a Senzing license file or BASE64 key?") with WAIT instructions. The agent cannot reliably resolve this conflict — it either asks the question itself (violating hook ownership) or skips it entirely (the observed bug).

3. **Information is gated behind questions rather than presented as content**: The current Step 5 treats license information as something to ask about rather than something to present. The evaluation limits (500 records), custom license instructions, and acquisition details are embedded in the question text rather than presented as standalone informational content. This means if the agent skips the question, it also skips the information.

4. **Two feedback reports confirm the pattern**: Two separate bootcampers reported that the agent checked for licenses, found none, and immediately proceeded with evaluation mode without presenting their options — confirming this is a reproducible behavioral pattern, not a one-off.

## Correctness Properties

Property 1: Bug Condition - Step 5 always presents license information as content

_For any_ execution of Module 2 Step 5, the steering file SHALL instruct the agent to always present license information as content — including evaluation license limits (500 records), how to provide a custom license file or BASE64 key, and where to obtain licenses — regardless of whether a license file is found, and SHALL NOT contain inline closing questions or WAIT-for-response instructions that allow the agent to skip presenting this information.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - License mechanics, other steps, and hook behavior unchanged

_For any_ content in `module-02-sdk-setup.md` that is not Step 5's inline questions, WAIT instructions, or conditional ask structure (license check priority order, BASE64 decode instructions, engine config PIPELINE setup, preference recording, checkpoint logic, all other steps 1–4 and 6–9), the fixed steering file SHALL preserve that content unchanged. The `ask-bootcamper` hook SHALL continue to fire on `agentStop` and generate contextual 👉 questions.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-02-sdk-setup.md`

**Section**: `## Step 5: Configure License`

**Specific Changes**:

1. **Keep the license check priority order**: Retain the opening sentence about Senzing's license check order (project-local → env var → system CONFIGPATH → built-in evaluation). This is informational content, not a question.

2. **Restructure the "license found" path as informational content**: Instead of "If found, confirm: 'I found a license at [location]. Use this one?' WAIT for response", instruct the agent to present the finding as information: tell the bootcamper where the license was found and what it means.

3. **Restructure the "no license found" path as informational content**: Instead of "If no license found, ask: 'Do you have a Senzing license file or BASE64 key?' WAIT for response", instruct the agent to always present the license options as content:
   - Evaluation license: works with 500-record limit, no file needed
   - Custom license: how to provide a license file or decode a BASE64 key to `licenses/g2.lic`
   - License acquisition: evaluation → support@senzing.com, production → sales@senzing.com

4. **Remove all inline questions and WAIT instructions from Step 5**: Remove "WAIT for response" instructions and inline question text. The `ask-bootcamper` hook will generate the contextual 👉 question.

5. **Keep all mechanical instructions unchanged**: The BASE64 decode command, "never paste into chat" warning, engine config PIPELINE `LICENSEFILE` setup, `config/bootcamp_preferences.yaml` recording, license acquisition contacts, and checkpoint write all remain exactly as-is.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Since this is a steering file (natural language instructions for an LLM), testing focuses on structural analysis of file content.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that Step 5 contains inline questions with WAIT instructions and a conditional structure that allows skipping license information.

**Test Plan**: Parse `senzing-bootcamp/steering/module-02-sdk-setup.md`, extract the Step 5 section, and check for inline questions, WAIT instructions, and conditional ask patterns. Run these tests on the UNFIXED code to confirm the bug condition exists.

**Test Cases**:
1. **Step 5 contains WAIT instructions**: Parse Step 5 and assert it does NOT contain `WAIT for response` (will fail on unfixed code because WAITs ARE present)
2. **Step 5 contains inline questions**: Parse Step 5 and assert it does NOT contain inline question patterns like "Do you have" or "Use this one?" (will fail on unfixed code)
3. **Step 5 always presents license info**: Assert Step 5 contains unconditional instructions to present evaluation limits, custom license options, and acquisition details (will fail on unfixed code because info is gated behind conditional questions)

**Expected Counterexamples**:
- Step 5 contains `WAIT for response` after both the "license found" and "no license found" paths
- License information is embedded in question text rather than presented as standalone content
- The conditional structure ("If found... If no license found...") gates information behind questions

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed step always presents license information as content without inline questions or WAITs.

**Pseudocode:**

```
FOR step5 WHERE isBugCondition(step5) DO
  fixed_content := extractSection(fixed_file, "## Step 5: Configure License")
  ASSERT NOT containsWaitInstruction(fixed_content)
  ASSERT NOT containsInlineClosingQuestion(fixed_content)
  ASSERT containsEvaluationLimitInfo(fixed_content)
  ASSERT containsCustomLicenseInstructions(fixed_content)
  ASSERT containsLicenseAcquisitionInfo(fixed_content)
END FOR
```

### Preservation Checking

**Goal**: Verify that all content outside Step 5's inline questions and WAIT instructions is preserved unchanged.

**Pseudocode:**

```
FOR ALL content WHERE NOT isBugCondition(content) DO
  ASSERT original_file(content) = fixed_file(content)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can verify that all non-question content in Step 5 is preserved
- It catches edge cases where adjacent content might be accidentally removed
- It provides strong guarantees that other steps and mechanical instructions are unchanged

**Test Plan**: Observe the full content of `module-02-sdk-setup.md` on UNFIXED code. Extract the license check priority order, BASE64 decode instructions, engine config setup, preference recording, checkpoint logic, and all other steps. Write tests asserting these are preserved after the fix.

**Test Cases**:
1. **License check order preserved**: Verify Step 5 still describes the priority order (project-local → env var → system CONFIGPATH → built-in evaluation)
2. **BASE64 decode preserved**: Verify Step 5 still contains the `base64 --decode > licenses/g2.lic` command
3. **Never-paste warning preserved**: Verify Step 5 still contains "NEVER ask the user to paste a license key into chat"
4. **Engine config PIPELINE preserved**: Verify Step 5 still contains the `LICENSEFILE` PIPELINE configuration
5. **Preference recording preserved**: Verify Step 5 still contains `license: custom` and `license: evaluation` recording instructions
6. **License contacts preserved**: Verify Step 5 still contains support@senzing.com and sales@senzing.com
7. **Checkpoint preserved**: Verify Step 5 still contains the checkpoint write instruction
8. **Other steps unchanged**: Verify Steps 1–4 and 6–9 are identical between unfixed and fixed versions

### Unit Tests

- Parse Step 5 and assert no WAIT instructions exist
- Parse Step 5 and assert no inline closing questions exist
- Parse Step 5 and assert license information is presented as unconditional content
- Parse Step 5 and assert evaluation limits (500 records) are mentioned as content
- Verify other steps (1–4, 6–9) are unchanged

### Property-Based Tests

- Generate random section selections from the file and verify non-Step-5-question content is preserved between unfixed and fixed versions
- Verify that Step 5 in the fixed file contains all required informational elements (evaluation limits, custom license path, acquisition contacts)
- Test that all step headings and their ordering are preserved

### Integration Tests

- Verify the full file parses as valid markdown after the fix
- Verify Step 5 presents a complete information flow: check results → license options → mechanical instructions → checkpoint
- Verify the `ask-bootcamper` hook can generate an appropriate contextual question based on the information Step 5 presents
