# Bugfix Requirements Document

## Introduction

After Module 3's core verification pipeline passed (159 records loaded, 84 entities resolved), the agent asked the bootcamper whether they wanted to continue with the remaining steps (including the visualization) or skip ahead. This violates the ⛔ mandatory gate on Step 9 — the agent should never present a ⛔ step as optional or offer to skip it. The existing enforcement hooks (`gate-module3-visualization`, `enforce-mandatory-gate`, `enforce-gate-on-stop`) catch the agent when it actually skips the step, but they do not prevent the agent from **offering** to skip it via a question. The violation occurs at the question-asking stage, before any checkpoint write.

## Related Specs

- `enforce-visualization-step` — Blocks Module 3 completion when Step 9 checkpoints are missing (reactive enforcement)
- `mandatory-visualization-gate` — Prevents agent-initiated skips of ⛔ steps (proactive enforcement on step advancement)

This spec addresses a third failure mode: the agent **asking** whether to skip a ⛔ step, which undermines the mandatory gate even if the bootcamper says "yes, continue."

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent completes Module 3 Steps 1–8 successfully THEN the agent asks a question like "Would you like to continue with the visualization, or skip ahead to the next module?" — presenting the ⛔ mandatory gate step as an optional choice

1.2 WHEN the agent formulates a closing question after Steps 1–8 THEN the `enforce-single-question` hook validates question format but does NOT check whether the question offers to skip a ⛔ mandatory gate step

1.3 WHEN the agent writes a question to `config/.question_pending` that offers to skip a ⛔ step THEN no hook or steering rule detects and blocks this violation — the question reaches the bootcamper

### Expected Behavior (Correct)

2.1 WHEN the agent completes steps preceding a ⛔ mandatory gate step THEN the agent SHALL proceed directly to the mandatory gate step without asking whether the bootcamper wants to skip it — no question offering to bypass the step shall be generated

2.2 WHEN the agent formulates any 👉 question during a module with ⛔ mandatory gate steps THEN the question SHALL NOT present the mandatory gate step as optional, skippable, or conditional — phrases like "or skip ahead", "or move on", "would you like to continue with [mandatory step]" are violations when referring to a ⛔ step

2.3 WHEN the agent reaches a ⛔ mandatory gate step THEN the agent SHALL announce it is proceeding to that step (not ask permission) and execute it unconditionally

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the agent reaches a non-mandatory step THEN the system SHALL CONTINUE TO allow the agent to offer choices about how to proceed, including skip options

3.2 WHEN the agent asks a 👉 question that does NOT reference a ⛔ mandatory gate step THEN the system SHALL CONTINUE TO allow the question without interference

3.3 WHEN the bootcamper explicitly invokes the skip-step protocol for a ⛔ step THEN the system SHALL CONTINUE TO refuse the skip per existing constraints ("Mandatory gates cannot be skipped")

3.4 WHEN the `ask-bootcamper` hook generates a closing question after work is done THEN the system SHALL CONTINUE TO generate contextual closing questions — but those questions must not offer to skip upcoming ⛔ steps

---

## Bug Condition

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type AgentQuestion
  OUTPUT: boolean
  
  // Returns true when the agent asks a question that offers to skip a ⛔ step
  RETURN X.type = "question"
     AND X.referencesStep.hasMandatoryGate = true
     AND X.offersSkipOrBypass = true
     AND X.initiator = "agent"
END FUNCTION
```

### Property Specification — Fix Checking

```pascal
// Property: Fix Checking — No skip offers for mandatory gates
FOR ALL X WHERE isBugCondition(X) DO
  result ← agentBehavior'(X)
  ASSERT result.questionGenerated = false
     OR result.questionContent.offersSkipOrBypass = false
END FOR
```

### Preservation Goal

```pascal
// Property: Preservation Checking — Non-mandatory questions unaffected
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT agentBehavior(X) = agentBehavior'(X)
END FOR
```
