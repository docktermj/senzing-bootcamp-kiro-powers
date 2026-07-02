# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion E ("Module 1 — Business Problem") of the Senzing
> Bootcamp improvement review (`x.md`). Requirements below are a starting point for refinement, not
> a finished spec.

## Introduction

Module 1 Step 6a calculates the total record count "across all sources **mentioned by the
bootcamper**" and, when it exceeds the built-in 500-record evaluation limit, triggers license
guidance (Steps 6b–6e). This calculation relies on the bootcamper stating record counts in prose
during Module 1. If they don't state counts (or under-state them), the total reads as ≤ 500, the
license-guidance branch is silently skipped, and the bootcamper only discovers the license ceiling
much later when loading real data exceeds 500 records.

By Module 4 (Data Collection), the bootcamper has collected the actual data files, each carrying
real record-count metadata. This feature adds a back-fill: after Module 4 collects real files,
infer the true total record count from those files and, if it exceeds the 500-record evaluation
limit while Module 1 license guidance was skipped or deferred, surface the license guidance at that
point. It reuses the existing license-guidance plumbing (including `license_guidance_deferred`)
rather than inventing a new flow.

## Glossary

- **Evaluation_Limit**: the built-in 500-record limit of the Senzing SDK evaluation license.
- **Prose_Count**: the record total inferred in Module 1 Step 6a from what the bootcamper stated.
- **Collected_Count**: the record total inferred from the actual files collected in Module 4
  (from their per-source Record Count metadata / `config/data_sources.yaml`).
- **License_Guidance**: the Module 1 Steps 6b–6e guidance (apply existing license, external request
  path, or MCP license-request path).
- **Deferred_Flag**: the existing `license_guidance_deferred` marker used by
  `license-guidance-workflow`.

## Requirements

### Requirement 1: Infer the real record total from collected files

**User Story:** As a bootcamper, I want the bootcamp to use my actual collected data to judge
whether I need a license, so that I am not blindsided by the 500-record limit later.

#### Acceptance Criteria

1. WHEN Module 4 finishes collecting data files, THE system SHALL compute the Collected_Count from
   the collected sources' record-count metadata (e.g. `config/data_sources.yaml`) rather than from
   Prose_Count alone.
2. WHERE a collected source lacks a record count, THE system SHALL use the best available count
   (e.g. counting rows in the collected file) or clearly treat that source's contribution as unknown
   rather than silently zero.

### Requirement 2: Back-fill license guidance when the limit is exceeded

**User Story:** As a bootcamper whose Module 1 counts were vague, I want license guidance to appear
once my real data shows I'm over the limit, so that I get the guidance I would have gotten in
Module 1.

#### Acceptance Criteria

1. IF the Collected_Count exceeds the Evaluation_Limit AND License_Guidance was skipped or carries
   the Deferred_Flag from Module 1, THEN the system SHALL present License_Guidance during Module 4
   using the existing Steps 6b–6e content.
2. WHEN License_Guidance was already delivered (and acted on) in Module 1, THE system SHALL NOT
   re-present it redundantly; it MAY confirm the earlier guidance still applies.
3. WHEN the Collected_Count is at or below the Evaluation_Limit, THE system SHALL NOT present
   License_Guidance in Module 4 (no false trigger).

### Requirement 3: Reuse existing license plumbing

**User Story:** As a maintainer, I want the back-fill to reuse the existing license-guidance
machinery so behavior stays consistent across modules.

#### Acceptance Criteria

1. THE feature SHALL reuse the existing License_Guidance content and the Deferred_Flag introduced by
   `license-guidance-workflow` rather than defining a parallel flow.
2. THE feature SHALL keep the framing consistent with `license-capacity-framing` (default capacity
   with an expansion path) across Modules 1 and 4.
3. WHERE the back-fill delivers or clears guidance, THE system SHALL update the same
   preferences/progress markers the Module 1 flow uses, so downstream modules (e.g. Module 2 handoff)
   see a consistent state.

### Requirement 4: Non-blocking and data-safe

**User Story:** As a bootcamper, I want the record-count inference to never block Module 4 or leak
data.

#### Acceptance Criteria

1. IF the Collected_Count cannot be computed (missing/unreadable metadata), THEN the system SHALL log
   a warning and continue Module 4, falling back to the existing Prose_Count-based behavior.
2. THE feature SHALL NOT ship or persist real PII from collected files into tracked artifacts; only
   counts and source names are used.

### Requirement 5: Test coverage

**User Story:** As a maintainer, I want tests so the back-fill does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests covering: Collected_Count over the limit with Module 1 skipped
   (guidance presented), Collected_Count under the limit (no guidance), guidance already delivered
   in Module 1 (no redundant re-presentation), and the missing-metadata warn-and-continue fallback.
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   `senzing-bootcamp/tests/`.
