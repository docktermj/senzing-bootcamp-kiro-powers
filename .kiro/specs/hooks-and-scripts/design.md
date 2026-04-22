# Design Document

## Overview

The hooks-and-scripts feature consists of three components: (1) a set of 13 Kiro hook JSON files in `senzing-bootcamp/hooks/`, (2) 10 Python utility scripts in `senzing-bootcamp/scripts/`, and (3) an interactive hook installer that copies hooks into the workspace. All components are part of the distributed power and follow cross-platform conventions.

## Architecture

### Hook Files

Each hook is a JSON file with the `.kiro.hook` extension following the Kiro hook schema:

```json
{
  "name": "Display Name",
  "version": "1.0.0",
  "description": "What the hook does",
  "when": {
    "type": "<eventType>",
    "patterns": ["<glob>"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "Instructions for the agent"
  }
}
```

Event types used across the 13 hooks:
- `fileEdited` (6 hooks): code-style-check, data-quality-check, backup-before-load, validate-senzing-json, commonmark-validation, run-tests-after-change
- `fileCreated` (2 hooks): analyze-after-mapping, verify-generated-code
- `userTriggered` (2 hooks): backup-project-on-request, git-commit-reminder
- `preToolUse` (2 hooks): verify-senzing-facts, enforce-working-directory
- `agentStop` (1 hook): summarize-on-stop

All hooks use `askAgent` as the action type (no `runCommand` hooks).

### Scripts

All scripts are standalone Python 3 CLI tools in `senzing-bootcamp/scripts/`. They share common patterns:

- Shebang line (`#!/usr/bin/env python3`)
- `color_supported()` helper that checks `NO_COLOR`, Windows terminal, and `isatty()`
- ANSI color wrappers (`green()`, `red()`, `yellow()`, `blue()`, `cyan()`)
- `main()` entry point with `if __name__ == "__main__"` guard
- Cross-platform path handling via `pathlib.Path`
- No third-party dependencies (stdlib only)

| Script | Purpose |
|---|---|
| `status.py` | Show current module, progress, project health |
| `validate_module.py` | Validate module prerequisites/success criteria |
| `check_prerequisites.py` | Verify environment tools and runtimes |
| `install_hooks.py` | Interactive hook installer |
| `backup_project.py` | Create timestamped ZIP backup |
| `restore_project.py` | Restore from backup ZIP |
| `clone_example.py` | Copy example project to workspace |
| `preflight_check.py` | Core system requirements check |
| `validate_commonmark.py` | Run markdownlint on Markdown files |
| `validate_power.py` | Validate power internal consistency |

### Hook Installer Flow

```
install_hooks.py
  ├── Discover *.kiro.hook files in senzing-bootcamp/hooks/
  ├── Display available hooks with descriptions
  ├── Prompt: (A) All, (B) Essential, (C) Individual, (Q) Quit
  ├── Create .kiro/hooks/ directory if needed
  ├── Copy selected hooks (skip if already installed)
  └── Report installation summary
```

Essential hooks subset: `code-style-check`, `backup-before-load`, `backup-project-on-request`.

## File Structure

```
senzing-bootcamp/
├── hooks/
│   ├── README.md
│   ├── analyze-after-mapping.kiro.hook
│   ├── backup-before-load.kiro.hook
│   ├── backup-project-on-request.kiro.hook
│   ├── code-style-check.kiro.hook
│   ├── commonmark-validation.kiro.hook
│   ├── data-quality-check.kiro.hook
│   ├── enforce-working-directory.kiro.hook
│   ├── git-commit-reminder.kiro.hook
│   ├── run-tests-after-change.kiro.hook
│   ├── summarize-on-stop.kiro.hook
│   ├── validate-senzing-json.kiro.hook
│   ├── verify-generated-code.kiro.hook
│   └── verify-senzing-facts.kiro.hook
├── scripts/
│   ├── backup_project.py
│   ├── check_prerequisites.py
│   ├── clone_example.py
│   ├── install_hooks.py
│   ├── preflight_check.py
│   ├── restore_project.py
│   ├── status.py
│   ├── validate_commonmark.py
│   ├── validate_module.py
│   └── validate_power.py
```
