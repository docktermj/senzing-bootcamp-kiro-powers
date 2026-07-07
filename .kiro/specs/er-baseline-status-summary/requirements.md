# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion H ("Module 5 — Data Quality & Mapping") of the
> Senzing Bootcamp improvement review (`x.md`). Requirements below are a starting point for
> refinement, not a finished spec.

## Introduction

Module 5 Phase 3 produces ER-baseline files (`config/er_baseline_{datasource}.json`) via the
mapping-regression machinery (`mapping-regression-testing`: `baseline_path()`, `accept_baseline()`,
`compare_results.py`). These baselines are powerful — they let later runs detect regressions in
entity resolution — but they are easy to lose track of across sessions. There is no single view of
which data sources currently have an accepted baseline and which do not, so a bootcamper (or the
agent resuming a session) can't quickly tell whether regression coverage is complete.

This feature adds a **baseline status summary**: a concise, on-demand (and resume-time) report of
which data sources have an ER baseline, which are missing one, and basic metadata (e.g. when each
baseline was accepted). It reuses the existing baseline path/metadata conventions rather than adding
a new baseline format.

## Glossary

- **ER_Baseline**: an accepted `config/er_baseline_{datasource}.json` file capturing expected
  entity-resolution results for a data source.
- **Baseline_Status_Summary**: the new report listing, per data source, whether an ER_Baseline
  exists and its key metadata.
- **Data_Sources**: the registered sources (from `config/data_sources.yaml`) that a baseline can be
  taken against.

## Requirements

### Requirement 1: Summarize baseline coverage across sources

**User Story:** As a bootcamper, I want to see at a glance which of my data sources have an ER
baseline, so that I know my regression coverage is complete before I move on.

#### Acceptance Criteria

1. WHEN the Baseline_Status_Summary is requested, THE system SHALL list each registered Data_Source
   and indicate whether an ER_Baseline exists for it.
2. WHERE an ER_Baseline exists, THE summary SHALL include basic metadata available from the baseline
   (e.g. the acceptance timestamp and/or record/entity counts) without dumping full contents.
3. WHERE a Data_Source has no ER_Baseline, THE summary SHALL mark it as missing and note how to
   create one (the existing `accept_baseline` path).

### Requirement 2: Availability at useful moments

**User Story:** As a bootcamper resuming across sessions, I want the baseline status surfaced when
it matters, so that I don't silently carry gaps forward.

#### Acceptance Criteria

1. THE Baseline_Status_Summary SHALL be available on demand (a script/command the bootcamper or
   agent can run).
2. WHERE session resume or Module 5 completion occurs, THE flow MAY surface the Baseline_Status_Summary
   so missing baselines are visible at natural checkpoints.
3. THE summary SHALL be read-only — it SHALL NOT create, modify, or delete any ER_Baseline.

### Requirement 3: Reuse existing baseline conventions

**User Story:** As a maintainer, I want the summary to reuse the existing baseline machinery so it
stays consistent.

#### Acceptance Criteria

1. THE feature SHALL locate baselines via the existing `baseline_path()` convention and read the
   existing `config/er_baseline_{datasource}.json` format (from `mapping-regression-testing`),
   rather than defining a new location or schema.
2. THE feature SHALL derive the Data_Sources list from `config/data_sources.yaml` (the existing
   registry).
3. THE feature SHALL use the Python standard library only (no new third-party dependencies), per
   `tech.md`.

### Requirement 4: Robustness

**User Story:** As a bootcamper, I want the summary to be reliable even if some files are missing or
malformed.

#### Acceptance Criteria

1. IF a baseline file is missing or unreadable, THEN the summary SHALL report that source as missing
   (or unreadable) and continue, never raising.
2. IF the data-sources registry is missing, THEN the summary SHALL report that no sources are
   registered and exit cleanly.

### Requirement 5: Test coverage

**User Story:** As a maintainer, I want tests so the summary does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests covering: all sources with baselines, a mix of present and missing
   baselines, an unreadable baseline, and a missing registry.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`, using synthetic fixtures only (no real PII).
