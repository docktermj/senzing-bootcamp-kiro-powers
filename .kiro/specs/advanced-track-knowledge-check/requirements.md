# Requirements Document

> **Status: DRAFT STUB.** Created from suggestion D ("Onboarding, pre-Module-1") of the Senzing
> Bootcamp improvement review (`x.md`). Requirements below are a starting point for refinement, not
> a finished spec.

## Introduction

Onboarding Step 4c (the Comprehension_Check added by the `onboarding-comprehension-check` spec) is a
warm, non-blocking pause — explicitly "NOT a quiz" and not a Mandatory_Gate. It invites questions
but does not confirm that the bootcamper actually absorbed the core entity-resolution (ER) concepts.
A distracted bootcamper can acknowledge ("looks good") and proceed to track selection without any
grasp of ER.

The review suggests a **light, one-question knowledge check scoped to the Advanced track**, where
the deeper modules assume more conceptual grounding. The check is not a hard gate that fails a
bootcamper; it is a single, friendly comprehension question whose wrong/uncertain answer prompts a
brief re-explanation before continuing. It must not turn onboarding into a test for the Core track
and must respect the existing Step 4c tone.

## Glossary

- **Knowledge_Check**: a single, light comprehension question about a core ER concept, presented
  only for the Advanced track.
- **Advanced_Track**: the longer bootcamp track (through Module 11), selected in Step 5.
- **Comprehension_Check**: the existing warm, non-blocking Step 4c pause (see
  `onboarding-comprehension-check`).
- **Re_Explanation**: a brief, plain-language clarification of the concept the bootcamper missed,
  offered before proceeding.

## Requirements

### Requirement 1: Scope the knowledge check to the Advanced track

**User Story:** As an Advanced-track bootcamper, I want a quick check that the core ER idea landed,
so that the deeper modules do not lose me.

#### Acceptance Criteria

1. WHEN the bootcamper selects the Advanced_Track, THE onboarding flow SHALL present exactly one
   light Knowledge_Check question about a core ER concept before Module 1 begins.
2. WHEN the bootcamper selects the Core track, THE onboarding flow SHALL NOT present the
   Knowledge_Check (Core onboarding is unchanged).
3. THE Knowledge_Check SHALL be positioned so it follows track selection (once the Advanced track is
   known) and precedes Module 1.

### Requirement 2: Light, non-punitive interaction

**User Story:** As a bootcamper, I want the check to feel like a friendly gut-check, not an exam, so
that a wrong answer helps me rather than blocks me.

#### Acceptance Criteria

1. THE Knowledge_Check SHALL ask a single question and SHALL use a warm, conversational tone
   consistent with the existing Comprehension_Check.
2. WHEN the bootcamper answers correctly (or clearly demonstrates understanding), THE flow SHALL
   affirm briefly and proceed to Module 1.
3. WHEN the bootcamper answers incorrectly or is unsure, THE flow SHALL offer a brief Re_Explanation
   of the concept and then proceed to Module 1.
4. THE Knowledge_Check SHALL NOT be a Mandatory_Gate (⛔) and SHALL NOT prevent the bootcamper from
   continuing regardless of the answer.

### Requirement 3: Consistency with existing onboarding

**User Story:** As a maintainer, I want the knowledge check to build on the existing onboarding
steps rather than duplicate them.

#### Acceptance Criteria

1. THE Knowledge_Check SHALL be defined in the onboarding steering files alongside the existing
   Comprehension_Check, reusing its tone conventions and the note that the Ask_Bootcamper_Hook
   handles closing questions.
2. THE feature SHALL update the affected steering file token counts in
   `senzing-bootcamp/steering/steering-index.yaml`.
3. WHEN answering, THE agent SHALL apply the bootcamper's current verbosity settings.

### Requirement 4: Test coverage

**User Story:** As a maintainer, I want tests so the behavior does not regress.

#### Acceptance Criteria

1. THE feature SHALL include tests asserting the Knowledge_Check appears for the Advanced track and
   not for the Core track, and that the flow proceeds to Module 1 on both correct and incorrect
   answers (with Re_Explanation on the latter).
2. Tests SHALL follow the project pattern (pytest + Hypothesis, class-based, `sys.path` import) in
   the appropriate `tests/` directory.
