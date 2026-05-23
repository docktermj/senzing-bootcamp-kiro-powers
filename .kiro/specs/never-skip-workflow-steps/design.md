# Design Document

## Overview

This feature enforces strict sequential execution of all numbered workflow steps across the Senzing Bootcamp Power. It elevates all numbered steps with 👉 questions to the same "never skip" enforcement level as ⛔ mandatory gates, using steering-file language reinforcement and a generic agentStop hook that detects when the agent advances past a 👉 step without writing its checkpoint.

## Architecture

This feature enforces strict sequential execution of all numbered workflow steps by combining three complementary mechanisms:

1. **Steering-file language reinforcement** — Strengthened rules in `agent-instructions.md` and `conversation-protocol.md` that elevate 👉 steps to the same precedence as ⛔ mandatory gates.
2. **Per-module Sequential Execution Reminders** — A short instruction block at the top of each of the 11 module steering files that reinforces the never-skip rule at the point of use.
3. **An agentStop hook** — `enforce-sequential-steps.kiro.hook` that fires after every agent turn, reads `config/bootcamp_progress.json`, and detects when `current_step` has advanced by more than one step without intermediate checkpoints.

The design follows the existing enforcement pattern established by `enforce-gate-on-stop.kiro.hook` and `enforce-mandatory-gate.kiro.hook`, extending it from ⛔-only enforcement to all numbered steps containing 👉 questions.

## Components and Interfaces

### 1. Enforce Sequential Steps Hook

**File:** `senzing-bootcamp/hooks/enforce-sequential-steps.kiro.hook`

A JSON hook file following the existing hook schema pattern:

```json
{
  "name": "to enforce sequential step execution across all modules",
  "version": "1.0.0",
  "description": "After each agent turn, verifies that current_step has not advanced by more than one step since the last checkpoint. Detects step-skipping violations for all numbered steps with pointing-hand questions.",
  "when": {
    "type": "agentStop"
  },
  "then": {
    "type": "askAgent",
    "prompt": "<detection prompt - see Interface section>"
  }
}
```

**Detection Logic (executed by the agent via the hook prompt):**

1. Read `config/bootcamp_progress.json`
2. Extract `current_module`, `current_step`, and `step_history[current_module]`
3. If `current_step` is `null` or `step_history` has no entry for the current module → produce no output (module just started or completed)
4. Compare `current_step` against `step_history[current_module].last_completed_step`
5. If the gap is > 1 integer step → output a violation message listing skipped steps
6. If `config/.question_pending` exists AND `current_step` has advanced → output a violation (step advanced while a question was pending)
7. Otherwise → produce no output (hook silence rule)

### 2. Steering File Modifications

#### 2a. `agent-instructions.md` — Mandatory Gate Precedence Section

Add a `never-skip-numbered-steps` rule to the existing "Mandatory Gate Precedence" section:

```markdown
- **NEVER skip a numbered step containing a 👉 question.** This rule has the same absolute precedence as ⛔ mandatory gate rules. No agent-internal consideration — context pressure, session length, token budget, or perceived redundancy — can justify skipping a 👉 step. The agent SHALL execute each numbered step sequentially, advancing by exactly one step at a time.
- IF the agent identifies an opportunity to combine or abbreviate steps, it SHALL ask the bootcamper for explicit consent before doing so.
```

#### 2b. `conversation-protocol.md` — Question Stop Protocol

Strengthen the existing Question Stop Protocol section with:

```markdown
### Numbered Step Execution Boundary

Every numbered step containing a 👉 question is a mandatory execution boundary with the same absolute precedence as ⛔ mandatory gates. The agent SHALL:
- Execute each numbered step individually in sequential order
- Never advance `current_step` by more than 1 without writing intermediate checkpoints
- Never skip a 👉 step for any internal reason (context budget, session length, redundancy)
- Write `config/.question_pending` before ending the turn at any 👉 question

Violation of this rule is equivalent to a ⛔ mandatory gate violation.
```

#### 2c. Per-Module Sequential Execution Reminder

A 3-4 line block inserted near the top of each module steering file (after the frontmatter and before the first workflow step):

```markdown
> ⚠️ **Sequential Execution Rule (absolute precedence):** Execute every numbered step in this module one at a time, in order. Never skip, combine, or abbreviate any step containing a 👉 question. This rule has the same precedence as ⛔ mandatory gates — no internal reasoning can override it.
```

This block is placed in all 11 module steering files:
- `module-01-business-problem.md`
- `module-02-system-verification.md`
- `module-03-first-demo.md`
- `module-04-data-preparation.md`
- `module-05-data-mapping.md`
- `module-06-data-loading.md`
- `module-07-entity-resolution.md`
- `module-08-performance-tuning.md`
- `module-09-security-hardening.md`
- `module-10-monitoring.md`
- `module-11-deployment.md`

### 3. Hook Registration

**File:** `senzing-bootcamp/hooks/hook-categories.yaml`

Add `enforce-sequential-steps` to the `critical` category list:

```yaml
critical:
  - ask-bootcamper
  - code-style-check
  - commonmark-validation
  - enforce-sequential-steps
  - question-format-gate
  - review-bootcamper-input
  - write-policy-gate
```

This ensures the hook is created during onboarding (Step 1) alongside other critical hooks.

### 4. Hook Prompt Interface

The hook prompt instructs the agent to perform the following detection algorithm:

```python
# Pseudocode for the detection logic the agent executes
def detect_step_skip(progress: dict, question_pending_exists: bool) -> str | None:
    """Detect if the agent skipped a numbered step.

    Args:
        progress: Contents of config/bootcamp_progress.json
        question_pending_exists: Whether config/.question_pending file exists

    Returns:
        Violation message string, or None if no violation detected.
    """
    current_module = progress.get("current_module")
    current_step = progress.get("current_step")
    step_history = progress.get("step_history", {})

    # No module active or step is null → no check needed
    if current_module is None or current_step is None:
        return None

    module_key = str(current_module)
    module_history = step_history.get(module_key)

    # No history for this module → first step, no violation possible
    if module_history is None:
        return None

    last_completed = module_history.get("last_completed_step")
    if last_completed is None:
        return None

    # Extract parent step numbers for comparison
    current_parent = parse_parent_step(current_step)
    last_parent = parse_parent_step(last_completed)

    if current_parent is None or last_parent is None:
        return None

    # Check for step gap > 1
    gap = current_parent - last_parent
    if gap > 1:
        skipped = list(range(last_parent + 1, current_parent))
        return f"VIOLATION: Steps {skipped} were skipped in Module {current_module}"

    # Check for advancement while question pending
    if question_pending_exists and current_parent > last_parent:
        return (
            f"VIOLATION: current_step advanced to {current_step} "
            f"while a question was still pending"
        )

    return None
```

**Hook Prompt Text:**

```
CHECK — Read `config/bootcamp_progress.json` and check if `config/.question_pending` exists. Evaluate:

1. Extract `current_module`, `current_step`, and `step_history[<current_module>].last_completed_step`.

2. If `current_step` is null OR `step_history` has no entry for the current module: produce no output. Do nothing.

3. Parse the parent step number from both `current_step` and `last_completed_step`:
   - Integer steps: use the value directly (e.g., 5 → 5)
   - Dotted sub-steps: use the part before the dot (e.g., "5.3" → 5)
   - Lettered sub-steps: use the numeric prefix (e.g., "7a" → 7)

4. Calculate the gap: current_parent - last_parent.

5. If the gap is greater than 1: Output exactly:
   ⚠️ SEQUENTIAL STEP VIOLATION DETECTED: The agent advanced from step [last] to step [current] in Module [N], skipping step(s) [list]. Every numbered step with a 👉 question must be executed individually in order. This rule has the same absolute precedence as ⛔ mandatory gates. Go back and execute the skipped step(s) NOW before proceeding.

6. If `config/.question_pending` exists AND current_step has advanced beyond last_completed_step: Output exactly:
   ⚠️ QUESTION PENDING VIOLATION DETECTED: current_step advanced to [current] while a 👉 question is still pending (file config/.question_pending exists). The agent must not advance past a step until the bootcamper responds. Wait for the bootcamper's response before proceeding.

7. Otherwise: produce no output. Do nothing.
```

## Data Models

### bootcamp_progress.json (existing — no schema changes)

The hook reads the existing progress file structure. No modifications to the schema are needed:

```json
{
  "current_module": 3,
  "current_step": 5,
  "step_history": {
    "3": {
      "last_completed_step": 4,
      "updated_at": "2024-01-15T10:30:00+00:00"
    }
  }
}
```

### config/.question_pending (existing — no changes)

A text file containing the pending question text. Its existence signals that the agent is waiting for bootcamper input.

### Hook JSON Schema (existing pattern)

```json
{
  "name": "string — conversational name starting with 'to'",
  "version": "semver string",
  "description": "string — what the hook does",
  "when": {
    "type": "agentStop"
  },
  "then": {
    "type": "askAgent",
    "prompt": "string — detection instructions"
  }
}
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| `config/bootcamp_progress.json` does not exist | Hook produces no output (no progress to validate) |
| `current_step` is `null` | Hook produces no output (module completed or not started) |
| `step_history` has no entry for current module | Hook produces no output (first step in module) |
| `current_step` is a sub-step (e.g., "5.3") | Parse parent step (5) for gap comparison |
| `step_history` entry missing `last_completed_step` | Hook produces no output (malformed state, not a skip) |
| Hook fires during onboarding (no module active) | Hook produces no output (`current_module` check) |

## Testing Strategy

Tests live in `senzing-bootcamp/tests/` following the existing pytest + Hypothesis pattern.

### Test File: `senzing-bootcamp/tests/test_enforce_sequential_steps.py`

**Unit tests:**
- Hook JSON file has valid schema (name, version, when, then fields)
- Hook is registered in `hook-categories.yaml` under `critical`
- Hook `when.type` is `"agentStop"` with no module filter
- Hook prompt contains key detection instructions

**Property tests:**
- Step-gap violation detection across random progress states
- Valid progression produces no false positives
- Question-pending violation detection
- Sequential Execution Reminder presence in all module files

### Test File: `senzing-bootcamp/tests/test_sequential_reminder_presence.py`

**Property tests:**
- For all 11 module steering files, the Sequential Execution Reminder block is present
- The reminder text contains required key phrases (absolute precedence, sequential, never skip)

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Step-gap violations are always detected

*For any* valid progress state where `current_step` has a parent step number that exceeds `step_history[current_module].last_completed_step` by more than 1, the detection logic SHALL produce a violation message listing the skipped step numbers.

**Validates: Requirements 1.1, 1.2, 5.3**

### Property 2: Valid single-step progression produces no violation

*For any* valid progress state where `current_step` has a parent step number that exceeds `step_history[current_module].last_completed_step` by exactly 1 (or 0 for sub-step advancement), and no `.question_pending` file exists, the detection logic SHALL produce no output.

**Validates: Requirements 5.4**

### Property 3: Question-pending advancement is always detected

*For any* valid progress state where `config/.question_pending` exists AND `current_step` has advanced beyond `step_history[current_module].last_completed_step`, the detection logic SHALL produce a violation message indicating the step advanced while a question was pending.

**Validates: Requirements 1.3, 3.3**

### Property 4: Sequential Execution Reminder is present in all module steering files

*For any* module steering file in the set of 11 module files (`module-01` through `module-11`), the file SHALL contain the Sequential Execution Reminder block with key phrases referencing absolute precedence and sequential execution.

**Validates: Requirements 6.1, 6.2, 6.3**
