# Changelog

All notable changes to the Senzing Boot Camp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-04-01

### Changed

- System requirements in onboarding checklist now reference the Senzing MCP server as the source of truth instead of hardcoding version numbers
- Added agent instruction to always fetch current requirements via `search_docs` during onboarding
- Added cloud-managed database options (AWS Aurora/RDS, Azure SQL) to database checklist
- Added link to official Senzing v4 System Requirements page

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
- `status.sh` had wrong module names (0=Quick Demo instead of 0=SDK Setup, etc.) — aligned to canonical numbering
- `troubleshoot.py` referenced non-existent `MODULE_5_SDK_SETUP.md` — corrected to `MODULE_0_SDK_SETUP.md`
- Python version requirement unified to 3.10+ across all files (was inconsistently 3.7+, 3.8+, or 3.10+)
- `MODULE_1_QUICK_DEMO.md` referenced non-existent `check_module0_prerequisites.sh` — corrected to `preflight_check.sh`
- `MODULE_1_QUICK_DEMO.md` referenced non-existent "Simulation Demo" fallback — removed
- System requirements aligned with official Senzing v4 specs: Java ≥ 17, .NET Standard 2.0, PostgreSQL ≥ 15, Ubuntu ≥ 22.04, macOS ≥ 15 Apple Silicon only, Windows ≥ 11, SQLite <1M records

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
