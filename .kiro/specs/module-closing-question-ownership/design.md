# Module Closing Question Ownership Bugfix Design

## Overview

The module steering files (module-01 through module-12, plus module-completion.md and module-07-reference.md) contain inline 👉 closing questions with WAIT instructions that conflict with the `ask-bootcamper` hook's role as the single owner of closing questions. This is the same architectural conflict that was already fixed in `onboarding-flow.md` (see `.kiro/specs/missing-pointing-prefix/`). The `agent-instructions.md` rule states: "Never end your turn with a closing question — the `ask-bootcamper` hook owns all closing questions." However, module steering files instruct the agent to ask inline 👉 questions and then WAIT for a response, causing the agent to place closing questions at the end of its output — violating the ownership rule. During Module 1, the bootcamper had to correct this behavior at least 6 times, and the agent repeated the mistake even after acknowledging it because the steering file instructions directly contradicted the hook ownership rule. The fix removes all inline 👉 closing questions and WAIT-for-response instructions from every module steering file, letting the `ask-bootcamper` hook be the sole source of closing questions — consistent with the existing ownership rule in `agent-instructions.md`.

## Glossary

- **Bug_Condition (C)**: A module steering file that contains inline 👉 closing questions and/or WAIT-for-response instructions, creating a question-ownership conflict with the `ask-bootcamper` hook
- **Property (P)**: Module steering files present information and stop cleanly without inline closing questions or WAITs, allowing the `ask-bootcamper` hook to generate the single contextual 👉 closing question
- **Preservation**: The `ask-bootcamper` hook continues to fire on `agentStop` and generate contextual 👉 questions; module step sequences remain unchanged; `agent-instructions.md` ownership rule remains in place; informational content (explanations, tables, code, MCP instructions, checkpoint logic) remains unchanged
- **Module steering files**: The files at `senzing-bootcamp/steering/module-*.md` plus `module-completion.md` and `module-07-reference.md` that define the step-by-step flow for each bootcamp module
- **`ask-bootcamper` hook**: The `agentStop` hook at `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` that recaps accomplishments and asks a contextual 👉 closing question
- **Closing question**: A question placed at the end of the agent's output that requires user input before proceeding — owned exclusively by the `ask-bootcamper` hook
- **WAIT instruction**: A directive in a steering file telling the agent to stop and wait for user input before continuing (e.g., `WAIT for response`, `WAIT for confirmation`, `WAIT for response before proceeding`)

## Bug Details

### Bug Condition

The bug manifests when the agent executes any module step that ends with an inline 👉 closing question and/or a WAIT instruction. The steering file instructs the agent to ask the question itself and wait, which conflicts with the `ask-bootcamper` hook's role as the single owner of closing questions. The agent either paraphrases the inline question (dropping the 👉 prefix), outputs the inline question and then the hook appends a second 👉 question, or the agent ignores the `agent-instructions.md` ownership rule because the steering file explicitly tells it to ask.

**Formal Specification:**

```
FUNCTION isBugCondition(file)
  INPUT: file of type SteeringFile (a module steering .md file)
  OUTPUT: boolean

  RETURN file.content CONTAINS inline 👉 closing question
         OR file.content CONTAINS WAIT-for-response instruction
         AND ask-bootcamper hook IS active on agentStop
END FUNCTION
```

### Affected Files and Instances

| File | Inline 👉 Questions | WAIT Instructions |
|------|---------------------|-------------------|
| `module-01-business-problem.md` | 0 | 4 (`WAIT for response` ×3, `WAIT for confirmation` ×1) |
| `module-02-sdk-setup.md` | 0 | 4 (`WAIT for response` ×3, `WAIT for response before proceeding` ×1) |
| `module-04-data-collection.md` | 0 | 1 (`WAIT for their response`) |
| `module-05-data-quality-mapping.md` | 0 | 4 (`WAIT for response before proceeding` ×1, `WAIT for confirmation` ×2, `WAIT for response` ×1) |
| `module-06-single-source.md` | 1 (`👉 **Ask the bootcamper:**`) | 1 (`⚠️ WAIT — Do NOT proceed`) |
| `module-07-multi-source.md` | 7 (inline `👉` questions) | 7 (`WAIT for response` after each) |
| `module-07-reference.md` | 2 (`👉` questions) | 1 (`WAIT for response`) |
| `module-08-query-validation.md` | 4 (`👉` questions) | 4 (`WAIT` instructions) |
| `module-12-deployment.md` | 1 (`👉` question) | 3 (`WAIT for response`, `WAIT for each`, `MANDATORY STOP`) |
| `module-completion.md` | 3 (`👉` questions) | 2 (`WAIT for response` ×2) |
| `module-03-quick-demo.md` | 0 | 0 (not affected) |
| `module-09-performance.md` | 0 | 0 (not affected) |
| `module-10-security.md` | 0 | 0 (not affected) |
| `module-11-monitoring.md` | 0 | 0 (not affected) |

### Examples

- **Module 01, Step 1**: Ends with `"Would you like me to initialize a git repository?"` followed by `WAIT for response.` — the hook will also fire and may generate a second question, or the agent places the closing question itself violating the ownership rule
- **Module 07, Step 2**: Ends with `👉 "Here are all the data sources from your project. Are there any sources missing, or any changes to this list?" WAIT for response.` — explicit 👉 closing question with WAIT, directly competing with the hook
- **Module 08, Step 4**: Contains `👉 **Ask the bootcamper:** "Would you like me to help you build an interactive entity graph?"` with `⚠️ WAIT — Do NOT proceed until the bootcamper responds.` — mandatory visualization offer with inline question
- **Module Completion**: Ends with `"👉 What would you like to do?" WAIT for response.` — inline closing question at the end of the completion workflow
- **Module 03, 09, 10, 11**: These modules do NOT contain inline 👉 questions or WAIT instructions — they are not affected by the bug

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The `ask-bootcamper` hook continues to fire on every `agentStop` and generate contextual 👉 closing questions based on what the agent just accomplished
- The `ask-bootcamper` hook file (`senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`) is not modified
- The `agent-instructions.md` file is not modified
- Informational content within module steps (explanations, tables, code examples, MCP query instructions, checkpoint logic, decision gates, visualization descriptions) remains unchanged
- Module step sequences, numbering, and checkpoint logic remain the same
- The already-fixed `onboarding-flow.md` is not modified (regression prevention)
- Mandatory visualization offers (modules 06, 07, 08) retain their informational descriptions — only the inline 👉 question and WAIT instruction are removed
- Phase gates (e.g., module-12 packaging gate) retain their stop-and-present behavior — only the WAIT instruction phrasing is adjusted to not conflict with hook ownership

**Scope:**
All module steering files that do NOT currently have inline 👉 closing questions or WAIT instructions (modules 03, 09, 10, 11) are completely unaffected by this fix. The fix only touches the trailing question/WAIT patterns. The informational content within affected steps (MCP instructions, checkpoint writes, decision logic, visualization descriptions) remains unchanged.

## Hypothesized Root Cause

Based on the bug analysis, the root cause is the same architectural contradiction found in `onboarding-flow.md`:

1. **Dual-source closing questions**: Module steering files were written with inline 👉 closing questions and WAIT instructions before the `ask-bootcamper` hook existed (or before the closing-question ownership rule was established). The hook was added later as the canonical source of closing questions, but the module steering files were never updated to remove their inline questions.

2. **WAIT instructions override the ownership rule**: When a steering file says `WAIT for response`, the agent interprets this as "I must ask the question and stop." This is a stronger signal than the `agent-instructions.md` rule saying "Never end your turn with a closing question." The steering file instruction wins because it is loaded in the immediate context of the current step, while the ownership rule is a general instruction.

3. **Repeated violations despite correction**: The bootcamper corrected the agent at least 6 times during Module 1, but the agent repeated the mistake because the steering file instruction was re-loaded on each step. The agent's acknowledgment of the rule was overridden by the explicit `WAIT for response` instruction in the next step.

4. **Unreliable prompt-based suppression**: The hook's suppression logic ("If your previous output already ends with a 👉 question, do nothing") relies on the LLM correctly detecting an existing trailing 👉 question. This is a soft prompt instruction, not a deterministic check — LLMs do not reliably follow suppression paths.

## Correctness Properties

Property 1: Bug Condition - Module steering files have inline closing questions and WAITs removed

_For any_ module steering file that previously contained an inline 👉 closing question or WAIT-for-response instruction, the fixed steering file SHALL NOT contain that inline closing question or WAIT instruction; the step SHALL present its informational content and end without a closing question or WAIT, allowing the `ask-bootcamper` hook to be the sole source of the closing 👉 question.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Non-question content, hook, and agent-instructions unchanged

_For any_ content in module steering files that is not an inline closing 👉 question or WAIT-for-response instruction (informational content, MCP instructions, checkpoint logic, decision gates, visualization descriptions, tables, code examples), the fixed steering files SHALL preserve that content unchanged. The `ask-bootcamper` hook SHALL continue to fire on `agentStop` and generate contextual 👉 questions, and `agent-instructions.md` SHALL remain unmodified.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**Files**: All module steering files in `senzing-bootcamp/steering/` that contain inline 👉 closing questions or WAIT instructions.

**Specific Changes per File**:

1. **`module-01-business-problem.md`**: Remove 4 WAIT instructions (`WAIT for response` ×3, `WAIT for confirmation` ×1). Keep all informational content, questions presented as information, and checkpoint logic.

2. **`module-02-sdk-setup.md`**: Remove 4 WAIT instructions (`WAIT for response` ×3, `WAIT for response before proceeding` ×1). Keep platform question, license check logic, database question, and all MCP instructions.

3. **`module-04-data-collection.md`**: Remove 1 WAIT instruction (`WAIT for their response`). Keep data source options and all informational content.

4. **`module-05-data-quality-mapping.md`**: Remove 4 WAIT instructions (`WAIT for response before proceeding` ×1, `WAIT for confirmation` ×2, `WAIT for response` ×1). Keep quality scoring logic, mapping workflow instructions, and all MCP state management.

5. **`module-06-single-source.md`**: Remove 1 inline 👉 question (`👉 **Ask the bootcamper:**`) and 1 WAIT instruction (`⚠️ WAIT — Do NOT proceed`). Keep the mandatory visualization offer description and DO NOT SKIP instruction — rephrase to present the offer as information without an inline closing question.

6. **`module-07-multi-source.md`**: Remove 7 inline 👉 questions and 7 WAIT instructions. Keep all step content: data source enumeration, dependency analysis, ordering heuristics, loading strategy descriptions, orchestrator testing, visualization descriptions, UAT instructions, and dashboard offer.

7. **`module-07-reference.md`**: Remove 2 inline 👉 questions and 1 WAIT instruction. Keep ordering examples, conflict resolution guidance, error handling options, and troubleshooting reference.

8. **`module-08-query-validation.md`**: Remove 4 inline 👉 questions and 4 WAIT instructions. Keep mandatory visualization offer descriptions, integration pattern descriptions, and all MCP instructions. Rephrase DO NOT SKIP blocks to present offers as information.

9. **`module-12-deployment.md`**: Remove 1 inline 👉 question and 3 WAIT instructions. Keep deployment target logic, phase gate description, DR guidance, and stakeholder summary offer.

10. **`module-completion.md`**: Remove 3 inline 👉 questions and 2 WAIT instructions. Keep journal template, reflection question description, next-step options list, path completion detection, graduation offer flow, and celebration content. Rephrase the reflection question and next-step options to present as information rather than inline closing questions.

**No changes to these files**:
- `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` — already the canonical question owner
- `senzing-bootcamp/steering/agent-instructions.md` — already has the ownership rule
- `senzing-bootcamp/steering/onboarding-flow.md` — already fixed in `.kiro/specs/missing-pointing-prefix/`
- `module-03-quick-demo.md`, `module-09-performance.md`, `module-10-security.md`, `module-11-monitoring.md` — no inline questions or WAITs

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Since these are steering files (natural language instructions for an LLM), testing focuses on structural analysis of file content rather than runtime execution.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that module steering files contain inline 👉 closing questions and/or WAIT instructions.

**Test Plan**: Parse each affected module steering file and check for the presence of inline 👉 closing questions and WAIT-for-response instructions. Run these tests on the UNFIXED files to confirm the bug condition exists.

**Test Cases**:
1. **Module 01 WAITs**: Verify module-01 contains `WAIT for response` instructions (will find matches on unfixed code)
2. **Module 02 WAITs**: Verify module-02 contains `WAIT for response` instructions (will find matches on unfixed code)
3. **Module 07 inline questions**: Verify module-07 contains inline `👉` questions with `WAIT for response` (will find matches on unfixed code)
4. **Module 08 inline questions**: Verify module-08 contains `👉 **Ask the bootcamper:**` with `WAIT` (will find matches on unfixed code)
5. **Module completion inline questions**: Verify module-completion contains `👉` questions with `WAIT for response` (will find matches on unfixed code)

**Expected Counterexamples**:
- Each affected file contains at least one inline 👉 closing question or WAIT instruction
- The pattern is consistent: question text followed by WAIT instruction
- Modules 03, 09, 10, 11 are clean (no matches expected)

### Fix Checking

**Goal**: Verify that for all module steering files where the bug condition holds, the fixed files no longer contain inline closing questions or WAIT instructions.

**Pseudocode:**

```
FOR ALL file WHERE isBugCondition(file) DO
  fixed_content := read_file(file)
  ASSERT NOT contains_inline_closing_question(fixed_content)
  ASSERT NOT contains_wait_instruction(fixed_content)
  ASSERT contains_informational_content(fixed_content)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all content where the bug condition does NOT hold, the fixed files preserve that content unchanged.

**Pseudocode:**

```
FOR ALL content WHERE NOT isBugCondition(content) DO
  ASSERT original_file(content) = fixed_file(content)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate random file/section selections and verify non-question content is preserved
- It catches edge cases where informational content might be accidentally removed
- It provides strong guarantees that step sequences, checkpoint logic, and MCP instructions are unchanged

**Test Plan**: Parse both the unfixed and fixed versions of each affected module steering file. For each section, extract the informational content (excluding inline closing questions and WAIT instructions) and verify it is preserved in the fixed version.

**Test Cases**:
1. **Step sequence preservation**: Verify each fixed file contains the same step headings in the same order
2. **Informational content preservation**: Verify MCP instructions, checkpoint writes, decision logic, visualization descriptions, tables, and code examples are unchanged
3. **Unaffected files preservation**: Verify modules 03, 09, 10, 11 are completely unchanged
4. **Hook file preservation**: Verify `ask-bootcamper.kiro.hook` is not modified
5. **Agent instructions preservation**: Verify `agent-instructions.md` is not modified
6. **Onboarding flow preservation**: Verify `onboarding-flow.md` is not modified (regression check)

### Unit Tests

- Parse each affected file and assert no inline 👉 closing questions exist
- Parse each affected file and assert no WAIT-for-response instructions exist
- Parse each affected file and assert informational content is preserved
- Verify mandatory visualization offers retain their descriptions without inline questions

### Property-Based Tests

- Generate random file selections from the affected set and verify none contain inline 👉 closing questions followed by WAIT instructions
- Generate random content sections and verify non-question content matches between unfixed and fixed versions
- Test that all step headings and their ordering are preserved across many random section samples

### Integration Tests

- Simulate module execution with fixed steering files and verify the agent presents information without inline closing questions
- Verify the `ask-bootcamper` hook generates appropriate contextual 👉 questions after each module step
- Verify no duplicate questions appear when the hook fires after a step that previously had an inline question
