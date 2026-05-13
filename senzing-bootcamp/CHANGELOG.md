# Changelog

All notable changes to the Senzing Bootcamp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Repo-root `tests/conftest.py` that snaps cwd to the project root before every test — eliminated cross-suite cwd drift that caused 115 collection errors when running both `senzing-bootcamp/tests/` and `tests/` in a single pytest invocation

### Changed

- CommonMark configuration (`.markdownlint.json`) tuned for Kiro's `#[[file:...]]` include syntax — disabled MD018/MD025/MD028/MD046 and scoped MD024 to `siblings_only`
- `sync_hook_registry.py` now wraps hook prompts in four-backtick ```` ````text ```` fences so prompts containing their own triple-backtick code blocks (e.g. `deployment-phase-gate`) render without breaking the outer fence
- `lint_steering.py` now recognizes H3-nested step headings (`### Step N:`) used by `module-03-system-verification.md` and accepts any `**Checkpoint:**` marker (not only `**Checkpoint:** Write step N`)
- `test_hook_categories_sync.py` uniqueness check rewritten to allow a single hook in multiple module sub-categories (e.g. `enforce-visualization-offers` in Modules 3, 5, 7, 8) while still enforcing no crossing of the critical/modules/any top-level boundary
- `test_hook_structural_validation.py::test_hook_file_count_matches_categories` compares against unique hook IDs rather than total list entries
- `test_hook_gaps_modules_1_and_3_properties.py::_load_modules_mapping` parses `hook-categories.yaml` directly instead of using `load_category_mapping`, which overwrites multi-module hook entries
- `test_steering_structure_properties.py` regex broadened to match `#{2,}\s+Step\s+(\d+)` headings and any `**Checkpoint:**` marker
- `CRITICAL_HOOKS` constant in `tests/hook_test_helpers.py` updated to reflect the 5 current critical hooks (removed stale `verify-senzing-facts`, `enforce-feedback-path`, `enforce-working-directory`)
- `test_hook_prompt_logic.py` — replaced `TestVerifySenzingFacts`, `TestEnforceWorkingDirectory`, and `TestEnforceFeedbackPath` classes with a single `TestEnforceFilePathPolicies` class matching the consolidated hook
- `module-03-system-verification.md` — added Step 10/11/12 checkpoint instructions, added success indicator, condensed Error Handling section to fit the 15-line lint budget, added explicit timeout declaration to Step 7
- Preservation snapshot hashes refreshed in `test_module2_license_question.py` and `test_module_closing_question_ownership.py` for edits made in the Module 3 rename pass
- Onboarding step sequence baseline updated in `test_onboarding_question_ownership.py` to include `0c. Version Display`
- `test_merge_mapping_validation_hooks.py` expected description updated to drop the obsolete Module 12 reference
- `test_cord_data_priority.py` `SYNTHESIZED_DATA_PATTERN` regex updated to match "test data can also be generated"
- `test_bootcamp_ux_feedback_unit.py` `_TEST_DATA_BULLET` fragment updated to match current CORD-first onboarding copy

### Fixed

- POWER.md `What's New (Unreleased)` bullets reorganized — items actually in 0.11.0 moved to a `What's New in 0.11.0` section; new Unreleased section summarizes the production-readiness pass
- POWER.md stale `~79 lines` claim for `agent-instructions.md` corrected to `~101 lines` (and `module-transitions.md` from `~59` to `~71`)
- `docs/guides/ARCHITECTURE.md` Critical Hooks table updated from 7 obsolete hooks (including deleted `verify-senzing-facts`, `enforce-feedback-path`, `enforce-working-directory`) to the 5 current critical hooks; Module Hooks table updated to reflect `enforce-visualization-offers` in Modules 3/5/7/8, `offer-visualization` removed from Module 7, and `module-completion-celebration` added to Any module
- `steering/onboarding-flow.md` Critical Hook failure-impact table merged `enforce-feedback-path` and `enforce-working-directory` rows into a single `enforce-file-path-policies` row
- `steering/module-03-system-verification.md` — fixed 96 `lint_steering` errors (missing checkpoints, missing success indicator, overly long Error Handling section)
- All shipped markdown files now pass `validate_commonmark.py` — fixed MD040 (missing language tags), MD028 (blank lines in blockquotes), MD056 (malformed tables) in `hook-registry.md` and `inline-status.md`
- Full test suite now at 2,603 passed / 0 failed / 0 errors / 0 collection errors (from 154 failed / 115 errors at the start of this pass)

## [0.11.0] - 2026-05-13

### Added

- AWS deployment reference steering file (`deployment-aws.md`) — dedicated guidance for ECS/Fargate, RDS, Secrets Manager, CloudWatch, IAM best practices, and cost optimization
- Skip Step Protocol (`skip-step-protocol.md`) — escape hatch for stuck bootcampers with step-level skip tracking, consequence assessment, and revisit workflow
- Module 8 phase-split into 3 phases: A (requirements/baselines), B (benchmarking), C (optimization/reporting)
- Module 9 phase-split into 2 phases: A (assessment/secrets), B (hardening/validation)
- Module 10 phase-split into 2 phases: A (monitoring setup), B (operations/validation)
- New hooks for Modules 2, 8, 9, 10: `verify-sdk-setup`, `validate-benchmark-results`, `security-scan-on-save`, `validate-alert-config`
- Integration test (`test_module_flow_integration.py`) validating multi-module state transitions across all tracks
- Enhanced `validate_module.py` checks for Modules 8–11 (benchmark environment, security utilities, monitoring utilities, runbooks, Dockerfile)
- Conversation protocol extracted to `conversation-protocol.md` (auto-included)
- Windows support improvements — Visual Studio Build Tools check in `preflight.py`, Windows-specific pitfalls section in `common-pitfalls.md`, PowerShell execution policy guidance, Windows Terminal recommendation

### Changed

- Module 3 renamed from Quick Demo to System Verification — now uses the Senzing TruthSet with MCP-generated verification code and compares results against expected TruthSet output; authoritative steering file is `module-03-system-verification.md` (replaces `module-03-quick-demo.md`); companion doc is `MODULE_3_SYSTEM_VERIFICATION.md`
- Hook consolidation — `feedback-submission-reminder` and `capture-feedback` merged into `ask-bootcamper` and `review-bootcamper-input` respectively; `enforce-feedback-path` and `enforce-working-directory` consolidated into `enforce-file-path-policies`; `verify-senzing-facts` and `offer-visualization` removed (24 hooks total)
- `hooks/README.md` regenerated to reflect the current 24-hook set
- `scripts/install_hooks.py` HOOKS list and ESSENTIAL set regenerated to match the current 24-hook set
- `deployment-phase-gate.kiro.hook` no longer references Module 12 (collapsed into Module 11)
- `steering-index.yaml` now includes full phase maps with `token_count` and `size_category` for Modules 7–10 (previously bare strings)
- `steering-index.yaml` deployment section now includes `aws` key
- `hook-categories.yaml` now includes hooks for Modules 2, 8, 9, 10
- `structure.md` steering file changed from `auto` to `always` inclusion
- `common-pitfalls.md` changed to manual inclusion
- `.gitignore` now covers `.hypothesis/` and `.pytest_cache/` directories
- Removed stale `__pycache__/`, `.hypothesis/`, `.pytest_cache/` directories from `scripts/` and `tests/`
- VERSION bumped from 0.1.0 to 0.11.0 to reconcile with CHANGELOG history

### Removed

- Deprecated `preflight_check.py` script (was a thin wrapper around `preflight.py`)
- Stale `MODULE_3_QUICK_DEMO.md` references from `docs/README.md`, `docs/modules/README.md`, `docs/guides/README.md`, and POWER.md
- Stale references to deleted hooks (`verify-senzing-facts`, `enforce-feedback-path`, `enforce-working-directory`, `offer-visualization`) from POWER.md and `scripts/install_hooks.py`
- Obsolete "Module 12" references in FAQ, `docs/guides/README.md`, and `deployment-phase-gate.kiro.hook`

## [0.10.0] - 2026-04-22

### Added in 0.10.0

- Visualization steering file (`steering/visualization-guide.md`) — guides the agent through helping bootcampers build their own interactive D3.js entity graph with detail panels, clustering, search/filter, and optional web server, in their chosen language
- Progress repair tool (`scripts/repair_progress.py`) — reconstructs `bootcamp_progress.json` from project artifacts when state is corrupted
- Steering file index (`steering/steering-index.yaml`) — machine-readable mapping of all steering files for faster agent file selection
- GitHub Actions CI workflow (`.github/workflows/validate-power.yml`) for power integrity, CommonMark validation, and test execution
- "What's New in 0.10.0" section in POWER.md for quick orientation
- Offer Entity Graph Visualization hook (`offer-visualization.kiro.hook`) — prompts visualization offer when query files are created in Module 8
- MCP offline fallback steering file (removed in 0.12.0 — MCP is now required)
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
- Offline mode guide (removed in 0.12.0 — MCP is now required)
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
