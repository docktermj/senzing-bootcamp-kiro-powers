# Design Document: Conversational Self-Audit Hook

## Overview

Add a deterministic, non-blocking **Leading-Question Count Audit** at the `Stop`
boundary that verifies the One_Question_Invariant (exactly one 👉 in a
Yielding_Turn) and emits a self-correction instruction on violation. The audit
is folded into the existing `ask-bootcamper` Stop hook as an additional phase
(minimal new surface, consistent with the one-hook-per-file registry model that
`sync_hook_registry.py` enforces by reading `hooks[0]`).

This targets the gap the experience audit surfaced: `write-policy-gate` guards a
question's *shape* at write time and `ask-bootcamper` *adds* a missing closing
question, but nothing flags a turn that leaked **two-plus** 👉 or independently
re-confirms the single-question invariant held.

## Where it lives

`ask-bootcamper` already inspects the most recent assistant message for a 👉 in
its Phase 1 (Closing Question) and enforces sequencing in Phase 2. The audit is a
natural sibling phase there:

- **New phase: Leading-Question Count Audit.** After Phase 1 has had its chance
  to add a closing question, count the 👉 leading-question lines in the rendered
  turn. Exactly one → silent pass. Zero on a substantive turn → "missing leading
  question" self-correction. Two or more → "multiple leading questions"
  self-correction (re-render ending on exactly one; if the extras are
  alternatives, fold them into a numbered list under one lead question).

Because `ask-bootcamper` is an `agent`-type hook, the audit is expressed as a
prompt phase the agent evaluates. Its determinism comes from a precise counting
rule (below) plus the existing `config/.question_pending` invariant (a
well-formed Yielding_Turn writes exactly one pending question).

## Counting rule (precise, to avoid false positives)

A **Leading_Question line** is a line whose first non-whitespace, non-blockquote,
non-bold content begins with 👉. The count excludes:

- 👉 characters inside fenced code blocks or inline code,
- 👉 appearing in quoted examples of prior turns,
- the internal control markers `🛑`/`⛔` (already internal-only per
  `agent-behavior-rules.md`).

Cross-check against `config/.question_pending`: a well-formed Yielding_Turn has
exactly one pending question recorded; a mismatch between the rendered 👉 count
and the pending-question state is itself a signal.

## Audit cadence (lightweight)

The audit is cheap (a scan of the last message), so the default cadence is
**every Yielding_Turn**. A `sampling_rate` knob (e.g., in
`config/bootcamp_preferences.yaml`) allows reducing it to a sampled subset if
ever needed; sampling never changes the self-correction behavior when the audit
does run. The audit is skipped entirely for non-yielding turns, silent
internal-file pass-throughs, and the DEFAULT-OUTPUT single period.

## Self-correction output

On violation the audit emits a short, non-blocking instruction that mirrors the
existing compound-question rewrite:

- **Zero 👉 (dead-end):** "This turn ended without a leading question — re-render
  it to end with exactly one 👉 question the bootcamper can answer."
- **Two-plus 👉:** "This turn ended with N leading questions — re-render ending
  with exactly one; if these are alternatives, present a single lead question
  with a numbered list."

The output never adds a second 👉 and never restructures non-question content.

## Interaction with existing hooks/specs

- **`write-policy-gate` (PreToolUse):** unchanged; still owns write-time
  compound/ambiguity validation. The audit is the read-time count check.
- **`ask-bootcamper` Phase 1:** unchanged behavior (adds a closing question when
  none exists); the audit runs after it and catches the residual zero/two-plus
  cases and confirms the one-👉 result.
- **`leading-question-enforcement` / `single-ask-question-guarantee` /
  `clean-question-presentation`:** the audit is the runtime spot-check layer for
  the invariants those specs define; it references them rather than redefining.

## Non-blocking guarantee

The audit is advisory (Soft_Block at most). Any failure to evaluate degrades to a
silent no-op. It never becomes a ⛔ gate and never permanently blocks progress,
consistent with the bootcamp's never-block principle.

## Consistency tasks (build-time)

- Regenerate the hook registry + lock (`sync_hook_registry.py --write`);
  `--verify` must pass.
- Re-sync `steering-index.yaml` token counts + budget total for
  `hook-registry-critical.md`; `measure_steering.py --check` must pass.

## Correctness properties

- **P1 (soundness):** for any rendered Yielding_Turn, the audit flags it **iff**
  the 👉 leading-question count is not exactly one (with the exclusions above).
- **P2 (non-yielding safety):** for any non-yielding / pass-through / period
  turn, the audit produces no output.
- **P3 (no self-worsening):** the self-correction output contains at most one 👉
  and no compound question.
- **P4 (non-blocking):** for any input or internal error, the audit never blocks
  the turn (exit/produce-nothing on error).

## Testing notes

Property/example tests over synthetic rendered turns (zero/one/many 👉, 👉 in
code fences, quoted examples, blockquote/bold-wrapped 👉) asserting P1-P4,
following the repo's `sys.path`-import, class-based pytest + Hypothesis
conventions. Tests are optional at spec time.
