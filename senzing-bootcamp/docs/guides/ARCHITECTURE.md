<!-- Source files: module-dependencies.yaml, steering-index.yaml, hook-categories.yaml -->
<!-- Created: 2026-04-18 -->

# Senzing Bootcamp Power Architecture

This document is the single entry point for understanding the senzing-bootcamp
Kiro Power architecture. It describes how the system's components — steering
files, hooks, scripts, the MCP server, configuration files, and modules —
relate to each other and work together to deliver a guided 11-module bootcamp
experience. The intended audience is contributors who modify or extend the
power and advanced bootcampers who want to understand the system they are using.

## Table of Contents

- [Component Overview](#component-overview)
- [Data Flow](#data-flow)
- [Module Lifecycle](#module-lifecycle)
- [Hook Architecture](#hook-architecture)
- [Configuration Relationships](#configuration-relationships)
- [MCP Integration](#mcp-integration)
- [Context Budget Management](#context-budget-management)

## Component Overview

The senzing-bootcamp power is composed of seven major components. Each has a
distinct responsibility and communicates with the others through configuration
files and agent context loading.

### Steering

| Attribute | Value |
|-----------|-------|
| Directory | `steering/` |
| Format | Markdown (`.md`) with YAML frontmatter |
| Index | `steering/steering-index.yaml` |

Steering files are the primary mechanism for driving agent behavior. Each file
contains instructions, rules, or workflows that the agent loads into its
context window on demand. The YAML frontmatter declares metadata such as
`inclusion` policy (always, on-demand, or module-triggered). The
`steering-index.yaml` file catalogs every steering file with its token count,
size category, and keyword associations.

### Hooks

| Attribute | Value |
|-----------|-------|
| Directory | `hooks/` |
| Format | JSON (`.kiro.hook` files) |
| Registry | `hooks/hook-categories.yaml` |

Hooks automate agent actions in response to IDE events. Each `.kiro.hook` file
defines a trigger condition (`when`) and an action (`then`). Hooks are
classified as either critical (installed during onboarding) or module-specific
(installed when the associated module starts). The `hook-categories.yaml` file
maps each hook to its category and module association.

### Scripts

| Attribute | Value |
|-----------|-------|
| Directory | `scripts/` |
| Format | Python (`.py`), stdlib only |
| Exception | `validate_dependencies.py` uses PyYAML |

Scripts provide CLI tooling for validation, measurement, and maintenance tasks.
They run in CI (via GitHub Actions) and locally during development. Key scripts
include `validate_power.py` (full power validation), `measure_steering.py`
(token budget checks), `validate_commonmark.py` (Markdown linting), and
`install_hooks.py` (hook installation during onboarding).

### Config

| Attribute | Value |
|-----------|-------|
| Directory | `config/` |
| Format | YAML (`.yaml`) for power assets |
| Runtime | JSON (`.json`) for mutable user state |

Configuration files store both static power definitions and dynamic user state.
Read-only power assets like `module-dependencies.yaml` define the module
prerequisite graph and gate conditions. Mutable user state files like
`bootcamp_progress.json` and `bootcamp_preferences.yaml` are created in the
user's working directory during sessions.

### MCP

| Attribute | Value |
|-----------|-------|
| Definition | `mcp.json` (project root) |
| Server | `https://mcp.senzing.com/mcp` |
| Protocol | Model Context Protocol over HTTPS |

The Senzing MCP server provides all Senzing-specific facts, code generation,
and tool assistance. The power enforces a strict rule: Senzing facts come
exclusively from MCP tools, never from model training data. The `mcp.json` file
configures the server connection and tool permissions.

### Modules

| Attribute | Value |
|-----------|-------|
| Steering | `steering/module-*.md` (per-module and per-phase files) |
| Docs | `docs/modules/MODULE_*.md` (reference documentation) |
| Config | `config/module-dependencies.yaml` (prerequisite graph) |

Modules are the 11 curriculum units that guide a bootcamper from first demo to
production deployment. Each module is defined by its steering files (which the
agent loads), its dependency gates (which control progression), and its
reference documentation. Large modules are split into phases with separate
steering files to reduce context pressure.

### Docs

| Attribute | Value |
|-----------|-------|
| Directory | `docs/` |
| Format | Markdown (`.md`) |
| Subdirs | `guides/`, `modules/`, `diagrams/`, `policies/`, `feedback/` |

The docs directory contains all human-readable documentation: reference guides,
module overviews, architecture diagrams, contribution policies, and feedback
templates. These files are not loaded into agent context — they serve
contributors and bootcampers who read them directly.

### Directory Layout and Component Relationships

The following diagram shows the top-level structure of `senzing-bootcamp/` and
how components interact during a bootcamp session.

```text
senzing-bootcamp/
├── steering/        Drives agent behavior
│   └── *.md           (YAML frontmatter + Markdown)
├── hooks/           Automates checks on IDE events
│   └── *.kiro.hook    (JSON trigger/action pairs)
├── scripts/         Provides tooling
│   └── *.py           (validation, measurement, CI)
├── config/          Stores state and gates
│   └── *.yaml         (module deps, artifacts)
├── mcp.json         Provides Senzing facts (remote)
├── docs/            Reference for humans
│   └── *.md           (guides, modules, policies)
└── POWER.md         Power entry point

         ┌─────────────────────────────┐
         │        Agent Context        │
         └──────┬──────┬──────┬────────┘
                │      │      │
    ┌───────────┘      │      └───────────┐
    ↓                  ↓                  ↓
┌────────┐      ┌──────────┐      ┌──────────┐
│steering│      │  hooks   │      │   MCP    │
│  files │      │  (IDE    │      │ (remote  │
│ (rules,│      │  events) │      │  facts)  │
│  flows)│      └────┬─────┘      └────┬─────┘
└───┬────┘           │                 │
    │                ↓                 ↓
    │         ┌──────────┐      ┌──────────┐
    └────────→│  config  │←─────│ scripts  │
              │  (state, │      │ (validate│
              │   gates) │      │  measure)│
              └──────────┘      └──────────┘
```

## Data Flow

A bootcamp session follows a deterministic path from startup to module
completion. The agent's first action at every session start is a single
decision point that routes the session into one of two flows: onboarding
(first time) or resume (returning user).

### Session-Start Decision Logic

When a session begins, the agent checks for the existence of
`config/bootcamp_progress.json` in the user's working directory:

- **File exists** → Load `steering/session-resume.md`. The bootcamper has
  prior progress to restore.
- **File does not exist** → Load `steering/onboarding-flow.md`. This is a
  fresh bootcamp start.

This check is the single branching point. All subsequent behavior follows
from which steering file is loaded.

### End-to-End Flow: Fresh Session (Onboarding)

1. **Setup preamble** — Agent announces administrative setup is starting.
2. **MCP health check** — Probe `search_docs` with a 10-second timeout.
   If the probe fails, block with troubleshooting steps until resolved.
3. **Directory creation** — Create `src/`, `data/`, `docs/` if missing.
4. **Hook installation** — Create critical hooks via `createHook`. Record
   installed hooks and timestamp in `config/bootcamp_preferences.yaml`
   under `hooks_installed`.
5. **Language selection** — Query MCP for supported languages on the
   detected platform. Persist choice to `config/bootcamp_preferences.yaml`.
6. **Prerequisite check** — Run `scripts/preflight.py`. Offer Scoop and
   runtime installation on Windows if needed.
7. **Welcome banner** — Display the bootcamp introduction and module
   overview.
8. **Track selection** — Present Core Bootcamp or Advanced Topics. Persist
   choice to `config/bootcamp_preferences.yaml`.
9. **First module load** — Load the steering file for the first module in
   the selected track. Create `config/bootcamp_progress.json` with initial
   state.

### End-to-End Flow: Returning Session (Resume)

1. **Read state files** — Load `config/bootcamp_progress.json`,
   `config/bootcamp_preferences.yaml`, `config/session_log.jsonl` (if
   exists), and any `config/mapping_state_*.json` checkpoints.
2. **Hook verification** — Check `hooks_installed` in preferences. If
   missing, re-create critical hooks.
3. **Language steering reload** — Load the language file matching the
   persisted `language` preference.
4. **Conversation style restore** — Apply `conversation_style` parameters
   from preferences (verbosity, tone, pacing, question framing).
5. **MCP health check** — Same probe as onboarding. If the probe fails,
   block with troubleshooting steps until resolved.
6. **What's New check** — Compare last session timestamp from
   `config/session_log.jsonl` against `CHANGELOG.md` entries.
7. **Welcome-back summary** — Display track, language, completed modules,
   current module and step position.
8. **Module resume** — Load the current module's steering file and skip to
   `current_step + 1`.

### Module Execution Loop

Once a module is loaded (whether from onboarding or resume), execution
follows a repeating cycle until the track is complete:

1. **Execute steps** — Work through numbered steps in the module steering
   file. After each step, update `current_step` in
   `config/bootcamp_progress.json`.
2. **Gate evaluation** — When all steps are done, check the gate condition
   from `config/module-dependencies.yaml` (e.g., gate `5→6` requires
   "Sources evaluated, mapped, programs tested, quality >70%").
3. **Progress update** — Move the completed module into the `completed`
   array in `config/bootcamp_progress.json`. Log the completion event to
   `config/session_log.jsonl`.
4. **Next module load** — Resolve the next module from the track sequence,
   verify prerequisites, and load its steering file.
5. **Repeat** until all modules in the track are complete.

### Configuration Files by Stage

| Stage | File | Operation |
|-------|------|-----------|
| Session start (decision) | `bootcamp_progress.json` | Read (existence check) |
| Onboarding: setup | `bootcamp_preferences.yaml` | Write (create) |
| Onboarding: language | `bootcamp_preferences.yaml` | Write (language) |
| Onboarding: track | `bootcamp_preferences.yaml` | Write (track) |
| Onboarding: first module | `bootcamp_progress.json` | Write (create) |
| Resume: state load | `bootcamp_progress.json` | Read |
| Resume: state load | `bootcamp_preferences.yaml` | Read |
| Resume: state load | `session_log.jsonl` | Read |
| Resume: state load | `data_sources.yaml` | Read (if exists) |
| Module load | `steering-index.yaml` | Read (file metadata) |
| Module load | `module-dependencies.yaml` | Read (prerequisites) |
| Module step execution | `bootcamp_progress.json` | Write (current_step) |
| Module gate passed | `bootcamp_progress.json` | Write (completed array) |
| Module gate passed | `module-dependencies.yaml` | Read (gate condition) |
| Module gate passed | `session_log.jsonl` | Append (completion event) |
| Module: data mapping | `data_sources.yaml` | Write (source config) |
| All stages | `session_log.jsonl` | Append (session events) |

### Session Lifecycle Diagram

```text
┌────────────────────────────────────────────────┐
│                SESSION START                    │
└───────────────────────┬────────────────────────┘
                        │
                        ↓
         ┌──────────────────────────────┐
         │ bootcamp_progress.json exists?│
         └──────┬───────────────┬───────┘
                │               │
           YES  │               │  NO
                ↓               ↓
     ┌────────────────┐  ┌────────────────┐
     │ session-resume │  │ onboarding-flow│
     │ .md            │  │ .md            │
     ├────────────────┤  ├────────────────┤
     │ • Read state   │  │ • Dir setup    │
     │ • Reload lang  │  │ • Hook install │
     │ • Restore style│  │ • Language pick│
     │ • MCP check    │  │ • Prerequisites│
     │ • Welcome back │  │ • Track select │
     └───────┬────────┘  └───────┬────────┘
             │                   │
             └─────────┬─────────┘
                       │
                       ↓
         ┌──────────────────────────────┐
         │         MODULE LOOP          │
         │                              │
         │  ┌────────────────────────┐  │
         │  │ Load module steering   │  │
         │  └───────────┬────────────┘  │
         │              ↓               │
         │  ┌────────────────────────┐  │
         │  │ Execute steps          │  │
         │  │ (checkpoint each)      │  │
         │  └───────────┬────────────┘  │
         │              ↓               │
         │  ┌────────────────────────┐  │
         │  │ Gate evaluation        │  │
         │  └───────────┬────────────┘  │
         │              ↓               │
         │  ┌────────────────────────┐  │
         │  │ Update progress        │  │
         │  └───────────┬────────────┘  │
         │              │               │
         │              ↓               │
         │      More modules?           │
         │        YES → loop back       │
         └──────────────┬───────────────┘
                        │ NO
                        ↓
         ┌──────────────────────────────┐
         │        TRACK COMPLETE        │
         └──────────────────────────────┘
```

## Module Lifecycle

Every module passes through a deterministic sequence of states from initial
load to completion. Understanding this lifecycle is essential for contributors
who add new modules or modify existing ones.

### Lifecycle States

A module transitions through six states in order:

1. **Prerequisite check** — The agent reads `config/module-dependencies.yaml`
   to verify that all required predecessor modules are in the `completed`
   array of `config/bootcamp_progress.json`. If a prerequisite is missing,
   the module cannot start.

2. **Steering file load** — The agent loads the module's steering file into
   context. For single-file modules (2, 4, 7), this is one file. For
   split modules (1, 3, 5, 6, 8, 9, 10, 11), only the current phase file is
   loaded based on the bootcamper's `current_step` position.

3. **Step execution** — The agent works through numbered steps defined in
   the steering file. Each step is a discrete unit of work (explanation,
   code generation, validation, or user interaction).

4. **Checkpointing** — After each numbered step completes, the agent writes
   the updated step position to `config/bootcamp_progress.json`. This
   enables mid-module resume if the session ends.

5. **Gate evaluation** — When all steps in the module are complete, the
   agent evaluates the gate condition from `config/module-dependencies.yaml`.
   The gate describes what must be true before the next module can begin
   (e.g., "Sources evaluated, mapped, programs tested, quality >70%").

6. **Completion** — The module is moved into the `completed` array in
   `config/bootcamp_progress.json`, a completion event is logged to
   `config/session_log.jsonl`, and the next module in the track is loaded.

### Split Modules and Phase-Level Loading

Seven of the eleven modules are split into phases to reduce context window
pressure. Instead of loading a single large steering file, the agent loads
only the phase file that covers the bootcamper's current step.

The `steering-index.yaml` file defines the phase structure for each split
module. Each phase entry specifies:

- **file** — The steering file to load for that phase
- **token_count** — Token budget consumed by the file
- **size_category** — Classification (small, medium, large)
- **step_range** — The `[first_step, last_step]` range covered by the phase

The split modules and their phases are:

| Module | Phases | Steps |
| ------ | ------ | ----- |
| 1 Business Problem | discovery (1–9), document-confirm (10–18) | 18 |
| 3 System Verification | verification (1–8), visualization (9–12) | 12 |
| 5 Data Quality | quality-assessment (1–7), data-mapping (8–20), test-load (21–26) | 26 |
| 6 Load Data | build-loading (1–3), load-first (4–10), multi-source (11–19), validation (20–27) | 27 |
| 8 Performance | requirements (1–3), benchmarking (4–7), optimization (8–13) | 13 |
| 9 Security | assessment (1–4), hardening (5–12) | 12 |
| 10 Monitoring | setup (1–5), operations (6–10) | 10 |
| 11 Deployment | packaging (1–12), deploy (13–15) | 15 |

When the bootcamper's `current_step` crosses a phase boundary, the agent
unloads the previous phase file and loads the next one. This keeps context
usage proportional to the active work rather than the total module size.

Single-file modules (2 SDK Setup, 4 Data Collection, 7 Query & Visualize)
load their entire steering file at once because they are small enough to
fit within budget without splitting.

### Module Dependency Gates

The `config/module-dependencies.yaml` file defines three controls for each
module that govern transitions:

**Prerequisite modules** (`requires` field) — A list of module numbers that
must be completed before this module can start. The agent checks the
`completed` array in `bootcamp_progress.json` against this list.

| Module | Prerequisites |
| ------ | ------------- |
| 1 Business Problem | (none) |
| 2 SDK Setup | (none) |
| 3 System Verification | 2 |
| 4 Data Collection | 1 |
| 5 Data Quality | 4 |
| 6 Load Data | 2, 5 |
| 7 Query & Visualize | 6 |
| 8 Performance | 7 |
| 9 Security | 8 |
| 10 Monitoring | 9 |
| 11 Deployment | 10 |

**Gate conditions** (`gates` section) — Text descriptions of what must be
achieved before the transition to the next module is allowed. The agent
evaluates these conditions against the work completed during the module:

| Transition | Gate Condition |
| ---------- | -------------- |
| 1 → 2 | Problem documented, sources identified, criteria defined |
| 2 → 3 | SDK installed, DB configured, test passes |
| 3 → 4 | System verification passed or explicitly skipped |
| 4 → 5 | Sources collected, files in data/raw/ |
| 5 → 6 | Sources evaluated, mapped, programs tested, quality >70% |
| 6 → 7 | Sources loaded, no critical errors |
| 7 → 8 | Queries answer business problem |
| 8 → 9 | Baselines captured, bottlenecks documented |
| 9 → 10 | Security checklist complete, no critical vulns |
| 10 → 11 | Monitoring configured, health checks passing |

**Skip conditions** (`skip_if` field) — An optional condition under which
the module can be bypassed entirely. When a skip condition is met, the
module is marked complete without executing any steps:

| Module | Skip Condition |
| ------ | -------------- |
| 2 SDK Setup | SDK already installed and configured |
| 3 System Verification | Already familiar with Senzing and system verified |
| 5 Data Quality | All sources Entity Specification-compliant |
| 6 Load Data | Data already loaded |
| 7 Query & Visualize | Already validated |
| 8 Performance | Not needed for POC |
| 9 Security | Internal-only with no sensitive data |
| 10 Monitoring | Not deploying to production |
| 11 Deployment | Not deploying to production |

Modules 1 (Business Problem) and 4 (Data Collection) have no skip
condition — they are always required.

### Step-Level Checkpointing

After each numbered step completes, the agent updates
`config/bootcamp_progress.json` to record progress. This provides
fine-grained resume capability — if a session ends mid-module, the
bootcamper resumes at the next unfinished step rather than restarting the
entire module.

The checkpoint update writes two fields:

- **`current_step`** — The number of the step just completed. On resume,
  the agent loads the module steering file and advances to
  `current_step + 1`.

- **`step_history`** — An array of records, one per completed step. Each
  record captures the step number, completion timestamp, and any artifacts
  produced (file paths, validation results). This history enables the
  welcome-back summary to show exactly where the bootcamper left off.

Example checkpoint state after completing step 14 of Module 5:

```json
{
  "current_module": 5,
  "current_step": 14,
  "completed": [1, 2, 3, 4],
  "step_history": [
    { "step": 1, "completed_at": "2025-07-15T10:30:00Z" },
    { "step": 2, "completed_at": "2025-07-15T10:45:00Z" },
    "..."
  ]
}
```

For split modules, the `current_step` value also determines which phase
file to load. In the example above, step 14 falls within Module 5's
phase2-data-mapping (steps 8–20), so the agent loads
`module-05-phase2-data-mapping.md` on resume.

For further details on the progress file structure, see
[PROGRESS_FILE_SCHEMA.md](PROGRESS_FILE_SCHEMA.md).

### Module Lifecycle State Machine

```text
┌──────────────────────────────────────────────────────────┐
│                    MODULE LIFECYCLE                       │
└──────────────────────────────────────────────────────────┘

┌───────────────────┐
│ PREREQUISITE      │  Read module-dependencies.yaml
│ CHECK             │  Verify requires[] in completed[]
└────────┬──────────┘
         │
         │ prerequisites met
         ↓
┌───────────────────┐
│ LOAD STEERING     │  Read steering-index.yaml
│ FILE              │  Load phase file for current_step
└────────┬──────────┘  (or full file if single-file module)
         │
         │ file loaded into context
         ↓
┌───────────────────┐
│ EXECUTE STEP      │← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
│                   │  Work through numbered step    │
└────────┬──────────┘                                │
         │                                           │
         │ step complete                             │
         ↓                                           │
┌───────────────────┐                                │
│ CHECKPOINT        │  Write current_step to         │
│                   │  bootcamp_progress.json        │
│                   │  Append to step_history        │
└────────┬──────────┘                                │
         │                                           │
         ↓                                           │
    More steps?  ─── YES ─── ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘
         │           (may cross phase boundary
         │ NO         → unload/load phase file)
         ↓
┌───────────────────┐
│ GATE EVALUATION   │  Check gate condition from
│                   │  module-dependencies.yaml
└────────┬──────────┘  (e.g., "quality >70%")
         │
         │ gate passed
         ↓
┌───────────────────┐
│ COMPLETION        │  Move module to completed[]
│                   │  Log to session_log.jsonl
└────────┬──────────┘  Load next module in track
         │
         ↓
   Next module (restart lifecycle)
```

## Hook Architecture

Hooks are the automation layer of the senzing-bootcamp power. Each hook is a
`.kiro.hook` JSON file in `hooks/` that pairs an IDE event trigger with an
agent action. When the IDE raises a matching event, the hook's condition is
evaluated and — only on failure — the agent produces output. This
fire-and-forget model keeps the bootcamp experience fluid: passing checks are
invisible, while problems surface immediately.

### How Hooks Work

A hook definition contains two top-level fields:

- **`when`** — The IDE event that activates the hook. Event types include
  `fileEdited` (a file matching a glob pattern was saved), `agentStop` (the
  agent finished a response), `preToolUse` (the agent is about to call a
  write tool), and `promptSubmit` (the bootcamper sent a message).
- **`then`** — The action the agent takes when the hook fires. The action
  type is `askAgent` with a prompt that instructs the agent how to evaluate
  the condition and what to do on pass or fail.

The hook prompt encodes the condition logic. The agent reads the prompt,
evaluates the condition against the current state (files, context, recent
output), and decides whether to produce output. This design keeps hooks
declarative — no scripting language, no external runtime.

### Hook Categories

The `hooks/hook-categories.yaml` file classifies every hook into one of two
categories that determine when it is installed.

#### Critical Hooks (5 hooks — installed during onboarding)

Critical hooks are created in Step 4 of the onboarding flow via `createHook`.
They remain active for the entire bootcamp session regardless of which module
is running. These hooks enforce cross-cutting concerns:

| Hook | Responsibility |
| ---- | -------------- |
| `ask-bootcamper` | Owns all closing questions at step boundaries |
| `review-bootcamper-input` | Routes feedback and status trigger phrases |
| `code-style-check` | Enforces language-appropriate coding standards |
| `commonmark-validation` | Checks Markdown files for CommonMark compliance |
| `enforce-file-path-policies` | Enforces feedback path and working-directory restrictions |

#### Module Hooks (created when the associated module starts)

Module hooks are installed only when the bootcamper enters the module that
needs them. This avoids cluttering the hook set with irrelevant checks. When
a module completes, its hooks remain installed but become inert (their
conditions no longer match the active context).

| Module | Hooks |
| ------ | ----- |
| 1 Business Problem | `validate-business-problem` |
| 2 SDK Setup | `verify-sdk-setup` |
| 3 System Verification | `verify-demo-results`, `enforce-visualization-offers` |
| 4 Data Collection | `validate-data-files` |
| 5 Data Quality | `analyze-after-mapping`, `data-quality-check`, `enforce-mapping-spec`, `enforce-visualization-offers` |
| 6 Load Data | `backup-before-load`, `run-tests-after-change`, `verify-generated-code` |
| 7 Query & Visualize | `enforce-visualization-offers` |
| 8 Performance | `validate-benchmark-results`, `enforce-visualization-offers` |
| 9 Security | `security-scan-on-save` |
| 10 Monitoring | `validate-alert-config` |
| 11 Deployment | `deployment-phase-gate` |
| Any module | `backup-project-on-request`, `error-recovery-context`, `git-commit-reminder`, `module-completion-celebration` |

The "any" category contains utility hooks that apply across all modules.
They are installed during onboarding alongside the critical hooks.
Note that `enforce-visualization-offers` is a single hook installed once but
activated in multiple modules (3, 5, 7, 8) based on the current-module check
in its prompt.

### The Hook Silence Rule

Hooks follow a strict silence-first protocol: **when a check passes, the
hook produces zero output**. No acknowledgment, no status message, no
explanation of what was checked. The agent's response is either empty or a
single period character (`.`), which the IDE discards.

This rule exists because hooks fire frequently — on every file save, every
agent stop, every write operation. If passing hooks produced output, the
bootcamper would be buried in noise. Silence on success means the
bootcamper only sees hook output when something needs attention.

The silence rule is enforced in the hook prompt itself. Each hook's `then`
prompt begins with instructions like:

> "If compliant, produce no output at all — zero tokens, zero characters."

or

> "DEFAULT OUTPUT: `.`"

The agent interprets these instructions and suppresses output when the
condition is satisfied.

### The `ask-bootcamper` Hook and Closing Questions

The `ask-bootcamper` hook has a unique role: it is the single hook
responsible for asking the bootcamper questions at step boundaries. It
fires on `agentStop` (after every agent response) and decides whether a
closing question is appropriate.

Before generating a question, `ask-bootcamper` checks three conditions:

1. No question is already pending (`config/.question_pending` does not exist)
2. The most recent assistant message does not already contain a `👉` marker
3. The most recent assistant message does not already end with a question

If all conditions pass and substantive work was accomplished, the hook
appends a brief recap and a contextual closing question (marked with `👉`).
If any condition fails or no real work was done, the hook stays silent.

This centralized ownership prevents multiple hooks from competing to ask
questions. Other hooks may surface warnings or suggestions, but only
`ask-bootcamper` poses direct questions to the bootcamper.

### Hook Trigger Flow

```text
┌──────────────────────────────────────────────────────┐
│                  HOOK TRIGGER FLOW                    │
└──────────────────────────────────────────────────────┘

┌────────────────┐
│   IDE EVENT    │  fileEdited, agentStop, preToolUse,
│                │  promptSubmit
└───────┬────────┘
        │
        ↓
┌────────────────┐
│ HOOK MATCHING  │  Does the event type match a hook's
│                │  "when" field? Does the file pattern
│                │  match (if applicable)?
└───────┬────────┘
        │
        │ match found
        ↓
┌────────────────┐
│ AGENT EVALUATES│  Agent reads the hook's "then" prompt
│ CONDITION      │  and checks the condition against
│                │  current state (files, context, output)
└───────┬────────┘
        │
        ├───────────────────────────────┐
        │                               │
        ↓                               ↓
┌────────────────┐              ┌────────────────┐
│ CONDITION      │              │ CONDITION      │
│ PASSES         │              │ FAILS          │
├────────────────┤              ├────────────────┤
│                │              │                │
│ Zero output    │              │ Agent produces │
│ (silent — no   │              │ output:        │
│  text, no      │              │ • Warning      │
│  acknowledgment│              │ • Suggestion   │
│  to bootcamper)│              │ • Question     │
│                │              │ • Fix action   │
└────────────────┘              └────────────────┘
```

For further details on hook installation and the full hook registry, see
[HOOKS_INSTALLATION_GUIDE.md](HOOKS_INSTALLATION_GUIDE.md).

## Configuration Relationships

The bootcamp relies on a set of configuration files that work together to drive
agent decisions. Some are static assets shipped with the power; others are
mutable state created and updated during a bootcamp session. Understanding which
file feeds into which decision is essential for contributors modifying the
system.

### File Classification

Configuration files fall into two categories based on mutability:

**Read-only power assets** — shipped with the power, never modified by the
agent:

| File | Location | Role |
|------|----------|------|
| `module-dependencies.yaml` | `config/` | Prerequisite graph, track definitions, gate/skip conditions |
| `steering-index.yaml` | `steering/` | File metadata, module-to-file mappings, keyword index |
| `hook-categories.yaml` | `hooks/` | Critical vs module hook classification |

**Mutable user state** — created or updated during bootcamp sessions:

| File | Location | Role |
|------|----------|------|
| `bootcamp_progress.json` | `config/` | Current module/step, completed array, step history |
| `bootcamp_preferences.yaml` | `config/` | Language, track, verbosity, style, hooks, pacing |
| `data_sources.yaml` | `config/` | Data source registry (quality, mapping, load status) |
| `session_log.jsonl` | `config/` | Session events log (append-only) |

Read-only assets define the rules. Mutable state records where the user is and
what they have chosen. The agent reads both categories but only writes to
mutable state files.

### How Configuration Files Relate

The four core configuration files form a dependency graph that drives every
major agent decision:

**`module-dependencies.yaml`** defines which modules exist, their
prerequisites, gate conditions, and skip conditions. The agent reads this file
to determine whether a module can start — it checks the `completed` array in
`bootcamp_progress.json` against the module's `requires[]` list.

**`steering-index.yaml`** maps modules to their steering files and phases. The
agent reads this to determine which file to load based on the `current_step`
field in `bootcamp_progress.json`. For split modules, it identifies the correct
phase file rather than loading the entire module.

**`hook-categories.yaml`** classifies hooks as critical (installed during
onboarding) or module-specific (installed when the associated module starts).
The agent reads this during onboarding to install the 7 critical hooks, and at
each module start to install that module's hooks. Installed hooks are recorded
in `bootcamp_preferences.yaml`.

**`bootcamp_progress.json`** is the central mutable state file. It is:

- Read at session start to determine resume vs onboarding
- Checked against `module-dependencies.yaml` for gate evaluation
- Used with `steering-index.yaml` to resolve the current steering file
- Updated after every numbered step (current_step, step_history)
- Updated at module completion (completed array)

### User Preferences

`bootcamp_preferences.yaml` stores user choices made during onboarding and
ongoing session interactions. These preferences influence agent behavior
throughout the bootcamp:

| Field | Description | Set During |
|-------|-------------|------------|
| `language` | Programming language (python, java, csharp, rust, typescript) | Onboarding |
| `track` | Selected track (quick_demo, core_bootcamp, advanced_topics) | Onboarding |
| `verbosity` | Output verbosity level | Onboarding or mid-session |
| `conversation_style` | Tone, pacing, question framing preferences | Onboarding or mid-session |
| `hooks_installed` | List of installed hooks with timestamps | Onboarding and module starts |
| `pacing_overrides` | Manual pacing adjustments (slow down / speed up) | Mid-session |

The agent reads `bootcamp_preferences.yaml` at session resume to restore
behavior settings. When a user says "slow down" or "speed up," the agent
updates `pacing_overrides`. When a new module starts and hooks are installed,
the agent appends to `hooks_installed`.

The `language` and `track` fields also influence which MCP tools are called
(language-specific code generation) and which modules are included or skipped
(track-based filtering in `module-dependencies.yaml`).

### Configuration Data Flow

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    READ-ONLY POWER ASSETS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ module-dependencies  │  │ steering-index   │  │ hook-        │  │
│  │ .yaml               │  │ .yaml            │  │ categories   │  │
│  │                      │  │                  │  │ .yaml        │  │
│  │ • Prerequisites      │  │ • File mappings  │  │              │  │
│  │ • Gate conditions    │  │ • Token counts   │  │ • Critical   │  │
│  │ • Track definitions  │  │ • Phase splits   │  │ • Module     │  │
│  │ • Skip conditions    │  │ • Keywords       │  │              │  │
│  └──────────┬───────────┘  └────────┬─────────┘  └──────┬───────┘  │
│             │                       │                    │           │
└─────────────┼───────────────────────┼────────────────────┼───────────┘
              │                       │                    │
              ↓                       ↓                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT DECISION LOGIC                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  "Can this module start?"  ←── module-dependencies + progress       │
│  "Which file to load?"     ←── steering-index + progress            │
│  "Which hooks to install?" ←── hook-categories + progress           │
│  "What language/track?"    ←── preferences                          │
│  "What verbosity/style?"   ←── preferences                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
              │                       │                    │
              ↓                       ↓                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      MUTABLE USER STATE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ bootcamp_progress    │  │ bootcamp_        │  │ session_log  │  │
│  │ .json               │  │ preferences.yaml │  │ .jsonl       │  │
│  │                      │  │                  │  │              │  │
│  │ • current_module     │  │ • language       │  │ • Events     │  │
│  │ • current_step       │  │ • track          │  │   (append)   │  │
│  │ • completed[]        │  │ • verbosity      │  │              │  │
│  │ • step_history       │  │ • hooks_installed│  │              │  │
│  └──────────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

The arrows flow downward: read-only assets define the rules, the agent applies
those rules using mutable state as input, and writes results back to mutable
state. The read-only assets are never modified — they represent the power
author's design decisions, while mutable state captures the individual user's
journey.

## MCP Integration

The Senzing MCP server is the authoritative source for all Senzing-specific
knowledge in the bootcamp. It provides facts about the Senzing SDK, generates
code scaffolds, guides data mapping workflows, and diagnoses errors. The power
enforces a strict boundary: local files handle bootcamp orchestration (modules,
hooks, progress), while the MCP server handles Senzing domain knowledge.

### The MCP-Only Rule

All Senzing facts come from MCP tools and never from model training data.
This rule exists because:

1. **Accuracy** — The MCP server reflects the current SDK version, current
   method signatures, and current best practices. Training data may be
   outdated or incorrect.
2. **Consistency** — Every bootcamper gets the same correct information
   regardless of which model version is running.
3. **Verifiability** — MCP responses can be traced to their source
   documentation. Training data cannot.

The rule is enforced by agent instructions that direct the agent to always
use MCP tools for Senzing-specific claims rather than relying on training
data.

**What counts as a "Senzing fact":**

- SDK method names, signatures, parameters, and flags
- Senzing Entity Specification attribute names and formats
- Error code meanings and resolutions
- Configuration values and their effects
- Performance characteristics and limits
- Best practices and anti-patterns

**What does NOT require MCP:**

- General programming concepts (loops, error handling, file I/O)
- Bootcamp orchestration (module flow, progress tracking, hooks)
- User preferences and session state
- File system operations and project structure

### MCP Tool Categories

The Senzing MCP server exposes 13 tools organized into five functional
categories:

#### Discovery

| Tool | Purpose |
| ---- | ------- |
| `get_capabilities` | Discover available tools and confirm server health |
| `search_docs` | Search indexed Senzing documentation by topic |

#### Data Mapping

| Tool | Purpose |
| ---- | ------- |
| `mapping_workflow` | Interactive 8-step data-to-Senzing-JSON mapping |
| `analyze_record` | Validate a mapped record against the Entity Spec |
| `get_sample_data` | Download sample datasets (Las Vegas, London, Moscow) |
| `download_resource` | Download entity spec, analyzer script, resources |

#### Code Generation

| Tool | Purpose |
| ---- | ------- |
| `generate_scaffold` | Generate SDK code (Python, Java, C#, Rust, TS) |
| `sdk_guide` | Platform-specific SDK install and config guidance |
| `find_examples` | Working code from 27 Senzing GitHub repositories |

#### Reference

| Tool | Purpose |
| ---- | ------- |
| `get_sdk_reference` | SDK method signatures, parameters, and flags |
| `reporting_guide` | Reporting, visualization, and dashboard guidance |

#### Diagnostics

| Tool | Purpose |
| ---- | ------- |
| `explain_error_code` | Diagnose Senzing error codes (456 codes covered) |
| `submit_feedback` | Report issues or suggestions (disabled by default) |

### MCP Requirement

The Senzing MCP server is required for the bootcamp to function. The health
check at session start (both onboarding and resume) is a hard gate — if MCP
is unreachable, the bootcamp blocks with troubleshooting steps until the
connection is fixed. There is no offline mode or fallback path.

### Local vs Remote Boundary

```text
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL POWER ASSETS                        │
│              (shipped with senzing-bootcamp/)                │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Steering   │  │    Hooks     │  │   Scripts    │     │
│  │              │  │              │  │              │     │
│  │ • Module     │  │ • Critical   │  │ • validate   │     │
│  │   workflows  │  │ • Module     │  │ • measure    │     │
│  │ • Agent rules│  │ • Utility    │  │ • install    │     │
│  │ • Language   │  │              │  │ • backup     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Config    │  │     Docs     │  │  Templates   │     │
│  │              │  │              │  │              │     │
│  │ • Module deps│  │ • Guides     │  │ • Checklists │     │
│  │ • Artifacts  │  │ • Policies   │  │ • Summaries  │     │
│  │ • Progress*  │  │ • Diagrams   │  │ • Lineage    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  * Progress/preferences are mutable user state but stored  │
│    locally in the project's config/ directory               │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTPS (mcp.senzing.com:443)
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                   REMOTE MCP SERVER                          │
│              (Senzing domain knowledge)                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Discovery   │  │ Data Mapping │  │   Code Gen   │     │
│  │              │  │              │  │              │     │
│  │ • Capabilities│ │ • Mapping    │  │ • Scaffold   │     │
│  │ • Doc search │  │   workflow   │  │ • SDK guide  │     │
│  │              │  │ • Analyze    │  │ • Examples   │     │
│  │              │  │ • Samples    │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  Reference   │  │ Diagnostics  │                        │
│  │              │  │              │                        │
│  │ • SDK ref    │  │ • Error codes│                        │
│  │ • Reporting  │  │ • Feedback   │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘

KEY BOUNDARY RULES:
• Senzing facts (methods, attributes, errors) → always from MCP
• Bootcamp orchestration (modules, hooks, progress) → always local
• Code generation → MCP (generate_scaffold, sdk_guide)
• Code execution → local (run previously generated programs)
• Data mapping → MCP (mapping_workflow, analyze_record)
• Data file management → local (copy, profile, organize)
```

## Context Budget Management

The agent manages a finite context window shared across all loaded steering
files, conversation history, and tool outputs. The `steering-index.yaml`
file provides per-file token counts that enable the agent to make informed
decisions about what to load and when to unload. This system prevents
context overflow while keeping relevant information accessible.

### How Token Tracking Works

Every steering file has two metadata fields in `steering-index.yaml`
under the `file_metadata` section:

- **`token_count`** — The approximate number of tokens the file consumes
  when loaded into context. Measured by `scripts/measure_steering.py`.
- **`size_category`** — A classification based on token count:
  - `small` — Under 500 tokens
  - `medium` — 500 to 2,500 tokens
  - `large` — Over 2,500 tokens

The `budget` section of `steering-index.yaml` defines the global
thresholds:

| Field | Value | Meaning |
| ----- | ----- | ------- |
| `total_tokens` | 119,024 | Sum of all steering file tokens |
| `reference_window` | 200,000 | Assumed context window size |
| `warn_threshold_pct` | 60 | Percentage triggering warnings |
| `critical_threshold_pct` | 80 | Percentage triggering auto-unload |
| `split_threshold_tokens` | 5,000 | Files above this should be split |

### Budget States

The context budget operates in three states based on the percentage of the
reference window currently consumed by loaded steering files:

#### Normal (below 60% — under 120,000 tokens loaded)

- The agent loads files freely as needed
- No restrictions on supplementary file loading
- Keyword-triggered files load on demand
- Multiple files can be loaded simultaneously

#### Warn (60%–80% — 120,000 to 160,000 tokens loaded)

- The agent identifies unload candidates and their token savings
- Only files directly relevant to the current module or user question
  are loaded
- Supplementary files are deferred until budget drops
- The agent presents an actionable message to the bootcamper:
  "Context budget at X%. I can free ~N tokens by unloading [file]
  (completed). Want me to proceed, or keep it loaded?"
- The agent waits for bootcamper response before acting

#### Critical (above 80% — over 160,000 tokens loaded)

- The agent automatically unloads all completed-module steering files
- No question asked — automatic action to prevent context overflow
- The agent reports what was freed: "Automatically unloaded [files] —
  freed ~N tokens. These can be reloaded on demand."
- If still critical after unloading completed modules, the agent loads
  only the current phase of split modules (not the full root file)

### Retention Priority

When deciding what to unload, the agent follows a strict 6-tier priority
order. Higher tiers are never unloaded before lower tiers:

| Tier | Content | Unload Policy |
| ---- | ------- | ------------- |
| 1 | `agent-instructions.md` | Never unload |
| 2 | Current module steering file | Never unload while active |
| 3 | Language file (`lang-*.md`) | Never unload |
| 4 | `conversation-protocol.md` | Never unload |
| 5 | `common-pitfalls.md` / troubleshooting | Unload only at critical |
| 6 | Completed module steering files | First to unload |

A file is eligible for unloading only when ALL of these conditions are
true:

1. It belongs to a completed module (not the current module)
2. It has not been referenced in the last 5 conversation turns
3. It is not in tiers 1–4 of the retention priority

### Split Modules and Context Pressure

Seven modules are split into phases specifically to reduce context
pressure. Instead of loading a single large file (which might exceed the
`split_threshold_tokens` of 5,000), the agent loads only the phase file
covering the bootcamper's current step.

Example: Module 6 (Load Data) has four phases totaling approximately
8,444 tokens. Rather than loading all four phases simultaneously, the
agent loads only the active phase:

| Phase | Token Cost | Steps |
| ----- | ---------- | ----- |
| phaseA-build-loading | 662 | 1–3 |
| phaseB-load-first-source | 1,194 | 4–10 |
| phaseC-multi-source | 1,428 | 11–19 |
| phaseD-validation | 5,160 | 20–27 |

At step 5, only `module-06-phaseB-load-first-source.md` (1,194 tokens)
is loaded — not the full 8,444 tokens. When the bootcamper crosses the
phase boundary to step 11, the agent unloads phaseB and loads phaseC.

This phase-based loading is the primary mechanism for keeping large
modules within budget. The `steering-index.yaml` `step_range` field for
each phase tells the agent exactly which phase to load for any given
`current_step` value.

### Budget State Transitions

```text
┌─────────────────────────────────────────────────────────────┐
│              CONTEXT BUDGET STATE MACHINE                    │
└─────────────────────────────────────────────────────────────┘

                    ┌───────────────────────┐
                    │       NORMAL          │
                    │    (below 60%)        │
                    │                       │
                    │ • Load files freely   │
                    │ • No restrictions     │
                    │ • Keywords trigger    │
                    │   on-demand loads     │
                    └───────────┬───────────┘
                                │
                                │ usage crosses 60%
                                ↓
                    ┌───────────────────────┐
                    │        WARN           │
                    │     (60%–80%)         │
                    │                       │
                    │ • Identify unload     │
                    │   candidates          │
                    │ • Load only relevant  │
                    │   files               │
                    │ • Ask bootcamper      │
                    │   before unloading    │
                    │ • Defer supplementary │
                    │   files               │
                    └───────────┬───────────┘
                                │
                                │ usage crosses 80%
                                ↓
                    ┌───────────────────────┐
                    │      CRITICAL         │
                    │    (above 80%)        │
                    │                       │
                    │ • Auto-unload all     │
                    │   completed modules   │
                    │ • Report freed tokens │
                    │ • Phase-only loading  │
                    │   for split modules   │
                    │ • No question asked   │
                    └───────────┬───────────┘
                                │
                                │ unloading frees
                                │ enough tokens
                                ↓
                    ┌───────────────────────┐
                    │   BACK TO NORMAL      │
                    │   or WARN             │
                    │                       │
                    │ Resume normal loading │
                    │ behavior for the new  │
                    │ budget state          │
                    └───────────────────────┘

OVERRIDE: If bootcamper says "keep everything loaded",
suppress automatic unloading for the current session.
Still show warnings but don't act.

RELOAD: Unloaded files can be reloaded on demand if the
bootcamper revisits a completed module or asks about
earlier content.
```

For the full steering index schema and file metadata, see
[STEERING_INDEX.md](STEERING_INDEX.md).
