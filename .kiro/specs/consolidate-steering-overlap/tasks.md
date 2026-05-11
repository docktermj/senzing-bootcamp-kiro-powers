# Implementation Plan: Consolidate Steering Overlap

## Overview

Replace two overlapping auto-included steering files (`structure.md` and `repository-organization.md`) with a single consolidated `structure.md` that preserves all rules under 80 lines.

## Tasks

- [x] 1. Write the consolidated steering file
  - [x] 1.1 Create `.kiro/steering/structure.md` with the consolidated content from the design document
    - Include valid YAML frontmatter with `inclusion: auto` and `description` field
    - Include the compact directory tree showing `senzing-bootcamp/` structure plus repo-level directories
    - Include the file placement table mapping content type → location → audience
    - Include naming conventions bullet list
    - Include the three rules (no dev notes, power config at root, hook tests in repo-root `tests/`)
    - _Requirements: 1.1, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4_

- [x] 2. Remove the original files
  - [x] 2.1 Delete `.kiro/steering/repository-organization.md`
    - Confirm the file no longer exists after deletion
    - _Requirements: 1.2_

- [x] 3. Verify consolidation
  - [x] 3.1 Verify line count is ≤ 80 lines (run `wc -l` on the consolidated file)
    - _Requirements: 3.1_
  - [x] 3.2 Verify content completeness against requirements 2.1–2.7
    - Confirm directory tree is present
    - Confirm file placement table with audience info is present
    - Confirm naming conventions are present
    - Confirm all three rules are present
    - Confirm repo-level directories are included
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [ ] 4. Final checkpoint
  - Ensure the consolidated file passes any existing CI linting, ask the user if questions arise.

## Notes

- No `steering-index.yaml` update is needed — that file tracks power steering files in `senzing-bootcamp/steering/`, not workspace-level `.kiro/steering/` files
- Property-based testing does not apply — this is a static file consolidation with no executable logic
- The consolidated content is fully specified in the design document
