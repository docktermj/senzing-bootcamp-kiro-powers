# Implementation Plan

- [x] 1. Write bug condition exploration tests
  - **Property 1: Bug Condition** - Missing Mandatory Gate and Anti-Fabrication Rules
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in the unfixed steering files
  - **Scoped PBT Approach**: Scope the property to the concrete failing cases — the three files that lack gate/anti-fabrication content
  - Create test file `senzing-bootcamp/tests/test_track_selection_gate_bug.py`
  - Test 1 — Missing Gate in Step 5: Parse `senzing-bootcamp/steering/onboarding-flow.md`, extract the Step 5 section, and assert it contains a mandatory gate/stop instruction (e.g., keywords like "MUST stop", "mandatory gate", "⛔"). On unfixed content this will FAIL because no gate exists.
  - Test 2 — Missing Anti-Fabrication Rule: Parse `senzing-bootcamp/steering/agent-instructions.md`, extract the Communication section, and assert it contains an explicit fabrication prohibition (e.g., keywords like "fabricat", "never generate.*Human:", "simulate.*user"). On unfixed content this will FAIL because no such rule exists.
  - Test 3 — Weak Hook Language: Parse `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` as JSON, extract the `then.prompt` field, and assert it contains explicit fabrication prohibition beyond just "role-play" (e.g., "fabricat", "Human:", "simulate"). On unfixed content this will FAIL because the prompt only uses weak "role-play" language.
  - Test 4 — Hook Registry Sync: Parse `senzing-bootcamp/steering/hook-registry.md`, extract the `ask-bootcamper` prompt text, and assert it matches the prompt in the hook JSON file. On unfixed content this may PASS or FAIL depending on current sync state.
  - Use Hypothesis `@given()` with `@settings(max_examples=100)` for property-based generation of gate-step identifiers to verify only Steps 2 and 5 are mandatory gates
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests 1-3 FAIL (this is correct — it proves the bug exists). Document counterexamples found.
  - Mark task complete when tests are written, run, and failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Gate Onboarding Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Create test file `senzing-bootcamp/tests/test_track_selection_gate_preservation.py`
  - Observe UNFIXED file content first, then write property-based tests asserting structural properties are preserved:
  - Observe: Steps 0, 1, 1b in `onboarding-flow.md` contain no gate/stop instructions — assert this holds
  - Observe: Step 4 content (introduction, module table, mock data, license, glossary reference) is present — assert these content markers exist
  - Observe: Track mapping logic "A"→Module 3, "B"→Module 5, "C"→Module 1, "D"→Module 1 is present in Step 5 — assert mapping text is preserved
  - Observe: General note about "Do NOT include inline closing questions or WAIT instructions" exists at top of onboarding-flow.md — assert it is preserved
  - Observe: `ask-bootcamper` hook prompt contains recap logic ("recap:", "what you accomplished", "files created or modified") and closing question logic ("👉 question") — assert these are preserved
  - Observe: `ask-bootcamper.kiro.hook` is valid JSON with required keys (`name`, `version`, `description`, `when.type`, `then.type`, `then.prompt`) — assert structure is preserved
  - Observe: Hook registry entry for `ask-bootcamper` contains id, name, description fields — assert format is preserved
  - Use Hypothesis `@given()` with `@settings(max_examples=100)` to generate random non-gate step identifiers and verify none contain gate instructions
  - Verify all tests PASS on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix for agent fabricating track selection response instead of stopping

  - [x] 3.1 Fix `onboarding-flow.md` — Add mandatory gate concept and gate instructions
    - Update the general note at the top of the file to acknowledge mandatory gates as an exception to the "no inline WAIT" rule
    - Add a mandatory gate instruction block to Step 5 (Track Selection) after the "Interpreting responses" line, using a visually distinct format (blockquote with ⛔ emoji) instructing the agent to STOP after presenting tracks
    - Annotate Step 2 (Language Selection) as a mandatory gate for consistency
    - _Bug_Condition: isBugCondition(agentState) where agentState.currentStep = "Step 5: Track Selection" AND trackOptionsPresented = true AND receivedRealUserInput = false AND agentStoppedAfterPresenting = false_
    - _Expected_Behavior: Fixed steering file contains mandatory gate instruction in Step 5 that forces agent to stop after presenting track options_
    - _Preservation: Steps 0, 1, 1b, 3, 4 remain unchanged; general "no inline WAIT" note preserved with gate exception documented_
    - _Requirements: 2.1, 2.4, 3.1, 3.2, 3.5_

  - [x] 3.2 Fix `agent-instructions.md` — Add anti-fabrication rule to Communication section
    - Add an explicit rule to the Communication section prohibiting the agent from fabricating, simulating, or generating text that represents user input
    - Rule must cover: generating "Human:" messages, assuming user choices, acting on behalf of the user without actual input
    - _Bug_Condition: No rule in Communication section explicitly prohibits fabricating user responses_
    - _Expected_Behavior: Communication section contains explicit anti-fabrication prohibition_
    - _Preservation: All existing Communication rules remain intact; new rule is additive_
    - _Requirements: 2.2_

  - [x] 3.3 Fix `ask-bootcamper.kiro.hook` — Strengthen anti-fabrication language in hook prompt
    - Replace "Do not role-play as the bootcamper" with explicit language: "NEVER fabricate user input. Do not generate 'Human:' messages, simulate user responses, assume user choices, or produce any text that represents what the bootcamper might say. If user input is required, STOP and wait."
    - Ensure the hook file remains valid JSON after modification
    - _Bug_Condition: Hook prompt uses only weak "role-play" language insufficient to prevent fabrication_
    - _Expected_Behavior: Hook prompt contains explicit fabrication prohibition covering "Human:" messages, simulated responses, and assumed choices_
    - _Preservation: Recap logic, closing question logic, 👉 pattern, and all non-fabrication-related prompt content preserved_
    - _Requirements: 2.2_

  - [x] 3.4 Fix `hook-registry.md` — Update registry entry to match updated hook file
    - Update the Prompt text in the `ask-bootcamper` entry under Critical Hooks to match the strengthened language in the actual hook file
    - Ensure the registry entry format remains consistent with other entries
    - _Bug_Condition: Hook registry prompt may diverge from actual hook file after fix_
    - _Expected_Behavior: Registry prompt matches hook file prompt exactly_
    - _Preservation: All other hook registry entries unchanged; entry format preserved_
    - _Requirements: 2.2_

  - [x] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Mandatory Gate and Anti-Fabrication Rules Present
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (gate instructions exist, anti-fabrication rules exist, strong hook language exists)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.4_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Gate Onboarding Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint — Ensure all tests pass
  - Run the full test suite: `pytest senzing-bootcamp/tests/test_track_selection_gate_bug.py senzing-bootcamp/tests/test_track_selection_gate_preservation.py -v`
  - Ensure all tests pass, ask the user if questions arise
