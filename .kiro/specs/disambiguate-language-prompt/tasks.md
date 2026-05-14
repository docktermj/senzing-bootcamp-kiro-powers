# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Ambiguous Language Prompt at Step 2
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists in `senzing-bootcamp/steering/onboarding-flow.md`
  - **Scoped PBT Approach**: Scope the property to the concrete Step 2 section of `onboarding-flow.md` — parse the section heading, body text, and any prompt directives
  - Test file: `senzing-bootcamp/tests/test_disambiguate_language_prompt.py` using pytest + Hypothesis
  - Parse the Step 2 section of `onboarding-flow.md` and assert:
    - The section heading contains "programming language" (case-insensitive)
    - An explicit wording directive exists requiring "programming language" in the prompt
    - A disambiguation constraint is present forbidding bare "language" alone
  - Bug condition from design: `isBugCondition(input)` where `input.stepNumber == 2 AND input.promptText CONTAINS "language" AND input.promptText DOES NOT CONTAIN "programming language"`
  - Expected behavior: prompt text uses "programming language" so the question is unambiguous
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists: heading says "Language Selection" without "programming," no wording directive exists, no disambiguation constraint exists)
  - Document counterexamples found (e.g., "Step 2 heading is 'Language Selection' — missing 'programming' qualifier")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 2.1, 2.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Unchanged Onboarding Behaviors at Step 2
  - **IMPORTANT**: Follow observation-first methodology
  - Test file: `senzing-bootcamp/tests/test_disambiguate_language_prompt.py` (same file, separate test class)
  - Observe on UNFIXED code and write property-based tests verifying:
    - **MCP Call Preservation**: Step 2 contains instructions to call `get_capabilities` or `sdk_guide` on the Senzing MCP server
    - **Warning Relay Preservation**: Step 2 contains the discouraged-language warning relay instruction (text about relaying MCP server warnings and suggesting alternatives)
    - **Config Persistence Preservation**: Step 2 contains instruction to persist selection to `config/bootcamp_preferences.yaml`
    - **Mandatory Gate Preservation**: Step 2 contains the ⛔ mandatory gate marker and "STOP" instruction requiring real user input
    - **Language Steering File Loading**: Step 2 contains instruction to load language steering file after confirmation
  - Use Hypothesis `@given` strategies to generate random section boundary variations and verify preservation properties hold
  - Verify that no other sections of `onboarding-flow.md` (Steps 0, 0b, 0c, 1, 1b, 3, 4, 5) are modified
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for ambiguous "language" prompt at onboarding Step 2

  - [x] 3.1 Implement the fix in `senzing-bootcamp/steering/onboarding-flow.md`
    - Update section heading from "## 2. Language Selection" to "## 2. Programming Language Selection"
    - Add explicit wording directive: agent MUST use the phrase "programming language" (not just "language") when presenting the selection question
    - Update instructional text from "present the MCP-returned language list" to "present the MCP-returned programming language list" where describing bootcamper-facing output
    - Add disambiguation constraint: "When presenting this question, always use the phrase 'programming language' — never the bare word 'language' alone — to avoid ambiguity with natural/spoken languages."
    - Preserve ALL other content: MCP call instructions (`get_capabilities`/`sdk_guide`), warning relay logic, config persistence to `bootcamp_preferences.yaml`, mandatory gate (⛔) marker and STOP instruction, language steering file loading
    - _Bug_Condition: isBugCondition(input) where input.stepNumber == 2 AND input.promptText CONTAINS "language" AND NOT CONTAINS "programming language"_
    - _Expected_Behavior: Step 2 heading contains "Programming Language", body contains explicit wording directive and disambiguation constraint_
    - _Preservation: MCP calls, warning relay, config persistence, mandatory gate, language steering file loading all unchanged_
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Programming Language Qualifier Present
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (heading contains "programming language", wording directive exists, disambiguation constraint present)
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Unchanged Onboarding Behaviors at Step 2
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — MCP calls, warning relay, config persistence, mandatory gate all preserved)
    - Confirm all tests still pass after fix (no regressions)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_disambiguate_language_prompt.py -v`
  - Verify Property 1 (Bug Condition / Expected Behavior) passes
  - Verify Property 2 (Preservation) passes
  - Ensure no other tests in the repository are broken by the change
  - Ask the user if questions arise
