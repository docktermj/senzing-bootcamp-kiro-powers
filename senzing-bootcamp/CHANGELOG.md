# Changelog

All notable changes to the Senzing Boot Camp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-04-01

### Fixed

- Updated all V3 SDK patterns to V4 across example projects and templates:
  - `G2Engine` → `SzAbstractFactoryCore` + `create_engine()`
  - `engine.init()`/`engine.destroy()` → factory-based lifecycle
  - `addRecord`/`deleteRecord`/`getRecord`/`searchByAttributes` → `add_record`/`delete_record`/`get_record`/`search_by_attributes`
  - `/opt/senzing/g2/resources` → `/opt/senzing/er/resources`
- Files updated: `templates/demo_quick_start.py`, `templates/rollback_load.py`, `templates/performance_baseline.py`, `examples/simple-single-source/README.md`, `examples/multi-source-project/README.md`, `examples/production-deployment/README.md`, `docs/policies/PEP8_COMPLIANCE.md`, `docs/policies/MODULE_1_CODE_LOCATION.md`, `docs/policies/SQLITE_DATABASE_LOCATION.md`

## [0.1.2] - 2026-04-01

### Added

- MODULE_6: Quick test path using `mapping_workflow` steps 5-8 for fast feedback before writing custom loading programs
- MODULE_8: `reporting_guide` references for 4-point ER evaluation framework and quality metrics
- MODULE_9: `reporting_guide` references for SQL analytics and data mart patterns
- MODULE_0: `find_examples` reference for real-world initialization patterns from GitHub
- MODULE_7 steering: `find_examples` reference for queue-based and multi-source loading patterns
- MODULE_12 steering: `find_examples` reference for Dockerfile patterns
- MODULE_1 steering: Instruction to present `download_url` from `get_sample_data` to users
- MODULE_6 steering: Anti-pattern check before loading
- MODULE_7 steering: Anti-pattern check before multi-source orchestration
- MODULE_12 steering: Anti-pattern check before deployment
- `verify-senzing-facts.kiro.hook`: preToolUse hook that enforces SENZING_INFORMATION_POLICY by reminding agent to verify Senzing facts via MCP before writing
- QUICK_START Path B: `sdk_guide(topic='full_pipeline')` as fastest option for experienced users
- Cross-references between troubleshooting-decision-tree and common-pitfalls steering files

### Changed

- steering/module-05-data-mapping: Replaced inline 40-line example program with `mapping_workflow`/`generate_scaffold` delegation
- steering/module-06-single-source: Replaced inline V3-style loading example with `generate_scaffold` delegation
- steering/troubleshooting-decision-tree: Added anti-pattern check to "When All Else Fails" section
- steering/common-pitfalls: Added cross-reference to troubleshooting decision tree

## [0.1.1] - 2026-04-01

### Changed

- System requirements in onboarding checklist now reference the Senzing MCP server as the source of truth instead of hardcoding version numbers
- Added agent instruction to always fetch current requirements via `search_docs` during onboarding
- Added cloud-managed database options (AWS Aurora/RDS, Azure SQL) to database checklist
- Added link to official Senzing v4 System Requirements page
- MODULE_5: Replaced hardcoded SGES attribute reference with MCP server delegation (`mapping_workflow`, `search_docs`, `download_resource`)
- MODULE_5: Replaced hardcoded mapping pattern code with MCP delegation reference
- MODULE_0: Replaced hardcoded platform install commands with `sdk_guide` delegation
- MODULE_0: Replaced hardcoded database config JSON and verification script with `sdk_guide`/`generate_scaffold` delegation
- MODULE_6: Replaced hardcoded error code explanations with `explain_error_code` delegation
- MODULE_6: Replaced hardcoded data source registration and loading code with `generate_scaffold` delegation
- MODULE_8: Replaced hardcoded SDK method signatures and query code with `generate_scaffold`/`get_sdk_reference` delegation
- MODULE_9: Replaced hardcoded performance benchmark numbers with `search_docs` delegation
- steering/module-00-sdk-setup: Replaced hardcoded engine config JSON and test script with MCP delegation
- steering/troubleshooting-decision-tree: Removed hardcoded attribute name and method name examples
- steering/common-pitfalls: Removed hardcoded wrong/right attribute and method name lists, replaced with MCP tool references
- All changes align with SENZING_INFORMATION_POLICY.md which mandates MCP-sourced Senzing facts

### Fixed

- Replaced all `lint_record` references with `analyze_record` — `lint_record` does not exist as an MCP tool; `analyze_record` handles both validation and quality analysis
- docs/modules/README.md was missing entries for Modules 0, 1, 2, and 5 — added all four
- docs/modules/README.md had broken navigation link to non-existent `docs/development/` — removed
- docs/modules/README.md dependency flow diagram incorrectly showed Module 5 → Module 0 → Module 6; corrected to show Module 0 and Module 5 as parallel prerequisites for Module 6
- docs/modules/README.md Quick Reference table was missing Modules 0, 1, 2, and 5 — added all four
- MODULE_12 example code had `python_requires=">=3.8"` in both setup.py and pyproject.toml — corrected to `>=3.10` to match bootcamp-wide Python version requirement
- steering/module-05-data-mapping.md still had hardcoded Senzing attribute names in Step 3 and "Important Rules" section — replaced with MCP delegation per SENZING_INFORMATION_POLICY

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
