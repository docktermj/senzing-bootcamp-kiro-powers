# Changelog

All notable changes to the Senzing Bootcamp power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2026-04-21

### Added in 0.9.0

- Module 7 steering file expanded from ~100 to 323 lines with 12-step orchestration workflow, source ordering heuristics, conflict resolution guidance, error handling, and troubleshooting
- MCP failure recovery section in `common-pitfalls.md` with blocked/continuable operation tables, per-operation fallback instructions, reconnection procedures, and connectivity troubleshooting
- Module 0 license step completed with license priority order, `SENZING_LICENSE_PATH` discovery, acquisition contacts, and `licenses/README.md` reference
- Data collection checklist template at `templates/data_collection_checklist.md` with 9-column inventory table and validation checklist
- Quality scoring methodology guide at `docs/guides/QUALITY_SCORING_METHODOLOGY.md` with weighted formula, threshold bands, and worked examples
- Quick navigation with anchor links in `common-pitfalls.md` for module-specific troubleshooting
- Language steering files expanded from ~10 to ~55 lines each with SDK best practices, common pitfalls, performance considerations, code style, and platform notes
- Stakeholder summary template at `templates/stakeholder_summary.md` with module-aware placeholder guidance for Modules 2, 8, and 12
- Performance baselines guide at `docs/guides/PERFORMANCE_BASELINES.md` with throughput tables, hardware requirements, SQLite vs PostgreSQL comparison, and profiling tools
- UAT test case template at `templates/uat_test_cases.md` with functional, performance, and data quality test sections
- Module 12 deployment expanded with on-premises, Azure, GCP, and Kubernetes platform reference sections
- Offline mode guide at `docs/guides/OFFLINE_MODE.md` with per-module offline capability and reconnection steps
- Transformation lineage template at `templates/transformation_lineage.md` with field mappings, format changes, filters, and quality improvements
- Integration patterns section in Module 8 steering file with 6 patterns (batch report, REST API, streaming, database sync, duplicate detection, watchlist screening)
- Disaster recovery subsection in Module 12 Step 15 with RTO/RPO, 3-2-1 backup rule, DR scenarios, and backup scripts
- Concrete SQLite pragma and PostgreSQL config snippets in performance baselines guide
- Profiling and monitoring section in performance baselines guide with bottleneck patterns and language-specific tools
- Common mistakes guide at `docs/guides/COMMON_MISTAKES.md`
- Getting help guide at `docs/guides/GETTING_HELP.md`
- Lessons learned template at `templates/lessons_learned.md`
- Module prerequisites Mermaid diagram in `docs/diagrams/module-prerequisites.md`

### Changed in 0.9.0

- `module-transitions.md` changed from `inclusion: auto` to `inclusion: fileMatch` on `config/bootcamp_progress.json` — reduces context waste on non-module-boundary interactions
- `agent-instructions.md` updated to note `module-transitions.md` is conditionally loaded
- Module 1 visualization offer promoted to its own numbered step (Step 5) before module close
- Module 1 completion Explore option now mentions visualization and interactive features
- Module 4 quality thresholds aligned to ≥80%/70-79%/<70% bands
- `data-lineage.md` steering file expanded with lineage file structure, example entries, tracker utility, and compliance guidance
- `COLLABORATION_GUIDE.md` expanded with bootcamp-specific collaboration examples
- Cross-references added between related guides (quality scoring ↔ performance baselines ↔ offline mode)
- Template references added to module docs (Module 3, 5, 8)
- POWER.md updated with references to new guides, templates, and offline mode
- Module 12 split into main workflow (296 lines) + 4 separate platform steering files (`deployment-onpremises.md`, `deployment-azure.md`, `deployment-gcp.md`, `deployment-kubernetes.md`) per Kiro steering best practices
- Module 7 split into main workflow (205 lines) + `module-07-reference.md` (130 lines) for ordering examples, conflict resolution, and troubleshooting
- Module 0 Step 5 (license) condensed from ~80 to ~20 prescriptive lines
- Generic language standards removed from all 5 language steering files — kept only Senzing SDK-specific content
- `agent-instructions.md` updated with Module 12 platform file references and Module 7 reference guidance
- POWER.md Advanced Topics section updated with 5 new steering file references
- Repository organization steering file simplified after development directory removal
- `docs/development.md` simplified after development directory removal
- `MODULE_8_QUERY_VALIDATION.md` fixed `uat_test_cases.yaml` → `uat_test_cases.md` references

### Removed in 0.9.0

- `senzing-bootcamp-power-development/` directory — historical development archive removed; useful content incorporated into distributed power
- `powers/git-best-practices/` — unrelated generic power removed

## Earlier Versions

### [0.8.0] - 2026-04-17

Added setup preamble, `👉` input-required markers across all modules, Goldilocks detail check every 3 modules, welcome-back banner in session resume, SQLite ≤1,000 record recommendation, and explicit Module 1 closure before Module 2 transition. Module 2 Steps 1-3 received explicit WAIT markers.

### [0.7.0] - 2026-04-17

Added one-question-at-a-time rule, license discovery in Module 0, interactive visualization features, zero-matches handling in Module 8, first-term explanation rule, guided troubleshooting diagnostics, validate_power.py script, system architecture diagram, iterate-vs-proceed decision gates, and next-step options in module completion. Trimmed onboarding-flow.md, COLLABORATION_GUIDE.md, and ONBOARDING_CHECKLIST.md significantly.

### [0.6.0] - 2026-04-16

Added glossary reference in onboarding, iterate-vs-proceed decision gates, system architecture diagram, next-step options after every module, guided troubleshooting in common-pitfalls.md, stakeholder summary templates, data visualization triggers, and validate_power.py script. Restructured Module 12 into Phase 1 (Packaging) and Phase 2 (Deployment). Made language selection MCP-driven and rewrote onboarding-flow.md from 333 to 85 lines.

### [0.5.0] - 2026-04-14

Added MCP offline guidance, mapping state checkpointing, summarize-on-stop and verify-generated-code hooks, module-completion.md steering file, and use-case bridging questions in Module 1. Major rewrites to reduce context usage: agent-instructions.md (98→54 lines), security-privacy.md (80→27), project-structure.md (130→44), module-transitions.md split into lean auto (27 lines) + manual module-completion.md (49 lines).

### [0.4.0] - 2026-04-09

Streamlined onboarding to two user-visible questions (language and path). Added session-resume.md, enforce-working-directory hook, PowerShell equivalents for all bash commands, and AWS CDK guidance. Condensed common-pitfalls.md (514→150 lines), module-prerequisites.md (401→54 lines), and complexity-estimator.md (352→53 lines). Removed `#[[file:]]` references from always-loaded agent-instructions.md.

### [0.3.0] - 2026-04-08

Split agent-instructions.md into always-loaded core + manual onboarding-flow.md. Trimmed Modules 9-12 from 1,100-1,500 lines each to 78-119 lines. Added 5 language-specific steering files (Python, Java, C#, Rust, TypeScript), cloud-provider-setup.md, and foundational steering file generation during onboarding. Removed templates/ directory (replaced by MCP dynamic generation).

### [0.2.0] - 2026-04-06

Standardized "boot camp" → "bootcamp" across all 55+ files. Removed time estimates from module listings (complexity estimator provides personalized estimates). Added MCP failure recovery, language switching, progress corruption recovery, and AWS/cloud provider guidance across steering files, docs, scripts, and examples.
