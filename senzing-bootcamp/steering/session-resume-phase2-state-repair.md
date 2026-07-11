---
inclusion: manual
---

# State Repair: Stale or Corrupted Progress

## Guard Condition

If this file was loaded but none of the following conditions are true, skip all content below and return to the Phase-1 flow:

- `config/bootcamp_progress.json` fails to parse as valid JSON
- `config/bootcamp_progress.json` is missing entirely
- `current_module` in the progress file is inconsistent with project artifacts

## Progress Reconstruction from Artifacts

When `config/bootcamp_progress.json` is missing or corrupted (unparseable JSON, missing required fields), reconstruct progress from project artifacts:

1. Scan `src/`, `data/`, and `docs/` for evidence of completed work
2. Check for module-specific artifacts (e.g., `src/query/` for Module 8, `src/transform/` for Module 5)
3. Inform the bootcamper what was found and what progress can be inferred
4. Offer to rebuild the progress file based on detected artifacts
5. If the bootcamper agrees, write a corrected `config/bootcamp_progress.json` with the inferred state

If `config/bootcamp_preferences.yaml` is also missing or corrupted, note this to the bootcamper and offer to re-run preference collection (language, track, cloud provider) before proceeding.

## Handling Stale or Corrupted State

If `bootcamp_progress.json` exists but contains inconsistencies (e.g., claims Module 8 is complete but `src/query/` is empty):

1. Run `python3 scripts/validate_module.py` to check actual artifact state
2. Show the bootcamper any discrepancies between the progress file and actual project state
3. Offer to correct the progress file based on what actually exists on disk
4. Proceed from the last verifiably complete module

### Discrepancy Examples

| Progress File Claims | Actual State | Action |
|---------------------|--------------|--------|
| Module N complete | No artifacts for Module N | Mark Module N incomplete |
| `current_module: 8` | Only Modules 1–5 artifacts exist | Reset `current_module` to 6 |
| `current_step: 7` | Module steering has only 5 steps | Clear `current_step`, use artifact scan |

After corrections are applied, return to the Phase-1 flow at Step 3 (Summarize and Confirm) with the corrected state.

## Pending Question Re-Rendering

When `config/.question_pending` exists from a prior session, an unanswered decision-point question was stored there in the structured format (type on line 1, raw question text on lines 2+). That raw text carries no presentation formatting, so echoing it verbatim would drop the 👉 prefix and bold styling.

When returning to the Phase-1 flow at Step 3 (Summarize and Confirm), re-render the stored question instead of echoing it:

1. Read the stored question text from lines 2+ of `config/.question_pending`.
2. Re-render it canonically as `👉 **{stored question text}**` — the 👉 at the start of the line, outside the bold span, and the text in CommonMark bold.
3. Present it as the turn's single closing 👉 question, replacing the default "Ready to continue…?" question.

Do not rewrite or delete `config/.question_pending` here — it stays in place. On the bootcamper's next response the treat-as-answer and delete-and-process rules apply unchanged.
