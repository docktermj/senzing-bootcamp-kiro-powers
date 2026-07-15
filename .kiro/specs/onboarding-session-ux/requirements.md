# Requirements Document

## Introduction

This feature bundles two related onboarding and session-continuity UX improvements for the
Senzing Bootcamp Kiro Power. Both improvements are delivered primarily through steering
Markdown under `senzing-bootcamp/steering/`, which ships to bootcampers as part of the power.

**Improvement 1 — Announce administrative setup before the WELCOME banner.** During
onboarding, administrative work (creating the project directory, installing hooks, running
environment checks) runs before the "WELCOME TO THE SENZING BOOTCAMP" banner appears. Without
an upfront heads-up, the bootcamper does not know that the official start is marked by the
banner, so the initial setup activity feels unexplained. The desired behavior is to tell the
bootcamper, as early as possible and before setup begins, that administrative setup will run
and that the bootcamp officially starts when the WELCOME banner is displayed.

**Improvement 2 — Preserve bold `👉` question formatting across session migration.** The
convention is to render questions posed to the bootcamper in bold as `👉 **question**`. After
a session migrates to a new session (context compaction), the agent stopped bolding the `👉`
questions and rendered them in plain text, because the bold-question convention was not
preserved in the compacted session summary. The desired behavior is (1) the agent always bolds
the `👉` question text, and (2) the "bold the question text" convention is codified explicitly
in the session-resume steering so it survives context compaction. Today the convention is only
implied by the conversation protocol and by the write-policy-gate's bold-marker stripping, so
it did not carry across the session handoff.

## Glossary

- **Bootcamp_Agent**: The agent that runs the bootcamp for the bootcamper by following the
  power's steering files.
- **Onboarding_Flow**: The onboarding steering (`onboarding-flow.md` and its phase sub-files)
  that drives the fresh-start setup and introduction sequence.
- **Administrative_Setup**: The pre-bootcamp preparation work performed during onboarding —
  creating the project directory, installing hooks, and running environment/prerequisite
  checks.
- **Setup_Preamble**: The message presented to the bootcamper before Administrative_Setup that
  explains the setup phase and the official start point.
- **WELCOME_Banner**: The "WELCOME TO THE SENZING BOOTCAMP" banner displayed after
  Administrative_Setup that marks the official start of the bootcamp.
- **Session_Resume**: The session-resume steering (`session-resume.md` and its phase-2
  sub-files) loaded when a prior bootcamp session is resumed.
- **Context_Compaction**: The event in which a prior session is summarized into a compacted
  summary carried forward into a new session (session migration).
- **Conversation_Protocol**: The turn-taking and question-handling steering
  (`conversation-protocol.md`).
- **Bold_Question_Convention**: The formatting convention that renders a `👉` leading
  question's text in CommonMark strong emphasis (`👉 **question**`).
- **Write_Policy_Gate**: The `PreToolUse` hook (`write-policy-gate.json`) that validates writes,
  including single-question validation of `config/.question_pending`.
- **Steering_Index**: The `steering-index.yaml` file that tracks per-file token counts and the
  steering token budget.

## Requirements

### Requirement 1: Announce Administrative Setup Before It Begins

**User Story:** As a bootcamper beginning onboarding, I want to be told before setup starts that
administrative setup will run, so that the initial setup activity does not feel unexplained.

#### Acceptance Criteria

1. WHEN onboarding begins, THE Onboarding_Flow SHALL display the Setup_Preamble before performing the first Administrative_Setup action.
2. IF an Administrative_Setup action is reached before the Setup_Preamble has been displayed, THEN THE Onboarding_Flow SHALL display the Setup_Preamble before performing that Administrative_Setup action.
3. THE Onboarding_Flow SHALL display the Setup_Preamble before displaying the WELCOME_Banner.

### Requirement 2: Setup Preamble Content

**User Story:** As a bootcamper, I want the upfront message to explain what the setup phase includes
and when the bootcamp officially starts, so that I understand the onboarding sequence.

#### Acceptance Criteria

1. THE Setup_Preamble SHALL state that Administrative_Setup will be performed before the bootcamp starts.
2. THE Setup_Preamble SHALL identify the Administrative_Setup activities as creating the project directory, installing hooks, and running environment checks.
3. THE Setup_Preamble SHALL state that the bootcamp officially starts when the WELCOME_Banner is displayed.
4. WHEN the WELCOME_Banner is displayed, THE Onboarding_Flow SHALL state that Administrative_Setup is complete and the bootcamp is starting.

### Requirement 3: Always Bold Question Text

**User Story:** As a bootcamper, I want every question rendered in bold, so that I can immediately
spot what I am being asked inside a dense turn.

#### Acceptance Criteria

1. WHEN THE Bootcamp_Agent presents a `👉` leading question, THE Bootcamp_Agent SHALL render the question text using CommonMark strong emphasis (`**...**`).
2. THE Bootcamp_Agent SHALL place the `👉` pointer at the start of the line and outside the bold span, separated from the question text by a single space.
3. WHERE a `👉` question presents numbered choice options, THE Bootcamp_Agent SHALL render the lead question text in bold and SHALL render each numbered option line in plain text.
4. WHILE presenting a `👉` question preceded by explanatory context, THE Bootcamp_Agent SHALL render the preceding explanatory sentences in plain text.
5. THE Bootcamp_Agent SHALL render the `🛑 STOP` marker in plain text.
6. IF THE Bootcamp_Agent detects, before sending a turn, a `👉` question whose text is not wrapped in bold, THEN THE Bootcamp_Agent SHALL wrap the question text in bold before sending the turn.

### Requirement 4: Preserve the Bold Convention Across Session Migration

**User Story:** As a bootcamper resuming after a session migration, I want questions to stay bold,
so that the look and feel is consistent across the entire bootcamp.

#### Acceptance Criteria

1. WHEN a session is resumed after Context_Compaction, THE Bootcamp_Agent SHALL render `👉` question text in bold.
2. THE Session_Resume steering SHALL state the Bold_Question_Convention explicitly among the core conversation rules it re-asserts on resume.
3. THE Session_Resume steering SHALL state the Bold_Question_Convention directly rather than solely by reference to Conversation_Protocol, so that the convention persists when only the compacted summary is available.
4. WHEN THE Session_Resume re-asserts the core conversation rules, THE Session_Resume SHALL include the instruction to render `👉` question text in bold.

### Requirement 5: Preserve Write-Policy-Gate Single-Question Validation

**User Story:** As a power maintainer, I want the write-policy-gate to keep validating single
questions correctly when bold markers are present, so that codifying the bold convention does not
weaken the safety check.

#### Acceptance Criteria

1. WHEN THE Write_Policy_Gate validates a question written to `config/.question_pending`, THE Write_Policy_Gate SHALL strip bold markers before performing single-question validation.
2. THE Write_Policy_Gate SHALL count `👉` leading questions independently of the presence of bold markers.
3. WHERE a question contains bold markers, THE Write_Policy_Gate SHALL produce the same compound-question verdict it would produce for the same question without bold markers.

### Requirement 6: Maintain Steering Token Budget Records

**User Story:** As a power maintainer, I want steering token budgets kept accurate after these
steering edits, so that the CI budget checks remain valid.

#### Acceptance Criteria

1. WHEN a steering file is modified for this feature, THE Steering_Index SHALL be updated to reflect that file's new token count.
2. WHERE a modified steering file exceeds the `split_threshold_tokens` value defined in the Steering_Index, THE modified steering file SHALL be split or added to the Steering_Index `split_allowlist` with a justification.
