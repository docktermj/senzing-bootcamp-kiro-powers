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

- `mapping_workflow`: pass exact `state`, never modify. Save checkpoints to `config/mapping_state_[datasource].json`.
- Progress: `config/bootcamp_progress.json`. Preferences: `config/bootcamp_preferences.yaml`. Corrupted? Run `python3 senzing-bootcamp/scripts/validate_module.py`.
- Step-level checkpointing: after each numbered step, update `config/bootcamp_progress.json` — set `current_step` to the step number, set `step_history["<module_number>"]` to `{ "last_completed_step": <step>, "updated_at": "<ISO 8601>" }`. On module completion, set `current_step` to `null`.
- Recovery from mistakes: load `recovery-from-mistakes.md` when a bootcamper needs to undo or redo a step.

## Communication

- One question at a time, wait for response. Prefix input-required questions with "👉" in ALL modules.
- Never fabricate user input. Do not simulate user responses or assume choices. STOP and wait at 👉 questions and ⛔ gates. This applies to agentStop hooks — zero output when a 👉 question is pending.
- Closing-question ownership: never end your turn with a closing question — the `ask-bootcamper` hook owns those.
- Goldilocks check: after Modules 3, 6, 9 ask if detail level is right. Store as `detail_level` in preferences. First-term explanations: define Senzing terms inline on first use via `docs/guides/GLOSSARY.md`.
- Before each step: what and why. During: status updates (never bare "Working..."). After: what changed, files with paths. Offer to visualize data results as a web page — save to `docs/` or `data/temp/`.
- At module completion: summary, all files, why it matters for next module. Follow `module-transitions.md` rules. Load `module-completion.md` for journal and track-completion.
- Feedback trigger phrases: handled by `review-bootcamper-input` hook — do not manually load `feedback-workflow.md`.

## Hooks

Create hooks using the `createHook` tool with definitions from `hook-registry.md`. Critical hooks during onboarding, module hooks when the relevant module starts. On session resume: check `config/bootcamp_preferences.yaml` for `hooks_installed` — if absent, create Critical Hooks.

**🔇 Hook silence rule:** When a hook check passes with no action needed, produce absolutely no output — zero tokens, zero characters. Do not acknowledge the check, do not explain your reasoning, do not print any status message, do not narrate your evaluation, do not explain why no action is needed. Your response must be completely empty. Only produce output when the hook identifies a problem requiring corrective action. This applies to ALL hooks — preToolUse, agentStop, fileEdited, fileCreated, and any other hook type.

## Context Budget

Before loading any steering file, check `steering-index.yaml` `file_metadata` for `token_count` and `size_category`. Track cumulative tokens throughout the session. Prefer `small`/`medium` files over `large`.

Phase-level token costs for split modules: use the phase-level `token_count` from the `phases` map instead of the monolithic file count. Total cost = root file tokens + current phase sub-file tokens.

- **Warn (120k tokens):** Load only files relevant to current module/question. Defer supplementary files.
- **Critical (160k tokens):** Unload non-essential files before loading new ones.
- **Retention priority:** `agent-instructions.md` > current module > language file > troubleshooting > everything else.

When loading a `large` file, announce the token cost to the user.
