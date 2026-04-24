# Implementation Plan: Show Modules at Track Selection

## Overview

Insert a condensed module reference table (modules 0–11, number + title) into Step 5 of `senzing-bootcamp/steering/onboarding-flow.md`, immediately before the track list. This is a static content edit to a single steering file — no executable code is involved.

## Tasks

- [x] 1. Read canonical module titles from documentation
  - Open each file in `senzing-bootcamp/docs/modules/MODULE_*.md` and extract the module number and title from the `# Module N: Title` heading
  - Build the list of all 12 modules (0–11) with their canonical titles
  - _Requirements: 2_

- [x] 2. Insert agent instruction and module table into Step 5
  - [x] 2.1 Add agent instruction line after the `## 5. Track Selection` heading
    - Insert a line telling the agent to display the quick-reference table before presenting the tracks
    - _Requirements: 1, 3_
  - [x] 2.2 Add two-column markdown table (Module, Title) for modules 0–11
    - Table must appear between the `## 5. Track Selection` heading and the line beginning "Present tracks — not mutually exclusive…"
    - Use the canonical titles extracted in task 1
    - Table format: `| Module | Title |` with entries for modules 0 through 11
    - _Requirements: 1, 2, 4_

- [x] 3. Validate the edited steering file
  - [x] 3.1 Run CommonMark lint validation
    - Execute `python senzing-bootcamp/scripts/validate_commonmark.py` on the edited `onboarding-flow.md`
    - Fix any formatting issues (blank lines around headings, malformed tables, etc.)
    - _Requirements: 1_
  - [x] 3.2 Run power structure validation
    - Execute `python senzing-bootcamp/scripts/validate_power.py` to confirm the steering file is still valid within the power distribution
    - _Requirements: 1_

- [x] 4. Final checkpoint
  - Ensure all validations pass, ask the user if questions arise.

## Notes

- No property-based tests — this is a static markdown content edit with no executable code
- The condensed table includes all modules 0–11 with number + title only (no full descriptions)
- Module titles must match the canonical headings in `senzing-bootcamp/docs/modules/`
- Only `senzing-bootcamp/steering/onboarding-flow.md` Step 5 is modified; no other files or sections are changed
