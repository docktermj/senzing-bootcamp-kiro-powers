---
name: "senzing-bootcamp"
displayName: "Senzing Bootcamp"
version: "0.12.0"
description: "Guided 11-module bootcamp for learning Senzing entity resolution, from first demo to production deployment."
keywords: ["senzing", "bootcamp", "entity-resolution", "senzing-bootcamp", "learning-track"]
author: "Senzing"
---

# Senzing Bootcamp

## Overview

This power provides a guided bootcamp for learning Senzing entity resolution through a structured 11-module curriculum (Modules 1-11). It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

**The Senzing MCP server is required for the bootcamp to function.** The server generates SDK code, looks up Senzing facts, provides working examples, and powers interactive mapping workflows. The bootcamp cannot proceed without an active MCP connection.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

This power works best with Claude Opus 4.6 or similar.

## What's New in 0.12.0

- Production-readiness pass: all CI validation steps green (`validate_power`, `measure_steering --check`, `validate_commonmark`, `validate_dependencies`, `sync_hook_registry --verify`, `validate_prerequisites`, `validate_progress_ci`); pytest at 2,603 passed / 0 failed / 0 errors
- CommonMark compliance across all 491 markdown files — `.markdownlint.json` tuned for Kiro `#[[file:...]]` include syntax; `sync_hook_registry.py` now wraps hook prompts in four-backtick `text` fences so nested code blocks render cleanly
- Consolidated visualization steering: merged visualization-protocol and visualization-reference into `visualization-guide.md` (saves ~3,000 tokens of context budget)
- User-state config files (`bootcamp_progress.json`, `bootcamp_preferences.yaml`, `er_baseline_vendors.json`) no longer tracked in git — `.example` templates provided instead
- Hook count reconciled to 28 (consolidated `enforce-file-path-policies`, `enforce-single-question`, and `block-direct-sql` into `write-policy-gate`; added `enforce-mandatory-gate` and `enforce-gate-on-stop` to documentation)

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
| 5 — Data Quality & Mapping              | Scores data quality, then transforms your data into Senzing Entity Specification format. Optional Phase 3 test-loads and evaluates results using `mapping_workflow` steps 5–8 | Identifies issues before they cause bad matches, gets data into the format Senzing needs, and optionally validates entity resolution quality before production loading |
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

**Experienced users:** Skip to Module 5 (have Entity Specification data), Module 6 (SDK + data ready), or Module 7 (data loaded).

## Relationship to Senzing Power

This bootcamp complements the optional **senzing** Kiro Power. Both connect to the same MCP server. Use this power for structured learning; use the senzing power for quick reference and troubleshooting.

## Available Steering Files

See `steering/steering-index.yaml` for the complete machine-readable index of all steering files with token counts and keyword routing. Key files loaded automatically: `agent-instructions.md`, `module-transitions.md`, `security-privacy.md`.

**Context budget thresholds:**

- **60% warn (120k tokens loaded):** The agent loads only files directly relevant to the current module or user question. Supplementary files are deferred.
- **80% critical (160k tokens loaded):** The agent unloads non-essential files before loading new ones, following the retention priority: agent-instructions → current module → language file → troubleshooting → everything else.

**Module Workflows (load the one you need):**

- `module-01-business-problem.md` — Module 1: Business Problem (split: `module-01-phase2-document-confirm.md`)
- `module-02-sdk-setup.md` — Module 2: SDK Setup
- `module-03-system-verification.md` — Module 3: System Verification (split: `module-03-phase2-visualization.md`)
- `module-04-data-collection.md` — Module 4: Data Collection
- `module-05-data-quality-mapping.md` — Module 5: Data Quality & Mapping
- `module-06-data-processing.md` — Module 6: Data Processing
- `module-07-query-visualize-discover.md` — Module 7: Query, Visualize, and Discover
- `module-08-performance.md` — Module 8: Performance Testing
- `module-09-security.md` — Module 9: Security Hardening
- `module-10-monitoring.md` — Module 10: Monitoring
- `module-11-deployment.md` — Module 11: Deployment (split: `module-11-phase2-deploy.md`)

## MCP Server Configuration

Connects to the Senzing MCP server (no API keys required):

```json
{
  "mcpServers": {
    "senzing-mcp-server": {
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

- `get_capabilities` — Discover all tools and workflows
- `mapping_workflow` — Interactive 8-step data mapping to Senzing JSON
- `generate_scaffold` — Generate SDK code (Python, Java, C#, Rust, TypeScript)
- `get_sample_data` — Download sample datasets (Las Vegas, London, Moscow)
- `search_docs` — Search indexed Senzing documentation
- `explain_error_code` — Diagnose Senzing errors (456 error codes)
- `analyze_record` — Analyze and validate mapped data against the Senzing Entity Specification
- `sdk_guide` — Platform-specific SDK installation and setup
- `find_examples` — Working code from 27 Senzing GitHub repositories
- `get_sdk_reference` — SDK method signatures and flags
- `reporting_guide` — Reporting, visualization, and dashboard guidance
- `download_resource` — Download workflow resources (entity spec, analyzer script)
- `submit_feedback` — Report issues or suggestions

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

Modules are progressive but iterative. Skip ahead options: have Entity Specification data (skip to 6), not deploying to production (skip 8-11). Modules 8-11 are production-focused and optional for learning/evaluation.

The goal is for you to finish the bootcamp with running code that is the basis of your real-world use of Senzing.

## Code Generation

All code templates are generated dynamically by the Senzing MCP server using `generate_scaffold`, `sdk_guide`, and `mapping_workflow` in your chosen programming language. No static templates are shipped — this ensures generated code always matches the current SDK version and follows current best practices.

> **Note:** The depth of supplementary example coverage (via `find_examples`) varies across languages — Python and Java currently have the most extensive example coverage. This does not affect `generate_scaffold` or `sdk_guide` output quality, which produce equivalent results for all supported languages.

## Code Quality Standards

All generated code follows language-appropriate coding standards based on the bootcamper's chosen language. The bootcamp supports Python, Java, C#, Rust, and TypeScript/Node.js — the agent queries the Senzing MCP server for the current list and asks the bootcamper to choose at the start. See `docs/policies/CODE_QUALITY_STANDARDS.md`.

## Recommended Hooks

Install pre-configured hooks for automated quality checks:

```console
python3 senzing-bootcamp/scripts/install_hooks.py
```

Or manually copy hook files into `.kiro/hooks/`.

Available (28 hooks): `ask-bootcamper` ⭐, `review-bootcamper-input` ⭐, `code-style-check` ⭐, `commonmark-validation` ⭐, `write-policy-gate` ⭐, `question-format-gate` ⭐, `enforce-visualization-offers`, `gate-module3-visualization`, `enforce-gate-on-stop`, `enforce-mandatory-gate`, `validate-business-problem`, `verify-sdk-setup`, `verify-demo-results`, `validate-data-files`, `data-quality-check`, `analyze-after-mapping`, `enforce-mapping-spec`, `backup-before-load`, `run-tests-after-change`, `verify-generated-code`, `validate-benchmark-results`, `security-scan-on-save`, `validate-alert-config`, `deployment-phase-gate`, `backup-project-on-request`, `error-recovery-context`, `git-commit-reminder`, `module-completion-celebration`.

## Project Directory Structure

The agent creates an organized directory structure in the bootcamper's working directory at bootcamp start. Key directories: `data/`, `database/`, `src/`, `docs/`, `config/`, `logs/`, `monitoring/`. During Module 4 the agent creates `config/data_sources.yaml` in the bootcamper's project — a registry tracking each data source's quality, mapping, and load status across modules. Load `project-structure.md` for details.

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

- Support: <support@senzing.com> / <https://senzing.com/support/>
- Sales: <sales@senzing.com> / <https://senzing.com/contact/>
- Docs: <https://docs.senzing.com>
