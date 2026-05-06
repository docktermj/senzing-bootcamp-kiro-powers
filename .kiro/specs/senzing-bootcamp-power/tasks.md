# Tasks

This spec documents the power as-built. All tasks reflect implemented state.

## Task 1: Core Curriculum (11 Modules)

- [x] 1.1 Module 1 (Business Problem): steering file with 2 phases, gate criteria (problem documented, sources identified)
- [x] 1.2 Module 2 (SDK Setup): steering file, preflight verification, license handling, EULA gate
- [x] 1.3 Module 3 (Quick Demo): steering file, sample data download, visualization offer
- [x] 1.4 Module 4 (Data Collection): steering file, data file validation hook, collection checklist template
- [x] 1.5 Module 5 (Data Quality & Mapping): steering file with 3 phases, quality scoring, mapping workflow integration, enforce-mapping-spec hook
- [x] 1.6 Module 6 (Load Data): steering file with 4 phases, loading program generation, redo processing, multi-source orchestration
- [x] 1.7 Module 7 (Query & Visualize): steering file, query program generation, entity graph visualization, results dashboard
- [x] 1.8 Module 8 (Performance Testing): steering file with 3 phases, benchmark scripts, database tuning, scalability testing
- [x] 1.9 Module 9 (Security Hardening): steering file with 2 phases, secrets management, RBAC, vulnerability scanning, security checklist
- [x] 1.10 Module 10 (Monitoring & Observability): steering file with 2 phases, metrics collection, dashboards, alerts, runbooks, health checks
- [x] 1.11 Module 11 (Package & Deploy): steering file with 2 phases, containerization, CI/CD, deployment phase gate, 5 platform reference files

## Task 2: Learning Tracks and Navigation

- [x] 2.1 Four tracks defined (A: 1→2→3, B: 5→6→7, C: 1→4→5→6→7, D: 1–11)
- [x] 2.2 Module 2 auto-insertion before SDK-dependent modules
- [x] 2.3 Module dependency graph in `config/module-dependencies.yaml`
- [x] 2.4 Validation gates between all module transitions
- [x] 2.5 Track switching with completed modules carrying forward
- [x] 2.6 Skip Step Protocol for step-level skips within modules
- [x] 2.7 Graduation workflow at track completion

## Task 3: Steering System

- [x] 3.1 Always-on files: agent-instructions (89 lines), module-transitions (71 lines), security-privacy (27 lines)
- [x] 3.2 Auto files: agent-context-management, conversation-protocol, design-patterns, module-prerequisites, project-structure, session-resume, verbosity-control (7 files)
- [x] 3.3 FileMatch files: 5 language steering files with troubleshooting sections (≤107 lines each)
- [x] 3.4 Manual files: 61 module workflows, deployment, troubleshooting, inline-status, whats-new, etc.
- [x] 3.5 steering-index.yaml with token counts, size categories, phase maps, keyword routing, deployment mapping
- [x] 3.6 Context budget tracking with percentage-based 60%/80% thresholds and 6-tier retention priority (in agent-context-management.md)
- [x] 3.7 Adaptive pacing: classify_pacing() in analyze_sessions.py, pacing_overrides in preferences, steering instructions in agent-context-management.md

## Task 4: Hook System (23 hooks)

- [x] 4.1 7 critical hooks created during onboarding
- [x] 4.2 Module 2 hook: verify-sdk-setup
- [x] 4.3 Module 4 hook: validate-data-files
- [x] 4.4 Module 5 hooks: analyze-after-mapping, data-quality-check, enforce-mapping-spec
- [x] 4.5 Module 6 hooks: backup-before-load, run-tests-after-change, verify-generated-code
- [x] 4.6 Module 7 hooks: enforce-visualization-offers, offer-visualization
- [x] 4.7 Module 8 hook: validate-benchmark-results
- [x] 4.8 Module 9 hook: security-scan-on-save
- [x] 4.9 Module 10 hook: validate-alert-config
- [x] 4.10 Module 11 hook: deployment-phase-gate
- [x] 4.11 Any-time hooks: backup-project-on-request, git-commit-reminder
- [x] 4.12 hook-categories.yaml and hook-registry.md kept in sync via sync_hook_registry.py
- [x] 4.13 test_hooks.py structural validation script (JSON validity, required fields, event types, patterns, registry consistency)

## Task 5: Platform and Language Support

- [x] 5.1 Cross-platform preflight.py (Linux, macOS, Windows)
- [x] 5.2 Windows-specific: VS Build Tools check, npm.cmd detection, PowerShell guidance, Windows Terminal recommendation
- [x] 5.3 5 language steering files with SDK best practices (Python, Java, C#, Rust, TypeScript)
- [x] 5.4 MCP-driven language selection during onboarding with platform warnings
- [x] 5.5 Language switching support mid-bootcamp
- [x] 5.6 Multi-language project support (load language file for current edit context)

## Task 6: Deployment Platform Support

- [x] 6.1 deployment-aws.md: ECS/Fargate, RDS, Secrets Manager, CloudWatch, IAM, cost optimization
- [x] 6.2 deployment-azure.md: ACI/AKS, Azure DB for PostgreSQL, Key Vault, Azure Monitor
- [x] 6.3 deployment-gcp.md: Cloud Run/GKE, Cloud SQL, Secret Manager, Cloud Monitoring
- [x] 6.4 deployment-kubernetes.md: Helm charts, StatefulSets, ConfigMaps, Ingress
- [x] 6.5 deployment-onpremises.md: Docker Compose, systemd, bare-metal PostgreSQL

## Task 7: Automation Scripts (30)

- [x] 7.1 Core: status.py (with --graph flag), validate_module.py (with --artifacts flag), preflight.py (with --mcp flag), install_hooks.py
- [x] 7.2 Backup/restore: backup_project.py, restore_project.py, rollback_module.py (with --preview/--yes flags)
- [x] 7.3 Validation: validate_power.py, validate_commonmark.py, validate_data_files.py, validate_dependencies.py
- [x] 7.4 Steering: measure_steering.py (with --simulate flag), lint_steering.py, split_steering.py, sync_hook_registry.py
- [x] 7.5 Team: team_dashboard.py, team_config_validator.py, merge_feedback.py
- [x] 7.6 Analytics: session_logger.py, analyze_sessions.py (with classify_pacing), triage_feedback.py
- [x] 7.7 Utilities: data_sources.py, export_results.py (with achievements section), repair_progress.py, verbosity.py, check_prerequisites.py
- [x] 7.8 New tools: test_hooks.py (hook structural validation), visualize_dependencies.py (ASCII + Mermaid dependency graph)

## Task 8: Testing (98 test files)

- [x] 8.1 Property-based tests (Hypothesis) for scripts: validate_module, steering structure, hook prompts, data validation, checkpointing, adaptive pacing, session analytics
- [x] 8.2 Unit tests for all scripts
- [x] 8.3 Integration test for module flow across all tracks (test_module_flow_integration.py)
- [x] 8.4 Hook prompt standards tests (JSON structure, registry sync, silent processing, no closing questions)
- [x] 8.5 Repo-level tests in `tests/` for hook file validation
- [x] 8.6 CI pipeline: validate_power.py + measure_steering.py + validate_commonmark.py + sync_hook_registry.py + pytest
- [x] 8.7 Feature-specific tests: adaptive pacing, context budget, hook self-test, rollback preview, where-am-i status, feedback loop closure, module completion certificates, MCP health check, language troubleshooting, module dependency visualization, artifact dependency tracking

## Task 9: Documentation

- [x] 9.1 POWER.md with full module table, track descriptions, MCP tool reference, useful commands
- [x] 9.2 CHANGELOG.md in Keep a Changelog format
- [x] 9.3 24 user guides in docs/guides/ (including MODULE_ARTIFACTS.md, INCREMENTAL_LOADING.md)
- [x] 9.4 5 policy documents in docs/policies/
- [x] 9.5 Architecture diagrams in docs/diagrams/
- [x] 9.6 Templates in templates/ (data collection checklist, stakeholder summary, transformation lineage, UAT test cases, lessons learned)
- [x] 9.7 SCRIPT_REFERENCE.md with categorized script inventory, validation hierarchy, See Also cross-references, and library markers
