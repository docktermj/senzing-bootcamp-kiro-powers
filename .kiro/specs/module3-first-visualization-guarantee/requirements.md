# Requirements Document

> **Status: DRAFT STUB.** Created from discrepancy D4 (the "implement" option) of the Senzing
> Bootcamp Experience Review. This is the stronger alternative to the D4 documentation clarification;
> adopt one or the other. Requirements below are a starting point, not a finished spec.

## Introduction

Governing Rule 15 is paraphrased across specs as "In Module 3, ALWAYS create the visualization," and
the Module 3 Step 9 visualization gate is unconditional once Module 3 is running (triple-guarded by
`gate-module3-visualization`, `enforce-mandatory-gate`, and `enforce-gate-on-stop`, and by
`NON_SKIPPABLE_GATES = {"3.9"}` in `validate_mandatory_gates.py`). However, Module 3 has a
whole-module Opt-Out Gate at the start of Phase 1 ("skip verification"): a bootcamper who opts out
records the module as skipped and sets gate 3->4 to skipped, so Step 9 never runs and the "first wow
moment" never happens.

This feature closes that gap so a first entity-resolution visualization is guaranteed for every
bootcamper, regardless of the Module 3 opt-out. The canonical Governing Rule 15 in
`config/governance-rules.yaml` (scoped to "no skip escape hatch" for step 3.9) and its pinned
assertions are NOT changed by this feature; this adds an always-on first-visualization guarantee at
the journey level.

## Glossary

- **Opt_Out_Gate**: the Phase 1 gate in `module-03-phase1-verification.md` that lets the bootcamper
  skip all of Module 3 via trigger phrases like "skip verification".
- **First_Visualization**: the bootcamper's first interactive entity-resolution visualization (the
  "wow moment") — today produced only by Module 3 Step 9.
- **Standalone_Demo_Visualization**: a minimal, self-contained TruthSet-backed visualization offered
  when Module 3 is opted out, reusing the Module 3 Step 9 web-service pattern.
- **Deferred_Guarantee**: an alternative in which the First_Visualization obligation carries forward
  to the first later module that has resolved data (Module 6 or 7) when Module 3 is opted out.

## Requirements

### Requirement 1: Guarantee a first visualization despite opt-out

**User Story:** As a bootcamper who skips system verification, I still want to see entity resolution
visualized at least once, so that I do not miss the core "wow moment" of the product.

#### Acceptance Criteria

1. WHEN the bootcamper triggers the Opt_Out_Gate in Module 3, THE system SHALL record that a
   First_Visualization is still owed (e.g., a `first_visualization: owed` marker in
   `config/bootcamp_progress.json`).
2. THE system SHALL NOT weaken the in-module Step 9 gate: when Module 3 is NOT opted out, Step 9
   remains an unconditional mandatory gate exactly as today.
3. THE system SHALL NOT modify the canonical Governing Rule 15 text or its pinned assertions in
   `config/governance-rules.yaml` / `validate_mandatory_gates.py`.

### Requirement 2: Choose a satisfaction path

**User Story:** As a product owner, I want a defined way the owed visualization is satisfied, so the
guarantee is testable and not open-ended.

#### Acceptance Criteria

1. WHEN a First_Visualization is owed after opt-out, THE system SHALL offer the bootcamper a
   Standalone_Demo_Visualization at the opt-out point (a minimal TruthSet-backed view reusing the
   Step 9 web-service pattern), presented as an offer, not a forced step.
2. IF the bootcamper declines the standalone demo, THEN the Deferred_Guarantee SHALL apply: the first
   later module with resolved data (Module 6 results dashboard, or Module 7 entity graph) SHALL treat
   its visualization offer as the guaranteed First_Visualization and clear the owed marker when it is
   generated.
3. WHEN any First_Visualization is generated (standalone or deferred), THE system SHALL clear the
   `first_visualization` owed marker.

### Requirement 3: Consistency with existing enforcement

**User Story:** As a maintainer, I want the new guarantee to align with the existing gate and
visualization-offer machinery rather than duplicating it.

#### Acceptance Criteria

1. THE Standalone_Demo_Visualization SHALL reuse the Module 3 Step 9 constraints (Python stdlib HTTP
   server, D3.js v7 CDN, single HTML file, artifacts inside the working directory).
2. THE Deferred_Guarantee SHALL reuse the existing Visualization Protocol / `visualization-guide.md`
   checkpoints for Modules 6 and 7 rather than adding a parallel offer mechanism.
3. WHERE this feature adds framing to steering or governance docs, it SHALL keep the distinction
   explicit: Step 9 is unconditional whenever Module 3 runs; the journey-level guarantee covers the
   opt-out case separately.

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want tests so the guarantee does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests asserting that opting out of Module 3 sets the owed marker and that
   completing a standalone or deferred visualization clears it.
2. THE feature SHALL include a preservation test asserting the in-module Step 9 gate behavior and the
   pinned Governing Rule 15 assertions are unchanged.
3. Tests SHALL follow the project pattern (pytest + Hypothesis where useful, class-based,
   `sys.path` import) in `senzing-bootcamp/tests/`.
