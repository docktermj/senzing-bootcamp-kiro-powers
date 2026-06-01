---
inclusion: manual
description: "Authoritative agentStop hook precedence, guard determinism, and capture-critical coverage for the bootcamp hook architecture"
---

# Hook Architecture

This document is the authoritative, human-readable record of how the bootcamp's hooks are ordered,
guarded, and kept reliably present. It covers the five `agentStop` hooks and their intended
precedence, the question-pending silence rule, the single-winner precedence rule, the assumption
that the power cannot control IDE firing order, the build-time fragment-composition decision, and
the capture-critical coverage requirement across both install paths.

The machine-readable companion to this document is the `agentstop_order` mapping in
`senzing-bootcamp/hooks/hook-categories.yaml`. That mapping is the source of truth for the ordered
ids and their one-sentence rationales; the prose here records the same order plus the surrounding
semantics and design decisions.

## agentStop Hooks — Ordered Precedence List

Exactly five hooks fire on `agentStop`. Their intended precedence, highest first, is:

1. `ask-bootcamper` — answer-processing and closing-question ownership.
2. `module-recap-append` — capture of the just-completed module.
3. `module-completion-celebration` — celebration of a completed module.
4. `enforce-gate-on-stop` — mandatory-gate enforcement.
5. `enforce-visualization-offers` — visualization-offer enforcement.

The intended precedence semantics are, in order: (1) answer-processing and closing-question
ownership belongs to `ask-bootcamper`; (2) capture (`module-recap-append`) runs next; (3) celebration
(`module-completion-celebration`) follows; (4) gate enforcement (`enforce-gate-on-stop`) follows
that; and (5) visualization-offer enforcement (`enforce-visualization-offers`) is last.

This ordered list is stored machine-readably as the `agentstop_order` mapping in
`hook-categories.yaml`, where each entry carries an integer `order` (contiguous `1..5`) and a
`rationale` string. Tests assert that the set of ids under `agentstop_order` equals exactly the set
of hooks whose `when.type` is `agentStop` — no more and no fewer. When the precedence changes, edit
the YAML mapping first and keep this prose in step with it.

## Per-Hook Rationale

Each hook's position in the precedence list is justified as follows.

- `ask-bootcamper` (order 1) — It owns answer-processing and the end-of-turn closing question per
  `agent-instructions.md`. It must rank first so that a pending answer or closing question is never
  pre-empted by a lower-stakes hook.
- `module-recap-append` (order 2) — Capture must run before celebration so that the appended recap
  reflects the module that was just completed. Recording the outcome takes precedence over announcing
  it.
- `module-completion-celebration` (order 3) — A celebration is a positive, low-urgency message. It
  ranks below capture (the recap should already be written) and must yield to any gate-violation
  output below it.
- `enforce-gate-on-stop` (order 4) — This is the mandatory-gate safety net for Module 3. A gate
  violation is a correctness concern, so it outranks the celebration: in the same turn, a
  gate-violation message wins over a celebration message.
- `enforce-visualization-offers` (order 5) — This is the lowest-stakes nudge. It offers missed
  visualization opportunities only when nothing higher in the list has fired, so it sits last.

## Closing-Question Ownership and Conflict Resolution

`ask-bootcamper` is the sole closing-question owner. All other `agentStop` hooks defer
closing-question emission to `ask-bootcamper` and never emit their own closing question. If the
documented precedence order ever appears to conflict with the established rule that `ask-bootcamper`
owns closing questions, the conflict is resolved in favor of `ask-bootcamper` owning closing
questions. Closing-question ownership is the higher rule; the precedence list never overrides it.

## Question-Pending Silence Rule

While `config/.question_pending` exists (or the most recent assistant message contains a pending
👉 question awaiting a bootcamper response), every `agentStop` hook emits zero output. No hook may
add a competing message, a celebration, a recap, a gate notice, or a visualization offer while a
question is pending — the turn must end cleanly so the bootcamper can answer. Each `agentStop` hook's
prompt therefore begins with a guard clause to the effect of: if `config/.question_pending` exists,
produce no output at all and defer to `ask-bootcamper`.

## Single-Winner Precedence Rule

When more than one `agentStop` hook would each produce visible output in the same turn, exactly one
hook's output takes precedence, chosen by the ordered list above (lowest `order` number wins). The
others stay silent for that turn.

The concrete, required example: a gate-violation output from `enforce-gate-on-stop` takes precedence
over a celebration output from `module-completion-celebration` in the same turn. In other words,
`enforce-gate-on-stop` outranks `module-completion-celebration` whenever both would otherwise speak —
the gate violation is shown and the celebration is suppressed.

When no hook's guard condition is satisfied in a turn, the `agentStop` hooks collectively produce
zero visible output.

## No-Stacking Rule

No `agentStop` hook appends its output after another `agentStop` hook's output in a way that stacks
two separate end-of-turn messages. The end of a turn carries at most one primary message. Hooks do
not concatenate; they defer. This keeps the conversation readable and avoids a wall of stacked
notices at every turn end.

## Assumption / Non-Goal: The Power Cannot Control IDE Firing Order

This feature does not modify the IDE hook-execution engine or the order in which the IDE dispatches
`agentStop` hooks. The power cannot control IDE-level firing order, and it makes no attempt to.

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

Three hooks are designated **capture-critical** because the completion summary and the journey recap
depend on them: `session-log-events`, `module-recap-append`, and `ask-bootcamper`. (`session-log-events`
is a `postToolUse` hook, not an `agentStop` hook, but it is capture-critical all the same.)

Capture-critical coverage is required on **both** install paths:

- The `createHook`-from-registry path that the agent runs during onboarding/session start.
- The `install_hooks.py` file-copy path the bootcamper may run manually.

A capture-critical hook missing from either path means a silently incomplete completion summary or
recap, so both paths must cover all three. If any capture-critical hook is absent from the
bootcamper's `.kiro/hooks` directory at session start, the session-start check warns which
capture-critical hooks are missing and how to install them.
