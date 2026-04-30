---
inclusion: always
---

# Agent Core Rules

On session start: check `config/bootcamp_progress.json`. If exists, load `session-resume.md`. If not, load `onboarding-flow.md`.

## File Placement

| Content     | Location   | Content    | Location     |
| ----------- | ---------- | ---------- | ------------ |
| Source code | `src/`     | SQLite DB  | `database/`  |
| Scripts     | `scripts/` | Config     | `config/`    |
| Docs        | `docs/`    | Temp files | `data/temp/` |
| Data        | `data/`    |            |              |

🚨 ALL files within working directory only. Never `/tmp`, `%TEMP%`, `~/Downloads`. Override MCP-generated paths (`/tmp/`, `ExampleEnvironment`) to project-relative equivalents. Never modify global shell config.

## MCP Rules

- All Senzing facts from MCP tools — never training data. Call `get_capabilities` first each session.
- Attribute names → `mapping_workflow` | SDK code → `generate_scaffold`/`sdk_guide` | Signatures → `get_sdk_reference` | Errors → `explain_error_code` | Docs → `search_docs` | Examples → `find_examples`
- Never hand-code Senzing JSON mappings or SDK method names
- **Third-party software:** When mentioning or recommending third-party tools (Elasticsearch, PostgreSQL, Docker, Kubernetes, etc.) in the context of Senzing integration, always consult the Senzing MCP server first (`search_docs` with relevant query) to get Senzing's guidance on how that tool integrates with entity resolution. Do not rely on general knowledge alone.
- Generate production-scale code. Reject `exportJSONEntityReport()`/`export_report` — use per-entity queries instead.
- Reuse MCP responses within a module; re-query across module boundaries
- No answer? Say so, suggest <https://docs.senzing.com> / <support@senzing.com> — never fabricate
- MCP skepticism: flag data mart tables (`sz_dm_report`), beta features, or non-core SDK references

## MCP Failure

Retry once. If still failing, load `mcp-offline-fallback.md` for what's blocked vs. what can continue. Never fabricate.

## Module Steering

Load per-module steering file when user starts that module (1→`module-01-business-problem.md` through 11→`module-11-deployment.md`). After Module 1: `complexity-estimator.md`. At 7→8 gate: `cloud-provider-setup.md`. At track end: `lessons-learned.md`. On errors: `common-pitfalls.md`.

**Phase-level loading for split modules:** Some large modules (currently 5 and 6) are split into phase-level sub-files. When entering a split module:

1. Check `steering-index.yaml` — if the module entry has a `root` and `phases` map (instead of a simple filename), it is a split module.
2. Load the root file first (contains preamble, prerequisites, and phase manifest).
3. Read `current_step` from `config/bootcamp_progress.json` and find the phase whose `step_range` in `steering-index.yaml` contains that step.
4. Load only the sub-file for the current phase.
5. On phase transition (when `current_step` crosses a phase boundary), unload the previous phase's sub-file before loading the next phase's sub-file.
6. If a sub-file cannot be found at the expected path, fall back to loading the root file and log a warning that the sub-file is missing.

**Session resume with split modules:** When resuming a session mid-module via `session-resume.md`, the agent reads `current_step` from `bootcamp_progress.json` (Step 1). If the current module has a `phases` entry in `steering-index.yaml`, use `current_step` to determine the phase and load only that sub-file instead of the full module. If `current_step` is absent or doesn't fall within any phase's `step_range`, load the root file only.

**At every module start:** Read `config/bootcamp_progress.json` first (this triggers `module-transitions.md` loading), then display the module start banner, journey map, and before/after framing BEFORE doing any module-specific work. Never skip these — they orient the user.

Module 11 platform files: load `deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, or `deployment-kubernetes.md` based on deployment target.

**Multi-language projects:** If the bootcamper uses different languages for different components (e.g., Python for data transformation, TypeScript for a frontend), load the language steering file for whichever language is currently being edited. Don't force a single language across all components.

## State & Progress

- `mapping_workflow`: pass exact `state`, never modify. Save checkpoints to `config/mapping_state_[datasource].json` per `module-05-data-quality-mapping.md`.
- Progress: `config/bootcamp_progress.json`. Preferences: `config/bootcamp_preferences.yaml`.
- Corrupted? Run `python senzing-bootcamp/scripts/validate_module.py`.
- **Step-level checkpointing:** After completing each numbered step in any module steering file, write a checkpoint to `config/bootcamp_progress.json`: read the file, set `current_step` to the completed step number, set `step_history["<module_number>"]` to `{ "last_completed_step": <step>, "updated_at": "<ISO 8601 now>" }`, and write the file back. On module completion, set `current_step` to `null` (retain the `step_history` entry).

## Communication

- One question at a time, wait for response. Prefix input-required questions with **"👉"** in ALL modules.
- **Never fabricate user input.** Do not generate "Human:" messages, simulate user responses, assume user choices, or act on behalf of the bootcamper without their actual input. If a question requires the bootcamper's choice (track selection, language selection, or any 👉 question), STOP and wait for their real response. Never proceed past a mandatory gate (⛔) without genuine user input.
- **Closing-question ownership:** Never end your turn with a closing question — the `ask-bootcamper` hook owns all closing questions. Mid-conversation 👉 questions are fine; just don't place one at the end of your output.
- **Goldilocks check:** After Modules 3, 6, 9 ask if detail level is right. Store preference in `config/bootcamp_preferences.yaml` as `detail_level`.
- **First-term explanations:** Define Senzing terms inline on first use, reference `docs/guides/GLOSSARY.md`. Don't re-explain.
- Before each step: what and why. During: status updates (never bare "Working..."). After: what changed, files with paths.
- **Data visualization:** Offer to visualize data results as a web page. Save to `docs/` or `data/temp/`.
- At module completion: summary, all files, why it matters for next module. Follow `module-transitions.md` rules. Load `module-completion.md` for journal and track-completion.
- Feedback trigger phrases: handled by `capture-feedback` hook — do not manually load `feedback-workflow.md`.

## Hooks

Create hooks using the `createHook` tool with definitions from `hook-registry.md`. Critical hooks during onboarding, module hooks when the relevant module starts. On session resume: check `config/bootcamp_preferences.yaml` for `hooks_installed` — if absent, create Critical Hooks.

When a hook check passes with no action needed, produce no output. Do not acknowledge the check, do not explain your reasoning, do not print any status message. Do not narrate your evaluation. Do not explain why no action is needed. Your response must be completely empty — zero tokens. Only produce output when the hook requires corrective action.

## Context Budget

Before loading any steering file, check `steering-index.yaml` `file_metadata` for `token_count` and `size_category`. Track cumulative tokens throughout the session. Prefer `small`/`medium` files over `large`.

**Phase-level token costs for split modules:** For modules with a `phases` entry in `steering-index.yaml`, use the phase-level `token_count` from the `phases` map instead of the monolithic file count. The root file token count is always loaded when entering the module; the phase sub-file token count is additive. This means the total cost for a split module at any point is: root file tokens + current phase sub-file tokens.

- **Warn (120k tokens):** Load only files relevant to current module/question. Defer supplementary files.
- **Critical (160k tokens):** Unload non-essential files before loading new ones.
- **Retention priority:** `agent-instructions.md` > current module > language file > troubleshooting > everything else.

When loading a `large` file, announce the token cost to the user.
