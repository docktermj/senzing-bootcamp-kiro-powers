# Implementation Plan: Module 8 Visualization Enforcement

## Overview

Create three static artifacts (steering file updates, JSON hook, README updates) that enforce visualization offers in Module 8. All deliverables are JSON and Markdown — no executable code.

**Note:** The design document references the new hook as README entry #16, but the module12-phase-gate spec claims #16. This plan uses entry #17 for the new hook, and updates the cross-reference in entry #14 accordingly.

## Tasks

- [x] 1. Update steering file with mandatory WAIT blocks
  - [x] 1.1 Insert entity graph MANDATORY WAIT block into `senzing-bootcamp/steering/module-08-query-validation.md`
    - Replace the soft "Offer entity graph visualization" paragraph in step 3 with the mandatory WAIT block from the design
    - Use `---` horizontal rules above and below, `⛔ MANDATORY VISUALIZATION OFFER — ENTITY GRAPH` heading, `🛑 DO NOT SKIP` blockquote, explicit WAIT instruction, and three-way decision tree (yes / no / unsure)
    - Reference `visualization-guide.md` in the "yes" path
    - _Requirements: 1.1, 1.2, 1.5, 1.7_

  - [x] 1.2 Insert results dashboard MANDATORY WAIT block into `senzing-bootcamp/steering/module-08-query-validation.md`
    - Replace the soft "Offer visualization" paragraph in step 7 with the mandatory WAIT block from the design
    - Use the same formatting pattern as the entity graph block: `---` rules, `⛔ MANDATORY VISUALIZATION OFFER — RESULTS DASHBOARD`, `🛑 DO NOT SKIP`, WAIT instruction, three-way decision tree
    - Reference `docs/results_dashboard.html` in the "yes" path
    - Verify no functional content in other steps was changed
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] 2. Create the visualization enforcement hook
  - [x] 2.1 Create `senzing-bootcamp/hooks/enforce-visualization-offers.kiro.hook`
    - JSON file with `name`, `version`, `description`, `when.type` = `"agentStop"`, `then.type` = `"askAgent"`
    - The `then.prompt` must: (a) instruct the agent to read `config/bootcamp_progress.json` and check `current_module`, (b) do nothing if module is not 8, (c) review conversation history for both visualization offers (entity graph and results dashboard), (d) do nothing if both were offered, (e) display `📊 MODULE 8 VISUALIZATION CHECK` banner for any missed offers, (f) ask the bootcamper about each missed visualization, (g) include explicit WAIT instruction
    - Follow the same JSON structure as `summarize-on-stop.kiro.hook`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 2.2 Write property test for hook JSON schema conformance
    - **Property 3: Hook JSON schema conformance**
    - Parse all `.kiro.hook` files in `senzing-bootcamp/hooks/`, assert each is valid JSON with required fields: `name` (string), `version` (string), `description` (string), `when.type` (string), `then.type` (string), `then.prompt` (string when `then.type` is `"askAgent"`)
    - **Validates: Requirements 2.5**

- [x] 3. Checkpoint — Verify steering file and hook
  - Ensure the hook file is valid JSON, both WAIT blocks are correctly placed in the steering file, and no existing step content was altered. Ask the user if questions arise.

- [x] 4. Update hooks README
  - [x] 4.1 Update entry #14 in `senzing-bootcamp/hooks/README.md`
    - Add a **Note** line to the existing entry for `offer-visualization.kiro.hook`
    - Note should explain the conjunction: this hook catches query program creation proactively, while the agentStop hook (#17) catches missed offers before the agent closes
    - _Requirements: 3.4_

  - [x] 4.2 Add entry #17 to `senzing-bootcamp/hooks/README.md`
    - Add as `### 17. Enforce Module 8 Visualization Offers (\`enforce-visualization-offers.kiro.hook\`) ⭐`
    - Include **Trigger**, **Action**, **Use case**, and **Recommended** lines matching the format of existing entries
    - Place after entry #16 (Module 12 Phase Gate, added by the module12-phase-gate spec)
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.3 Write property test for README hook entry format conformance
    - **Property 4: README hook entry format conformance**
    - Parse all numbered hook entry sections in `senzing-bootcamp/hooks/README.md`, assert each contains a **Trigger** line, an **Action** line, and a **Use case** line with non-empty content
    - **Validates: Requirements 3.2**

- [x] 5. Final checkpoint — Validate all deliverables
  - Ensure the hook file parses as valid JSON, both WAIT blocks use consistent formatting (⛔, 🛑, blockquotes, horizontal rules), the README has entries through #17, entry #14 has the conjunction note, and all tests pass. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All deliverables are static JSON and Markdown — no executable code
- The hook is safe to leave installed across all modules (no-op outside Module 8)
- Entry #17 accounts for the module12-phase-gate spec which adds entry #16
- Property tests validate cross-cutting schema conformance across all hooks and README entries
