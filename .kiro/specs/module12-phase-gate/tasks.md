# Implementation Plan: Module 12 Phase Gate

## Overview

Create three static artifacts (JSON hook, steering file update, README entry) that enforce the packaging-to-deployment phase gate in Module 12. All deliverables are JSON and Markdown — no executable code.

## Tasks

- [ ] 1. Create the phase gate hook file
  - [x] 1.1 Create `senzing-bootcamp/hooks/module12-phase-gate.kiro.hook`
    - JSON file with `name`, `version`, `description`, `when.type` = `"postTaskExecution"`, `then.type` = `"askAgent"`
    - The `then.prompt` must: (a) instruct the agent to read `config/bootcamp_progress.json` and check `current_module`, (b) do nothing if module is not 12, (c) display the packaging-complete banner with all five checklist items (containerization, multi-env config, CI/CD, checklist, documentation), (d) reassure that nothing was deployed, (e) ask deploy-or-stop question, (f) include explicit WAIT instruction
    - Follow the same JSON structure as existing hooks (see `offer-visualization.kiro.hook`, `summarize-on-stop.kiro.hook`)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

  - [ ]* 1.2 Write property test for hook JSON schema conformance
    - **Property 1: Hook JSON schema conformance**
    - Parse all `.kiro.hook` files in `senzing-bootcamp/hooks/`, assert each is valid JSON with required fields: `name` (string), `version` (string), `description` (string), `when.type` (string), `then.type` (string), `then.prompt` (string when `then.type` is `"askAgent"`)
    - **Validates: Requirements 1.7**

- [ ] 2. Update the steering file with phase gate section
  - [x] 2.1 Insert PHASE GATE section into `senzing-bootcamp/steering/module-12-deployment.md`
    - Insert between Step 11 (Pre-Deployment Checklist) and Step 12 (Rollback Plan)
    - Use `---` horizontal rules above and below for visual separation
    - Include `⛔ PHASE GATE` heading, `🛑 MANDATORY STOP` blockquote, packaging-complete banner, deploy-or-stop question, and bold WAIT instruction
    - Include three-way decision tree: stop / deploy now / unsure
    - Do NOT change any functional content in Steps 2–11 or Steps 12–15
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 3. Checkpoint — Verify hook and steering file
  - Ensure the hook file is valid JSON, the steering file phase gate section is correctly placed, and no existing step content was altered. Ask the user if questions arise.

- [ ] 4. Update hooks README with new entry
  - [x] 4.1 Add entry #16 to `senzing-bootcamp/hooks/README.md`
    - Add as `### 16. Module 12 Phase Gate (\`module12-phase-gate.kiro.hook\`)`
    - Include **Trigger**, **Action**, and **Use case** lines matching the format of existing entries
    - Place after entry #15 (Capture Bootcamp Feedback)
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 4.2 Write property test for README hook entry format conformance
    - **Property 2: README hook entry format conformance**
    - Parse all numbered hook entry sections in `senzing-bootcamp/hooks/README.md`, assert each contains a **Trigger** line, an **Action** line, and a **Use case** line with non-empty content
    - **Validates: Requirements 3.2**

- [x] 5. Final checkpoint — Validate all deliverables
  - Ensure the hook file parses as valid JSON, the steering file phase gate is between Step 11 and Step 12, the README has 16 numbered entries, and all tests pass. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All deliverables are static JSON and Markdown — no executable code
- The hook is safe to leave installed across all modules (no-op outside Module 12)
- Property tests validate cross-cutting schema conformance across all hooks and README entries
