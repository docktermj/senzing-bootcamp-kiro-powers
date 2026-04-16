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

Retry once. If still failing, load `common-pitfalls.md` "MCP Server Unavailable" section for what's blocked vs. what can continue. Never fabricate.

## Module Steering

Load per-module steering file when user starts that module (0→`module-00-sdk-setup.md` through 12→`module-12-deployment.md`). After Module 2: `complexity-estimator.md`. At 8→9 gate: `cloud-provider-setup.md`. At path end: `lessons-learned.md`. On errors: `common-pitfalls.md`.

## State & Progress

- `mapping_workflow`: pass exact `state`, never modify. Save checkpoints to `config/mapping_state_[datasource].json` per `module-05-data-mapping.md`.
- Progress: `config/bootcamp_progress.json`. Preferences: `config/bootcamp_preferences.yaml`.
- Corrupted? Run `python senzing-bootcamp/scripts/validate_module.py`.

## Communication

- One question at a time, wait for response
- Before each step: what you're doing and why. During: status updates (never bare "Working..."). After: what changed, files produced with paths.
- **Data visualization:** When presenting data results to the bootcamper (entity resolution results, quality analysis, match explanations, statistics), ask: "Would you like me to visualize this data as a web page?" If yes, generate a self-contained HTML file with the data formatted as tables/charts and save it to `docs/` or `data/temp/`.
- At module completion: summary of accomplishments, all files, why it matters for next module
- At module start/completion: follow `module-transitions.md` rules. After completing any module: load `module-completion.md` for journal and path-completion workflow.
- On "power feedback" / "bootcamp feedback": load `feedback-workflow.md`

## Hooks

Install to `.kiro/hooks/` from `senzing-bootcamp/hooks/`. Create directory if needed.
