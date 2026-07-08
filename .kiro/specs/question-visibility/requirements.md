# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power already prefixes every input-requiring prompt with the 👉 pointer indicator (defined in `agent-behavior-rules.md` Rule 4, reinforced in `agent-instructions.md` and `conversation-protocol.md`). The pointer helps bootcampers recognize when it is their turn to respond, but the question text itself carries no additional visual weight, so the actual interrogative can be hard to spot inside a dense turn.

This feature improves question visibility by layering a second, additive visual cue on top of the existing pointer convention: the actual question posed to the bootcamper is rendered in bold. The 👉 pointer convention is preserved unchanged — bold emphasis is added in addition to it, never as a replacement. The new formatting applies consistently in every context where a question is presented (onboarding, module steps, transitions, feedback, session resume), remains compatible with the `write-policy-gate` validation and the 🛑 STOP / One Question Rule protocol, produces valid CommonMark, is reflected in the canonical formatting examples, and stays within the token budgets tracked in `steering-index.yaml`.

## Glossary

- **Bootcamper**: The developer working through the senzing-bootcamp power in the Kiro IDE.
- **Agent**: The Kiro agent that produces conversation turns while running the bootcamp.
- **Pointer_Indicator**: The 👉 emoji prefix placed at the start of a line to mark an input-requiring prompt. Defined by `agent-behavior-rules.md` Rule 4.
- **Leading_Question**: A question directed at the Bootcamper that expects a response and ends a yielding turn. Marked by the Pointer_Indicator.
- **Question_Text**: The interrogative sentence(s) of a Leading_Question that pose the request to the Bootcamper — the "actual question" the Bootcamper must answer. Excludes preceding explanatory context and following answer options.
- **Bold_Emphasis**: CommonMark strong emphasis produced by wrapping text in paired double-asterisk markers (`**...**`).
- **Choice_Question**: A Leading_Question that presents two or more distinct alternatives, formatted as a neutral lead question followed by a numbered list of options.
- **Lead_Question**: The single neutral interrogative line that precedes the numbered option list in a Choice_Question.
- **STOP_Marker**: The `🛑 STOP` directive that marks the absolute end-of-turn boundary after a Leading_Question.
- **One_Question_Rule**: The constraint that every yielding turn ends with exactly one Leading_Question.
- **Question_Pending_File**: The file `config/.question_pending` written after a Leading_Question to enforce the wait-for-response mechanism.
- **Write_Policy_Gate**: The `PreToolUse` hook (`senzing-bootcamp/hooks/write-policy-gate.json`) that validates single-question format when `config/.question_pending` is written.
- **Agent_Behavior_Rules**: The steering file `agent-behavior-rules.md` (`inclusion: auto`) containing Rule 4 (Consistent Pointer Indicator).
- **Agent_Instructions**: The steering file `agent-instructions.md` (`inclusion: always`) containing the Communication section.
- **Conversation_Protocol**: The steering file `conversation-protocol.md` (`inclusion: auto`) defining turn-taking and question rules.
- **Conversation_Examples**: The steering file `conversation-examples.md` (`inclusion: manual`) containing canonical correct/incorrect question examples.
- **Question_Bearing_Steering_File**: Any steering file that contains one or more literal Leading_Question examples for the Agent to present (module-01 through module-11 files, `visualization-guide.md`, the `deployment-*.md` guides, `feedback-workflow.md`, `onboarding-flow.md`, `session-resume.md`, and similar).
- **Behavior_Rules_Validator**: The script `senzing-bootcamp/scripts/validate_behavior_rules.py` that validates the four agent behavior rules, including Rule 4 (pointer indicator).
- **CommonMark_Validator**: The CI check `senzing-bootcamp/scripts/validate_commonmark.py` that validates CommonMark correctness of Markdown files.
- **Steering_Index**: The file `senzing-bootcamp/steering/steering-index.yaml` that tracks per-file token counts and size categories.

## Requirements

### Requirement 1: Bold Emphasis on the Question Text

**User Story:** As a Bootcamper, I want the actual question I am being asked to stand out in bold, so that I can immediately locate what I need to answer inside a dense turn.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL state that the Question_Text of every Leading_Question is wrapped in Bold_Emphasis.
2. WHEN the Agent presents a Leading_Question, THE Agent SHALL wrap the entire Question_Text — from its first character through its final character, including terminal punctuation such as the question mark — in a single paired Bold_Emphasis span.
3. THE Conversation_Protocol SHALL define the Bold_Emphasis formatting as additive to the Pointer_Indicator: the 👉 Pointer_Indicator is retained at the start of the line, remains outside the Bold_Emphasis span, is separated from the Question_Text by a single space, and the Bold_Emphasis span opens at the first character of the Question_Text that follows the Pointer_Indicator and closes at its last character.
4. WHERE a Leading_Question includes explanatory context sentences preceding the Question_Text, THE Agent SHALL apply Bold_Emphasis to the Question_Text only.
5. WHERE a Leading_Question includes explanatory context sentences preceding the Question_Text, THE Agent SHALL render those context sentences in plain text with no Bold_Emphasis markers applied to them.

### Requirement 2: Pointer Indicator Convention Preserved

**User Story:** As a Bootcamper, I want the 👉 pointer to keep appearing on every question, so that the existing signal I rely on to know it is my turn is not lost when bold formatting is added.

#### Acceptance Criteria

1. THE Agent_Behavior_Rules SHALL retain Rule 4 requiring the Pointer_Indicator at the start of the line of every input-requiring prompt.
2. THE Conversation_Protocol SHALL state that Bold_Emphasis is added in addition to the Pointer_Indicator and does not replace the Pointer_Indicator.
3. WHEN the Agent presents a Leading_Question, THE Agent SHALL place the Pointer_Indicator at the start of the line outside the Bold_Emphasis span, and THE Agent SHALL wrap the Question_Text that follows on the same line in Bold_Emphasis.
4. IF a Leading_Question does not begin with the Pointer_Indicator at the start of its line, THEN THE Conversation_Protocol SHALL classify the prompt as a formatting violation regardless of whether Bold_Emphasis is present.

### Requirement 3: Bold Emphasis Scope for Choice Questions

**User Story:** As a Bootcamper, I want only the lead question of a multiple-choice prompt to be bold, so that the question stands out clearly while the selectable options remain easy to read as a list.

#### Acceptance Criteria

1. WHEN the Agent presents a Choice_Question, THE Agent SHALL apply Bold_Emphasis to the Lead_Question line only and SHALL retain the Pointer_Indicator on that same line.
2. WHERE a Choice_Question includes explanatory context sentences before the Lead_Question, THE Agent SHALL apply Bold_Emphasis to the Lead_Question only and SHALL leave the context sentences in plain text.
3. WHEN the Agent presents a Choice_Question, THE Agent SHALL render each numbered option line in plain text with no Bold_Emphasis markers.
4. THE Conversation_Protocol SHALL state that the numbered option lines of a Choice_Question are not wrapped in Bold_Emphasis.
5. THE Conversation_Protocol SHALL retain the existing rule that two or more alternatives are formatted as a numbered list preceded by a single neutral Lead_Question.
6. IF one or more numbered option lines of a Choice_Question are wrapped in Bold_Emphasis, THEN THE Conversation_Protocol SHALL classify the Choice_Question as a formatting violation.

### Requirement 4: Steering Rule Documentation

**User Story:** As a power maintainer, I want the bold-question rule stated in the authoritative steering files, so that the Agent applies it consistently and future contributors understand the convention.

#### Acceptance Criteria

1. THE Agent_Behavior_Rules SHALL state in Rule 4 that the Question_Text of every Leading_Question is wrapped in Bold_Emphasis in addition to the Pointer_Indicator and not as a replacement for the Pointer_Indicator.
2. THE Agent_Instructions Communication section SHALL state that every input-requiring prompt is prefixed with the Pointer_Indicator and has its Question_Text wrapped in Bold_Emphasis.
3. THE Conversation_Protocol SHALL contain a distinct, separately identifiable rule that states the Bold_Emphasis requirement for the Question_Text of a Leading_Question, states that the Bold_Emphasis is additive to and does not replace the Pointer_Indicator, and states that in a Choice_Question the Bold_Emphasis applies only to the Lead_Question while the numbered options remain in plain text.
4. THE Conversation_Protocol Pre-Output Validation Checklist SHALL include an explicit checklist item that requires confirming, before the turn is output, that the Question_Text of the closing Leading_Question is wrapped in Bold_Emphasis.
5. THE Conversation_Protocol Self-Check section SHALL include an explicit verification item that requires confirming the closing Leading_Question renders its Question_Text in Bold_Emphasis.

### Requirement 5: Canonical Examples Updated

**User Story:** As a power maintainer, I want the canonical formatting examples to show the bold-question convention, so that the Agent has correct reference patterns and reviewers can identify violations.

#### Acceptance Criteria

1. THE Conversation_Examples SHALL render the Question_Text of every non-Choice_Question example that is explicitly labeled CORRECT in Bold_Emphasis with the Pointer_Indicator retained on the same line as the Question_Text.
2. THE Conversation_Protocol embedded examples SHALL render the Question_Text of every non-Choice_Question example that is explicitly labeled CORRECT in Bold_Emphasis with the Pointer_Indicator retained on the same line as the Question_Text.
3. THE Conversation_Examples SHALL include at least one Missing-Bold example pair in which a Leading_Question that has the Pointer_Indicator but no Bold_Emphasis is labeled WRONG and the same Question_Text with both the Pointer_Indicator and Bold_Emphasis is labeled CORRECT, such that the two members of the pair differ only in the presence of Bold_Emphasis.
4. WHERE a Choice_Question example is labeled CORRECT, THE Conversation_Examples SHALL render the Lead_Question in Bold_Emphasis with the Pointer_Indicator retained and SHALL render the numbered option lines in plain text.

### Requirement 6: Compatibility with Write Policy Gate Validation

**User Story:** As a power maintainer, I want the bold markers to leave the single-question validation unaffected, so that adding bold does not cause false compound-question rejections or bypass real ones.

#### Acceptance Criteria

1. THE Write_Policy_Gate SHALL continue to enforce the One_Question_Rule on content written to the Question_Pending_File, applying the same single-question validation logic that was in effect before Bold_Emphasis formatting was introduced.
2. WHEN the Write_Policy_Gate evaluates question content that contains Bold_Emphasis markers at any position, THE Write_Policy_Gate SHALL count question marks and detect joining conjunctions using only the underlying question wording with all Bold_Emphasis markers removed.
3. WHEN the Write_Policy_Gate evaluates two content inputs whose question wording is identical and that differ only in the presence of Bold_Emphasis markers, THE Write_Policy_Gate SHALL produce the same pass-or-fail verdict for both inputs.
4. IF a question containing Bold_Emphasis markers violates the One_Question_Rule, THEN THE Write_Policy_Gate SHALL report the violation using its existing compound-question output format.

### Requirement 7: Compatibility with Turn-Taking Protocol

**User Story:** As a Bootcamper, I want bold formatting to be purely visual, so that turn boundaries, the stop behavior, and the one-question guarantee keep working exactly as before.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL state that Bold_Emphasis is a presentational cue that does not alter the One_Question_Rule.
2. WHEN the Agent ends a yielding turn with a Leading_Question whose Question_Text is wrapped in Bold_Emphasis, THE Agent SHALL place the STOP_Marker in the same position and form as required for a Leading_Question that has no Bold_Emphasis.
3. THE Conversation_Protocol SHALL state that the count of Leading_Questions per turn is determined by the Pointer_Indicator occurrences and is unaffected by the presence of Bold_Emphasis markers.
4. WHEN the Agent ends a yielding turn with a Leading_Question whose Question_Text is wrapped in Bold_Emphasis, THE Agent SHALL write the Question_Pending_File with the same content and wait-for-response triggering behavior as required for a Leading_Question that has no Bold_Emphasis.
5. THE Agent SHALL render the STOP_Marker in plain text and SHALL NOT wrap the STOP_Marker in Bold_Emphasis.

### Requirement 8: CommonMark Validity

**User Story:** As a power maintainer, I want every bold question to be valid CommonMark, so that the rendered output is correct and the CI documentation check keeps passing.

#### Acceptance Criteria

1. WHEN a Leading_Question is written in a steering file, THE Question_Text SHALL be wrapped in a Bold_Emphasis span whose opening double-asterisk marker is matched by exactly one closing double-asterisk marker, with no unmatched Bold_Emphasis markers remaining on that line or within that paragraph.
2. WHEN the CommonMark_Validator runs against the steering files modified by this feature, THE CommonMark_Validator SHALL report zero CommonMark errors.
3. WHERE the Question_Text of a Leading_Question spans a single paragraph across soft line breaks, THE Bold_Emphasis span SHALL open and close within that paragraph without crossing a blank line or a numbered list boundary.
4. IF the CommonMark_Validator detects one or more CommonMark errors in a modified steering file, THEN THE CommonMark_Validator SHALL fail the CI documentation check and identify each steering file that contains an error, leaving the file content unchanged.

### Requirement 9: Token Budget and Steering Index Synchronization

**User Story:** As a power maintainer, I want the token counts to stay accurate and within budget after the edits, so that the always-loaded steering budget check keeps passing in CI.

#### Acceptance Criteria

1. WHEN steering files are modified to add Bold_Emphasis and the supporting rules, THE Steering_Index SHALL record for each modified file a `token_count` equal to the value measured by `measure_steering.py` and a `size_category` consistent with that recorded `token_count`.
2. THE Agent_Instructions `token_count` recorded in the Steering_Index SHALL be less than or equal to the always-loaded steering budget defined by the Steering_Index after the modifications.
3. WHEN `measure_steering.py --check` runs in CI, THE check SHALL report a passing result only if the recorded `token_count` for each modified file is exactly equal to its measured token count and the Agent_Instructions `token_count` is less than or equal to the always-loaded steering budget.
4. IF the recorded `token_count` of any modified file is not exactly equal to its measured token count when `measure_steering.py --check` runs, THEN THE check SHALL report a failing result that identifies each mismatched file.
5. IF the Agent_Instructions `token_count` exceeds the always-loaded steering budget after the modifications when `measure_steering.py --check` runs, THEN THE check SHALL report a failing result indicating that the always-loaded steering budget is exceeded.

### Requirement 10: Validation of the Bold-Question Rule

**User Story:** As a power maintainer, I want automated validation that questions carry bold emphasis, so that regressions are caught by CI rather than by bootcampers.

#### Acceptance Criteria

1. IF a steering-file Leading_Question carries the Pointer_Indicator but its Question_Text is not wrapped in a paired, correctly closed Bold_Emphasis span, THEN THE Behavior_Rules_Validator SHALL report a violation that identifies the offending steering file and the affected question and SHALL return a non-passing validation result.
2. WHEN the Behavior_Rules_Validator evaluates a Leading_Question that carries both the Pointer_Indicator and Bold_Emphasis on its Question_Text, THE Behavior_Rules_Validator SHALL report no Bold_Emphasis violation for that question and SHALL NOT contribute a non-passing result on account of that question.
3. THE Behavior_Rules_Validator SHALL NOT report a Bold_Emphasis violation for a steering-file line that is neither a Leading_Question nor carries the Pointer_Indicator.
4. THE test suite SHALL include a deterministic test that asserts the Behavior_Rules_Validator flags a Pointer_Indicator question whose Question_Text lacks Bold_Emphasis.
5. THE test suite SHALL include a deterministic test that asserts the Behavior_Rules_Validator accepts a Pointer_Indicator question whose Question_Text is wrapped in Bold_Emphasis, where deterministic means the tests produce identical results across repeated runs with no dependence on randomness, wall-clock time, or external state.

### Requirement 11: Consistent Application Across Question-Bearing Steering Files

**User Story:** As a Bootcamper, I want every question across the whole bootcamp to look the same, so that the bold-question cue is reliable in every module and workflow.

#### Acceptance Criteria

1. THE Question_Text of every literal Leading_Question example in any Question_Bearing_Steering_File SHALL be wrapped in Bold_Emphasis, with the Pointer_Indicator retained on the same line immediately preceding the Question_Text.
2. WHEN the Agent presents a Leading_Question in the onboarding, module-step, module-transition, feedback, or session-resume context, THE Agent SHALL include the Pointer_Indicator and SHALL wrap the Question_Text in Bold_Emphasis in addition to that Pointer_Indicator.
3. WHERE a Question_Bearing_Steering_File presents a Choice_Question, THE Lead_Question SHALL be wrapped in Bold_Emphasis with the Pointer_Indicator retained, and the numbered option lines SHALL remain in plain text.
