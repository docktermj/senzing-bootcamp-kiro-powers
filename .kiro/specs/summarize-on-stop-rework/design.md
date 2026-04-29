# Design Document

## Overview

This design renames the `summarize-on-stop` hook to `ask-bootcamper`, rewrites its prompt to always end with a 👉-prefixed closing question, and adds a steering rule that prevents the agent from asking its own closing questions. The hook becomes the single owner of "what's next" questions.

## Architecture

### Components

1. **Hook File** (`senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`)
   - Renamed from `summarize-on-stop.kiro.hook`
   - JSON structure with updated `name`, `description`, and `prompt`
   - Event type `agentStop`, action type `askAgent` (unchanged)

2. **Hook Registry** (`senzing-bootcamp/steering/hook-registry.md`)
   - Old `summarize-on-stop` entry replaced with `ask-bootcamper`
   - Prompt text matches hook file exactly

3. **Agent Instructions** (`senzing-bootcamp/steering/agent-instructions.md`)
   - Updated Communication section: agent must not end turns with closing questions
   - References `ask-bootcamper` hook as the owner of closing questions
   - All questions to the bootcamper use 👉 prefix

4. **Test Suite** (`senzing-bootcamp/tests/test_ask_bootcamper_hook.py`)
   - Renamed from `test_summarize_on_stop_hook.py`
   - Validates new hook metadata, prompt content, and registry sync

### Hook Prompt Design

The new prompt follows a structured format with three conditional paths:

```
Path 1: Previous output already ends with 👉 question
  → Do nothing (question already present)

Path 2: No-op turn (no files changed, no substantive action)
  → Skip recap, ask contextual 👉 question

Path 3: Normal turn (work was done)
  → Recap: (1) what was accomplished, (2) files created/modified
  → Ask contextual 👉 question
```

The prompt must stay concise (target: under 500 characters) and use clear conditional language.

### Steering Instruction Design

The existing Communication section in `agent-instructions.md` already has:
```
One question at a time, wait for response. Prefix input-required questions with "👉" in ALL modules.
```

This will be updated to add:
- The agent must not end its turn with a closing question
- The `ask-bootcamper` hook owns all closing questions
- Mid-conversation 👉 questions are still allowed

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `senzing-bootcamp/hooks/summarize-on-stop.kiro.hook` | Delete | Old hook file removed |
| `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` | Create | New hook file with updated name, description, prompt |
| `senzing-bootcamp/steering/hook-registry.md` | Modify | Replace `summarize-on-stop` entry with `ask-bootcamper` |
| `senzing-bootcamp/steering/agent-instructions.md` | Modify | Add closing-question ownership rule to Communication section |
| `senzing-bootcamp/tests/test_summarize_on_stop_hook.py` | Delete | Old test file removed |
| `senzing-bootcamp/tests/test_ask_bootcamper_hook.py` | Create | New test file validating renamed hook and new behavior |

## Correctness Properties

### Property 1: Hook Prompt Contains Recap Instructions

**Type:** Property-based test
**Validates:** Requirement 2.1, 2.2

For any generated agent output string (with or without file paths), the hook prompt must contain keywords related to recap elements: "accomplish" (or equivalent) and "files" (or equivalent). This ensures the prompt always instructs the agent to produce a recap regardless of what the agent output looks like.

**Strategy:** Generate random agent output strings. For each, parse the hook prompt and verify it contains recap-related keywords.

### Property 2: Hook Prompt Contains 👉 Question Instructions

**Type:** Property-based test
**Validates:** Requirement 3.1, 3.4, 7.7

For any generated 👉-prefixed question string, the hook prompt must contain instructions about ending with a 👉 question and about not duplicating an existing 👉 question. This is a round-trip property: generate question markers → verify the prompt handles them.

**Strategy:** Generate random 👉-prefixed strings and WAIT patterns. For each, verify the prompt mentions 👉 and contains duplicate-detection instructions.

### Property 3: Hook Metadata Stability

**Type:** Example-based test
**Validates:** Requirement 5.1, 5.2, 5.3

The hook file must be valid JSON with keys `name`, `version`, `description`, `when`, `then`. The `when.type` must be `agentStop` and `then.type` must be `askAgent`. The `name` must be "Ask Bootcamper".

### Property 4: Registry-Hook Prompt Synchronization

**Type:** Example-based test
**Validates:** Requirement 6.1

The prompt extracted from the hook file must exactly match the prompt extracted from the hook registry entry for `ask-bootcamper`.

### Property 5: No-Op Turn Skip Instructions

**Type:** Example-based test
**Validates:** Requirement 2.3

The hook prompt must contain instructions for skipping the recap when no substantive work was done (no-op turn detection).

### Property 6: Steering File Contains Closing Question Rule

**Type:** Example-based test
**Validates:** Requirement 4.1, 4.2, 4.3

The agent instructions steering file must contain a rule about the `ask-bootcamper` hook owning closing questions, and the agent not ending turns with closing questions.

### Property 7: Old Hook Removed

**Type:** Example-based test
**Validates:** Requirement 1.1, 1.5

The old `summarize-on-stop.kiro.hook` file must not exist. The hook registry must not contain a `summarize-on-stop` entry.
