# Windows Scoop SUPPORTPATH Fix — Bugfix Design

## Overview

On Windows with a Scoop-installed Senzing SDK, the agent blindly uses `$SENZING_DIR\data` as SUPPORTPATH during engine configuration (Step 8). In the Scoop package layout, `SENZING_DIR` points to the `er` subdirectory, and the `data` directory lives one level up at the Scoop app version root (`$SENZING_DIR\..\data`). This causes SENZ2027 at engine initialization. The fix adds a path verification fallback to the `module-02-sdk-setup.md` steering file's Step 8 so the agent checks the standard path first, then falls back to the parent directory on Windows when the standard path doesn't exist.

## Glossary

- **Bug_Condition (C)**: The agent is on Windows with a Scoop-installed SDK where `$SENZING_DIR\data` does not exist, but `$SENZING_DIR\..\data` does
- **Property (P)**: The agent sets SUPPORTPATH to the verified existing `data` directory path on the first attempt, avoiding SENZ2027
- **Preservation**: Non-Windows platforms and standard Windows installs (where `$SENZING_DIR\data` exists) continue to use the MCP-returned path unmodified
- **SENZING_DIR**: The SDK installation directory; on Scoop this is the `er` subdirectory within the Scoop app folder (e.g., `C:\Users\<user>\scoop\apps\senzing\current\er`)
- **SUPPORTPATH**: Engine configuration path pointing to the directory containing `g2SifterRules.ibm` and other GNR support files
- **SENZ2027**: Senzing error code for "Plugin initialization error... GNR data files failed to load" — triggered when SUPPORTPATH points to a non-existent or empty directory
- **Scoop app version root**: The parent of `er` in a Scoop install (e.g., `C:\Users\<user>\scoop\apps\senzing\current\`)

## Bug Details

### Bug Condition

The bug manifests when the agent configures the Senzing engine on Windows with a Scoop-installed SDK. The `sdk_guide(topic='configure')` MCP tool returns a configuration JSON with SUPPORTPATH set to `$SENZING_DIR\data`. In the Scoop package layout, this path does not exist because the `data` directory is at `$SENZING_DIR\..\data` (one level above the `er` directory). The steering file's Step 8 instructs the agent to save the MCP-returned JSON directly without verifying paths exist.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type EngineConfigContext
  OUTPUT: boolean

  RETURN input.platform == 'windows'
         AND input.installMethod == 'scoop'
         AND NOT directoryExists(input.senzingDir + '\data')
         AND directoryExists(input.senzingDir + '\..\data')
         AND steeringStep8UsesPathWithoutVerification()
END FUNCTION
```

### Examples

- **Example 1**: Agent on Windows, Scoop install, `SENZING_DIR=C:\Users\dev\scoop\apps\senzing\current\er`. MCP returns SUPPORTPATH=`C:\Users\dev\scoop\apps\senzing\current\er\data`. Path does not exist. Engine fails with SENZ2027. **Expected**: Agent detects missing path, checks `C:\Users\dev\scoop\apps\senzing\current\data`, finds it, uses it.
- **Example 2**: Agent on Windows, Scoop install, `SENZING_DIR=C:\Users\dev\scoop\apps\senzing\0.4.0\er`. MCP returns SUPPORTPATH ending in `er\data`. Path does not exist. **Expected**: Agent falls back to `C:\Users\dev\scoop\apps\senzing\0.4.0\data`.
- **Example 3**: Agent on Windows, MSI install, `SENZING_DIR=C:\Program Files\Senzing\er`. MCP returns SUPPORTPATH=`C:\Program Files\Senzing\er\data`. Path exists. **Expected**: Agent uses it directly — no fallback needed.
- **Example 4**: Agent on Linux, `SENZING_DIR=/opt/senzing/er`. MCP returns SUPPORTPATH=`/opt/senzing/data`. Path exists. **Expected**: Agent uses it directly — no Windows-specific logic triggered.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Linux and macOS engine configuration must continue to use the MCP-returned SUPPORTPATH without modification
- Windows installs where `$SENZING_DIR\data` exists must continue to use that path directly
- The `sdk_guide` MCP tool call remains the starting point for all engine configuration
- Step 9 (database connection test) proceeds unchanged after successful engine initialization
- The "NEVER construct engine configuration JSON manually" instruction remains in force
- All other Step 8 behavior (saving to `config/engine_config.json`, using `sdk_guide` with correct parameters) is unchanged

**Scope:**
All inputs that do NOT involve Windows + Scoop + missing `$SENZING_DIR\data` should be completely unaffected by this fix. This includes:
- All Linux/macOS configurations
- Windows configurations where `$SENZING_DIR\data` exists (MSI, manual installs)
- All other steps in Module 2 (Steps 1–7, Step 9)
- Engine configuration fields other than SUPPORTPATH (CONFIGPATH, RESOURCEPATH, SQL)

## Hypothesized Root Cause

Based on the bug description, the root cause is:

1. **Missing path verification in steering instructions**: Step 8 of `module-02-sdk-setup.md` instructs the agent to "Save the MCP-returned JSON directly to `config/engine_config.json` — do not modify the paths." This blanket instruction prevents the agent from verifying that SUPPORTPATH actually exists before using it.

2. **Scoop package layout diverges from standard**: The unofficial Scoop package places `SENZING_DIR` at the `er` subdirectory, but puts the `data` directory at the app version root (sibling to `er`, not child of `er`). The MCP server's `sdk_guide` tool assumes the standard layout where `data` is under `SENZING_DIR`.

3. **No Windows-specific path validation guidance**: The steering file has no conditional logic for Windows Scoop installs. It treats all platforms uniformly after the MCP call, with no fallback for non-standard directory layouts.

4. **Agent lacks proactive verification**: Without explicit steering instructions to verify paths exist, the agent trusts the MCP-returned paths and only discovers the problem after SENZ2027 occurs at runtime.

## Correctness Properties

Property 1: Bug Condition — SUPPORTPATH Fallback on Windows Scoop

_For any_ engine configuration context where the platform is Windows, the install method is Scoop, and `$SENZING_DIR\data` does not exist, the fixed steering file SHALL instruct the agent to check `$SENZING_DIR\..\data` as a fallback and use that path as SUPPORTPATH when it exists, enabling successful engine initialization without SENZ2027 errors.

**Validates: Requirements 2.1, 2.2, 2.3**

Property 2: Preservation — Non-Scoop Configurations Unchanged

_For any_ engine configuration context where the platform is NOT Windows, OR where the platform is Windows but `$SENZING_DIR\data` exists (non-Scoop or standard layout), the fixed steering file SHALL produce the same agent behavior as the original — using the MCP-returned SUPPORTPATH directly without modification, preserving all existing configuration logic.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `senzing-bootcamp/steering/module-02-sdk-setup.md`

**Section**: Step 8 — Create Engine Configuration

**Specific Changes**:

1. **Add Windows SUPPORTPATH verification block**: After the existing instruction to use `sdk_guide(topic='configure')`, add a conditional block that instructs the agent to verify SUPPORTPATH exists on Windows before saving the configuration. If `$SENZING_DIR\data` does not exist, check `$SENZING_DIR\..\data`.

2. **Add Scoop layout fallback logic**: Include explicit instructions for the agent to:
   - Check if the platform is Windows
   - Verify the SUPPORTPATH directory from the MCP response actually exists
   - If it doesn't exist, compute the parent-level path (`$SENZING_DIR\..\data`)
   - If the parent-level path exists, update SUPPORTPATH in the configuration JSON
   - If neither path exists, report the error clearly to the bootcamper

3. **Add verification command**: Include a platform-appropriate command the agent should run to verify the path exists (e.g., `Test-Path` on PowerShell or `if exist` on cmd).

4. **Preserve the "never construct manually" rule**: The new instructions must clarify that this is a targeted path correction based on filesystem verification, not manual construction of the configuration JSON. The MCP-returned JSON remains the starting point.

5. **Add informational note about Scoop layout**: Include a brief note explaining why the Scoop package has a different layout, so the agent can explain to the bootcamper if needed.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (the steering file lacks path verification), then verify the fix works correctly and preserves existing behavior. Since this is a steering file fix, tests parse the markdown content to verify the presence or absence of specific instructions.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that Step 8 currently lacks SUPPORTPATH verification logic for Windows Scoop installs.

**Test Plan**: Parse `module-02-sdk-setup.md`, extract the Step 8 section, and assert it contains path verification instructions for SUPPORTPATH on Windows. Run these tests on the UNFIXED code to observe failures confirming the bug.

**Test Cases**:
1. **Missing Path Verification Test**: Assert Step 8 contains instructions to verify SUPPORTPATH exists on Windows (will fail on unfixed code)
2. **Missing Fallback Logic Test**: Assert Step 8 contains fallback to `$SENZING_DIR\..\data` when standard path doesn't exist (will fail on unfixed code)
3. **Missing Scoop Layout Note Test**: Assert Step 8 mentions Scoop package layout or non-standard directory structure (will fail on unfixed code)
4. **Missing Verification Command Test**: Assert Step 8 includes a filesystem check command like `Test-Path` or directory existence verification (will fail on unfixed code)

**Expected Counterexamples**:
- Step 8 contains no path verification logic — it instructs the agent to save MCP-returned JSON directly
- No mention of Scoop, fallback paths, or `$SENZING_DIR\..\data` in Step 8
- Possible cause: steering file was written assuming all platforms have standard directory layouts

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (Windows + Scoop + missing standard path), the fixed steering file contains instructions that guide the agent to the correct SUPPORTPATH.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  step8_content := extractStep8(steeringFile)
  ASSERT containsPathVerification(step8_content, 'SUPPORTPATH')
  ASSERT containsFallbackPath(step8_content, '$SENZING_DIR\..\data')
  ASSERT containsWindowsConditional(step8_content)
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed steering file preserves existing behavior — the MCP-returned paths are still the starting point, non-Windows platforms are unaffected, and the "never construct manually" rule remains.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  step8_content := extractStep8(steeringFile)
  ASSERT containsMCPAsStartingPoint(step8_content)
  ASSERT containsNeverConstructManually(step8_content)
  ASSERT fallbackIsConditionalOnWindows(step8_content)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many variations of platform/install-method combinations to verify the conditional logic is properly scoped
- It catches edge cases where the fix might accidentally apply to non-Windows platforms
- It provides strong guarantees that existing instructions remain intact

**Test Plan**: Observe behavior on UNFIXED code first — confirm that the "never construct manually" rule, MCP-first approach, and platform-agnostic instructions exist. Then write property-based tests to verify these are preserved after the fix.

**Test Cases**:
1. **MCP Starting Point Preserved**: Verify Step 8 still instructs using `sdk_guide(topic='configure')` as the starting point for engine configuration
2. **Never Construct Manually Preserved**: Verify the "NEVER construct engine configuration JSON manually" instruction remains in Step 8
3. **Non-Windows Unaffected**: Verify the fallback logic is explicitly scoped to Windows only (conditional on platform)
4. **Step 9 Flow Preserved**: Verify Step 9 (database connection test) follows Step 8 without additional gates or verification steps

### Unit Tests

- Parse Step 8 and verify presence of SUPPORTPATH verification keywords
- Parse Step 8 and verify presence of fallback path pattern (`\..\data` or parent directory)
- Parse Step 8 and verify the Windows-conditional scoping of the fallback
- Verify the "never construct manually" instruction is preserved
- Verify `sdk_guide` MCP call instruction is preserved

### Property-Based Tests

- Generate random platform/install-method combinations and verify the fallback logic only triggers for Windows + missing standard path
- Generate random Step 8 section variants and verify preservation markers (MCP-first, never-construct-manually) are always present
- Test that the fix instructions are properly scoped with Windows-only conditionals across many generated scenarios

### Integration Tests

- Parse the full `module-02-sdk-setup.md` and verify Step 8 flows correctly into Step 9
- Verify the Agent Behavior section at the bottom of the file still contains the "NEVER construct engine configuration JSON manually" rule
- Verify the Error Handling section still references SENZ2027 and `explain_error_code`
