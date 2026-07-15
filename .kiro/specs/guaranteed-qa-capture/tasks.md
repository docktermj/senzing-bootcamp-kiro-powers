# Implementation Plan: Guaranteed Q&A Capture

- [x] 1. Create the deterministic capture helper
  - Add `senzing-bootcamp/scripts/log_qa_event.py` (stdlib-only, non-blocking,
    reuses `session_logger`): `record-question` (reads `.question_pending`,
    idempotent via text-hash sidecar) and `record-answer` (reads stdin, pairs via
    sidecar, self-heals, no orphan answers).
  - Smoke-tested: paired ids, dedupe, self-heal, and safe no-ops.
  - _Requirements: 1.2, 1.3, 1.4, 2.2, 2.3, 2.4, 2.5, 4.1_

- [x] 2. Fold question capture into `ask-bootcamper` (Stop)
  - Add a "Q&A CAPTURE (silent side effect)" instruction that runs
    `log_qa_event.py record-question` when `config/.question_pending` exists,
    without changing the DEFAULT-OUTPUT period rule.
  - _Requirements: 1.1, 1.5, 3.4_

- [x] 3. Fold answer capture into `review-bootcamper-input` (UserPromptSubmit)
  - Add an "ANSWER CAPTURE (silent side effect)" instruction that runs
    `log_qa_event.py record-answer` with the bootcamper's verbatim message on
    stdin, before the existing trigger-phrase checks.
  - _Requirements: 2.1, 2.6, 3.4_

- [x] 4. Update `qa-transcript.md` steering
  - Describe the hook-enforced mechanism; preserve the no-per-write-hook /
    zero-cost-on-write-only-turns constraints and the `session-log-events`
    leave-alone rule; keep the guaranteed-transcript cross-reference.
  - _Requirements: 3.1, 3.2, 3.3, 4.3, 5.2_

- [x] 5. Regenerate registry + lock and re-sync steering budget
  - `python3 senzing-bootcamp/scripts/sync_hook_registry.py --write`; `--verify`
    passes.
  - Re-sync `steering-index.yaml`: `hook-registry-critical.md` 12859→13182,
    `qa-transcript.md` 1284→1097, budget total 226721→226857;
    `measure_steering.py --check` passes.
  - _Requirements: 5.1, 5.2_

- [x] 6. Record supersession and regenerate the spec catalog
  - Add `guaranteed-qa-capture supersedes bootcamp-qa-transcript` to
    `.kiro/spec-catalog.yaml`; regenerate `.kiro/SPEC_CATALOG.md`;
    `generate_spec_catalog.py --check` passes.
  - _Requirements: 5.3_

- [x] 7*. (Optional) Add property/example tests for `log_qa_event.py`
  - Temp-workspace tests: paired events, text-hash dedupe, self-heal, empty/no
    pending no-ops, non-blocking on unreadable inputs. Follow the repo's
    `sys.path`-import, class-based pytest + Hypothesis conventions.
  - _Requirements: 1.3, 2.3, 2.4, 4.1_

- [x] 8. Confirm safeguard remains a Soft_Block (no change)
  - Verified `module-completion.md` is unchanged — the Capture-Critical Hook
    Safeguard is still an advisory Soft_Block (never a ⛔ mandatory gate), and
    `capture_hook_safeguard.py` was not modified. The never-block principle holds.
  - _Requirements: 4.2_
