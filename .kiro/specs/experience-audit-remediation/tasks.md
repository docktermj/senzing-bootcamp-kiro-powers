# Implementation Plan: Experience Audit Remediation

Each task carries an explicit **Disposition** (remove / modify / implement) and
the concrete action that resolves the discrepancy. Optional tasks are marked `*`.

- [x] 1. (Disposition: keep-as-superseded / remove) Confirm retirement of the superseded self-answering specs
  - Verify `spec-catalog.yaml` records the chain `self-answering-questions-fix`
    → `self-answering-prevention-v2` → `self-answering-reinforcement` and that
    `SPEC_CATALOG.md` shows both older specs as `superseded`.
  - Default: no directory deletion (retain history); the `superseded` status is
    the retirement record.
  - _Requirements: 1.1, 1.2_

  - [x] 1.1* (Disposition: remove — only if maintainer opts in) Physically delete the superseded specs
    - `rm -rf .kiro/specs/self-answering-questions-fix .kiro/specs/self-answering-prevention-v2`
    - Remove both supersession entries from `.kiro/spec-catalog.yaml`.
    - Regenerate: `python3 senzing-bootcamp/scripts/generate_spec_catalog.py`
    - _Requirements: 1.3_

- [x] 2. (Disposition: modify) Document the Q&A "logged for the recap" guarantee boundary
  - In `qa-transcript.md` (and/or the recap-facing note in
    `module-completion-artifacts.md`), add one explicit sentence: Q&A capture is
    best-effort/event-driven mid-module, reconciled at every stopping point, and
    hard-guaranteed at track completion / graduation via
    `enforce-critical-artifacts` → `ensure_graduation_artifacts.py`.
  - Do NOT add a per-write Q&A hook (forbidden regression).
  - Re-sync `steering-index.yaml` token counts + budget total; run
    `measure_steering.py --check` and `validate_commonmark.py`.
  - _Requirements: 2.1, 2.2_

  - [x] 2.1* (Disposition: implement — optional stronger capture) Reconcile the transcript at the module-completion boundary
    - Add a `reconcile_transcript.py` (no-arg, idempotent) call to the
      module-completion step ordering in `module-completion.md`, after the
      consolidated recap append, so mid-bootcamp sessions self-heal the log at
      each module boundary — not only at stopping points.
    - Keep it non-blocking and add no per-write hook or per-write process spawn.
    - _Requirements: 2.3_

- [x] 3. (Disposition: implement — DONE) End-of-preface administrative-setup summary
  - Added subsection "4.0 Administrative Setup Summary" to
    `onboarding-phase1b-intro-language.md` (report only what actually ran in
    Steps 0b–2; verbosity-aware; surface failures/deferrals; orientation-only).
  - Re-synced `steering-index.yaml` (phase + file token_count 1734→1986; budget
    total 226469→226721).
  - Verified: `measure_steering.py --check` exit 0; `validate_commonmark.py` exit 0.
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Regenerate the spec catalog after any change in tasks 1–2
  - `python3 senzing-bootcamp/scripts/generate_spec_catalog.py`
  - `python3 senzing-bootcamp/scripts/generate_spec_catalog.py --check` (exit 0)
  - _Requirements: 1.3_
