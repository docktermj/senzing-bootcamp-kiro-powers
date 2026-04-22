# Design Document

## Overview

The module completion workflow is implemented as a single agent steering file (`senzing-bootcamp/steering/module-completion.md`, inclusion: manual). The Agent loads it after any module finishes and follows its sequential instructions: write a journal entry, ask for reflection, present next-step options, then check for path completion. No application code is involved — the entire workflow is steering-file-driven.

## Architecture

### Steering File

```text
senzing-bootcamp/steering/
└── module-completion.md    # Post-module workflow (inclusion: manual)
```

Loaded manually by the Agent after each module completes. Depends on `lessons-learned.md` for path-completion retrospectives.

### Post-Module Sequence

```text
Module Completes
  └─ Load module-completion.md
       ├─ Step 1: Journal Entry
       │    └─ Append structured entry to docs/bootcamp_journal.md
       ├─ Step 2: Reflection
       │    ├─ 👉 Ask for takeaway → WAIT
       │    └─ Append response (or "No additional notes")
       ├─ Step 3: Next-Step Options
       │    ├─ Present: Proceed / Iterate / Explore / Share
       │    ├─ Module 1 special: Explore = visualization re-offer
       │    └─ 👉 "What would you like to do?" → WAIT
       └─ Step 4: Path Completion Check
            ├─ Compare current module against Path_Completion_Map
            ├─ NOT complete → done
            └─ COMPLETE → celebration flow
                 ├─ 🎉 message + artifact summary + file locations
                 ├─ Next options (switch path / harden / use code)
                 ├─ Load lessons-learned.md → offer retrospective
                 └─ Remind: "bootcamp feedback"
```

### Journal Entry Format

Each entry appended to `docs/bootcamp_journal.md`:

```markdown
## Module N: [Name] — Completed [date]
**What we did:** [1-2 sentences]
**What was produced:** [files/artifacts]
**Why it matters:** [enables next step]
**Bootcamper's takeaway:** [reflection response or "No additional notes"]
```

### Path Completion Map

| Path | Final Module |
| ---- | ------------ |
| A    | Module 1     |
| B    | Module 8     |
| C    | Module 8     |
| D    | Module 12    |

### Artifact Location Summary (shown at path completion)

| Directory          | Contents                    |
| ------------------ | --------------------------- |
| `src/`             | Application code            |
| `data/transformed/`| Processed data files        |
| `docs/`            | Journal, guides, glossary   |
| `config/`          | Preferences, progress state |
| `database/`        | Senzing database files      |

## Constraints

- No application code — entirely steering-file-driven.
- Journal file is created on first use if it does not exist.
- Reflection question must not be repeated or pushed if declined.
- `lessons-learned.md` must be loadable at path completion time.
- Module 1 Explore option assumes visualization was already offered earlier in the module flow.
