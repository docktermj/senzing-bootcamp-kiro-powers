# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Windows Multi-Arg Mkdir Ambiguity
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the steering file lacks explicit platform-selection logic
  - **Scoped PBT Approach**: Scope the property to the concrete failing case: parse the current `project-structure.md` and assert it contains explicit platform-conditional gating (e.g., "On Windows" / "On Linux" conditional blocks) that prevent multi-arg `mkdir` on Windows
  - Test that the steering file content, when parsed for Windows platform, unambiguously directs to Python `os.makedirs` loop or PowerShell `ForEach-Object` pipeline (from Bug Condition in design: `isBugCondition(input)` where `input.platform == "Windows" AND input.commandSyntax == "mkdir <path1> <path2> ... <pathN>"`)
  - Use Hypothesis to generate random subsets of the 18 required directory paths and assert the steering content contains an explicit prohibition against multi-arg `mkdir` on Windows
  - Test file: `senzing-bootcamp/tests/test_windows_directory_fix_exploration.py`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the steering file lacks platform-selection logic)
  - Document counterexamples found (e.g., "steering file presents commands as flat alternatives without platform gate")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 2.1, 2.2, 2.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Windows Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: Parse the current UNFIXED `project-structure.md` and record the Linux/macOS `mkdir -p` brace-expansion command text
  - Observe: Record the Python `os.makedirs` loop content verbatim
  - Observe: Record the YAML frontmatter `inclusion: auto` setting
  - Observe: Record all 18 required directory paths present in the file
  - Write property-based tests using Hypothesis:
    - For all non-Windows platforms (Linux, macOS), assert the `mkdir -p` command block is textually identical between original and fixed content
    - For random subsets of the 18 directory paths, assert all paths appear in the Linux/macOS command block
    - Assert the Python `os.makedirs` loop content is textually unchanged
    - Assert YAML frontmatter `inclusion: auto` is preserved
  - Test file: `senzing-bootcamp/tests/test_windows_directory_fix_preservation.py`
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix for Windows directory creation failure

  - [x] 3.1 Implement the fix in `senzing-bootcamp/steering/project-structure.md`
    - Add explicit platform-detection instruction at the top of the "Create Structure" section: "Detect the operating system first. Use the platform-specific command below that matches the detected OS."
    - Restructure command alternatives as conditional blocks with headers: "### On Windows (PowerShell)" and "### On Linux / macOS"
    - Promote Python `os.makedirs` loop as "Preferred (all platforms)" and place it first
    - Add explicit prohibition: "NEVER use `mkdir path1 path2 path3` on Windows — PowerShell's mkdir does not accept multiple positional arguments."
    - Keep existing command content (Python loop, `mkdir -p` brace expansion, PowerShell `ForEach-Object` pipeline) unchanged
    - _Bug_Condition: isBugCondition(input) where input.platform == "Windows" AND input.commandSyntax == "mkdir <path1> <path2> ... <pathN>" AND numberOfPaths > 1_
    - _Expected_Behavior: On Windows, agent uses Python os.makedirs loop or PowerShell ForEach-Object pipeline, never multi-arg mkdir; all directories created without error on first attempt_
    - _Preservation: Linux/macOS continues to use mkdir -p with brace expansion; Python loop unchanged; YAML frontmatter unchanged; all 18 directory paths present in every platform block_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Windows Multi-Arg Mkdir Ambiguity
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (explicit platform gate, prohibition of multi-arg mkdir on Windows)
    - When this test passes, it confirms the steering file now contains proper platform-selection logic
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Windows Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm Linux/macOS command block unchanged, Python loop unchanged, frontmatter unchanged, all 18 paths present

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_windows_directory_fix_exploration.py senzing-bootcamp/tests/test_windows_directory_fix_preservation.py`
  - Verify the fixed `project-structure.md` passes CommonMark validation
  - Verify the fixed file's token count stays within budget defined in `steering-index.yaml`
  - Ensure all tests pass, ask the user if questions arise.
