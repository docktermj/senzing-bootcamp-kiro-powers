# Design Document

## Overview

This design addresses the enforcement gap where the agent bypasses mandatory gate hooks by deciding not to execute a step at the reasoning level, never triggering the write-level preToolUse hooks. The fix adds a **decision-level enforcement layer** using an `agentStop` hook that detects when the agent has ended a turn during Module 3 without executing or completing Step 9, and forces the agent back on track.

The existing write-level hooks (`enforce-mandatory-gate`, `gate-module3-visualization`) remain as a secondary safety net. The new enforcement operates at a higher level — catching the agent's *decision to skip* rather than only blocking the *write that follows*.

## Architecture

### Defense-in-Depth Model

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Steering Language (existing, strengthened)          │
│ - Module 3 steering: ⛔ MANDATORY GATE block                │
│ - Skip-step protocol: "agent can NEVER self-initiate skip"  │
│ - Prohibited rationalizations list                          │
└─────────────────────────────────────────────────────────────┘
                            │ (agent may still ignore)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Decision-Level Hook (NEW — agentStop)              │
│ - Fires after every agent turn during Module 3              │
│ - Checks: is current_step ≥ 9 AND checkpoint missing?       │
│ - If yes: forces agent to execute Step 9 immediately        │
│ - Catches the "skip without writing" bypass                 │
└─────────────────────────────────────────────────────────────┘
                            │ (agent attempts write)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Write-Level Hooks (existing, unchanged)            │
│ - enforce-mandatory-gate: blocks current_step > 9 write     │
│ - gate-module3-visualization: blocks module completion write │
└─────────────────────────────────────────────────────────────┘
```

### New Hook: `enforce-gate-on-stop`

**Type:** `agentStop`
**Purpose:** After every agent turn, check whether the agent is in Module 3 at or past Step 9 without having completed the mandatory gate checkpoint. If so, instruct the agent to execute Step 9 immediately.

**Logic:**

```
ON agentStop:
  1. Read config/bootcamp_progress.json
  2. IF current_module ≠ 3 → do nothing
  3. IF current_step < 9 → do nothing (hasn't reached the gate yet)
  4. IF module_3_verification.checks.web_service.status = "passed"
     AND module_3_verification.checks.web_page.status = "passed" → do nothing (gate satisfied)
  5. IF skipped_steps contains "3.9" → do nothing (bootcamper-initiated skip via protocol)
  6. OTHERWISE → output enforcement message forcing Step 9 execution
```

**Key insight:** This hook fires on `agentStop`, meaning it catches the scenario where the agent finishes a turn having offered to "move on" or "skip" the visualization step. The hook fires *after* the agent's response, and its output becomes the next agent instruction — forcing the agent to execute Step 9 in the following turn.

### Steering Reinforcement

The existing Module 3 steering already has strong mandatory gate language. The reinforcement adds a **pre-step checkpoint verification instruction** that fires when the agent is about to offer advancement past Step 9. This is a steering-level instruction (not a hook) that tells the agent to self-check before offering to proceed.

**Addition to `module-03-system-verification.md`:**

A new blockquote instruction immediately before the "Ready for Module 4?" transition that requires the agent to verify Step 9 checkpoints exist before offering advancement.

## Components

### 1. New Hook File: `enforce-gate-on-stop.kiro.hook`

**Location:** `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook`

```json
{
  "name": "to enforce mandatory gate execution on agent stop",
  "version": "1.0.0",
  "description": "After each agent turn during Module 3, verifies that Step 9 (⛔ mandatory gate) has been executed if the agent has reached or passed it. Forces immediate execution if the gate checkpoint is missing.",
  "when": {
    "type": "agentStop"
  },
  "then": {
    "type": "askAgent",
    "prompt": "CHECK — Read `config/bootcamp_progress.json` and evaluate:\n\n1. Is `current_module` equal to 3?\n2. Is `current_step` greater than or equal to 9?\n\nIf EITHER condition is false: produce no output. Do nothing.\n\nIf BOTH are true: Check whether the ⛔ mandatory gate for Step 9 has been satisfied:\n\nCONDITION A — Step 9 checkpoints exist:\n- `module_3_verification.checks.web_service.status` equals `\"passed\"`\n- `module_3_verification.checks.web_page.status` equals `\"passed\"`\n\nCONDITION B — Step 9 was explicitly skipped by the bootcamper:\n- `skipped_steps` contains an entry with key `\"3.9\"`\n\nIf CONDITION A is true OR CONDITION B is true: produce no output. The mandatory gate is satisfied.\n\nIf NEITHER condition is met: The agent has reached or passed Step 9 without executing it. This is a ⛔ mandatory gate violation. Output exactly:\n\n⛔ MANDATORY GATE VIOLATION DETECTED: Step 9 (Web Service + Visualization) has not been executed but the agent has advanced past it. This step CANNOT be skipped by the agent under any circumstances. Load `module-03-phase2-visualization.md` and execute Step 9 NOW — generate the web service, start the server, verify all 3 API endpoints, and present the URL to the bootcamper. Do not proceed with any other work until Step 9 is complete and checkpoints are written to bootcamp_progress.json."
  }
}
```

### 2. Steering Update: `module-03-system-verification.md`

Add a pre-advancement verification instruction after the Step 9 section and before any module completion or "Ready for Module 4?" transition:

```markdown
> **⛔ PRE-ADVANCEMENT VERIFICATION (Agent self-check):**
>
> Before offering to advance to Module 4 or marking Module 3 complete, the agent
> MUST read `config/bootcamp_progress.json` and verify:
> - `module_3_verification.checks.web_service.status` = `"passed"`
> - `module_3_verification.checks.web_page.status` = `"passed"`
>
> If these checkpoints are NOT present, the agent MUST execute Step 9 immediately.
> Do NOT offer advancement. Do NOT ask "Ready for Module 4?" Do NOT save progress.
> Execute Step 9 first.
```

### 3. Hook Registry Updates

**`hook-registry.md`** — Add entry for `enforce-gate-on-stop`:

| Hook ID | Module | Trigger | Description |
|---------|--------|---------|-------------|
| enforce-gate-on-stop | 3 | agentStop → askAgent | After each agent turn during Module 3, verifies Step 9 mandatory gate has been executed if the agent has reached or passed it. Forces immediate execution on violation. |

**`hook-registry-detail.md`** — Add detailed entry with full prompt text.

### 4. Steering Index Update

Update `steering-index.yaml` with the new token count for `module-03-system-verification.md` after the steering reinforcement is added.

## Behavior Matrix

| Scenario | Layer 1 (Steering) | Layer 2 (agentStop hook) | Layer 3 (Write hooks) | Outcome |
|----------|--------------------|--------------------------|-----------------------|---------|
| Agent executes Step 9 normally | ✅ Followed | No output (gate satisfied) | No output (checkpoints present) | ✅ Normal flow |
| Agent tries to skip Step 9 and write checkpoint | Violated | N/A (write attempted) | ⛔ BLOCKED | Agent forced back |
| Agent skips Step 9 without writing anything | Violated | ⛔ VIOLATION DETECTED → forces execution | Never reached | Agent forced back |
| Agent offers "Ready for Module 4?" without Step 9 | Pre-advancement check catches it | ⛔ VIOLATION DETECTED on next stop | Would block completion write | Agent forced back |
| Bootcamper requests skip via protocol | Protocol refuses (mandatory gate) | No output (would need "3.9" in skipped_steps, which protocol won't write) | Would block if somehow written | ✅ Skip refused |
| Context budget pressure during Step 9 | Prohibited rationalization | Catches if agent stops mid-step | N/A | Agent continues Step 9 |

## Unchanged Components

- `enforce-mandatory-gate.kiro.hook` — unchanged, continues as write-level safety net
- `gate-module3-visualization.kiro.hook` — unchanged, continues as module-completion safety net
- `skip-step-protocol.md` — unchanged, already refuses mandatory gate skips
- `module-03-phase2-visualization.md` — unchanged, full Step 9 implementation spec
- All non-Module-3 behavior — unchanged, no new enforcement overhead

## Testing Strategy

1. **Property test:** Verify hook JSON schema validity for the new hook file
2. **Prompt validation test:** Verify the agentStop hook prompt contains required enforcement language (checkpoint field names, blocking message, file references)
3. **Regression test:** Verify existing hooks (`enforce-mandatory-gate`, `gate-module3-visualization`) are unchanged
4. **Integration scenario (manual):** Walk through Module 3 and verify the agentStop hook fires correctly when Step 9 is reached but not executed
