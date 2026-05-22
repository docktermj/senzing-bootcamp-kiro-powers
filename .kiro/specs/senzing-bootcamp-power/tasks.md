# Tasks

This spec documents the power as-built (v0.12.0). All tasks reflect implemented state.

## Task 1: Core Curriculum (11 Modules)

- [x] 1.1 Module 1 (Business Problem): steering file with 2 phases, gate criteria (problem documented, sources identified)
- [x] 1.2 Module 2 (SDK Setup): steering file, preflight verification, license handling, EULA gate
- [x] 1.3 Module 3 (System Verification): steering file with 2 phases (verification, visualization), TruthSet data, MCP-generated verification code, mandatory visualization gate
- [x] 1.4 Module 4 (Data Collection): steering file, data file validation hook, collection checklist template
- [x] 1.5 Module 5 (Data Quality & Mapping): steering file with 3 phases, quality scoring, mapping workflow integration, enforce-mapping-spec hook
- [x] 1.6 Module 6 (Data Processing): steering file with 4 phases, loading program generation, redo processing, multi-source orchestration
- [x] 1.7 Module 7 (Query, Visualize, and Discover): steering file, query program generation, entity graph visualization, results dashboard, integration patterns
- [x] 1.8 Module 8 (Performance Testing & Benchmarking): steering file with 3 phases, benchmark scripts, database tuning, scalability testing
- [x] 1.9 Module 9 (Security Hardening): steering file with 2 phases, secrets management, RBAC, vulnerability scanning, security checklist
- [x] 1.10 Module 10 (Monitoring & Observability): steering file with 2 phases, metrics collection, dashboards, alerts, runbooks, health checks
- [x] 1.11 Module 11 (Package & Deploy): steering file with 2 phases, containerization, CI/CD, deployment phase gate, 5 platform reference files

## Task 2: Learning Tracks and Navigation

- [x] 2.1 Two tracks defined: Core Bootcamp (Modules 1–7, recommended), Advanced Topics (Modules 1–11, not recommended for bootcamp)
- [x] 2.2 Module 2 auto-insertion before SDK-dependent modules
- [x] 2.3 Module dependency graph in `config/module-dependencies.yaml` with gates and skip conditions
- [x] 2.4 Validation gates between all module transitions
- [x] 2.5 Track switching with completed modules carrying forward
- [x] 2.6 Skip Step Protocol for step-level skips within modules (mandatory gates cannot be skipped)
- [x] 2.7 Graduation workflow at track completion
- [x] 2.8 Experienced user skip-ahead (to Module 5, 6, or 7)

## Task 3: Steering System (79 files)

- [x] 3.1 Always-on files (3): agent-instructions (140 lines), module-transitions (84 lines), security-privacy (27 lines)
- [x] 3.2 Auto files (7): agent-context-management, conversation-protocol, design-patterns, module-prerequisites, project-structure, session-resume, verbosity-control
- [x] 3.3 FileMatch files (5): language steering files with SDK best practices and troubleshooting (~105 lines each)
- [x] 3.4 Manual files (65): module workflows, deployment, troubleshooting, visualization, mcp-usage-reference, conversation-examples, etc.
- [x] 3.5 steering-index.yaml with token counts, size categories, phase maps, keyword routing, deployment mapping, budget section
- [x] 3.6 Context budget tracking with percentage-based 60%/80% thresholds and retention priority (in agent-context-management.md)
- [x] 3.7 Consolidated visualization steering: visualization-guide.md (protocol + reference merged) + visualization-web-service.md

## Task 4: Hook System (28 hooks)

- [x] 4.1 7 critical hooks created during onboarding: ask-bootcamper, block-direct-sql, review-bootcamper-input, code-style-check, commonmark-validation, enforce-file-path-policies, enforce-single-question
- [x] 4.2 Module 1 hook: validate-business-problem
- [x] 4.3 Module 2 hook: verify-sdk-setup
- [x] 4.4 Module 3 hooks: enforce-mandatory-gate, enforce-visualization-offers, gate-module3-visualization, verify-demo-results
- [x] 4.5 Module 4 hook: validate-data-files
- [x] 4.6 Module 5 hooks: analyze-after-mapping, data-quality-check, enforce-mapping-spec, enforce-visualization-offers
- [x] 4.7 Module 6 hooks: backup-before-load, run-tests-after-change, verify-generated-code
- [x] 4.8 Module 7 hook: enforce-visualization-offers
- [x] 4.9 Module 8 hooks: enforce-visualization-offers, validate-benchmark-results
- [x] 4.10 Module 9 hook: security-scan-on-save
- [x] 4.11 Module 10 hook: validate-alert-config
- [x] 4.12 Module 11 hook: deployment-phase-gate
- [x] 4.13 Any-module hooks: backup-project-on-request, error-recovery-context, git-commit-reminder, module-completion-celebration
- [x] 4.14 hook-categories.yaml, hook-registry.md, and hook-registry-detail.md kept in sync via sync_hook_registry.py
- [x] 4.15 tests/test_hook_structural_validation.py for structural validation (JSON validity, required fields, event types, patterns, registry consistency)

## Task 5: Platform and Language Support

- [x] 5.1 Cross-platform preflight.py (Linux, macOS, Windows) with Scoop detection, VS Build Tools, npm.cmd
- [x] 5.2 Windows-specific: Scoop installation offer (Step 3a), runtime installation via Scoop (Step 3b), PowerShell guidance, Windows Terminal recommendation
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

## Task 7: Automation Scripts (40)

- [x] 7.1 Core: status.py, validate_module.py, preflight.py (with --mcp, --json, --fix flags), install_hooks.py
- [x] 7.2 Backup/restore: backup_project.py, restore_project.py, rollback_module.py
- [x] 7.3 Validation: validate_power.py, validate_commonmark.py, validate_data_files.py, validate_dependencies.py, validate_prerequisites.py, validate_progress_ci.py, validate_mandatory_gates.py
- [x] 7.4 Steering: measure_steering.py (with --check and --simulate flags), lint_steering.py, split_steering.py, sync_hook_registry.py (with --verify and --write flags)
- [x] 7.5 Team: team_dashboard.py, team_config_validator.py, merge_feedback.py
- [x] 7.6 Analytics: session_logger.py, analyze_sessions.py, bootcamp_analytics.py, triage_feedback.py
- [x] 7.7 Utilities: data_sources.py, export_results.py, repair_progress.py, verbosity.py, compare_results.py, track_switcher.py

## Task 8: Testing (177 test files)

- [x] 8.1 Property-based tests (Hypothesis) for scripts: validate_module, steering structure, hook prompts, data validation, checkpointing, adaptive pacing, session analytics
- [x] 8.2 Unit tests for all scripts in senzing-bootcamp/tests/ (151 files)
- [x] 8.3 Repo-level tests in tests/ (26 files) for hook file validation, visualization consistency, enforce-visualization-offers modules
- [x] 8.4 Integration test for module flow across all tracks (test_module_flow_integration.py)
- [x] 8.5 Hook structural validation tests (JSON structure, registry sync, silent processing, prompt logic)
- [x] 8.6 CI pipeline: validate_power + measure_steering + validate_commonmark + validate_dependencies + sync_hook_registry + validate_prerequisites + validate_progress_ci + validate_mandatory_gates + pytest

## Task 9: Documentation

- [x] 9.1 POWER.md with module table, track descriptions, MCP tool reference, useful commands, troubleshooting
- [x] 9.2 CHANGELOG.md in Keep a Changelog format (versions 0.2.0 through 0.12.0)
- [x] 9.3 19 user guides in docs/guides/
- [x] 9.4 4 policy documents in docs/policies/ (CODE_QUALITY_STANDARDS, FILE_STORAGE_POLICY, SENZING_INFORMATION_POLICY, DEPENDENCY_MANAGEMENT_POLICY)
- [x] 9.5 Architecture diagrams in docs/diagrams/ (module-flow, data-flow, system-architecture, module-prerequisites)
- [x] 9.6 Templates in templates/ (data collection checklist, stakeholder summary, transformation lineage, UAT test cases, lessons learned, team.yaml.example, module-steering-template)
- [x] 9.7 hooks/README.md with full hook documentation, installation options, and per-module recommendations
