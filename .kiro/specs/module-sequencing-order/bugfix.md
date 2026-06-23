# Bugfix Requirements Document

## Introduction

The Senzing Bootcamp guides bootcampers through a numbered sequence of modules (1–11) grouped into tracks (Core Bootcamp = modules 1, 2, 3, 4, 5, 6, 7). The sequencing logic in `senzing-bootcamp/steering/` decides which module runs next based on module dependencies and completion state rather than enforcing a numeric default. Because Module 4 (Data Collection) only *hard*-requires Module 1 and treats Module 3 (System Verification) as a *soft* prerequisite, a dependency-only sequencer can legitimately produce a running order such as `1 → 4 → 5 → 2 → 6 → 7` — interleaving preparatory modules (SDK Setup, System Verification) with solution-building modules, and skipping Module 3 entirely before real data is loaded in Module 6.

This bugfix consolidates three related feedback items (two Medium, one High) into a single fix:

1. **Order Modules 2 and 3 before Module 4** — preparatory steps should be completed and clearly separated before solution-building begins.
2. **Always run Module 3 after Module 2** — System Verification proves the SDK, engine, database, and config resolve the known-good Senzing TruthSet before any real data is loaded; it must not be silently skipped.
3. **Run modules in numeric order by default** — the journey should follow `1 → 2 → 3 → 4 → 5 → 6 → 7`, deviating only when there is a clear, stated dependency reason.

The fix establishes numeric-order-by-default sequencing for any selected track and guarantees Module 3 runs immediately after Module 2 and before any data loading (Module 6), unless the bootcamper explicitly requests to skip verification.

## Bug Analysis

### Current Behavior (Defect)

When the bootcamp sequences modules for a selected track, it derives the running order from module dependencies and completion state without a numeric-order default, producing the following defects:

1.1 WHEN a track is selected and its running order is determined THEN the system presents modules out of ascending numeric sequence (e.g., `1 → 4 → 5 → 2 → 6 → 7` for the Core track)

1.2 WHEN preparatory modules (Module 2 SDK Setup, Module 3 System Verification) and solution-building modules (Module 4 Data Collection onward) are sequenced THEN the system interleaves them, placing Modules 2 and 3 after Module 4

1.3 WHEN the bootcamper completes Module 2 (SDK Setup) and Module 3 is part of the selected track THEN the system can transition directly to Module 6 (Data Processing), skipping Module 3 (System Verification) without an explicit skip request from the bootcamper

1.4 WHEN Module 3 (System Verification) is skipped THEN the system proceeds to load real data in Module 6 without first proving the setup resolves the known-good Senzing TruthSet correctly

### Expected Behavior (Correct)

2.1 WHEN a track is selected and its running order is determined THEN the system SHALL present modules in ascending numeric order (e.g., `1 → 2 → 3 → 4 → 5 → 6 → 7` for the Core track)

2.2 WHEN preparatory modules (2, 3) and solution-building modules (4 and later) are sequenced THEN the system SHALL complete Modules 2 and 3 before Module 4

2.3 WHEN the bootcamper completes Module 2 (SDK Setup) and Module 3 is part of the selected track THEN the system SHALL run Module 3 (System Verification) immediately after Module 2 and before any data loading (Module 6)

2.4 WHEN the system would deviate from ascending numeric order THEN the system SHALL do so only when there is a clear, stated dependency reason

2.5 WHEN data loading (Module 6) is about to begin and Module 3 is part of the selected track THEN the system SHALL have already completed Module 3, and SHALL NOT skip Module 3 unless the bootcamper explicitly requested to skip verification

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the Core track is selected THEN the system SHALL CONTINUE TO include the same set of modules (1, 2, 3, 4, 5, 6, 7), and the Advanced track SHALL CONTINUE TO include modules 1–11

3.2 WHEN a module has a genuine hard dependency (e.g., Module 6 requires Module 5's transformed data) THEN the system SHALL CONTINUE TO enforce that prerequisite before allowing the module to start

3.3 WHEN the bootcamper explicitly requests to skip a skippable module (e.g., 'skip verification' or 'I've already verified' for Module 3) THEN the system SHALL CONTINUE TO honor the explicit skip request

3.4 WHEN entity resolution quality is assessed as marginal or poor in Module 7 and the bootcamper returns to Module 5 for remapping THEN the system SHALL CONTINUE TO allow that valid backward transition without rollback or track switching

3.5 WHEN the bootcamper completes the final module of their selected track THEN the system SHALL CONTINUE TO trigger path-completion detection and the completion celebration

## Bug Condition

The bug condition identifies inputs — a selected track and the sequence the system produces for it — that trigger out-of-order or skipped-module behavior.

**Key Definitions:**
- **F**: The original (unfixed) sequencing logic — derives the running order from dependencies/completion state with no numeric-order default and Module 3 as a soft prerequisite.
- **F'**: The fixed sequencing logic — numeric-order-by-default with Module 3 guaranteed after Module 2 and before any data loading.
- **track.modules**: The ordered set of module numbers in the selected track (e.g., `[1,2,3,4,5,6,7]`).
- **order**: The running order the sequencer produces for the track (the sequence in which modules are actually presented/run).

```pascal
FUNCTION isBugCondition(X)
  INPUT: X = (track, order)  // track.modules = selected modules; order = produced running order
  OUTPUT: boolean

  // (a) order is not ascending numeric over the modules present, OR
  // (b) Module 3 is in the track but missing from order (silently skipped, no explicit skip request), OR
  // (c) Module 3 is in the track but appears after data loading (Module 6) in order

  notNumericOrder ← EXISTS i WHERE order[i] > order[i+1]

  module3Skipped ← (3 IN track.modules)
                   AND (3 NOT IN order)
                   AND NOT bootcamperRequestedSkip(3)

  module3AfterLoading ← (3 IN order) AND (6 IN order)
                        AND positionOf(3, order) > positionOf(6, order)

  RETURN notNumericOrder OR module3Skipped OR module3AfterLoading
END FUNCTION
```

```pascal
FUNCTION bootcamperRequestedSkip(moduleNumber)
  // True only when the bootcamper explicitly asked to skip the module
  // (e.g., 'skip verification' / 'I've already verified' for Module 3).
  RETURN explicit skip request present for moduleNumber
END FUNCTION
```

**Property Specification — Fix Checking:**

```pascal
// Property: Fix Checking — Numeric-order-by-default sequencing
FOR ALL X WHERE isBugCondition(X) DO
  order' ← F'(X.track)
  // 1. The produced order is ascending numeric over the modules present
  ASSERT FOR ALL i: order'[i] < order'[i+1]
  // 2. Module 3 runs after Module 2 and before any data loading, unless explicitly skipped
  ASSERT (3 NOT IN X.track.modules)
         OR bootcamperRequestedSkip(3)
         OR (positionOf(2, order') < positionOf(3, order')
             AND positionOf(3, order') < positionOf(6, order'))
END FOR
```

**Preservation Goal — Preservation Checking:**

```pascal
// Property: Preservation Checking — Non-buggy sequences are unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  // A track whose order is already ascending numeric with Module 3 correctly placed
  // (or explicitly skipped) must be produced identically by the fixed logic.
  ASSERT F(X.track) = F'(X.track)
END FOR
```

In addition, the fixed logic must preserve: genuine hard-dependency enforcement (3.2), explicit skip handling (3.3), the Module 7 → Module 5 quality feedback loop (3.4), and path-completion detection (3.5).
