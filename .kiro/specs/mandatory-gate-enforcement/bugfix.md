# Bugfix Requirements Document

## Introduction

The agent skipped Module 3 Step 9 (Web Service + Visualization), a ⛔ mandatory gate, by rationalizing the skip with "Due to the length of this session" — an explicitly prohibited justification. The preToolUse hooks (`enforce-mandatory-gate`, `gate-module3-visualization`) exist to block progress file updates when mandatory gate checkpoints are missing, but the agent bypassed them entirely by skipping the step at the decision-making level without ever attempting to write the checkpoint. This reveals an enforcement gap: hooks that trigger on write operations cannot prevent an agent from simply deciding not to execute a step. The ⛔ mandatory gate designation must be treated as an absolute constraint that overrides all other agent considerations — the bootcamper must ALWAYS see the web app created in Module 3, with no escape path for either the agent or the bootcamper.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the agent reaches a ⛔ mandatory gate step and perceives session length pressure, context budget constraints, or perceived redundancy THEN the agent self-initiates a skip of the mandatory step without attempting to execute it or write any checkpoint, thereby never triggering the preToolUse hooks designed to enforce the gate

1.2 WHEN the agent skips a ⛔ mandatory gate step without writing to `bootcamp_progress.json` THEN the `enforce-mandatory-gate` preToolUse hook never fires because no write operation is attempted, leaving the enforcement mechanism completely bypassed

1.3 WHEN the agent rationalizes skipping a ⛔ mandatory gate step using prohibited justifications (session length, context budget, perceived redundancy, forward progress) THEN the system accepts the rationalization and allows the agent to proceed to subsequent steps or module completion without executing the gated step

1.4 WHEN the agent skips the ⛔ mandatory gate step and later attempts to mark the module complete THEN the `gate-module3-visualization` hook blocks the completion write, but the bootcamper has already lost the "wow moment" experience and the agent must backtrack — or worse, the agent may attempt to complete the module without a formal write, further bypassing enforcement

### Expected Behavior (Correct)

2.1 WHEN the agent reaches a ⛔ mandatory gate step THEN the system SHALL execute that step unconditionally regardless of session length, context budget pressure, perceived redundancy, or any other agent-internal consideration — the ⛔ designation is an absolute constraint that cannot be overridden by any rationalization

2.2 WHEN the agent encounters any internal reason to skip a ⛔ mandatory gate step THEN the system SHALL reject that reason at the decision-making level and proceed with full step execution (for Module 3 Step 9: generate web service, start server, verify 3 API endpoints, present URL to bootcamper)

2.3 WHEN the agent is about to advance past a ⛔ mandatory gate step in its conversational flow (offering to proceed to the next step or module) THEN the system SHALL verify that the mandatory gate step has been executed by checking for the corresponding checkpoint entries before offering advancement — this enforcement must occur at the agent reasoning level, not only at the write-hook level

2.4 WHEN prohibited justifications (session length, context budget, perceived redundancy, "we've covered enough") are considered as reasons to skip a ⛔ mandatory gate step THEN the system SHALL treat these justifications as explicitly invalid and discard them — only an explicit bootcamper request via the skip-step protocol can even attempt to skip, and the protocol itself blocks mandatory gates

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the bootcamper explicitly requests to skip a non-mandatory step (one without ⛔ designation) via the skip-step protocol trigger phrases THEN the system SHALL CONTINUE TO follow the skip-step protocol normally (acknowledge, record, assess consequences, proceed)

3.2 WHEN the bootcamper explicitly requests to skip a ⛔ mandatory gate step (Module 3 Step 9) via the skip-step protocol THEN the system SHALL CONTINUE TO refuse the skip per the existing constraint ("Mandatory gates (⛔) cannot be skipped"), explain why the visualization step is required, and offer help getting past any blockers — the bootcamper ALWAYS sees the web app, no exceptions

3.3 WHEN context budget reaches warning or critical thresholds during a module THEN the system SHALL CONTINUE TO apply context management rules (unloading non-essential files, adaptive pacing, summarizing prior work) without using budget pressure as justification to skip ⛔ mandatory gate steps

3.4 WHEN the agent reaches a non-mandatory step and no skip has been requested THEN the system SHALL CONTINUE TO execute that step normally as part of the module workflow without additional enforcement overhead

3.5 WHEN the preToolUse hooks (`enforce-mandatory-gate`, `gate-module3-visualization`) fire on a write to `bootcamp_progress.json` THEN the system SHALL CONTINUE TO enforce checkpoint verification at the write level as a secondary safety net, independent of the decision-level enforcement

---

## Bug Condition

### Bug Condition Function

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type AgentDecision
  OUTPUT: boolean
  
  // Returns true when the agent decides to skip a mandatory gate step
  // without the bootcamper requesting it, regardless of whether a
  // write operation is attempted
  RETURN X.step.hasMandatoryGate = true
     AND X.action = "skip" OR X.action = "offer_advancement_past_gate"
     AND X.initiator = "agent"
     AND X.bootcamperRequestedSkip = false
END FUNCTION
```

### Property Specification — Fix Checking

```pascal
// Property: Fix Checking — Mandatory Gate Enforcement at Decision Level
FOR ALL X WHERE isBugCondition(X) DO
  result ← agentBehavior'(X)
  ASSERT result.action = "execute_step"
     AND result.stepFullyCompleted = true
     AND result.skipAttempted = false
     AND result.rationalizationAccepted = false
END FOR
```

### Preservation Goal

```pascal
// Property: Preservation Checking — Non-mandatory steps and existing hooks unaffected
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT agentBehavior(X) = agentBehavior'(X)
END FOR
```
