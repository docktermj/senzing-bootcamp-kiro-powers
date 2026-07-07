# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion I ("Module 6 — Data Processing") of the Senzing
> Bootcamp improvement review (`x.md`). Requirements below are a starting point for refinement, not
> a finished spec.

## Introduction

Module 6 (Data Processing) classifies the data volume tier (Demo / Small / Medium / Large) via the
`record-volume-guidance` Volume_Step and `scripts/volume_utils.py` (`TIER_MEDIUM`, `TIER_LARGE`).
SQLite is fine for demo/small loads, but for medium/large volumes it becomes slow — the existing
SQLite slowdown guidance (≤ 1,000 records) is **advisory prose** repeated in several places, and the
SQLite→PostgreSQL migration is an *optional* pointer from Module 8. A bootcamper on SQLite with a
medium or large dataset can therefore start a load that stalls for a long time before anyone
suggests a different database.

This feature adds a **hard prompt** (a stop-and-confirm) in Module 6 when the classified volume tier
is medium or large **and** the active database is SQLite, before the long-running load begins. The
prompt surfaces the expected slowdown and the alternatives (switch to PostgreSQL now, or proceed on
SQLite with eyes open) so the bootcamper makes an informed choice rather than discovering the stall
mid-load. It is not a Mandatory_Gate that blocks forever — the bootcamper may proceed — but it must
be a real prompt, not passive prose.

## Glossary

- **Volume_Tier**: the Demo / Small / Medium / Large classification from `volume_utils.py`
  (`TIER_MEDIUM`, `TIER_LARGE`), persisted to preferences by the Volume_Step.
- **SQLite_Active**: the condition that the bootcamper's current Senzing datastore is SQLite.
- **Hard_Prompt**: a stop-and-confirm prompt presented before the Module 6 load when
  Volume_Tier ∈ {Medium, Large} and SQLite_Active, offering the migration alternative.
- **Migration_Alternative**: switching to PostgreSQL (per `database-migration-guide`) instead of
  running the large load on SQLite.

## Requirements

### Requirement 1: Trigger the hard prompt on the risky combination

**User Story:** As a bootcamper with a medium/large dataset on SQLite, I want to be warned before a
long load starts, so that I don't sit through an avoidable stall.

#### Acceptance Criteria

1. WHEN Module 6 is about to begin the data load AND the Volume_Tier is Medium or Large AND
   SQLite_Active is true, THE system SHALL present the Hard_Prompt before starting the load.
2. WHEN the Volume_Tier is Demo or Small, THE system SHALL NOT present the Hard_Prompt (no change to
   the small-volume flow).
3. WHEN the active database is not SQLite (e.g. already PostgreSQL), THE system SHALL NOT present the
   Hard_Prompt.

### Requirement 2: Prompt content and choices

**User Story:** As a bootcamper, I want the prompt to explain the tradeoff and give me a real
choice, so that I can switch databases or proceed knowingly.

#### Acceptance Criteria

1. THE Hard_Prompt SHALL state that a Medium/Large load on SQLite is expected to be slow and SHALL
   name the Volume_Tier and record count driving the warning.
2. THE Hard_Prompt SHALL offer the Migration_Alternative (switch to PostgreSQL per
   `database-migration-guide`) and a proceed-on-SQLite option.
3. WHEN the bootcamper chooses the Migration_Alternative, THE flow SHALL route to the existing
   migration guidance rather than duplicating it.
4. WHEN the bootcamper chooses to proceed on SQLite, THE flow SHALL continue the load and SHALL NOT
   re-prompt for the same load.

### Requirement 3: Non-blocking and consistent

**User Story:** As a maintainer, I want the prompt to reuse existing volume/migration machinery and
not become a permanent block.

#### Acceptance Criteria

1. THE Hard_Prompt SHALL NOT be a Mandatory_Gate (⛔) and SHALL always allow the bootcamper to
   proceed on SQLite.
2. THE feature SHALL reuse the existing Volume_Tier classification (`volume_utils.py`) and the
   existing `database-migration-guide` content rather than adding parallel logic.
3. IF the Volume_Tier or database type cannot be determined, THEN the system SHALL fall back to the
   existing advisory behavior and continue without blocking.

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want tests so the trigger condition does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests covering the trigger truth table: {Demo, Small, Medium, Large} ×
   {SQLite, non-SQLite}, asserting the Hard_Prompt fires only for Medium/Large on SQLite, plus the
   proceed and migrate paths and the indeterminate-tier fallback.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`.
