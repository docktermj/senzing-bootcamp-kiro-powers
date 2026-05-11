---
inclusion: manual
description: "Protocol for switching bootcamp tracks mid-session"
---

# Track Switching

When a bootcamper wants to switch tracks mid-bootcamp, follow this protocol to preview the change, confirm intent, and apply the switch safely.

## Confirmation Gate

Before making any changes, run the track switcher in dry-run mode to preview the effect:

```bash
python3 senzing-bootcamp/scripts/track_switcher.py --from <current_track> --to <target_track> --progress config/bootcamp_progress.json
```

Present the before/after comparison to the bootcamper:

| | Before | After |
| --- | --- | --- |
| **Track** | `<current_track>` | `<target_track>` |
| **Modules completed** | (list from progress) | (same — progress is preserved) |
| **Modules remaining** | (ordered list with names) | (ordered list with names) |
| **Extra modules** | — | (completed modules not in new track, with names) |

Then ask:

👉 "This will switch you from `<current_track>` to `<target_track>`. You have X modules remaining. Shall I apply the switch?"

> **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

## Script Invocation

**Preview (dry-run, default):**

```bash
python3 senzing-bootcamp/scripts/track_switcher.py --from <current_track> --to <target_track> --progress config/bootcamp_progress.json
```

**Apply (after bootcamper confirms):**

```bash
python3 senzing-bootcamp/scripts/track_switcher.py --from <current_track> --to <target_track> --progress config/bootcamp_progress.json --apply
```

## Post-Switch Guidance

After applying the switch, display:

1. **New track:** `<target_track>`
2. **Remaining modules (N):** ordered list with module numbers and names
3. **Extra modules:** if any completed modules are not part of the new track, list them and explain that progress is preserved — these modules simply aren't required by the new track

Then offer:

👉 "Would you like to begin Module X: <name> now?"

> **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

## Completion Case

When the switch results in zero remaining modules (all target track modules already completed):

- Congratulate the bootcamper: "You've already completed all modules in `<target_track>`!"
- Offer to load `lessons-learned.md` for a retrospective

👉 "You've finished the entire track. Would you like to do a lessons-learned retrospective?"

> **🛑 STOP — End your response here.** Wait for the bootcamper's real input.

## Cancellation Case

If the bootcamper declines the switch after seeing the comparison:

- Make no changes to `config/bootcamp_progress.json`
- Confirm: "No changes made. You're still on `<current_track>`."
- Resume normal module flow
