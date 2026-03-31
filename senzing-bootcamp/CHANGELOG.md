# Changelog

All notable changes to the Senzing Boot Camp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-27

### Added

- Comprehensive guided boot camp with 13 modules (0-12)
- Design pattern gallery with 10 common entity resolution patterns
- 3 example project blueprints (simple, multi-source, production)
- 10+ code templates for utilities (backup, restore, collection, validation)
- Steering guides for all modules with on-demand loading
- Progress tracking system (`scripts/status.sh`)
- PEP-8 compliance checking via hooks
- Live demo for Module 1 that runs real Senzing SDK
- Feedback collection workflow with dual submission (local file + MCP server)
- Prerequisite checker (`scripts/check_prerequisites.sh`)
- Hook auto-installer (`scripts/install_hooks.sh`)
- Example project cloner (`scripts/clone_example.sh`)
- Project backup/restore scripts
- FAQ, collaboration guide
- Visual diagrams (module flow, data flow)
- Dedicated feedback workflow steering file
- Explicit MCP tool usage patterns in documentation
- `get_stats()` usage clarification in Module 1 docs and demo template
- File placement enforcement for Module 5 mapping workflow
- Module 3: Agent proactively mentions [senzing-bootcamp-free-data](https://github.com/docktermj/senzing-bootcamp-free-data) when users need free data sources
- Elevated "all files must stay in the project directory" to a core principle in agent-instructions
- `.history/` in default `.gitignore` template
- Reduced `agent-instructions.md` from 734 to ~150 lines by moving module-specific behaviors into per-module steering files
- Removed content duplication across steering files and policies
- Boot camp completion and feedback reminder in Module 12 steering file
- Feedback mechanism mention in Module 2 steering file
- MCP caching policy: agents must make fresh MCP calls on every Senzing question, even repeated ones within the same session
- "Repeated Questions" section in `SENZING_INFORMATION_POLICY.md`
- Apache 2.0 LICENSE file
- Blueprint notices on all example project READMEs
- No-fabrication rule: agent must not present inferred answers as authoritative when MCP returns no definitive result

### Fixed

- `security-privacy.md` contradicting itself with a "When to Load" section on an always-loaded file
- Path B inconsistency: aligned to "Modules 5-6" everywhere
- Module 0 prerequisites incorrectly required Module 5 completion
- Duplicate numbering in `agent-instructions.md` Core Principles
- `backup-before-load.kiro.hook` referenced non-existent `backup_database.sh`
- Path A time estimate in `QUICK_START.md` now clarifies Module 0 prerequisite
- Complexity estimator "When to Load" referenced wrong module numbers

### Changed

- Tightened POWER.md description from 2 sentences to 1
- Consolidated three CommonMark validation hooks into one (`commonmark-validation.kiro.hook`)
- Narrowed POWER.md keywords to avoid false-positive activations

### Architecture

- POWER.md kept concise (~190 lines) with details in steering files
- `agent-instructions.md` (always loaded) for behavioral rules
- Per-module steering files (manual inclusion) for detailed module workflows
- 19 steering files organized by category
- Separate development repository for internal docs

## Feedback

We welcome feedback on the boot camp experience. Say "power feedback" at any time during the boot camp, or document issues in `docs/feedback/`.
