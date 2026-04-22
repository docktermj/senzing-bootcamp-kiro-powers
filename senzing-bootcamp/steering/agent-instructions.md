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

Load per-module steering file when user starts that module (0→`module-00-sdk-setup.md` through 12→`module-12-deployment.md`). After Module 2: `complexity-estimator.md`. At 8→9 gate: `cloud-provider-setup.md`. At path end: `lessons-learned.md`. On errors: `common-pitfalls.md`.

**At every module start:** Read `config/bootcamp_progress.json` first (this triggers `module-transitions.md` loading), then display the module start banner, journey map, and before/after framing BEFORE doing any module-specific work. Never skip these — they orient the user.

Module 12 platform files: load `deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, or `deployment-kubernetes.md` based on deployment target. Module 7 reference: load `module-07-reference.md` for ordering examples, conflict resolution, and troubleshooting.

**Multi-language projects:** If the bootcamper uses different languages for different components (e.g., Python for data transformation, TypeScript for a frontend), load the language steering file for whichever language is currently being edited. Don't force a single language across all components.

## State & Progress

- `mapping_workflow`: pass exact `state`, never modify. Save checkpoints to `config/mapping_state_[datasource].json` per `module-05-data-mapping.md`.
- Progress: `config/bootcamp_progress.json`. Preferences: `config/bootcamp_preferences.yaml`.
- Corrupted? Run `python senzing-bootcamp/scripts/validate_module.py`.

## Communication

- One question at a time, wait for response
- **Input-required marker:** When asking the bootcamper a question that requires their input, prefix it with **"👉"** so they can clearly see when a response is needed vs. when you're just providing information. Example: "👉 Which language would you like to use?" vs. "I've created the project directory structure." Apply this in ALL modules, not just onboarding — every WAIT-marked question in every steering file should use 👉.
- **Goldilocks check:** Every 3 modules (after Modules 3, 6, and 9), ask: "👉 Quick check — is the level of detail I'm providing too much, too little, or just right? I can adjust." If they want less detail, be more concise in explanations. If they want more, add context and examples. Remember their preference in `config/bootcamp_preferences.yaml` as `detail_level: more|less|default`.
- **First-term explanations:** The first time a Senzing-specific term appears in conversation (entity resolution, SGES, DATA_SOURCE, RECORD_ID, features, redo queue, etc.), briefly define it inline (one sentence) and mention `docs/guides/GLOSSARY.md` for more detail. Don't re-explain on subsequent uses.
- Before each step: what you're doing and why. During: status updates (never bare "Working..."). After: what changed, files produced with paths.
- **Data visualization:** When presenting data results to the bootcamper (entity resolution results, quality analysis, match explanations, statistics), ask: "👉 Would you like me to visualize this data as a web page?" If yes, ask what interactive features they'd like. Generate accordingly — use the SDK's query capabilities to power interactive features. Save to `docs/` or `data/temp/`.
- At module completion: summary of accomplishments, all files, why it matters for next module
- At module start/completion: follow `module-transitions.md` rules (conditionally loaded when `config/bootcamp_progress.json` is accessed, not auto-included). After completing any module: load `module-completion.md` for journal and path-completion workflow.
- On "power feedback" / "bootcamp feedback": load `feedback-workflow.md`

## Hooks

Install to `.kiro/hooks/` from `senzing-bootcamp/hooks/`. Create directory if needed.
