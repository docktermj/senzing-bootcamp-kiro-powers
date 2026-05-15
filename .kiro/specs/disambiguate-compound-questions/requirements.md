# Requirements Document

## Introduction

The bootcamp agent asks compound questions where a short answer ("yes" or "no") maps to multiple possible meanings. For example, "Does that sound right? Anything I missed or got wrong?" — where "yes" could mean "yes it's right" or "yes you missed something." These compound questions are baked into the steering files themselves (not just agent improvisation), so the fix requires both a rule update in the conversation protocol and a sweep of all steering files to rewrite offending question text.

The existing `conversation-protocol.md` One Question Rule prohibits questions joined by conjunctions, but does not explicitly address the **confirmation+follow-up** pattern where two semantically distinct questions are posed in sequence within the same 👉 prompt. This spec closes that gap.

## Glossary

- **Compound_Question**: A 👉 prompt that contains two or more semantically distinct questions, such that a short answer (yes/no/a single word) could be interpreted as responding to different sub-questions with different meanings.
- **Confirmation_Question**: A question asking the bootcamper to validate or approve something the agent produced (e.g., "Does this look right?").
- **Follow_Up_Question**: A question asking for additional input or corrections (e.g., "Anything I missed?").
- **Ambiguous_Response_Risk**: The condition where a "yes" or "no" answer to a Compound_Question has two or more valid interpretations.
- **Steering_File**: A markdown file with YAML frontmatter in `senzing-bootcamp/steering/` that guides the agent through a bootcamp module or workflow.
- **Conversation_Protocol**: The steering file `conversation-protocol.md` with `inclusion: auto` that defines turn-taking rules.
- **Agent_Instructions**: The steering file `agent-instructions.md` with `inclusion: always` that defines top-level agent behavior.
- **One_Question_Rule**: The existing constraint that each agent turn contains at most one 👉 question directed at the bootcamper.

## Requirements

### Requirement 1: Add Disambiguation Rule to Conversation Protocol

**User Story:** As a bootcamper, I want every 👉 question to have exactly one unambiguous meaning for "yes" and one for "no," so that I can respond with a short answer and be understood correctly.

#### Acceptance Criteria

1. THE Conversation_Protocol SHALL include a "Question Disambiguation" section stating that every 👉 question must have a single unambiguous interpretation for each possible short answer (yes, no, a numbered choice).
2. THE Conversation_Protocol SHALL define the Compound_Question anti-pattern: a 👉 prompt containing a Confirmation_Question followed by a Follow_Up_Question (e.g., "Does X look right? Anything to change?").
3. THE Conversation_Protocol SHALL state that appending "or should we adjust/change/fix anything?" to a confirmation question creates a Compound_Question violation.
4. THE Conversation_Protocol SHALL provide a concrete before/after example demonstrating the violation and its fix.
5. THE Conversation_Protocol SHALL state that when both confirmation and correction input are needed, the agent must ask the confirmation question first, and only ask for corrections in a subsequent turn if the bootcamper indicates something is wrong.

### Requirement 2: Add Violation Example for Compound Confirmation Questions

**User Story:** As a power maintainer, I want a clear violation example in the conversation protocol showing the compound confirmation pattern, so that future steering file authors avoid it.

#### Acceptance Criteria

1. THE Conversation_Protocol Violation Examples section SHALL include a "Compound Confirmation (WRONG)" example showing: `👉 Does that summary sound right? Anything I missed or got wrong?`
2. THE Conversation_Protocol Violation Examples section SHALL include a "Compound Confirmation (CORRECT)" example showing the fix: `👉 Does that summary capture your situation accurately?` (single question, "yes" means confirmed, "no" means needs changes — the agent then asks what to change in the next turn)
3. THE Conversation_Protocol Violation Examples section SHALL include a "Compound Either/Or (WRONG)" example showing: `👉 Would you like me to create a summary, or would you prefer to skip that and move on?`
4. THE Conversation_Protocol Violation Examples section SHALL include a "Compound Either/Or (CORRECT)" example showing the fix as a numbered choice list where each number maps to one action.

### Requirement 3: Rewrite Compound Questions in Module 1 Steering Files

**User Story:** As a bootcamper going through Module 1, I want every question to be clear and unambiguous, so that I can respond quickly without parsing which part of the question to answer.

#### Acceptance Criteria

1. THE `module-01-business-problem.md` Step 9 question "Does that sound right? Anything I missed or got wrong?" SHALL be rewritten as a single unambiguous confirmation question.
2. THE `module-01-phase2-document-confirm.md` Step 16 question "Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?" SHALL be rewritten as a single unambiguous confirmation question.
3. EACH rewritten question SHALL have exactly one meaning for "yes" (confirmed, proceed) and one meaning for "no" (needs changes — agent asks what to fix in the next turn).
4. THE rewritten questions SHALL preserve the intent of seeking bootcamper validation before proceeding.

### Requirement 4: Audit All Steering Files for Compound Questions

**User Story:** As a power maintainer, I want all steering files audited for compound question patterns, so that every instance is identified and fixed — not just the ones reported in feedback.

#### Acceptance Criteria

1. THE Audit SHALL scan all files in `senzing-bootcamp/steering/` for 👉 prompts that contain two or more question marks within the same prompt block.
2. THE Audit SHALL scan for 👉 prompts that contain the patterns: "? Anything", "? Or ", "? Does ", "? Should ", "? Would ", "? Is there" (a question mark followed by another question starter).
3. THE Audit SHALL produce a list of affected files, step numbers, and the offending question text.
4. EACH identified compound question SHALL be rewritten following the disambiguation rule from Requirement 1.
5. THE Audit SHALL verify that no rewritten question introduces new ambiguity.

### Requirement 5: Reinforce Disambiguation in Agent Instructions

**User Story:** As a power maintainer, I want the disambiguation rule reinforced in agent-instructions.md, so that the agent follows it even when improvising questions not written in steering files.

#### Acceptance Criteria

1. THE Agent_Instructions Communication section SHALL add a bullet stating: "Every 👉 question must have one unambiguous meaning for 'yes' and one for 'no.' Never append a follow-up question to a confirmation question."
2. THE Agent_Instructions SHALL cross-reference the Conversation_Protocol Question Disambiguation section.
3. THE Agent_Instructions SHALL state that when the agent needs both confirmation and correction input, it must ask confirmation first, then ask for corrections only if the bootcamper says no.

### Requirement 6: Property-Based Test for Question Disambiguation

**User Story:** As a power maintainer, I want an automated test that detects compound questions in steering files, so that future changes cannot reintroduce the pattern.

#### Acceptance Criteria

1. A test SHALL scan all steering files in `senzing-bootcamp/steering/` for 👉 prompts containing two or more question marks.
2. THE test SHALL flag any 👉 prompt where a question mark is followed (within 50 characters) by another sentence starting with a question word (Does, Is, Are, Would, Should, Could, Can, Will, Anything, Or).
3. THE test SHALL pass when zero compound questions are found across all steering files.
4. THE test SHALL be located in `senzing-bootcamp/tests/` and run as part of the standard pytest suite.
5. THE test SHALL produce clear failure messages identifying the file, line number, and offending text when a compound question is detected.

### Requirement 7: Validate Changes Pass CI

**User Story:** As a power maintainer, I want all changes to pass existing CI validation, so that the disambiguation fixes do not break the power.

#### Acceptance Criteria

1. WHEN all changes are complete, THE steering files SHALL pass `validate_commonmark.py` without errors.
2. WHEN all changes are complete, THE steering files SHALL pass `measure_steering.py --check` without errors.
3. WHEN all changes are complete, ALL existing pytest tests SHALL pass without failures.
4. WHEN all changes are complete, THE new disambiguation test SHALL pass.
