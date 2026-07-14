# Design Document: Guaranteed Q&A Capture

## Overview

Q&A capture moves from *agent-voluntary emission* to *hook-enforced capture on
the Q&A cadence*, driven by the two existing critical hooks and a small
deterministic helper. The design threads the needle between two prior specs:

- `bootcamp-qa-transcript` (superseded): defined the transcript and the
  voluntary, event-driven emission.
- `session-log-hook-performance` (preserved): removed per-write logging and
  forbids per-write hooks. The new capture fires on the **Q&A cadence** (Stop /
  UserPromptSubmit), not the write cadence, so it honors this constraint.

The architectural constraint that shapes the design: `sync_hook_registry.py`
reads exactly one hook per file (`hooks[0]`), and both critical hooks are
`agent`-type. Capture is therefore folded into the existing agent-hook **prompts**
(each instructs the hook to run the helper), backed by a deterministic helper
script that does the actual, schema-correct logging.

## Components

### QA_Helper — `senzing-bootcamp/scripts/log_qa_event.py`

Stdlib-only, non-blocking (exits 0 on every path), reuses `session_logger`.

```
record-question   # reads config/.question_pending; logs the question idempotently
record-answer     # reads answer from stdin; pairs to the pending question; self-heals
```

State files (in the bootcamper's workspace `config/`, never shipped):

- `config/.question_pending` — existing marker; the question **text** source.
- `config/.qa_capture.json` — new sidecar: `{ "question_id", "text_hash" }` for
  pairing the answer and de-duplicating a re-presented question.

Pairing/dedupe logic:

- `record-question`: if `.question_pending` absent → no-op; else hash the text;
  if the sidecar's `text_hash` matches → no-op (already logged); else generate a
  `question_id`, append a `question` event, write the sidecar.
- `record-answer`: read stdin; if empty → no-op; if sidecar present → use its
  `question_id`; else if `.question_pending` present → self-heal (log the
  question, get a `question_id`); else → no-op (no orphan answers). Append the
  `answer` event, then delete the sidecar.

### Hook wiring (no new hooks, no per-write hook)

- **`ask-bootcamper` (Stop, agent).** A "Q&A CAPTURE (silent side effect)"
  instruction runs `log_qa_event.py record-question` when `.question_pending`
  exists, explicitly not counting as visible output and not changing the
  DEFAULT-OUTPUT period rule.
- **`review-bootcamper-input` (UserPromptSubmit, agent).** An "ANSWER CAPTURE
  (silent side effect)" instruction runs `log_qa_event.py record-answer` with the
  bootcamper's verbatim message on stdin (heredoc), before the existing
  trigger-phrase checks.

Because these are agent hooks, capture is delivered by the hook prompt **every**
Stop / UserPromptSubmit — it no longer depends on the agent recalling always-on
steering. The `record-answer` **self-heal** makes the answer path robust even if
the Stop-side `record-question` is occasionally skipped: it logs both the
question and the answer at answer time.

## Layered guarantee

1. **Ask-time** — `record-question` logs the question at Stop (new).
2. **Answer-time** — `record-answer` logs (and self-heals) at UserPromptSubmit
   (new). Together these capture Q&A *as it happens*, closing the
   abandoned-mid-module gap from D2.
3. **Module completion** — `ask-bootcamper` Phase 0 captures verified `Questions
   & Responses` into the recap (existing).
4. **Stopping points** — `reconcile_transcript.py` backfills the transcript from
   the recap (existing).
5. **Graduation** — `enforce-critical-artifacts` → `ensure_graduation_artifacts.py`
   reconstructs from all sources and blocks "done" until artifacts exist
   (existing).

"Guaranteed" means hook-enforced given the hooks are installed — the same
asterisk that applies to every hook-based bootcamp guarantee. Onboarding installs
and verifies the critical hooks; the capture-hook safeguard reminds (as a
Soft_Block) if one goes missing. This design deliberately keeps that safeguard a
Soft_Block to honor the never-block-the-bootcamper principle.

## Determinism and safety

- The helper is pure/deterministic given its inputs; all I/O is wrapped so any
  error yields exit 0 (never blocks).
- Idempotent question logging (text-hash dedupe) makes session-resume
  re-presentation safe.
- No orphan answers (record-answer no-ops without a pending question).
- Zero cost on write-only turns (capture is off the write path entirely).

## Consistency tasks (build-time)

- Regenerate the registry + lock (`sync_hook_registry.py --write`); `--verify`
  must pass.
- Re-sync `steering-index.yaml` token counts for `hook-registry-critical.md` and
  `qa-transcript.md`, plus the budget total; `measure_steering.py --check` must
  pass.
- Record `bootcamp-qa-transcript` as superseded by this spec in
  `.kiro/spec-catalog.yaml`; regenerate `.kiro/SPEC_CATALOG.md`.

## Testing notes

The helper is a strong fit for example/property tests (temp workspace, feed a
`.question_pending`, assert paired events, dedupe, self-heal, and no-ops). Tests
are optional here and follow the repository's `sys.path`-import, class-based
pytest conventions if added.
