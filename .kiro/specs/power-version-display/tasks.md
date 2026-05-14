# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - POWER.md Frontmatter Missing Version Field
  - **IMPORTANT**: Write this property-based test BEFORE implementing the fix
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to the concrete failing case — parse current `senzing-bootcamp/POWER.md` frontmatter and attempt to extract a `version` field
  - Create test file `senzing-bootcamp/tests/test_version_frontmatter_properties.py`
  - Import `version` module via `sys.path` manipulation (follow existing pattern in `test_version_properties.py`)
  - Add a `read_version_from_frontmatter()` import (will fail initially since function doesn't exist yet — use `pytest.importorskip` or conditional import with skip)
  - **Property under test**: For any POWER.md content containing valid YAML frontmatter with a `version` field in MAJOR.MINOR.PATCH format, `read_version_from_frontmatter(content)` returns the validated version string
  - **Concrete bug condition test**: Read the actual `senzing-bootcamp/POWER.md` file content, attempt to extract version from frontmatter — assert it returns `"0.11.0"` (matching VERSION file)
  - **Bug Condition from design**: `isBugCondition(input)` where `input.currentStep == "0c" AND input.environment == "kiro-sandboxed" AND NOT fileAccessible("senzing-bootcamp/VERSION") AND steeringInstructs(readFile("senzing-bootcamp/VERSION"))`
  - **Expected Behavior**: `read_version_from_frontmatter(power_md_content)` returns the same version as the VERSION file
  - Use Hypothesis `@given()` with strategy generating valid POWER.md frontmatter content containing semver version strings — assert `read_version_from_frontmatter` extracts and validates them correctly
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (ImportError for missing function, or assertion failure because POWER.md has no `version` field) — this confirms the bug exists
  - Document counterexamples found (e.g., "Current POWER.md frontmatter has no `version` field — `read_version_from_frontmatter` does not exist")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Existing Version Functions Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - **IMPORTANT**: Write these tests BEFORE implementing the fix
  - Create preservation test class in `senzing-bootcamp/tests/test_version_frontmatter_properties.py` (same file as task 1)
  - Observe on UNFIXED code:
    - `read_version()` reads from `senzing-bootcamp/VERSION` and returns `"0.11.0"`
    - `validate_version("0.11.0")` returns `"0.11.0"`
    - `validate_version("invalid")` raises `VersionError`
    - `format_version_display("0.11.0")` returns `"Senzing Bootcamp Power v0.11.0"`
    - `parse_version("0.11.0")` returns `(0, 11, 0)`
    - `format_version(0, 11, 0)` returns `"0.11.0"`
  - Write property-based tests using Hypothesis:
    - **Property**: For all valid semver strings (components 0–99), `read_version()` continues to read from VERSION file and `validate_version()` accepts/rejects the same inputs as before
    - **Property**: For all valid semver strings, `format_version_display(v)` returns `f"Senzing Bootcamp Power v{v}"`
    - **Property**: For all valid semver strings, `parse_version(format_version(a, b, c)) == (a, b, c)` round-trip holds
    - **Property**: For all invalid version strings (leading zeros, non-numeric, wrong format), `validate_version()` raises `VersionError`
  - Verify that `onboarding-flow.md` Step 0c currently references `senzing-bootcamp/VERSION` (steering content preservation baseline)
  - Use `@settings(max_examples=100)` per project conventions
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 3. Fix for POWER.md version not accessible in sandboxed workspaces

  - [x] 3.1 Add `version` field to POWER.md YAML frontmatter
    - Edit `senzing-bootcamp/POWER.md` frontmatter block
    - Add `version: "0.11.0"` field after `displayName` and before `description`
    - Resulting frontmatter:
      ```yaml
      ---
      name: "senzing-bootcamp"
      displayName: "Senzing Bootcamp"
      version: "0.11.0"
      description: "Guided 11-module bootcamp..."
      keywords: [...]
      author: "Senzing"
      ---
      ```
    - Verify the VERSION file (`senzing-bootcamp/VERSION`) contains `0.11.0` — both sources must match
    - _Bug_Condition: isBugCondition(input) where input.environment == "kiro-sandboxed" AND NOT fileAccessible("senzing-bootcamp/VERSION")_
    - _Expected_Behavior: POWER.md frontmatter contains version field accessible during power activation_
    - _Preservation: VERSION file remains unchanged as single source of truth for CI/scripts_
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Add `read_version_from_frontmatter()` function to `version.py`
    - Edit `senzing-bootcamp/scripts/version.py`
    - Add function `read_version_from_frontmatter(power_md_content: str) -> str` that:
      - Parses YAML frontmatter (between `---` delimiters) from the provided string
      - Extracts the `version` field value
      - Validates it using existing `validate_version()` function
      - Returns the validated version string
      - Raises `VersionError` if frontmatter is missing, has no `version` field, or version is invalid
    - Use stdlib-only parsing (no PyYAML) — split on `---` delimiters, parse key-value pairs
    - Follow existing code style: type hints, Google-style docstring, `VersionError` for all error cases
    - Do NOT modify existing functions (`read_version`, `validate_version`, `format_version_display`, `parse_version`, `format_version`)
    - _Bug_Condition: Agent cannot access VERSION file in sandboxed workspace_
    - _Expected_Behavior: read_version_from_frontmatter(content) extracts and validates version from POWER.md frontmatter string_
    - _Preservation: All existing functions remain unchanged — new function is additive only_
    - _Requirements: 2.1, 2.2, 3.1, 3.4_

  - [x] 3.3 Update `onboarding-flow.md` Step 0c steering instructions
    - Edit `senzing-bootcamp/steering/onboarding-flow.md` section `## 0c. Version Display`
    - Replace instruction to read `senzing-bootcamp/VERSION` with instruction to extract version from POWER.md frontmatter `version` field (received during power activation)
    - Updated text should instruct the agent to:
      - Extract the version from the POWER.md frontmatter `version` field received during power activation
      - Display `Senzing Bootcamp Power vX.Y.Z` as the first onboarding output
      - Fall back to `⚠️ Could not determine power version.` if the version field is not present or cannot be parsed
      - Continue with onboarding — do NOT block on version errors
    - Remove reference to `version.py` script's logic (agent doesn't need to run scripts)
    - _Bug_Condition: steeringInstructs(readFile("senzing-bootcamp/VERSION")) — current instructions direct agent to inaccessible file_
    - _Expected_Behavior: Steering instructs agent to use POWER.md frontmatter version (always available via activation)_
    - _Preservation: Fallback warning message preserved; non-blocking behavior preserved_
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.3_

  - [x] 3.4 Add CI sync check for VERSION ↔ POWER.md frontmatter consistency
    - Edit `senzing-bootcamp/scripts/validate_power.py` (or create a new validation in the existing CI script)
    - Add a check that reads both `senzing-bootcamp/VERSION` and the `version` field from `senzing-bootcamp/POWER.md` frontmatter
    - Assert they match — fail CI if they drift apart
    - Use `read_version()` for the VERSION file and `read_version_from_frontmatter()` for POWER.md
    - _Bug_Condition: Version drift between VERSION file and POWER.md frontmatter would reintroduce display bugs_
    - _Expected_Behavior: CI catches any mismatch between the two version sources_
    - _Preservation: Existing validate_power.py checks remain unchanged — this is additive_
    - _Requirements: 3.2, 3.4_

  - [x] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - POWER.md Frontmatter Missing Version Field
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (version extractable from frontmatter)
    - Now that POWER.md has a `version` field and `read_version_from_frontmatter()` exists, the test should pass
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed — version is now extractable from POWER.md frontmatter)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Existing Version Functions Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — existing version functions unchanged)
    - Confirm `read_version()`, `validate_version()`, `format_version_display()`, `parse_version()`, `format_version()` all behave identically
    - Confirm VERSION file is unchanged
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest senzing-bootcamp/tests/test_version_frontmatter_properties.py -v`
  - Run existing version tests to confirm no regressions: `pytest senzing-bootcamp/tests/test_version_properties.py senzing-bootcamp/tests/test_version_unit.py -v`
  - Verify CI validation passes: `python3 senzing-bootcamp/scripts/validate_power.py`
  - Ensure all tests pass, ask the user if questions arise.
