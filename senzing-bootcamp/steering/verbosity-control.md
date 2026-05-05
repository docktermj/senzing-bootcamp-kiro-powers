---
inclusion: auto
description: "Verbosity control system — output categories, presets, and adjustment instructions"
---

# Verbosity Control

This steering file defines the verbosity control system. The agent consults it every turn to classify output into categories, apply per-category levels (1–3), and handle adjustment requests. Presets set all categories at once; bootcampers can also fine-tune individual categories via natural language.

## Output Categories

Every output section is classified into exactly one category before applying verbosity rules:

- **explanations** — Conceptual "what and why" context around actions and decisions
- **code_walkthroughs** — Line-by-line or block-by-block explanations of code
- **step_recaps** — Summaries of what a step accomplished and what changed
- **technical_details** — SDK internals, configuration specifics, and performance notes
- **code_execution_framing** — Before/during/after framing around code execution runs

## Preset Definitions

| Preset | explanations | code_walkthroughs | step_recaps | technical_details | code_execution_framing |
| --- | :---: | :---: | :---: | :---: | :---: |
| `concise` | 1 | 1 | 2 | 1 | 1 |
| `standard` | 2 | 2 | 2 | 2 | 2 |
| `detailed` | 3 | 3 | 3 | 3 | 3 |

- **concise** — Minimal output for experienced developers. Step recaps stay at 2 for orientation.
- **standard** — Balanced default. "What and why" context, block-level code summaries, before/after framing.
- **detailed** — Maximum depth including SDK internals and line-by-line code explanations.

## Natural Language Term Mapping

| Term | Maps to Category |
| --- | --- |
| "explanations", "context", "explain", "why" | `explanations` |
| "code detail", "code walkthrough", "code walkthroughs", "line by line" | `code_walkthroughs` |
| "recaps", "summaries", "recap", "summary" | `step_recaps` |
| "technical", "internals", "technical detail", "technical details" | `technical_details` |
| "before and after", "execution framing", "code framing", "framing" | `code_execution_framing` |

If the bootcamper's term does not match any entry, list the five categories with brief descriptions and ask the bootcamper to clarify.

## Adjustment Instructions

### Preset Changes

1. Identify the requested preset name.
2. Update all five category levels to match the preset definition table.
3. Write the updated `verbosity` block to the preferences file (`config/bootcamp_preferences.yaml` or `config/preferences_{member_id}.yaml` in team mode).
4. Confirm the change by stating the new preset name and summarizing the per-category levels.

### Natural Language Adjustments

1. Match the term to a category using the NL Term Mapping table (case-insensitive).
2. If no match, list the five categories with brief descriptions and ask the bootcamper to clarify.
3. If matched, adjust the category level by +1 (for "more") or −1 (for "less"), clamped to 1–3.
4. If the adjusted levels no longer match any named preset, set the preset to `custom`.
5. If the adjusted levels happen to match a named preset, set the preset to that preset's name.
6. Write the updated `verbosity` block to the preferences file.
7. Confirm the change by stating the category name and its new level.

### Custom Preset

When any individual category adjustment causes levels to diverge from all three named presets, the active preset becomes `custom`. This is not an error. If the bootcamper later selects a named preset, all categories reset to that preset's levels.

### Session Start

On session start, read the `verbosity` key from the preferences file:

- If the key exists, apply the stored preset and category levels.
- If the key does not exist, apply the `standard` preset as the default.
- If the key exists but is malformed, apply `standard` and inform the bootcamper that preferences were reset.

## Reference

Load the reference file when applying level-specific content rules or framing patterns for the first time in a session: #[[file:senzing-bootcamp/steering/verbosity-control-reference.md]]
