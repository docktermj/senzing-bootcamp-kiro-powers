# Implementation Plan: Windows Prerequisite Installation

## Overview

Add proactive Scoop and language runtime installation offers during the onboarding prerequisite check on Windows. Implementation spans two components: (1) a new `check_scoop()` function and `ScoopInstallInfo` dataclass in `preflight.py` for detection, and (2) new conditional installation logic in `onboarding-flow.md` Step 3 for the agent to offer and execute installations.

All code is Python 3.11+ stdlib only. Tests use pytest + Hypothesis in `senzing-bootcamp/tests/`.

## Tasks

- [x] 1. Add ScoopInstallInfo dataclass and SCOOP_RUNTIME_COMMANDS mapping to preflight.py
  - [x] 1.1 Create `ScoopInstallInfo` dataclass in `senzing-bootcamp/scripts/preflight.py`
    - Add `@dataclasses.dataclass` class with fields: `bucket_add: str | None`, `install_cmd: str`, `verify_cmd: str`
    - Place after the existing `PreflightReport` class
    - Include docstring explaining the purpose
    - _Requirements: 3.2, 6.1_

  - [x] 1.2 Create `SCOOP_RUNTIME_COMMANDS` constant mapping in `senzing-bootcamp/scripts/preflight.py`
    - Define `SCOOP_RUNTIME_COMMANDS: dict[str, ScoopInstallInfo]` with entries for java, dotnet, rust, nodejs
    - Java entry must include `bucket_add="scoop bucket add java"` and `install_cmd="scoop install java/temurin-lts-jdk"`
    - Other entries have `bucket_add=None` with their respective install and verify commands
    - _Requirements: 3.2, 6.1, 6.2_

  - [x] 1.3 Write property test for Property 2: Installation command mapping produces valid sequences
    - **Property 2: Installation command mapping produces valid sequences**
    - For any supported runtime name in SCOOP_RUNTIME_COMMANDS, verify: (a) `install_cmd` is non-empty and contains "scoop install", (b) `verify_cmd` is non-empty, (c) if runtime is "java" then `bucket_add` is non-empty and contains "scoop bucket add java", otherwise `bucket_add` may be None
    - Use `st.sampled_from(list(SCOOP_RUNTIME_COMMANDS.keys()))` strategy
    - Minimum 100 iterations with `@settings(max_examples=100)`
    - Create test file `senzing-bootcamp/tests/test_windows_prerequisite_installation.py`
    - **Validates: Requirements 3.2, 6.1**

- [x] 2. Implement check_scoop() function in preflight.py
  - [x] 2.1 Add `check_scoop()` function to `senzing-bootcamp/scripts/preflight.py`
    - Return type: `list[CheckResult]`
    - On non-Windows (`sys.platform != "win32"`): return empty list
    - On Windows with scoop on PATH (`shutil.which("scoop")`): return single CheckResult with status "pass", category "Package Manager", and version in message
    - On Windows without scoop: return single CheckResult with status "warn", category "Package Manager", fix message referencing `irm get.scoop.sh | iex`
    - Wrap in try/except to catch unexpected exceptions, returning a "warn" CheckResult with "Could not check for Scoop" message
    - Use `_get_version("scoop", ["--version"])` for version retrieval; handle failure gracefully with "version unknown"
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.2 Register `check_scoop` in `CheckRunner.CHECK_SEQUENCE`
    - Insert `("Package Manager", check_scoop)` between "Core Tools" and "Language Runtimes" in the CHECK_SEQUENCE list
    - _Requirements: 1.1_

  - [x] 2.3 Write property test for Property 1: Scoop detection is platform-conditional and status-correct
    - **Property 1: Scoop detection is platform-conditional and status-correct**
    - Mock `sys.platform` and `shutil.which` to test all branches
    - Use `st.sampled_from(["win32", "linux", "darwin"])` for platform and `st.booleans()` for scoop availability
    - Verify: (a) empty list when not win32, (b) single pass result with version when win32 + scoop available, (c) single warn result with non-empty fix when win32 + scoop unavailable
    - Minimum 100 iterations with `@settings(max_examples=100)`
    - Add to `senzing-bootcamp/tests/test_windows_prerequisite_installation.py`
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

  - [x] 2.4 Write unit tests for check_scoop() edge cases
    - Test: scoop command exists but `--version` fails → returns pass with "version unknown"
    - Test: unexpected exception in `shutil.which` → returns warn with graceful message
    - Test: CheckRunner includes scoop check in correct position (after Core Tools, before Language Runtimes)
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 3. Checkpoint — Verify preflight.py changes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Add Windows installation offer logic to onboarding-flow.md Step 3
  - [x] 4.1 Add Scoop installation offer conditional block to Step 3 in `senzing-bootcamp/steering/onboarding-flow.md`
    - After the existing WARN verdict handling, add a Windows-specific conditional block
    - IF platform is Windows AND scoop check status is "warn": offer Scoop installation with explanation of what Scoop is and why it's needed
    - Present clear "install now" and "skip for later" options
    - If accepted: execute `irm get.scoop.sh | iex` via PowerShell, verify with `scoop --version`, report result
    - If declined: proceed with existing WARN behavior, note Module 2 will handle it
    - If installation fails: display error output, suggest manual installation steps, proceed without blocking
    - Agent MUST NOT attempt installation without explicit bootcamper confirmation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.4_

  - [x] 4.2 Add runtime installation offer conditional block to Step 3 in `senzing-bootcamp/steering/onboarding-flow.md`
    - IF platform is Windows AND scoop is available AND chosen runtime check is "warn": offer runtime installation via Scoop
    - Reference `SCOOP_RUNTIME_COMMANDS` mapping for the correct install command
    - For Java: first run `scoop bucket add java`, handle bucket failure by suggesting Adoptium website
    - If accepted: execute the scoop install command, verify with the runtime's version command, report result
    - If declined: proceed with WARN behavior, note Module 2 will handle it
    - If installation fails: display error, suggest alternative methods, proceed without blocking
    - If scoop is not available AND bootcamper declined scoop installation: skip runtime offer entirely, defer to Module 2
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 6.1, 6.2, 6.3_

  - [x] 4.3 Add re-run preflight instruction after successful installations
    - After any successful installation (Scoop or runtime), instruct the agent to re-run `python3 senzing-bootcamp/scripts/preflight.py` to update the report verdict
    - Present updated report to bootcamper before proceeding
    - _Requirements: 4.5_

- [x] 5. Add preferences recording logic to onboarding-flow.md Step 3
  - [x] 5.1 Add preference recording instructions to the installation offer block
    - After successful Scoop installation: record `scoop_installed_during_onboarding: true` in `config/bootcamp_preferences.yaml`
    - After successful runtime installation: record runtime name and version under `runtimes_installed_during_onboarding` in `config/bootcamp_preferences.yaml`
    - When bootcamper declines installation: record `prerequisite_installation_deferred: true` in `config/bootcamp_preferences.yaml`
    - Do not overwrite existing preferences content; append/merge new keys
    - _Requirements: 5.1, 5.2, 5.4_

  - [x] 5.2 Add Module 2 skip-check instruction reference
    - Add a note in the steering file that Module 2 should check `config/bootcamp_preferences.yaml` for `runtimes_installed_during_onboarding` and `scoop_installed_during_onboarding` before re-installing
    - _Requirements: 5.3_

  - [x] 5.3 Write property test for Property 3: Preferences installation record round-trip
    - **Property 3: Preferences installation record round-trip**
    - Generate arbitrary preferences records with `scoop_installed_during_onboarding` (bool), `runtimes_installed_during_onboarding` (list of name/version dicts), and `prerequisite_installation_deferred` (bool)
    - Use `st.booleans()`, `st.lists(st.fixed_dictionaries({"name": st.sampled_from(["java", "dotnet", "rust", "nodejs"]), "version": st.from_regex(r"[0-9]+\.[0-9]+\.[0-9]+", fullmatch=True)}))` strategies
    - Serialize to YAML and deserialize, verify all fields preserved exactly
    - Minimum 100 iterations with `@settings(max_examples=100)`
    - Add to `senzing-bootcamp/tests/test_windows_prerequisite_installation.py`
    - **Validates: Requirements 5.1, 5.2, 5.4**

- [x] 6. Checkpoint — Verify steering file changes and preferences logic
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Write remaining tests for verdict invariance and structural validation
  - [x] 7.1 Write property test for Property 4: Verdict invariance under installation outcomes
    - **Property 4: Verdict invariance under installation outcomes**
    - Generate a PreflightReport with at least one "warn" CheckResult (simulating missing scoop/runtime)
    - Verify that the `verdict` property returns "WARN" regardless of any additional state
    - Confirm that no code path in `check_scoop()` or `SCOOP_RUNTIME_COMMANDS` can produce a "fail" status
    - Use `st.lists(st.fixed_dictionaries({"status": st.sampled_from(["pass", "warn"])}), min_size=1)` with at least one "warn"
    - Minimum 100 iterations with `@settings(max_examples=100)`
    - Add to `senzing-bootcamp/tests/test_windows_prerequisite_installation.py`
    - **Validates: Requirements 4.2**

  - [x] 7.2 Write unit tests for steering file structural validation
    - Test: `onboarding-flow.md` Step 3 contains Scoop installation offer conditional
    - Test: `onboarding-flow.md` Step 3 contains `irm get.scoop.sh | iex` PowerShell command
    - Test: `onboarding-flow.md` Step 3 contains decline/skip path language
    - Test: `onboarding-flow.md` Step 3 contains re-run preflight instruction after installation
    - Test: `onboarding-flow.md` Step 3 contains preferences recording instructions
    - Test: `onboarding-flow.md` Step 3 references `SCOOP_RUNTIME_COMMANDS` or lists all four runtimes
    - _Requirements: 2.1, 2.2, 2.4, 3.1, 4.5, 5.1_

  - [x] 7.3 Write unit test for check_scoop() integration with CheckRunner
    - Mock platform as win32, mock `shutil.which("scoop")` returning a path
    - Run `CheckRunner().run()` and verify scoop check appears after "Core Tools" checks and before "Language Runtimes" checks
    - _Requirements: 1.1_

- [x] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Verify existing `test_preflight.py` and `test_preflight_check.py` tests still pass after changes

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The feature spans two file types: Python script (`preflight.py`) and steering markdown (`onboarding-flow.md`)
- All error paths are non-blocking — installation failures never escalate the verdict to FAIL
- Python 3.11+ stdlib only for script code; pytest + Hypothesis for test framework
