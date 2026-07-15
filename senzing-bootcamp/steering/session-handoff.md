---
inclusion: manual
description: "Session handoff synthesis: produce a fixed 8-section Handoff_Summary for a future Agent instance from the current bootcamp session, chat-only by default, without rewriting persisted state."
---

# Session Handoff

Instructions for producing a Handoff_Summary: a terse, fixed-structure end-of-session
artifact addressed to a **future Agent instance**, not a human stakeholder. Its purpose
is to let the user clear the conversation context (or hand the bootcamp to a teammate)
and resume in a fresh chat without losing continuity. The Handoff_Summary is delivered
in chat by default and is never written to a file unless the user explicitly asks.

This capability **coordinates with and never overrides** three existing mechanisms:
`session-resume.md` (reconstructs persisted state next session), `agent-context-management.md`
(owns the context-reset message and the continuation-phrase convention), and
`module-completion-artifacts.md` (sole writer of recap, certificate, and progress artifacts).
The handoff *reads and references* their outputs and *reuses* their conventions; it writes
none of them.

## Invocation & Offers

There are three entry points. Only the first produces a Handoff_Summary unconditionally;
the other two are one-line offers that respect the single-question protocol in
`conversation-protocol.md` (a single 👉 question, then 🛑 STOP — never a second question in
the same turn, never a self-answer).

### Trigger phrases (produce immediately)

When the user's message contains a trigger phrase or a near-equivalent request, produce the
Handoff_Summary immediately without asking first. Recognized phrases include:

- "session handoff"
- "handoff summary"
- "hand off"
- "wrap up session"
- "summarize before I clear"

Treat close paraphrases the same way (for example "give me a handoff", "let's wrap up and
hand off", "summarize the session so I can start fresh").

### Offer paths (offer first, do not force)

Offer to produce a Handoff_Summary — but do not produce one unprompted — in these cases:

- **Clear-context intent.** The user signals intent to clear, reset, or restart the
  conversation before any Handoff_Summary has been produced this session. Offer to produce
  one first, as a single 👉 question, then 🛑 STOP. If the user declines, proceed without a
  handoff and take no other action.
- **Context-reset message.** When the Agent emits the context-reset message defined in
  `agent-context-management.md` (triggered near the context budget limit or on degraded
  quality), append a one-line offer to produce a Handoff_Summary before the user opens the
  fresh chat. The offer reuses that file's continuation-phrase and current-module convention
  rather than inventing a new resume mechanism. (The wiring of this offer into the reset flow
  lives in `agent-context-management.md`.)

### Empty session

If the Current_Session contains no recorded work, decisions, or touched artifacts, still
produce the full Handoff_Summary with every one of the eight sections present, recording
"none" as the content of each section that has nothing to report. Never omit a section.

## Session-Scoped Synthesis

Producing the handoff is a recall-and-format task, not a discovery task. The Agent already
holds the full Current_Session in context.

- **In-session sources only.** Derive all content exclusively from the Current_Session
  conversation and the artifacts the Agent created or modified during this session.
- **No repository sweeps.** Do not run version-control history queries and do not perform
  repository-wide file searches to reconstruct state. Reading the specific persisted state
  files named below (for accuracy reconciliation) is allowed; open-ended scanning is not.
- **Whole conversation.** Base the summary on the entire Current_Session, not only the most
  recent turns. Decisions and open questions raised early in the session are as load-bearing
  as recent ones.

## State Gathering & Reconciliation

Gather every state item below. For each item, recall the in-session value from the
conversation first, then reconcile it — **read-only** — against the persisted file listed for
accuracy. Reading these files sharpens accuracy; the handoff modifies none of them.

Persisted files read for reconciliation (never written):

- `config/bootcamp_progress.json`
- `config/bootcamp_preferences.yaml`
- `config/mapping_state_*.json`
- `config/session_log.jsonl`
- `config/.question_pending`
- `docs/bootcamp_recap.md`

State items to collect:

- **Current_Module, Current_Step, completed modules** — reconcile against
  `config/bootcamp_progress.json` (`current_module`, `current_step`, `modules_completed`).
  `current_step` may be an integer or a sub-step string such as `"5.3"` or `"7a"`.
- **Active Track and active Language** — reconcile against `config/bootcamp_preferences.yaml`.
- **Data sources loaded and database type** — reconcile against `config/bootcamp_progress.json`.
- **Generated code artifacts produced this session** — from the conversation and the files
  touched this session.
- **Each active Mapping_Checkpoint** — reconcile against `config/mapping_state_*.json`.
- **MCP_Session connection status** — live state (connected or disconnected), re-established
  by calling `get_capabilities` against the Senzing MCP server.
- **Each Visualization_Service and Background_Process started this session** — live state, from
  the conversation, including the port of each Visualization_Service.
- **Pending_Question text**, where one exists — from the conversation, reconciled against
  `config/.question_pending`.
- **In-session decisions and unresolved questions that live in no file** — recalled from the
  conversation only. These are the items not recorded in `config/bootcamp_progress.json`,
  `config/bootcamp_preferences.yaml`, a mapping checkpoint, or `docs/bootcamp_recap.md`, and are
  the unique value the handoff adds over `session-resume.md`.

Reconciliation surfaces the persisted state that `session-resume.md` reconstructs **together
with** the in-session decisions and open questions that are stored in no file. If a persisted
file is missing or unparsable, record what was observed in-session for the affected item and use
"none" where nothing is known — never invent values, and never attempt repair (that is the
session-resume workflow's job).

## Output Template

Every Handoff_Summary uses the same fixed skeleton: a level-1 Title followed by the seven
level-2 sections below, always in this exact order. Emit all eight sections every time; a
section with nothing to report reads exactly "none" — never omit it and never leave it blank.
The "Pick up here" section carries a single most-likely next action, not a list of options.

```text
# Handoff: <one-line subject of the session>

## Where it started
<starting module/step, track, language, initial goal>

## Decisions locked + what shipped
<in-session decisions made; code/artifacts produced this session>

## Key files for next session
- <Driving_Artifact absolute path — first if one exists>
- <other absolute paths>

## Running state
- Database: <absolute SQLite path | PostgreSQL connection description>
- MCP: <connected | disconnected>
- Processes: <name @ port — stop with `<command>`> | none

## Verification — how to confirm things still work
- Re-establish MCP: call get_capabilities — expect a reachable Senzing MCP server and a capabilities list.
- Run: python3 senzing-bootcamp/scripts/baseline_status.py — expect the data-source coverage report.
- Confirm Module <N> artifacts exist: <absolute paths> — expect all present.

## Deferred + open questions
<pending question text; unresolved in-session questions> | none

## Pick up here
<single most-likely next action>
Resume phrase: "continue the bootcamp from module <N>"
```

The section headings are fixed strings — reproduce them verbatim, including the em-dash in
"Verification — how to confirm things still work". Do not rename, renumber, or reword them.

### Worked example

A filled-in Handoff_Summary for a mid-module session. Use it as the reference for tone,
absolute-path style, and the quoted resume phrase:

```text
# Handoff: Module 5 data mapping for CUSTOMERS_CRM (in progress)

## Where it started
Resumed Module 5 (Data Quality & Mapping), step 5.3. Track: Core (A). Language: Python.
Goal: finish the CUSTOMERS_CRM mapping and run a test load.

## Decisions locked + what shipped
- Mapped CRM full_name to Senzing NAME_FULL; split addr into ADDR_LINE1 / ADDR_CITY / ADDR_STATE.
- Decided to defer phone normalization to a follow-up rather than block the test load.
- Produced /home/bootcamper/senzing/mappers/customers_crm_mapper.py this session.

## Key files for next session
- /home/bootcamper/senzing/.kiro/specs/module-05/mapping-plan.md
- /home/bootcamper/senzing/mappers/customers_crm_mapper.py
- /home/bootcamper/senzing/config/mapping_state_customers_crm.json

## Running state
- Database: /home/bootcamper/senzing/var/senzing.db
- MCP: connected
- Processes: none

## Verification — how to confirm things still work
- Re-establish MCP: call get_capabilities — expect a reachable Senzing MCP server and a capabilities list.
- Run: python3 senzing-bootcamp/scripts/baseline_status.py — expect CUSTOMERS_CRM listed with coverage status.
- Confirm Module 5 artifacts exist: /home/bootcamper/senzing/mappers/customers_crm_mapper.py,
  /home/bootcamper/senzing/config/mapping_state_customers_crm.json — expect both present.

## Deferred + open questions
- Pending: should REFERENCE data sources use a separate DATA_SOURCE code? (from config/.question_pending)
- Open: confirm whether phone normalization is in scope for Module 5 or deferred to Module 6.

## Pick up here
Validate the CUSTOMERS_CRM mapping against the sample records, then run the Module 5 test load.
Resume phrase: "continue the bootcamp from module 5"
```

## Precision Rules

Apply these rules to every Handoff_Summary so a fresh Agent — possibly running from a different
working directory — can act without guesswork:

- **Absolute paths everywhere.** Express every file reference as an absolute path (leading `/`).
  Never use a relative path, a `~` shortcut, or a bare filename. This applies to "Key files for
  next session", the database entry in "Running state", and any completion-artifact reference.
- **Driving_Artifact first.** When a Driving_Artifact guided the session (the plan, spec, or
  module document that primarily drove the work), list it as the **first** entry in "Key files
  for next session", ahead of the other absolute paths.
- **Per-process port and stop command.** For each Visualization_Service or Background_Process in
  "Running state", record its port where applicable and the exact command that stops it — for
  example `viz-server @ 8080 — stop with kill <pid>`. When nothing is running, record "none".
- **Database.** In "Running state", record the database as an absolute SQLite file path (for
  example `/home/bootcamper/senzing/var/senzing.db`) or as a PostgreSQL connection description.
- **MCP status.** In "Running state", record the MCP_Session status as `connected` or
  `disconnected`.

## Verification Block

The "Verification — how to confirm things still work" section always carries the same three
checks, each command paired with its expected outcome. Adapt the module number and artifact
paths to the Current_Session, but keep all three checks and their order:

1. **Re-establish MCP.** Call `get_capabilities` — expect a reachable Senzing MCP server and a
   capabilities list.
2. **Baseline status.** Run `python3 senzing-bootcamp/scripts/baseline_status.py` — expect the
   data-source coverage report. This command is deliberately relative: it is the documented
   invocation from the power root, not a file reference, so it is exempt from the absolute-path
   rule.
3. **Artifacts exist.** Confirm the Current_Module artifacts exist by their absolute paths —
   expect all present.

Pairing each command with its expected outcome lets the next Agent tell a healthy environment
from a broken one at a glance.

## Pick Up Here & Continuation

The "Pick up here" section closes the handoff with exactly two things:

- **A single next action.** State the one most-likely next step for a fresh Agent — not a menu
  of options, and not a retrospective.
- **The quoted continuation phrase.** On its own line, emit the Continuation_Phrase naming the
  Current_Module, enclosed in quotation marks — for example, `Resume phrase: "continue the bootcamp from module 5"`.
  Read the module number from the `current_module` field of `config/bootcamp_progress.json`.

This reuses the continuation-phrase convention owned by `agent-context-management.md` rather than
inventing a new resume mechanism: the phrase must match the form the Context_Reset_Message uses,
so the user can paste the same phrase into a fresh chat. If `current_module` cannot be read, state
that the module is unknown in "Pick up here" rather than guessing a number, and still quote the
resume-phrase form.

Never let any of these forbidden temporal phrases appear in "Pick up here":

- "come back later"
- "come back tomorrow"
- "take a break"
- "try again in a while"
- "when you're ready"
- "try again later"
- "wait a moment"
- "give it some time"

The handoff points at the next action, never at a waiting period.

## Coordination Boundaries

The handoff is a reader and a pointer, never a writer of shared state. It surfaces the persisted
state that `session-resume.md` reconstructs next session **together with** the in-session decisions
and open questions that live in no file — that pairing is the handoff's unique contribution over
`session-resume.md`.

Never rewrite any of the following. The handoff reads them for accuracy and references them by path;
it modifies none of them:

- **Persisted bootcamp state** — `config/bootcamp_progress.json`, `config/bootcamp_preferences.yaml`,
  the `config/mapping_state_*.json` checkpoints, `config/session_log.jsonl`, and
  `config/.question_pending`. `session-resume.md` reconstructs this state at the start of the next
  session; the handoff only reads it.
- **Module-completion artifacts** — the recap (`docs/bootcamp_recap.md`), the certificate, and the
  progress artifacts under `docs/`. `module-completion-artifacts.md` is their sole writer. The handoff
  never regenerates them.
- **The context-reset message** — owned by `agent-context-management.md`. The handoff reuses that
  file's continuation-phrase and current-module convention (see "Pick Up Here & Continuation"); it
  does not redefine the reset message or invent a competing resume mechanism.

**Reference completion artifacts by absolute path.** When the module-completion workflow has already
written a recap, certificate, or progress artifact, cite it by its absolute path in "Key files for
next session" rather than reproducing or regenerating its content.

## Tone & Discipline

The Handoff_Summary is written for a future Agent instance, not a human stakeholder. Keep it terse
and concrete:

- **Engineering tone.** Plain, factual, and short. State what happened and what to do next; skip
  narrative framing and stakeholder-report phrasing.
- **No emojis, no celebration, no retrospective.** Do not add emoji, congratulatory language, or a
  recap of how the session went. The invocation offer may carry the conversation protocol's
  question/stop markers, but the summary body carries none.
- **One recommendation only.** Limit all forward-looking guidance to the single next action in "Pick
  up here". Do not present a menu of options or scatter suggestions across the other sections.
- **"none" over inference.** Record only state observed during the Current_Session. Where a section
  has nothing to report, write exactly "none" — never fill it with guessed, assumed, or inferred
  content.

## Output Destination

- **Chat by default.** Deliver the Handoff_Summary as chat output in the Current_Session. This is the
  only default behavior.
- **No silent file writes.** Unless the user explicitly asks to save it, write no Handoff_Summary
  file and leave every persisted state file and every steering file unmodified.
- **Save only on explicit request, to an explicit absolute path.** When the user asks to save the
  Handoff_Summary, write it to the user-specified absolute path and then report that path back. If no
  path is given, ask for an absolute one rather than choosing a location; if the given path is
  relative or unwritable, report that it must be absolute and writable and keep the chat-only output.
