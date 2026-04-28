# Bugfix Requirements Document

## Introduction

The `summarize-on-stop` hook (`agentStop` event) appends a progress summary after the agent's final output, which is often a question awaiting the bootcamper's response (e.g., "Which track sounds right for you?"). This produces a disorienting experience: the bootcamper reads the question, then an unexpected summary appears below it. The summary should precede the question so the bootcamper gets a recap first, then sees the question they need to answer as the very last thing on screen.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent finishes a turn that ends with a question to the bootcamper (e.g., track selection in onboarding) THEN the `agentStop` hook fires and appends a progress summary after the question, placing the summary below the question the bootcamper needs to answer

1.2 WHEN the `summarize-on-stop` hook prompt says "Before finishing" THEN the agent still places the summary after all prior output including any pending question, because the `agentStop` event fires after the agent has already produced its complete output

1.3 WHEN the bootcamper reads the agent's response during onboarding THEN they see the question first, followed by an unexpected summary block, disrupting the natural conversational flow and making it unclear what they should respond to

### Expected Behavior (Correct)

2.1 WHEN the agent finishes a turn that ends with a question to the bootcamper THEN the system SHALL place the progress summary before the question, so the question is always the last thing the bootcamper sees

2.2 WHEN the `summarize-on-stop` hook fires THEN the system SHALL instruct the agent to present the summary first and re-state or preserve the pending question as the final element of the response, ensuring the bootcamper's call-to-action is never buried

2.3 WHEN the bootcamper reads the agent's response THEN the system SHALL present content in the order: summary of what was accomplished → files changed → pending question, so the flow feels natural and the actionable question is always at the end

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent finishes a turn that does not end with a question (e.g., completing a setup step with no user input needed) THEN the system SHALL CONTINUE TO append the progress summary at the end of the response as it does today

3.2 WHEN the `summarize-on-stop` hook fires THEN the system SHALL CONTINUE TO include all three summary elements: (1) what was accomplished, (2) which files were created or modified, and (3) what the next step is

3.3 WHEN the agent is in any module (not just onboarding) THEN the system SHALL CONTINUE TO fire the `summarize-on-stop` hook on every `agentStop` event, preserving the summary functionality across the entire bootcamp

3.4 WHEN the agent produces a response with no pending question THEN the system SHALL CONTINUE TO place "what is the next step" as the final element of the summary, maintaining forward momentum for the bootcamper

---

## Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type AgentStopEvent
  OUTPUT: boolean

  // The bug triggers when the agent's output ends with a question
  // awaiting the bootcamper's response (indicated by 👉 prefix or
  // WAIT instruction in the steering flow)
  RETURN X.agentOutput ends with a pending question for the bootcamper
END FUNCTION
```

## Property Specification

```pascal
// Property: Fix Checking — Summary Before Question
FOR ALL X WHERE isBugCondition(X) DO
  result ← agentOutputWithHook'(X)
  ASSERT result.summaryPosition < result.questionPosition
    AND result.question is the last content block in result
END FOR
```

## Preservation Goal

```pascal
// Property: Preservation Checking — No-Question Turns Unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT agentOutputWithHook(X) = agentOutputWithHook'(X)
END FOR
```
