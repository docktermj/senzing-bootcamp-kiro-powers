# Design: Consolidate Redundant agentStop Hooks

## Overview

This feature merges the two agentStop hooks ("Ask Bootcamper" and "Feedback Submission Reminder") into a single consolidated agentStop hook. The merged hook handles both responsibilities: (1) the recap/closing question or suppression logic from Ask Bootcamper, and (2) the conditional feedback reminder that only triggers near track completion. This eliminates the visual noise of two hook invocations firing after every agent turn.

## Architecture

### Affected Files

| File | Change Type | Purpose |
|------|-------------|---------|
| `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook` | Modify | Update to include feedback reminder logic in its prompt |
| `senzing-bootcamp/hooks/feedback-submission-reminder.kiro.hook` | Delete | Remove the separate hook — its logic moves into ask-bootcamper |
| `senzing-bootcamp/steering/hook-registry.md` | Modify | Update registry to reflect consolidated hook, remove separate feedback reminder entry |

### Design Rationale

Rather than creating a new hook, we consolidate into the existing `ask-bootcamper` hook because:
- It already fires on `agentStop` and handles the primary post-turn logic
- The feedback reminder is a lightweight conditional check that fits naturally as a secondary responsibility
- Keeping the `ask-bootcamper` name preserves backward compatibility with any references in steering files

### Consolidated Hook Logic

```
IF a 👉 question is pending in the previous turn:
  → Produce zero output (existing suppression behavior)
ELSE:
  → Produce recap of work done + contextual closing 👉 question (existing behavior)
  → ADDITIONALLY: If the bootcamper is approaching or has completed a track,
    append a brief feedback reminder to the closing message
```

The feedback reminder check is a simple conditional appended to the SECOND branch (recap + closing question). It only produces visible output when track completion is near — otherwise it adds nothing.

## Components and Interfaces

### Component 1: Merged Hook Prompt

The `ask-bootcamper.kiro.hook` prompt will be updated to include a new section at the end:

```
--- FEEDBACK REMINDER (conditional) ---
If the bootcamper has completed or is on the final step of their current track,
append to your closing message: "By the way, if you have feedback about the
bootcamp experience, just say 'bootcamp feedback' anytime."
Otherwise, do NOT mention feedback — produce nothing for this section.
```

### Component 2: Hook File Deletion

The `feedback-submission-reminder.kiro.hook` file is deleted entirely. Its logic is subsumed by the merged prompt.

### Component 3: Hook Registry Update

The `hook-registry.md` entry for `feedback-submission-reminder` is removed. The `ask-bootcamper` entry is updated to note its dual responsibility.

## Data Models

No data model changes. The hook JSON structure remains the same — only the prompt text within `ask-bootcamper.kiro.hook` changes.

## Error Handling

Not applicable — this is a hook prompt consolidation with no runtime error paths.

## Testing Strategy

- Verify that only one agentStop hook exists in `senzing-bootcamp/hooks/` after the change
- Verify that the consolidated hook prompt contains both the ask-bootcamper logic and the feedback reminder conditional
- Verify that the hook-registry.md no longer references a separate feedback-submission-reminder hook
- Verify that the feedback reminder logic only triggers when track completion is near (by checking the conditional language in the prompt)
