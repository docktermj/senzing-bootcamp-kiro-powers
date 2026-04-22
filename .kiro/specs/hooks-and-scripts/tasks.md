# Tasks

## Requirement 1: Kiro Hooks

- [x] 1.1 Create `code-style-check.kiro.hook` with fileEdited trigger on `*.py,*.java,*.cs,*.rs,*.ts,*.js`
- [x] 1.2 Create `data-quality-check.kiro.hook` with fileEdited trigger on `src/transform/*.*`
- [x] 1.3 Create `backup-before-load.kiro.hook` with fileEdited trigger on `src/load/*.*`
- [x] 1.4 Create `validate-senzing-json.kiro.hook` with fileEdited trigger on `data/transformed/*.jsonl`
- [x] 1.5 Create `backup-project-on-request.kiro.hook` with userTriggered event
- [x] 1.6 Create `commonmark-validation.kiro.hook` with fileEdited trigger on `**/*.md`
- [x] 1.7 Create `verify-senzing-facts.kiro.hook` with preToolUse trigger on write operations
- [x] 1.8 Create `analyze-after-mapping.kiro.hook` with fileCreated trigger on `data/transformed/*.jsonl`
- [x] 1.9 Create `run-tests-after-change.kiro.hook` with fileEdited trigger on `src/load/*.*,src/query/*.*,src/transform/*.*`
- [x] 1.10 Create `git-commit-reminder.kiro.hook` with userTriggered event
- [x] 1.11 Create `enforce-working-directory.kiro.hook` with preToolUse trigger on write operations
- [x] 1.12 Create `summarize-on-stop.kiro.hook` with agentStop event
- [x] 1.13 Create `verify-generated-code.kiro.hook` with fileCreated trigger on `src/transform/*.*,src/load/*.*,src/query/*.*`
- [x] 1.14 Create `hooks/README.md` documenting all hooks, installation options, and troubleshooting

## Requirement 2: Utility Scripts

- [x] 2.1 Create `status.py` — display current module, progress, project health, and next steps
- [x] 2.2 Create `validate_module.py` — validate module prerequisites and success criteria with per-module checks
- [x] 2.3 Create `check_prerequisites.py` — verify required tools, language runtimes, directory structure, and config files
- [x] 2.4 Create `backup_project.py` — create timestamped ZIP backup excluding build artifacts
- [x] 2.5 Create `restore_project.py` — restore project from backup ZIP with confirmation prompts
- [x] 2.6 Create `clone_example.py` — interactive example project cloner with merge/new-directory options
- [x] 2.7 Create `preflight_check.py` — core system requirements check (runtimes, disk, memory, permissions)
- [x] 2.8 Create `validate_commonmark.py` — run markdownlint and report CommonMark compliance
- [x] 2.9 Create `validate_power.py` — validate power consistency (hooks, steering, scripts, module docs, references)

## Requirement 3: Hook Installer

- [x] 3.1 Implement hook discovery via glob for `*.kiro.hook` in the power hooks directory
- [x] 3.2 Implement interactive menu with All / Essential / Individual / Quit options
- [x] 3.3 Implement copy logic with skip-if-exists and auto-create `.kiro/hooks/` directory
- [x] 3.4 Define essential hooks subset (code-style-check, backup-before-load, backup-project-on-request)

## Requirement 4: Cross-Platform Compatibility

- [x] 4.1 Use `pathlib.Path` for all file path operations across all scripts
- [x] 4.2 Implement `color_supported()` helper with NO_COLOR, Windows terminal, and isatty detection
- [x] 4.3 Use only Python standard library modules (no third-party dependencies)
