# Implementation Plan: Module Transition Enforcement

## Overview

Add explicit instructions to 14 steering files so the agent always reads the progress file and displays the module start banner, journey map, and before/after framing at every module start. Two reinforcement layers: a central directive in `agent-instructions.md` and a per-module `🚀 First:` reminder in all 13 module steering files.

## Tasks

- [x] 1. Add central instruction to agent-instructions.md
  - Add an "At every module start" paragraph to the Module Steering section of `senzing-bootcamp/steering/agent-instructions.md`
  - The paragraph directs the agent to read `config/bootcamp_progress.json` first, then display the banner, journey map, and before/after framing before any module-specific work
  - Place after the module-to-steering-file mapping paragraph, before the Module 12 platform files paragraph
  - _Requirements: 1.1, 1.3_

- [x] 2. Add 🚀 First reminder to all 13 module steering files
  - [x] 2.1 Add reminder to module-00-sdk-setup.md
    - Add `🚀 First:` line immediately after the module heading, before the `User reference` line
    - Line reads: read `config/bootcamp_progress.json` and follow `module-transitions.md` — display banner, journey map, and before/after framing before proceeding
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.2 Add reminder to module-01-quick-demo.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.3 Add reminder to module-02-business-problem.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.4 Add reminder to module-03-data-collection.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.5 Add reminder to module-04-data-quality.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.6 Add reminder to module-05-data-mapping.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.7 Add reminder to module-06-single-source.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.8 Add reminder to module-07-multi-source.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.9 Add reminder to module-08-query-validation.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.10 Add reminder to module-09-performance.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.11 Add reminder to module-10-security.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.12 Add reminder to module-11-monitoring.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_
  - [x] 2.13 Add reminder to module-12-deployment.md
    - Same `🚀 First:` line placement and content as 2.1
    - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Checkpoint - Verify all changes are in place
  - Confirm `agent-instructions.md` contains the "At every module start" paragraph
  - Confirm all 13 module steering files contain the `🚀 First:` reminder line
  - Confirm the reminder appears before the `User reference` line in each file
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are marked complete — this spec retroactively documents work already implemented
- No code was written; all changes are natural-language text edits to steering files
- Requirements 3, 4, and 5 (banner display, journey map, before/after framing) are satisfied by the existing `module-transitions.md` file — the enforcement mechanism in tasks 1–2 ensures it gets loaded
