# Bugfix Requirements Document

## Introduction

The Module 2 (SDK Setup) verification hook `senzing-bootcamp/hooks/verify-sdk-setup.kiro.hook` runs after edits to configuration or database files. When verification fails, its failure-guidance text instructs the bootcamper to run `python3 senzing-bootcamp/scripts/preflight.py` as a remediation fallback.

That path does not resolve from the bootcamper's project workspace. The `preflight.py` script exists inside the power repository, but the hook prompt executes in the bootcamper's installed project, where the power lives elsewhere and the path `senzing-bootcamp/scripts/preflight.py` does not exist. A bootcamper who follows the suggestion gets a "No such file or directory" error, turning the remediation step into a dead end. This erodes trust in the guidance precisely when the bootcamper is already dealing with a verification failure.

The verification logic itself is correct (it properly detects missing `database/G2C.db` and `config/engine_config.json` as expected at step 7). The defect is isolated to the recommended remediation command path in the failure-guidance text. The script the bootcamper actually has in their workspace is the generated `src/scripts/verify_sdk.py`.

## Bug Analysis

### Current Behavior (Defect)

When verification fails, the hook recommends a remediation command that points to a script path that does not resolve in the bootcamper's project workspace.

1.1 WHEN the verification hook reports a failure THEN the system suggests running `python3 senzing-bootcamp/scripts/preflight.py`, a path that does not resolve from the bootcamper's project workspace
1.2 WHEN the bootcamper follows the suggested remediation command THEN the system produces a "No such file or directory" error, leaving the bootcamper at a dead end with no working remediation path

### Expected Behavior (Correct)

When verification fails, the hook recommends a remediation command that references a script that exists and resolves in the bootcamper's workspace.

2.1 WHEN the verification hook reports a failure THEN the system SHALL suggest a remediation command whose script path exists and resolves within the bootcamper's project workspace (e.g., `src/scripts/verify_sdk.py`)
2.2 WHEN the bootcamper follows the suggested remediation command THEN the system SHALL invoke a script that exists, avoiding a "No such file or directory" dead end

### Unchanged Behavior (Regression Prevention)

The verification detection and reporting behavior must be preserved exactly. Only the recommended remediation path changes.

3.1 WHEN a configuration or database file is modified and the bootcamper is in Module 2 THEN the system SHALL CONTINUE TO run the verification, checking that `database/G2C.db` exists and is accessible and that the Senzing engine can initialize with the current config
3.2 WHEN verification detects a genuine failure (e.g., missing `database/G2C.db` or `config/engine_config.json`) THEN the system SHALL CONTINUE TO detect and present that error correctly
3.3 WHEN a configuration or database file is modified and the bootcamper is NOT in Module 2 THEN the system SHALL CONTINUE TO produce no output
3.4 WHEN the hook trigger conditions are evaluated THEN the system SHALL CONTINUE TO trigger on edits to `config/senzing_config.*`, `config/bootcamp_preferences.yaml`, and `database/*.*`

## Bug Condition Derivation

### Bug Condition Function

Identifies the input/state that triggers the bug. Here the relevant input `X` is the failure-guidance text emitted by the hook on a verification failure.

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type FailureGuidanceText
  OUTPUT: boolean

  // True when the recommended remediation command references a script
  // path that does not resolve from the bootcamper's project workspace
  RETURN X.recommendsCommand
     AND NOT pathResolvesInBootcamperWorkspace(X.recommendedScriptPath)
END FUNCTION
```

Concrete instance: the current prompt recommends `python3 senzing-bootcamp/scripts/preflight.py`, and `senzing-bootcamp/scripts/preflight.py` does not resolve in the bootcamper's workspace, so `isBugCondition` returns true.

### Fix Property (Fix Checking)

Defines the correct behavior for buggy inputs: the recommended remediation path must resolve in the bootcamper's workspace.

```pascal
// Property: Fix Checking - Remediation path resolves
FOR ALL X WHERE isBugCondition(X) DO
  result ← emitFailureGuidance'(X)
  ASSERT result.recommendsCommand
     AND pathResolvesInBootcamperWorkspace(result.recommendedScriptPath)
END FOR
```

Concrete expectation: after the fix, the failure-guidance text recommends a script that exists in the bootcamper's workspace (e.g., `src/scripts/verify_sdk.py`), so following the suggestion does not produce a "No such file or directory" error.

### Preservation Property (Preservation Checking)

For all inputs that do not trigger the bug, the fixed hook behaves identically to the original. This includes the trigger patterns, the Module 2 gating, the verification checks performed, and the correct detection/reporting of genuine failures.

```pascal
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Where:
- **F**: the original hook behavior (before the fix)
- **F'**: the fixed hook behavior (after updating the recommended remediation path)
