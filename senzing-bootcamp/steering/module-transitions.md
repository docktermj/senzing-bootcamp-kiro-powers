---
inclusion: auto
---

# Module Transitions

Rules for starting and completing modules. Kiro loads this when module work is happening.

## Journey Map (at module start)

Show the bootcamper a compact journey map with their current position. Use the path from `config/bootcamp_preferences.yaml` to show only modules in their path:

```text
✅ Module 0: Installed the SDK — Senzing is ready to use
✅ Module 1: Ran the demo — saw entity resolution in action
→  Module 2: Define your business problem — so we know what to solve
   Module 3: Collect data — get your data into the project
   Module 5: Map data — translate your fields into Senzing format
```

Mark completed with ✅, current with →, upcoming plain. Include the one-line "why" for each.

## Before/After Framing (at module start)

Each module steering file has a `Before/After` line. Present it to the user so they know what they have now and what they'll have when the module is done.

## Bootcamp Journal (at module completion)

After each module completes, append a short entry to `docs/bootcamp_journal.md`:

```markdown
## Module N: [Name] — Completed [date]
**What we did:** [1-2 sentences]
**What was produced:** [files/artifacts created]
**Why it matters:** [how this enables the next step]
```

Create the file if it doesn't exist.
