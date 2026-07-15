# Implementation Plan: Setup Summary Persistence

- [x] 1. Define and document the `setup_summary` schema
  - Add the block shape to the Progress_File schema docs (fields: captured_at,
    power_version, mcp_reachable, directories_created, hooks_installed{count,
    names}, steering_generated, preflight_verdict, preflight_warnings,
    deferrals). Secret-free.
  - _Requirements: 1.2, 3.2_

- [x] 2. Write `setup_summary` at onboarding §4.0
  - In `onboarding-phase1b-intro-language.md` §4.0, after presenting the summary,
    merge a `setup_summary` object built from the real Step 0b-2 outcomes into
    `config/bootcamp_progress.json` (member-specific file in team mode), using a
    read-modify-write that preserves all other keys. Mirror (not duplicate) the
    `hooks_installed` record already in `bootcamp_preferences.yaml`. Non-blocking.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.3_

- [x] 3. Replay on resume in `session-resume.md`
  - After progress reconstruction, if `setup_summary` exists present a concise,
    verbosity-aware "your environment already has…" recap; mark failed/deferred
    items and where they're revisited; orientation-only (no question, no
    re-running). If absent, proceed unchanged.
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Extend schema validation
  - Teach `progress-file-schema-validation` (or its validator script) to accept
    and lightly validate the `setup_summary` block; a missing block stays valid.
  - _Requirements: 3.1_

- [x] 5*. (Optional) Tests
  - Additive-write preservation (P2), field fidelity + secret-free (P1/P3),
    resume-with/without-block (P4), non-blocking on I/O error (P5). Follow repo
    pytest conventions.
  - _Requirements: 1.x, 2.x, 3.x_
