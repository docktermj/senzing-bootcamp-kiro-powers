# Bugfix Requirements Document

## Introduction

This bugfix consolidates two related Stop-hook UX defects in the senzing-bootcamp Kiro
Power. Both concern what the bootcamper *sees* at the end of a turn, not how the hook
logic is internally organized.

- **Defect 1 (Priority: Low, Category: UX):** Two Stop-triggered agent hooks surface in
  the UI whenever the agent stops — `ask-bootcamper` ("to wait for your answer") and
  `module-recap-append` ("to append module recap on completion"). Only one of them ever
  waits for the bootcamper's answer, so showing two Stop hooks adds visual clutter and
  implies that two things are waiting on the bootcamper.
- **Defect 2 (Priority: Medium, Category: UX):** On turns where the `ask-bootcamper` Stop
  hook evaluates all of its phases to no output, the agent leaks a sentence narrating its
  internal hook evaluation (for example, "My last message ends with a 👉 question, and no
  module was completed.") instead of emitting the required silent single "." and nothing
  else.

The fix is framed with the bug-condition methodology. The bug condition `C(X)` covers two
disjuncts: (1) a Stop event that would surface a second Stop hook in the UI, and (2) a
turn on which the `ask-bootcamper` hook's phases all produce no output. The fix-checking
property is that under `C(X)` the bootcamper sees exactly one "waiting for your answer"
Stop hook, and a no-output turn produces only ".". The preservation goal is that for all
non-`C(X)` inputs the observable behavior is identical to today: the recap is still
captured at module completion, precedence and firing order are unchanged, answer
processing still runs, and the "." silent-turn contract for other Stop hooks is untouched.

The exact consolidation mechanism (folding recap logic into `ask-bootcamper`, or otherwise
hiding the second Stop hook from the UI) is deliberately left to the design phase. Removing
or altering `preToolUse` write-gate hooks is out of scope.

## Bug Analysis

### Current Behavior (Defect)

What currently happens when the bug is triggered:

1.1 WHEN the agent stops (the Stop trigger fires) THEN the system surfaces two separate Stop-triggered hooks in the UI — "to wait for your answer" (`ask-bootcamper`) and "to append module recap on completion" (`module-recap-append`) — even though only `ask-bootcamper` ever waits for the bootcamper's answer.

1.2 WHEN the agent stops on a turn where no module was just completed THEN the system still surfaces the second "to append module recap on completion" Stop hook (which produces no visible output on that turn), adding visual clutter and implying two things are waiting on the bootcamper.

1.3 WHEN the `ask-bootcamper` Stop hook evaluates and all of its phases (Phase 1 closing question, Phase 2 step sequencing, Phase 3 MCP-first, Phase 4 question format) produce no output THEN the system displays a sentence narrating its internal hook evaluation (e.g., "My last message ends with a 👉 question, and no module was completed.") instead of the required silent output.

### Expected Behavior (Correct)

What should happen instead (fix-checking property for the buggy inputs above):

2.1 WHEN the agent stops THEN the system SHALL present only one "waiting for your answer" Stop hook to the bootcamper — e.g., by folding the recap logic into the answer-waiting hook, or otherwise avoiding surfacing a second Stop hook in the UI.

2.2 WHEN the agent stops and the recap logic runs THEN the system SHALL preserve the internal precedence — recap capture defers to a pending 👉 question and runs before the module-completion celebration — while still surfacing at most one Stop hook to the bootcamper.

2.3 WHEN the `ask-bootcamper` Stop hook evaluates and all of its phases produce no output THEN the system SHALL emit only a single "." with no explanatory sentence and no narration of its internal checks (e.g., no "...ends with a 👉 question...", no "no module was completed").

### Unchanged Behavior (Regression Prevention)

Existing behavior that must be preserved for all non-buggy inputs:

3.1 WHEN a module is completed THEN the system SHALL CONTINUE TO capture the structured recap section (the "## Module N" heading, "Questions & Responses", and "Actions Taken") to docs/bootcamp_recap.md, regardless of how the two Stop hooks are consolidated.

3.2 WHEN a module is completed THEN the system SHALL CONTINUE TO run recap capture before the module-completion celebration, and both SHALL CONTINUE TO defer to a pending 👉 question.

3.3 WHEN a 👉 question or a completed module is pending THEN the system SHALL CONTINUE TO wait for and process the bootcamper's answer via `ask-bootcamper`, which retains absolute precedence.

3.4 WHEN the celebration and enforcement Stop hooks fire THEN the system SHALL CONTINUE TO fire them in the documented agentstop_order precedence (recap before celebration, celebration below gate enforcement, and so on).

3.5 WHEN a Stop hook other than `ask-bootcamper` evaluates to no output THEN the system SHALL CONTINUE TO honor the single "." silent-turn contract unchanged.

3.6 WHEN the `preToolUse` write-gate hooks fire THEN the system SHALL CONTINUE TO operate exactly as today (these hooks are out of scope for this fix and SHALL NOT be removed or altered).

3.7 WHEN the Stop-hook registry files are read THEN hook-categories.yaml (`agentstop_order`) and hooks.lock.yaml SHALL CONTINUE TO stay mutually consistent with the actual set of Stop-trigger hooks after any consolidation.
