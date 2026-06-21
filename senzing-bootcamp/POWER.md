---
name: "senzing-bootcamp"
displayName: "Senzing Bootcamp"
version: "0.12.1"
description: "Guided 11-module bootcamp for learning Senzing entity resolution, from first demo to production deployment."
keywords: ["senzing", "bootcamp", "entity-resolution", "senzing-bootcamp", "learning-track"]
author: "Senzing"
---

# Senzing Bootcamp

## Overview

This power provides a guided bootcamp for learning Senzing entity resolution through a structured 11-module curriculum (Modules 1-11). It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

**The Senzing MCP server is required for the bootcamp to function.** The server generates SDK code, looks up Senzing facts, provides working examples, and powers interactive mapping workflows. The bootcamp cannot proceed without an active MCP connection.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

This power works best with Claude Opus 4.8 or similar.

## What's New in 0.12.1

- "Lint Python (ruff)" CI gate brought from 438 violations to 0 — the full CI suite is now green, with pytest at 4,868 passed / 0 failed
- Fixed 3 correctness defects the ruff gate surfaced: two duplicate test functions that silently shadowed earlier definitions, and a duplicate dict key that dropped a fixture entry
- Style-only ruff remediation (long-line reflow, import-order suppression for the documented `sys.path` pattern, unused-variable/whitespace cleanup, ambiguous-name renames) with no runtime behavior change to any script
- External-link checking (`validate_links.py`) wired into the CI gate sequence

## What's New in 0.12.0

- Production-readiness pass: CI validation steps green (`validate_power`, `measure_steering --check`, `validate_commonmark`, `validate_dependencies`, `sync_hook_registry --verify`, `validate_prerequisites`, `validate_progress_ci`); pytest at 4,830 passed / 0 failed / 0 errors
- CommonMark compliance across all shipped markdown files — `.markdownlint.json` tuned for Kiro `#[[file:...]]` include syntax; `sync_hook_registry.py` now wraps hook prompts in four-backtick `text` fences so nested code blocks render cleanly
- Consolidated visualization steering: merged visualization-protocol and visualization-reference into `visualization-guide.md` (saves ~3,000 tokens of context budget)
- User-state config files (`bootcamp_progress.json`, `bootcamp_preferences.yaml`, `er_baseline_vendors.json`) no longer tracked in git — `.example` templates provided instead
- Hook count reconciled to 29 (consolidated `enforce-file-path-policies`, `enforce-single-question`, and `block-direct-sql` into `write-policy-gate`; added `enforce-mandatory-gate`, `enforce-gate-on-stop`, and `session-log-events` to documentation)

See the CHANGELOG for the full release history.

## What This Bootcamp Does

This bootcamp is a guided discovery of how to use Senzing for entity resolution. Feel free to take it slow, read what the bootcamp is telling you, and ask questions at any point — that's what it's here for.

The purpose is to make you comfortable writing code — with Kiro's help — that uses the Senzing SDK. By the end, you'll have running code that serves as the foundation for your real-world use of Senzing.

The bootcamp is a series of modules. Each module builds on the previous ones, producing working artifacts (code, data files, documentation) that you keep and extend. Here's what each module does and why it matters:

| Module                                  | What It Does                                                              | Why It Matters                                                                                                   |
|-----------------------------------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| 1 — Business Problem                    | Defines what you're trying to solve and which data sources matter         | Focuses the rest of the bootcamp on your actual use case                                                         |
| 2 — SDK Setup                           | Installs and configures the Senzing SDK on your machine                   | Everything else depends on a working SDK installation                                                            |
| 3 — System Verification                 | Runs entity resolution on Senzing TruthSet data and verifies expected entity counts | Validates your entire setup end-to-end against a known-good reference dataset — proving the system works before you use your own data |
| 4 — Data Collection                     | Gets your data files into the project                                     | You can't resolve entities without data to work with                                                             |
| 5 — Data Quality & Mapping              | Scores data quality, then transforms your data into Senzing Generic Entity Specification (SGES) format. Optional Phase 3 test-loads and evaluates results using `mapping_workflow` steps 5–8 | Identifies issues before they cause bad matches, gets data into the format Senzing needs, and optionally validates entity resolution quality before production loading |
| 6 — Data Processing                     | Loads all data sources, processes redo records, and validates entity resolution results | Your data is loaded and entity resolution is running — duplicates matched, cross-source connections found |
| 7 — Query, Visualize, and Discover       | Builds query programs and visualizations for your resolved entities       | Proves the system answers your business questions                                                                |
| 8 — Performance Testing & Benchmarking  | Benchmarks and optimizes for your data volume                             | Ensures the system handles production-scale data                                                                 |
| 9 — Security Hardening                  | Implements access controls and data protection                            | Required for production with sensitive data                                                                      |
| 10 — Monitoring & Observability         | Sets up dashboards, alerts, and health checks                             | Keeps the system running reliably in production                                                                  |
| 11 — Package & Deploy                   | Packages everything for production deployment                             | Gets your solution out of the bootcamp and into the real world                                                   |

**Don't have data handy?** No problem — Senzing provides [CORD (Collections Of Relatable Data)](https://senzing.com/senzing-ready-data-collections-cord/), curated real-world-like datasets designed specifically for entity resolution evaluation. CORD includes three ready-made datasets — Las Vegas, London, and Moscow — that you can use throughout the bootcamp. Use `get_sample_data` to download them. If CORD data doesn't meet your specific needs, test data can also be generated at any point as a fallback.

**Licensing:** Senzing includes a built-in evaluation license that allows 500 records, which is enough for the bootcamp. If you have your own license (or need more capacity), you can configure it during Module 2.

## Quick Start

**New users:** Say "start the bootcamp" to begin. Choose your track:

- **Core Bootcamp** *(recommended)* — Modules 1, 2, 3, 4, 5, 6, 7. Recommended foundation covering problem definition through query, visualize, and discover.
- **Advanced Topics** *(not recommended for bootcamp)* — Modules 1–11. Adds production-readiness topics (performance, security hardening, monitoring, and packaging/deployment) as advanced add-ons layered on top of the core bootcamp.

Tracks are not mutually exclusive — you can start with one and extend to another at any time. All completed modules carry forward.

Module 2 (SDK Setup) is inserted automatically before any module that needs it.

After completing any track, the agent offers a **graduation workflow** that transitions your bootcamp project into a production-ready codebase — clean directory structure, production configs, CI/CD pipeline, and a migration checklist. Say "run graduation" or "graduate" at any time to start it manually.

**Experienced users:** Skip to Module 5 (have Senzing Generic Entity Specification (SGES) data), Module 6 (SDK + data ready), or Module 7 (data loaded).

## Relationship to Senzing Power

This bootcamp complements the optional **senzing** Kiro Power. Both connect to the same MCP server. Use this power for structured learning; use the senzing power for quick reference and troubleshooting.

## Available Steering Files

See `steering/steering-index.yaml` for the complete machine-readable index of all steering files with token counts and keyword routing. Key files loaded automatically: `agent-instructions.md`, `module-transitions.md`, `security-privacy.md`.

**Context budget thresholds:**

- **60% warn (120k tokens loaded):** The agent loads only files directly relevant to the current module or user question. Supplementary files are deferred.
- **80% critical (160k tokens loaded):** The agent unloads non-essential files before loading new ones, following the retention priority: agent-instructions → current module → language file → troubleshooting → everything else.

**Module Workflows (load the one you need):**

- `module-01-business-problem.md` — Module 1: Business Problem (split: `module-01-phase1-discovery.md`, `module-01-phase2-document-confirm.md`)
- `module-02-sdk-setup.md` — Module 2: SDK Setup
- `module-03-system-verification.md` — Module 3: System Verification (split: `module-03-phase1-verification.md`, `module-03-phase2-visualization.md`, `module-03-phase3-report-close.md`)
- `module-04-data-collection.md` — Module 4: Data Collection
- `module-05-data-quality-mapping.md` — Module 5: Data Quality & Mapping (split: `module-05-phase1-quality-assessment.md`, `module-05-phase2-data-mapping.md`, `module-05-phase3-test-load.md`)
- `module-06-data-processing.md` — Module 6: Data Processing (split: `module-06-phaseA-build-loading.md`, `module-06-phaseB-load-first-source.md`, `module-06-phaseC-multi-source.md`, `module-06-phaseD-validation.md`)
- `module-07-query-visualize-discover.md` — Module 7: Query, Visualize, and Discover (split: `module-07-phase1-query-visualize.md`, `module-07-phase2-discover.md`, `module-07-phase2b-discover.md`)
- `module-08-performance.md` — Module 8: Performance Testing (split: `module-08-phaseA-requirements.md`, `module-08-phaseB-benchmarking.md`, `module-08-phaseC-optimization.md`)
- `module-09-security.md` — Module 9: Security Hardening (split: `module-09-phaseA-assessment.md`, `module-09-phaseB-hardening.md`)
- `module-10-monitoring.md` — Module 10: Monitoring (split: `module-10-phaseA-setup.md`, `module-10-phaseB-operations.md`)
- `module-11-deployment.md` — Module 11: Deployment (split: `module-11-phase1-packaging.md`, `module-11-phase2-deploy.md`)

<!-- BEGIN GENERATED: steering-files -->

| Steering File | Tokens | Size |
|---|---|---|
| `agent-behavior-rules.md` | 760 | medium |
| `agent-context-management.md` | 1326 | medium |
| `agent-instructions.md` | 4815 | large |
| `cloud-provider-setup.md` | 784 | medium |
| `common-pitfalls.md` | 4612 | large |
| `completion-summary-offer.md` | 1867 | medium |
| `complexity-estimator.md` | 606 | medium |
| `conversation-examples.md` | 536 | medium |
| `conversation-protocol.md` | 4022 | large |
| `data-lineage.md` | 603 | medium |
| `data-processing-reference.md` | 1174 | medium |
| `deployment-aws.md` | 1323 | medium |
| `deployment-azure.md` | 965 | medium |
| `deployment-gcp.md` | 956 | medium |
| `deployment-kubernetes.md` | 1397 | medium |
| `deployment-onpremises.md` | 952 | medium |
| `design-patterns.md` | 749 | medium |
| `entity-resolution-intro.md` | 1864 | medium |
| `environment-setup.md` | 658 | medium |
| `feedback-workflow.md` | 1239 | medium |
| `graduation.md` | 3584 | large |
| `hook-architecture.md` | 2149 | large |
| `hook-registry-critical.md` | 8517 | large |
| `hook-registry-module-01.md` | 474 | small |
| `hook-registry-module-02.md` | 261 | small |
| `hook-registry-module-03.md` | 2341 | large |
| `hook-registry-module-04.md` | 282 | small |
| `hook-registry-module-05.md` | 1390 | medium |
| `hook-registry-module-06.md` | 519 | medium |
| `hook-registry-module-07.md` | 544 | medium |
| `hook-registry-module-08.md` | 760 | medium |
| `hook-registry-module-09.md` | 268 | small |
| `hook-registry-module-10.md` | 286 | small |
| `hook-registry-module-11.md` | 463 | small |
| `hook-registry-module-any.md` | 3846 | large |
| `hook-registry.md` | 1914 | medium |
| `inline-status.md` | 460 | small |
| `lang-csharp.md` | 1642 | medium |
| `lang-java.md` | 1688 | medium |
| `lang-python.md` | 1655 | medium |
| `lang-rust.md` | 1698 | medium |
| `lang-typescript.md` | 1887 | medium |
| `lessons-learned.md` | 434 | small |
| `mcp-response-caching.md` | 1442 | medium |
| `mcp-tool-decision-tree.md` | 2310 | large |
| `mcp-usage-reference.md` | 580 | medium |
| `module-01-business-problem.md` | 500 | medium |
| `module-01-phase1-discovery.md` | 5027 | large |
| `module-01-phase2-document-confirm.md` | 1853 | medium |
| `module-02-sdk-setup.md` | 4491 | large |
| `module-03-phase1-verification.md` | 3536 | large |
| `module-03-phase2-visualization.md` | 4411 | large |
| `module-03-phase3-report-close.md` | 1751 | medium |
| `module-03-system-verification.md` | 604 | medium |
| `module-03-visualization-api-reference.md` | 1711 | medium |
| `module-04-data-collection.md` | 3460 | large |
| `module-05-data-quality-mapping.md` | 689 | medium |
| `module-05-phase1-quality-assessment.md` | 1710 | medium |
| `module-05-phase2-data-mapping.md` | 5355 | large |
| `module-05-phase3-test-load.md` | 2947 | large |
| `module-06-data-processing.md` | 652 | medium |
| `module-06-phaseA-build-loading.md` | 2034 | large |
| `module-06-phaseB-load-first-source.md` | 1193 | medium |
| `module-06-phaseC-multi-source.md` | 1428 | medium |
| `module-06-phaseD-validation.md` | 2109 | large |
| `module-07-phase1-query-visualize.md` | 3233 | large |
| `module-07-phase2-discover.md` | 3453 | large |
| `module-07-phase2b-discover.md` | 3174 | large |
| `module-07-query-visualize-discover.md` | 545 | medium |
| `module-08-performance.md` | 617 | medium |
| `module-08-phaseA-requirements.md` | 2169 | large |
| `module-08-phaseB-benchmarking.md` | 429 | small |
| `module-08-phaseC-optimization.md` | 746 | medium |
| `module-09-phaseA-assessment.md` | 1221 | medium |
| `module-09-phaseB-hardening.md` | 928 | medium |
| `module-09-security.md` | 571 | medium |
| `module-10-monitoring.md` | 568 | medium |
| `module-10-phaseA-setup.md` | 808 | medium |
| `module-10-phaseB-operations.md` | 451 | small |
| `module-11-deployment.md` | 479 | small |
| `module-11-phase1-packaging.md` | 2870 | large |
| `module-11-phase2-deploy.md` | 850 | medium |
| `module-completion-artifacts.md` | 2902 | large |
| `module-completion-error-handling.md` | 604 | medium |
| `module-completion-next-steps.md` | 555 | medium |
| `module-completion-track.md` | 1277 | medium |
| `module-completion.md` | 1163 | medium |
| `module-prerequisites.md` | 1344 | medium |
| `module-transitions.md` | 1534 | medium |
| `onboarding-flow.md` | 3866 | large |
| `onboarding-phase1b-intro-language.md` | 2055 | large |
| `onboarding-phase2-track-setup.md` | 991 | medium |
| `phase-loading-guide.md` | 890 | medium |
| `project-structure.md` | 764 | medium |
| `recovery-from-mistakes.md` | 1227 | medium |
| `security-privacy.md` | 278 | small |
| `session-resume-phase2-mapping.md` | 656 | medium |
| `session-resume-phase2-setup-recovery.md` | 997 | medium |
| `session-resume-phase2-state-repair.md` | 547 | medium |
| `session-resume.md` | 3380 | large |
| `skip-step-protocol.md` | 799 | medium |
| `track-switching.md` | 766 | medium |
| `troubleshooting-commands.md` | 672 | medium |
| `troubleshooting-decision-tree.md` | 1606 | medium |
| `uat-framework.md` | 576 | medium |
| `verbosity-control.md` | 2048 | large |
| `visualization-guide.md` | 4334 | large |
| `visualization-web-service.md` | 2195 | large |
| `whats-new.md` | 602 | medium |

**Total budget:** 179803 tokens

<!-- END GENERATED: steering-files -->

## MCP Server Configuration

Connects to the Senzing MCP server (no API keys required):

```json
{
  "mcpServers": {
    "senzing-mcp-server": {
      "type": "http",
      "url": "https://mcp.senzing.com/mcp",
      "disabled": false,
      "autoApprove": [],
      "disabledTools": ["submit_feedback"]
    }
  }
}
```

**Server name:** `senzing-mcp-server`

All tools are enabled by default except `submit_feedback` (disabled to keep feedback local). To re-enable it or disable other tools, edit the `disabledTools` array. See <https://kiro.dev/docs/mcp/configuration/> for full configuration options.

## Available MCP Tools

Always call `get_capabilities` first when starting a session.

**Core tools:**

<!-- BEGIN GENERATED: mcp-tools -->

- `get_capabilities` — Discover all tools and workflows
- `mapping_workflow` — Interactive 8-step data mapping to Senzing JSON
- `analyze_record` — Analyze and validate mapped data against the Senzing Entity Specification
- `download_resource` — Download workflow resources (entity spec, analyzer script)
- `explain_error_code` — Diagnose Senzing errors (456 error codes)
- `search_docs` — Search indexed Senzing documentation
- `find_examples` — Working code from 27 Senzing GitHub repositories
- `generate_scaffold` — Generate SDK code (Python, Java, C#, Rust, TypeScript)
- `get_sample_data` — Download sample datasets (Las Vegas, London, Moscow)
- `get_sdk_reference` — SDK method signatures and flags
- `sdk_guide` — Platform-specific SDK installation and setup
- `reporting_guide` — Reporting, visualization, and dashboard guidance
- `submit_feedback` — Report issues or suggestions

<!-- END GENERATED: mcp-tools -->

**Key rules:**

- Never hand-code Senzing JSON mappings — use `mapping_workflow`
- Never guess SDK method signatures — use `generate_scaffold` or `sdk_guide`
- Use `search_docs` with category `anti_patterns` before recommending approaches

## Tool Usage Examples

Call `get_capabilities()` first to discover all tools. Key patterns:

```text
sdk_guide(topic='install', platform='linux', language='python', version='current')
generate_scaffold(language='java', workflow='add_records', version='current')
mapping_workflow(action='start', source_file='data/raw/customers.csv')
search_docs(query='loading performance', category='anti_patterns', version='current')
```

See `steering/mcp-tool-decision-tree.md` for the full decision tree with all tools and call examples.

## Module Progression

Modules are progressive but iterative. Skip ahead options: have Senzing Generic Entity Specification (SGES) data (skip to 6), not deploying to production (skip 8-11). Modules 8-11 are production-focused and optional for learning/evaluation.

**Module numbers are topic labels, not a strict running order.** SDK Setup (Module 2) is performed right before the first module that actually needs the SDK — that's System Verification (Module 3) if you run it, otherwise Data Processing (Module 6). In practice the Core path runs **1 → 4 → 5 → 2 → 6 → 7**: you define the problem, collect your data, and map it first, then install the SDK just before loading. The agent inserts Module 2 automatically at the right point, so you never have to track this yourself.

The goal is for you to finish the bootcamp with running code that is the basis of your real-world use of Senzing.

<!-- BEGIN GENERATED: modules -->

| # | Module |
|---|---|
| 1 | Business Problem |
| 2 | SDK Setup |
| 3 | System Verification |
| 4 | Data Collection |
| 5 | Data Quality & Mapping |
| 6 | Data Processing |
| 7 | Query, Visualize, and Discover |
| 8 | Performance Testing & Benchmarking |
| 9 | Security Hardening |
| 10 | Monitoring & Observability |
| 11 | Package & Deploy |

Total: 11 modules.

<!-- END GENERATED: modules -->

## Code Generation

All code templates are generated dynamically by the Senzing MCP server using `generate_scaffold`, `sdk_guide`, and `mapping_workflow` in your chosen programming language. No static templates are shipped — this ensures generated code always matches the current SDK version and follows current best practices.

> **Note:** The depth of supplementary example coverage (via `find_examples`) varies across languages — Python and Java currently have the most extensive example coverage. This does not affect `generate_scaffold` or `sdk_guide` output quality, which produce equivalent results for all supported languages.

<!-- BEGIN GENERATED: example-coverage -->

> **Note:** Based on the tracked coverage snapshot, `python` currently has the most extensive supplementary example coverage (availability observed via `find_examples`).
> This tracked coverage signal reflects supplementary example availability only.
> `generate_scaffold` and `sdk_guide` produce equivalent results for all supported languages.

<!-- END GENERATED: example-coverage -->

## Code Quality Standards

All generated code follows language-appropriate coding standards based on the bootcamper's chosen language. The bootcamp supports Python, Java, C#, Rust, and TypeScript/Node.js — the agent queries the Senzing MCP server for the current list and asks the bootcamper to choose at the start. See `docs/policies/CODE_QUALITY_STANDARDS.md`.

## Recommended Hooks

Install pre-configured hooks for automated quality checks:

```console
python3 senzing-bootcamp/scripts/install_hooks.py
```

Or manually copy hook files into `.kiro/hooks/`.

<!-- BEGIN GENERATED: hooks -->

Available (29 hooks): `ask-bootcamper` ⭐, `code-style-check` ⭐, `commonmark-validation` ⭐, `review-bootcamper-input` ⭐, `write-policy-gate` ⭐, `analyze-after-mapping`, `backup-before-load`, `backup-project-on-request`, `data-quality-check`, `deployment-phase-gate`, `enforce-gate-on-stop`, `enforce-mandatory-gate`, `enforce-mapping-spec`, `enforce-visualization-offers`, `error-recovery-context`, `gate-module3-visualization`, `git-commit-reminder`, `module-completion-celebration`, `module-recap-append`, `run-tests-after-change`, `security-scan-on-save`, `session-log-events`, `validate-alert-config`, `validate-benchmark-results`, `validate-business-problem`, `validate-data-files`, `verify-demo-results`, `verify-generated-code`, `verify-sdk-setup`.

<!-- END GENERATED: hooks -->

## Project Directory Structure

The agent creates an organized directory structure in the bootcamper's working directory at bootcamp start. Key directories: `data/`, `database/`, `src/`, `docs/`, `config/`, `logs/`, `monitoring/`. Module 1 initializes `config/data_sources.yaml` in the bootcamper's project from the data sources and matching criteria identified in the business problem, and Module 4 (Data Collection) populates each entry as sources are collected — a registry tracking each data source's quality, mapping, and load status across modules. Load `project-structure.md` for details.

## Entity Resolution Design Patterns

10 patterns available: Customer 360, Fraud Detection, Data Migration, Compliance Screening, Marketing Dedup, Patient Matching, Vendor MDM, Claims Fraud, KYC/Onboarding, Supply Chain. Load `design-patterns.md` for the full gallery.

## Troubleshooting

- Module stuck? Check `module-prerequisites.md`
- Error codes? Use `explain_error_code` tool
- Wrong attribute names? Use `mapping_workflow` (never guess)
- Wrong method signatures? Use `generate_scaffold` or `sdk_guide`
- MCP connection issues? Check internet/firewall for `mcp.senzing.com:443`
- MCP unreachable? Try these steps:
  1. Verify internet connectivity
  2. Test endpoint: `curl -s -o /dev/null -w "%{http_code}" https://mcp.senzing.com:443`
  3. If behind a corporate proxy, allowlist `mcp.senzing.com:443`
  4. Check DNS: `nslookup mcp.senzing.com`
  5. Restart the MCP connection in the Kiro Powers panel
- Visual diagnostic? Load `troubleshooting-decision-tree.md`

Additional resources: `docs/guides/FAQ.md`. For Senzing terminology and error codes, use MCP tools `search_docs` and `explain_error_code`.

## Providing Feedback

Say "power feedback" or "bootcamp feedback" at any time to document issues or suggestions. The agent will guide you through a structured feedback workflow. See `feedback-workflow.md` for details.

## Useful Commands

Common commands (run from project root):

```text
python3 senzing-bootcamp/scripts/status.py               # Check progress
python3 senzing-bootcamp/scripts/status.py --step        # Show step-level progress for the current module
python3 senzing-bootcamp/scripts/preflight.py             # Environment verification
python3 senzing-bootcamp/scripts/install_hooks.py         # Install hooks
python3 senzing-bootcamp/scripts/backup_project.py        # Backup project
python3 senzing-bootcamp/scripts/validate_power.py        # Validate power integrity
python3 senzing-bootcamp/scripts/measure_steering.py      # Update steering token counts
python3 senzing-bootcamp/scripts/bootcamp_analytics.py    # Session analytics
python3 senzing-bootcamp/scripts/bootcamp_analytics.py --compare  # With baseline comparison
python3 senzing-bootcamp/scripts/compare_results.py --baseline <file> --current <file>
  # Compare ER statistics before/after mapping changes (shows diff + quality assessment)
```

Use `python` instead of `python3` on Windows. For best results on Windows, use Windows Terminal or PowerShell 7 (`winget install Microsoft.WindowsTerminal`).

For the complete script reference with all flags and options, see `docs/guides/SCRIPT_REFERENCE.md`.

## Additional Resources

- FAQ: `docs/guides/FAQ.md`
- Quick Start: `docs/guides/QUICK_START.md`
- Collaboration Guide: `docs/guides/COLLABORATION_GUIDE.md`
- Module Flow Diagram: `docs/diagrams/module-flow.md` (text-based; use a Mermaid preview extension or paste into [mermaid.live](https://mermaid.live) to render)
- Data Flow Diagram: `docs/diagrams/data-flow.md` (text-based ASCII art, viewable in any editor)
- System Architecture: `docs/diagrams/system-architecture.md` (shows how SDK, database, programs, and optional layers fit together)
- Quality Scoring Methodology: `docs/guides/QUALITY_SCORING_METHODOLOGY.md`
- Performance Baselines: `docs/guides/PERFORMANCE_BASELINES.md`
- Templates: `templates/data_collection_checklist.md`, `templates/stakeholder_summary.md`, `templates/transformation_lineage.md`, `templates/uat_test_cases.md`, `templates/performance_report.md`, `templates/security_checklist.md`, `templates/monitoring_runbook.md`, `templates/deployment_plan.md`

## Senzing Contact Information

- Support: <support@senzing.com> / <https://senzing.com/contact/>
- Sales: <sales@senzing.com> / <https://senzing.com/contact/>
- Docs: <https://docs.senzing.com>
