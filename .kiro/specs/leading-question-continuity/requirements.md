# Requirements Document

## Introduction

This feature addresses a UX/workflow regression in the Senzing Bootcamp guided flow. The bootcamp's core promise is a continuous, agent-led experience where every turn that returns control to the bootcamper ends with exactly one clear leading question. During data generation and module transitions, the `write-policy-gate` `preToolUse` hook intercepts most config/progress writes and requires the agent to re-issue the identical write in a follow-up step. This produces turns containing only tool activity (and, on hook-only turns, a bare "."), with no visible leading question. The bootcamper perceives the bootcamp as having stalled and is forced to prompt the agent to continue.

This feature has two outcomes:

- **Outcome A — Leading-question continuity:** Every turn that yields control to the bootcamper ends with exactly one clear leading question, including turns whose primary action was a re-issued write following a hook intercept.
- **Outcome B — Reduced intercept churn:** Routine power-managed config files pass the `write-policy-gate` silently on the first attempt, so they no longer trigger the intercept/retry cycle.

A hard constraint applies to Outcome B: the four existing security checks performed by the `write-policy-gate` hook — Senzing SQL blocking, the feedback-file append-only guard, the `.question_pending` single-question enforcement, and root file placement enforcement — must remain fully intact. Only routine power-managed config files are added to the silent pass-through set.

## Glossary

- **Bootcamp_Agent**: The Kiro agent that guides the bootcamper through the Senzing Bootcamp modules, performs writes, and asks leading questions.
- **Bootcamper**: The developer working through the bootcamp who receives leading questions and provides responses.
- **Leading_Question**: Exactly one clear, actionable question presented to the Bootcamper at the end of a turn that directs the next step in the guided flow.
- **Turn**: A single unit of agent activity that ends by yielding control back to the Bootcamper.
- **Yielding_Turn**: A Turn that ends by returning control to the Bootcamper (as opposed to an internal hook-only step that immediately re-invokes a tool).
- **Write_Policy_Gate**: The `preToolUse` hook defined at `senzing-bootcamp/hooks/write-policy-gate.kiro.hook`, registered on `toolTypes: ["write"]`, that performs four policy checks on write operations.
- **Hook_Intercept**: The event in which the Write_Policy_Gate halts a write so the Bootcamp_Agent must re-issue the identical write in a follow-up step.
- **Pass_Through_Set**: The exact set of routine power-managed internal file paths that the Write_Policy_Gate allows to proceed silently on the first attempt without producing output.
- **Routine_Power_Managed_Config_File**: A config file written by the power during normal operation that carries no security-sensitive content, specifically `config/data_sources.yaml` and `config/visualization_tracker.json` (in addition to the files already in the Pass_Through_Set).
- **Security_Checks**: The four policy checks performed by the Write_Policy_Gate: Senzing SQL blocking, feedback-file append-only guard, `.question_pending` single-question enforcement, and root file placement enforcement.
- **Question_Pending_File**: The file at `config/.question_pending` used by the separate single-question enforcement mechanism.
- **Feedback_File**: The append-only feedback file at `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`.

## Requirements

### Requirement 1: Leading question present on every yielding turn

**User Story:** As a Bootcamper, I want every turn that returns control to me to end with one clear leading question, so that I always know what to do next and never perceive the bootcamp as stalled.

#### Acceptance Criteria

1. WHEN a Yielding_Turn completes, THE Bootcamp_Agent SHALL present exactly one Leading_Question at the end of that Yielding_Turn.
2. THE Bootcamp_Agent SHALL present each Leading_Question as visible text content rather than as tool activity alone.
3. IF a Turn consists only of tool activity with no Leading_Question, THEN THE Bootcamp_Agent SHALL treat that Turn as not yet yielding control and SHALL continue until a Leading_Question is presented.
4. THE Bootcamp_Agent SHALL present each Leading_Question as a single, unambiguous question consistent with the existing `.question_pending` single-question rules.

### Requirement 2: Leading-question continuity across hook intercept and re-issued write

**User Story:** As a Bootcamper, I want the agent to keep guiding me with a leading question even when its turn was spent re-issuing a write after a hook intercept, so that the intercept/retry cycle never separates the work from the next instruction.

#### Acceptance Criteria

1. WHEN a Hook_Intercept causes the Bootcamp_Agent to re-issue an identical write in a follow-up step, THE Bootcamp_Agent SHALL present a Leading_Question at the end of the Yielding_Turn that completes that re-issued write.
2. WHILE the Bootcamp_Agent is performing only Hook_Intercept handling and write re-issuance, THE Bootcamp_Agent SHALL withhold yielding control to the Bootcamper until a Leading_Question accompanies the completed work.
3. IF the primary action of a Yielding_Turn was a re-issued write following a Hook_Intercept, THEN THE Bootcamp_Agent SHALL include a Leading_Question that reflects the next step in the guided flow.
4. THE Bootcamp_Agent SHALL present the Leading_Question described in this requirement without requiring the Bootcamper to prompt for the next leading question.

### Requirement 3: Silent first-attempt pass-through for routine power-managed config files

**User Story:** As a Bootcamper, I want routine power-managed config writes to succeed on the first attempt without interception, so that data generation and module transitions flow continuously.

#### Acceptance Criteria

1. WHEN the Write_Policy_Gate evaluates a write whose target path is `config/data_sources.yaml`, THE Write_Policy_Gate SHALL allow the write to proceed silently on the first attempt without producing output.
2. WHEN the Write_Policy_Gate evaluates a write whose target path is `config/visualization_tracker.json`, THE Write_Policy_Gate SHALL allow the write to proceed silently on the first attempt without producing output.
3. THE Write_Policy_Gate SHALL continue to allow the existing Pass_Through_Set paths (`config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `config/progress_{id}.json`, `config/preferences_{id}.yaml`, and power-written session/recap log files `docs/progress/MODULE_*_COMPLETE.md` and recap/journal log files) to proceed silently on the first attempt.
4. WHEN the Write_Policy_Gate allows a Routine_Power_Managed_Config_File to pass through, THE Write_Policy_Gate SHALL produce zero output tokens for that write.

### Requirement 4: Pass-through scope limited to the exact config file set

**User Story:** As a power maintainer, I want the silent pass-through to match only the intended config files, so that no unintended write is exempted from policy checks.

#### Acceptance Criteria

1. THE Write_Policy_Gate SHALL apply the silent pass-through only to the exact paths enumerated in the Pass_Through_Set.
2. WHERE a write targets a path outside the Pass_Through_Set, THE Write_Policy_Gate SHALL evaluate that write against the Security_Checks.
3. IF a write targets a config file path that resembles but does not exactly match a Pass_Through_Set entry, THEN THE Write_Policy_Gate SHALL evaluate that write against the Security_Checks.

### Requirement 5: Security checks remain intact under pass-through

**User Story:** As a power maintainer, I want all four existing security checks to remain enforced, so that exempting routine config files does not weaken the bootcamp's safety guarantees.

#### Acceptance Criteria

1. IF a write contains Senzing SQL targeting a Senzing database indicator, THEN THE Write_Policy_Gate SHALL block the write and provide corrective SDK guidance, regardless of the target path.
2. IF a write targets the Feedback_File using a full-overwrite or in-place-edit operation, THEN THE Write_Policy_Gate SHALL block the write and require an append operation, regardless of the Pass_Through_Set.
3. IF a write targets the Question_Pending_File, THEN THE Write_Policy_Gate SHALL apply the single-question enforcement check and SHALL NOT apply the silent pass-through.
4. IF a write places a blocked file type in the project root that is not on the root whitelist, THEN THE Write_Policy_Gate SHALL block the write and provide corrective routing, regardless of the Pass_Through_Set.
5. WHERE any Security_Check NOT-guard fails for a candidate pass-through path, THE Write_Policy_Gate SHALL decline the silent pass-through and evaluate the write against the Security_Checks.
