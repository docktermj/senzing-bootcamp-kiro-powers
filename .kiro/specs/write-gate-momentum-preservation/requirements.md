# Requirements Document

## Introduction

During the senzing-bootcamp guided flow, the `write-policy-gate` preToolUse write hook intercepts nearly every config and progress write. When the hook's checks pass, the SILENCE RULE makes the hook produce zero tokens and re-invoke the tool, which causes the agent to re-issue the identical write in a follow-up step. These intercept/retry cycles produce turns that contain only tool activity — and on hook-only turns, a bare "." — with no visible leading question. The bootcamper perceives the bootcamp as having stopped and is forced to prompt "ask the next leading question," breaking the bootcamp's core UX promise of a continuous guided flow with a clear leading question at each turn.

This feature addresses the problem along two complementary outcomes:

- **Outcome A — Leading-question guarantee:** Every turn that yields control back to the bootcamper must end with a single leading question, including turns whose primary action was a re-issued write after a hook intercept. This behavior is governed by the bootcamp steering files under `senzing-bootcamp/steering/`.
- **Outcome B — Reduced intercept churn:** The `write-policy-gate` INTERNAL-FILE PASS-THROUGH set is extended to include the routine power-managed files named in the feedback (`config/data_sources.yaml`, `config/visualization_tracker.json`) so they pass silently on the first attempt, while preserving all existing NOT-guard safety conditions.

This feature does not weaken any existing safety check. The Senzing SQL block, the single-question rule for `.question_pending`, the feedback-file append-only guard, and root file placement enforcement all remain in force.

## Glossary

- **Bootcamper**: A developer progressing through the senzing-bootcamp guided learning flow.
- **Write_Policy_Gate**: The preToolUse write hook defined in `senzing-bootcamp/hooks/write-policy-gate.kiro.hook` that evaluates write operations before they execute.
- **Bootcamp_Agent**: The agent that conducts the bootcamp conversation, generates content, and issues write operations on behalf of the bootcamper.
- **Leading_Question**: A single `👉`-prefixed question, placed at the end of a turn, that tells the bootcamper what to do or decide next.
- **Yielding_Turn**: A turn at the end of which the Bootcamp_Agent stops producing tokens and returns control to the bootcamper for input.
- **Intercept_Retry_Cycle**: The sequence in which Write_Policy_Gate intercepts a write, produces zero tokens under the SILENCE RULE, and the Bootcamp_Agent re-issues the identical write in a follow-up step.
- **Internal_File_Passthrough**: The block in the Write_Policy_Gate prompt, evaluated before the FAST PATH GATE, that silently passes a defined set of routine power-managed internal files.
- **Routine_Power_Managed_File**: A config or log file the power writes during normal operation, listed explicitly in the Internal_File_Passthrough set.
- **NOT_Guard**: A condition in the Internal_File_Passthrough that must hold for the pass-through to apply; if any NOT_Guard fails, the write falls through to the four policy checks.
- **Senzing_SQL**: Write content containing a SQL pattern (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA) that targets a Senzing database indicator (G2C.db, database/G2C.db, RES_ENT, OBS_ENT, RES_FEAT_STAT, DSRC_RECORD, LIB_FEAT, RES_REL, SZ_, sz_dm_).
- **Question_Pending_File**: The file `config/.question_pending` that records the single pending leading question for the current turn.
- **Feedback_File**: The append-only file `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`.
- **Steering_Files**: The Markdown steering files under `senzing-bootcamp/steering/` that govern Bootcamp_Agent turn-taking and question behavior, including `conversation-protocol.md` and `agent-behavior-rules.md`.

## Requirements

### Requirement 1: Leading-question guarantee on yielding turns

**User Story:** As a bootcamper, I want every turn that returns control to me to end with a clear leading question, so that I always know what to do next and never perceive the bootcamp as stalled.

#### Acceptance Criteria

1. WHEN a Yielding_Turn completes, THE Bootcamp_Agent SHALL end the turn with exactly one Leading_Question prefixed with `👉`, where the Leading_Question contains exactly one question mark and no second `👉`-prefixed question.
2. WHILE the turn's primary action was a write re-issued after a Write_Policy_Gate intercept, THE Bootcamp_Agent SHALL end the Yielding_Turn with exactly one Leading_Question prefixed with `👉`.
3. IF a turn would otherwise yield control to the bootcamper containing only tool activity, THEN THE Bootcamp_Agent SHALL append exactly one Leading_Question prefixed with `👉` as the final content before yielding control.
4. THE Bootcamp_Agent SHALL place the Leading_Question as the final content of the Yielding_Turn and SHALL produce no further tokens after the Leading_Question text.
5. WHEN the Bootcamp_Agent ends a Yielding_Turn with a Leading_Question prefixed with `👉`, THE Bootcamp_Agent SHALL write the Question_Pending_File before yielding control, recording the question type on the first line as one of `track_selection`, `module_transition`, `step_question`, `confirmation`, or `choice`, and the full question text on the subsequent lines.

### Requirement 2: No bare-acknowledgment or empty yielding turns

**User Story:** As a bootcamper, I want the bootcamp to never hand control back to me with an empty or bare "." response, so that the guided flow remains continuous and legible.

#### Acceptance Criteria

1. IF a Yielding_Turn would otherwise contain only a bare punctuation acknowledgment, an empty response, or a single-word acknowledgment, THEN THE Bootcamp_Agent SHALL replace that response with a turn that ends in a Leading_Question.
2. WHEN the Bootcamp_Agent completes work that does not already end with a Leading_Question, THE Bootcamp_Agent SHALL append a contextual Leading_Question that states what the bootcamper can do next.
3. THE Bootcamp_Agent SHALL treat provision of the closing Leading_Question as its own responsibility rather than relying on any hook to supply the closing question.

### Requirement 3: Steering governance of leading-question behavior

**User Story:** As a power maintainer, I want the leading-question guarantee to be defined in the bootcamp steering files, so that the behavior is enforced consistently across all modules and turns.

#### Acceptance Criteria

1. THE Steering_Files SHALL contain an explicit written statement specifying that every Yielding_Turn ends with exactly one Leading_Question prefixed with `👉`.
2. THE Steering_Files SHALL contain an explicit written statement specifying that a Yielding_Turn whose primary action was a write re-issued after a Write_Policy_Gate intercept ends with exactly one Leading_Question prefixed with `👉`.
3. WHERE the Steering_Files describe end-of-turn behavior, THE Steering_Files SHALL state that the Bootcamp_Agent owns the closing Leading_Question and does not depend on any hook to provide the closing Leading_Question.
4. THE Steering_Files SHALL state the One Question Rule as exactly one Leading_Question per Yielding_Turn, such that a turn ending with zero Leading_Questions or with two or more Leading_Questions violates the rule, when stating the leading-question guarantee.
5. THE Steering_Files SHALL include the statements required by criteria 1 through 4 in both `conversation-protocol.md` and `agent-behavior-rules.md` without conflicting wording between the two files.

### Requirement 4: Extend the internal-file pass-through set

**User Story:** As a bootcamper, I want routine power-managed config files to write without an intercept/retry cycle, so that data generation and module transitions flow without visible stalls.

#### Acceptance Criteria

1. WHEN a write targets `config/data_sources.yaml` AND all NOT_Guards hold, THE Write_Policy_Gate SHALL pass the write through silently on the first attempt with zero tokens.
2. WHEN a write targets `config/visualization_tracker.json` AND all NOT_Guards hold, THE Write_Policy_Gate SHALL pass the write through silently on the first attempt with zero tokens.
3. THE Write_Policy_Gate SHALL retain `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`, `config/progress_{id}.json`, `config/preferences_{id}.yaml`, and the power-written session/recap log files in the Internal_File_Passthrough set.
4. THE Write_Policy_Gate SHALL evaluate the Internal_File_Passthrough before the FAST PATH GATE.
5. WHEN the Internal_File_Passthrough applies to a write, THE Write_Policy_Gate SHALL produce the same silent outcome as the FAST PATH GATE and introduce no new output strings.
6. THE Write_Policy_Gate SHALL limit the Internal_File_Passthrough to the exact set of named Routine_Power_Managed_Files and SHALL match only those exact paths rather than partial or pattern over-matches.

### Requirement 5: Preserve NOT-guard safety conditions

**User Story:** As a power maintainer, I want the extended pass-through to keep every existing safety guard, so that broadening the set does not allow unsafe or policy-violating writes to pass silently.

#### Acceptance Criteria

1. IF a write to a Routine_Power_Managed_File contains Senzing_SQL, THEN THE Write_Policy_Gate SHALL fall through to the four policy checks instead of passing the write through.
2. IF the target path is the Question_Pending_File, THEN THE Write_Policy_Gate SHALL fall through to the four policy checks and enforce the single-question rule.
3. IF the target path is the Feedback_File, THEN THE Write_Policy_Gate SHALL fall through to the four policy checks and enforce the append-only guard.
4. IF the target path is a root-blocked placement that is not on the ROOT WHITELIST, THEN THE Write_Policy_Gate SHALL fall through to the four policy checks and enforce root file placement.
5. WHERE any single NOT_Guard fails for a write to a Routine_Power_Managed_File, THE Write_Policy_Gate SHALL fall through to the four policy checks instead of passing the write through.

### Requirement 6: Hook structural integrity

**User Story:** As a power maintainer, I want the modified hook to remain a valid preToolUse write hook, so that the bootcamp continues to load and enforce write policy correctly after the change.

#### Acceptance Criteria

1. THE Write_Policy_Gate SHALL retain its `when.type` value of exactly `preToolUse` and its `toolTypes` value of exactly `["write"]`.
2. THE Write_Policy_Gate SHALL retain the required hook fields `name`, `version`, `when`, and `then`, each with a non-empty value.
3. THE Write_Policy_Gate file SHALL be well-formed JSON that parses without error when the bootcamp loads the hook.
4. WHEN all four policy checks pass for an intercepted write, THE Write_Policy_Gate SHALL produce zero output characters and re-invoke the original tool with the unmodified write.
5. WHEN the Write_Policy_Gate detects a policy violation, THE Write_Policy_Gate SHALL output exactly one corrective instruction for that single violation and no other content, including no Leading_Question and no acknowledgment text.
