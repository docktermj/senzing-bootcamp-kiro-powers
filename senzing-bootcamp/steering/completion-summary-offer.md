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

## Summary Offer Message Format

When a stopping point is detected, present the following offer message:

> 📄 **Completion Summary PDF**
>
> I can generate a Completion Summary PDF that captures your bootcamp journey — organized by module, it includes:
>
> - **Questions asked** — what you wanted to know
> - **Answers given** — what was explained
> - **Actions taken** — what was built and configured
> - **Artifacts created** — scripts, configs, data files, and reports produced
>
> Would you like me to generate it? (yes/no)

The message must:

1. Name the deliverable as "Completion Summary PDF"
2. List all four content categories: questions asked, answers given, actions taken, artifacts created
3. State that content is organized by module

## Prompt Format

The offer must be presented as a **binary yes/no prompt**. The bootcamper must explicitly accept or decline before the post-completion flow continues.

- If the bootcamper accepts ("yes"): invoke the narrative formatter followed by the PDF generator
- If the bootcamper declines ("no"): proceed to the next post-completion step without generating any summary file and without re-prompting for the same stopping point

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
