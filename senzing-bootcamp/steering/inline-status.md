---
inclusion: manual
---

# Inline Status Response

When the bootcamper asks for status using any of these trigger phrases: "where am I", "status", "what step am I on", "show progress", "how far along am I":

## Steps

1. Read `config/bootcamp_progress.json`
2. Read `config/data_sources.yaml` (if exists)
3. Read `config/bootcamp_preferences.yaml` for track selection
4. Compute track completion percentage
5. Format response using the template below

## Response Template

```
📍 **Module [N]: [Title]** — Step [S] of [Total]

Track: [Track Display Name] — [X]% complete
Data sources: [count] registered ([names])
Next milestone: [what completing current step unlocks]

👉 Ready to continue with [current step description]?
```

## Format Rules

- Maximum 8 lines total
- Starts with 📍 emoji and current position
- Includes track name and completion percentage
- Shows data sources only if registry exists
- Ends with a single 👉 question to resume flow
- Do NOT show historical analytics or session stats — keep it compact

## Track Completion Calculation

Track completion uses partial credit for the current module:

- Completed modules in track: count all steps as done
- Current module: count completed steps as partial credit
- Locked modules: zero credit

Percentage = (completed steps across track modules / total steps across track modules) × 100

Track module lists:
- Quick Demo: Modules 2, 3
- Core Bootcamp: Modules 1, 2, 3, 4, 5, 6, 7
- Advanced Topics: Modules 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11

## Edge Cases

- **No progress file**: Respond with "You haven't started yet — would you like to begin onboarding?"
- **Between modules** (current_module is null): Show last completed module and next available module
- **Track not selected**: Omit the track line, show module progress only
- **No data sources registered**: Omit the data sources line
