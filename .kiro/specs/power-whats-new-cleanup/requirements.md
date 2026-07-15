# Requirements Document

## Introduction

The `senzing-bootcamp` Kiro Power ships `senzing-bootcamp/POWER.md`, which currently
carries five hand-written "What's New in X.Y.Z" sections: `0.2.0`, `0.1.3`, `1.0.0`
(retained as a historical note because the `1.0.0` tag was premature and later withdrawn),
`0.12.1`, and `0.12.0`. The frontmatter `version` is `0.2.0`.

These sections are maintained by hand and sit **outside** the generator-owned regions of
POWER.md (the `<!-- BEGIN GENERATED: ... -->` / `<!-- END GENERATED: ... -->` blocks for
the MCP tool list, hook list, steering table, and module table). No Python script parses
them and no CI gate reads their content, so they accumulate and drift: prior work
(`power-doc-drift-cleanup`) already had to correct stale point-in-time metric claims (for
example "pytest at 4,830 passed") embedded in these sections, and three of the current
sections (`0.12.0`, `0.12.1`, `1.0.0`) still carry such frozen numeric claims.

This feature is a **documentation-only** cleanup that prunes the per-version "What's New"
sections in POWER.md, deferring to `senzing-bootcamp/CHANGELOG.md` — the single source of
truth for the full release history — via the existing pointer sentence
"See the CHANGELOG for the full release history." The intent is to reduce drift risk and
clutter without changing any script, hook, steering logic, or test behavior, without
touching the generator-owned regions of POWER.md, and without affecting the separate
runtime "What's New" notification (`senzing-bootcamp/steering/whats-new.md`), which is
generated from CHANGELOG.md and `config/session_log.jsonl` and never reads POWER.md.

### Confirmed retention policy

The Maintainer has confirmed the retention policy. The requirements below are written
against this policy, which is now a set of decided facts:

- **Keep** exactly one section — the current release section (`What's New in 0.2.0`,
  matching the frontmatter `version`) — and add the CHANGELOG pointer sentence to it (it
  currently lacks one).
- **Remove** the four older sections: `0.1.3`, `1.0.0`, `0.12.1`, and `0.12.0`.
- The `1.0.0` withdrawn-tag note is removed, not retained, because the same versioning
  explanation already lives in the CHANGELOG "Versioning note" and the `## [1.0.0]` entry,
  so no release information is lost.
- Any retained section carries no frozen numeric point-in-time metric claim (test counts,
  lint-violation counts).

## Glossary

- **POWER.md**: The power configuration and documentation file at `senzing-bootcamp/POWER.md` that ships to users and is delivered to the agent as the activation overview.
- **Documentation_Cleanup**: The documentation-only change applied to POWER.md that removes or consolidates What's New content according to the confirmed Retention_Policy, changing no script, hook, steering logic, or test behavior.
- **Whats_New_Section**: A section of POWER.md introduced by a level-2 Markdown heading of the form `## What's New in X.Y.Z`, spanning from that heading up to the next level-2 heading.
- **Current_Version**: The semantic version recorded in the POWER.md YAML frontmatter `version` field, which is `0.2.0` at the time of writing.
- **Older_Whats_New_Section**: A Whats_New_Section whose version differs from the Current_Version; at the time of writing these are the sections for `0.1.3`, `1.0.0`, `0.12.1`, and `0.12.0`.
- **Retained_Whats_New_Section**: A Whats_New_Section that the confirmed Retention_Policy keeps in POWER.md.
- **Retention_Policy**: The confirmed rule set that determines which Whats_New_Sections remain in POWER.md after the Documentation_Cleanup.
- **CHANGELOG.md**: The release-history file at `senzing-bootcamp/CHANGELOG.md`, the single source of truth for the full release history.
- **CHANGELOG_Pointer**: The exact sentence "See the CHANGELOG for the full release history." that directs a reader to CHANGELOG.md.
- **Generated_Region**: A region of POWER.md bounded by a `<!-- BEGIN GENERATED: <id> -->` marker comment and its matching `<!-- END GENERATED: <id> -->` marker comment, whose content is owned by the power documentation generator.
- **Whats_New_Notification**: The runtime session-resume notification behavior defined by `senzing-bootcamp/steering/whats-new.md`, generated from CHANGELOG.md and `config/session_log.jsonl`.
- **Point_In_Time_Metric_Claim**: A statement of a specific measured value fixed to a past moment, such as a passing-test count (for example "pytest at 4,830 passed") or a lint-violation count.
- **CommonMark_Validator**: The `senzing-bootcamp/scripts/validate_commonmark.py` markdown validation check.
- **CI_Validation_Suite**: The gate sequence in `.github/workflows/validate-power.yml` — `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, and `sync_hook_registry.py --verify` — followed by the pytest suite.
- **Maintainer**: A maintainer of the `senzing-bootcamp` power who edits POWER.md and CHANGELOG.md.

## Requirements

### Requirement 1: Retain only the What's New sections named by the policy

**User Story:** As a Maintainer, I want POWER.md to keep only the What's New sections named by the confirmed Retention_Policy, so that per-version notes stop accumulating and drifting.

#### Acceptance Criteria

1. THE POWER.md SHALL contain exactly one Whats_New_Section.
2. THE Retained_Whats_New_Section SHALL correspond to the Current_Version recorded in the POWER.md frontmatter `version` field.
3. WHEN the Documentation_Cleanup is applied, THE Documentation_Cleanup SHALL remove every Older_Whats_New_Section from POWER.md.

### Requirement 2: Defer to the CHANGELOG for full release history

**User Story:** As a reader of POWER.md, I want the retained What's New content to point to CHANGELOG.md, so that the pruned per-version notes remain discoverable in one authoritative place.

#### Acceptance Criteria

1. THE Retained_Whats_New_Section SHALL end with the CHANGELOG_Pointer.
2. WHERE a reader seeks release history beyond the Current_Version, THE POWER.md SHALL direct that reader to CHANGELOG.md through the CHANGELOG_Pointer.
3. THE CHANGELOG.md SHALL contain a release entry for every version whose Older_Whats_New_Section the Documentation_Cleanup removes, so that no release information is lost.

### Requirement 3: Retained content carries no frozen point-in-time metric claim

**User Story:** As a Maintainer, I want the retained What's New content to avoid frozen numeric metrics, so that the cleaned-up section does not reintroduce the drift the prior cleanup fixed.

#### Acceptance Criteria

1. THE Retained_Whats_New_Section SHALL describe release changes without stating a Point_In_Time_Metric_Claim as a current-state fact.
2. IF the confirmed Retention_Policy keeps a section that currently contains a Point_In_Time_Metric_Claim, THEN THE Documentation_Cleanup SHALL remove that Point_In_Time_Metric_Claim from the retained content.

### Requirement 4: Preserve generator-owned regions and frontmatter

**User Story:** As a Maintainer, I want the cleanup confined to the hand-written What's New content, so that generator-owned regions and version metadata are untouched.

#### Acceptance Criteria

1. WHEN the Documentation_Cleanup is applied, THE Documentation_Cleanup SHALL leave the content of every Generated_Region in POWER.md byte-for-byte unchanged.
2. WHEN the Documentation_Cleanup is applied, THE Documentation_Cleanup SHALL leave the POWER.md YAML frontmatter, including the `version` field value, byte-for-byte unchanged.
3. WHEN the Documentation_Cleanup is applied, THE Documentation_Cleanup SHALL leave every POWER.md section other than the Whats_New_Sections byte-for-byte unchanged.

### Requirement 5: Leave the runtime What's New notification unaffected

**User Story:** As a bootcamper, I want the session-resume What's New notification to keep working, so that CHANGELOG-driven update notices are unchanged by this cleanup.

#### Acceptance Criteria

1. WHEN the Documentation_Cleanup is applied, THE Documentation_Cleanup SHALL make no change to `senzing-bootcamp/steering/whats-new.md`.
2. THE Whats_New_Notification SHALL continue to derive its content from CHANGELOG.md and `config/session_log.jsonl` after the Documentation_Cleanup is applied.

### Requirement 6: Remain documentation-only, valid, and CI-green

**User Story:** As a Maintainer, I want the cleanup to stay documentation-only and keep every gate green, so that the change ships without behavioral risk.

#### Acceptance Criteria

1. WHEN the Documentation_Cleanup is applied, THE POWER.md SHALL pass CommonMark_Validator validation.
2. WHEN the Documentation_Cleanup is applied, THE CI_Validation_Suite SHALL complete with zero failures.
3. WHEN the Documentation_Cleanup is applied, THE Documentation_Cleanup SHALL introduce no change to any Python script, hook definition, steering logic file, or the runtime behavior of the power.
4. THE Documentation_Cleanup SHALL confine every edit to `senzing-bootcamp/POWER.md`, except for an optional regression-guard test permitted under Requirement 7.

### Requirement 7: Optional regression guard against future accumulation

**User Story:** As a Maintainer, I want an optional automated guard on the What's New structure, so that the sections cannot silently accumulate again.

#### Acceptance Criteria

1. WHERE a regression-guard test is added, THE regression-guard test SHALL reside as a `test_*.py` module under `senzing-bootcamp/tests/` consistent with the repository test conventions.
2. WHERE a regression-guard test is added, THE regression-guard test SHALL fail if POWER.md contains a Whats_New_Section for any version not permitted by the confirmed Retention_Policy.
3. WHERE a regression-guard test is added, THE regression-guard test SHALL verify that the Retained_Whats_New_Section ends with the CHANGELOG_Pointer.
