# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion C ("whole bootcamp") of the Senzing Bootcamp
> improvement review (`x.md`). Requirements below are a starting point for refinement, not a
> finished spec.

## Introduction

The steering corpus is large relative to the context window (`reference_window: 200000` in
`steering-index.yaml`), and the whole design leans on aggressive load/unload discipline with
`warn_threshold_pct: 60` and `critical_threshold_pct: 80`. The most likely source of protocol drift
is a mis-timed unload of an always-loaded file (e.g. `conversation-protocol.md`) or a module phase
file, or steady growth of the always-loaded set pushing the baseline footprint up.

`scripts/measure_steering.py --check` validates that stored per-file and per-phase `token_count`
values match the measured files and that `budget.total_tokens` equals the sum of `file_metadata`
counts. `--simulate` prints a per-module load simulation including an "always-loaded" baseline
(`agent-instructions.md`, `conversation-protocol.md`, `module-transitions.md` plus a representative
language file). However, **no check fails CI when the always-loaded baseline itself creeps above the
warn threshold** — the simulation is informational only.

This feature adds a first-class, CI-enforced measurement that the always-loaded steering set stays
well under the warn threshold, so baseline creep is caught before it erodes the headroom the
load/unload discipline depends on.

## Glossary

- **Always_Loaded_Set**: the steering files that are loaded for the entire session (files declared
  `inclusion: always`, i.e. the baseline that `--simulate` already models as "always-loaded").
- **Warn_Threshold**: `budget.warn_threshold_pct` (currently 60) of `budget.reference_window`.
- **Baseline_Footprint**: the summed measured `token_count` of the Always_Loaded_Set (optionally
  including the representative language file the simulation already assumes).
- **Always_Loaded_Check**: the new `measure_steering.py` validation that fails when the
  Baseline_Footprint exceeds a configured fraction of the Warn_Threshold.

## Requirements

### Requirement 1: Define the always-loaded set authoritatively

**User Story:** As a maintainer, I want the always-loaded set derived from a single authoritative
source, so that the check reflects what is actually loaded for the whole session.

#### Acceptance Criteria

1. THE feature SHALL determine the Always_Loaded_Set from the steering files' `inclusion: always`
   frontmatter (and/or an explicit list in `steering-index.yaml`), not from a value hard-coded only
   inside `simulate_context_load`.
2. WHERE the simulation's always-loaded list and the authoritative source diverge, THE feature SHALL
   reconcile them so a single definition drives both `--simulate` and the new check.

### Requirement 2: Enforce baseline headroom under the warn threshold

**User Story:** As a maintainer, I want CI to fail if the always-loaded baseline creeps toward the
warn threshold, so that we keep headroom for module and language files.

#### Acceptance Criteria

1. WHEN `measure_steering.py --check` runs, THE system SHALL compute the Baseline_Footprint of the
   Always_Loaded_Set from measured `token_count` values.
2. IF the Baseline_Footprint exceeds a configured fraction of the Warn_Threshold (the "always-loaded
   ceiling," e.g. a `budget.always_loaded_ceiling_pct` stored in `steering-index.yaml`), THEN the
   system SHALL report the overage and exit non-zero.
3. WHEN the Baseline_Footprint is at or below the ceiling, THE system SHALL treat the always-loaded
   check as passing (no new failure), preserving the existing `--check` pass/fail behavior for the
   `file_metadata`, phase, and budget-total checks.
4. THE ceiling SHALL be configuration-driven in `steering-index.yaml` (consistent with the existing
   `warn_threshold_pct` / `critical_threshold_pct` authority), not a magic number in the script.

### Requirement 3: Reporting

**User Story:** As a maintainer, I want the check output to tell me the baseline size and remaining
headroom, so that I can act before the corpus grows further.

#### Acceptance Criteria

1. WHEN the Always_Loaded_Check runs, THE system SHALL report the Baseline_Footprint in tokens, the
   Warn_Threshold in tokens, and the percentage of the Warn_Threshold consumed.
2. WHEN the check fails, THE report SHALL name the always-loaded files contributing to the
   footprint so a maintainer can target the reduction.

### Requirement 4: CI integration and unchanged behavior

**User Story:** As a maintainer, I want the new check wired into CI without disturbing existing
validations.

#### Acceptance Criteria

1. THE existing CI step that runs `measure_steering.py --check` SHALL exercise the Always_Loaded_Check
   without adding a separate CI invocation.
2. THE feature SHALL preserve the existing `file_metadata`, phase-count, and budget-total checks and
   the documented 10% tolerance exactly as today.
3. THE feature SHALL use the Python standard library only (no new third-party dependencies), per
   `tech.md`.

### Requirement 5: Test coverage

**User Story:** As a maintainer, I want tests so the check does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests covering: a baseline under the ceiling passing, a baseline over
   the ceiling failing with a naming report, and the always-loaded set being derived from the
   authoritative source.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`.
