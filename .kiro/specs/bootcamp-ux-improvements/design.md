# Bootcamp UX Improvements Bugfix Design

## Overview

Three steering-file bugs degrade the Senzing Bootcamp experience: (1) the agent skips the post-Module 1 visualization offer because `module-01-quick-demo.md` places it mid-phase but the completion flow jumps straight to `module-completion.md`, (2) module starts lack the bold banner treatment that onboarding uses for its welcome message, and (3) the journey map rendered at module start is not enforced as a markdown table. All three fixes are text changes to steering markdown files — no code logic changes.

## Glossary

- **Bug_Condition (C)**: The set of agent states where the steering instructions produce incorrect UX — missing visualization prompt, missing banner, or non-tabular journey map
- **Property (P)**: The desired agent behavior — visualization offered before journal, bold banner at module start, tabular journey map
- **Preservation**: Existing behaviors that must remain unchanged — onboarding welcome banner, module-completion journal/reflection/next-step flow, step-level progress updates, Module 1→2 transition sequence
- **Steering file**: A markdown instruction file loaded by the AI agent at runtime to control bootcamp workflow behavior
- **module-transitions.md**: Auto-included steering file controlling journey map display and before/after framing at module start
- **module-01-quick-demo.md**: Manually loaded steering file for Module 1 execution, including demo phases and completion
- **module-completion.md**: Manually loaded steering file for post-module journal entries, reflection, and next-step options

## Bug Details

### Bug Condition

The bugs manifest in three related scenarios during module lifecycle events. The steering files either omit instructions, lack formatting enforcement, or order steps incorrectly, causing the agent to skip or under-deliver UX elements.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input of type AgentSteeringEvent
  OUTPUT: boolean

  // Bug 1: Module 1 completion skips visualization offer
  IF input.event = "module_completion" AND input.module = 1
    RETURN true  // Agent jumps to module-completion.md without offering visualization

  // Bug 2: Module start lacks bold banner
  IF input.event = "module_start"
    RETURN true  // No banner instruction exists in module-transitions.md

  // Bug 3: Journey map not tabular
  IF input.event = "module_start" AND input.showsJourneyMap = true
    RETURN true  // module-transitions.md says "compact journey map" but doesn't enforce table format

  RETURN false
END FUNCTION
```

### Examples

- **Bug 1**: User completes Module 1 demo. Agent says "That's Module 1 complete!" and immediately starts the journal entry. The "Would you like me to create a web page?" prompt from Phase 2 Step 4 is never shown because Step 5 tells the agent to "Close Module 1 explicitly" and "Follow the module-completion.md workflow" — the visualization offer in Step 4 gets lost in the transition.
- **Bug 2**: User finishes Module 1 and starts Module 2. Agent says "Starting Module 2: Discover the Business Problem" in plain text. Compare to onboarding, which shows a bold `━━━ 🎓🎓🎓 WELCOME TO THE SENZING BOOTCAMP! 🎓🎓🎓 ━━━` banner.
- **Bug 3**: Agent shows the journey map as a bullet list: "✅ Module 0: SDK Setup, → Module 2: Business Problem, Module 3: Data Collection..." instead of a structured table with Module, Name, Status columns.
- **Edge case**: Module 1 user declines visualization — agent should still proceed to module-completion.md normally. The fix only ensures the offer is made, not that the user accepts.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The onboarding welcome banner in `onboarding-flow.md` must continue to use 🎓 emojis and "WELCOME TO THE SENZING BOOTCAMP!" text exactly as-is
- The `module-completion.md` journal entry, reflection question, and next-step options workflow must continue to execute in its current order
- Step-level Before/During/After progress updates in `module-transitions.md` must remain unchanged
- Module 1's explicit close statement, purpose summary, and Module 2 transition with use-case discovery questions (Steps 5-6) must remain intact
- Modules other than Module 1 must not receive Module-1-specific visualization prompts in their next-step options

**Scope:**
All steering file content not directly related to the three bug conditions should be completely unaffected. This includes:
- All module-specific steering file content (phase instructions, agent rules, prerequisites)
- The module-completion.md journal template format
- Path completion detection and celebration in module-completion.md
- Validation gates in onboarding-flow.md

## Hypothesized Root Cause

Based on analysis of the steering files, the root causes are:

1. **Ordering issue in module-01-quick-demo.md**: Step 4 contains the visualization offer, but Step 5 says "Close Module 1 explicitly" and "Follow the module-completion.md workflow." The agent interprets Step 5 as the immediate next action after the demo results explanation, skipping the visualization offer embedded in Step 4. The visualization offer needs to be a clearly sequenced step that happens BEFORE the module close.

2. **Missing banner instruction in module-transitions.md**: The "Journey Map" and "Before/After Framing" sections tell the agent what content to show at module start, but never instruct it to display a bold visual banner. The onboarding flow has an explicit banner template — module-transitions.md has nothing equivalent.

3. **Vague journey map format in module-transitions.md**: The instruction says "Show a compact journey map" but doesn't specify the format. Without an explicit table template, the agent defaults to whatever format it chooses (usually bullet lists). The fix needs an explicit markdown table template with column definitions.

4. **Vague "Explore" option in module-completion.md**: The generic "Would you like to dig deeper into what we just did?" doesn't mention visualization or interactive exploration, so even if the agent reaches this point, the user doesn't know these options exist.

## Correctness Properties

Property 1: Bug Condition - Post-Module 1 Visualization Prompt

_For any_ Module 1 completion event, the fixed steering instructions SHALL cause the agent to offer visualization ("Would you like me to create a web page showing these results?") with interactive feature options BEFORE entering the module-completion.md journal/reflection workflow.

**Validates: Requirements 2.1, 2.2**

Property 2: Bug Condition - Bold Module Start Banners

_For any_ module start event, the fixed steering instructions SHALL cause the agent to display a prominent visual banner using the format `━━━ 🚀🚀🚀 MODULE N: [NAME IN CAPS] 🚀🚀🚀 ━━━` before showing the journey map and before/after framing.

**Validates: Requirements 2.3**

Property 3: Bug Condition - Tabular Journey Map

_For any_ module start event where the journey map is displayed, the fixed steering instructions SHALL cause the agent to render the journey map as a markdown table with Module, Name, and Status columns, using ✅ for completed, 🔄 for current (with → prefix), and ⬜ for upcoming modules.

**Validates: Requirements 2.4**

Property 4: Preservation - Onboarding Welcome Banner Unchanged

_For any_ onboarding flow execution, the fixed steering files SHALL produce the same welcome banner with 🎓 emojis and "WELCOME TO THE SENZING BOOTCAMP!" text, preserving the existing onboarding experience.

**Validates: Requirements 3.1**

Property 5: Preservation - Module Completion Workflow Unchanged

_For any_ module completion event, the fixed steering files SHALL continue to execute the journal entry, reflection question, and next-step options in the same order and format as the original module-completion.md, preserving the post-module workflow.

**Validates: Requirements 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

**File 1**: `senzing-bootcamp/steering/module-01-quick-demo.md`

**Changes**:
1. **Reorder Phase 2 steps to make visualization offer explicit and sequenced**: Currently Step 4 contains both "Explain results" and "Offer visualization" as a sub-point. Step 5 then says "Close Module 1 explicitly" and jumps to module-completion.md. Split the visualization offer into its own numbered step (new Step 5) so the sequence becomes: Step 4 (Explain results) → Step 5 (Offer visualization) → Step 6 (Close Module 1) → Step 7 (Transition to Module 2). This makes the visualization offer impossible to skip.

2. **Add explicit instruction that visualization must happen before module close**: Add a note in the new Step 5 stating: "This step MUST complete before closing the module. Do not skip to module-completion.md until the user has responded to the visualization offer."

---

**File 2**: `senzing-bootcamp/steering/module-transitions.md`

**Changes**:
1. **Add Module Start Banner section**: Insert a new section before "Journey Map" called "Module Start Banner" with an explicit banner template:
   ```text
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🚀🚀🚀  MODULE N: [MODULE NAME IN CAPS]  🚀🚀🚀
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```
   Include instruction: "Display this banner at the start of every module. This is the module equivalent of the onboarding welcome banner."

2. **Replace journey map prose with explicit table template**: Replace the current "Show a compact journey map" instruction with an explicit markdown table template:
   ```markdown
   | Module | Name | Status |
   |--------|------|--------|
   | 0 | SDK Setup | ✅ |
   | → 2 | Business Problem | 🔄 |
   | 3 | Data Collection | ⬜ |
   ```
   Include instruction: "MUST use this exact table format. Use ✅ for completed, 🔄 for current (prefix module number with →), ⬜ for upcoming. Only show modules in the user's selected path."

3. **Reorder the section sequence**: The display order at module start should be: (1) Banner, (2) Journey Map table, (3) Before/After Framing. Update section ordering to reflect this.

---

**File 3**: `senzing-bootcamp/steering/module-completion.md`

**Changes**:
1. **Enhance the "Explore" option with concrete examples**: Change the generic "Would you like to dig deeper into what we just did?" to include module-aware concrete options. Add a note that for Module 1 specifically, the Explore option should mention visualization: "Would you like to explore further — visualize entities, examine match explanations, or search by attributes?" For other modules, keep the Explore option contextual to what was produced.

2. **Add a Module 1 note in the Next-Step Options section**: Add a callout: "**Module 1 special case:** The visualization offer (web page with interactive features) should already have been presented before reaching this workflow. If the user declined, the Explore option below gives them another chance."

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, verify the bug exists by reading the current steering files and confirming the missing/incorrect instructions, then verify the fix by reading the updated files and confirming the instructions are present and correctly formatted. Since these are markdown instruction files (not executable code), testing is done through content inspection rather than runtime execution.

### Exploratory Bug Condition Checking

**Goal**: Confirm the three bugs exist in the current steering files before making changes.

**Test Plan**: Read each steering file and verify the absence of the required instructions.

**Test Cases**:
1. **Missing visualization sequencing**: Read `module-01-quick-demo.md` and confirm that the visualization offer is embedded as a sub-point of Step 4 rather than its own sequenced step, and that Step 5 jumps directly to module-completion.md (will confirm bug on unfixed files)
2. **Missing module banner**: Read `module-transitions.md` and confirm there is no banner template or banner display instruction (will confirm bug on unfixed files)
3. **Non-tabular journey map**: Read `module-transitions.md` and confirm the journey map instruction says "Show a compact journey map" without specifying table format (will confirm bug on unfixed files)
4. **Vague Explore option**: Read `module-completion.md` and confirm the Explore option uses generic "dig deeper" language without mentioning visualization (will confirm bug on unfixed files)

**Expected Counterexamples**:
- `module-01-quick-demo.md` Step 5 references module-completion.md without a preceding visualization step
- `module-transitions.md` has no banner template anywhere in the file
- `module-transitions.md` journey map section lacks table format specification
- `module-completion.md` Explore option is generic across all modules

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed steering files contain the correct instructions.

**Pseudocode:**

```
FOR ALL file WHERE isBugCondition(file) DO
  content := readFile(file)
  IF file = "module-01-quick-demo.md" THEN
    ASSERT content CONTAINS visualization step as separate numbered step
    ASSERT visualization step number < module close step number
    ASSERT content CONTAINS "MUST complete before closing the module"
  IF file = "module-transitions.md" THEN
    ASSERT content CONTAINS banner template with "━━━" and "🚀🚀🚀"
    ASSERT content CONTAINS markdown table template with "| Module | Name | Status |"
    ASSERT content CONTAINS "✅" AND "🔄" AND "⬜" status icons
  IF file = "module-completion.md" THEN
    ASSERT content CONTAINS visualization-specific Explore language for Module 1
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed steering files preserve existing behavior.

**Pseudocode:**

```
FOR ALL file WHERE NOT isBugCondition(file) DO
  ASSERT originalContent(file) = fixedContent(file)
END FOR

// Additionally, within changed files:
FOR ALL section WHERE section NOT IN changedSections DO
  ASSERT originalSection(section) = fixedSection(section)
END FOR
```

**Testing Approach**: Manual diff review is appropriate for steering file changes because:
- The files are markdown text, not executable code
- Changes are localized to specific sections
- Preservation can be verified by confirming unchanged sections are identical

**Test Cases**:
1. **Onboarding banner preservation**: Verify `onboarding-flow.md` is not modified at all — the 🎓 welcome banner remains untouched
2. **Module completion workflow preservation**: Verify the journal template, reflection question, and path completion sections in `module-completion.md` are unchanged
3. **Step-level progress preservation**: Verify the "Step-Level Progress" section in `module-transitions.md` is unchanged
4. **Module 1 transition preservation**: Verify Steps 6-7 (formerly 5-6) in `module-01-quick-demo.md` retain the explicit close, purpose statement, and Module 2 use-case discovery questions

### Unit Tests

- Verify `module-01-quick-demo.md` has visualization as a distinct numbered step before the module close step
- Verify `module-transitions.md` contains the banner template with correct emoji and line format
- Verify `module-transitions.md` contains a markdown table template with Module, Name, Status columns
- Verify `module-completion.md` Explore option includes visualization language for Module 1

### Property-Based Tests

- For any module number N, verify `module-transitions.md` banner template can be instantiated with N and a module name
- For any set of modules with mixed completion states, verify the journey map table template can represent all three states (✅, 🔄, ⬜)
- For any module completion event, verify the next-step options in `module-completion.md` are present and well-formed

### Integration Tests

- Simulate Module 1 full flow: demo → results → visualization offer → user response → module close → journal → Module 2 transition
- Simulate Module 2 start: banner display → journey map table → before/after framing → module content
- Simulate Module 1 completion reaching module-completion.md: verify Explore option mentions visualization
