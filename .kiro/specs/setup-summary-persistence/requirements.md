# Requirements Document: Setup Summary Persistence

## Introduction

The `experience-audit-remediation` change added an end-of-preface
**Administrative Setup Summary** (`onboarding-phase1b-intro-language.md`
§4.0) that tells the bootcamper what the quiet setup phase actually did — MCP
reachability, power version, directories created, hooks installed (with the
verified count), foundational steering generated, and the preflight verdict.

That summary is presented **once** and then lost. On session resume, the
bootcamper (or a returning agent) has no durable, structured record of "here's
what your environment already has," so `session-resume.md` cannot replay it and
may re-narrate or re-check things that were already done during onboarding.

This feature persists the setup summary as a structured `setup_summary` block in
`config/bootcamp_progress.json` at onboarding time, and has `session-resume.md`
read and replay it on resume. It complements `session-resume`,
`session-persistence`, `progress-file-schema-validation`, and
`experience-audit-remediation`.

## Glossary

- **Setup_Summary**: the structured record of what administrative setup did,
  derived only from the real outcomes of onboarding Steps 0b-2.
- **Progress_File**: `config/bootcamp_progress.json` (single-user) or the
  member-specific progress file in team mode.
- **Replay**: presenting, on resume, a concise "your environment already has…"
  recap built from the persisted Setup_Summary.

## Requirements

### Requirement 1: Persist the setup summary at onboarding time

**User Story:** As a returning bootcamper, I want the record of what setup did to
survive the session, so resume can remind me what my environment already has.

#### Acceptance Criteria

1. WHEN the Administrative Setup Summary is presented (onboarding §4.0), THE
   agent SHALL write a `setup_summary` object into the Progress_File.
2. THE `setup_summary` SHALL be populated **only** from the real outcomes of
   onboarding Steps 0b-2 (never hardcoded), with fields for: `mcp_reachable`,
   `power_version`, `directories_created`, `hooks_installed` (list + count),
   `steering_generated` (list), `preflight_verdict` (PASS/WARN/FAIL) and any
   `preflight_warnings`, `deferrals` (e.g., declined runtime install), and a
   `captured_at` ISO-8601 timestamp.
3. THE write SHALL be additive/merge — it SHALL NOT overwrite unrelated
   Progress_File content (module progress, ledger, checkpoints).
4. WHERE onboarding already records related state elsewhere (e.g.,
   `hooks_installed` in `config/bootcamp_preferences.yaml`), THE `setup_summary`
   SHALL reference/mirror rather than contradict it (single source of truth
   preserved; no divergent duplicate).
5. WHERE the write fails, onboarding SHALL continue (non-blocking) and the
   summary remains a presentation-only artifact for that session.

### Requirement 2: Replay on session resume

**User Story:** As a returning bootcamper, I want resume to remind me what my
environment already has so I don't redo setup.

#### Acceptance Criteria

1. WHEN a session resumes AND a `setup_summary` exists in the Progress_File, THE
   `session-resume.md` flow SHALL present a concise "your environment already
   has…" recap drawn from it (verbosity-aware).
2. THE Replay SHALL clearly mark any item recorded as failed or deferred and
   note where it is revisited (usually Module 2).
3. WHEN no `setup_summary` exists (older projects, or the write failed), THE
   resume flow SHALL proceed unchanged with no error.
4. THE Replay SHALL be orientation-only — it SHALL NOT ask a question or block,
   and SHALL NOT re-run setup steps; it only reports the recorded state.

### Requirement 3: Schema validation and safety

#### Acceptance Criteria

1. THE `setup_summary` schema SHALL be documented alongside the Progress_File
   schema and covered by `progress-file-schema-validation` (or its validator)
   so a malformed block is detected rather than silently mis-read.
2. THE `setup_summary` SHALL contain no secrets, credentials, tokens, or
   connection strings (only names, counts, versions, verdicts).
3. IN team mode, THE `setup_summary` SHALL be written to the member-specific
   progress file, consistent with the rest of progress tracking.

## Non-Goals

- Re-running or re-verifying setup on resume (Replay is report-only).
- Moving the authoritative `hooks_installed` record out of
  `config/bootcamp_preferences.yaml` (this feature mirrors, not migrates).
- Changing the onboarding setup steps themselves.
