# Requirements Document

## Introduction

The "Summarize Progress on Stop" hook (`senzing-bootcamp/hooks/summarize-on-stop.kiro.hook`) fires on every `agentStop` event and instructs the agent to append a progress summary before finishing. This rework renames the hook from `summarize-on-stop` to `ask-bootcamper`, simplifies the prompt, and changes the behavior so the hook always ends with a 👉-prefixed question asking the bootcamper what to do next. The old pending-question detection logic is removed — the hook itself now owns the closing question. A new steering instruction ensures the agent's main work output never ends with a closing question, creating a clean separation: the agent does work, the hook asks "what's next."

## Glossary

- **Hook**: A Kiro hook file (JSON) that maps an IDE event to an agent action.
- **Hook_Prompt**: The `then.prompt` string inside the hook JSON that instructs the agent what to do when the hook fires.
- **Hook_Registry**: The markdown file `senzing-bootcamp/steering/hook-registry.md` that documents all bootcamp hooks and their prompts.
- **Summary**: The structured recap block the agent appends when the hook fires, describing what was accomplished and which files changed.
- **Ask_Bootcamper_Question**: A 👉-prefixed question the hook instructs the agent to present after the summary, asking the bootcamper what they want to do next.
- **No_Op_Turn**: An agent turn where no meaningful work was performed (e.g., the agent only answered a clarifying question or acknowledged input).
- **Bootcamper**: The human user working through the Senzing Bootcamp.
- **Closing_Question**: Any question at the end of the agent's output that asks the bootcamper to respond or choose a next action. All questions to the bootcamper — both mid-conversation and closing — use the 👉 prefix.

## Requirements

### Requirement 1: Hook Rename

**User Story:** As a power author, I want the hook renamed from `summarize-on-stop` to `ask-bootcamper`, so that the name reflects the new behavior of always asking the bootcamper what's next.

#### Acceptance Criteria

1. THE Hook file SHALL be renamed from `summarize-on-stop.kiro.hook` to `ask-bootcamper.kiro.hook`.
2. THE Hook file SHALL set the `name` field to "Ask Bootcamper".
3. THE Hook file SHALL update the `description` field to reflect the new behavior: recapping progress and asking the bootcamper what to do next.
4. THE Hook_Registry SHALL replace the `summarize-on-stop` entry with an `ask-bootcamper` entry using the updated id, name, description, and prompt.
5. THE Hook_Registry SHALL remove the old `summarize-on-stop` entry entirely.

### Requirement 2: Summary Recap

**User Story:** As a bootcamper, I want a concise recap of what just happened when the agent stops, so that I always know what was accomplished and which files changed.

#### Acceptance Criteria

1. WHEN the hook fires, THE Hook_Prompt SHALL instruct the agent to produce a recap containing: (1) what was accomplished, and (2) which files were created or modified (with file paths).
2. THE Hook_Prompt SHALL instruct the agent to keep the recap concise — one or two sentences per element.
3. WHEN the agent's previous turn contained no file changes and no substantive action (a No_Op_Turn), THE Hook_Prompt SHALL instruct the agent to skip the recap and proceed directly to the Ask_Bootcamper_Question.

### Requirement 3: Ask Bootcamper Question

**User Story:** As a bootcamper, I want the agent to always end with a clear 👉-prefixed question asking what I want to do next, so that I always have a prompt to continue the conversation.

#### Acceptance Criteria

1. WHEN the hook fires, THE Hook_Prompt SHALL instruct the agent to end its output with an Ask_Bootcamper_Question — a question prefixed with 👉 that asks the bootcamper what they want to do next.
2. THE Ask_Bootcamper_Question SHALL always be the final element of the agent's output.
3. THE Hook_Prompt SHALL instruct the agent to make the Ask_Bootcamper_Question contextual — it should relate to the work that was just done or the current bootcamp module, not be a generic "what's next?" every time.
4. IF the agent's previous output already ended with a 👉-prefixed question, THEN THE Hook_Prompt SHALL instruct the agent to not add a second 👉 question — the existing 👉 question is sufficient and serves as the closing question.

### Requirement 4: Closing Question Ownership

**User Story:** As a power author, I want the `ask-bootcamper` hook to be the single owner of all closing questions, so that the bootcamper never sees duplicate questions and the conversation flow is consistent.

#### Acceptance Criteria

1. THE bootcamp steering instructions SHALL include a rule that the agent's main work output must not end with a Closing_Question — the `ask-bootcamper` hook is responsible for all closing questions.
2. THE steering instruction SHALL be added to the main bootcamp steering file (`senzing-bootcamp/steering/steering.md` or equivalent) so it applies to all agent turns.
3. THE steering instruction SHALL explicitly reference the `ask-bootcamper` hook as the reason the agent should not ask closing questions itself.
4. WHEN the agent needs to present choices or ask for input mid-conversation (not at the end of a turn), THE agent SHALL use the 👉 prefix for those questions — all questions to the bootcamper use 👉 regardless of position.
5. THE Hook_Prompt SHALL instruct the agent that if the output already ends with a 👉-prefixed question, the hook should not add a second one — the existing 👉 question is sufficient.
6. THE agent SHALL NOT ask any question at the end of its turn that the `ask-bootcamper` hook would also ask — the hook is the single source of "what's next" closing questions, and the agent must not duplicate that responsibility.

### Requirement 5: Hook Structure Stability

**User Story:** As a power author, I want the hook's event type and action type to remain unchanged, so that the hook continues to fire correctly.

#### Acceptance Criteria

1. THE Hook file SHALL retain the event type `agentStop` in the `when.type` field.
2. THE Hook file SHALL retain the action type `askAgent` in the `then.type` field.
3. THE Hook file SHALL be valid JSON containing the keys: `name`, `version`, `description`, `when`, and `then`.

### Requirement 6: Registry Synchronization

**User Story:** As a power author, I want the hook registry to always reflect the current hook prompt, so that documentation and behavior stay in sync.

#### Acceptance Criteria

1. WHEN the Hook_Prompt is updated in the hook file, THE Hook_Registry SHALL contain the identical prompt text for the `ask-bootcamper` entry.
2. WHEN the hook file is renamed, THE Hook_Registry SHALL be updated in the same change to prevent drift between the hook file and the registry.

### Requirement 7: Test Suite Update

**User Story:** As a power author, I want the existing test suite updated to validate the renamed hook and new behavior, so that regressions are caught.

#### Acceptance Criteria

1. THE test file SHALL be renamed from `test_summarize_on_stop_hook.py` to `test_ask_bootcamper_hook.py` to match the new hook name.
2. THE test suite SHALL validate that the hook file is named `ask-bootcamper.kiro.hook` and contains the correct metadata (name "Ask Bootcamper", event type `agentStop`, action type `askAgent`).
3. THE test suite SHALL validate that the Hook_Prompt contains instructions for producing a recap (accomplished, files changed).
4. THE test suite SHALL validate that the Hook_Prompt contains instructions for ending with a 👉-prefixed question.
5. THE test suite SHALL validate that the Hook_Prompt contains instructions for skipping the recap on No_Op_Turns.
6. THE test suite SHALL validate that the Hook_Registry prompt matches the hook file prompt exactly.
7. FOR ALL valid 👉-prefixed question strings, parsing the Hook_Prompt SHALL confirm the presence of 👉 question instructions (round-trip property between marker generation and prompt validation).
