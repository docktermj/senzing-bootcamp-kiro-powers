# Changelog

All notable changes to the Senzing Boot Camp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-30

### Improved

- Reduced `agent-instructions.md` (always-loaded) from 734 to ~150 lines by moving module-specific behaviors into their respective module steering files and removing content duplicated in policies
- Removed content duplication: directory creation script lives only in `project-structure.md`, file placement rules live only in `FILE_STORAGE_POLICY.md`, module behaviors live only in per-module steering files
- Fixed `security-privacy.md` contradicting itself — was `inclusion: always` but had a "When to Load" section listing manual triggers. Removed the contradictory section
- Fixed Path B inconsistency: POWER.md said "Modules 0, 6" while agent-instructions said "Modules 5-6". Aligned to "Modules 5-6" everywhere
- Tightened POWER.md description from 2 sentences to 1 (removed redundant second sentence)
- Added boot camp completion and feedback reminder to Module 12 steering file
- Added feedback mechanism mention to Module 2 steering file

## [0.1.1] - 2026-03-30

### Improved

- Module 3: Agent now proactively mentions https://github.com/docktermj/senzing-bootcamp-free-data when users need free data sources for the boot camp
- Global: Elevated "all files must stay in the project directory" to a core principle in agent-instructions — applies to all modules, not just Module 5. Covers `/tmp`, `~/Downloads`, and all system directories.
- Project setup: Added `.history/` to default `.gitignore` template to prevent IDE history artifacts from cluttering git commits

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
- Feedback collection workflow
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

### Architecture

- POWER.md kept concise (~190 lines) with details in steering files
- `agent-instructions.md` (always loaded) for behavioral rules
- `steering.md` (manual inclusion) for detailed module workflows
- 19 steering files organized by category
- Separate development repository for internal docs

## Feedback

We welcome feedback on the boot camp experience. Say "power feedback" at any time during the boot camp, or document issues in `docs/feedback/`.
