# Design Document

## Overview

The feedback collection workflow is implemented as a single agent steering file (`senzing-bootcamp/steering/feedback-workflow.md`, inclusion: manual). The Agent loads it when a Bootcamper uses a trigger phrase and follows its sequential instructions: check/create the feedback file, gather answers one at a time, format a structured entry, append it, and confirm. No application code is involved — the entire workflow is steering-file-driven.

## Architecture

### Steering File

```text
senzing-bootcamp/steering/
└── feedback-workflow.md    # Feedback collection workflow (inclusion: manual)
```

Loaded manually by the Agent when a trigger phrase is detected.

### Feedback File Structure

```text
docs/feedback/
└── SENZING_BOOTCAMP_POWER_FEEDBACK.md    # Created from template on first use

senzing-bootcamp/docs/feedback/
├── README.md
└── SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md    # Source template
```

### Workflow Sequence

```text
Trigger Phrase Detected
  └─ Load feedback-workflow.md
       ├─ Step 1: File Check
       │    ├─ Feedback file exists → proceed
       │    └─ Missing → copy template, set today's date
       ├─ Step 2: Gather Feedback (one question at a time)
       │    ├─ Category (7 options) → WAIT
       │    ├─ Module (0-12 or General) → WAIT
       │    ├─ Description → WAIT
       │    ├─ Impact → WAIT
       │    ├─ Suggested fix → WAIT
       │    └─ Priority (High/Medium/Low) → WAIT
       ├─ Step 3: Format Entry
       │    └─ Build structured markdown block
       ├─ Step 4: Append to Feedback File
       │    └─ Insert under "Your Feedback" section, preserve existing
       └─ Step 5: Confirm and Guide
            ├─ Confirm save location
            ├─ Offer: add more feedback or continue bootcamp
            └─ Do NOT submit to MCP server unless explicitly asked
```

### Feedback Entry Format

Each entry appended to the feedback file:

```markdown
## Improvement: [Brief title from description]

**Date**: YYYY-MM-DD
**Module**: [0-12 or "General"]
**Priority**: [High/Medium/Low]
**Category**: [Documentation/Workflow/Tools/UX/Bug/Performance/Security]

### What Happened
[User's description]

### Why It's a Problem
[User's impact explanation]

### Suggested Fix
[User's suggestion or "None provided"]

### Workaround Used
[If provided, or "None"]
```

### Feedback Categories

| Category      | Scope                                  |
| ------------- | -------------------------------------- |
| Documentation | Clarity, accuracy, completeness        |
| Workflow      | Step ordering, prerequisites, transitions |
| Tools         | Missing utilities, template improvements |
| UX            | Confusion points, navigation issues    |
| Bug           | Incorrect behavior, errors             |
| Performance   | Slow operations, optimization opportunities |
| Security      | Security concerns, compliance issues   |

### Agent Reminder Points

| Trigger         | Action                                      |
| --------------- | ------------------------------------------- |
| Module 1 start  | Inform Bootcamper about feedback mechanism   |
| Module 12 end   | Remind Bootcamper to share feedback file     |

## Constraints

- No application code — entirely steering-file-driven.
- Feedback file is created from template on first use if it does not exist.
- Questions must be asked one at a time with WAIT between each.
- Feedback is local-only; no MCP server submission unless the Bootcamper explicitly requests it.
- Existing feedback entries must be preserved when appending new ones.
