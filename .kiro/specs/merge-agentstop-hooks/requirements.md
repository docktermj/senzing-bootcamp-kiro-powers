# Requirements Document

## Introduction

Merge two redundant `agentStop → askAgent` hooks (`ask-bootcamper` and `enforce-wait-after-question`) into a single `ask-bootcamper` hook. The `enforce-wait-after-question` hook's entire behavior — scanning for a pending 👉 question and suppressing output when one exists — is already implemented as the FIRST step of `ask-bootcamper`'s prompt. Both hooks fire on the same event (`agentStop`) with no filters, so running both wastes a conversation-history scan with zero additional protection. This change removes the redundant hook file, updates all registry/config/test references, and verifies consistency via the existing sync and test tooling.

## Glossary

- **Ask_Bootcamper_Hook**: The `ask-bootcamper.kiro.hook` file — an `agentStop → askAgent` hook that recaps accomplishments and asks a contextual 👉 question, with a built-in first step that suppresses all output when a 👉 question is already pending.
- **Enforce_Wait_Hook**: The `enforce-wait-after-question.kiro.hook` file — an `agentStop → askAgent` hook whose sole purpose is suppressing output when a 👉 question is pending. Redundant with Ask_Bootcamper_Hook's first step.
- **Hook_Registry**: The generated `senzing-bootcamp/steering/hook-registry.md` file that documents all bootcamp hooks. Produced by `sync_hook_registry.py` from `.kiro.hook` files and `hook-categories.yaml`.
- **Hook_Categories_Config**: The `senzing-bootcamp/hooks/hook-categories.yaml` file that maps each hook ID to its category (critical or module) for registry generation.
- **Sync_Script**: The `senzing-bootcamp/scripts/sync_hook_registry.py` script that generates Hook_Registry from hook files and Hook_Categories_Config.
- **Hook_Count**: The total number of `.kiro.hook` files in the hooks directory. Currently 19; will become 18 after the merge.

## Requirements

### Requirement 1: Retain Complete Suppression Logic in Ask_Bootcamper_Hook

**User Story:** As a power maintainer, I want the merged Ask_Bootcamper_Hook to retain all suppression behavior from both hooks, so that no functionality is lost.

#### Acceptance Criteria

1. THE Ask_Bootcamper_Hook prompt SHALL contain instructions to scan the entire conversation history for a pending 👉 question and suppress all output when one is found.
2. THE Ask_Bootcamper_Hook prompt SHALL contain instructions to never answer a 👉 question on the bootcamper's behalf, fabricate responses, or simulate user choices.
3. THE Ask_Bootcamper_Hook prompt SHALL contain instructions to suppress output when the last assistant message asked any question, with or without the 👉 character.
4. WHEN no 👉 question is pending, THE Ask_Bootcamper_Hook prompt SHALL instruct the agent to recap accomplishments and ask a contextual 👉 question.

### Requirement 2: Remove Enforce_Wait_Hook File

**User Story:** As a power maintainer, I want the redundant Enforce_Wait_Hook file deleted, so that only one agentStop hook handles question suppression.

#### Acceptance Criteria

1. WHEN the merge is complete, THE hooks directory SHALL NOT contain a file named `enforce-wait-after-question.kiro.hook`.
2. THE hooks directory SHALL contain exactly 18 `.kiro.hook` files after the merge.

### Requirement 3: Update Hook_Categories_Config

**User Story:** As a power maintainer, I want Hook_Categories_Config updated to remove the deleted hook, so that the Sync_Script generates a correct registry.

#### Acceptance Criteria

1. WHEN the merge is complete, THE Hook_Categories_Config SHALL NOT contain an entry for `enforce-wait-after-question`.
2. THE Hook_Categories_Config SHALL list exactly 18 hook IDs across all categories after the merge.
3. THE Hook_Categories_Config critical section SHALL list exactly 7 hook IDs after the merge.

### Requirement 4: Regenerate Hook_Registry

**User Story:** As a power maintainer, I want Hook_Registry regenerated from the updated source files, so that the registry accurately reflects the current set of hooks.

#### Acceptance Criteria

1. WHEN the Sync_Script is run with `--write`, THE Hook_Registry SHALL be regenerated from the remaining 18 hook files and the updated Hook_Categories_Config.
2. THE Hook_Registry SHALL report "All 18 bootcamp hooks" in its introductory paragraph.
3. THE Hook_Registry SHALL NOT contain any reference to `enforce-wait-after-question`.
4. WHEN the Sync_Script is run with `--verify`, THE Sync_Script SHALL exit with code 0, confirming the on-disk registry matches the generated output.

### Requirement 5: Update Test Suites

**User Story:** As a power maintainer, I want all test suites updated to reflect the new hook count, so that CI passes without failures.

#### Acceptance Criteria

1. WHEN the merge is complete, THE `EXPECTED_HOOK_COUNT` constant in `tests/test_hook_prompt_standards.py` SHALL equal 18.
2. WHEN the merge is complete, THE hardcoded count assertions in `senzing-bootcamp/tests/test_sync_hook_registry_unit.py` SHALL expect 18 hooks instead of 19.
3. WHEN the full test suite is run, THE test suite SHALL pass with zero failures.

### Requirement 6: Preserve Steering File Accuracy

**User Story:** As a power maintainer, I want steering files to remain accurate after the merge, so that agent behavior instructions are consistent.

#### Acceptance Criteria

1. THE `senzing-bootcamp/steering/agent-instructions.md` file SHALL NOT contain any reference to `enforce-wait-after-question` after the merge.
2. IF any other steering file references `enforce-wait-after-question`, THEN THE reference SHALL be removed or updated to reference `ask-bootcamper` instead.

### Requirement 7: CI Verification

**User Story:** As a power maintainer, I want the Sync_Script verify mode and the test suite to confirm consistency, so that the merge is validated end-to-end.

#### Acceptance Criteria

1. WHEN `sync_hook_registry.py --verify` is executed after the merge, THE Sync_Script SHALL exit with code 0.
2. WHEN `pytest` is executed on both test directories after the merge, THE test suite SHALL report zero failures.
