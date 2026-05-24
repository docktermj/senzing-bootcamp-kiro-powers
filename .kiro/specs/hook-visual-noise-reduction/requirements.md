# Requirements Document

## Introduction

Reduce visual hook noise in the senzing-bootcamp Kiro Power by consolidating four agentStop hooks into one, suppressing "Fast path passes" messages from the write-policy-gate, and suppressing original compound questions before rewrites so the bootcamper only sees the clean version.

## Glossary

- **Ask_Bootcamper_Hook**: The consolidated agentStop hook (`ask-bootcamper.kiro.hook`) that fires after every agent response, responsible for closing questions, step sequencing, MCP-first compliance, and question format enforcement.
- **Question_Format_Phase**: The internal phase within Ask_Bootcamper_Hook that detects compound 👉 questions and silently rewrites them using numbered list format via agent self-correction.
- **Step_Sequencing_Phase**: The internal phase within Ask_Bootcamper_Hook that verifies current_step has not advanced by more than one step and detects module transition failures.
- **MCP_First_Phase**: The internal phase within Ask_Bootcamper_Hook that audits agent responses for Senzing content presented without prior MCP tool consultation.
- **Closing_Question_Phase**: The internal phase within Ask_Bootcamper_Hook that generates a contextual 👉 closing question when no question is already pending.
- **Write_Policy_Gate**: The preToolUse hook (`write-policy-gate.kiro.hook`) that performs policy checks on file write operations.
- **Silent_Self_Correction**: A rewrite technique where the hook instructs the agent to regenerate its last response with the corrected question inline, so the bootcamper only sees the clean version without the original compound question.
- **Hook_Categories_File**: The YAML file (`hook-categories.yaml`) that maps hooks to critical or module-specific categories.
- **Hooks_Lock_File**: The auto-generated YAML file (`hooks.lock.yaml`) that records all hook IDs, versions, categories, and event types.
- **Hook_Registry_Critical**: The steering file (`hook-registry-critical.md`) containing full prompt text for critical hooks used during onboarding.
- **Hook_Registry**: The steering file (`hook-registry.md`) containing a quick-reference table of all hooks.
- **Hooks_README**: The documentation file (`hooks/README.md`) describing available hooks for users.

## Requirements

### Requirement 1: Consolidate agentStop hooks into Ask_Bootcamper_Hook

**User Story:** As a bootcamp maintainer, I want four agentStop hooks consolidated into a single hook file, so that only one hook fires per agent response instead of four, reducing visible noise in the IDE.

#### Acceptance Criteria

1.1. THE Ask_Bootcamper_Hook SHALL contain four internal phases: Closing_Question_Phase, Step_Sequencing_Phase, MCP_First_Phase, and Question_Format_Phase.

1.2. WHEN the agent response contains no violations and no closing question is needed, THE Ask_Bootcamper_Hook SHALL produce a single period character as its complete output.

1.3. THE Ask_Bootcamper_Hook SHALL evaluate all four phases within a single hook firing, producing at most one combined output.

1.4. THE Ask_Bootcamper_Hook SHALL preserve the complete prompt logic from the original `enforce-step-and-transition.kiro.hook` within the Step_Sequencing_Phase.

1.5. THE Ask_Bootcamper_Hook SHALL preserve the complete prompt logic from the original `mcp-first-invariant.kiro.hook` within the MCP_First_Phase.

1.6. THE Ask_Bootcamper_Hook SHALL preserve the complete prompt logic from the original `question-format-gate.kiro.hook` within the Question_Format_Phase, modified to use Silent_Self_Correction.

1.7. THE Ask_Bootcamper_Hook SHALL increment its version number to reflect the consolidation change.

### Requirement 2: Silent self-correction for compound question rewrites

**User Story:** As a bootcamper, I want to see only the clean rewritten question without the original compound version, so that my conversation is not cluttered with duplicate questions.

#### Acceptance Criteria

2.1. WHEN the Question_Format_Phase detects a compound 👉 question, THE Ask_Bootcamper_Hook SHALL instruct the agent to regenerate its entire last response with the corrected question inline, replacing the compound question in-place.

2.2. WHEN the Question_Format_Phase detects a compound 👉 question, THE Ask_Bootcamper_Hook SHALL instruct the agent to suppress the original compound question from the bootcamper's view.

2.3. WHEN the Question_Format_Phase detects no compound question, THE Ask_Bootcamper_Hook SHALL produce no output for that phase.

2.4. THE Question_Format_Phase SHALL preserve all compound-question detection patterns from the original `question-format-gate.kiro.hook`: sentence-starter Or, inline prose or, and appended alternative.

### Requirement 3: Delete obsolete hook files

**User Story:** As a bootcamp maintainer, I want the three individual hook files removed from the repository, so that there is no confusion about which hooks are active.

#### Acceptance Criteria

3.1. THE repository SHALL NOT contain the file `senzing-bootcamp/hooks/question-format-gate.kiro.hook`.

3.2. THE repository SHALL NOT contain the file `senzing-bootcamp/hooks/enforce-step-and-transition.kiro.hook`.

3.3. THE repository SHALL NOT contain the file `senzing-bootcamp/hooks/mcp-first-invariant.kiro.hook`.

### Requirement 4: Update Hook_Categories_File

**User Story:** As a bootcamp maintainer, I want hook-categories.yaml to reflect the consolidation, so that the registry remains accurate.

#### Acceptance Criteria

4.1. THE Hook_Categories_File SHALL NOT list `question-format-gate` in any category.

4.2. THE Hook_Categories_File SHALL NOT list `enforce-step-and-transition` in any category.

4.3. THE Hook_Categories_File SHALL NOT list `mcp-first-invariant` in any category.

4.4. THE Hook_Categories_File SHALL list `ask-bootcamper` in the critical category.

### Requirement 5: Update Hooks_Lock_File

**User Story:** As a bootcamp maintainer, I want hooks.lock.yaml to reflect the consolidation, so that CI verification passes.

#### Acceptance Criteria

5.1. THE Hooks_Lock_File SHALL NOT contain an entry with id `question-format-gate`.

5.2. THE Hooks_Lock_File SHALL NOT contain an entry with id `enforce-step-and-transition`.

5.3. THE Hooks_Lock_File SHALL NOT contain an entry with id `mcp-first-invariant`.

5.4. THE Hooks_Lock_File SHALL contain an entry for `ask-bootcamper` with the updated version number.

### Requirement 6: Suppress "Fast path passes" messages from Write_Policy_Gate

**User Story:** As a bootcamper, I want the write-policy-gate hook to produce zero visible output when all checks pass, so that I do not see distracting "Fast path passes" messages.

#### Acceptance Criteria

6.1. WHEN all policy checks pass, THE Write_Policy_Gate SHALL produce zero output tokens with no acknowledgment, no reasoning, and no status summary.

6.2. THE Write_Policy_Gate prompt SHALL contain "Fast path passes" in its FORBIDDEN output list as an explicitly prohibited phrase.

6.3. THE Write_Policy_Gate prompt SHALL contain a front-loaded silence directive within the first 200 characters of the prompt text.

6.4. THE Write_Policy_Gate prompt SHALL contain a closing OUTPUT FORMAT section that reiterates the zero-token directive and enumerates forbidden narration phrases.

### Requirement 7: Update steering and documentation references

**User Story:** As a bootcamp maintainer, I want all steering files and documentation to reflect the consolidation, so that onboarding and hook installation remain correct.

#### Acceptance Criteria

7.1. THE Hook_Registry_Critical SHALL NOT contain separate entries for `question-format-gate`, `enforce-step-and-transition`, or `mcp-first-invariant` as standalone hooks.

7.2. THE Hook_Registry_Critical SHALL contain the updated Ask_Bootcamper_Hook prompt text reflecting all four consolidated phases.

7.3. THE Hook_Registry SHALL NOT list `question-format-gate`, `enforce-step-and-transition`, or `mcp-first-invariant` as separate rows in the hook table.

7.4. THE Hooks_README SHALL NOT list `question-format-gate`, `enforce-step-and-transition`, or `mcp-first-invariant` as separate hook entries.

7.5. WHEN the POWER.md hook list references the deleted hooks, THE POWER.md SHALL be updated to remove those references and adjust the hook count.

### Requirement 8: Maintain test coverage

**User Story:** As a bootcamp maintainer, I want existing tests to pass after the consolidation, so that no behavioral regressions are introduced.

#### Acceptance Criteria

8.1. WHEN tests reference `mcp-first-invariant.kiro.hook` as a standalone file, THE tests SHALL be updated to validate the MCP_First_Phase within Ask_Bootcamper_Hook.

8.2. WHEN tests reference `question-format-gate.kiro.hook` as a standalone file, THE tests SHALL be updated to validate the Question_Format_Phase within Ask_Bootcamper_Hook.

8.3. WHEN tests reference `enforce-step-and-transition.kiro.hook` as a standalone file, THE tests SHALL be updated to validate the Step_Sequencing_Phase within Ask_Bootcamper_Hook.

8.4. THE test suite SHALL pass after all changes are applied.

### Requirement 9: Structural validity of consolidated hook

**User Story:** As a bootcamp maintainer, I want the consolidated hook to remain a valid hook file, so that the Kiro framework can load and execute it.

#### Acceptance Criteria

9.1. THE Ask_Bootcamper_Hook SHALL parse as valid JSON containing all required keys: name, version, description, when, and then.

9.2. THE Ask_Bootcamper_Hook SHALL have `when.type` set to `agentStop`.

9.3. THE Ask_Bootcamper_Hook SHALL have `then.type` set to `askAgent`.

9.4. THE Ask_Bootcamper_Hook SHALL have a `then.prompt` field containing the complete consolidated prompt text.
