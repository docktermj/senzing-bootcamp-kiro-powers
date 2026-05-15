# Power Version Display Bugfix Design

## Overview

The agent cannot read `senzing-bootcamp/VERSION` in Kiro-sandboxed workspaces because only steering files and the MCP server are exposed — the `VERSION` file and Python scripts inside `senzing-bootcamp/` are not accessible to the agent at runtime. This causes onboarding Step 0c to always fall back to "⚠️ Could not determine power version."

The fix adds a `version` field to the POWER.md YAML frontmatter. Since POWER.md content is delivered to the agent during power activation (the `overview` field in the activate response), the agent can parse the version from frontmatter metadata that it already receives — no file system access required. The `VERSION` file remains the single source of truth for programmatic/CI access, and a CI check ensures the two stay in sync.

## Glossary

- **Bug_Condition (C)**: The agent executes onboarding Step 0c in a Kiro-sandboxed workspace where `senzing-bootcamp/VERSION` is not accessible via file system reads
- **Property (P)**: The agent successfully retrieves and displays the version string "Senzing Bootcamp Power vX.Y.Z" using POWER.md frontmatter data received during activation
- **Preservation**: Existing CI scripts, `version.py`, and non-sandboxed workflows that read `VERSION` directly continue to function unchanged
- **POWER.md frontmatter**: The YAML metadata block at the top of `senzing-bootcamp/POWER.md` — delivered to the agent as part of the power activation `overview` response
- **`onboarding-flow.md`**: The steering file at `senzing-bootcamp/steering/onboarding-flow.md` that defines Step 0c version display instructions
- **`version.py`**: The script at `senzing-bootcamp/scripts/version.py` that reads and validates the VERSION file for CLI/CI use

## Bug Details

### Bug Condition

The bug manifests when the agent executes onboarding Step 0c in a Kiro-sandboxed workspace. The current steering instructions tell the agent to "read the power version from `senzing-bootcamp/VERSION` using the `version.py` script's logic," but in sandboxed environments the agent cannot access files inside the `senzing-bootcamp/` directory tree — only steering file content and MCP tool responses are available.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type OnboardingContext
  OUTPUT: boolean
  
  RETURN input.currentStep == "0c"
         AND input.environment == "kiro-sandboxed"
         AND NOT fileAccessible("senzing-bootcamp/VERSION")
         AND steeringInstructs(readFile("senzing-bootcamp/VERSION"))
END FUNCTION
```

### Examples

- **Sandboxed workspace, Step 0c**: Agent tries to read `senzing-bootcamp/VERSION`, file is not accessible, displays "⚠️ Could not determine power version" — bootcamper never sees version. **Expected**: Agent parses version from POWER.md frontmatter received during activation and displays "Senzing Bootcamp Power v0.11.0".
- **Sandboxed workspace, version.py execution**: Agent tries to run `python3 senzing-bootcamp/scripts/version.py`, script is not accessible, falls back to warning. **Expected**: No script execution needed — version comes from already-available POWER.md metadata.
- **Non-sandboxed workspace, Step 0c**: Agent can read `senzing-bootcamp/VERSION` directly and displays version correctly. **Expected**: Same correct behavior — POWER.md frontmatter provides the same version string, so the fix works in both environments.
- **POWER.md frontmatter missing version field**: Agent cannot find version in frontmatter. **Expected**: Falls back to "⚠️ Could not determine power version" (graceful degradation preserved).

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- The `VERSION` file at `senzing-bootcamp/VERSION` remains the single source of truth for programmatic access (CI, scripts, `version.py`)
- `version.py` continues to read from the `VERSION` file and validate/format version strings for CLI use
- CI validation (`validate_power.py`) continues to check the `VERSION` file format
- The fallback warning "⚠️ Could not determine power version" continues to display when version cannot be determined from any source
- All onboarding steps after 0c (MCP health check, directory setup, hook installation, language selection, prerequisite check, welcome banner, track selection) execute in their existing order and behavior
- Non-sandboxed workspaces continue to work (the fix is additive, not a replacement of file-based access)

**Scope:**
All inputs that do NOT involve the agent attempting to read the version during onboarding Step 0c should be completely unaffected by this fix. This includes:
- CI pipeline version validation (reads `VERSION` file directly)
- Script-based version access (`version.py` CLI)
- All other onboarding steps (0, 0b, 1, 1b, 2, 3, 4, 5)
- Module steering file loading and execution
- MCP tool interactions

## Hypothesized Root Cause

Based on the bug description, the root cause is an architectural mismatch between the version source and the agent's sandbox constraints:

1. **Inaccessible File Path**: The steering instructions in `onboarding-flow.md` Step 0c direct the agent to read `senzing-bootcamp/VERSION`, but in Kiro Power sandboxed environments, the agent only receives steering file content and MCP responses — it cannot perform arbitrary file reads into the power's source tree.

2. **No Alternative Source Provided**: The original design assumed the agent would always have file system access to the power's directory. No fallback source was provided that works within sandbox constraints.

3. **Version Not Embedded in Agent-Accessible Content**: The POWER.md file (which IS delivered to the agent during activation) does not currently include the version in its YAML frontmatter. The "What's New in X.Y.Z" section headers contain version numbers, but parsing release notes headers is fragile and may not reflect the current version (the "Unreleased" section sits above the latest numbered release).

4. **Script Execution Not Available**: The steering instructions reference "using the `version.py` script's logic," but the agent cannot execute Python scripts from the power's `scripts/` directory in sandboxed environments.

## Correctness Properties

Property 1: Bug Condition - Version Retrieved from POWER.md Frontmatter

_For any_ onboarding context where the agent executes Step 0c and the POWER.md frontmatter contains a valid `version` field (MAJOR.MINOR.PATCH format), the updated steering instructions SHALL direct the agent to extract the version from the POWER.md frontmatter metadata (received during power activation) and display "Senzing Bootcamp Power vX.Y.Z" regardless of whether the `VERSION` file is accessible.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation - CI and Script Version Access Unchanged

_For any_ invocation of `version.py`, `validate_power.py`, or other CI/script tooling that reads the `VERSION` file directly, the fix SHALL produce exactly the same behavior as before — the `VERSION` file remains the authoritative source for programmatic access, and no existing script behavior is altered.

**Validates: Requirements 3.1, 3.2, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/POWER.md`

**Change**: Add `version` field to YAML frontmatter

**Specific Changes**:
1. **Add version to frontmatter**: Add `version: "0.11.0"` to the POWER.md YAML frontmatter block. This field is delivered to the agent as part of the power activation overview, making it always accessible regardless of sandbox constraints.

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

---

**File**: `senzing-bootcamp/steering/onboarding-flow.md`

**Section**: `## 0c. Version Display`

**Specific Changes**:
2. **Update Step 0c instructions**: Replace the instruction to read `senzing-bootcamp/VERSION` with an instruction to extract the version from the POWER.md frontmatter metadata that the agent received during power activation. The agent already has this content in its context — no file read is needed.

   Updated steering text:
   ```markdown
   ## 0c. Version Display

   Extract the power version from the POWER.md frontmatter `version` field
   (received during power activation) and display it to the bootcamper:

   ```text
   Senzing Bootcamp Power v0.11.0
   ```

   This is automatic — no user interaction is required. Display the version
   as the first onboarding output before proceeding.

   If the version field is not present in the POWER.md frontmatter or cannot
   be parsed, display:

   ```text
   ⚠️ Could not determine power version.
   ```

   Then continue with the onboarding sequence — do NOT block on version errors.
   ```

---

**File**: `senzing-bootcamp/scripts/validate_power.py` (or equivalent CI validation)

**Specific Changes**:
3. **Add frontmatter-VERSION sync check**: Add a CI validation step that parses the `version` field from POWER.md frontmatter and asserts it matches the content of the `VERSION` file. This ensures the two sources never drift apart.

---

**File**: `senzing-bootcamp/scripts/version.py`

**Specific Changes**:
4. **Add `read_version_from_frontmatter()` function**: Add a utility function that can parse the version from POWER.md frontmatter content (a string). This provides a reusable validation path for CI to compare frontmatter version against the VERSION file. The function accepts a string (the frontmatter content) and returns the validated version string.

   ```python
   def read_version_from_frontmatter(power_md_content: str) -> str:
       """Extract and validate version from POWER.md frontmatter content.

       Args:
           power_md_content: The full text content of POWER.md.

       Returns:
           The validated version string.

       Raises:
           VersionError: If frontmatter is missing, has no version field,
               or the version string is invalid.
       """
   ```

5. **No changes to existing functions**: `read_version()`, `validate_version()`, `format_version_display()`, `parse_version()`, and `format_version()` remain unchanged. The `VERSION` file remains the primary source for script/CI use.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate the agent's perspective in a sandboxed environment — attempt to read `senzing-bootcamp/VERSION` from a context where only POWER.md content is available. Run these tests on the UNFIXED code to observe failures.

**Test Cases**:
1. **Missing frontmatter version**: Parse current POWER.md frontmatter — confirm no `version` field exists (will demonstrate the bug condition)
2. **Steering instruction mismatch**: Verify that `onboarding-flow.md` Step 0c references `senzing-bootcamp/VERSION` file path (confirms the agent is directed to an inaccessible resource)
3. **No alternative source**: Confirm that no agent-accessible source (steering files, POWER.md frontmatter) currently contains the version string in a parseable location
4. **Frontmatter parsing on current POWER.md**: Attempt to extract version from current POWER.md frontmatter — will fail because the field doesn't exist

**Expected Counterexamples**:
- POWER.md frontmatter has no `version` field — agent cannot extract version from activation data
- Possible causes: version was only stored in `VERSION` file, POWER.md frontmatter was not designed as a version source

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := read_version_from_frontmatter(power_md_content)
  ASSERT result == VERSION_file_content
  ASSERT format_version_display(result) == "Senzing Bootcamp Power v" + result
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT read_version(VERSION_FILE_PATH) == read_version_original(VERSION_FILE_PATH)
  ASSERT validate_version(input) == validate_version_original(input)
  ASSERT format_version_display(input) == format_version_display_original(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many version string variants to verify validation behavior is unchanged
- It catches edge cases in frontmatter parsing that manual tests might miss
- It provides strong guarantees that existing `version.py` functions remain unaffected

**Test Plan**: Observe behavior on UNFIXED code first for `read_version()`, `validate_version()`, and `format_version_display()`, then write property-based tests capturing that behavior continues after adding `read_version_from_frontmatter()`.

**Test Cases**:
1. **VERSION file read preservation**: Verify `read_version()` continues to read from `VERSION` file correctly after the fix
2. **Validation preservation**: Verify `validate_version()` accepts/rejects the same inputs as before
3. **Display format preservation**: Verify `format_version_display()` produces identical output for all valid version strings
4. **CI script preservation**: Verify `validate_power.py` continues to validate the `VERSION` file

### Unit Tests

- Test `read_version_from_frontmatter()` with valid POWER.md content containing a version field
- Test `read_version_from_frontmatter()` with missing frontmatter (no `---` delimiters)
- Test `read_version_from_frontmatter()` with frontmatter missing the `version` field
- Test `read_version_from_frontmatter()` with invalid version format in frontmatter
- Test `read_version_from_frontmatter()` with extra whitespace, quotes, and edge cases
- Test that the VERSION file and POWER.md frontmatter version match (sync check)
- Test existing `read_version()` behavior is unchanged

### Property-Based Tests

- Generate random valid semver strings (MAJOR.MINOR.PATCH with components 0–99), embed them in synthetic POWER.md frontmatter, and verify `read_version_from_frontmatter()` extracts and validates them correctly
- Generate random invalid version strings and verify `read_version_from_frontmatter()` raises `VersionError` with appropriate messages
- Generate random POWER.md content (with and without frontmatter, with and without version field) and verify graceful handling of all variants
- Generate random valid version strings and verify `read_version()` (file-based) behavior is unchanged — round-trip through `validate_version` and `format_version_display` produces consistent results

### Integration Tests

- Test full onboarding Step 0c flow: POWER.md with version in frontmatter → agent extracts version → displays formatted string
- Test CI sync validation: VERSION file content matches POWER.md frontmatter version field
- Test graceful degradation: POWER.md without version field → warning message displayed → onboarding continues
- Test that `validate_power.py` catches version drift between VERSION file and POWER.md frontmatter
