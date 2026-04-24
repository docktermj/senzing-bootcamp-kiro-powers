# Implementation Plan: Hooks Distribution via createHook

## Overview

Replace file-copy-based hook installation with programmatic `createHook` calls. All deliverables are steering file and documentation updates — no executable code. The Hook Registry (all 18 hook definitions) is embedded in `onboarding-flow.md`, and all other files are updated to reference the new approach.

## Tasks

- [ ] 1. Add Hook Registry to onboarding-flow.md
  - [x] 1.1 Append the Hook Registry section to the end of `senzing-bootcamp/steering/onboarding-flow.md`
    - Add a `## Hook Registry` section with two subsections: `### Critical Hooks` (7 hooks) and `### Module Hooks` (11 hooks)
    - Each hook definition uses a markdown table with `Parameter | Value` columns containing: id, name, description, eventType, hookAction, outputPrompt, and where applicable filePatterns, toolTypes
    - Critical Hooks (created during onboarding): capture-feedback, enforce-feedback-path, enforce-working-directory, verify-senzing-facts, code-style-check, summarize-on-stop, commonmark-validation
    - Module Hooks with module associations: data-quality-check (Module 5), validate-senzing-json (Module 5), analyze-after-mapping (Module 5), backup-before-load (Module 6), run-tests-after-change (Module 6), verify-generated-code (Module 6), offer-visualization (Module 8), enforce-visualization-offers (Module 8), module12-phase-gate (Module 12), backup-project-on-request (any module), git-commit-reminder (any module)
    - All parameter values must exactly match the definitions in the design document (Component 1)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Update onboarding-flow.md Step 1 to use createHook
  - [ ] 2.1 Replace the file-copy instruction in Step 1 with createHook-based hook creation
    - Replace `2. Install hooks: copy senzing-bootcamp/hooks/*.kiro.hook to .kiro/hooks/.` with the new instruction to create Critical Hooks from the Hook Registry using `createHook`
    - Add a verification sub-step (2b) instructing the agent to check `.kiro/hooks/` for each Critical Hook, retry once on failure, and record status in `config/bootcamp_preferences.yaml` under `hooks_installed`
    - Include error handling: log failures, continue with remaining hooks, report failures with impact messages after all attempts
    - Preserve existing step ordering: directory creation (1) → hook creation (2) → glossary copy (3) → steering file generation (4)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3_

- [ ] 3. Checkpoint — Review onboarding-flow.md changes
  - Ensure the Hook Registry contains all 18 hook definitions and Step 1 uses createHook. Ask the user if questions arise.

- [ ] 4. Update agent-instructions.md Hooks section
  - [ ] 4.1 Replace the Hooks section in `senzing-bootcamp/steering/agent-instructions.md`
    - Replace `Install to .kiro/hooks/ from senzing-bootcamp/hooks/. Create directory if needed.` with the new directive to create hooks using `createHook` and the Hook Registry in `onboarding-flow.md`
    - Add directive for Module Hooks: check the Hook Registry and create Module_Hooks at each module start
    - Add session resume directive: check `config/bootcamp_preferences.yaml` for `hooks_installed`; if present skip creation, if absent create Critical Hooks
    - Retain the existing directive that `capture-feedback` is critical and must be verified
    - _Requirements: 7.1, 7.2, 7.3_

- [ ] 5. Update session-resume.md to check hooks_installed status
  - [ ] 5.1 Add hooks_installed check to Step 1 of `senzing-bootcamp/steering/session-resume.md`
    - In Step 1 (Read All State Files), add `config/bootcamp_preferences.yaml` check for `hooks_installed` key
    - If `hooks_installed` exists with hook names and timestamp → skip hook creation
    - If `hooks_installed` is missing or empty → load Hook Registry from `onboarding-flow.md` and create Critical Hooks before the welcome-back banner
    - _Requirements: 5.4_

- [ ] 6. Update HOOKS_INSTALLATION_GUIDE.md
  - [ ] 6.1 Rewrite `senzing-bootcamp/docs/guides/HOOKS_INSTALLATION_GUIDE.md` to reflect createHook approach
    - Replace "Automatic Installation" section: hooks are created programmatically via `createHook` during onboarding, not copied from files
    - Replace "Manual Installation" section: primary method is "Ask the agent: Please recreate the bootcamp hooks"; remove file-copy commands and `scripts/install_hooks.py` references
    - Update the hook count from 11 to 18
    - Update the hook table to list all 18 hooks with their triggers and purposes
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 7. Update hooks/README.md
  - [ ] 7.1 Update `senzing-bootcamp/hooks/README.md` installation section
    - Add `createHook`-based installation as the primary method (Option 1: automatic during onboarding, Option 2: ask the agent)
    - Demote file-copying to secondary method for development environments where the hooks directory is available
    - Remove `scripts/install_hooks.py` from recommended methods
    - Add a note that `.kiro.hook` files are the canonical source and the Hook Registry in `onboarding-flow.md` must be kept in sync
    - _Requirements: 9.1, 9.2, 9.3, 10.1, 10.2, 10.3_

- [ ] 8. Checkpoint — Review all documentation changes
  - Ensure all files are consistent: agent-instructions.md references createHook, session-resume.md checks hooks_installed, HOOKS_INSTALLATION_GUIDE.md lists 18 hooks, hooks/README.md uses createHook as primary method. Ask the user if questions arise.

- [ ] 9. Validate with validate_power.py
  - [ ] 9.1 Run `python senzing-bootcamp/scripts/validate_power.py` and fix any issues
    - Execute the validation script to check for broken cross-references, missing files, or structural issues introduced by the changes
    - Fix any validation errors found
    - _Requirements: 10.1_

- [ ] 10. Final checkpoint — Ensure consistency across all modified files
  - Verify: onboarding-flow.md no longer contains `copy senzing-bootcamp/hooks/` instruction, Hook Registry has all 18 definitions, agent-instructions.md references createHook, session-resume.md checks hooks_installed, HOOKS_INSTALLATION_GUIDE.md lists 18 hooks, hooks/README.md lists createHook as primary. Ask the user if questions arise.

## Notes

- All deliverables are steering file and documentation updates — no executable code
- The 18 `.kiro.hook` files in `senzing-bootcamp/hooks/` are retained as canonical definitions (Requirement 10.1)
- The Hook Registry in onboarding-flow.md must stay in sync with the `.kiro.hook` files (Requirement 10.2)
- Task 1 (Hook Registry) is the largest task — it contains all 18 hook definitions with full createHook parameters
