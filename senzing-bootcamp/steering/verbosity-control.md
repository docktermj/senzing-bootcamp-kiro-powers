---
inclusion: auto
description: "Verbosity control system — output categories, presets, adjustment instructions, and content rules by level"
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

### Conversation Style Sync

Whenever the bootcamper requests a style change, update the `conversation_style` key in the preferences file alongside the `verbosity` block:

- **Verbosity preset change** → update `conversation_style.verbosity_preset` to the new preset name. If the preset is `custom`, also update `conversation_style.category_levels` with the per-category values.
- **Tone feedback** (e.g., "be more concise", "more detail please") → update `conversation_style.tone` to the matching descriptor (`concise`, `conversational`, or `detailed`).
- **Pacing feedback** (e.g., "one thing at a time", "you can group things") → update `conversation_style.pacing` to the matching value (`one_concept_per_turn` or `grouped_concepts`).
- **Question framing feedback** (e.g., "shorter questions", "more context before questions") → update `conversation_style.question_framing` to the matching value (`minimal`, `moderate`, or `full`).

### Session Start

On session start, read the `verbosity` key from the preferences file:

- If the key exists, apply the stored preset and category levels.
- If the key does not exist, apply the `standard` preset as the default.
- If the key exists but is malformed, apply `standard` and inform the bootcamper that preferences were reset.

## Content Rules by Level

### explanations

- **Level 1 — "What" only:** Single sentence describing the action. Omit rationale and workflow context.
- **Level 2 — "What" + "Why":** Action description followed by purpose or rationale.
- **Level 3 — "What" + "Why" + workflow connection:** Action, rationale, and how this step fits into the broader pipeline.

### code_walkthroughs

- **Level 1 — No walkthrough:** Let the code speak for itself. Code comments within generated code are still permitted.
- **Level 2 — Block-level summary:** Summarize what each logical section does in one or two sentences per block.
- **Level 3 — Detailed block or line-by-line:** Explain each block in detail, including why specific SDK methods were chosen and what alternatives exist.

### step_recaps

- **Level 1 — One-line summary + file paths:** Single sentence + list of file paths created or modified.
- **Level 2 — Accomplishment + files + understanding check:** What was accomplished, file paths, and what the bootcamper should understand before proceeding.
- **Level 3 — Level 2 + next-step connection:** Everything from Level 2, plus how this step's output connects to the next step and module goal.

### technical_details

- **Level 1 — Omit:** No SDK internals, configuration specifics, or performance notes.
- **Level 2 — Relevant details when they aid understanding:** Include SDK details and config specifics when they help understanding. Omit purely internal details.
- **Level 3 — Full technical depth:** SDK internals, configuration deep-dives, performance characteristics, and resolution algorithm details.

### code_execution_framing

- **Level 1 — "What this code does" + one-line result:** Plain-language summary before execution, one-line result after.
- **Level 2 — "Before" + "What" + "After":** Current state, what the code does, what changed.
- **Level 3 — Level 2 + specific metric values:** Everything from Level 2, plus specific before/after values for key metrics.

## Framing Pattern Examples

### "What and Why" (explanations)

- **L1:** We're adding the customer data source to the Senzing configuration.
- **L2:** We're adding the customer data source to the Senzing configuration. This registers the source so Senzing knows where records come from when it resolves entities.
- **L3:** We're adding the customer data source to the Senzing configuration. This registers the source so Senzing knows where records come from. Once registered, we'll use this name in the mapping file (Module 5) and loading script (Module 6).

### Code Execution (code_execution_framing)

- **L1:** What this code does: Loads 500 customer records. Result: 500 records loaded successfully.
- **L2:** Before: Database has 0 records. What: Reads each record and loads via customer mapping. After: 500 records loaded, entities resolved.
- **L3:** Before: Records: 0, Entities: 0. What: Reads and loads via mapping. After: Records: 0→500, Entities: 0→423, Time: 12.3s (40.6 rec/s).

### Step Recap (step_recaps)

- **L1:** Created the customer data mapping. Files: `config/mappings/customers.json`
- **L2:** Created the mapping defining how each CSV column maps to Senzing attributes. Files: `config/mappings/customers.json`. The mapping tells Senzing which columns are names, addresses, and identifiers.
- **L3:** Level 2 content + "Next, we'll use this mapping to load records into Senzing in Module 6."
