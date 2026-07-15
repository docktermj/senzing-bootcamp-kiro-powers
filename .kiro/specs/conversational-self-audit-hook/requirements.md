# Requirements Document: Conversational Self-Audit Hook

## Introduction

An experience audit of the bootcamp found that its strongest guarantees are
**format/gate-level** (mandatory gates, write-time `write-policy-gate`
validation), while the highest-value *conversational* rule — **every yielding
turn ends with exactly one 👉 leading question** (`agent-behavior-rules.md`
Rule 4; `conversation-protocol.md` The One Question Rule) — rests largely on
agent discipline. Today's coverage is partial and asymmetric:

- `write-policy-gate` (PreToolUse) validates a question's *shape* when it is
  written to `config/.question_pending` (compound-question / ambiguity checks),
  but not the *count* of 👉 in the rendered turn.
- `ask-bootcamper` (Stop) will *add* a closing 👉 when the last message has none,
  but it does not flag a turn that leaked **two or more** 👉 questions, nor does
  it independently confirm the single-question invariant held.

The result: a turn that ends with **zero** 👉 (dead-end) or **two-plus** 👉
(multi-question) can slip through. This feature adds a **lightweight periodic
self-audit** at the `Stop` boundary that spot-checks the one-👉 invariant and, on
a violation, emits a self-correction instruction — hardening the rule without a
per-write hook and without changing the never-block principle.

This complements, and does not replace, `leading-question-enforcement`,
`leading-question-continuity`, `single-ask-question-guarantee`,
`missing-pointer-marker`, and `clean-question-presentation`.

## Glossary

- **Yielding_Turn**: an agent turn that ends by handing control back to the
  bootcamper (i.e., it is not a silent internal-file pass-through and not a
  non-yielding continuation).
- **Leading_Question**: a 👉-prefixed, bootcamper-facing question at the end of a
  Yielding_Turn.
- **One_Question_Invariant**: a Yielding_Turn contains **exactly one**
  Leading_Question — never zero, never two or more.
- **Self_Audit**: a deterministic, non-blocking Stop-boundary spot check of the
  One_Question_Invariant on the most recent assistant message.
- **Audit_Cadence**: how often the Self_Audit runs — every yielding turn, or a
  sampled subset, chosen to stay lightweight.

## Requirements

### Requirement 1: Detect one-👉 invariant violations at the Stop boundary

**User Story:** As a bootcamper, I want the agent to catch when a turn ends with
no question or with multiple questions, so the conversation never dead-ends or
overwhelms me with stacked choices.

#### Acceptance Criteria

1. WHEN a Yielding_Turn completes, THE Self_Audit SHALL count the 👉
   Leading_Questions in the most recent assistant message.
2. WHEN the count is exactly one, THE Self_Audit SHALL produce no output (silent
   pass).
3. WHEN the count is zero on a Yielding_Turn that performed substantive work,
   THE Self_Audit SHALL flag a "missing leading question" violation.
4. WHEN the count is two or more, THE Self_Audit SHALL flag a "multiple leading
   questions" violation naming that the turn must end with exactly one.
5. THE Self_Audit SHALL NOT flag a non-yielding turn, a silent internal-file
   pass-through (per `agent-behavior-rules.md` Rule 5), or the DEFAULT-OUTPUT
   single-period response.

### Requirement 2: Self-correct without blocking

**User Story:** As a bootcamper, I never want an audit to stall the bootcamp.

#### Acceptance Criteria

1. WHEN a violation is detected, THE Self_Audit SHALL emit a concise
   self-correction instruction directing the agent to re-render the turn ending
   with exactly one 👉 (reusing the compound-question rewrite / numbered-list
   pattern already defined in the hooks and steering).
2. THE Self_Audit SHALL be advisory (a Soft_Block at most) — it SHALL NOT be a
   ⛔ mandatory gate and SHALL NEVER permanently block progress.
3. THE self-correction output SHALL NOT itself introduce a second 👉 or a
   compound question.
4. WHERE the audit cannot run or errors, it SHALL degrade to a silent no-op and
   never block the turn.

### Requirement 3: Stay lightweight and off the write path

**User Story:** As a maintainer, I want the audit to add negligible cost and not
reintroduce per-write overhead.

#### Acceptance Criteria

1. THE Self_Audit SHALL run only at the `Stop` boundary — never on a file-write
   tool call, and never as a `PostToolUse` hook on the write tools.
2. THE Audit_Cadence SHALL be tunable: it MAY sample (e.g., run on a subset of
   Stop events) to remain lightweight while still exercising the invariant
   regularly.
3. THE feature SHALL prefer folding the audit into the existing `ask-bootcamper`
   Stop hook (minimal new surface) over adding a new hook, consistent with the
   one-hook-per-file registry model.

### Requirement 4: Consistency and registry hygiene

#### Acceptance Criteria

1. IF the audit changes a hook prompt, THEN the hook registry
   (`hook-registry.md`, `hook-registry-critical.md`, module slices) and
   `hooks.lock.yaml` SHALL be regenerated via `sync_hook_registry.py --write`
   so `--verify` passes, and `steering-index.yaml` token counts + budget total
   SHALL be re-synced so `measure_steering.py --check` passes.
2. THE feature SHALL add no new always-loaded steering budget beyond what the
   audit phase requires.

## Non-Goals

- Replacing `write-policy-gate`'s write-time question-shape validation.
- Making the audit a hard (⛔) blocking gate.
- Auditing question *semantics* beyond the count/dead-end invariant (ambiguity
  and compound-question shape remain owned by `write-policy-gate`).
