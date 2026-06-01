# Bugfix Requirements Document

## Introduction

The Senzing Bootcamp Power has a governing rule (rule 16): **"After all modules, in the graduation: ALWAYS create the completion-summary, which is the collection of module-by-module questions posed to the Bootcamper, the Bootcamper's response, the actions taken, and the artifacts generated."**

The implementation violates this rule. The dedicated **Completion Summary** artifact — the module-by-module collection of questions posed, bootcamper responses, actions taken, and artifacts generated, produced by `senzing-bootcamp/scripts/generate_completion_summary.py` at `docs/completion_summary.md` (and optionally `docs/completion_summary.pdf`) — is gated behind a **binary yes/no opt-in offer**. `senzing-bootcamp/steering/completion-summary-offer.md` states: *"The offer must be presented as a binary yes/no prompt. The bootcamper must explicitly accept or decline before the post-completion flow continues"* and *"If the bootcamper declines ('no'): proceed to the next post-completion step without generating any summary file."* So when the bootcamper declines, **no completion-summary artifact is created**, breaching the "ALWAYS create" rule.

### Artifact distinction (important)

The audit surfaced three related but distinct artifacts. The fix targets only the third:

- `docs/bootcamp_recap.md` — appended **incrementally on every module completion** by the `module-recap-append` hook and the Recap Append step in `module-completion.md`. This file is always created/updated per-module and is **not** the bug site. It must be preserved.
- `docs/bootcamp_recap.pdf` — graduation Step 0 (`graduation.md`) always *attempts* to render this from `docs/bootcamp_recap.md`, with a reconstruction fallback. Also **not** the bug site; preserved.
- `docs/completion_summary.md` (+ optional `docs/completion_summary.pdf`) — the dedicated **Completion Summary** artifact named by rule 16, built by `generate_completion_summary.py` from `config/session_log.jsonl`. This is the artifact that is currently **only** produced when the bootcamper answers "yes" to the offer. **This is the bug site.**

Throughout this document, "the completion-summary artifact" refers to the `docs/completion_summary.md` document produced by `generate_completion_summary.py`.

### Intended contract for the fix

During graduation, the completion-summary **document** (`docs/completion_summary.md`) SHALL be generated unconditionally, regardless of the bootcamper's yes/no answer. The binary yes/no choice is narrowed to governing **secondary presentation concerns only** — specifically whether the shareable **PDF** (`docs/completion_summary.pdf`) is rendered and whether the summary is surfaced/shared with the bootcamper. The summary document itself must always exist after graduation. This mirrors the existing "ALWAYS generate `GRADUATION_REPORT.md`" and "always attempt the recap PDF" patterns in `graduation.md`.

The fix is realized in the steering files (the contract that gates artifact creation) and is wired into the graduation workflow as an unconditional step. `generate_completion_summary.py` already supports unconditional markdown generation (markdown is always written by `main()`; PDF is gated behind the `--pdf` flag), so the script can run unconditionally without behavioral change to its internals.

## Bug Analysis

### Current Behavior (Defect)

The completion-summary artifact is created only when the bootcamper accepts the binary offer; declining (or any non-acceptance) skips creation entirely.

1.1 WHEN a stopping point is detected at graduation/track completion and the bootcamper declines the Completion Summary offer ("no") THEN the system proceeds to the next post-completion step WITHOUT generating any completion-summary file, leaving `docs/completion_summary.md` uncreated.

1.2 WHEN the bootcamper accepts the offer ("yes") THEN the system generates the completion-summary, but WHEN they decline THEN the rule-mandated artifact is omitted, making creation conditional on the bootcamper's choice rather than guaranteed.

1.3 WHEN graduation completes after the bootcamper declined the offer THEN no `docs/completion_summary.md` exists, even though graduation always produces `GRADUATION_REPORT.md` and always attempts `docs/bootcamp_recap.pdf` — the dedicated completion-summary is the only graduation artifact whose creation is opt-in.

1.4 WHEN the bootcamper declines THEN the binary choice suppresses BOTH the secondary concern (PDF rendering / sharing) AND the primary artifact (the summary document), conflating presentation control with artifact creation.

### Expected Behavior (Correct)

The completion-summary document is always generated during graduation; the yes/no choice governs only presentation and sharing.

2.1 WHEN a stopping point is detected at graduation/track completion THEN the system SHALL generate the completion-summary document `docs/completion_summary.md` regardless of the bootcamper's subsequent yes/no answer.

2.2 WHEN the bootcamper declines the offer ("no") THEN the system SHALL still create `docs/completion_summary.md`, and SHALL only skip the secondary presentation concerns (rendering the shareable PDF and/or surfacing/sharing the summary), then proceed to the next post-completion step.

2.3 WHEN the bootcamper accepts the offer ("yes") THEN the system SHALL create `docs/completion_summary.md` AND additionally render the shareable PDF (`docs/completion_summary.pdf`) and surface it to the bootcamper.

2.4 WHEN the completion-summary document is generated THEN it SHALL CONTINUE TO contain the module-by-module collection of questions posed, bootcamper responses, actions taken, and artifacts generated, as built from `config/session_log.jsonl` by `generate_completion_summary.py`.

2.5 WHEN completion-summary generation fails for any reason (missing/empty session log, file-system error) THEN the system SHALL handle it non-blockingly — log a warning and continue the post-completion/graduation flow — consistent with the existing non-blocking patterns for the recap PDF and graduation report.

2.6 WHERE the offer message and prompt are presented THEN they SHALL be reframed so the binary choice governs PDF rendering / sharing of the always-created summary, rather than gating whether any summary file is created.

### Unchanged Behavior (Regression Prevention)

Everything outside the "always create the artifact" change must be preserved, including stopping-point detection, offer ordering, the per-module recap, and the other post-completion steps.

3.1 WHEN evaluating stopping points THEN the system SHALL CONTINUE TO detect them by the existing rules (Module 7 completion, Module 11 completion, explicit stop request, track switch at boundary) and SHALL CONTINUE TO apply the existing false-positive guards (stop phrase in a longer substantive request; missing/unreadable progress file does not trigger detection).

3.2 WHEN a module is completed THEN the system SHALL CONTINUE TO append the per-module recap section to `docs/bootcamp_recap.md` via the Recap Append step / `module-recap-append` hook, unchanged, and SHALL CONTINUE TO preserve all prior bytes in that file.

3.3 WHEN graduation Step 0 runs THEN it SHALL CONTINUE TO attempt the recap PDF (`docs/bootcamp_recap.pdf`) with its recovery/validation/reconstruction fallbacks, and SHALL CONTINUE TO generate `production/GRADUATION_REPORT.md` and the rest of the graduation steps unchanged.

3.4 WHEN presenting post-completion offers at track completion THEN the system SHALL CONTINUE TO present them in the existing order (celebration → completion summary → export results / record export → analytics → certificate → graduation offer → feedback reminder), with the completion-summary offer in its existing position relative to the celebration message and export offer.

3.5 WHEN a mid-session explicit stop is detected (not track completion) THEN the system SHALL CONTINUE TO follow the mid-session ordering (acknowledge stop, then the completion-summary offer with no intervening prompts), and SHALL CONTINUE TO follow the track-completion sequence when both are detected simultaneously.

3.6 WHEN the journal entry and module completion certificate steps run THEN they SHALL CONTINUE TO execute in their fixed order with their existing non-blocking error handling, unchanged.

3.7 WHEN the offer is presented at multiple stopping points in a session THEN the repeat policy SHALL CONTINUE TO apply (the offer/summary opportunity occurs at every stopping point), and re-prompting for the same stopping point after a decline SHALL CONTINUE TO be avoided.

3.8 WHEN `generate_completion_summary.py` builds and renders the summary THEN it SHALL CONTINUE TO behave as covered by the existing unit, property, and integration tests — session-log parsing, secret filtering, append-only JSONL integrity, module-ascending section ordering, four subsections per module, metadata completeness, size truncation, the PDF fallback messages, and the separation of `docs/completion_summary.*` paths from `docs/bootcamp_recap.*` paths.

3.9 WHEN the session log is unavailable or empty THEN the script SHALL CONTINUE TO produce its existing fallback behavior (e.g., per-module "Session log was unavailable for this module." rendering and the PDF fallback messages) rather than crashing.

## Bug Condition Derivation

**Key Definitions:**

- **F** — the original (unfixed) post-completion/graduation workflow, where the completion-summary artifact is created only on an accepted ("yes") offer.
- **F'** — the fixed workflow, where the completion-summary document is always created during graduation and the yes/no answer governs only PDF rendering / sharing.
- **X** — a graduation/stopping-point situation, characterized by the bootcamper's offer answer, the availability of session-log data, and the stopping-point type.

### Bug Condition C(X)

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type GraduationSituation
  OUTPUT: boolean

  // The bug manifests at any stopping point where the bootcamper does NOT
  // accept the offer, because the mandated completion-summary artifact is
  // then skipped entirely.
  RETURN X.stoppingPointDetected
         AND X.offerAnswer <> "yes"
END FUNCTION
```

### Property — Fix Checking

For every stopping-point situation where the bootcamper does not accept, the fixed workflow must still create the completion-summary document; only PDF rendering / sharing may be skipped.

```pascal
// Property: Fix Checking — completion-summary always created at graduation
FOR ALL X WHERE isBugCondition(X) DO
  workflow ← F'(X)
  ASSERT createsFile(workflow, "docs/completion_summary.md")     // artifact always created
     AND summaryHasModuleByModuleContent(workflow)               // questions, answers, actions, artifacts
     AND (X.offerAnswer = "no" IMPLIES skipsOnly(workflow,       // decline suppresses ONLY secondary concerns
            {render_pdf, surface_or_share}))
     AND nonBlockingOnFailure(workflow)                          // failures warn-and-continue
END FOR
```

### Property — Preservation Checking

For every situation that is not a bug condition (the bootcamper accepts, or no stopping point is detected), the fixed workflow must behave identically to the original.

```pascal
// Property: Preservation Checking — accepted/non-stopping paths unchanged
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

### Counterexample (demonstrates the bug under F)

```pascal
// Track completion at Module 7: stopping point detected, bootcamper declines the offer.
X ← { stoppingPointDetected: true, offerAnswer: "no", sessionLogAvailable: true,
      stoppingPointType: "module_7_completion" }
// isBugCondition(X) = true
// F(X): "proceed to the next post-completion step without generating any summary file."
//       docs/completion_summary.md is never created  →  rule 16 violated.
// F'(X): docs/completion_summary.md IS created; only the PDF render / sharing is skipped.
```
