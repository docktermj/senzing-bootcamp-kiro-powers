# Changelog

All notable changes to the Senzing Bootcamp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

For the complete version history (0.1.0 through 0.1.9), see the development repository at `senzing-bootcamp-power-development/CHANGELOG_FULL.md`.

## [0.4.0] - 2026-04-09

### Changed in 0.4.0

- Streamlined onboarding: directory creation, hook installation, and steering generation now happen silently — user only sees two questions (language and path)
- Hooks install automatically at bootcamp start — no longer asks for permission
- Trimmed path descriptions in POWER.md and onboarding-flow.md to concise labels
- Rewrote QUICK_START.md from 230 lines to ~50 lines, aligned with current onboarding flow
- Condensed `common-pitfalls.md` from 514 to ~150 lines using prescriptive table format, changed from `auto` to `manual` inclusion
- Condensed `module-prerequisites.md` from 401 to ~54 lines using compact tables
- Condensed `complexity-estimator.md` from 352 to ~53 lines using compact tables
- Removed `#[[file:]]` references from always-loaded `agent-instructions.md` — reduced effective always-on context from ~700 to ~90 lines
- Changed `security-privacy.md` and `project-structure.md` from `manual` to `auto` inclusion
- Removed redundant directory setup narration from Module 2
- Updated HOOKS_INSTALLATION_GUIDE.md to reflect automatic installation
- Fixed broken markdown fence in module-03-data-collection.md
- Updated FAQ to note prerequisites are checked automatically

### Added in 0.4.0

- `session-resume.md` — structured workflow for resuming previous bootcamp sessions across context windows
- `enforce-working-directory.kiro.hook` — preToolUse hook that blocks writes to `/tmp` or paths outside the working directory
- Tool Usage Examples section in POWER.md with concrete MCP tool call examples
- Mapping workflow state loss recovery guidance in `common-pitfalls.md`
- Windows/WSL2 setup instructions in onboarding flow
- Path B note for Module 0 requirement in onboarding flow
- PowerShell equivalents for all bash commands in modules 0-3
- AWS CDK guidance at the 8→9 gate and in Module 12
- Language steering file loaded immediately after language selection (not just on file match)
- Explicit `inclusion` frontmatter instructions for generated workspace steering files
- Kiro Refine button recommendation for generated steering files
- `preflight_check.py` and `validate_commonmark.py` added to POWER.md Useful Commands

### Fixed in 0.4.0

- `module-prerequisites.md` Module 5 skip note said "Go directly to Module 0" — corrected to Module 6
- `module-01-quick-demo.md` had Python-specific `os.makedirs` in language-agnostic instructions — made language-neutral
- `export_report` and `exportJSONEntityReport()` now explicitly banned across agent-instructions, module-08, and policies
- `/tmp` override instructions added to modules 6, 7, 8, 9 (previously only in 0, 1, 5)
- `generate_scaffold(workflow='redo')` in Module 9 Step 9 now has path override reminder

## [0.3.0] - 2026-04-08

### Changed in 0.3.0

- Split `agent-instructions.md` into a slim always-loaded core (principles, MCP rules, error handling) and a manual `onboarding-flow.md` (directory creation, language selection, prerequisites, path selection, validation gates) to reduce context usage on every turn
- Tightened `agent-instructions.md` from 156 lines to 90 lines — more prescriptive, less descriptive, uses `#[[file:]]` references instead of inline content
- Changed `security-privacy.md` from `inclusion: always` to `inclusion: manual` — loaded on demand during Module 10 or when handling PII
- Changed `common-pitfalls.md` from `inclusion: manual` to `inclusion: auto` — Kiro includes it when relevant to the conversation
- Extracted 8→9 gate cloud provider selection into dedicated `cloud-provider-setup.md` steering file
- Trimmed Modules 9-12 steering files from 1,100-1,500 lines each to 78-119 lines — removed verbose pseudocode, kept prescriptive step lists with MCP tool delegation
- Clarified script paths in POWER.md — scripts live in `senzing-bootcamp/scripts/` and should be referenced from the power directory
- Updated example project READMEs to explicitly note they are architectural blueprints, not runnable code
- Added diagram viewing guidance in POWER.md (Mermaid preview extension or mermaid.live)
- Trimmed CHANGELOG to current version only; full history moved to development repository
- Added foundational steering file generation (product.md, tech.md, structure.md) to onboarding flow
- Added `#[[file:]]` references in steering files to pull policy docs into context when needed

### Added in 0.3.0

- `lang-python.md` — conditional steering for Python files (`*.py`)
- `lang-java.md` — conditional steering for Java files (`*.java`)
- `lang-csharp.md` — conditional steering for C# files (`*.cs`)
- `lang-rust.md` — conditional steering for Rust files (`*.rs`)
- `lang-typescript.md` — conditional steering for TypeScript/JavaScript files (`*.ts`, `*.tsx`, `*.js`, `*.jsx`)

### Removed in 0.3.0

- `templates/` directory (templates have been dynamically generated by MCP since v0.1.5)
- `scripts/__pycache__/` build artifacts from power distribution

### Fixed in 0.3.0

- `module-prerequisites.md` Module 1 listed "No prerequisites" but Module 0 (SDK Setup) is required — corrected to match agent-instructions and QUICK_START

## [0.2.0] - 2026-04-06

### Changed in 0.2.0

- Standardized "boot camp" → "bootcamp" (one word) across all 55+ files
- Removed time estimates from all module listings — the complexity estimator provides personalized estimates instead
- Added MCP Failure Recovery, language switching, progress corruption recovery, AWS/cloud provider guidance, and many other improvements across steering files, docs, scripts, and examples
- See development repository for full 0.2.0 details
