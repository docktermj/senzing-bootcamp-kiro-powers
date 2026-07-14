# Design Document: Early fpdf2 Hint

## Overview

Surface the existing `fpdf2` availability hint **once, during Module 1**, when
`fpdf2` is absent, so the bootcamper has time to `pip install fpdf2` before
graduation and receive the professionally-designed recap PDF. The change reuses
the existing `scripts/fpdf2_preflight.py` helper, is non-blocking and one-time,
and keeps `fpdf2` an optional, lazily-imported dependency.

## Where the hint fires

Module 1 (`module-01-*.md`), at a natural non-interrupting point — the module
completion recap is the cleanest spot (orientation-only, no pending question).
At that point:

1. Run `python3 senzing-bootcamp/scripts/fpdf2_preflight.py`.
2. If it prints a hint line (fpdf2 absent), surface it to the bootcamper with a
   one-line framing that installing `fpdf2` upgrades the *final* recap PDF and
   that a valid PDF is produced either way (never a requirement).
3. If it prints nothing (fpdf2 present), stay silent.

This mirrors how `module-completion-track.md` and graduation Step 0b.0 already
invoke the same helper — the only new thing is the earlier surface.

## One-time behavior (no nagging)

- After surfacing the Early_Hint, set a `fpdf2_hint_shown: true` flag in
  `config/bootcamp_preferences.yaml`.
- Before surfacing, check the flag; if already set, do nothing. This bounds the
  hint to at most once per project, regardless of session resumes or module
  revisits.
- If `fpdf2` is present at Module 1, no hint and no flag write are needed
  (nothing to show); if it is later removed, the graduation-time preflight still
  covers the case.

## Non-blocking and optional

- The hint is orientation-only: no 👉 question, no gate, no required action, no
  auto-install during Module 1.
- If `fpdf2_preflight.py` cannot run (missing script, error), proceed silently;
  the hint may surface at the next natural opportunity, and the graduation-time
  preflight remains the backstop.

## Keeping fpdf2 optional

- No top-level `import fpdf`; the helper only *detects* availability. The
  best-effort auto-install stays solely in the graduation-time tiered render
  path (`generate_recap_pdf.py` and friends), unchanged.
- This feature adds only a detection + one-line message + a preference flag.

## Correctness properties

- **P1 (early + conditional):** the hint is surfaced during Module 1 iff `fpdf2`
  is absent and the Hint_Shown_Flag is unset.
- **P2 (one-time):** after surfacing, the flag is set and the hint is never
  repeated.
- **P3 (silent when present):** when `fpdf2` is available, nothing is surfaced.
- **P4 (non-blocking / optional):** the hint never asks a question, gates, or
  installs; a preflight failure degrades to a silent no-op.
- **P5 (fpdf2 stays optional):** no new hard dependency and no module-top-level
  `fpdf` import; graduation-time behavior is unchanged.

## Testing notes

Steering-content + light behavior tests: assert the Module 1 steering invokes
`fpdf2_preflight.py` at a non-interrupting point, frames the hint as an upgrade
(not a requirement), guards on the `fpdf2_hint_shown` flag, and adds no 👉
question/gate. Optionally, a preference round-trip test for the flag. Follow repo
pytest conventions. Tests optional at spec time.
