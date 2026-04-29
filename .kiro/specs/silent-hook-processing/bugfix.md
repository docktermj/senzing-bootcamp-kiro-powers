# Bugfix Requirements Document

## Introduction

Two related bugs cause the agent to produce visible chat noise when hook checks pass with no action needed. The `capture-feedback` hook (promptSubmit) prints "No feedback trigger phrases — continuing normally" on virtually every message, and the three preToolUse hooks (`enforce-feedback-path`, `enforce-working-directory`, `verify-senzing-facts`) print their internal reasoning ("Not in feedback workflow, path is project-relative, no Senzing SDK content. Proceeding:") on every write operation. Both stem from the same root cause: hook prompts use phrases like "do nothing" or "let the write proceed normally" when checks pass, but the agent interprets these as requiring an acknowledgment rather than truly producing zero output. The fix updates all four hook prompts plus `hook-registry.md` and adds a general silent-processing rule to `agent-instructions.md`.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the `capture-feedback` hook fires on a promptSubmit event and no feedback trigger phrase is detected THEN the system prints "No feedback trigger phrases — continuing normally" as visible chat output

1.2 WHEN the `enforce-feedback-path` hook fires on a write operation and the agent is not in the feedback workflow THEN the system prints its internal reasoning (e.g., "Not in feedback workflow") as visible chat output

1.3 WHEN the `enforce-working-directory` hook fires on a write operation and all paths are project-relative THEN the system prints its internal reasoning (e.g., "path is project-relative") as visible chat output

1.4 WHEN the `verify-senzing-facts` hook fires on a write operation and the content contains no Senzing-specific facts THEN the system prints its internal reasoning (e.g., "no Senzing SDK content. Proceeding:") as visible chat output

1.5 WHEN multiple preToolUse hooks fire on a single write operation and all checks pass THEN the system prints a combined reasoning summary visible to the bootcamper before proceeding with the write

### Expected Behavior (Correct)

2.1 WHEN the `capture-feedback` hook fires on a promptSubmit event and no feedback trigger phrase is detected THEN the system SHALL produce no visible output and silently allow the conversation to continue

2.2 WHEN the `enforce-feedback-path` hook fires on a write operation and the agent is not in the feedback workflow THEN the system SHALL produce no visible output and silently allow the write to proceed

2.3 WHEN the `enforce-working-directory` hook fires on a write operation and all paths are project-relative THEN the system SHALL produce no visible output and silently allow the write to proceed

2.4 WHEN the `verify-senzing-facts` hook fires on a write operation and the content contains no Senzing-specific facts THEN the system SHALL produce no visible output and silently allow the write to proceed

2.5 WHEN multiple preToolUse hooks fire on a single write operation and all checks pass THEN the system SHALL produce zero combined visible output and silently proceed with the write

2.6 WHEN any hook check passes with no action needed THEN the system SHALL follow a general silent-processing rule defined in `agent-instructions.md` that instructs the agent to produce zero visible output for passing hook checks

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the `capture-feedback` hook fires and a feedback trigger phrase IS detected THEN the system SHALL CONTINUE TO initiate the feedback workflow with context capture and produce visible output guiding the bootcamper through feedback submission

3.2 WHEN the `enforce-feedback-path` hook fires and the agent IS in the feedback workflow writing to the wrong path THEN the system SHALL CONTINUE TO block the write and redirect it to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` with visible output explaining the redirect

3.3 WHEN the `enforce-working-directory` hook fires and a file path references a location outside the working directory THEN the system SHALL CONTINUE TO block the write and suggest project-relative alternatives with visible output explaining the correction

3.4 WHEN the `verify-senzing-facts` hook fires and the content contains Senzing-specific facts not verified via MCP tools THEN the system SHALL CONTINUE TO flag the unverified facts with visible output prompting verification before writing

3.5 WHEN the `ask-bootcamper` hook fires on agentStop THEN the system SHALL CONTINUE TO produce visible recap and closing question output as designed

3.6 WHEN any other hook (code-style-check, data-quality-check, validate-senzing-json, etc.) fires and requires action THEN the system SHALL CONTINUE TO produce visible output as designed by that hook's prompt

---

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type HookInvocation (hook_name, event_type, check_result)
  OUTPUT: boolean

  // Returns true when a hook fires and its check passes with no action needed
  RETURN X.hook_name IN {"capture-feedback", "enforce-feedback-path",
                          "enforce-working-directory", "verify-senzing-facts"}
         AND X.check_result = PASS_NO_ACTION_NEEDED
END FUNCTION
```

### Fix Checking Property

```pascal
// Property: Fix Checking — Silent processing when hook checks pass
FOR ALL X WHERE isBugCondition(X) DO
  output ← processHook'(X)
  ASSERT output.visible_chat_text = EMPTY
END FOR
```

### Preservation Property

```pascal
// Property: Preservation Checking — Action-required hooks still produce output
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT processHook(X) = processHook'(X)
END FOR
```
