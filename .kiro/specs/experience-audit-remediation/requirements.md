# Requirements Document: Experience Audit Remediation

## Introduction

This spec is the actionable output of a Bootcamper-experience audit of the
`senzing-bootcamp` power. The audit classified every stage of the bootcamp
(whole bootcamp, administration, preface, each module, graduation) into
experiences that are **guaranteed**, **probable**, or **prevented**, then
compared those expected experiences against the intents recorded in
`.kiro/specs/` (283 implemented specs, 2 superseded per `.kiro/SPEC_CATALOG.md`).

The purpose of this spec is not to re-describe the bootcamp. It records the
**discrepancies** the audit found — places where a spec/bugfix intent and the
delivered experience diverge — and, for each, a decision to **remove**,
**modify**, or **implement**, with the concrete action that carries it out.

Scope note (honesty about coverage): the audit verified the high-signal
behaviors that map directly to the guaranteed/probable/prevented categories and
used the generated `SPEC_CATALOG.md` supersession data. It did not re-execute
all 283 "implemented" specs at runtime; "implemented" in the catalog means every
`tasks.md` checkbox is checked, which for behavioral (steering) specs is a
task-completion signal, not a runtime guarantee.

## Glossary

- **Guaranteed_Experience**: An experience enforced by a hook, a mandatory gate
  (⛔), an always-run step, or a Stop-time enforcement script — it happens
  regardless of agent discretion.
- **Probable_Experience**: An experience produced by steering the agent follows
  by discipline (offers, voluntary logging, ask-once ledger) — highly likely but
  not hook-enforced.
- **Prevented_Experience**: An experience the design explicitly disallows
  (agent answering a 👉 question, skipping a ⛔ gate, compound questions, direct
  SQL, root-directory file placement).
- **Disposition**: One of `remove`, `modify`, or `implement` — the decision for
  a discrepancy.

## Discrepancies and Dispositions

### Requirement 1: Retire the superseded self-answering specs (Disposition: remove / keep-as-superseded)

**Finding.** `self-answering-questions-fix` and `self-answering-prevention-v2`
are recorded as `superseded` in `.kiro/SPEC_CATALOG.md` (chain:
`self-answering-questions-fix` → `self-answering-prevention-v2` →
`self-answering-reinforcement`). The requested experience — the agent never
answers its own 👉 question — is a **Prevented_Experience** today, delivered by
the current `Answer_Required_Rule` (`conversation-protocol.md`,
`agent-behavior-rules.md`) and the surviving `self-answering-reinforcement`
spec. The two older specs are redundant historical artifacts.

#### Acceptance Criteria

1. WHEN a maintainer inspects the self-answering line of work, THE catalog SHALL
   continue to mark the two older specs `superseded` with a resolvable
   supersession chain to `self-answering-reinforcement`.
2. THE remediation SHALL NOT delete the superseded spec directories by default
   (repository convention preserves historical specs and their references); the
   `superseded` status in `spec-catalog.yaml` is the retained "means" of
   retirement.
3. WHERE a maintainer chooses physical removal instead, THE removal SHALL delete
   both directories and their `spec-catalog.yaml` supersession entries together,
   then regenerate `.kiro/SPEC_CATALOG.md`.

### Requirement 2: Reconcile the "every question and response is logged" guarantee (Disposition: modify docs; implement optional)

**Finding.** The Bootcamper-experience goal "every question and response is
logged for the graduation recap" is delivered as a **Probable_Experience**, not
a **Guaranteed_Experience**, mid-module. Q&A events are emitted **voluntarily**
by the agent (`qa-transcript.md`) and are deliberately **decoupled from file
writes** for performance (`session-log-hook-performance` spec removed per-write
logging). The transcript/recap become faithful only via reconciliation at
stopping points (`reconcile_transcript.py`, `completion_artifacts.py --backfill`)
and are hard-**guaranteed** only at track-completion/graduation by the
`enforce-critical-artifacts` Stop hook (`ensure_graduation_artifacts.py`).

The tension is intentional (faithfulness vs. per-write cost) and mostly closed
by reconciliation, but a window remains: a session that ends abruptly
mid-module, before any stopping point, can under-represent Q&A in the live log.

#### Acceptance Criteria

1. THE steering SHALL state, where the "logged for the recap" guarantee is
   described, the explicit guarantee boundary: Q&A capture is best-effort and
   event-driven mid-module, reconciled at every stopping point, and hard
   guaranteed at track completion / graduation.
2. THE modification SHALL NOT reintroduce a per-write Q&A hook (that regression
   is explicitly forbidden by `qa-transcript.md` and `session-log-hook-performance`).
3. WHERE stronger mid-module capture is desired (optional implement path), THE
   implementation SHALL reconcile the transcript at additional non-write
   boundaries (e.g., module-completion boundary, already a natural checkpoint)
   without adding any per-write hook, and SHALL remain idempotent and
   non-blocking.

### Requirement 3: Deliver an end-of-preface administrative-setup summary (Disposition: implement — DONE)

**Finding.** The administration experience "at the end of the preface, let the
Bootcamper know what was done during administrative setup" was **not** delivered.
Onboarding announced "Administrative setup is complete" (`onboarding-phase1b-intro-language.md`
Step 4) but never enumerated what ran (directories, hooks + count, steering,
MCP health, version, preflight verdict). No prior spec requested this summary,
so it was a gap in the administration experience rather than a spec discrepancy.

#### Acceptance Criteria

1. WHEN administrative setup completes and before the welcome banner, THE agent
   SHALL present a brief, scannable recap of what setup actually did, drawn only
   from the real outcomes of onboarding Steps 0b–2 (never a hardcoded list).
2. THE recap SHALL honor the bootcamper's verbosity preset and SHALL state any
   failed or deferred setup item plainly, noting where it is revisited.
3. THE recap SHALL be orientation-only (no 👉 question, no wait); the first
   onboarding question remains the detail-level step (4a).
4. Status: **implemented** in `onboarding-phase1b-intro-language.md` (new
   subsection "4.0 Administrative Setup Summary"); steering token counts and the
   budget total in `steering-index.yaml` re-synced; `measure_steering.py --check`
   and `validate_commonmark.py` pass.

## Non-Goals

- Re-auditing or re-verifying every implemented spec at runtime.
- Adding any per-write hook for Q&A logging.
- Deleting historical/superseded spec directories by default.
