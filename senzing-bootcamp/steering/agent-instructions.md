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

Load per-module steering file when user starts that module (1→`module-01-business-problem.md` through 12→`module-12-deployment.md`). After Module 1: `complexity-estimator.md`. At 8→9 gate: `cloud-provider-setup.md`. At track end: `lessons-learned.md`. On errors: `common-pitfalls.md`.

**At every module start:** Read `config/bootcamp_progress.json` first (this triggers `module-transitions.md` loading), then display the module start banner, journey map, and before/after framing BEFORE doing any module-specific work. Never skip these — they orient the user.

Module 12 platform files: load `deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, or `deployment-kubernetes.md` based on deployment target. Module 7 reference: load `module-07-reference.md` for ordering examples, conflict resolution, and troubleshooting.

**Multi-language projects:** If the bootcamper uses different languages for different components (e.g., Python for data transformation, TypeScript for a frontend), load the language steering file for whichever language is currently being edited. Don't force a single language across all components.

## State & Progress

- `mapping_workflow`: pass exact `state`, never modify. Save checkpoints to `config/mapping_state_[datasource].json` per `module-05-data-quality-mapping.md`.
- Progress: `config/bootcamp_progress.json`. Preferences: `config/bootcamp_preferences.yaml`.
- Corrupted? Run `python senzing-bootcamp/scripts/validate_module.py`.
- **Step-level checkpointing:** After completing each numbered step in any module steering file, write a checkpoint to `config/bootcamp_progress.json`: read the file, set `current_step` to the completed step number, set `step_history["<module_number>"]` to `{ "last_completed_step": <step>, "updated_at": "<ISO 8601 now>" }`, and write the file back. On module completion, set `current_step` to `null` (retain the `step_history` entry).

## Communication

- One question at a time, wait for response. Prefix input-required questions with **"👉"** in ALL modules.
- **Closing-question ownership:** Never end your turn with a closing question — the `ask-bootcamper` hook owns all closing questions. Mid-conversation 👉 questions are fine; just don't place one at the end of your output.
- **Goldilocks check:** After Modules 3, 6, 9 ask if detail level is right. Store preference in `config/bootcamp_preferences.yaml` as `detail_level`.
- **First-term explanations:** Define Senzing terms inline on first use, reference `docs/guides/GLOSSARY.md`. Don't re-explain.
- Before each step: what and why. During: status updates (never bare "Working..."). After: what changed, files with paths.
- **Data visualization:** Offer to visualize data results as a web page. Save to `docs/` or `data/temp/`.
- At module completion: summary, all files, why it matters for next module. Follow `module-transitions.md` rules. Load `module-completion.md` for journal and track-completion.
- Feedback trigger phrases: handled by `capture-feedback` hook — do not manually load `feedback-workflow.md`.

## Hooks

Create hooks using the `createHook` tool with definitions from `hook-registry.md`. Critical hooks during onboarding, module hooks when the relevant module starts. On session resume: check `config/bootcamp_preferences.yaml` for `hooks_installed` — if absent, create Critical Hooks.

## Context Budget

Before loading any steering file, check `steering-index.yaml` `file_metadata` for `token_count` and `size_category`. Track cumulative tokens throughout the session. Prefer `small`/`medium` files over `large`.

- **Warn (120k tokens):** Load only files relevant to current module/question. Defer supplementary files.
- **Critical (160k tokens):** Unload non-essential files before loading new ones.
- **Retention priority:** `agent-instructions.md` > current module > language file > troubleshooting > everything else.

When loading a `large` file, announce the token cost to the user.
