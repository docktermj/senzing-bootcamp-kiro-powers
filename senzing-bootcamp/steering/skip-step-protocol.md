---
inclusion: manual
description: "Protocol for skipping steps when bootcampers are stuck or a step is not applicable"
---

# Skip Step Protocol

When a bootcamper says they want to skip a step, are stuck, or a step doesn't apply to their situation, follow this protocol.

## Trigger Phrases

- "skip this step"
- "this doesn't apply to me"
- "I'm stuck"
- "can we move on"
- "not relevant"
- "I don't need this"

## Protocol

### 1. Acknowledge and Clarify

Ask ONE question to understand why:

👉 "Got it — would you like to skip this because (a) it doesn't apply to your use case, (b) you've already done this outside the bootcamp, or (c) you're stuck and want to come back later?"

> **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

### 2. Record the Skip

After the bootcamper responds, update `config/bootcamp_progress.json`:

```json
{
  "skipped_steps": {
    "<module>.<step>": {
      "reason": "<a|b|c>",
      "note": "<brief explanation from bootcamper>",
      "skipped_at": "<ISO 8601>"
    }
  }
}
```

### 3. Assess Consequences

Check whether the skipped step produces artifacts that later steps depend on:

| If the skipped step produces... | Then... |
|---|---|
| A file that later steps read | Warn: "Step X will need [file]. We can create a minimal placeholder or revisit this later." |
| Configuration that later steps use | Warn: "Steps Y–Z assume [config] is set. I'll note this and we can fill it in when needed." |
| Nothing downstream depends on it | Proceed silently |

### 4. Proceed

- Advance `current_step` in progress to the next step
- Tell the bootcamper what's next
- If they chose (c) "come back later", add the step to a `revisit_later` list in progress

## Revisiting Skipped Steps

When the bootcamper says "what did I skip?" or "revisit skipped steps":

1. Read `skipped_steps` from `config/bootcamp_progress.json`
2. Present the list with reasons
3. Ask which one they'd like to revisit

## Constraints

- **Mandatory gates (⛔) cannot be skipped.** If the bootcamper tries to skip a mandatory gate, explain why it's required and offer help getting past it.
- **The agent can NEVER self-initiate a skip of a ⛔ mandatory gate step.** No agent-internal reasoning — session length, context budget, perceived redundancy, or any other consideration — justifies skipping a ⛔ step. Only the bootcamper can attempt to skip a mandatory gate (and this protocol refuses that attempt). If the agent reaches a ⛔ step, it MUST execute it unconditionally. This constraint is enforced by the `enforce-mandatory-gate.kiro.hook` preToolUse hook, which blocks step advancement past a ⛔ gate when checkpoint evidence is missing.
- **Module-level skips** use the existing track system (switch tracks or use `skip_if` from `module-dependencies.yaml`). This protocol is for step-level skips within a module.
- Steps that produce database state (loading, SDK setup) should be skipped with extra caution — warn that downstream modules may not work correctly.
