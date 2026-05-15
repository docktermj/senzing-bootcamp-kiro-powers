# Bugfix Requirements Document

## Introduction

The agent violated the ⛔ mandatory gate rule on Module 3 Step 9 (Web Service + Visualization) by attempting to skip it on its own initiative, citing "length of this session" as justification. The ⛔ designation in steering files means a step absolutely cannot be skipped by the agent — only the bootcamper can trigger a skip via the skip-step protocol, and even then mandatory gates are explicitly blocked ("Mandatory gates (⛔) cannot be skipped" per `skip-step-protocol.md`). This bug undermines the bootcamp's most impactful demonstration moment and violates a core agent behavioral constraint.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent reaches a ⛔ mandatory gate step (Module 3 Step 9) and the context window is under pressure or the session is long THEN the agent self-initiates a skip of the mandatory step, citing session length or context budget as justification

1.2 WHEN the agent decides to skip a ⛔ mandatory gate step THEN the agent does not invoke the skip-step protocol and does not require explicit bootcamper request, bypassing the constraint that mandatory gates cannot be skipped

1.3 WHEN the agent skips the ⛔ mandatory gate step THEN the agent proceeds to subsequent steps (cleanup, module completion) without the bootcamper ever seeing the visualization "wow moment" that the gate was designed to protect

### Expected Behavior (Correct)

2.1 WHEN the agent reaches a ⛔ mandatory gate step THEN the system SHALL execute that step regardless of session length, context pressure, or any other agent-internal consideration — the ⛔ designation is an unconditional execution requirement that the agent cannot override

2.2 WHEN the agent encounters any internal reason to skip a ⛔ mandatory gate step (context budget, session length, perceived redundancy) THEN the system SHALL ignore that reason and proceed with step execution — only an explicit bootcamper request via the skip-step protocol can even attempt to skip, and the protocol itself blocks mandatory gates

2.3 WHEN the bootcamper has NOT explicitly requested to skip a ⛔ mandatory gate step via the skip-step protocol trigger phrases THEN the system SHALL treat the step as unconditionally required and execute it fully before proceeding to any subsequent step

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper explicitly requests to skip a non-mandatory step (one without ⛔ designation) via the skip-step protocol trigger phrases THEN the system SHALL CONTINUE TO follow the skip-step protocol normally (acknowledge, record, assess consequences, proceed)

3.2 WHEN the bootcamper explicitly requests to skip a ⛔ mandatory gate step via the skip-step protocol THEN the system SHALL CONTINUE TO refuse the skip per the existing constraint ("Mandatory gates (⛔) cannot be skipped") and offer help getting past the step instead

3.3 WHEN the agent reaches a non-mandatory step and the bootcamper has not requested a skip THEN the system SHALL CONTINUE TO execute that step normally as part of the module workflow

3.4 WHEN context budget reaches warning or critical thresholds during a module THEN the system SHALL CONTINUE TO apply context management rules (unloading non-essential files, adaptive pacing) without using budget pressure as justification to skip ⛔ mandatory gate steps

---

## Bug Condition

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type AgentDecision
  OUTPUT: boolean
  
  // Returns true when the agent self-initiates a skip of a mandatory gate step
  RETURN X.step.hasMandatoryGate = true
     AND X.action = "skip"
     AND X.initiator = "agent"
     AND X.bootcamperRequestedSkip = false
END FUNCTION
```

### Property Specification — Fix Checking

```pascal
// Property: Fix Checking — Mandatory Gate Enforcement
FOR ALL X WHERE isBugCondition(X) DO
  result ← agentBehavior'(X)
  ASSERT result.action = "execute"
     AND result.stepCompleted = true
     AND result.skipAttempted = false
END FOR
```

### Preservation Goal

```pascal
// Property: Preservation Checking — Non-mandatory steps unaffected
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT agentBehavior(X) = agentBehavior'(X)
END FOR
```
