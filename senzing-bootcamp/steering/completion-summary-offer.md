---
inclusion: manual
description: "Detects stopping points and presents the completion summary PDF offer"
triggers:
  - module_completion
  - stop_request
  - track_switch
priority: high
---

# Completion Summary Offer

This steering file instructs the agent on when to detect stopping points in the bootcamp flow and how to present the completion summary PDF offer. It is steering-driven because detection requires evaluating conversational context (e.g., interpreting "I'm done" as a stop request vs. part of a longer statement).

## Stopping Point Detection Rules

A **stopping point** is detected when any of the following conditions are met:

### 1. Module 7 Completion (Core Track End)

When Module 7 appears in the `modules_completed` array of `config/bootcamp_progress.json`, detect a stopping point within the same agent turn that the module completion is recorded.

### 2. Module 11 Completion (Advanced Track End)

When Module 11 appears in the `modules_completed` array of `config/bootcamp_progress.json`, detect a stopping point within the same agent turn that the module completion is recorded.

### 3. Explicit Stop Request

When the bootcamper sends a message whose **primary intent** is to end the session. Match phrases such as:

- "stop here"
- "I'm done"
- "that's enough"
- "wrap up"
- "let's stop"
- "I want to stop"
- Semantically equivalent statements where ending the session is the main purpose

### 4. Track Switch at Boundary

When the bootcamper switches tracks at a track boundary (Module 7 for core-to-advanced, or any module endpoint defined by the track_switcher script), detect a stopping point for the **completed track** before the track switch is applied.

## False Positive Guards

### Stop Phrase in Longer Substantive Request

If the bootcamper's message contains a stop phrase embedded within a longer substantive request, do **NOT** trigger a stopping point from the stop phrase alone.

**Examples that should NOT trigger:**

- "I'm done with this module, let's move to the next one" — primary intent is to continue
- "Let's stop using SQLite and switch to PostgreSQL" — "stop" refers to a tool change
- "I want to stop and think about this before we proceed" — intent is to pause, not end
- "Wrap up this file and create the next one" — "wrap up" refers to a specific task

**Rule:** The stop phrase must represent the bootcamper's primary intent to end the session. If the message contains additional substantive instructions or requests, the stop phrase is incidental and should not trigger detection.

### Missing or Unreadable Progress File

If `config/bootcamp_progress.json` is missing or cannot be read when checking for module completion:

- Do **NOT** detect a stopping point
- Log a warning (e.g., "Warning: Could not read progress file — skipping stopping point detection")
- Continue the bootcamp flow without interruption

## Always Generate the Summary Document

When a stopping point is detected, **always** generate the completion-summary document **before** presenting the offer — independent of the bootcamper's yes/no answer. Run the markdown generator unconditionally:

```bash
python3 senzing-bootcamp/scripts/generate_completion_summary.py
```

This always writes `docs/completion_summary.md` — the module-by-module collection of questions posed, bootcamper responses, actions taken, and artifacts generated, built from `config/session_log.jsonl`. It mirrors the always-generate patterns already in graduation, where `production/GRADUATION_REPORT.md` is always created and the recap PDF is always attempted.

This step is **non-blocking**. If the script exits non-zero or raises (for example, `config/session_log.jsonl` is missing or unreadable → `parse_session_log` raises and `main()` returns exit code 1), log a warning and continue the post-completion flow:

> ⚠️ Completion summary generation skipped: <reason>. Continuing.

An empty-but-present session log is **not** an error path: the script still produces a valid markdown file with per-module "Session log was unavailable for this module." rendering. Only a missing or unreadable log triggers the warn-and-continue branch.

## Summary Offer Message Format

The completion summary has already been captured at `docs/completion_summary.md` (see "Always Generate the Summary Document"). The offer is about rendering a **shareable PDF** of that summary, not about whether the summary itself exists. When a stopping point is detected, present the following offer message:

> 📄 **Completion Summary PDF**
>
> I've captured your bootcamp journey in a Completion Summary — organized by module, it includes:
>
> - **Questions asked** — what you wanted to know
> - **Answers given** — what was explained
> - **Actions taken** — what was built and configured
> - **Artifacts created** — scripts, configs, data files, and reports produced
>
> It's saved at `docs/completion_summary.md`. Would you like me to also render a shareable Completion Summary PDF? (yes/no)

The message must:

1. Name the shareable deliverable as "Completion Summary PDF"
2. List all four content categories: questions asked, answers given, actions taken, artifacts created
3. State that content is organized by module
4. Make clear the summary itself is already saved at `docs/completion_summary.md`

## Prompt Format

The offer must be presented as a **binary yes/no prompt**. The completion summary document (`docs/completion_summary.md`) has already been created (see "Always Generate the Summary Document"), so the binary yes/no choice governs **only** the secondary concern: whether the shareable **Completion Summary PDF** is rendered and surfaced. `docs/completion_summary.md` remains created either way.

- If the bootcamper accepts ("yes"): render the shareable PDF by running `python3 senzing-bootcamp/scripts/generate_completion_summary.py --pdf` (→ `docs/completion_summary.pdf`) and surface the output path(s) to the bootcamper.
- If the bootcamper declines ("no"): skip **only** the PDF render and the surfacing/sharing, then proceed to the next post-completion step without re-prompting for the same stopping point. `docs/completion_summary.md` is still present.

## Ordering Rules

### Track Completion (Module 7 or Module 11)

Present the summary offer in this position within the track completion sequence:

1. Track completion celebration message (🎉)
2. **→ Completion Summary PDF offer ← (here)**
3. Export results offer (`scripts/export_results.py`)

If the export results offer is not available, present the summary offer as the next step after the celebration message.

### Mid-Session Stop (Explicit Stop Request)

Present the summary offer in this position:

1. Acknowledge the stop request
2. **→ Completion Summary PDF offer ← (immediately next, no intervening prompts)**

There must be no intervening prompts or offers between the acknowledgment and the summary offer.

### Simultaneous Detection

If both a track completion stopping point and a mid-session stopping point are detected for the same event (e.g., bootcamper says "stop here" at a track boundary), follow the **track completion sequence** (celebration message first, then summary offer) rather than the mid-session sequence.

## Repeat Policy

The summary offer is presented at **every** stopping point regardless of whether a previous summary was generated earlier in the session. Each stopping point is an independent opportunity to capture the current state of the bootcamp journey.
