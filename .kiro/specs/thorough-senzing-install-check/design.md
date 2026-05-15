# Thorough Senzing Install Check Bugfix Design

## Overview

The Module 2 SDK Setup steering file (`senzing-bootcamp/steering/module-02-sdk-setup.md`) has a defective Step 1 that only uses language-level import checks and package manager queries to detect an existing Senzing installation. These methods fail when `PYTHONPATH` is not configured or when package names don't match the `senzing-*` glob pattern, causing the agent to miss a valid installation at `/opt/senzing/er/` and proceed with unnecessary reinstallation.

The fix adds filesystem-based fallback checks for `/opt/senzing/er/lib/libSz.so` (native library) and `/opt/senzing/er/szBuildVersion.json` (build version file) to Step 1 of the steering file. These checks run when the language import check fails, providing a reliable detection path independent of environment variables and package manager metadata.

## Glossary

- **Bug_Condition (C)**: The condition where the Senzing SDK is installed at `/opt/senzing/er/` but the language import check and package manager query both fail to detect it (due to missing `PYTHONPATH` or non-matching package names)
- **Property (P)**: When filesystem sentinel files exist (`libSz.so` and `szBuildVersion.json`), the steering file instructs the agent to report the SDK as installed and skip reinstallation
- **Preservation**: Existing detection behavior (successful import check, genuine not-installed case, version-below-V4.0 upgrade path) must remain unchanged
- **Step 1**: The "Check for Existing Installation" step in `module-02-sdk-setup.md` that determines whether to install or skip
- **Sentinel files**: `/opt/senzing/er/lib/libSz.so` (native shared library) and `/opt/senzing/er/szBuildVersion.json` (build version metadata) — their presence reliably indicates a Senzing SDK installation

## Bug Details

### Bug Condition

The bug manifests when the Senzing SDK is physically installed at `/opt/senzing/er/` but the agent's detection logic fails to find it. The current Step 1 relies exclusively on a language-level import (e.g., `python3 -c "import senzing"`) and a package manager query (`dpkg -l senzing-*`). Both can fail even when the SDK is fully functional on disk.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type InstallCheckContext
  OUTPUT: boolean

  RETURN input.sdkExistsOnFilesystem == true
         AND fileExists("/opt/senzing/er/lib/libSz.so") == true
         AND fileExists("/opt/senzing/er/szBuildVersion.json") == true
         AND input.languageImportSucceeds == false
         AND input.packageManagerQuerySucceeds == false
END FUNCTION
```

### Examples

- **PYTHONPATH not set**: SDK installed at `/opt/senzing/er/`, `libSz.so` present, but `python3 -c "import senzing"` fails with `ModuleNotFoundError` because `PYTHONPATH` doesn't include the SDK's Python bindings path. Current behavior: agent concludes SDK is not installed. Expected: agent detects installation via filesystem check.
- **Non-standard package name**: SDK installed via a tarball or custom package named `senzingapi-runtime` instead of `senzing-*`. `dpkg -l senzing-*` returns no results. Current behavior: agent concludes SDK is not installed. Expected: agent detects installation via filesystem check.
- **Both checks fail together**: Neither import nor dpkg succeeds, but `/opt/senzing/er/lib/libSz.so` and `/opt/senzing/er/szBuildVersion.json` both exist. Current behavior: agent proceeds with full installation. Expected: agent reports SDK found and skips to verification.
- **Edge case — partial installation**: Only `libSz.so` exists but `szBuildVersion.json` is missing. Expected: agent does NOT conclude SDK is installed (both sentinel files required).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- When the language-level import check succeeds (SDK detected via import), the agent must continue to report the SDK as installed and skip reinstallation — the filesystem fallback is not needed
- When the SDK is genuinely not installed (no sentinel files on disk), the agent must continue to proceed with the full installation workflow (Steps 2-3)
- When the SDK is installed but the version is below V4.0, the agent must continue to recommend an upgrade rather than skipping installation
- Mouse/keyboard interaction patterns with the steering file are unaffected (this is a content change, not a UI change)

**Scope:**
All inputs where the language import check succeeds OR where the SDK is genuinely not installed should be completely unaffected by this fix. This includes:
- Environments where `PYTHONPATH` is correctly configured (import succeeds)
- Fresh machines with no Senzing installation
- Machines with incompatible (<V4.0) Senzing versions
- Non-Linux platforms where `/opt/senzing/er/` is not the installation path

## Hypothesized Root Cause

Based on the bug description, the root cause is a gap in the detection logic within the steering file's Step 1 instructions:

1. **No filesystem fallback path**: The steering file only instructs the agent to use language-level imports and package manager queries. There is no instruction to check the filesystem directly when these methods fail.

2. **Over-reliance on environment configuration**: The Python import check assumes `PYTHONPATH` or `sys.path` includes the SDK's binding directory. In container environments or fresh shells, this is often not the case even when the SDK is installed.

3. **Brittle package name matching**: The `dpkg -l senzing-*` glob assumes all Senzing packages start with `senzing-`. Alternative package names (e.g., `senzingapi-runtime`, `senzingapi-tools`) or non-dpkg installations (tarball, manual) are missed entirely.

4. **Single-strategy detection**: The current design uses an "either import works OR dpkg works" approach with no tertiary fallback. A defense-in-depth approach with filesystem checks would catch installations missed by both primary methods.

## Correctness Properties

Property 1: Bug Condition - Filesystem Fallback Detects Installed SDK

_For any_ install check context where the SDK is physically installed (both `/opt/senzing/er/lib/libSz.so` and `/opt/senzing/er/szBuildVersion.json` exist) but the language import check and package manager query both fail, the fixed Step 1 instructions SHALL direct the agent to check the filesystem sentinel files and report the SDK as already installed, skipping reinstallation steps.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - Existing Detection and Not-Installed Paths

_For any_ install check context where the bug condition does NOT hold (either the language import succeeds, or the SDK is genuinely not installed, or the version is below V4.0), the fixed Step 1 instructions SHALL produce the same agent behavior as the original instructions, preserving the existing detection-success path, the full-installation path, and the upgrade-recommendation path.

**Validates: Requirements 3.1, 3.2, 3.3**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-02-sdk-setup.md`

**Section**: Step 1: Check for Existing Installation

**Specific Changes**:

1. **Add filesystem fallback instructions**: After the existing language import check instruction, add a new paragraph instructing the agent to check for sentinel files on the filesystem if the import check fails.

2. **Define sentinel file paths**: Specify the two files to check:
   - `/opt/senzing/er/lib/libSz.so` (native shared library)
   - `/opt/senzing/er/szBuildVersion.json` (build version metadata)

3. **Require both files present**: The filesystem check should only conclude the SDK is installed if BOTH sentinel files exist. A partial installation (only one file) should not trigger the "already installed" path.

4. **Integrate with existing flow**: If the filesystem check succeeds, the agent should follow the same "SDK found" path as a successful import check — report the version (read from `szBuildVersion.json`), skip Steps 2-3, and proceed to Step 4 verification.

5. **Preserve ordering**: The filesystem check is a fallback — the language import check remains the primary detection method. The filesystem check only runs if the import check fails.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on the unfixed steering file content, then verify the fix works correctly and preserves existing behavior. Since the bug is in a Markdown steering file (not executable code), testing focuses on parsing the steering file content and verifying the presence and correctness of the filesystem fallback instructions.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that the current steering file lacks filesystem fallback instructions.

**Test Plan**: Parse the current `module-02-sdk-setup.md` Step 1 content and assert that filesystem-based detection instructions are present. Run on the UNFIXED file to observe failures confirming the gap.

**Test Cases**:
1. **Missing libSz.so check**: Assert Step 1 contains an instruction to check `/opt/senzing/er/lib/libSz.so` (will fail on unfixed file)
2. **Missing szBuildVersion.json check**: Assert Step 1 contains an instruction to check `/opt/senzing/er/szBuildVersion.json` (will fail on unfixed file)
3. **Missing fallback logic**: Assert Step 1 contains fallback language indicating filesystem checks run when import fails (will fail on unfixed file)
4. **Missing both-files-required condition**: Assert Step 1 specifies both sentinel files must exist (will fail on unfixed file)

**Expected Counterexamples**:
- The string `/opt/senzing/er/lib/libSz.so` does not appear in Step 1
- The string `szBuildVersion.json` does not appear in Step 1
- No fallback/filesystem detection logic exists in the current Step 1 instructions

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed steering file provides correct filesystem fallback instructions.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  step1_content := parseStep1(steering_file_fixed)
  ASSERT contains(step1_content, "/opt/senzing/er/lib/libSz.so")
  ASSERT contains(step1_content, "/opt/senzing/er/szBuildVersion.json")
  ASSERT contains(step1_content, fallback_trigger_language)
  ASSERT contains(step1_content, both_files_required_language)
  ASSERT step1_content preserves "skip Steps 2 and 3" outcome when files found
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed steering file produces the same agent behavior as the original.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT parseStep1(steering_file_original).importCheckLogic
         == parseStep1(steering_file_fixed).importCheckLogic
  ASSERT parseStep1(steering_file_original).sdkFoundBehavior
         == parseStep1(steering_file_fixed).sdkFoundBehavior
  ASSERT parseStep1(steering_file_original).sdkNotFoundBehavior
         == parseStep1(steering_file_fixed).sdkNotFoundBehavior
  ASSERT parseStep1(steering_file_original).versionCheckBehavior
         == parseStep1(steering_file_fixed).versionCheckBehavior
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It can generate many variations of steering file content to verify structural preservation
- It catches edge cases where the fix might accidentally alter unrelated instructions
- It provides strong guarantees that the import-success path and not-installed path remain unchanged

**Test Plan**: Parse the UNFIXED steering file to capture the existing Step 1 structure (import check instructions, SDK-found behavior, SDK-not-found behavior, version check behavior). Then write property-based tests verifying these elements are preserved in the fixed file.

**Test Cases**:
1. **Import check preservation**: Verify the language import check instruction remains as the primary detection method in the fixed file
2. **SDK-found path preservation**: Verify the "skip Steps 2 and 3" behavior when import succeeds is unchanged
3. **SDK-not-found path preservation**: Verify the "proceed with Step 2" behavior when SDK is genuinely absent is unchanged
4. **Version check preservation**: Verify the V4.0 version check and upgrade recommendation path is unchanged

### Unit Tests

- Test that the fixed steering file contains the filesystem fallback section in Step 1
- Test that both sentinel file paths are specified correctly
- Test that the fallback is positioned after the import check (ordering)
- Test that the "both files required" condition is explicit
- Test that `szBuildVersion.json` is referenced for version extraction

### Property-Based Tests

- Generate random steering file structures and verify the filesystem fallback section is always present in Step 1 after the import check
- Generate random combinations of sentinel file existence (both present, one missing, neither present) and verify the steering instructions produce correct outcomes for each
- Test across many input variations that the preserved sections (import-success path, not-installed path, upgrade path) remain structurally identical to the original

### Integration Tests

- Parse the full `module-02-sdk-setup.md` and verify Step 1 flows correctly from import check → filesystem fallback → appropriate next step
- Verify the checkpoint write instruction remains at the end of Step 1
- Verify cross-references to Steps 2, 3, and 4 remain consistent after the fix
