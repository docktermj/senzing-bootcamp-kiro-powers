# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Steering File UX Defects
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bugs exist
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the three bugs exist in the current steering files
  - **Scoped PBT Approach**: Since these are deterministic markdown content bugs, scope the property to concrete failing assertions against file content
  - Write a test file at `tests/test_bootcamp_ux_bugs.py` using `pytest` that reads the three steering files and asserts the expected (fixed) content:
    - **Bug 1 — Visualization step ordering** (`senzing-bootcamp/steering/module-01-quick-demo.md`):
      - Assert that a visualization offer exists as its own numbered Phase 2 step (not embedded as a sub-point of the "Explain results" step)
      - Assert the visualization step number is less than the module-close step number
      - Assert the file contains instruction text requiring visualization to complete before module close
    - **Bug 2 — Missing module start banner** (`senzing-bootcamp/steering/module-transitions.md`):
      - Assert the file contains a "Module Start Banner" section
      - Assert the file contains the banner template with `━━━` line borders and `🚀🚀🚀` emojis
      - Assert the banner section appears before the "Journey Map" section
    - **Bug 3 — Non-tabular journey map** (`senzing-bootcamp/steering/module-transitions.md`):
      - Assert the journey map section contains a markdown table with `| Module | Name | Status |` header
      - Assert the section contains status icons `✅`, `🔄`, and `⬜`
    - **Bug 4 — Vague Explore option** (`senzing-bootcamp/steering/module-completion.md`):
      - Assert the Explore option mentions visualization, entity examination, or attribute search for Module 1
      - Assert a Module 1 special-case note exists in the next-step options section
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bugs exist)
  - Document which assertions fail and what the current content looks like
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Unchanged Steering File Behavior
  - **IMPORTANT**: Follow observation-first methodology — read current files, record baseline content, then write assertions
  - Observe and record the following from UNFIXED steering files:
    - `module-01-quick-demo.md`: Phase 2 Step 5 contains explicit module close text ("That's Module 1 complete!"), purpose statement, and `module-completion.md` reference; Step 6 contains Module 2 transition with use-case discovery questions
    - `module-transitions.md`: "Step-Level Progress" section contains Before/During/After framing with three numbered items; "Module Completion" section references `module-completion.md`
    - `module-completion.md`: Journal template format with `## Module N:` header and four fields; Reflection question with 👉 emoji; Next-step options include Proceed/Iterate/Explore/Share; Path Completion Detection table with paths A-D; Path Completion Celebration section with 🎉 emoji
  - Write property-based preservation tests in `tests/test_bootcamp_ux_preservation.py`:
    - Assert `module-01-quick-demo.md` retains the explicit module close statement and purpose summary
    - Assert `module-01-quick-demo.md` retains Module 2 transition with all three use-case discovery questions
    - Assert `module-transitions.md` retains the Step-Level Progress section with Before/During/After items unchanged
    - Assert `module-transitions.md` retains the Module Completion section referencing `module-completion.md`
    - Assert `module-completion.md` retains the journal template format with all four fields
    - Assert `module-completion.md` retains the reflection question text
    - Assert `module-completion.md` retains Proceed/Iterate/Share options (Explore will be enhanced, not removed)
    - Assert `module-completion.md` retains Path Completion Detection table and Celebration section
    - Assert `senzing-bootcamp/steering/onboarding-flow.md` (if it exists) is NOT modified — the 🎓 welcome banner is untouched
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for bootcamp UX steering file defects

  - [x] 3.1 Reorder Phase 2 steps in module-01-quick-demo.md to make visualization its own step
    - In `senzing-bootcamp/steering/module-01-quick-demo.md`, split Phase 2 Step 4 so "Explain results" stays as Step 4 and the visualization offer becomes a new Step 5
    - New Step 5 should contain the full visualization offer text: "Would you like me to create a web page showing these results?" with interactive feature options (how-entity, why-match, attribute search, path finding, static summary)
    - Add instruction in new Step 5: "This step MUST complete before closing the module. Do not skip to module-completion.md until the user has responded to the visualization offer."
    - Renumber old Step 5 (module close) → Step 6, old Step 6 (Module 2 transition) → Step 7
    - Preserve all existing content in the renumbered steps — only the step numbers change
    - _Bug_Condition: isBugCondition_Viz(X) where X.module = 1 AND X.phase = "completion" — visualization embedded as sub-point of Step 4_
    - _Expected_Behavior: Visualization offer is a separate numbered step before module close, with explicit "MUST complete" instruction_
    - _Preservation: Module close text, purpose statement, Module 2 transition questions must remain intact in renumbered steps_
    - _Requirements: 1.1, 2.1_

  - [x] 3.2 Add bold banner template and reformat journey map in module-transitions.md
    - In `senzing-bootcamp/steering/module-transitions.md`, insert a new "Module Start Banner" section BEFORE the existing "Journey Map" section
    - Banner section must contain the template:
      ```
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      🚀🚀🚀  MODULE N: [MODULE NAME IN CAPS]  🚀🚀🚀
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      ```
    - Include instruction: "Display this banner at the start of every module. This is the module equivalent of the onboarding welcome banner."
    - Replace the journey map prose ("Show a compact journey map...") with an explicit markdown table template using `| Module | Name | Status |` columns
    - Include status icon definitions: ✅ completed, 🔄 current (prefix module number with →), ⬜ upcoming
    - Include instruction: "MUST use this exact table format. Only show modules in the user's selected path."
    - Ensure section order is: (1) Module Start Banner, (2) Journey Map, (3) Before/After Framing, (4) Step-Level Progress, (5) Module Completion
    - Do NOT modify the Step-Level Progress or Module Completion sections
    - _Bug_Condition: isBugCondition_Banner(X) where X.event = "module_start" — no banner template exists; isBugCondition_Table(X) — journey map format unspecified_
    - _Expected_Behavior: Banner with ━━━ borders and 🚀🚀🚀 emojis displayed first; journey map as markdown table with three status icons_
    - _Preservation: Step-Level Progress section unchanged; Module Completion section unchanged_
    - _Requirements: 1.3, 1.4, 2.3, 2.4, 3.3_

  - [x] 3.3 Enhance Explore option with Module 1 visualization language in module-completion.md
    - In `senzing-bootcamp/steering/module-completion.md`, update the "Explore" bullet in the Next-Step Options section
    - Change from generic "Would you like to dig deeper into what we just did?" to include Module 1 context: "Would you like to explore further — visualize entities, examine match explanations, or search by attributes? (For other modules: dig deeper into what we just produced.)"
    - Add a callout after the next-step options list: "**Module 1 special case:** The visualization offer (web page with interactive features) should already have been presented before reaching this workflow. If the user declined, the Explore option above gives them another chance."
    - Do NOT modify the journal template, reflection question, Proceed/Iterate/Share options, Path Completion Detection table, or Path Completion Celebration section
    - _Bug_Condition: Explore option uses generic "dig deeper" language without mentioning visualization_
    - _Expected_Behavior: Explore option explicitly mentions visualization, entity examination, attribute search for Module 1_
    - _Preservation: Journal template, reflection question, other next-step options, path completion sections unchanged_
    - _Requirements: 1.2, 2.2, 3.2, 3.5_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Steering File UX Defects Fixed
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior for all three bugs
    - Run `pytest tests/test_bootcamp_ux_bugs.py`
    - **EXPECTED OUTCOME**: Test PASSES (confirms all three bugs are fixed)
    - All assertions about visualization step ordering, banner template, table format, and Explore option should now pass
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 2: Preservation** - Unchanged Steering File Behavior
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run `pytest tests/test_bootcamp_ux_preservation.py`
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm module close text, Module 2 transition, Step-Level Progress, journal template, reflection question, path completion sections all remain intact
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run `pytest tests/test_bootcamp_ux_bugs.py tests/test_bootcamp_ux_preservation.py`
  - Ensure all tests pass, ask the user if questions arise
