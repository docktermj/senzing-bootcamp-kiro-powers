# Design Document: Setup Summary Persistence

## Overview

Persist the end-of-preface Administrative Setup Summary as a structured
`setup_summary` object in `config/bootcamp_progress.json`, written at onboarding
§4.0 (the moment the summary is presented), and replay it on session resume. The
change is additive, non-blocking, and secret-free.

## Data model — `setup_summary` (in the Progress_File)

```json
{
  "setup_summary": {
    "captured_at": "2026-07-14T13:49:00-05:00",
    "power_version": "X.Y.Z",
    "mcp_reachable": true,
    "directories_created": true,
    "hooks_installed": {
      "count": 4,
      "names": ["ask-bootcamper", "review-bootcamper-input",
                "code-style-check", "write-policy-gate", "session-log-events"]
    },
    "steering_generated": ["product.md", "tech.md", "structure.md"],
    "preflight_verdict": "WARN",
    "preflight_warnings": ["Senzing SDK not installed — Module 2 will cover it"],
    "deferrals": ["runtime install declined (revisit in Module 2)"]
  }
}
```

- Every value is derived from the **real** outcomes of onboarding Steps 0b-2 —
  never hardcoded. `hooks_installed` mirrors the authoritative record onboarding
  already writes to `config/bootcamp_preferences.yaml` (`hooks_installed` key),
  so the two never diverge; `setup_summary` is the resume-facing snapshot.
- Contains only names/counts/versions/verdicts — **no** secrets, tokens, or
  connection strings.

## Write path (onboarding §4.0)

When the Administrative Setup Summary is presented:

1. Assemble the `setup_summary` object from the outcomes already computed in
   Steps 0b (MCP health), 0c (version), 1 (directories, hooks + verified count,
   steering), and 2 (preflight verdict + warnings, deferrals from 2a-2d).
2. Merge it into the Progress_File (read-modify-write that preserves
   `modules_completed`, `current_step`, `step_history`, the Question_Ledger, and
   all other keys). In team mode, write to the member-specific progress file.
3. Non-blocking: if the merge fails, log a warning and continue — the summary is
   still presented this session, just not persisted.

This reuses the existing progress-write discipline (the same read-modify-write
pattern used for checkpoints); it adds no new hook and no per-write cost.

## Replay path (`session-resume.md`)

On resume, after the existing progress reconstruction:

1. If `setup_summary` exists, present a concise, verbosity-aware recap:
   "Your environment already has: Senzing project directories, N background
   quality-check hooks, foundational steering, and a [PASS/WARN] preflight
   (power vX.Y.Z)." Mark any failed/deferred item and where it is revisited.
2. If `setup_summary` is absent (older projects / write failed), skip silently
   and resume unchanged.
3. Orientation-only: no question, no gate, no re-running of setup.

## Schema validation

Document the `setup_summary` shape alongside the Progress_File schema and extend
the `progress-file-schema-validation` validator to accept and lightly validate
the block (types + no unexpected secret-like fields), so a malformed block is
surfaced rather than silently mis-read. A missing block is valid (backward
compatible).

## Correctness properties

- **P1 (fidelity):** each persisted field equals the corresponding real
  onboarding outcome; no field is fabricated.
- **P2 (additive):** writing `setup_summary` preserves every other Progress_File
  key byte-for-byte except the added block.
- **P3 (secret-free):** the block never contains secrets/tokens/connection
  strings.
- **P4 (backward compatible):** resume works whether or not `setup_summary`
  exists; absence is never an error.
- **P5 (non-blocking):** a write or read failure never blocks onboarding or
  resume.

## Testing notes

Example/property tests: build a Progress_File with arbitrary existing keys, write
`setup_summary`, assert P2 (other keys unchanged) and P1/P3 (fields fidelity, no
secret-like keys); resume with and without the block asserts P4. Follow repo
pytest conventions. Tests optional at spec time.
