---
inclusion: manual
description: "Authoritative Stop-trigger hook precedence, guard determinism, and capture-critical coverage for the bootcamp hook architecture"
---

# Hook Architecture

This document is the authoritative, human-readable record of how the bootcamp's hooks are ordered,
guarded, and kept reliably present. It covers the five `Stop`-trigger hooks and their intended
precedence, the question-pending silence rule, the single-winner precedence rule, the assumption
that the power cannot control IDE firing order, the build-time fragment-composition decision, and
the capture-critical coverage requirement across both install paths. (Module recap capture is no
longer a standalone `Stop` hook: the stop-hook-ux bugfix folded the former `module-recap-append`
hook into `ask-bootcamper` as its Phase 0.)

Under Kiro 1.0 the end-of-turn event is the `Stop` trigger (the legacy `agentStop` event renamed).
The machine-readable companion to this document is the `agentstop_order` mapping in
`senzing-bootcamp/hooks/hook-categories.yaml`. That mapping is the source of truth for the ordered
ids and their one-sentence rationales; the prose here records the same order plus the surrounding
semantics and design decisions.

## Stop-Trigger Hooks — Ordered Precedence List

Exactly five hooks fire on the `Stop` trigger. Their intended precedence, highest first, is:

1. `ask-bootcamper` — answer-processing, closing-question ownership, and module recap capture (Phase 0).
2. `module-completion-celebration` — celebration of a completed module.
3. `enforce-gate-on-stop` — mandatory-gate enforcement.
4. `enforce-visualization-offers` — visualization-offer enforcement.
5. `enforce-critical-artifacts` — graduation-artifact completion enforcement.

The intended precedence semantics are, in order: (1) answer-processing and closing-question
ownership belongs to `ask-bootcamper`, which also performs recap capture of the just-completed
module first in its Phase 0 (recording the outcome takes precedence over announcing it);
(2) celebration (`module-completion-celebration`) follows; (3) gate enforcement
(`enforce-gate-on-stop`) follows that; (4) visualization-offer enforcement
(`enforce-visualization-offers`) follows that; and (5) graduation-artifact enforcement
(`enforce-critical-artifacts`) is last.

This ordered list is stored machine-readably as the `agentstop_order` mapping in
`hook-categories.yaml` (the key name predates the `Stop` rename and holds the `Stop`-trigger
ordering), where each entry carries an integer `order` (contiguous `1..5`) and a `rationale` string.
Tests assert that the set of ids under `agentstop_order` equals exactly the set of hooks whose
`trigger` is `Stop` — no more and no fewer. When the precedence changes, edit the YAML mapping first
and keep this prose in step with it.

## Per-Hook Rationale

Each hook's position in the precedence list is justified as follows.

- `ask-bootcamper` (order 1) — It owns answer-processing, the end-of-turn closing question per
  `agent-instructions.md`, and module recap capture (its Phase 0 appends the recap of the
  just-completed module before any celebration). It must rank first so that a pending answer or
  closing question is never pre-empted by a lower-stakes hook, and so the outcome is recorded before
  the module completion is announced.
- `module-completion-celebration` (order 2) — A celebration is a positive, low-urgency message. It
  ranks below `ask-bootcamper` (whose Phase 0 recap should already be written) and must yield to any
  gate-violation output below it.
- `enforce-gate-on-stop` (order 3) — This is the mandatory-gate safety net for Module 3. A gate
  violation is a correctness concern, so it outranks the celebration: in the same turn, a
  gate-violation message wins over a celebration message.
- `enforce-visualization-offers` (order 4) — This is the lowest-stakes nudge. It offers missed
  visualization opportunities only when nothing higher in the list has fired.
- `enforce-critical-artifacts` (order 5) — This is the graduation-artifact completion safety net.
  Unlike the other four Stop hooks it is a **deterministic `command` hook**, not an `agent` hook: on
  every Stop it runs `ensure_graduation_artifacts.py --stop-hook`, which itself gates on the pending
  question and the track-end stopping point before regenerating any missing artifact. Because it
  emits **no agent output**, it never competes for the single-winner slot and never stacks a message
  onto the turn — it is listed last only nominally, so the `agentstop_order` set stays exactly equal
  to the Stop-trigger hook set. It still runs conceptually after `ask-bootcamper` (whose Phase 0
  recap is a reconstruct/verify source) and the celebration and gate hooks, but as a runtime-executed
  command it does not depend on IDE firing order or on the agent choosing to act.

## Closing-Question Ownership and Conflict Resolution

`ask-bootcamper` is the sole closing-question owner. All other `Stop`-trigger hooks defer
closing-question emission to `ask-bootcamper` and never emit their own closing question. If the
documented precedence order ever appears to conflict with the established rule that `ask-bootcamper`
owns closing questions, the conflict is resolved in favor of `ask-bootcamper` owning closing
questions. Closing-question ownership is the higher rule; the precedence list never overrides it.

## Question-Pending Silence Rule

While `config/.question_pending` exists (or the most recent assistant message contains a pending
👉 question awaiting a bootcamper response), every `Stop`-trigger hook emits zero output. No hook may
add a competing message, a celebration, a recap, a gate notice, or a visualization offer while a
question is pending — the turn must end cleanly so the bootcamper can answer. Each `agent`
`Stop`-trigger hook's prompt therefore begins with a guard clause to the effect of: if
`config/.question_pending` exists, produce no output at all and defer to `ask-bootcamper`. The
`enforce-critical-artifacts` `command` hook enforces the same guard in code: `ensure_graduation_artifacts.py --stop-hook`
does nothing and produces no output while `config/.question_pending` exists.

## Single-Winner Precedence Rule

When more than one `Stop`-trigger hook would each produce visible output in the same turn, exactly
one hook's output takes precedence, chosen by the ordered list above (lowest `order` number wins).
The others stay silent for that turn.

The concrete, required example: a gate-violation output from `enforce-gate-on-stop` takes precedence
over a celebration output from `module-completion-celebration` in the same turn. In other words,
`enforce-gate-on-stop` outranks `module-completion-celebration` whenever both would otherwise speak —
the gate violation is shown and the celebration is suppressed.

When no hook's guard condition is satisfied in a turn, the `Stop`-trigger hooks collectively produce
zero visible output.

## No-Stacking Rule

No `Stop`-trigger hook appends its output after another `Stop`-trigger hook's output in a way that
stacks two separate end-of-turn messages. The end of a turn carries at most one primary message. Hooks do
not concatenate; they defer. This keeps the conversation readable and avoids a wall of stacked
notices at every turn end.

## Assumption / Non-Goal: The Power Cannot Control IDE Firing Order

This feature does not modify the IDE hook-execution engine or the order in which the IDE dispatches
`Stop`-trigger hooks. The power cannot control IDE-level firing order, and it makes no attempt to.

Determinism of the *effective* end-of-turn behavior does not depend on the engine's dispatch order.
Instead it comes from two documented mechanisms working together:

- Per-hook guard conditions make each hook a silent no-op unless its specific state holds. Because
  the guards are mutually consistent, at most one hook emits a primary end-of-turn message for any
  given progress state, regardless of the order in which the IDE fired them.
- The documented precedence rule (the `agentstop_order` mapping plus this prose) resolves the rare
  case where more than one hook would otherwise emit, naming the single winner.

So the guarantee is: per-hook guards plus the documented precedence, not control over the IDE's
dispatch order.

## Build-Time Fragment Composition — Sibling-Script Decision

Shared hook-prompt fragments (the Module 3 gate logic and the ⛔ output strings duplicated across the
gate hooks) are authored once and composed into the self-contained `then.prompt` strings at build
time. The design decision recorded here is that fragment composition is implemented as a **sibling
script**, `compose_hook_prompts.py`, rather than being folded into `sync_hook_registry.py`.

The composer runs **before** `sync_hook_registry.py` (see the design document's
"Composer-before-sync ordering" section). The data flow is `compose_hook_prompts.py --write`
(fragments → hook JSON) followed by `sync_hook_registry.py --write` (hook JSON → mirror docs and
lockfile). Each script keeps a single responsibility and its own `--verify` mode, and CI runs the
composer's `--verify` first so any fragment drift is reported with a precise, localized message
before the registry-sync check runs. The CI-verifiable round-trip is required regardless of this
structural choice.

## Capture-Critical Hooks and Both-Paths Coverage

Two hooks are designated **capture-critical** because the completion summary and the journey recap
depend on them: `session-log-events` and `ask-bootcamper`. (`session-log-events` is a `PostToolUse`
hook, not a `Stop`-trigger hook, but it is capture-critical all the same. `ask-bootcamper` now owns
the recap capture too — its Phase 0 appends the module recap that the former `module-recap-append`
hook used to write.)

Capture-critical coverage is required on **both** install paths:

- The `createHook`-from-registry path that the agent runs during onboarding/session start.
- The `install_hooks.py` file-copy path the bootcamper may run manually.

A capture-critical hook missing from either path means a silently incomplete completion summary or
recap, so both paths must cover all three. If any capture-critical hook is absent from the
bootcamper's `.kiro/hooks` directory at session start, the session-start check warns which
capture-critical hooks are missing and how to install them.
