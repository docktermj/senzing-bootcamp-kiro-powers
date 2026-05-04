---
inclusion: always
---

# Module Transitions

## Module Start Banner

Display this banner at the start of every module. This is the module equivalent of the onboarding welcome banner. Replace N with the module number and [MODULE NAME IN CAPS] with the module's full name in uppercase.

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀🚀🚀  MODULE N: [MODULE NAME IN CAPS]  🚀🚀🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Journey Map (at module start)

MUST use this exact table format. Only show modules in the user's selected path from `config/bootcamp_preferences.yaml`.

| Module | Name | Status |
|--------|------|--------|
| 2 | SDK Setup | ✅ Complete |
| → 3 | Quick Demo | 🔄 Current |
| 1 | Business Problem | ⬜ Upcoming |

Use ✅ for completed modules, 🔄 for the current module (prefix module number with →), ⬜ for upcoming modules. Include one-line "why" for each.

**Step-level detail in status column:** If `current_step` is present in `config/bootcamp_progress.json` for the current module, display the step position in the status column: `🔄 Current — Step S/T` (where S is `current_step` — either an integer or a sub-step identifier string like `"5.3"` or `"7a"` — and T is the total number of numbered steps in the module steering file). When `current_step` is a sub-step identifier, display it directly (e.g., `🔄 Current — Step 5.3/26`). When it is an integer, display the existing format (e.g., `🔄 Current — Step 5/26`). If `current_step` is absent, display the existing `🔄 Current` status without step detail.

Example with step info:

| Module | Name | Status |
|--------|------|--------|
| 2 | SDK Setup | ✅ Complete |
| → 5 | Data Quality & Mapping | 🔄 Current — Step 3/12 |
| 6 | Single Source Loading | ⬜ Upcoming |

## Before/After Framing (at module start)

Present the `Before/After` line from the module's steering file so the user knows what they have now and what they'll have when done.

## Step-Level Progress

Every step within a module, communicate three things:

1. **Before:** "Next up: [action]. This matters because [reason]." Never bare "Working..."
2. **During:** Status updates describing what's happening (e.g., "Analyzing 15 columns across 1,000 rows...")
3. **After:** What changed, what was produced, file paths. Always include paths.

**Checkpoint emission:** After completing each numbered step or sub-step, write a checkpoint to `config/bootcamp_progress.json` updating `current_step` and `step_history`. Sub-step checkpoints follow the same emission pattern as whole-step checkpoints — set `current_step` to the sub-step identifier string and update `step_history` accordingly.

## Module Completion

Provide a clear summary: what was accomplished, all files produced with paths, why it matters for the next module.

Then follow the journal and path-completion rules in `module-completion.md`.
