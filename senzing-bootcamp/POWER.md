---
name: "senzing-bootcamp"
displayName: "Senzing Bootcamp"
description: "Guided 11-module bootcamp for learning Senzing entity resolution, from first demo to production deployment."
keywords: ["senzing", "bootcamp", "entity-resolution", "senzing-bootcamp", "learning-track"]
author: "Senzing"
---

# Senzing Bootcamp

## Overview

This power provides a guided bootcamp for learning Senzing entity resolution through a structured 11-module curriculum (Modules 1-11). It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

This power works best with Claude Opus 4.6 or similar.

## What's New in 0.10.0

- Data source registry — `config/data_sources.yaml` tracks every source's quality score, mapping status, and load status across Modules 4–6. The agent maintains it automatically; view it with `data_sources.py` or in `status.py` output.
- Team bootcamp mode — `config/team.yaml` enables multi-user sessions with per-member progress tracking, a team dashboard (`team_dashboard.py`), and consolidated feedback reports (`merge_feedback.py`). Supports both co-located (shared repo) and distributed (separate repos) setups. See `docs/guides/COLLABORATION_GUIDE.md` for details.
- Context budget tracking — `file_metadata` in `steering-index.yaml` provides per-file token counts and size categories so the agent can manage context window pressure. Use `measure_steering.py` to keep counts up to date.
- Interactive entity graph visualization — the agent guides bootcampers through building their own D3.js force-directed graph with entity detail panels, clustering, and search. Load `steering/visualization-guide.md` during Module 7.
- Progress repair tool (`scripts/repair_progress.py`) — reconstructs `bootcamp_progress.json` from project artifacts when state is corrupted.
- Steering file index (`steering/steering-index.yaml`) — machine-readable mapping for faster agent file selection.
- CI validation via GitHub Actions for power integrity, CommonMark, and tests.

## What This Bootcamp Does

This bootcamp is a guided discovery of how to use Senzing for entity resolution. Feel free to take it slow, read what the bootcamp is telling you, and ask questions at any point — that's what it's here for.

The purpose is to make you comfortable writing code — with Kiro's help — that uses the Senzing SDK. By the end, you'll have running code that serves as the foundation for your real-world use of Senzing.

The bootcamp is a series of modules. Each module builds on the previous ones, producing working artifacts (code, data files, documentation) that you keep and extend. Here's what each module does and why it matters:

| Module                                  | What It Does                                                              | Why It Matters                                                                                                   |
|-----------------------------------------|---------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| 1 — Business Problem                    | Defines what you're trying to solve and which data sources matter         | Focuses the rest of the bootcamp on your actual use case                                                         |
| 2 — SDK Setup                           | Installs and configures the Senzing SDK on your machine                   | Everything else depends on a working SDK installation                                                            |
| 3 — Quick Demo                          | Runs entity resolution on sample data so you can see it work              | Validates your entire setup end-to-end; the result is trivial on purpose — the point is proving the system works |
| 4 — Data Collection Policy              | Gets your data files into the project                                     | You can't resolve entities without data to work with                                                             |
| 5 — Data Quality & Mapping              | Scores data quality, then transforms your data into Senzing Entity Specification (SGES) format. Optional Phase 3 test-loads and evaluates results using `mapping_workflow` steps 5–8 | Identifies issues before they cause bad matches, gets data into the format Senzing needs, and optionally validates entity resolution quality before production loading |
| 6 — Load Data                           | Loads all data sources, processes redo records, and validates entity resolution results | Your data is loaded and entity resolution is running — duplicates matched, cross-source connections found |
| 7 — Query & Visualize                   | Builds query programs and visualizations for your resolved entities       | Proves the system answers your business questions                                                                |
| 8 — Performance Testing & Benchmarking  | Benchmarks and optimizes for your data volume                             | Ensures the system handles production-scale data                                                                 |
| 9 — Security Hardening                  | Implements access controls and data protection                            | Required for production with sensitive data                                                                      |
| 10 — Monitoring & Observability         | Sets up dashboards, alerts, and health checks                             | Keeps the system running reliably in production                                                                  |
| 11 — Package & Deploy                   | Packages everything for production deployment                             | Gets your solution out of the bootcamp and into the real world                                                   |

**Don't have data handy?** No problem — mock data can be generated at any point. Senzing also provides three ready-made sample datasets you can use throughout the bootcamp: Las Vegas, London, and Moscow. Use `get_sample_data` to download them.

**Licensing:** Senzing includes a built-in evaluation license that allows 500 records, which is enough for the bootcamp. If you have your own license (or need more capacity), you can configure it during Module 2.

## Quick Start

**New users:** Say "start the bootcamp" to begin. Choose your track:

- **A) Quick Demo** — Modules 1 → 2 → 3. See entity resolution in action with sample data. Done in one session. Choose this if you want to verify the technology works before investing more time.
- **B) Fast Track** — Modules 5 → 6 → 7 (Module 2 inserted automatically). For users who already have Senzing-ready Entity Specification data. Choose this if you've already mapped your data and want to get straight to loading and querying. If you complete Module 5's optional Phase 3 (test load and validate) and have a simple use case, you can take the shortcut path directly to Module 7.
- **C) Complete Beginner** — Modules 1 → 4 → 5 → 6 → 7. Full learning track from defining the problem through validating results. Choose this if you're starting from scratch with raw data and want guided help through the entire process. Simple use cases can take the Phase 3 shortcut path from Module 5 directly to Module 7, skipping Module 6.
- **D) Full Production** — All modules 1-11, including performance testing, security, monitoring, and deployment. Choose this if you're building something that needs to run in production.

Tracks are not mutually exclusive — you can start with one and jump to another at any time. For example, start with Track A to see a quick demo, then switch to Track C to work with your own data. All completed modules carry forward.

Module 2 (SDK Setup) is inserted automatically before any module that needs it.

After completing any track, the agent offers a **graduation workflow** that transitions your bootcamp project into a production-ready codebase — clean directory structure, production configs, CI/CD pipeline, and a migration checklist. Say "run graduation" or "graduate" at any time to start it manually.

**Experienced users:** Skip to Module 5 (have Entity Specification data), Module 6 (SDK + data ready), or Module 7 (data loaded).

## Relationship to Senzing Power

This bootcamp complements the optional **senzing** Kiro Power. Both connect to the same MCP server. Use this power for structured learning; use the senzing power for quick reference and troubleshooting.

## Available Steering Files

Load these on-demand when needed. Each file in `steering-index.yaml` includes a `token_count` and `size_category` (`small`, `medium`, or `large`) so the agent can assess context cost before loading.

**Context budget thresholds:**

- **60% warn (120k tokens loaded):** The agent loads only files directly relevant to the current module or user question. Supplementary files are deferred.
- **80% critical (160k tokens loaded):** The agent unloads non-essential files before loading new ones, following the retention priority: agent-instructions → current module → language file → troubleshooting → everything else.

**Module Workflows (load the one you need):**

- `module-01-business-problem.md` — Module 1: Business Problem
- `module-02-sdk-setup.md` — Module 2: SDK Setup
- `module-03-quick-demo.md` — Module 3: Quick Demo (Optional)
- `module-04-data-collection.md` — Module 4: Data Collection
- `module-05-data-quality-mapping.md` — Module 5: Data Quality & Mapping
- `module-06-load-data.md` — Module 6: Load Data
- `module-07-query-validation.md` — Module 7: Query and Visualize
- `module-08-performance.md` — Module 8: Performance Testing
- `module-09-security.md` — Module 9: Security Hardening
- `module-10-monitoring.md` — Module 10: Monitoring
- `module-11-deployment.md` — Module 11: Deployment

**Agent Behavior:**

- `agent-instructions.md` — Core agent rules and MCP usage (always loaded, ~74 lines)
- `session-resume.md` — Restores full context when resuming a previous bootcamp session
- `onboarding-flow.md` — Full onboarding sequence: directory creation, language selection, prerequisite checks, track selection, validation gates
- `cloud-provider-setup.md` — Cloud provider selection at the 8→9 gate (AWS, Azure, GCP, on-premises, local)
- `feedback-workflow.md` — Feedback collection workflow

**Auto-included (Kiro loads when relevant to the conversation):**

- `security-privacy.md` — Data privacy and PII protection (`inclusion: always` — loaded in every conversation)
- `project-structure.md` — Directory structure and setup commands (`inclusion: auto` — Kiro decides based on relevance)
- `module-transitions.md` — Journey map, before/after framing, and step-level progress rules (`inclusion: fileMatch` on `config/bootcamp_progress.json`)

**Module Completion (load after completing any module):**

- `module-completion.md` — Journal entries, reflection questions, next-step options, and track completion celebration
- `graduation.md` — Post-track graduation workflow — transitions bootcamp project to production structure

**Language-Specific (loaded automatically when editing matching files):**

- `lang-python.md` — Python/PEP-8 conventions (loads on `*.py`)
- `lang-java.md` — Java conventions (loads on `*.java`)
- `lang-csharp.md` — C#/.NET conventions (loads on `*.cs`)
- `lang-rust.md` — Rust conventions (loads on `*.rs`)
- `lang-typescript.md` — TypeScript conventions (loads on `*.ts`, `*.tsx`, `*.js`, `*.jsx`)

**Planning and Design:**

- `design-patterns.md` — 10 entity resolution patterns with use cases
- `module-prerequisites.md` — Prerequisites and dependencies for each module
- `complexity-estimator.md` — Time estimation based on data characteristics

**Project Setup:**

- `environment-setup.md` — Version control, language-specific environment setup

**Visualization:**

- `visualization-guide.md` — Interactive entity graph and results dashboard generation workflow

**Troubleshooting:**

- `common-pitfalls.md` — Common mistakes and solutions (load on errors or when user is stuck)
- `troubleshooting-decision-tree.md` — Visual diagnostic flowchart
- `mcp-offline-fallback.md` — MCP server offline: blocked/continuable operations, fallback instructions, reconnection
- `troubleshooting-commands.md` — Diagnostic commands, system checks, escalation procedures
- `lessons-learned.md` — Post-project retrospective template

**Reference (loaded indirectly via `#[[file:]]` directives):**

- `graduation-reference.md` — Detailed tables and templates used by `graduation.md`
- `hook-registry.md` — Canonical hook definitions used by `onboarding-flow.md`

**Advanced Topics:**

- `data-lineage.md` — Track data transformations and lineage
- `uat-framework.md` — User acceptance testing framework
- `deployment-onpremises.md` — On-premises/Docker Compose deployment reference
- `deployment-azure.md` — Azure deployment reference
- `deployment-gcp.md` — GCP/Google Cloud deployment reference
- `deployment-kubernetes.md` — Kubernetes/Helm deployment reference

## MCP Server Configuration

Connects to the Senzing MCP server (no API keys required):

```json
{
  "mcpServers": {
    "senzing-mcp-server": {
      "url": "https://mcp.senzing.com/mcp",
      "disabled": false,
      "autoApprove": [],
      "disabledTools": []
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

```text
# Discover available tools and workflows
get_capabilities()

# Get SDK installation instructions for a specific platform and language
sdk_guide(topic='install', platform='linux', language='python', version='current')

# Generate loading code in the user's chosen language
generate_scaffold(language='java', workflow='add_records', version='current')

# Start an interactive data mapping session
mapping_workflow(action='start', source_file='data/raw/customers.csv')

# Search Senzing docs for anti-patterns before recommending an approach
search_docs(query='loading performance', category='anti_patterns', version='current')

# Validate a mapped record against the Senzing Entity Specification
analyze_record(record='{"DATA_SOURCE":"CUSTOMERS","RECORD_ID":"1001","NAME_FULL":"John Smith"}')

# Diagnose a Senzing error code
explain_error_code(error_code='0023')
```

## Bootcamp Modules

| Module | Topic                                          |
|--------|------------------------------------------------|
| 1      | Understand Business Problem                    |
| 2      | Set Up SDK                                     |
| 3      | Quick Demo (Optional)                          |
| 4      | Data Collection Policy                         |
| 5      | Data Quality & Mapping (with optional test load)  |
| 6      | Load Data                                      |
| 7      | Query and Visualize                            |
| 8      | Performance Testing and Benchmarking           |
| 9      | Security Hardening                             |
| 10     | Monitoring and Observability                   |
| 11     | Package and Deploy                             |

Modules are progressive but iterative. Skip ahead options: have Entity Specification data (skip to 6), not deploying to production (skip 8-11). Modules 8-11 are production-focused and optional for learning/evaluation.

The goal is for you to finish the bootcamp with running code that is the basis of your real-world use of Senzing.

## Code Generation

All code templates are generated dynamically by the Senzing MCP server using `generate_scaffold`, `sdk_guide`, and `mapping_workflow` in your chosen programming language. No static templates are shipped — this ensures generated code always matches the current SDK version and follows current best practices.

## Code Quality Standards

All generated code follows language-appropriate coding standards based on the bootcamper's chosen language. The bootcamp supports Python, Java, C#, Rust, and TypeScript/Node.js — the agent queries the Senzing MCP server for the current list and asks the bootcamper to choose at the start. See `docs/policies/CODE_QUALITY_STANDARDS.md`.

## Recommended Hooks

Install pre-configured hooks for automated quality checks:

```console
python senzing-bootcamp/scripts/install_hooks.py
```

Or manually copy hook files into `.kiro/hooks/`.

Available: Code Style Check (`code-style-check`) ⭐, `ask-bootcamper`, `data-quality-check`, `backup-before-load`, `validate-senzing-json`, `backup-project-on-request`, `commonmark-validation`, `verify-senzing-facts`, `analyze-after-mapping`, `run-tests-after-change`, `git-commit-reminder`, `enforce-working-directory` ⭐, `verify-generated-code`, `offer-visualization`, `capture-feedback` ⭐, `deployment-phase-gate`, `enforce-visualization-offers` ⭐, `enforce-feedback-path`.

## Project Directory Structure

The agent creates an organized directory structure at bootcamp start. Key directories: `data/`, `database/`, `src/`, `docs/`, `config/`, `logs/`, `monitoring/`. The `config/` directory includes `data_sources.yaml` — a registry tracking each data source's quality, mapping, and load status across modules. Load `project-structure.md` for details.

## Entity Resolution Design Patterns

10 patterns available: Customer 360, Fraud Detection, Data Migration, Compliance Screening, Marketing Dedup, Patient Matching, Vendor MDM, Claims Fraud, KYC/Onboarding, Supply Chain. Load `design-patterns.md` for the full gallery.

## Troubleshooting

- Module stuck? Check `module-prerequisites.md`
- Error codes? Use `explain_error_code` tool
- Wrong attribute names? Use `mapping_workflow` (never guess)
- Wrong method signatures? Use `generate_scaffold` or `sdk_guide`
- MCP connection issues? Check internet/firewall for `mcp.senzing.com:443`
- MCP down? See `docs/guides/OFFLINE_MODE.md` for what works offline and reconnection steps
- Visual diagnostic? Load `troubleshooting-decision-tree.md`

Additional resources: `docs/guides/FAQ.md`. For Senzing terminology and error codes, use MCP tools `search_docs` and `explain_error_code`.

## Providing Feedback

Say "power feedback" or "bootcamp feedback" at any time to document issues or suggestions. The agent will guide you through a structured feedback workflow. See `feedback-workflow.md` for details.

## Useful Commands

All scripts are cross-platform Python and live in `senzing-bootcamp/scripts/`. Run them from your project root after the agent copies them during setup, or reference them directly from the power directory:

```text
python3 senzing-bootcamp/scripts/preflight.py            # Environment verification (primary)
python3 senzing-bootcamp/scripts/preflight.py --json     # Environment verification (JSON output)
python3 senzing-bootcamp/scripts/preflight.py --fix      # Environment verification with auto-fix
python3 senzing-bootcamp/scripts/status.py               # Check progress
python3 senzing-bootcamp/scripts/status.py --sync        # Sync progress to PROGRESS_TRACKER.md
python3 senzing-bootcamp/scripts/validate_module.py      # Validate current module completion
python3 senzing-bootcamp/scripts/validate_module.py --next 7  # Check if ready for module 7
python3 senzing-bootcamp/scripts/install_hooks.py        # Install hooks
python3 senzing-bootcamp/scripts/backup_project.py       # Backup project
python3 senzing-bootcamp/scripts/restore_project.py      # Restore from backup
python3 senzing-bootcamp/scripts/validate_commonmark.py  # Validate Markdown formatting
python3 senzing-bootcamp/scripts/validate_power.py       # Validate power integrity (cross-references, hooks, steering)
python3 senzing-bootcamp/scripts/measure_steering.py     # Update steering file token counts in steering-index.yaml
python3 senzing-bootcamp/scripts/measure_steering.py --check  # Verify stored token counts are within 10% of actual (CI mode)
python3 senzing-bootcamp/scripts/repair_progress.py      # Repair corrupted bootcamp_progress.json
python3 senzing-bootcamp/scripts/team_dashboard.py                    # Generate team progress dashboard (requires config/team.yaml)
python3 senzing-bootcamp/scripts/team_dashboard.py --output report.html  # Generate dashboard to custom path
python3 senzing-bootcamp/scripts/merge_feedback.py                    # Merge team feedback into one report
python3 senzing-bootcamp/scripts/merge_feedback.py --output report.md    # Merge feedback to custom path
python3 senzing-bootcamp/scripts/export_results.py                    # Export HTML report
python3 senzing-bootcamp/scripts/export_results.py --format zip       # Export ZIP with all artifacts
python3 senzing-bootcamp/scripts/export_results.py --modules 1,2,3    # Export specific modules only
python3 senzing-bootcamp/scripts/data_sources.py                     # View data source registry (table)
python3 senzing-bootcamp/scripts/data_sources.py --detail CUSTOMERS  # Show all fields for one source
python3 senzing-bootcamp/scripts/data_sources.py --summary           # Aggregate registry statistics
python3 senzing-bootcamp/scripts/rollback_module.py --module N           # Roll back a specific module
python3 senzing-bootcamp/scripts/rollback_module.py --module N --dry-run # Preview rollback without changes
python3 senzing-bootcamp/scripts/sync_hook_registry.py --write        # Regenerate hook-registry.md from .kiro.hook files
python3 senzing-bootcamp/scripts/sync_hook_registry.py --verify       # Verify hook registry matches hook files (CI mode)
python3 senzing-bootcamp/scripts/validate_dependencies.py             # Validate module dependency graph consistency
python3 senzing-bootcamp/scripts/lint_steering.py                     # Lint steering files for structural issues
python3 senzing-bootcamp/scripts/lint_steering.py --warnings-as-errors # Lint with warnings treated as errors
python3 senzing-bootcamp/scripts/lint_steering.py --skip-template     # Lint without template conformance checks
python3 senzing-bootcamp/scripts/split_steering.py --module 5         # Split large steering file into phase sub-files
python3 senzing-bootcamp/scripts/session_logger.py                    # Internal: append structured events to session log
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl          # Analyze session log (text table)
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl --format json  # Analyze session log (JSON)
python3 senzing-bootcamp/scripts/analyze_sessions.py config/session_log.jsonl --pretty       # Pretty-print log entries
python3 senzing-bootcamp/scripts/triage_feedback.py docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md  # Parse feedback into spec skeletons
python3 senzing-bootcamp/scripts/triage_feedback.py --dry-run         # Preview triage without creating files
python3 senzing-bootcamp/scripts/progress_utils.py       # Internal: progress tracking utilities (used by other scripts)
python3 senzing-bootcamp/scripts/team_config_validator.py # Internal: validate config/team.yaml structure (used during onboarding)
python3 senzing-bootcamp/scripts/check_prerequisites.py  # DEPRECATED — use preflight.py instead
python3 senzing-bootcamp/scripts/preflight_check.py      # DEPRECATED — use preflight.py instead
```

Use `python` instead of `python3` on Windows.

## Additional Resources

- FAQ: `docs/guides/FAQ.md`
- Quick Start: `docs/guides/QUICK_START.md`
- Collaboration Guide: `docs/guides/COLLABORATION_GUIDE.md`
- Module Flow Diagram: `docs/diagrams/module-flow.md` (text-based; use a Mermaid preview extension or paste into [mermaid.live](https://mermaid.live) to render)
- Data Flow Diagram: `docs/diagrams/data-flow.md` (text-based ASCII art, viewable in any editor)
- System Architecture: `docs/diagrams/system-architecture.md` (shows how SDK, database, programs, and optional layers fit together)
- Offline Mode Guide: `docs/guides/OFFLINE_MODE.md`
- Quality Scoring Methodology: `docs/guides/QUALITY_SCORING_METHODOLOGY.md`
- Performance Baselines: `docs/guides/PERFORMANCE_BASELINES.md`
- Templates: `templates/data_collection_checklist.md`, `templates/stakeholder_summary.md`, `templates/transformation_lineage.md`, `templates/uat_test_cases.md`

## Senzing Contact Information

- Support: <support@senzing.com> / <https://senzing.com/support/>
- Sales: <sales@senzing.com> / <https://senzing.com/contact/>
- Docs: <https://docs.senzing.com>
