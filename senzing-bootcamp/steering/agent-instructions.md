---
inclusion: always
---

# Agent Core Rules

On session start: check `config/bootcamp_progress.json`. If exists, load `session-resume.md`. If not, load `onboarding-flow.md`.

## File Placement

| Content       | Location   | Content       | Location     |
| ------------- | ---------- | ------------- | ------------ |
| Source code   | `src/`     | SQLite DB     | `database/`  |
| Scripts       | `scripts/` | Config        | `config/`    |
| Docs          | `docs/`    | Temp files    | `data/temp/` |
| Data          | `data/`    | Markdown docs | `docs/`      |

🚨 ALL files within working directory only. Never `/tmp`, `%TEMP%`, `~/Downloads`. Override MCP-generated paths (`/tmp/`, `ExampleEnvironment`) to project-relative equivalents. Never modify global shell config.

If about to write a `.md` file to `scripts/`, redirect to `docs/` instead.

## MCP Rules

- All Senzing facts from MCP tools — never training data. Call `get_capabilities` first each session.
- Attribute names → `mapping_workflow` | SDK code → `generate_scaffold`/`sdk_guide` | Signatures → `get_sdk_reference` | Errors → `explain_error_code` | Docs → `search_docs` | Examples → `find_examples`
- Uncertain which tool? Load `mcp-tool-decision-tree.md` for the full decision tree with anti-patterns and call examples.
- Never hand-code Senzing JSON mappings or SDK method names
- Third-party software: consult Senzing MCP (`search_docs`) before recommending tools in a Senzing integration context.
- Production-scale code only. Reject `exportJSONEntityReport()`/`export_report` — use per-entity queries.
- Reuse MCP responses within a module; re-query across module boundaries. No answer? Say so, suggest <https://docs.senzing.com> / <support@senzing.com> — never fabricate.
- MCP skepticism: flag data mart tables (`sz_dm_report`), beta features, or non-core SDK references

## MCP Failure

Retry once. If still failing, load `mcp-offline-fallback.md` for what's blocked vs. what can continue. Never fabricate.

## Module Steering

Load per-module steering file when user starts that module (1→`module-01-business-problem.md` through 11→`module-11-deployment.md`). After Module 1: `complexity-estimator.md`. At 7→8 gate: `cloud-provider-setup.md`. At track end: `lessons-learned.md`.

- Split modules (1, 5, 6, 8, 9, 10, 11): check `steering-index.yaml` for `phases` map. Load `phase-loading-guide.md` for detailed loading rules.

**At every module start:** Read `config/bootcamp_progress.json` first, then display the module start banner, journey map, and before/after framing (per `module-transitions.md`, which is always loaded) BEFORE doing any module-specific work. Never skip these — they orient the user. Module 11 platform files: load `deployment-aws.md`, `deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, or `deployment-kubernetes.md` based on deployment target.

**Artifact readiness check (Modules 4-11):** Before displaying the module banner, read `config/module-artifacts.yaml` and check that all `requires_from` artifacts for the current module exist on disk. If all present, proceed silently. If any are missing, report which files are missing and from which module, then offer: (a) go back to complete the prerequisite, (b) skip the check and proceed anyway, (c) run rollback. The check is advisory — the bootcamper can always skip.

**Multi-language projects:** Load the language steering file for whichever language is currently being edited. Don't force a single language across all components.

## State & Progress

- `mapping_workflow`: pass exact `state`, never modify. Checkpoint to `config/mapping_state_[datasource].json` after **each** step. Delete checkpoint when workflow completes for a source.
- Progress: `config/bootcamp_progress.json`. Preferences: `config/bootcamp_preferences.yaml`. Corrupted? Run `python3 senzing-bootcamp/scripts/validate_module.py`.
- Conversation style persistence: after onboarding completes and the first module interaction establishes a baseline style, write a `conversation_style` profile to `config/bootcamp_preferences.yaml`. Schema — `verbosity_preset` (string: concise | standard | detailed | custom), `question_framing` (string: minimal | moderate | full), `tone` (string: concise | conversational | detailed), `pacing` (string: one_concept_per_turn | grouped_concepts).
- Step-level checkpointing: after each numbered step or sub-step, update `config/bootcamp_progress.json` — set `current_step` (integer for whole steps, string like `"5.3"` or `"7a"` for sub-steps), set `step_history["<module_number>"]` to `{ "last_completed_step": <step>, "updated_at": "<ISO 8601>" }`. On module completion, set `current_step` to `null`.
- Recovery from mistakes: load `recovery-from-mistakes.md` when a bootcamper needs to undo or redo a step.
- Skip steps: `skip-step-protocol.md` handles "I'm stuck" / "skip this" requests with consequence tracking. Load it via `#skip-step-protocol` or when keyword routing triggers.

## Communication

- One question at a time, wait for response. Prefix input-required questions with "👉" in ALL modules.
  - Never combine questions with conjunctions (and, or, also, but first) — each is a separate turn.
  - A question without the 👉 prefix is a formatting violation.
  - These rules apply in ALL contexts — onboarding, feedback workflow, module steps, and session resume. See conversation-protocol.md for the full rule set.
- Never fabricate user input. Do not simulate user responses or assume choices. STOP and wait at 👉 questions and ⛔ gates. This applies to agentStop hooks — zero output when a 👉 question is pending.
- Goldilocks check: after Modules 3, 6, 9 ask if detail level is right. Store as `detail_level` in preferences. First-term explanations: define Senzing terms inline on first use via `docs/guides/GLOSSARY.md`.
- Before each step: what and why. During: status updates. After: what changed, files with paths. Offer to visualize data results as a web page.
- At module completion: summary, all files, why it matters for next module. Follow `module-transitions.md` rules. Load `module-completion.md`.
- Feedback trigger phrases: the `review-bootcamper-input` hook handles this automatically — do not manually load feedback-workflow.md.
- Turn-taking, closing question ownership, and question protocols: see `conversation-protocol.md` (auto-loaded during active modules). Closing-question ownership: the `ask-bootcamper` hook is the primary owner; agent-instructions provides the inline stop protocol as reinforcement.

### Question Stop Protocol

Every 👉 question and ⛔ gate is an end-of-turn boundary. End your response immediately after the question — do not answer, do not assume a response, do not proceed to the next step.

## Hooks

Create hooks via `createHook` with definitions from the Hook Registry (`#[[file:]]` in `onboarding-flow.md`). Critical hooks during onboarding; module hooks when the relevant module starts. On session resume: check `config/bootcamp_preferences.yaml` for `hooks_installed` — if present, skip creation; if absent, create Critical Hooks.

**🔇 Hook silence rule:** When a hook check passes with no action needed, produce zero output — no acknowledgment, no reasoning, no status. Only produce output when the hook identifies a problem. Applies to ALL hook types. The `ask-bootcamper` hook owns all closing questions — never end your turn with a closing question yourself; the hook handles it.

## Context Budget

Check `steering-index.yaml` `file_metadata` for `token_count` and `size_category` before loading. For split modules, use phase-level `token_count` from the `phases` map. Track cumulative tokens.

- **Warn (60% of context budget):** Load only files relevant to current module/question.
- **Critical (80% of context budget):** Unload non-essential files first.
- **Retention priority:** `agent-instructions.md` > current module > language file > troubleshooting > everything else.

When loading a `large` file, announce the token cost. See `agent-context-management.md` for detailed unloading rules and adaptive pacing.
