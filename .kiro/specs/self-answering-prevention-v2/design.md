# Design: Self-Answering Prevention v2

## Overview

This fix addresses the systemic self-answering issue by making a structural change to the hook architecture. The previous fix (stronger prompt language) failed because the problem is not instruction-following — it's that the `askAgent` hook creates a new agent turn, and the model sometimes hallucinates user input when prompted to generate in that turn.

The fix has three parts:
1. **Embed recap behavior in steering** — the agent always ends non-question turns with a recap + 👉 question (no hook needed for this)
2. **Restructure the ask-bootcamper hook** — invert the prompt logic so silence is the unconditional default, with output gated behind an explicit verification step
3. **Add a question-pending sentinel** — the agent writes a marker when it asks a 👉 question, giving the hook an unambiguous signal

## Architecture

### Strategy: Defense in Depth

Rather than relying on a single mechanism, this fix layers three independent defenses:

```
Layer 1: Steering Instructions (agent-instructions.md)
  → Agent always ends non-question turns with recap + 👉
  → Eliminates the NEED for the hook to produce output in most cases

Layer 2: Sentinel File (config/.question_pending)
  → Agent writes this file when asking a 👉 question
  → Agent deletes it when processing bootcamper's response
  → Provides unambiguous state signal

Layer 3: Restructured Hook Prompt (ask-bootcamper.kiro.hook)
  → Default: SILENCE (zero tokens)
  → Exception: ONLY if sentinel file does NOT exist AND no 👉 in last message
  → Even if the hook fires, the default path is silence
```

### Affected Files

| File | Change Type | Purpose |
|------|-------------|---------|
| `senzing-bootcamp/steering/agent-instructions.md` | Modify | Add mandatory end-of-turn recap rule for non-question turns |
| `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` | Modify | Restructure prompt: silence-first with narrow output exception |
| `senzing-bootcamp/steering/hook-registry.md` | Modify | Update ask-bootcamper entry to match new prompt |

### Design Rationale

**Why not just delete the hook?**

Deleting the hook entirely and relying solely on steering instructions would work in theory, but the agent doesn't always remember to provide a recap. The hook serves as a safety net. However, the hook's prompt must be restructured so that its failure mode is silence (safe) rather than hallucination (dangerous).

**Why invert the prompt logic?**

Current prompt: "FIRST check for 👉. If found, produce nothing. SECOND, if no 👉, produce recap."

This structure asks the model to evaluate a condition before deciding whether to generate. If the model starts generating before fully processing the condition, it produces output (the dangerous path).

New prompt: "YOUR OUTPUT IS NOTHING. EMPTY. ZERO TOKENS. [end of primary instruction] EXCEPTION CLAUSE: If and only if you have confirmed that..."

This structure makes silence the unconditional default. The model must actively override the default to produce output. The failure mode (failing to override) results in silence — which is safe.

**Why add a sentinel file?**

The sentinel file (`config/.question_pending`) provides a concrete, verifiable signal that doesn't depend on the model correctly parsing conversation history. The hook prompt can reference it: "If the file config/.question_pending exists, your output is NOTHING." This is a simpler check than "scan the entire conversation history for 👉."

## Components and Interfaces

### Component 1: Steering-Embedded Recap Rule

In `agent-instructions.md`, add to the Communication section:

```markdown
### End-of-Turn Protocol

When you complete work that does NOT end with a 👉 question:
- Briefly recap what you accomplished and which files changed
- End with a contextual 👉 question asking what the bootcamper wants to do next
- This is YOUR responsibility — do not rely on hooks to provide the closing question

When you DO end with a 👉 question:
- Write the file `config/.question_pending` containing the question text
- The ask-bootcamper hook will fire but produce no output (this is correct)
- When the bootcamper responds, delete `config/.question_pending` before processing their answer
```

### Component 2: Question-Pending Sentinel

The agent writes `config/.question_pending` whenever it asks a 👉 question. Contents: the question text (for debugging). The agent deletes this file at the start of processing the bootcamper's next message.

This gives the hook an unambiguous, file-system-level signal that doesn't require parsing conversation history.

### Component 3: Restructured Hook Prompt

New `ask-bootcamper.kiro.hook` prompt:

```
PRODUCE NOTHING. YOUR OUTPUT IS EMPTY. ZERO TOKENS. DO NOT GENERATE ANY TEXT.

---

EXCEPTION (read ONLY if you are certain no question is pending):

Before producing ANY output, verify ALL of these conditions:
1. The file config/.question_pending does NOT exist
2. The most recent assistant message does NOT contain the 👉 character
3. The most recent assistant message does NOT end with a question mark directed at the bootcamper

If ANY condition fails: PRODUCE NOTHING. STOP. ZERO TOKENS.

If ALL conditions pass: You may provide a brief recap of work done and a contextual 👉 closing question. Keep it to 2-3 sentences maximum.

CRITICAL: If you are uncertain about ANY condition, default to SILENCE. Silence is always safe. Output is only safe when you are certain no question is pending.
```

Key structural changes:
- The prompt STARTS with "produce nothing" — this is the first thing the model processes
- The exception is gated behind a verification checklist
- The default/failure mode is silence (safe)
- The prompt is shorter and less complex — less cognitive load

### Component 4: Closing-Question Ownership Transfer

Currently, `agent-instructions.md` says: "Closing-question ownership: never end your turn with a closing question — the ask-bootcamper hook owns those."

This rule must be INVERTED: "End-of-turn recap and closing questions are YOUR responsibility. The ask-bootcamper hook is a safety net only — do not rely on it."

This is critical because if the agent owns the closing question, the hook rarely needs to produce output at all. The hook becomes a true safety net that fires but almost always produces nothing.

## Data Models

### Sentinel File

`config/.question_pending`:
```
👉 What deployment target are you planning for?
```

Simple text file. Created by the agent when asking a 👉 question. Deleted by the agent when processing the bootcamper's response. Existence = question pending.

## Error Handling

- If `config/.question_pending` exists but no question is actually pending (stale file from a crashed session): the hook produces silence (safe). The agent will delete the file when it next processes input.
- If the sentinel file is missing but a question IS pending: the hook falls back to checking for 👉 in the last message (the existing check, now as a secondary signal).
- If both checks fail (no sentinel, no 👉 detected) but a question was actually asked: the hook may produce a recap — this is the same failure mode as today but is now much less likely given the dual-check approach.

## Testing Strategy

### Structural Verification

1. Verify `agent-instructions.md` contains the End-of-Turn Protocol with sentinel file instructions
2. Verify the ask-bootcamper hook prompt starts with "PRODUCE NOTHING" as the unconditional default
3. Verify the hook prompt's exception clause requires checking the sentinel file
4. Verify the "Closing-question ownership" rule has been inverted

### Behavioral Verification

1. After the agent asks a 👉 question, verify `config/.question_pending` is created
2. After the bootcamper responds, verify `config/.question_pending` is deleted
3. When the hook fires with a question pending, verify it produces zero output
4. When the hook fires without a question pending, verify it can produce a recap (if the agent didn't already provide one)

### Regression Verification

1. Non-question turns still get a recap + closing question (either from the agent or the hook)
2. Other hooks (preToolUse, fileEdited, etc.) are unaffected
3. The bootcamper's genuine responses are processed normally
