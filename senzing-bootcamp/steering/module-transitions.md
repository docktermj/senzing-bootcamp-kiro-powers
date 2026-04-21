---
inclusion: fileMatch
fileMatchPattern: "config/bootcamp_progress.json"
description: "Module boundary guidance: start banners, journey maps, before/after framing, step-level progress, and completion summaries. Loaded when bootcamp progress is read or written."
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
| 0 | SDK Setup | ✅ Complete |
| → 1 | Quick Demo | 🔄 Current |
| 2 | Business Problem | ⬜ Upcoming |

Use ✅ for completed modules, 🔄 for the current module (prefix module number with →), ⬜ for upcoming modules. Include one-line "why" for each.

## Before/After Framing (at module start)

Present the `Before/After` line from the module's steering file so the user knows what they have now and what they'll have when done.

## Step-Level Progress

Every step within a module, communicate three things:

1. **Before:** "Next up: [action]. This matters because [reason]." Never bare "Working..."
2. **During:** Status updates describing what's happening (e.g., "Analyzing 15 columns across 1,000 rows...")
3. **After:** What changed, what was produced, file paths. Always include paths.

## Module Completion

Provide a clear summary: what was accomplished, all files produced with paths, why it matters for the next module.

Then follow the journal and path-completion rules in `module-completion.md`.
