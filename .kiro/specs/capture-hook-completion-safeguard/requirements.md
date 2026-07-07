# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion A ("whole bootcamp") of the Senzing Bootcamp
> improvement review (`x.md`). Requirements below are a starting point for refinement, not a
> finished spec.

## Introduction

The three **capture-critical** hooks — `session-log-events`, `module-recap-append`, and
`ask-bootcamper` — feed the recap (`docs/bootcamp_recap.md`), the Q&A transcript
(`docs/bootcamp_transcript.md`), and the completion summary (`docs/completion_summary.md`). They are
created on the `createHook`-from-registry path at session start and can also be installed via
`scripts/install_hooks.py --essential`.

Today, their presence is guaranteed only if `createHook` succeeds during onboarding. If `createHook`
fails (and the bootcamper never runs `install_hooks.py`), the only safety net is the
**Capture-Critical Warn-on-Absence Check** in `session-resume-phase2-setup-recovery.md`, which is
"advisory only — never blocks." A bootcamper can therefore proceed module after module with a
capture-critical hook missing, silently degrading the recap, transcript, and completion summary,
and the degradation surfaces only at track completion when the deliverables are thin.

The existing `hook-architecture-improvements` spec (Requirement 10) deliberately keeps the check
warn-only. This feature adds the stronger angle the review calls for: a **recurring reminder** and a
**soft block at module completion** when a capture-critical hook is absent — a stop-and-confirm the
bootcamper can override, not a hard gate — so the absence is acknowledged rather than silently
carried forward. It must not weaken or duplicate the existing session-start warn-on-absence check.

## Glossary

- **Capture_Critical_Hooks**: `session-log-events`, `module-recap-append`, `ask-bootcamper` — the
  hooks whose absence silently degrades the recap, transcript, and completion summary.
- **Warn_On_Absence_Check**: the existing advisory, non-blocking check in
  `session-resume-phase2-setup-recovery.md` run at session start.
- **Module_Completion_Safeguard**: the new check, run at each module-completion boundary, that
  detects missing Capture_Critical_Hooks and prompts the bootcamper to install them before
  continuing.
- **Soft_Block**: a stop-and-confirm prompt the bootcamper may explicitly override to continue; it
  is not a Mandatory_Gate (⛔) and never permanently blocks progress.

## Requirements

### Requirement 1: Detect missing capture-critical hooks at module completion

**User Story:** As a bootcamper, I want the bootcamp to notice at each module boundary when a
capture-critical hook is missing, so that my recap, transcript, and completion summary are not
silently degrading module after module.

#### Acceptance Criteria

1. WHEN a module-completion boundary is reached, THE Module_Completion_Safeguard SHALL inspect the
   bootcamper's `.kiro/hooks` directory for each of the three Capture_Critical_Hooks.
2. IF any Capture_Critical_Hook `<id>.kiro.hook` file is absent, THEN the safeguard SHALL name the
   specific missing hook(s) and the output(s) they feed (recap, transcript, and/or completion
   summary).
3. WHEN all three Capture_Critical_Hooks are present, THE safeguard SHALL make no output (silent
   no-op) and SHALL NOT delay the module transition.

### Requirement 2: Recurring reminder plus soft block

**User Story:** As a bootcamper, I want a clear, repeated prompt to install a missing capture hook
before I move on, so that I can fix it while it still matters instead of discovering thin
deliverables at graduation.

#### Acceptance Criteria

1. WHEN a Capture_Critical_Hook is missing at a module-completion boundary, THE safeguard SHALL
   present the two existing install options (re-create via `createHook` from the hook registry, or
   `python3 senzing-bootcamp/scripts/install_hooks.py --essential`) and pause as a Soft_Block.
2. WHERE the bootcamper explicitly chooses to continue without installing, THE safeguard SHALL
   record the acknowledgment and allow the module transition to proceed.
3. WHILE a Capture_Critical_Hook remains missing across subsequent module boundaries, THE safeguard
   SHALL re-present the reminder at each boundary (recurring), rather than suppressing after a single
   acknowledgment.
4. THE Soft_Block SHALL NOT be a Mandatory_Gate (⛔) and SHALL never permanently block progress.

### Requirement 3: Consistency with the existing warn-on-absence check

**User Story:** As a maintainer, I want the new safeguard to complement the existing session-start
check rather than duplicate or contradict it.

#### Acceptance Criteria

1. THE feature SHALL NOT remove or weaken the existing session-start Warn_On_Absence_Check in
   `session-resume-phase2-setup-recovery.md` (preserve `hook-architecture-improvements`
   Requirement 10).
2. THE feature SHALL reuse the same Capture_Critical_Hooks list and the same install options as the
   Warn_On_Absence_Check so the two checks stay in sync.
3. THE feature SHALL NOT add or modify any `preToolUse` write-tool hook and SHALL NOT change the
   behavior of the capture-critical hooks themselves.

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want tests so the safeguard does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests covering: detection of each missing Capture_Critical_Hook,
   the all-present silent no-op, the recurring re-prompt across multiple boundaries, and the
   explicit-override continue path.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   the appropriate `tests/` directory.
