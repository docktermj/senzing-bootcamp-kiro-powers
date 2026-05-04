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

Load per-module steering file when user starts that module (1→`module-01-business-problem.md` through 11→`module-11-deployment.md`). After Module 1: `complexity-estimator.md`. At 7→8 gate: `cloud-provider-setup.md`. At track end: `lessons-learned.md`. On errors: `common-pitfalls.md`.

- Split modules (1, 5, 6, 11): check `steering-index.yaml` for `phases` map. Load `phase-loading-guide.md` for detailed loading rules.

**At every module start:** Read `config/bootcamp_progress.json` first (this triggers `module-transitions.md` loading), then display the module start banner, journey map, and before/after framing BEFORE doing any module-specific work. Never skip these — they orient the user. Module 11 platform files: load `deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, or `deployment-kubernetes.md` based on deployment target.

**Multi-language projects:** If the bootcamper uses different languages for different components (e.g., Python for data transformation, TypeScript for a frontend), load the language steering file for whichever language is currently being edited. Don't force a single language across all components.

## State & Progress

- `mapping_workflow`: pass exact `state`, never modify. Write a checkpoint to `config/mapping_state_[datasource].json` after **each** mapping step, not only at workflow completion. When the full mapping workflow completes for a data source, delete the corresponding checkpoint file.
- Progress: `config/bootcamp_progress.json`. Preferences: `config/bootcamp_preferences.yaml`. Corrupted? Run `python3 senzing-bootcamp/scripts/validate_module.py`.
- Step-level checkpointing: after each numbered step, update `config/bootcamp_progress.json` — set `current_step` to the step number or sub-step identifier, set `step_history["<module_number>"]` to `{ "last_completed_step": <step>, "updated_at": "<ISO 8601>" }`. `current_step` accepts integer values for whole steps (e.g., `5`) and string sub-step identifiers in dotted (`"5.3"`) or lettered (`"7a"`) notation. On module completion, set `current_step` to `null`.
- Sub-step checkpointing: after completing each sub-step within a multi-part step, write a sub-step checkpoint using the sub-step identifier format defined in the module steering file (dotted or lettered notation).
- Recovery from mistakes: load `recovery-from-mistakes.md` when a bootcamper needs to undo or redo a step.

### Sub-Step Convention

When a steering file step contains multiple independent 👉 questions, split it into lettered sub-steps so each sub-step holds at most one question. Follow these rules:

- **Naming**: sub-steps use `{step_number}{letter}` format — `7a`, `7b`, `7c`, etc. Letters start at `a` and increment alphabetically within the parent step.
- **One question per sub-step**: each sub-step contains at most one 👉 question and one 🛑 STOP instruction.
- **Checkpoint per sub-step**: each sub-step has its own checkpoint instruction referencing its identifier (e.g., "Write step 7a to `config/bootcamp_progress.json`"). The parent step does not get a checkpoint when all content is distributed into sub-steps.
- **No-question steps stay whole**: steps with zero questions remain as single numbered steps — do not split them into sub-steps.
- **Mutually exclusive conditionals may share a sub-step**: when conditional questions are mutually exclusive (only one fires based on runtime state), they stay in a single sub-step with the conditional logic preserved. Only independent questions that could fire sequentially get their own sub-steps.

## Communication

- One question at a time, wait for response. Prefix input-required questions with "👉" in ALL modules.
- Never fabricate user input. Do not simulate user responses or assume choices. STOP and wait at 👉 questions and ⛔ gates. This applies to agentStop hooks — zero output when a 👉 question is pending.
- Closing-question ownership: never end your turn with a closing question — the `ask-bootcamper` hook owns those.
- Goldilocks check: after Modules 3, 6, 9 ask if detail level is right. Store as `detail_level` in preferences. First-term explanations: define Senzing terms inline on first use via `docs/guides/GLOSSARY.md`.
- Before each step: what and why. During: status updates (never bare "Working..."). After: what changed, files with paths. Offer to visualize data results as a web page — save to `docs/` or `data/temp/`.
- At module completion: summary, all files, why it matters for next module. Follow `module-transitions.md` rules. Load `module-completion.md` for journal and track-completion.
- Feedback trigger phrases: the capture-feedback hook handles this automatically — do not manually load feedback-workflow.md.

### Question Stop Protocol

Treat every 👉 question and ⛔ gate as an end-of-turn boundary. Your response **MUST** end after the question text. Produce no further tokens.

**End your response immediately** after any 👉 question or ⛔ mandatory gate. Do not generate any content beyond the question itself.

**Prohibited behaviors after a question or gate:**

- Do not answer the question.
- Do not assume a response.
- Do not say "I'll go with X."
- Do not proceed to the next step.
- Do not write checkpoints for the current step.

## Hooks

Create hooks using the `createHook` tool with definitions from the Hook Registry in `onboarding-flow.md`. Critical hooks are created during onboarding. Module hooks are created when the relevant module starts — check the Hook Registry for module associations and create any missing hooks for the current module before beginning module work.

The `capture-feedback` hook is critical — it guarantees feedback is captured when bootcampers use trigger phrases. Verify it is installed.

On session resume: check `config/bootcamp_preferences.yaml` for `hooks_installed`. If present and populated, skip hook creation. If absent, create Critical Hooks from the Hook Registry.

**🔇 Hook silence rule:** When a hook check passes with no action needed, produce absolutely no output — zero tokens, zero characters. Do not acknowledge the check, do not explain your reasoning, do not print any status message, do not narrate your evaluation, do not explain why no action is needed. Your response must be completely empty. Only produce output when the hook identifies a problem requiring corrective action. This applies to ALL hooks — preToolUse, agentStop, fileEdited, fileCreated, and any other hook type.

## Context Budget

Before loading any steering file, check `steering-index.yaml` `file_metadata` for `token_count` and `size_category`. Track cumulative tokens throughout the session. Prefer `small`/`medium` files over `large`.

Phase-level token costs for split modules: use the phase-level `token_count` from the `phases` map instead of the monolithic file count. Total cost = root file tokens + current phase sub-file tokens.

- **Warn (120k tokens):** Load only files relevant to current module/question. Defer supplementary files.
- **Critical (160k tokens):** Unload non-essential files before loading new ones.
- **Retention priority:** `agent-instructions.md` > current module > language file > troubleshooting > everything else.

When loading a `large` file, announce the token cost to the user.
