---
inclusion: always
---

# Agent Core Rules

On session start: check `config/bootcamp_progress.json`. If exists, load `session-resume.md` and follow the resume workflow. If not, load `onboarding-flow.md`.

## File Placement

| Content     | Location     |
| ----------- | ------------ |
| Source code | `src/`       |
| Scripts     | `scripts/`   |
| Docs        | `docs/`      |
| Data        | `data/`      |
| SQLite DB   | `database/`  |
| Config      | `config/`    |
| Temp files  | `data/temp/` |

**🚨 MANDATORY:** ALL files MUST be placed within the working directory. Never use `/tmp`, `%TEMP%`, `~/Downloads`, or any path outside the project. If MCP tools (e.g., `generate_scaffold`, `ExampleEnvironment`, `mapping_workflow`, `download_resource`) return code or paths referencing `/tmp/` or any system temporary directory, you MUST override those paths to use project-relative directories before saving or executing. Never modify global shell config (`~/.zshrc`, `~/.bashrc`, etc.) — use `scripts/senzing-env.sh` for environment variables.

## MCP Rules

- All Senzing facts must come from MCP tools — never from training data
- Never hand-code Senzing JSON mappings or SDK method names
- Attribute names → `mapping_workflow`
- SDK code → `generate_scaffold` or `sdk_guide`
- Method signatures → `get_sdk_reference`
- Errors → `explain_error_code`
- Docs → `search_docs`
- Examples → `find_examples`
- Always call `get_capabilities` first when starting a session
- Tell MCP to generate production-scale code, not small-data-only patterns
- Reject `exportJSONEntityReport()` and `export_report` — these do not scale. Use per-entity queries (`get_entity_by_entity_id`, `get_entity_by_record_id`, `search_by_attributes`) or streaming patterns instead
- Reuse MCP responses within a module; re-query across module boundaries
- If MCP has no answer: say so, suggest docs.senzing.com or <support@senzing.com> — never fabricate
- **Path override rule:** When MCP tools return code or paths containing `/tmp/`, `ExampleEnvironment`, or any location outside the working directory, ALWAYS replace those paths with project-relative equivalents (e.g., `database/G2C.db`, `data/temp/`, `src/`) before saving or executing

## MCP Failure

Retry once. If still failing, tell user it's temporary. Fallbacks: `find_examples` for code, docs.senzing.com for search, <support@senzing.com> for errors. Never fabricate as substitute.

**MCP skepticism:** If MCP tool output references features, tables, or infrastructure not part of the core Senzing SDK (e.g., data mart tables like `sz_dm_report`, separate open-source projects, beta features), flag it to the user rather than presenting it as built-in. Say what it is, what additional setup it requires, and whether it's production-ready.

## Module Steering

Load per-module steering when user starts that module:

| Module | File                              |
| ------ | --------------------------------- |
| 0      | `module-00-sdk-setup.md`          |
| 1      | `module-01-quick-demo.md`         |
| 2      | `module-02-business-problem.md`   |
| 3      | `module-03-data-collection.md`    |
| 4      | `module-04-data-quality.md`       |
| 5      | `module-05-data-mapping.md`       |
| 6      | `module-06-single-source.md`      |
| 7      | `module-07-multi-source.md`       |
| 8      | `module-08-query-validation.md`   |
| 9      | `module-09-performance.md`        |
| 10     | `module-10-security.md`           |
| 11     | `module-11-monitoring.md`         |
| 12     | `module-12-deployment.md`         |

After Module 2: load `complexity-estimator.md` for personalized time estimates.
At 8→9 gate: load `cloud-provider-setup.md`.
At path end: load `lessons-learned.md`.
On errors: load `common-pitfalls.md`.
On PII/security questions: load `security-privacy.md`.

## Code Standards

Follow language-appropriate standards for the bootcamper's chosen language (Python→PEP-8, Java→standard conventions, C#→.NET conventions, Rust→rustfmt/clippy, TypeScript→ESLint). Use the bootcamper's chosen language for all generated code.

## State & Progress

- `mapping_workflow`: pass exact `state` from previous response, never modify. If lost, restart.
- Progress persisted in `config/bootcamp_progress.json` — checked on session start.
- Preferences in `config/bootcamp_preferences.yaml` — language, path, license survive sessions.
- If progress corrupted: run `python senzing-bootcamp/scripts/validate_module.py`.
- Warn before long mapping sessions: state is not persisted across sessions.

## Communication

- Ask one question at a time, wait for response
- Explain "why" not just "what" — after each step, include a one-liner explaining what it accomplished and why it matters for what comes next
- Admit when you need MCP tools
- On "power feedback" / "bootcamp feedback": load `feedback-workflow.md`
- At module start and completion: follow the journey map, before/after framing, and journal rules in `module-transitions.md`

## Hooks

Install to `.kiro/hooks/` from `senzing-bootcamp/hooks/`. Create directory if needed.
