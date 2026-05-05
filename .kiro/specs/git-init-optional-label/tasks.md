# Implementation Plan: Git Initialization Question Should Indicate It's Optional

## Overview

Update the git initialization question in Module 1 Step 1 to explicitly state it's optional and can be skipped without affecting the bootcamp.

## Tasks

- [x] 1. Update git init question wording in module-01-business-problem.md
  - [x] 1.1 Locate the git initialization question in Step 1 of `senzing-bootcamp/steering/module-01-business-problem.md`
  - [x] 1.2 Replace the question text with: "👉 This is optional, but would you like me to initialize a git repository for version control? You can skip this without affecting the bootcamp."
    - Preserve the 👉 marker for hook detection
    - Preserve any surrounding hard-stop block (🛑 STOP) if present
    - Do not modify any other content in Step 1
    - _Requirements: 1, 2, 3_

- [x] 2. Verify the change
  - Confirm the updated question contains "optional" and reassurance about not affecting the bootcamp
  - Confirm the 👉 marker is present
  - Confirm no other Step 1 content was modified
  - Confirm existing git-init behavior (skip if already a repo, act on yes/no) is not affected by the wording change

## Notes

- This is a single-line wording change — no logic, hook, or structural changes
- The existing `agent-skips-git-question` spec already fixed the stop-and-wait behavior; this spec only addresses the "optional" labeling
