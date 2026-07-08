# Senzing Bootcamp Hooks - Installation Guide

## Automatic Installation

Hooks are created automatically during onboarding. The agent reads the V1 hook definitions from the Hook Registry (`hook-registry.md` and its `hook-registry-critical.md` / per-module slices) and calls the `createHook` tool for each one — no manual action needed. Each hook is created with the Kiro 1.0 parameters:

- **trigger:** the 1.0 event name that fires the hook (for example `PostFileSave`, `Stop`, `PreToolUse`).
- **matcher:** a single regular expression that scopes the hook — a file-path regex for file triggers or a tool-name regex such as `fs_write|str_replace|fs_append` for tool triggers. Unscoped triggers (`Stop`, `UserPromptSubmit`, `PostTaskExec`) omit the matcher.
- **action:** either `{"type": "agent", "prompt": "..."}` or `{"type": "command", "command": "..."}`.

The migrated set is 27 hooks:

- **Critical Hooks** (4) are created during initial setup.
- **Module Hooks** (23) are created when you reach the relevant module.

No files are copied. The `createHook` tool creates hooks programmatically, so hooks work whether the power was installed via Kiro's power system or cloned from the source repository.

## Manual Reinstallation

If hooks need to be recreated (for example, after clearing `.kiro/hooks/`):

```text
"Please recreate the bootcamp hooks"
```

The agent will read the Hook Registry (`hook-registry.md`) and recreate all Critical Hooks using the `createHook` tool. Module Hooks are recreated when you start the associated module.

## What Gets Installed

27 pre-configured V1 hooks, shipped as `.json` files under `senzing-bootcamp/hooks/`.

### Critical Hooks (created during onboarding)

| Hook | Trigger | Purpose |
| ---- | ------- | ------- |
| ask-bootcamper | Agent stops (Stop) | Recaps accomplishments, owns the closing question, and reminds about saved feedback |
| code-style-check | Save source code (PostFileSave) | Check language-appropriate coding standards |
| review-bootcamper-input | Every message (UserPromptSubmit) | Detect feedback and status trigger phrases |
| write-policy-gate | Before write (PreToolUse) | Enforce SQL blocking, single-question, path, and root-placement policies |

### Module Hooks (created when module starts)

| Hook | Module | Trigger | Purpose |
| ---- | ------ | ------- | ------- |
| validate-business-problem | 1 | After task (PostTaskExec) | Validate the problem definition before proceeding |
| verify-sdk-setup | 2 | Save config/database file (PostFileSave) | Re-verify SDK setup during config changes |
| enforce-gate-on-stop | 3 | Agent stops (Stop) | Catch missed mandatory-gate violations at agent stop |
| enforce-mandatory-gate | 3 | Before write (PreToolUse) | Block step advancement past a mandatory gate before it executes |
| gate-module3-visualization | 3 | Before write (PreToolUse) | Block Module 3 completion until the visualization step is done |
| verify-demo-results | 3 | After task (PostTaskExec) | Verify system verification against the TruthSet |
| enforce-visualization-offers | 3, 5, 7, 8 | Agent stops (Stop) | Safety net for missed visualization offers |
| validate-data-files | 4 | New file in data/raw/ (PostFileCreate) | Check file format, encoding, and readability |
| analyze-after-mapping | 5 | New file in data/transformed/ (PostFileCreate) | Run analyze_record for quality metrics |
| data-quality-check | 5 | Save transformation program (PostFileSave) | Remind to validate data quality |
| enforce-mapping-spec | 5 | New file in data/transformed/ (PostFileCreate) | Block progression until a per-source mapping spec exists |
| backup-before-load | 6 | Save loading program (PostFileSave) | Remind to back up the database before loading |
| run-tests-after-change | 6 | Save src/ code files (PostFileSave) | Remind to run tests after code changes |
| verify-generated-code | 6 | New source file created (PostFileCreate) | Run new code on sample data |
| validate-benchmark-results | 8 | Save benchmark output (PostFileSave) | Validate benchmark output metrics |
| security-scan-on-save | 9 | Save security/config file (PostFileSave) | Re-run the vulnerability scanner |
| validate-alert-config | 10 | New alert/dashboard file (PostFileCreate) | Validate monitoring alert rules |
| deployment-phase-gate | 11 | After task (PostTaskExec) | Enforce the packaging-to-deployment gate |
| enforce-critical-artifacts | Any | Agent stops (Stop) | Enforce the graduation-artifact completion invariant |
| error-recovery-context | Any | After shell command (PostToolUse) | Consult pitfalls on non-zero shell exits |
| module-completion-celebration | Any | Agent stops (Stop) | Celebrate module completion and point to the next step |
| module-recap-append | Any | Agent stops (Stop) | Append a structured recap section to docs/bootcamp_recap.md |
| session-log-events | Any | After write (PostToolUse) | Log write operations to the session log |

## Slash Commands (formerly manual hooks)

Kiro 1.0 removes the manual (`userTriggered`) hook trigger, so the three former manual-trigger hooks are now manual-invocation slash commands. Invoke each by name when you need it:

- `/backup-project` — run the project backup script (replaces `backup-project-on-request`). See `senzing-bootcamp/steering/slash-backup-project.md`.
- `/git-commit` — suggest a descriptive commit for your module progress (replaces `git-commit-reminder`). See `senzing-bootcamp/steering/slash-git-commit.md`.
- `/commonmark-validation` — validate and fix Markdown CommonMark compliance in one pass (replaces `commonmark-validation`). See `senzing-bootcamp/steering/slash-commonmark-validation.md`.

## Customization

Hooks are managed through the Kiro hooks system. Common changes:

- **Disable a hook:** Edit the hook's `.json` file in `.kiro/hooks/` and set `"enabled": false`, or delete the file.
- **Recreate hooks:** Ask the agent: "Please recreate the bootcamp hooks"

## Support

- Hook overview (IDs, triggers, descriptions): `senzing-bootcamp/steering/hook-registry.md`
- Full hook prompts for `createHook`: `senzing-bootcamp/steering/hook-registry-critical.md` (critical) and the per-module `senzing-bootcamp/steering/hook-registry-module-NN.md` slices (module-specific, including `hook-registry-module-any.md`)
- Hook source files: `senzing-bootcamp/hooks/README.md`
- Kiro docs: [https://kiro.dev/docs/hooks/](https://kiro.dev/docs/hooks/)
