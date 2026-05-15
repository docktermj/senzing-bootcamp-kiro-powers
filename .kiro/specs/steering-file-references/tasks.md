# Implementation Plan: Steering File References

## Overview

Add `#[[file:]]` references to two manual steering workflow files so the Kiro agent automatically receives critical context when those workflows are activated. This is a purely additive Markdown change — no new files, no executable logic.

## Tasks

- [x] 1. Add file references to `add-new-module.md`
  - [x] 1.1 Insert `#[[file:senzing-bootcamp/config/module-dependencies.yaml]]` and `#[[file:senzing-bootcamp/steering/module-prerequisites.md]]` after the YAML frontmatter closing `---` and before the first heading
    - Place references on their own lines, separated by a blank line from the heading
    - _Requirements: 1.1, 1.2, 4.1, 4.2, 4.3_

- [x] 2. Add file reference to `add-new-script.md`
  - [x] 2.1 Insert `#[[file:.kiro/steering/python-conventions.md]]` after the YAML frontmatter closing `---` and before the first heading
    - Place reference on its own line, separated by a blank line from the heading
    - _Requirements: 2.1, 4.1, 4.2, 4.3_

- [x] 3. Verify changes
  - [x] 3.1 Confirm referenced files exist at the specified paths
    - `senzing-bootcamp/config/module-dependencies.yaml` exists
    - `senzing-bootcamp/steering/module-prerequisites.md` exists
    - `.kiro/steering/python-conventions.md` exists
    - _Requirements: 1.1, 1.2, 2.1_
  - [x] 3.2 Run `python senzing-bootcamp/scripts/lint_steering.py` and confirm the modified steering files pass
    - _Requirements: 4.1, 4.2, 4.3_
  - [x] 3.3 Run `python senzing-bootcamp/scripts/measure_steering.py --check` and confirm token budgets are not exceeded
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 4. Final checkpoint
  - Ensure all validations pass, ask the user if questions arise.

## Notes

- `validation-suite.md` remains unchanged per Requirements 3.1 and 3.2
- No files exceeding 200 lines are referenced (Requirements 5.1)
- No execute-only scripts are referenced (Requirements 1.3, 1.4, 2.2, 2.3, 5.3)
- PBT does not apply — this is a documentation enhancement with no executable logic
