# Bugfix Requirements Document

## Introduction

The `enforce-file-path-policies` preToolUse hook outputs the literal text "policy: pass" in the agent's response whenever a write operation passes its path validation checks. This internal hook machinery is visible to the bootcamper, adding noise to the conversation with no informational value. The hook prompt explicitly instructs the agent to "output exactly: policy: pass" on the fast path, which the agent dutifully renders as visible chat text. The fix must suppress this output so that passing policy checks proceed silently.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `enforce-file-path-policies` hook fires on a write operation and the target path is inside the working directory and is not misrouted feedback THEN the system outputs "policy: pass" as visible text in the bootcamper's chat

1.2 WHEN multiple write operations occur in sequence and each passes the file path policy check THEN the system outputs "policy: pass" repeatedly, cluttering the conversation with redundant internal status messages

### Expected Behavior (Correct)

2.1 WHEN the `enforce-file-path-policies` hook fires on a write operation and the target path is inside the working directory and is not misrouted feedback THEN the system SHALL produce no visible output and silently allow the write to proceed

2.2 WHEN multiple write operations occur in sequence and each passes the file path policy check THEN the system SHALL produce no visible output for any of the passing checks and silently allow each write to proceed

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the `enforce-file-path-policies` hook fires and the target path is outside the working directory THEN the system SHALL CONTINUE TO block the write and produce visible output instructing the agent to use project-relative equivalents

3.2 WHEN the `enforce-file-path-policies` hook fires and feedback content is being written to a path other than `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` THEN the system SHALL CONTINUE TO block the write and produce visible output redirecting to the correct feedback file

3.3 WHEN the `enforce-file-path-policies` hook fires and file content references external paths like `/tmp/` or `%TEMP%` THEN the system SHALL CONTINUE TO block the write and produce visible output requiring replacement with project-relative equivalents

---

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type HookInvocation (hook_name, target_path, is_feedback_content, content_refs_external)
  OUTPUT: boolean

  // Returns true when the enforce-file-path-policies hook fires and all checks pass
  RETURN X.hook_name = "enforce-file-path-policies"
         AND X.target_path IS INSIDE working_directory
         AND NOT (X.is_feedback_content AND X.target_path != "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md")
         AND NOT X.content_refs_external
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — No visible output when file path policy passes
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
