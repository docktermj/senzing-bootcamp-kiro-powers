# Skip Reflection Questions Bugfix Design

## Overview

At module completion, the agent presents a "reflection question" (e.g., "which verification step gave you the most confidence?") before offering next-step options. This adds friction at module transitions — the bootcamper wants to move forward, not engage with a pedagogical prompt. The fix removes the reflection question from the module-completion workflow, removes it from Module 3 step 12, removes it as a completion condition, and omits or auto-fills the "Bootcamper's takeaway" field in journal entries. The fix must preserve all other completion behaviors: journal entries, certificates, next-step options, immediate module startup on "yes", path completion celebration, and the celebration hook.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — the module-completion workflow presents a reflection question and waits for a response before offering next-step options
- **Property (P)**: The desired behavior — module completion skips the reflection question and proceeds directly to the certificate and next-step options
- **Preservation**: Existing journal entry writing, certificate generation, next-step options, immediate module startup, path completion celebration, and celebration hook behavior that must remain unchanged
- **module-completion.md**: The steering file at `senzing-bootcamp/steering/module-completion.md` that defines the standard module completion workflow for all modules
- **module-03-system-verification.md**: The steering file at `senzing-bootcamp/steering/module-03-system-verification.md` that defines Module 3's step-by-step workflow including step 12 (Module Close)
- **module-completion-celebration.kiro.hook**: The hook at `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook` that fires on `postTaskExecution` to display a brief celebration and next-step offer

## Bug Details

### Bug Condition

The bug manifests when any module completes and the agent follows the `module-completion.md` workflow. The workflow includes a "Reflection Question" section that asks the bootcamper about their main takeaway, waits for a response, and appends it to the journal entry before proceeding to the certificate and next-step options. Additionally, Module 3 step 12 explicitly instructs the agent to present a reflection question, and the Module 3 success criteria require the bootcamper to have answered it.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type ModuleCompletionEvent
  OUTPUT: boolean
  
  RETURN input.workflowPhase == "module_completion"
         AND steeringFileContains("module-completion.md", "Reflection Question" section)
         AND (
           agentPresentsReflectionQuestion(input.moduleNumber)
           OR successCriteriaRequiresReflectionAnswer(input.moduleNumber)
           OR journalTemplateWaitsForTakeaway(input.moduleNumber)
         )
END FUNCTION
```

### Examples

- Module 3 completes → agent asks "which verification step gave you the most confidence?" → bootcamper must respond before seeing next-step options (DEFECT: should skip directly to certificate and options)
- Module 1 completes → agent asks "what's your main takeaway?" → bootcamper must respond or explicitly decline before proceeding (DEFECT: should skip directly to certificate and options)
- Module 7 completes (path B/C end) → agent asks reflection question → bootcamper must respond before seeing path completion celebration (DEFECT: should skip directly to certificate, options, and celebration)
- Module 3 re-run → success criteria check fails because "bootcamper has answered the reflection question" is false (DEFECT: this criterion should not exist)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Journal entries must continue to be appended to `docs/bootcamp_journal.md` with module name, completion date, what was done, what was produced, and why it matters
- Module completion certificates must continue to be generated in `docs/progress/MODULE_N_COMPLETE.md`
- Next-step options (Proceed, Iterate, Explore, Undo, Share) must continue to be presented after completion
- When the bootcamper says "yes" to proceed, the next module's startup sequence must execute immediately with zero intermediate steps
- Path completion celebration must continue to fire when the last module in a path completes
- The `module-completion-celebration.kiro.hook` must continue to provide a brief celebration and next-step offer without performing journal entries or certificates
- The celebration hook constraint "Do NOT ask reflection questions" must remain intact

**Scope:**
All inputs that do NOT involve the reflection question presentation or response collection should be completely unaffected by this fix. This includes:
- Journal entry content (minus the takeaway field)
- Certificate generation logic and template
- Next-step option presentation and immediate execution behavior
- Path completion detection and celebration flow
- Hook firing behavior and constraints
- Module progress tracking in `config/bootcamp_progress.json`
- All other steering file workflows

## Hypothesized Root Cause

Based on the bug description, the root causes are explicit instructions in the steering files:

1. **module-completion.md "Reflection Question" section**: The steering file contains a dedicated section instructing the agent to ask the bootcamper about their main takeaway after the journal entry and before the certificate/next-step options. This section also instructs appending the response under "Bootcamper's takeaway" in the journal.

2. **module-completion.md journal template**: The journal entry template includes a `**Bootcamper's takeaway:** [response to reflection question]` field that implies the agent should collect this data.

3. **module-03-system-verification.md step 12 item 3**: Step 12 explicitly says "Reflection question: Present one reflection question to the bootcamper" with a specific example question.

4. **module-03-system-verification.md success criteria**: The success criteria section includes "The bootcamper has answered the reflection question" as a mandatory completion condition.

## Correctness Properties

Property 1: Bug Condition - Reflection Question Skipped at Module Completion

_For any_ module completion event where the agent follows the `module-completion.md` workflow, the fixed steering files SHALL NOT instruct the agent to present a reflection question, SHALL NOT wait for a reflection response, and SHALL proceed directly from the journal entry to the module completion certificate and next-step options.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation - Completion Workflow Integrity

_For any_ module completion event, the fixed steering files SHALL continue to instruct the agent to write a journal entry (with module name, date, what was done, what was produced, why it matters), generate a completion certificate, present next-step options, execute immediate module startup on affirmative response, fire path completion celebration when applicable, and maintain celebration hook behavior — producing the same outcomes as the original files for all non-reflection behaviors.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-completion.md`

**Section**: Reflection Question + Journal Template

**Specific Changes**:
1. **Remove the "Reflection Question" section entirely**: Delete the section that instructs the agent to ask about the bootcamper's main takeaway and append the response to the journal.

2. **Update the journal template**: Remove the `**Bootcamper's takeaway:** [response to reflection question]` line from the journal entry template, or replace it with a static value like `**Bootcamper's takeaway:** N/A`.

3. **Update flow references**: The "Module Completion Certificate" section header says "After the journal entry and reflection" — update to "After the journal entry". Similarly update the "Next-Step Options" section header.

4. **Preserve ordering**: Ensure the flow remains: journal entry → certificate → next-step options (removing the reflection step between journal and certificate).

---

**File**: `senzing-bootcamp/steering/module-03-system-verification.md`

**Section**: Step 12 (Module Close)

**Specific Changes**:
1. **Remove reflection question item**: Delete item 3 from step 12 that says "Reflection question: Present one reflection question to the bootcamper" along with the example question.

2. **Remove from success criteria**: Delete the bullet "The bootcamper has answered the reflection question" from the Success Criteria section.

3. **Renumber if needed**: Ensure step 12 items remain coherent after removing item 3 (items: follow module-completion.md, journal entry, transition to Module 4).

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed steering files, then verify the fix works correctly and preserves existing behavior. Since this is a steering file bug (markdown instructions to an agent), testing focuses on structural validation of the steering file content rather than runtime code execution.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that parse the steering files and assert the presence of reflection question instructions. Run these tests on the UNFIXED files to observe that the bug condition holds (reflection question content exists).

**Test Cases**:
1. **module-completion.md Reflection Section Test**: Assert that `module-completion.md` contains a "## Reflection Question" section (will pass on unfixed code, confirming the bug)
2. **Journal Template Takeaway Field Test**: Assert that the journal template contains "Bootcamper's takeaway" with a placeholder referencing reflection (will pass on unfixed code)
3. **Module 3 Step 12 Reflection Test**: Assert that step 12 contains "Reflection question:" instruction (will pass on unfixed code)
4. **Module 3 Success Criteria Test**: Assert that success criteria contain "answered the reflection question" (will pass on unfixed code)

**Expected Counterexamples**:
- All four tests pass on unfixed code, confirming the reflection question is explicitly instructed in the steering files
- Root cause confirmed: the bug is in the steering file instructions, not in agent behavior diverging from instructions

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed steering files no longer contain reflection question instructions.

**Pseudocode:**
```
FOR ALL steeringFile WHERE isBugCondition(steeringFile) DO
  content := readFile(steeringFile)
  ASSERT NOT containsReflectionQuestionSection(content)
  ASSERT NOT containsReflectionCompletionCondition(content)
  ASSERT journalTemplateOmitsOrAutoFillsTakeaway(content)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all non-reflection content in the steering files, the fixed files produce the same agent instructions as the original files.

**Pseudocode:**
```
FOR ALL steeringFile WHERE NOT isBugCondition(steeringFile) DO
  ASSERT originalContent(steeringFile) = fixedContent(steeringFile)
END FOR

FOR ALL section IN fixedFile WHERE section != "Reflection Question" DO
  ASSERT sectionPreserved(section, originalFile, fixedFile)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate many module completion scenarios and verify the steering file structure supports them
- It catches edge cases where removing the reflection section might accidentally break adjacent content
- It provides strong guarantees that journal entry structure, certificate generation instructions, next-step options, and immediate execution rules remain intact

**Test Plan**: Parse the UNFIXED steering files to capture the structure of preserved sections (journal template fields minus takeaway, certificate template, next-step options, immediate execution rules). Then write property-based tests verifying these structures remain in the fixed files.

**Test Cases**:
1. **Journal Entry Preservation**: Verify the fixed journal template still contains module name, completion date, what was done, what was produced, and why it matters fields
2. **Certificate Generation Preservation**: Verify the certificate section and template remain unchanged in the fixed file
3. **Next-Step Options Preservation**: Verify all five options (Proceed, Iterate, Explore, Undo, Share) remain in the fixed file
4. **Immediate Execution Preservation**: Verify the "⛔ Immediate Execution on Affirmative Response" section and its PROHIBITED list remain unchanged
5. **Path Completion Preservation**: Verify the path completion detection table and celebration section remain unchanged
6. **Celebration Hook Preservation**: Verify the hook file's constraint "Do NOT ask reflection questions" remains (already correct behavior)

### Unit Tests

- Test that `module-completion.md` does not contain a "## Reflection Question" heading after the fix
- Test that `module-completion.md` journal template omits or auto-fills the takeaway field
- Test that `module-03-system-verification.md` step 12 does not contain "Reflection question:" after the fix
- Test that `module-03-system-verification.md` success criteria do not require reflection answer after the fix
- Test that the flow order in `module-completion.md` is: journal → certificate → next-step options (no reflection between)

### Property-Based Tests

- Generate random module numbers (1-11) and verify the completion workflow structure supports them without reflection questions
- Generate random journal entry content and verify the template structure is valid without the takeaway field
- Test that all preserved sections (certificate, next-step, path completion) maintain their structural integrity across many random content variations

### Integration Tests

- Test full module completion flow: verify journal entry is written, certificate is generated, and next-step options are presented without any reflection question step
- Test Module 3 specifically: verify step 12 transitions directly to Module 4 offer without reflection
- Test path completion: verify celebration fires correctly without reflection blocking it
- Test celebration hook: verify it continues to NOT ask reflection questions (existing correct behavior maintained)
