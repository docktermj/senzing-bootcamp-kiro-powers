# Requirements Document

## Introduction

A verification of the Senzing Bootcamp power found that the stated outcome "all questions must be answered by the bootcamper; Kiro cannot answer questions nor assume answers" is only true for mandatory gates (⛔). Two onboarding questions violate it by silently supplying an answer when the bootcamper does not respond:

- **Verbosity (Detail_Level_Step, currently Step 5a):** "If the bootcamper skips without answering, apply the `standard` preset as the default." — the agent assumes an answer.
- **Comprehension check (Any_Questions_Step, currently Step 5b):** treated as non-mandatory and skippable.

There is also a general risk that, under context or token pressure, the agent proceeds past a `👉` question without a real answer. This feature makes the guarantee universal and enforced: **every `👉` question requires a real bootcamper response before the flow proceeds; the agent never fabricates, assumes, or silently defaults an answer.** An explicit bootcamper choice to "use the default / skip" is itself a valid answer — the point is that the choice must come from the bootcamper, not from the agent.

## Glossary

- **Question**: A `👉`-prefixed prompt directed at the bootcamper that yields the turn.
- **Real_Answer**: A response actually provided by the bootcamper, including an explicit decline/skip ("use the default", "skip this", "no preference").
- **Assumed_Answer**: Any answer the agent supplies on the bootcamper's behalf — a fabricated choice, a silent default, or proceeding as if a response was given when none was.
- **Answer_Required_Rule**: The normative rule that every Question must receive a Real_Answer before the flow proceeds past it.
- **Detail_Level_Step**: The verbosity-preference question (currently Step 5a of onboarding).
- **Any_Questions_Step**: The comprehension check / "any questions" prompt (currently Step 5b of onboarding).
- **Explicit_Default_Choice**: A menu option the bootcamper can select that means "use the recommended default" — a Real_Answer, not an Assumed_Answer.
- **Pending_Question_Marker**: The existing `config/.question_pending` file marking the single outstanding Question.

## Requirements

### Requirement 1: Every Question Requires a Real Answer

**User Story:** As a bootcamper, I want the bootcamp to wait for my actual response to every question, so that no choice is ever made for me without my input.

#### Acceptance Criteria

1. WHEN the agent presents a Question, THE agent SHALL wait for a Real_Answer and SHALL NOT proceed past that Question until one is received.
2. THE agent SHALL NOT supply an Assumed_Answer under any circumstance, including context-budget pressure, token limits, session resume, or perceived time savings.
3. WHEN the bootcamper provides an explicit decline/skip, THE agent SHALL treat that as a Real_Answer, record it, and proceed accordingly.
4. THE Answer_Required_Rule SHALL apply in all contexts: onboarding, module steps, transitions, feedback, and session resume.
5. IF the agent cannot obtain a Real_Answer (e.g., the session ends), THEN THE Question SHALL remain outstanding via the Pending_Question_Marker so a later turn re-presents it, rather than being resolved by an Assumed_Answer.

### Requirement 2: Remove the Verbosity Silent Default

**User Story:** As a bootcamper, I want to actively choose my detail level, so that the verbosity of the whole bootcamp reflects my real preference.

#### Acceptance Criteria

1. THE Detail_Level_Step SHALL require a Real_Answer before proceeding.
2. THE Detail_Level_Step SHALL NOT apply the `standard` preset (or any preset) as a silent default when the bootcamper does not respond.
3. THE Detail_Level_Step SHALL offer an Explicit_Default_Choice (e.g., "standard (recommended)") that the bootcamper can select, so choosing the default remains one keystroke away as a Real_Answer.
4. WHEN the bootcamper selects the Explicit_Default_Choice, THE agent SHALL persist `standard` to `config/bootcamp_preferences.yaml` exactly as today and proceed.
5. THE Detail_Level_Step SHALL be marked as a mandatory gate (⛔) consistent with the Answer_Required_Rule.

### Requirement 3: The Comprehension Check Requires a Response

**User Story:** As a bootcamper, I want to explicitly signal whether I have questions before Module 1, so that the bootcamp never assumes I am ready when I am not.

#### Acceptance Criteria

1. THE Any_Questions_Step SHALL require a Real_Answer before proceeding to the next step.
2. WHEN the bootcamper acknowledges readiness (e.g., "makes sense", "no questions", "ready"), THE agent SHALL treat that as a Real_Answer and proceed.
3. WHEN the bootcamper asks a clarification question, THE agent SHALL answer it and then re-present the Any_Questions_Step, repeating until the bootcamper signals readiness.
4. THE Any_Questions_Step SHALL NOT be resolved by an Assumed_Answer (e.g., proceeding as if the bootcamper acknowledged when they said nothing).

### Requirement 4: Consolidated, Enforced Rule

**User Story:** As a bootcamp maintainer, I want one normative Answer_Required_Rule enforced by the existing question machinery, so that the guarantee is reliable and not contradicted elsewhere.

#### Acceptance Criteria

1. THE steering rules (`conversation-protocol.md`, `agent-behavior-rules.md`, `agent-instructions.md`) SHALL state the Answer_Required_Rule as a single normative rule.
2. THE power SHALL contain no steering instruction that authorizes an Assumed_Answer; any existing "apply default when skipped" or "not a gate / can skip" phrasing that would let the agent proceed without a Real_Answer SHALL be removed or reworded to require an Explicit_Default_Choice instead.
3. THE `ask-bootcamper` Stop hook SHALL continue to own the closing Question and SHALL NOT emit content that advances past an unanswered Question.
4. THE `write-policy-gate` PreToolUse hook (or equivalent enforcement) SHALL treat writing progress/preferences that resolves a Question without a recorded Real_Answer as a violation to be blocked or rewritten.
5. WHERE a step is genuinely optional, THE optionality SHALL be expressed as an Explicit_Default_Choice within the Question, not as license for the agent to proceed with no answer.

### Requirement 5: Interaction With Existing Behavior

**User Story:** As a bootcamp maintainer, I want this guarantee to align with related existing rules, so that nothing regresses or contradicts.

#### Acceptance Criteria

1. THE Answer_Required_Rule SHALL be consistent with the self-answering-prevention rules (`self-answering-prevention-v2`) and mandatory-gate enforcement (`mandatory-gate-enforcement`); this spec generalizes "no self-answering" to also forbid silent defaults.
2. THE Answer_Required_Rule SHALL be consistent with the single-ask guarantee: a Question that already has a recorded Real_Answer is not re-asked (it was answered), and is never resolved by an Assumed_Answer.
3. THE Advanced_Knowledge_Check (currently non-gating) MAY remain non-blocking for *progress*, but SHALL still require a Real_Answer to the question it poses before proceeding, OR be reworded so it no longer presents a `👉` question if it is truly skippable. (The step SHALL NOT present a `👉` question that the agent then answers for the bootcamper.)
4. THE change SHALL preserve all existing persistence and hook-ownership behavior except for removing Assumed_Answer paths.

### Requirement 6: Tests

**User Story:** As a bootcamp maintainer, I want tests proving no Assumed_Answer paths remain, so that the guarantee does not regress.

#### Acceptance Criteria

1. THE test suite SHALL assert the Detail_Level_Step no longer contains a silent-default instruction and is marked as a mandatory gate with an Explicit_Default_Choice.
2. THE test suite SHALL assert the Any_Questions_Step requires a Real_Answer.
3. THE test suite SHALL assert the steering corpus contains the single Answer_Required_Rule and contains no "apply default when skipped" / "proceed without an answer" phrasing for `👉` questions.
4. WHEN the full suite runs, THE suite SHALL pass.
