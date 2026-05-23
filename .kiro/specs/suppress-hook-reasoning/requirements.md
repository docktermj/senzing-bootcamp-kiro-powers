# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power uses preToolUse and agentStop hooks to enforce write policies and question formatting. Currently, when these hooks evaluate content and determine no action is needed (fast path), the agent narrates its internal reasoning to the bootcamper (e.g., "Fast path passes — file is inside the working directory…" or "The 👉 question contains 'or' joining alternatives… however this is asking about a single concept…"). This internal processing noise degrades the bootcamp UX. This feature strengthens hook prompts with top-and-bottom suppression reinforcement and adds a strengthened steering rule to eliminate all hook reasoning output from the bootcamper-facing conversation.

## Glossary

- **Write_Policy_Gate**: The preToolUse hook (`write-policy-gate.kiro.hook`) that intercepts write operations and enforces SQL blocking, single-question format, and file path policies
- **Question_Format_Gate**: The agentStop hook (`question-format-gate.kiro.hook`) that inspects agent responses for compound 👉 questions and rewrites them into numbered-list format
- **Agent_Instructions**: The always-loaded steering file (`agent-instructions.md`) containing core agent rules including the hook silence rule
- **Fast_Path**: The evaluation branch in a hook prompt where all checks pass and no corrective action is needed
- **Slow_Path**: The evaluation branch in a hook prompt where a violation is detected and corrective output is required
- **Suppression_Reinforcement**: A prompt engineering technique placing explicit zero-output directives at both the top (front-loaded) and bottom (OUTPUT FORMAT section) of a hook prompt to prevent reasoning narration
- **Hook_Reasoning**: Any visible text output by the agent that describes, summarizes, or narrates the hook's internal evaluation process (e.g., "Fast path passes", "The question is not compound", "This is a JSON configuration file — not SQL code")

## Requirements

### Requirement 1: Write Policy Gate Fast Path Silent Re-invocation

**User Story:** As a bootcamper, I want the write-policy-gate hook to pass silently when no violation is detected, so that I never see internal hook reasoning cluttering my conversation.

#### Acceptance Criteria

1.1 WHEN the Write_Policy_Gate evaluates a write operation where the target path is inside the working directory, does not end with `.question_pending`, and the content does not contain SQL patterns targeting Senzing database indicators, THEN THE Write_Policy_Gate prompt SHALL instruct the agent to produce zero tokens of output.

1.2 THE Write_Policy_Gate prompt SHALL contain a front-loaded suppression instruction within the first 200 characters of the prompt text that explicitly states the agent must produce no output when the fast path applies.

1.3 THE Write_Policy_Gate prompt SHALL contain a closing OUTPUT FORMAT section after all check definitions that reinforces the zero-output requirement for the fast path using explicit anti-narration language.

1.4 THE Write_Policy_Gate prompt SHALL contain at least one explicit anti-narration directive that forbids phrases such as "Fast path passes", "Proceeding", "All checks pass", or any summary of the evaluation.

1.5 WHEN the Write_Policy_Gate fast path applies, THE Write_Policy_Gate prompt SHALL instruct the agent to re-invoke the original tool call with the same parameters without emitting any acknowledgment or explanation.

### Requirement 2: Write Policy Gate Edge Case Suppression

**User Story:** As a bootcamper, I want the write-policy-gate to remain silent even when content references Senzing indicators without containing SQL patterns, so that edge-case reasoning about why the fast path applies is never visible to me.

#### Acceptance Criteria

2.1 WHEN the Write_Policy_Gate evaluates content that references Senzing database indicators (G2C.db, RES_ENT, OBS_ENT, DSRC_RECORD, LIB_FEAT, RES_FEAT_STAT, RES_REL, SZ_, sz_dm_) but does NOT contain SQL patterns (SELECT, INSERT, UPDATE, DELETE, CREATE TABLE, DROP TABLE, ALTER TABLE, PRAGMA), THEN THE Write_Policy_Gate prompt SHALL instruct the agent to produce zero tokens of output.

2.2 THE Write_Policy_Gate prompt SHALL contain an explicit instruction that non-SQL content referencing Senzing indicators (such as JSON configuration files with connection strings) passes silently without explanation.

2.3 IF the Write_Policy_Gate prompt contains instructions for the edge case where content references Senzing indicators without SQL patterns, THEN THE Write_Policy_Gate prompt SHALL use the same zero-output directive as the standard fast path with no additional narration permitted.

### Requirement 3: Question Format Gate No-Rewrite Silent Output

**User Story:** As a bootcamper, I want the question-format-gate to output only a single period character when no compound question is detected, so that I never see reasoning about why the question was not flagged.

#### Acceptance Criteria

3.1 WHEN the Question_Format_Gate evaluates an agent response and determines no compound 👉 question is present, THEN THE Question_Format_Gate prompt SHALL instruct the agent to output only a single period character (`.`) with no additional text.

3.2 THE Question_Format_Gate prompt SHALL contain a front-loaded suppression instruction within the first 200 characters of the prompt text that explicitly states the agent must never output reasoning about its detection process.

3.3 THE Question_Format_Gate prompt SHALL contain a closing OUTPUT FORMAT section that reinforces: no-rewrite-needed outputs exactly `.` and rewrite-needed outputs only the corrected question.

3.4 THE Question_Format_Gate prompt SHALL contain at least one explicit anti-narration directive that forbids phrases such as "The question is not compound", "No rewrite needed", "Scanning for compound questions", or any description of the evaluation logic.

### Requirement 4: Question Format Gate Rewrite-Only Output

**User Story:** As a bootcamper, I want the question-format-gate to output only the corrected question when a rewrite is needed, so that I never see an explanation of why the question was rewritten.

#### Acceptance Criteria

4.1 WHEN the Question_Format_Gate detects a compound 👉 question and rewrites it, THEN THE Question_Format_Gate prompt SHALL instruct the agent to output only the corrected question text with no preamble, explanation, or reasoning.

4.2 THE Question_Format_Gate prompt SHALL contain an explicit instruction forbidding output such as "This is a compound question", "Let me rewrite", "The question contains 'or' joining alternatives", or any description of the detection that triggered the rewrite.

4.3 WHEN the Question_Format_Gate outputs a rewritten question, THE Question_Format_Gate prompt SHALL instruct the agent to preserve all non-question content from the original message and replace only the compound question portion.

### Requirement 5: Agent Instructions Strengthened Hook Silence Rule

**User Story:** As a bootcamper, I want the agent-instructions steering file to contain a strengthened hook silence rule that explicitly forbids reasoning output after any hook fires, so that the suppression policy is enforced at both the hook prompt level and the steering level.

#### Acceptance Criteria

5.1 THE Agent_Instructions SHALL contain a hook silence rule that explicitly forbids the agent from outputting any Hook_Reasoning after any hook fires, regardless of hook type or evaluation outcome.

5.2 THE Agent_Instructions hook silence rule SHALL enumerate specific forbidden output patterns including but not limited to: "Fast path passes", "Proceeding", "The question is not compound", "All checks pass", "This is a JSON configuration file", and any text that describes, summarizes, or narrates the hook evaluation process.

5.3 THE Agent_Instructions hook silence rule SHALL state that when a hook check passes with no action needed, the agent produces zero visible tokens — no acknowledgment, no reasoning, no status, no summary.

5.4 THE Agent_Instructions hook silence rule SHALL state that when a hook produces corrective output (e.g., a rewritten question), the agent outputs only the corrective content with no preamble or explanation of why the correction was made.

5.5 THE Agent_Instructions hook silence rule SHALL apply to all hook types including preToolUse hooks, agentStop hooks, and any future hook types added to the power.

### Requirement 6: Prompt Structure — Top and Bottom Reinforcement

**User Story:** As a power developer, I want both hook prompts to use a dual-reinforcement structure (front-loaded instruction at top, OUTPUT FORMAT section at bottom), so that the suppression directive is maximally effective regardless of where the LLM focuses attention in the prompt.

#### Acceptance Criteria

6.1 THE Write_Policy_Gate prompt SHALL begin with a suppression preamble (before any check logic) that states the zero-output requirement for passing checks.

6.2 THE Write_Policy_Gate prompt SHALL end with a strict OUTPUT FORMAT section (after all check definitions) that restates the zero-output requirement and lists forbidden narration patterns.

6.3 THE Question_Format_Gate prompt SHALL begin with a suppression preamble (before any detection logic) that states the output constraints: `.` for no-rewrite, corrected question only for rewrite, never reasoning.

6.4 THE Question_Format_Gate prompt SHALL end with a strict OUTPUT FORMAT section (after all detection and rewrite rules) that restates the output constraints and lists forbidden narration patterns.

6.5 THE suppression preamble in each hook prompt SHALL appear within the first 200 characters of the prompt text to ensure the LLM processes it before any evaluation logic.

### Requirement 7: Preservation of Violation Detection Behavior

**User Story:** As a power developer, I want the prompt restructuring to preserve all existing violation-detection behavior (SQL blocking, compound question rewriting, file path enforcement, feedback redirect), so that the suppression changes do not break any slow-path functionality.

#### Acceptance Criteria

7.1 THE Write_Policy_Gate prompt SHALL preserve the complete SQL blocking logic including all Senzing database indicators, SQL pattern detection, STOP instruction, and SDK method alternatives.

7.2 THE Write_Policy_Gate prompt SHALL preserve the complete single-question enforcement logic for `.question_pending` files including all five validation rules and the compound question violation output format.

7.3 THE Write_Policy_Gate prompt SHALL preserve the complete file path policy logic including external path blocking, feedback redirect to the canonical path, and content path checking.

7.4 THE Question_Format_Gate prompt SHALL preserve the complete compound question detection logic including all three detection patterns (sentence-starter Or, inline prose or, appended alternative) and the NOT COMPOUND exclusion list.

7.5 THE Question_Format_Gate prompt SHALL preserve the rewrite format: a neutral lead question followed by a numbered list of alternatives.

### Requirement 8: Test Coverage Extension

**User Story:** As a power developer, I want the existing test files to be extended with new property-based tests validating the suppression reinforcement structure, so that regressions in hook silence behavior are caught by CI.

#### Acceptance Criteria

8.1 WHEN the test suite runs, THE test file `test_suppress_policy_pass_output.py` SHALL contain property-based tests validating that the Write_Policy_Gate prompt contains both a front-loaded suppression preamble and a closing OUTPUT FORMAT section.

8.2 WHEN the test suite runs, THE test file `test_hook_silent_fast_path_properties.py` SHALL contain property-based tests validating that the Write_Policy_Gate prompt contains explicit anti-narration directives forbidding specific phrases.

8.3 WHEN the test suite runs, THE test file `test_hook_silent_fast_path_properties.py` SHALL contain property-based tests validating that the Question_Format_Gate prompt contains both a front-loaded suppression preamble and a closing OUTPUT FORMAT section.

8.4 WHEN the test suite runs, THE test file `test_suppress_policy_pass_output.py` SHALL contain property-based tests validating that the Agent_Instructions steering file contains the strengthened hook silence rule with enumerated forbidden patterns.

8.5 THE new property-based tests SHALL use Hypothesis with `@settings(max_examples=20)` and follow the existing test patterns (class-based organization, docstrings documenting which requirements are validated).
