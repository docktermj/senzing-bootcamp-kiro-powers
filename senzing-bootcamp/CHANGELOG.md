# Changelog

All notable changes to the Senzing Boot Camp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.8] - 2026-04-02

### Added

- Validation gates for Modules 9→10, 10→11, 11→12 in `agent-instructions.md` — production modules now have explicit criteria before advancing
- Path C auto-insertion of Module 0: agent-instructions now detect when Path C reaches Module 6 without Module 0 complete and insert SDK setup automatically
- Complete `bootcamp_preferences.yaml` schema documented in agent-instructions — defines all fields (language, path, started_at, current_module, license, license_path) with merge-not-overwrite rule
- Resume resilience: First Action now checks `bootcamp_preferences.yaml` for missing fields (e.g., license) when resuming an interrupted session and asks user to fill gaps
- Hook installation offer moved to Second Action (directory creation) — agent now offers hooks during initial setup instead of burying it in Module 4

### Changed

- `backup-project-on-request.kiro.hook`: Changed from `promptSubmit` (fired on every message) to `userTriggered` (manual button click) to eliminate per-prompt latency; action changed from `askAgent` to `runCommand` for direct execution
- `module-04-data-quality.md`: Removed embedded hook installation workflow (moved to agent-instructions); fixed prerequisite from "Module 2" to "Module 3"
- `environment-setup.md`: Added `data/temp/*` to `.gitignore` template
- `security-privacy.md`: Replaced Python-specific "faker library" with language-agnostic list of synthetic data libraries
- `complexity-estimator.md`: Fixed "Module 4" references to "Module 5" in all three complexity tier time estimates
- `POWER.md` and `QUICK_START.md`: Path C description now notes Module 0 is auto-inserted before Module 6
- Fifth Action intro text corrected from "After language selection" to "After the license check"

### Fixed

- Module 2 steering transition text said "Module 1 Complete" and "Ready to move to Module 2" — corrected to "Module 2 Complete" and "Ready to move to Module 3"
- Module 4 prerequisite said "Module 2 complete" — corrected to "Module 3 complete" (data collection, not business problem)
- Module 4 categorization step said "Proceed to Module 3 (data mapping)" — corrected to "Module 5" (Module 3 is data collection, Module 5 is mapping)
- Module 4 evaluation template "Next step" said "Module 3 / Module 4" — corrected to "Module 5 / Module 6"
- Module 5 steering said "identified in Module 3" — corrected to "identified in Module 4" (Module 4 categorizes sources, Module 3 collects them)
- `POWER.md` steering file list said "Module 4: Data Quality + Hook Installation" — removed hook reference since hooks moved to setup
- `HOOKS_INSTALLATION_GUIDE.md` said "Install hooks at the start of Module 5" and "before Module 3" — updated to reference initial project setup

## [0.1.7] - 2026-04-02

### Added

- Senzing license check step in `agent-instructions.md` (new Fourth Action): agent now asks bootcampers about their Senzing license before the prerequisite check, guides license placement in `licenses/g2.lic`, and persists the choice in `config/bootcamp_preferences.yaml`
- `ExampleEnvironment` override note in `FILE_STORAGE_POLICY.md`: explicitly documents that the SDK helper's `/tmp/` default must be overridden with `database/G2C.db`

### Changed

- `module-01-quick-demo.md`: Demo script now uses `database/G2C.db` instead of in-memory SQLite; agent behavior section reinforces overriding `/tmp/` defaults from `generate_scaffold` or `ExampleEnvironment`
- `module-05-data-mapping.md`: Added instruction to override any `/tmp/` paths returned by `mapping_workflow` with project-local paths (`data/temp/`, `data/raw/`, `src/transform/`); added file storage rule to Important Rules section
- `module-00-sdk-setup.md`: SQLite configuration step now includes explicit warning against `/tmp/` and in-memory databases; SDK install step is now language-agnostic
- `feedback-workflow.md`: Feedback is now saved locally only — removed MCP server submission. Agent will only submit to MCP if user explicitly requests it
- `SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md`: Removed MCP server submission references; updated submission section to local-only
- `senzing-bootcamp-power-development/guides/FEEDBACK_WORKFLOW.md`: Updated to local-only feedback, removed dual-submission references, updated agent best practices and example interaction
- Removed Python bias across the entire power to support language-agnostic bootcamp:
  - `scripts/preflight_check.sh`: Rewritten to detect all supported language runtimes instead of only Python/pip
  - `scripts/check_prerequisites.sh`: Rewritten with language runtime section checking all 5 languages; removed Python package checks; language runtimes shown as "at least one required"
  - `scripts/backup_project.sh`: Exclude patterns now cover all language build artifacts (target/, bin/, obj/, node_modules/, dist/)
  - `docs/guides/FAQ.md`: Prerequisites no longer list "Python 3.10+, pip" — now say "a supported language runtime"
  - `docs/guides/ONBOARDING_CHECKLIST.md`: SDK Language section lists all 5 languages with tooling; Quick Validation checks all runtimes; Troubleshooting covers all languages
  - `docs/guides/AFTER_BOOTCAMP.md`: Removed `language='python'` from example MCP call
  - `docs/guides/HOOKS_INSTALLATION_GUIDE.md`: Example hook patterns cover all source file extensions
  - `docs/modules/MODULE_5_DATA_MAPPING.md`: File extensions changed from `.py` to `.[ext]`
  - `docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md`: File extensions changed from `.py` to `.[ext]`; scaffold example uses `<chosen_language>` instead of `python`
  - `docs/modules/MODULE_10_SECURITY_HARDENING.md`: Security scanning and testing sections now show tools for all languages
  - `docs/policies/FILE_STORAGE_POLICY.md`: Examples use `.[ext]` instead of `.py`; dependency file list consolidated; temp dir examples are language-neutral
  - `steering/common-pitfalls.md`: SDK check commands cover all languages; "Python mapper scripts" → "Mapper scripts"
  - `steering/module-05-data-mapping.md`: Code quality reference points to policy doc instead of inlining Python-specific rules
  - `steering/module-06-single-source.md`: Code quality reference points to policy doc
  - `steering/module-07-multi-source.md`: Removed Python-specific example command
  - `steering/module-08-query-validation.md`: Removed Python-specific example command
  - `steering/uat-framework.md`: Test executor uses `.[ext]` instead of `.py`

### Fixed

- Module 1 demo created SQLite databases in `/tmp/` instead of project `database/` directory
- Feedback workflow submitted to MCP server without explicit user consent
- No license check before Module 1, causing bootcampers with paid licenses to miss using them
- Module 5 mapping workflow saved resources and profiler output to `/tmp/` instead of project directories
- Duplicate step numbering (two step 7s) in `agent-instructions.md` Third Action
- `QUICK_START.md` time estimates for Modules 10-12 inconsistent with `POWER.md` (now aligned: Module 10 = 2-8 hrs, Module 11 = 60-90 min, Module 12 = 2-4 hrs)
- `QUICK_START.md` listed "Python 3.10+" as requirement for all paths — updated to mention all supported languages
- `environment-setup.md` contradicted `FILE_STORAGE_POLICY.md` by saying shell scripts don't go in `scripts/` — corrected
- `project-structure.md` tree diagram missing `licenses/`, `backups/`, `data/temp/`, and `scripts/` directories — added
- `project-structure.md` wrong module references in docs comments (Module 1→2, Module 2→4, Module 3→5, Module 6→8)
- `project-structure.md` mkdir commands missing `licenses/`, `backups/`, and `data/temp/` — added
- `ONBOARDING_CHECKLIST.md` directory structure and mkdir commands missing `licenses/`, `backups/`, and `data/temp/` — added
- `module-prerequisites.md` Module 0 had Python-only references — updated to multi-language
- `MODULE_1_QUICK_DEMO.md` referenced "in-memory SQLite database" — updated to `database/G2C.db`
- `docs/README.md` missing `AFTER_BOOTCAMP.md` and `GLOSSARY.md` from guides listing
- `production-deployment/README.md` Module 10 time estimate "1-2 hours" inconsistent with POWER.md "2-8 hrs" — corrected
- `licenses/README.md` had Python-specific verification script — replaced with language-agnostic instructions
- `licenses/README.md` and `FAQ.md` said license was "required" for Module 0+ — updated to reflect SDK built-in evaluation limits
- `MODULE_0_SDK_SETUP.md` said "A valid Senzing license is required" — updated to reflect built-in evaluation limits and reference the new license check step
- `MODULE_1_QUICK_DEMO.md` example output still showed "in-memory database" — corrected to `database/G2C.db`

## [0.1.6] - 2026-04-01

### Added

- `docs/guides/AFTER_BOOTCAMP.md`: Post-bootcamp guide covering production maintenance cadence, scaling, adding new data sources, staying updated, advanced topics, and community resources
- `docs/guides/GLOSSARY.md`: Quick-reference glossary of 18 Senzing entity resolution terms
- Cross-references between all 13 steering files and their corresponding module docs for easier navigation

### Changed

- Consolidated 3 micro-policies (`MODULE_1_CODE_LOCATION.md`, `SQLITE_DATABASE_LOCATION.md`, `SHELL_SCRIPT_LOCATIONS.md`) into `FILE_STORAGE_POLICY.md` — policies/ reduced from 8 files to 5
- Trimmed all 3 example project READMEs to architecture-only descriptions — removed inline Python code, kept project structure, data flow diagrams, field mappings, and expected results

### Removed

- `docs/policies/MODULE_1_CODE_LOCATION.md` (consolidated into FILE_STORAGE_POLICY.md)
- `docs/policies/SQLITE_DATABASE_LOCATION.md` (consolidated into FILE_STORAGE_POLICY.md)
- `docs/policies/SHELL_SCRIPT_LOCATIONS.md` (consolidated into FILE_STORAGE_POLICY.md)

## [0.1.5] - 2026-04-01

### Added

- Multi-language support: bootcamp now queries the Senzing MCP server for supported programming languages and asks the bootcamper to choose before starting. All generated code, scaffold calls, and examples use the chosen language throughout every module.
- Language-appropriate prerequisite checks (Python, Java, C#, Rust, TypeScript/Node.js)
- Language-appropriate coding standards guidance via `docs/policies/CODE_QUALITY_STANDARDS.md`
- Language-agnostic dependency management via `docs/policies/DEPENDENCY_MANAGEMENT_POLICY.md`
- Session persistence: language choice and path saved to `config/bootcamp_preferences.yaml`
- Progress tracking: `config/bootcamp_progress.json` updated after each module's validation gate
- Resume flow: agent checks for existing progress on startup and offers to continue
- Progress celebration: congratulates user every 3 modules
- `run-tests-after-change.kiro.hook`: reminds agent to run tests after code changes in src/
- Expanded Modules 9-12 steering files to match the depth of Modules 0-5 (3-10x more content each)
  - Module 9: 13 steps with MCP tool integration, database-specific tuning, scalability testing, 4-point ER evaluation framework
  - Module 10: 12 steps covering secrets management, authentication, RBAC, encryption, audit logging, input validation, network security, Senzing-specific security, vulnerability scanning
  - Module 11: 10 steps with Senzing-specific monitoring (get_stats semantics, redo queue, cross-source metrics), 4 dashboard definitions, alert rules with escalation, health checks, runbooks
  - Module 12: 14 steps covering containerization, database migration, CI/CD (GitHub Actions/GitLab/Jenkins), REST API layer, scaling guidance, Kubernetes manifests, pre-deployment checklist, rollback plan
- Language-aware .gitignore generation in environment-setup.md
- MCP-driven SDK verification in Module 0 (replaces hardcoded per-language checks)
- Actionable MCP tool calls in troubleshooting-decision-tree.md

### Changed

- `agent-instructions.md`: Added progress check as First Action, directory creation as Second Action, language selection as Third Action, prerequisite check as Fourth Action. Added progress persistence after validation gates. Added resume flow.
- `module-00-sdk-setup.md`: SDK verification now uses MCP `sdk_guide` instead of hardcoded per-language commands
- `module-09-performance.md`: Expanded from 1-page skeleton to comprehensive 13-step workflow with MCP integration
- `module-10-security.md`: Expanded from 1-page skeleton to comprehensive 12-step workflow with Senzing-specific security
- `module-11-monitoring.md`: Expanded from 1-page skeleton to comprehensive 10-step workflow with Senzing-specific monitoring
- `module-12-deployment.md`: Expanded from 1-page skeleton to comprehensive 14-step workflow with containerization, CI/CD, and scaling
- `environment-setup.md`: .gitignore now generates language-specific entries based on chosen language
- `troubleshooting-decision-tree.md`: Added MCP tool calls for each diagnostic path
- `POWER.md`: Updated time estimates for Modules 9-12 to be realistic; noted Modules 9-12 are production-focused and optional
- `hooks/pep8-check.kiro.hook`: Renamed to `code-style-check.kiro.hook`
- `module-01-quick-demo.md`: Demo script generation uses chosen language; file extensions are language-appropriate
- `module-05-data-mapping.md`: Transformation program generation uses chosen language
- `module-06-single-source.md`: Loading program generation uses chosen language
- `module-07-multi-source.md`: Orchestrator generation uses chosen language
- `module-08-query-validation.md`: Query program generation uses chosen language
- `module-09-performance.md`: Performance benchmarks use pseudocode instead of Python
- `module-10-security.md`: Security code references use generic file extensions
- `module-11-monitoring.md`: Monitoring code uses pseudocode instead of Python
- `module-12-deployment.md`: Package structure is language-agnostic
- `project-structure.md`: Dependency file guidance now covers all supported languages
- `data-lineage.md`: Lineage tracker described as algorithm instead of Python class
- `common-pitfalls.md`: File references use generic extensions
- `environment-setup.md`: Setup instructions cover all supported languages
- `POWER.md`: Code quality standards section updated to reflect multi-language support
- All module docs (MODULE_0 through MODULE_9): Replaced Python code with pseudocode and MCP scaffold instructions
- All hooks: Updated file patterns to match all supported language extensions
- `hooks/pep8-check.kiro.hook`: Renamed to "Code Style Check", now triggers on all source file types

### Removed

- 12 Python template files from `templates/` (replaced by dynamic MCP code generation)
- `docs/policies/PEP8_COMPLIANCE.md` (replaced by `CODE_QUALITY_STANDARDS.md`)
- `docs/policies/PYTHON_REQUIREMENTS_POLICY.md` (replaced by `DEPENDENCY_MANAGEMENT_POLICY.md`)
- `examples/requirements.txt.example` and `examples/requirements-dev.txt.example`

## [0.1.4] - 2026-04-01

### Added

- `analyze-after-mapping.kiro.hook`: Triggers on new JSONL files in `data/transformed/`, reminds agent to run `analyze_record` before loading
- Module 3 steering: `get_sample_data` MCP tool as first option when users need sample data (alongside existing GitHub free-data link)
- Module 7 steering: `reporting_guide(topic='graph')` for cross-source entity relationship visualization
- Module 7 steering: `explain_error_code` guidance for diagnosing per-source failures during orchestration
- Module 5 steering: Globalization guidance — `search_docs(category='globalization')` for non-Latin character data

### Fixed

- PEP8_COMPLIANCE.md CI/CD example used `python-version: 3.8` — corrected to `3.10`
- Example project READMEs used wrong Senzing attribute names (`PRIMARY_NAME_LAST`, `PRIMARY_NAME_FULL`, `EMPLOYER_NAME`) — corrected to V4 names (`NAME_LAST`, `NAME_FULL`, `NAME_ORG`) with note that `mapping_workflow` generates the actual names
- Production deployment example benchmark used `PRIMARY_NAME_FULL` — corrected to `NAME_FULL`

## [0.1.3] - 2026-04-01

### Fixed

- Updated all V3 SDK patterns to V4 across example projects and templates:
  - `G2Engine` → `SzAbstractFactoryCore` + `create_engine()`
  - `engine.init()`/`engine.destroy()` → factory-based lifecycle
  - `addRecord`/`deleteRecord`/`getRecord`/`searchByAttributes` → `add_record`/`delete_record`/`get_record`/`search_by_attributes`
  - `/opt/senzing/g2/resources` → `/opt/senzing/er/resources`
- Files updated: `templates/demo_quick_start.py`, `templates/rollback_load.py`, `templates/performance_baseline.py`, `examples/simple-single-source/README.md`, `examples/multi-source-project/README.md`, `examples/production-deployment/README.md`, `docs/policies/PEP8_COMPLIANCE.md`, `docs/policies/MODULE_1_CODE_LOCATION.md`, `docs/policies/SQLITE_DATABASE_LOCATION.md`
- Removed references to non-existent `docs/development/` directory from `docs/README.md`, `docs/policies/FILE_STORAGE_POLICY.md`, `docs/policies/README.md` (development docs are in `senzing-bootcamp-power-development/`)
- Fixed `docs/README.md` incomplete file listings — added missing Modules 0, 1, 2, 5 and missing policy/guide files
- Fixed V3 method name `whyEntities` → `why_entities` in `templates/troubleshoot.py`

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
- Feedback collection workflow with local file storage
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
