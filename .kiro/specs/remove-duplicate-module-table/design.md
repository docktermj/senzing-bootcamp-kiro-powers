# Remove Duplicate Module Table Bugfix Design

## Overview

The onboarding flow in `senzing-bootcamp/steering/onboarding-flow.md` presents the full module list (Modules 1–12) twice during the welcome sequence. Step 4 ("Bootcamp Introduction") instructs the agent to present a "Module overview table (1-12): what each does and why it matters" as part of the welcome overview. Step 5 ("Track Selection") then displays a separate "quick-reference module table" — a full markdown table with the same 12 modules — before presenting the track options. This redundancy makes the welcome message unnecessarily long and cluttered. The fix removes the duplicate table from Step 5 and its introductory sentence, keeping only the track descriptions and supporting content. Step 4's overview table remains the single source of module information.

## Glossary

- **Bug_Condition (C)**: Step 5 (Track Selection) of `onboarding-flow.md` contains a markdown module table that duplicates the module list already presented in Step 4
- **Property (P)**: Step 5 presents only the track descriptions (A–D), Module 2 auto-insertion note, and response interpretation rules — no module table
- **Preservation**: Step 4's module overview table, Step 5's track options, Module 2 auto-insertion note, response interpretation rules, and all other onboarding flow content remain unchanged
- **`onboarding-flow.md`**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines the bootcamp onboarding sequence from setup through track selection
- **Module overview table**: The table in Step 4 listing modules 1–12 with descriptions of what each does and why it matters
- **Quick-reference module table**: The duplicate markdown table in Step 5 listing modules 1–12 by number and title only

## Bug Details

### Bug Condition

The bug manifests when the agent executes Step 5 (Track Selection) of the onboarding flow. The steering file instructs the agent to "Display this quick-reference module table before presenting the tracks" — a full 12-row markdown table that repeats the same module list already shown in Step 4's overview. The bootcamper sees the module list twice in the same welcome message.

**Formal Specification:**

```
FUNCTION isBugCondition(input)
  INPUT: input of type OnboardingFlowFile
  OUTPUT: boolean

  step5_content := extractSection(input, "## 5. Track Selection")
  RETURN step5_content CONTAINS markdownTable WITH moduleNumbers [1..12]
END FUNCTION
```

### Examples

- **Full onboarding flow**: Agent executes Steps 4 and 5 in sequence → Step 4 presents the module overview table (1–12) with descriptions → Step 5 presents the same 12 modules again as a plain number/title table → bootcamper reads the module list twice
- **Step 5 in isolation**: Agent executes Step 5 → displays a 12-row markdown table before the track options → this table adds no information beyond what Step 4 already provided
- **Track cross-referencing**: The introductory sentence says "so the bootcamper can cross-reference module numbers" — but Step 4's overview already provides this, and the track descriptions themselves include module numbers (e.g., "2→3", "5→6→8")

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Step 4 (Bootcamp Introduction) continues to present the module overview table (1–12) with descriptions of what each module does and why it matters
- Step 5 (Track Selection) continues to present the four track options (A: Quick Demo, B: Fast Track, C: Complete Beginner, D: Full Production) with their module sequences
- Step 5 continues to include the "Module 2 inserted automatically before any module needing SDK" note
- Step 5 continues to include the response interpretation rules ("A"/"demo"→Module 3, etc.)
- All other sections of `onboarding-flow.md` (Steps 0–3, Switching Tracks, Changing Language, Validation Gates, Hook Registry) remain unchanged

**Scope:**
All content outside of Step 5's quick-reference module table and its introductory sentence is completely unaffected by this fix. The removal is limited to:
- The sentence "Display this quick-reference module table before presenting the tracks so the bootcamper can cross-reference module numbers:"
- The 12-row markdown table (header + 12 data rows)

## Hypothesized Root Cause

Based on the bug analysis, the root cause is straightforward:

1. **Redundant content in steering file**: Step 5 was written with its own module table to serve as a "quick reference" for track selection. However, Step 4 already presents the full module overview table with even more detail (descriptions of what each module does). Since Steps 4 and 5 are presented in the same onboarding session, the Step 5 table is purely redundant.

2. **Track descriptions already include module numbers**: Each track option already lists its module sequence (e.g., "2→3", "5→6→8", "1→4→5→6→8", "All 1-12"), making a separate cross-reference table unnecessary.

## Correctness Properties

Property 1: Bug Condition - Duplicate module table removed from Step 5

_For any_ version of `onboarding-flow.md` where Step 5 (Track Selection) contains a markdown table listing modules 1–12, the fixed file SHALL NOT contain that table in Step 5; Step 5 SHALL present only the track descriptions, Module 2 auto-insertion note, and response interpretation rules.

**Validates: Requirements 2.1, 2.2**

Property 2: Preservation - Step 4 table, track options, and all other content unchanged

_For any_ content in `onboarding-flow.md` that is not the Step 5 quick-reference module table or its introductory sentence, the fixed file SHALL preserve that content unchanged, including Step 4's module overview table, Step 5's track descriptions, Module 2 auto-insertion note, response interpretation rules, and all other sections.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Section**: `## 5. Track Selection`

**Specific Changes**:

1. **Remove introductory sentence**: Delete the line "Display this quick-reference module table before presenting the tracks so the bootcamper can cross-reference module numbers:"

2. **Remove markdown table**: Delete the entire quick-reference module table (header row, separator row, and all 12 data rows):
   ```
   | Module | Title                                |
   |--------|--------------------------------------|
   | 1      | Understand Business Problem          |
   | 2      | Set Up SDK                           |
   | 3      | Quick Demo (Optional)                |
   | 4      | Data Collection Policy               |
   | 5      | Data Quality & Mapping               |
   | 6      | Load Single Data Source              |
   | 7      | Multi-Source Orchestration           |
   | 8      | Query and Visualize                  |
   | 9      | Performance Testing and Benchmarking |
   | 10     | Security Hardening                   |
   | 11     | Monitoring and Observability         |
   | 12     | Package and Deploy                   |
   ```

3. **No other changes**: All remaining Step 5 content (track descriptions, Module 2 note, response interpretation rules) stays exactly as-is. All other sections of the file are untouched.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior. Since this is a steering file (natural language instructions for an LLM), testing focuses on structural analysis of file content — verifying the presence or absence of the markdown table in specific sections.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that Step 5 contains a duplicate module table.

**Test Plan**: Parse `onboarding-flow.md`, extract the Step 5 section, and check for the presence of a markdown table with module numbers 1–12. Run this test on the UNFIXED file to confirm the bug condition exists.

**Test Cases**:
1. **Step 5 contains module table**: Parse Step 5 and assert it does NOT contain a markdown table with module rows (will fail on unfixed code because the table IS present)
2. **Module list appears only once**: Count the number of sections containing module tables listing 1–12 and assert exactly one exists (will fail on unfixed code because two exist)

**Expected Counterexamples**:
- Step 5 contains a 12-row markdown table with modules 1–12
- The file contains two distinct sections with module listings (Step 4 overview + Step 5 table)

### Fix Checking

**Goal**: Verify that for the file where the bug condition holds, the fixed file no longer contains the duplicate table in Step 5.

**Pseudocode:**

```
FOR onboarding-flow.md WHERE isBugCondition(file) DO
  step5 := extractSection(fixed_file, "## 5. Track Selection")
  ASSERT NOT containsMarkdownModuleTable(step5)
  ASSERT containsTrackDescriptions(step5)
END FOR
```

### Preservation Checking

**Goal**: Verify that all content outside the removed table is preserved unchanged.

**Pseudocode:**

```
FOR ALL sections WHERE NOT isBugCondition(section) DO
  ASSERT original_file(section) = fixed_file(section)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can verify that all non-table content in Step 5 is preserved
- It catches edge cases where adjacent content might be accidentally removed
- It provides strong guarantees that Step 4's module table and all other sections are unchanged

**Test Plan**: Observe the full content of `onboarding-flow.md` on UNFIXED code. Extract Step 4's module overview content, Step 5's track descriptions, Module 2 note, response interpretation rules, and all other sections. Write tests asserting these are preserved after the fix.

**Test Cases**:
1. **Step 4 module overview preserved**: Verify Step 4 still contains the module overview table (1–12) with descriptions
2. **Track descriptions preserved**: Verify Step 5 still contains all four track options (A–D) with module sequences
3. **Module 2 note preserved**: Verify Step 5 still contains "Module 2 inserted automatically before any module needing SDK"
4. **Response interpretation preserved**: Verify Step 5 still contains the interpretation rules ("A"/"demo"→Module 3, etc.)
5. **Other sections preserved**: Verify all other sections (Steps 0–3, Switching Tracks, Changing Language, Validation Gates, Hook Registry) are unchanged

### Unit Tests

- Parse Step 5 and assert no markdown table with module numbers exists
- Parse Step 5 and assert track descriptions (A–D) are present
- Parse Step 4 and assert the module overview table is still present
- Count module tables in the full file and assert exactly one exists (in Step 4)

### Property-Based Tests

- Generate random section selections from the file and verify non-Step-5-table content is preserved between unfixed and fixed versions
- Verify that the Step 5 section in the fixed file contains all expected content (tracks, Module 2 note, interpretation rules) except the removed table

### Integration Tests

- Verify the full file parses as valid markdown after the fix
- Verify the Step 4 → Step 5 flow presents module information exactly once followed by track selection
