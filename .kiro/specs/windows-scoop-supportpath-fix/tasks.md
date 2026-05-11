# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Windows Scoop SUPPORTPATH Missing Fallback
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the steering file lacks SUPPORTPATH verification and fallback logic for Windows Scoop installs
  - **Scoped PBT Approach**: Scope the property to the concrete failing case: parse the current `module-02-sdk-setup.md` Step 8 and assert it contains SUPPORTPATH path verification with fallback to `$SENZING_DIR\..\data` when the standard path doesn't exist on Windows
  - Test that the steering file Step 8 content contains:
    - Instructions to verify SUPPORTPATH directory exists on Windows before using it
    - Fallback logic to check `$SENZING_DIR\..\data` when `$SENZING_DIR\data` does not exist
    - A Windows-conditional gate (e.g., "On Windows" or platform-specific scoping)
    - A filesystem verification command (e.g., `Test-Path` or directory existence check)
  - From Bug Condition in design: `isBugCondition(input)` where `input.platform == 'windows' AND input.installMethod == 'scoop' AND NOT directoryExists(input.senzingDir + '\data') AND directoryExists(input.senzingDir + '\..\data')`
  - Use Hypothesis to generate random Windows Scoop path scenarios (varying usernames, version strings) and assert the steering content contains explicit SUPPORTPATH verification instructions
  - Test file: `senzing-bootcamp/tests/test_scoop_supportpath_exploration.py`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the steering file lacks SUPPORTPATH verification logic for Scoop installs)
  - Document counterexamples found (e.g., "Step 8 instructs saving MCP-returned JSON directly without verifying SUPPORTPATH exists")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Scoop Configuration Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: Parse the current UNFIXED `module-02-sdk-setup.md` Step 8 and record the `sdk_guide(topic='configure')` MCP call instruction
  - Observe: Record the "NEVER construct engine configuration JSON manually" instruction text
  - Observe: Record that Step 8 flows into Step 9 (database connection test) without additional gates
  - Observe: Record that the MCP-returned JSON is the starting point for all engine configuration
  - Write property-based tests using Hypothesis:
    - For all non-Windows platforms (Linux, macOS), assert the MCP-first approach is unchanged — `sdk_guide(topic='configure')` remains the starting point
    - Assert the "NEVER construct engine configuration JSON manually" rule is preserved verbatim in the steering file
    - Assert any fallback logic is explicitly scoped to Windows only (conditional on platform detection)
    - Assert Step 9 follows Step 8 without additional verification gates for non-Windows platforms
    - Generate random platform/install-method combinations and verify fallback logic only applies to Windows + missing standard path
  - Test file: `senzing-bootcamp/tests/test_scoop_supportpath_preservation.py`
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for Windows Scoop SUPPORTPATH resolution failure

  - [x] 3.1 Implement the fix in `senzing-bootcamp/steering/module-02-sdk-setup.md`
    - Add Windows SUPPORTPATH verification block in Step 8 after the `sdk_guide(topic='configure')` MCP call instruction
    - Add conditional logic: "On Windows, verify the SUPPORTPATH directory exists before saving the configuration"
    - Add Scoop layout fallback: "If `$SENZING_DIR\data` does not exist, check `$SENZING_DIR\..\data` (Scoop package layout places the data directory one level above the `er` directory)"
    - Add verification command: instruct the agent to use `Test-Path` (PowerShell) to confirm the directory exists
    - Add informational note about Scoop layout explaining why the directory structure differs
    - Preserve the "NEVER construct engine configuration JSON manually" rule — clarify this is a targeted path correction based on filesystem verification, not manual JSON construction
    - Ensure the fallback is explicitly scoped to Windows only — Linux/macOS paths remain unmodified
    - _Bug_Condition: isBugCondition(input) where input.platform == 'windows' AND input.installMethod == 'scoop' AND NOT directoryExists(input.senzingDir + '\data') AND directoryExists(input.senzingDir + '\..\data')_
    - _Expected_Behavior: Agent verifies SUPPORTPATH exists on Windows, falls back to parent-level data directory for Scoop installs, engine initializes without SENZ2027 on first attempt_
    - _Preservation: Linux/macOS use MCP-returned paths unmodified; Windows installs where $SENZING_DIR\data exists use it directly; "never construct manually" rule preserved; sdk_guide MCP call remains starting point; Step 9 flow unchanged_
    - _Requirements: 1.1, 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Windows Scoop SUPPORTPATH Missing Fallback
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (SUPPORTPATH verification, fallback to parent-level data directory)
    - When this test passes, it confirms the steering file now contains proper Scoop SUPPORTPATH fallback logic
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Scoop Configuration Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm MCP-first approach unchanged, "never construct manually" rule preserved, fallback scoped to Windows only, Step 9 flow intact

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_scoop_supportpath_exploration.py senzing-bootcamp/tests/test_scoop_supportpath_preservation.py`
  - Verify the fixed `module-02-sdk-setup.md` passes CommonMark validation
  - Verify the fixed file's token count stays within budget defined in `steering-index.yaml`
  - Ensure all tests pass, ask the user if questions arise.
