# Requirements Document

## Introduction

Several module steering files contain steps that combine multiple 👉 questions or multiple conditional questions within a single numbered step. The agent-instructions.md rule "One question at a time, wait for response" relies on agent interpretation rather than structural enforcement. This feature splits multi-question steps into sub-steps (e.g., 7a, 7b, 7c) so that the one-question-at-a-time rule is enforced by the document structure itself. All existing question content is preserved — only the structure changes.

## Glossary

- **Steering_File**: A markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that guides the agent through a bootcamp module or workflow
- **Step**: A numbered item in a steering file workflow (e.g., Step 7, Step 3) that the agent executes sequentially
- **Sub_Step**: A lettered subdivision of a step (e.g., 7a, 7b, 7c) where each sub-step contains at most one 👉 question
- **Question**: A prompt prefixed with 👉 that requires the bootcamper to respond before the agent proceeds
- **Conditional_Question**: A question that is asked only when a specific condition is met (e.g., "If record types unknown: ask...")
- **Checkpoint**: An instruction to write progress to `config/bootcamp_progress.json` after a step or sub-step completes
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file that maps modules to their steering files, phases, step ranges, and token counts
- **Agent_Instructions**: The `senzing-bootcamp/steering/agent-instructions.md` file containing core rules for agent behavior across all modules
- **Sub_Step_Convention**: The naming pattern where a parent step N is split into sub-steps Na, Nb, Nc, each containing at most one question and its own checkpoint

## Requirements

### Requirement 1: Audit Steering Files for Multi-Question Steps

**User Story:** As a maintainer, I want a complete audit of all module steering files identifying steps that contain multiple 👉 questions or multiple conditional questions, so that I know exactly which steps need restructuring.

#### Acceptance Criteria

1. THE Audit SHALL identify every step across all steering files in `senzing-bootcamp/steering/` that contains more than one 👉 question marker
2. THE Audit SHALL identify every step that contains multiple conditional questions (e.g., multiple "If X unknown: ask Y" branches within a single step)
3. THE Audit SHALL produce a list of affected files, step numbers, and the count of questions per step
4. WHEN a step contains exactly one 👉 question and zero conditional questions, THE Audit SHALL classify the step as compliant
5. WHEN a step contains instructions that say "ask about only one undetermined item per turn" but structurally lists multiple questions, THE Audit SHALL classify the step as non-compliant

### Requirement 2: Split Multi-Question Steps into Sub-Steps

**User Story:** As a maintainer, I want multi-question steps split into sub-steps using the lettered convention (e.g., 7a, 7b, 7c), so that the one-question-at-a-time rule is structurally enforced.

#### Acceptance Criteria

1. WHEN a step contains N questions (where N > 1), THE Steering_File SHALL be restructured so that the step is split into N sub-steps using the Sub_Step_Convention
2. THE Sub_Step_Convention SHALL use the format `{step_number}{letter}` where letter starts at `a` and increments alphabetically (e.g., 7a, 7b, 7c)
3. WHEN a step contains conditional questions that are mutually exclusive (only one can be asked based on runtime state), THE Steering_File SHALL group the mutually exclusive questions into a single sub-step with the conditional logic preserved
4. WHEN a step contains conditional questions that are independent (multiple could be asked sequentially based on different conditions), THE Steering_File SHALL assign each independent conditional question to its own sub-step

### Requirement 3: Enforce One Question Per Sub-Step

**User Story:** As a maintainer, I want each sub-step to contain at most one 👉 question, so that the agent cannot combine multiple questions in a single turn.

#### Acceptance Criteria

1. THE Sub_Step SHALL contain at most one 👉 question marker
2. THE Sub_Step SHALL contain at most one point where the agent must stop and wait for bootcamper input
3. WHEN a sub-step contains contextual information that precedes the question, THE Sub_Step SHALL include that context as part of the same sub-step
4. WHEN a step contains no questions (it is purely informational or action-based), THE Steering_File SHALL leave the step as a single step without sub-step splitting

### Requirement 4: Assign Checkpoints to Each Sub-Step

**User Story:** As a maintainer, I want each sub-step to have its own checkpoint instruction, so that progress tracking is granular enough to resume from any sub-step.

#### Acceptance Criteria

1. THE Sub_Step SHALL include a checkpoint instruction that writes the sub-step identifier to `config/bootcamp_progress.json`
2. WHEN a step is split into sub-steps, THE Checkpoint SHALL use the sub-step identifier (e.g., "Write step 7a to `config/bootcamp_progress.json`") rather than the parent step number
3. THE parent step number SHALL NOT have its own checkpoint if all its content has been distributed into sub-steps

### Requirement 5: Preserve All Existing Question Content

**User Story:** As a maintainer, I want all existing question text, conditional logic, and instructional content preserved during restructuring, so that no bootcamper-facing behavior is lost.

#### Acceptance Criteria

1. THE Restructuring SHALL preserve the exact wording of every 👉 question from the original step
2. THE Restructuring SHALL preserve all conditional logic (IF/WHEN clauses) that governs when a question is asked
3. THE Restructuring SHALL preserve all agent instructions, MCP tool calls, and contextual explanations associated with each question
4. THE Restructuring SHALL preserve all "STOP and wait" instructions associated with each question
5. IF a step contains a summary or preamble that applies to all sub-steps, THEN THE Restructuring SHALL place the shared preamble before the first sub-step or in a non-question parent step header

### Requirement 6: Document the Sub-Step Convention in Agent Instructions

**User Story:** As a maintainer, I want the sub-step convention documented in agent-instructions.md, so that future steering file authors follow the same pattern.

#### Acceptance Criteria

1. THE Agent_Instructions SHALL include a section describing the Sub_Step_Convention
2. THE Agent_Instructions SHALL state that each sub-step contains at most one 👉 question
3. THE Agent_Instructions SHALL state that each sub-step has its own checkpoint instruction
4. THE Agent_Instructions SHALL state that sub-steps use the `{step_number}{letter}` naming format
5. THE Agent_Instructions SHALL state that steps with no questions remain as single steps without sub-step splitting

### Requirement 7: Update Steering Index Step Ranges

**User Story:** As a maintainer, I want the steering-index.yaml step ranges updated to reflect the new sub-step structure, so that the phase system and token budget tracking remain accurate.

#### Acceptance Criteria

1. WHEN a module's steps are restructured with sub-steps, THE Steering_Index SHALL update the `step_range` for affected phases to reflect the new step identifiers
2. WHEN sub-steps are introduced, THE Steering_Index SHALL update the `token_count` for affected files to reflect the actual token count after restructuring
3. THE Steering_Index SHALL remain valid YAML after all updates
4. WHEN a phase's step range previously used integer bounds (e.g., `[1, 9]`), THE Steering_Index SHALL use a notation that accounts for sub-steps within that range

### Requirement 8: Validate Restructured Files Pass Existing CI

**User Story:** As a maintainer, I want the restructured steering files to pass all existing CI validation checks, so that the restructuring does not break the power.

#### Acceptance Criteria

1. WHEN restructuring is complete, THE Steering_Files SHALL pass `validate_power.py` without errors
2. WHEN restructuring is complete, THE Steering_Files SHALL pass `measure_steering.py --check` without errors
3. WHEN restructuring is complete, THE Steering_Files SHALL pass `validate_commonmark.py` without errors
4. WHEN restructuring is complete, THE Steering_Files SHALL pass all existing pytest tests without failures
