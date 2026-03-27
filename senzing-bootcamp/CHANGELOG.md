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
- Live demo for Module 0 that runs real Senzing SDK
- Simulation fallback demo when SDK unavailable
- Feedback collection workflow
- Prerequisite checker (`scripts/check_prerequisites.sh`)
- Hook auto-installer (`scripts/install_hooks.sh`)
- Example project cloner (`scripts/clone_example.sh`)
- Project backup/restore scripts
- FAQ (100+ questions), glossary, collaboration guide
- Visual diagrams (module flow, data flow)
- Dedicated feedback workflow steering file
- Explicit MCP tool usage patterns in documentation
- `get_stats()` usage clarification in Module 0 docs and demo template
- File placement enforcement for Module 4 mapping workflow

### Architecture

- POWER.md kept concise (~190 lines) with details in steering files
- `agent-instructions.md` (always loaded) for behavioral rules
- `steering.md` (manual inclusion) for detailed module workflows
- 19 steering files organized by category
- Separate development repository for internal docs

## Feedback

We welcome feedback on the boot camp experience. Say "power feedback" at any time during the boot camp, or document issues in `docs/feedback/`.
