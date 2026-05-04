# Changelog

All notable changes to the Senzing Bootcamp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Removed 28 orphaned specs from `.kiro/specs/` that referenced old module numbering, renamed hooks, or deleted files
- Fixed module numbering in `common-pitfalls.md` — merged old Module 6/7 sections into Module 6 (Load Data), renumbered Module 8 to Module 7
- Fixed `onboarding-flow.md` failure impact table referencing `summarize-on-stop` (renamed to `ask-bootcamper`)
- Fixed `POWER.md` MCP JSON block showing empty `disabledTools` instead of `["submit_feedback"]`
- Fixed `POWER.md` duplicate listing of `module-01-business-problem.md`
- Fixed `agent-instructions.md` stale "triggers loading" language for `module-transitions.md`
- Changed `security-privacy.md` from `inclusion: auto` to `inclusion: always` (27 lines, negligible context cost)
- Dropped unused "(SGES)" abbreviation from `POWER.md` and `onboarding-flow.md`
- Updated `POWER.md` Recommended Hooks to list all 20 hooks (was missing `capture-feedback` and `feedback-submission-reminder`)
- Removed stale `examples/` row from repository-organization steering
- Added steering file cross-references to `docs/modules/README.md`
- Removed ghost-artifact absence assertions from test files
- Trimmed `agent-instructions.md` from 109 to ~80 lines: moved Sub-Step Convention to `module-transitions.md`, collapsed Question Stop Protocol
- Changed `verbosity-control.md` from `inclusion: always` to `inclusion: auto` — saves ~71 lines of context on lightweight interactions
- Split `visualization-guide.md` (414 lines) into workflow root (~85 lines) + `visualization-reference.md` (~90 lines) via `#[[file:]]`
- Split `module-06-phaseD-validation.md` (355 lines) into validation steps (~150 lines) + `module-06-reference.md` (~110 lines) via `#[[file:]]`
- Extracted "What Is Entity Resolution?" section from `onboarding-flow.md` into `entity-resolution-intro.md` via `#[[file:]]`
- Changed `common-pitfalls.md`, `module-prerequisites.md`, `design-patterns.md` from `inclusion: manual` to `inclusion: auto`
- Trimmed `hook-registry.md` from 235 to ~105 lines by removing duplicated prompt text (prompts live in `.kiro.hook` files)
- Added Windows-specific pitfalls section to `common-pitfalls.md` (python3 vs python, PowerShell execution policy, npm.cmd, VS Build Tools, DLL PATH, Unicode, source command)
- Added PowerShell execution policy and dot-sourcing guidance to `environment-setup.md`
- Added Visual Studio Build Tools check and npm.cmd detection to `preflight.py` for Windows
- Added Windows `PATH` / DLL guidance to `lang-python.md` and `lang-java.md` platform notes
- Added `pyenv-win` mention to `lang-python.md` for Windows version management
- Added macOS `DYLD_LIBRARY_PATH` guidance to `lang-java.md`
- Added Windows section to `QUICK_START.md` (python command, Windows Terminal, VS Build Tools)
- Added Windows Terminal recommendation to `POWER.md` Useful Commands section
- Fixed onboarding failure impact table — added missing `review-bootcamper-input` and `feedback-submission-reminder` hooks (was 7/9 critical hooks, now 9/9)
- Fixed Track A definition in `onboarding-flow.md` — was "2→3", now "1→2→3" to match POWER.md and module-dependencies.yaml
- Fixed `#[[file:]]` path in `verbosity-control.md` — was relative, now full path consistent with all other references
- Added "What's New (Unreleased)" section to POWER.md summarizing changes since 0.10.0

## [0.10.0] - 2026-04-22

### Added in 0.10.0

- Visualization steering file (`steering/visualization-guide.md`) — guides the agent through helping bootcampers build their own interactive D3.js entity graph with detail panels, clustering, search/filter, and optional web server, in their chosen language
- Progress repair tool (`scripts/repair_progress.py`) — reconstructs `bootcamp_progress.json` from project artifacts when state is corrupted
- Steering file index (`steering/steering-index.yaml`) — machine-readable mapping of all steering files for faster agent file selection
- GitHub Actions CI workflow (`.github/workflows/validate-power.yml`) for power integrity, CommonMark validation, and test execution
- "What's New in 0.10.0" section in POWER.md for quick orientation
- Offer Entity Graph Visualization hook (`offer-visualization.kiro.hook`) — prompts visualization offer when query files are created in Module 8
- MCP offline fallback steering file (`steering/mcp-offline-fallback.md`) — extracted from common-pitfalls.md for leaner context loading
- Troubleshooting commands steering file (`steering/troubleshooting-commands.md`) — extracted from troubleshooting-decision-tree.md

- Review Bootcamper Input hook (`review-bootcamper-input.kiro.hook`) — deterministic feedback capture via promptSubmit trigger with automatic context capture
- Module 11 Phase Gate hook (`deployment-phase-gate.kiro.hook`) — enforces packaging-to-deployment decision gate in Module 11
- Enforce Module 8 Visualization Offers hook (`enforce-visualization-offers.kiro.hook`) — catches missed visualization offers before Module 8 closes
- Feedback workflow rewritten with Step 0 (automatic context capture) and Step 7 (return to previous activity)
- Module 8 steering file updated with mandatory ⛔ WAIT blocks for both visualization offers
- Module 11 steering file updated with prominent ⛔ PHASE GATE section between packaging and deployment

### Changed in 0.10.0

- FAQ feedback section updated with direct link to feedback template file
- Module 8 steering file updated with visualization steering file reference (replaces script approach)
- Hooks README updated with entry #14 for offer-visualization hook
- `#[[file:]]` references added to module-04, module-05, and module-08 steering files for template access
- Multi-language project note added to agent-instructions.md
- PowerShell directory creation command added to project-structure.md
- common-pitfalls.md reduced from 312 to 212 lines (MCP section extracted)
- troubleshooting-decision-tree.md reduced from 299 to 224 lines (commands section extracted)

## [0.9.0] - 2026-04-21

### Added in 0.9.0

- Module 7 steering file expanded from ~100 to 323 lines with 12-step orchestration workflow, source ordering heuristics, conflict resolution guidance, error handling, and troubleshooting
- MCP failure recovery section in `common-pitfalls.md` with blocked/continuable operation tables, per-operation fallback instructions, reconnection procedures, and connectivity troubleshooting
- Module 2 license step completed with license priority order, `SENZING_LICENSE_PATH` discovery, acquisition contacts, and `licenses/README.md` reference
- Data collection checklist template at `templates/data_collection_checklist.md` with 9-column inventory table and validation checklist
- Quality scoring methodology guide at `docs/guides/QUALITY_SCORING_METHODOLOGY.md` with weighted formula, threshold bands, and worked examples
- Quick navigation with anchor links in `common-pitfalls.md` for module-specific troubleshooting
- Language steering files expanded from ~10 to ~55 lines each with SDK best practices, common pitfalls, performance considerations, code style, and platform notes
- Stakeholder summary template at `templates/stakeholder_summary.md` with module-aware placeholder guidance for Modules 1, 8, and 12
- Performance baselines guide at `docs/guides/PERFORMANCE_BASELINES.md` with throughput tables, hardware requirements, SQLite vs PostgreSQL comparison, and profiling tools
- UAT test case template at `templates/uat_test_cases.md` with functional, performance, and data quality test sections
- Module 11 deployment expanded with on-premises, Azure, GCP, and Kubernetes platform reference sections
- Offline mode guide at `docs/guides/OFFLINE_MODE.md` with per-module offline capability and reconnection steps
- Transformation lineage template at `templates/transformation_lineage.md` with field mappings, format changes, filters, and quality improvements
- Integration patterns section in Module 8 steering file with 6 patterns (batch report, REST API, streaming, database sync, duplicate detection, watchlist screening)
- Disaster recovery subsection in Module 11 Step 15 with RTO/RPO, 3-2-1 backup rule, DR scenarios, and backup scripts
- Concrete SQLite pragma and PostgreSQL config snippets in performance baselines guide
- Profiling and monitoring section in performance baselines guide with bottleneck patterns and language-specific tools
- Common mistakes guide at `docs/guides/COMMON_MISTAKES.md`
- Getting help guide at `docs/guides/GETTING_HELP.md`
- Lessons learned template at `templates/lessons_learned.md`
- Module prerequisites Mermaid diagram in `docs/diagrams/module-prerequisites.md`

### Changed in 0.9.0

- `module-transitions.md` changed from `inclusion: auto` to `inclusion: fileMatch` on `config/bootcamp_progress.json` — reduces context waste on non-module-boundary interactions
- `agent-instructions.md` updated to note `module-transitions.md` is conditionally loaded
- Module 3 visualization offer promoted to its own numbered step (Step 5) before module close
- Module 3 completion Explore option now mentions visualization and interactive features
- Module 5 quality thresholds aligned to ≥80%/70-79%/<70% bands
- `data-lineage.md` steering file expanded with lineage file structure, example entries, tracker utility, and compliance guidance
- `COLLABORATION_GUIDE.md` expanded with bootcamp-specific collaboration examples
- Cross-references added between related guides (quality scoring ↔ performance baselines ↔ offline mode)
- Template references added to module docs (Module 4, 5, 8)
- POWER.md updated with references to new guides, templates, and offline mode
- Module 11 split into main workflow (296 lines) + 4 separate platform steering files (`deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, `deployment-kubernetes.md`) per Kiro steering best practices
- Module 7 split into main workflow (205 lines) + `module-07-reference.md` (130 lines) for ordering examples, conflict resolution, and troubleshooting
- Module 2 Step 5 (license) condensed from ~80 to ~20 prescriptive lines
- Generic language standards removed from all 5 language steering files — kept only Senzing SDK-specific content
- `agent-instructions.md` updated with Module 11 platform file references and Module 7 reference guidance
- POWER.md Advanced Topics section updated with 5 new steering file references
- Repository organization steering file simplified after development directory removal
- `docs/development.md` simplified after development directory removal
- `MODULE_8_QUERY_VALIDATION.md` fixed `uat_test_cases.yaml` → `uat_test_cases.md` references

### Removed in 0.9.0

- `senzing-bootcamp-power-development/` directory — historical development archive removed; useful content incorporated into distributed power
- `powers/git-best-practices/` — unrelated generic power removed

## Earlier Versions

### [0.8.0] - 2026-04-17

Added setup preamble, `👉` input-required markers across all modules, Goldilocks detail check every 3 modules, welcome-back banner in session resume, SQLite ≤1,000 record recommendation, and explicit Module 3 closure before Module 1 transition. Module 1 Steps 1-3 received explicit WAIT markers.

### [0.7.0] - 2026-04-17

Added one-question-at-a-time rule, license discovery in Module 2, interactive visualization features, zero-matches handling in Module 8, first-term explanation rule, guided troubleshooting diagnostics, validate_power.py script, system architecture diagram, iterate-vs-proceed decision gates, and next-step options in module completion. Trimmed onboarding-flow.md, COLLABORATION_GUIDE.md, and ONBOARDING_CHECKLIST.md significantly.

### [0.6.0] - 2026-04-16

Added glossary reference in onboarding, iterate-vs-proceed decision gates, system architecture diagram, next-step options after every module, guided troubleshooting in common-pitfalls.md, stakeholder summary templates, data visualization triggers, and validate_power.py script. Restructured Module 11 into Phase 1 (Packaging) and Phase 2 (Deployment). Made language selection MCP-driven and rewrote onboarding-flow.md from 333 to 85 lines.

### [0.5.0] - 2026-04-14

Added MCP offline guidance, mapping state checkpointing, summarize-on-stop and verify-generated-code hooks, module-completion.md steering file, and use-case bridging questions in Module 3. Major rewrites to reduce context usage: agent-instructions.md (98→54 lines), security-privacy.md (80→27), project-structure.md (130→44), module-transitions.md split into lean auto (27 lines) + manual module-completion.md (49 lines).

### [0.4.0] - 2026-04-09

Streamlined onboarding to two user-visible questions (language and path). Added session-resume.md, enforce-working-directory hook, PowerShell equivalents for all bash commands, and AWS CDK guidance. Condensed common-pitfalls.md (514→150 lines), module-prerequisites.md (401→54 lines), and complexity-estimator.md (352→53 lines). Removed `#[[file:]]` references from always-loaded agent-instructions.md.

### [0.3.0] - 2026-04-08

Split agent-instructions.md into always-loaded core + manual onboarding-flow.md. Trimmed Modules 8-11 from 1,100-1,500 lines each to 78-119 lines. Added 5 language-specific steering files (Python, Java, C#, Rust, TypeScript), cloud-provider-setup.md, and foundational steering file generation during onboarding. Removed templates/ directory (replaced by MCP dynamic generation).

### [0.2.0] - 2026-04-06

Standardized "boot camp" → "bootcamp" across all 55+ files. Removed time estimates from module listings (complexity estimator provides personalized estimates). Added MCP failure recovery, language switching, progress corruption recovery, and AWS/cloud provider guidance across steering files, docs, scripts, and examples.
