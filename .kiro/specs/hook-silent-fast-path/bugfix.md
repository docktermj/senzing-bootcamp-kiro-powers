# Bugfix Requirements Document

## Introduction

The consolidated `write-policy-gate` preToolUse hook produces visible clutter in the bootcamper's chat when its fast path passes. After the hook fires, the agent narrates its internal evaluation reasoning (e.g., "Fast path passes — inside working directory, not .question_pending, no SQL patterns targeting Senzing DB. Proceeding:") before executing the write. The hook prompt explicitly instructs "Do not acknowledge. Do not explain. Do not print anything. Proceed silently." but the agent does not honor this directive. The fix must ensure the agent produces zero visible output when the write-policy-gate fast path passes.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `write-policy-gate` hook fires on a write operation and the target path is inside the working directory and does not end with `.question_pending` and the content does not contain SQL patterns targeting Senzing database indicators THEN the system narrates its fast-path evaluation reasoning as visible chat output before proceeding with the write

1.2 WHEN multiple write operations occur in sequence and each passes the fast path gate THEN the system outputs its internal reasoning for each invocation, producing repeated visible clutter in the bootcamper's conversation

1.3 WHEN the `write-policy-gate` hook's fast path passes THEN the system prefixes the write execution with explanatory text such as "Fast path passes — inside working directory, not .question_pending, no SQL patterns targeting Senzing DB. Proceeding:" despite the prompt explicitly stating "Do not acknowledge. Do not explain. Do not print anything. Proceed silently."

### Expected Behavior (Correct)

2.1 WHEN the `write-policy-gate` hook fires on a write operation and the target path is inside the working directory and does not end with `.question_pending` and the content does not contain SQL patterns targeting Senzing database indicators THEN the system SHALL produce no visible output and silently allow the write to proceed

2.2 WHEN multiple write operations occur in sequence and each passes the fast path gate THEN the system SHALL produce zero visible output for any of the passing checks and silently allow each write to proceed

2.3 WHEN the `write-policy-gate` hook's fast path passes THEN the system SHALL honor the "Do not acknowledge. Do not explain. Do not print anything. Proceed silently." directive by producing exactly zero characters of visible chat output

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the `write-policy-gate` hook fires and the content contains SQL patterns targeting Senzing database indicators THEN the system SHALL CONTINUE TO block the write and produce visible output explaining the prohibition and suggesting SDK alternatives

3.2 WHEN the `write-policy-gate` hook fires and the target path ends with `.question_pending` and the question content violates the single-question rules THEN the system SHALL CONTINUE TO block the write and produce visible output with the compound question violation and rewrite instructions

3.3 WHEN the `write-policy-gate` hook fires and the target path is outside the working directory THEN the system SHALL CONTINUE TO block the write and produce visible output instructing the agent to use project-relative equivalents

3.4 WHEN the `write-policy-gate` hook fires and feedback content is being written to a path other than `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` THEN the system SHALL CONTINUE TO block the write and produce visible output redirecting to the correct feedback file

3.5 WHEN the `write-policy-gate` hook fires and file content references external paths like `/tmp/` or `%TEMP%` THEN the system SHALL CONTINUE TO block the write and produce visible output requiring replacement with project-relative equivalents

3.6 WHEN the `write-policy-gate` hook fires and the target path ends with `.question_pending` and the question content passes all single-question rules THEN the system SHALL CONTINUE TO silently allow the write to proceed with no visible output

---

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type HookInvocation (hook_name, target_path, content)
  OUTPUT: boolean

  // Returns true when the write-policy-gate hook fires and the fast path passes
  RETURN X.hook_name = "write-policy-gate"
         AND X.target_path IS INSIDE working_directory
         AND NOT endsWith(X.target_path, ".question_pending")
         AND NOT (containsSqlPatterns(X.content) AND containsSenzingDbIndicators(X.content))
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — Zero visible output when fast path passes
FOR ALL X WHERE isBugCondition(X) DO
  output ← processHook'(X)
  ASSERT output.visible_chat_text = EMPTY
  ASSERT output.write_operation_proceeds = TRUE
END FOR
```

### Preservation Property

```pascal
// Property: Preservation Checking — Violations still produce visible corrective output
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT processHook(X) = processHook'(X)
END FOR
```
