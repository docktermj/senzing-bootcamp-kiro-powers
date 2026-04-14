---
name: "senzing-bootcamp"
displayName: "Senzing Bootcamp"
description: "Guided 13-module bootcamp for learning Senzing entity resolution, from first demo to production deployment."
keywords: ["senzing", "bootcamp", "entity-resolution", "senzing-bootcamp", "learning-path"]
author: "Senzing"
---

# Senzing Bootcamp

## Overview

This power provides a guided bootcamp for learning Senzing entity resolution through a structured 13-module curriculum (Modules 0-12). It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

This power works best with Claude Opus 4.6 or similar.

## What This Bootcamp Does

The purpose of this bootcamp is to make you comfortable writing code — with Kiro's help — that uses the Senzing SDK for entity resolution. By the end, you'll have running code that serves as the foundation for your real-world use of Senzing.

The bootcamp is a series of modules. Each module builds on the previous ones, producing working artifacts (code, data files, documentation) that you keep and extend. Here's what each module does and why it matters:

| Module | What It Does | Why It Matters |
|--------|-------------|----------------|
| 0 — SDK Setup | Installs and configures the Senzing SDK on your machine | Everything else depends on a working SDK installation |
| 1 — Quick Demo | Runs entity resolution on sample data so you can see it work | Validates your entire setup end-to-end; the result is trivial on purpose — the point is proving the system works |
| 2 — Business Problem | Defines what you're trying to solve and which data sources matter | Focuses the rest of the bootcamp on your actual use case |
| 3 — Data Collection | Gets your data files into the project | You can't resolve entities without data to work with |
| 4 — Data Quality | Scores your data for completeness and consistency | Identifies issues before they cause bad matches |
| 5 — Data Mapping | Transforms your data into Senzing's format (SGES) | Senzing needs data in a specific JSON format to do its work |
| 6 — Single Source Loading | Loads your first data source into Senzing | Your first real entity resolution run with your own data |
| 7 — Multi-Source Orchestration | Loads and coordinates multiple data sources | Cross-source matching is where entity resolution really shines |
| 8 — Query & Validation | Builds query programs and validates results against your success criteria | Proves the system answers your business questions |
| 9 — Performance Testing | Benchmarks and optimizes for your data volume | Ensures the system handles production-scale data |
| 10 — Security Hardening | Implements access controls and data protection | Required for production with sensitive data |
| 11 — Monitoring | Sets up dashboards, alerts, and health checks | Keeps the system running reliably in production |
| 12 — Deployment | Packages everything for production deployment | Gets your solution out of the bootcamp and into the real world |

**Don't have data handy?** No problem — mock data can be generated at any point. Senzing also provides three ready-made sample datasets you can use throughout the bootcamp: Las Vegas (customer records), London (person records), and Moscow (organization records). Use `get_sample_data` to download them.

**Licensing:** Senzing includes a built-in evaluation license that allows 500 records, which is enough for the bootcamp. If you have your own license (or need more capacity), you can configure it during Module 0.

## Quick Start

**New users:** Say "start the bootcamp" to begin. Choose your path:

- **A) Quick Demo** — Modules 0 → 1. See entity resolution in action with sample data. Done in one session. Choose this if you want to verify the technology works before investing more time.
- **B) Fast Track** — Modules 5 → 6 → 8. For users who already have Senzing-ready (SGES) data. Choose this if you've already mapped your data and want to get straight to loading and querying.
- **C) Complete Beginner** — Modules 2 → 3 → 4 → 5 → 6 → 8. Full learning path from defining the problem through validating results. Choose this if you're starting from scratch with raw data and want guided help through the entire process.
- **D) Full Production** — All modules 0-12, including performance testing, security, monitoring, and deployment. Choose this if you're building something that needs to run in production.

Paths are not mutually exclusive — you can start with one and jump to another at any time. For example, start with Path A to see a quick demo, then switch to Path C to work with your own data. All completed modules carry forward.

Module 0 (SDK Setup) is inserted automatically before any module that needs it.

**Experienced users:** Skip to Module 5 (have SGES data), Module 6 (SDK + data ready), or Module 8 (data loaded).

## Relationship to Senzing Power

This bootcamp complements the optional **senzing** Kiro Power. Both connect to the same MCP server. Use this power for structured learning; use the senzing power for quick reference and troubleshooting.

## Available Steering Files

Load these on-demand when needed:

**Module Workflows (load the one you need):**

- `module-00-sdk-setup.md` — Module 0: SDK Setup
- `module-01-quick-demo.md` — Module 1: Quick Demo (Optional)
- `module-02-business-problem.md` — Module 2: Business Problem
- `module-03-data-collection.md` — Module 3: Data Collection
- `module-04-data-quality.md` — Module 4: Data Quality
- `module-05-data-mapping.md` — Module 5: Data Mapping
- `module-06-single-source.md` — Module 6: Single Source Loading
- `module-07-multi-source.md` — Module 7: Multi-Source Orchestration
- `module-08-query-validation.md` — Module 8: Query and Validation
- `module-09-performance.md` — Module 9: Performance Testing
- `module-10-security.md` — Module 10: Security Hardening
- `module-11-monitoring.md` — Module 11: Monitoring
- `module-12-deployment.md` — Module 12: Deployment

**Agent Behavior:**

- `agent-instructions.md` — Core agent rules and MCP usage (always loaded, ~80 lines)
- `session-resume.md` — Restores full context when resuming a previous bootcamp session
- `onboarding-flow.md` — Full onboarding sequence: directory creation, language selection, prerequisite checks, path selection, validation gates
- `cloud-provider-setup.md` — Cloud provider selection at the 8→9 gate (AWS, Azure, GCP, on-premises, local)
- `feedback-workflow.md` — Feedback collection workflow

**Auto-included (Kiro loads when relevant to the conversation):**

- `security-privacy.md` — Data privacy and PII protection (auto-included when PII or security is discussed)
- `project-structure.md` — Directory structure and setup commands (auto-included when creating files)
- `module-transitions.md` — Journey map, before/after framing, and bootcamp journal rules (auto-included during module work)

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

**Troubleshooting:**

- `common-pitfalls.md` — Common mistakes and solutions (load on errors or when user is stuck)
- `troubleshooting-decision-tree.md` — Visual diagnostic flowchart
- `lessons-learned.md` — Post-project retrospective template

**Advanced Topics:**

- `data-lineage.md` — Track data transformations and lineage
- `uat-framework.md` — User acceptance testing framework

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

All tools are enabled by default. To disable specific tools, add their names to `disabledTools` (e.g., `["submit_feedback"]`). See <https://kiro.dev/docs/mcp/configuration/> for full configuration options.

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

| Module | Topic                              |
|--------|------------------------------------|
| 0      | Set Up SDK                         |
| 1      | Quick Demo (Optional)              |
| 2      | Understand Business Problem        |
| 3      | Identify and Collect Data Sources  |
| 4      | Evaluate Data Quality              |
| 5      | Map Your Data                      |
| 6      | Load Single Data Source            |
| 7      | Multi-Source Orchestration         |
| 8      | Query and Validate Results         |
| 9      | Performance Testing                |
| 10     | Security Hardening                 |
| 11     | Monitoring and Observability       |
| 12     | Package and Deploy                 |

Modules are progressive but iterative. Skip ahead options: have SGES data (skip 5), single source (skip 7), not deploying to production (skip 9-12). Modules 9-12 are production-focused and optional for learning/evaluation.

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

Available: Code Style Check (`code-style-check`), `data-quality-check`, `backup-before-load`, `validate-senzing-json`, `backup-project-on-request`, `commonmark-validation`, `verify-senzing-facts`, `analyze-after-mapping`, `run-tests-after-change`, `git-commit-reminder`, `enforce-working-directory`, `summarize-on-stop`, `verify-generated-code`.

## Project Directory Structure

The agent creates an organized directory structure at bootcamp start. Key directories: `data/`, `database/`, `src/`, `docs/`, `config/`, `logs/`, `monitoring/`. Load `project-structure.md` for details.

## Entity Resolution Design Patterns

10 patterns available: Customer 360, Fraud Detection, Data Migration, Compliance Screening, Marketing Dedup, Patient Matching, Vendor MDM, Claims Fraud, KYC/Onboarding, Supply Chain. Load `design-patterns.md` for the full gallery.

## Troubleshooting

- Module stuck? Check `module-prerequisites.md`
- Error codes? Use `explain_error_code` tool
- Wrong attribute names? Use `mapping_workflow` (never guess)
- Wrong method signatures? Use `generate_scaffold` or `sdk_guide`
- MCP connection issues? Check internet/firewall for `mcp.senzing.com:443`
- Visual diagnostic? Load `troubleshooting-decision-tree.md`

Additional resources: `docs/guides/FAQ.md`. For Senzing terminology and error codes, use MCP tools `search_docs` and `explain_error_code`.

## Providing Feedback

Say "power feedback" or "bootcamp feedback" at any time to document issues or suggestions. The agent will guide you through a structured feedback workflow. See `feedback-workflow.md` for details.

## Useful Commands

All scripts are cross-platform Python and live in `senzing-bootcamp/scripts/`. Run them from your project root after the agent copies them during setup, or reference them directly from the power directory:

```text
python3 senzing-bootcamp/scripts/status.py              # Check progress
python3 senzing-bootcamp/scripts/status.py --sync       # Sync progress to PROGRESS_TRACKER.md
python3 senzing-bootcamp/scripts/check_prerequisites.py # Validate prerequisites
python3 senzing-bootcamp/scripts/validate_module.py     # Validate current module completion
python3 senzing-bootcamp/scripts/validate_module.py --next 6  # Check if ready for module 6
python3 senzing-bootcamp/scripts/install_hooks.py       # Install hooks
python3 senzing-bootcamp/scripts/clone_example.py       # Clone example project
python3 senzing-bootcamp/scripts/backup_project.py      # Backup project
python3 senzing-bootcamp/scripts/restore_project.py     # Restore from backup
python3 senzing-bootcamp/scripts/preflight_check.py     # Pre-demo environment check
python3 senzing-bootcamp/scripts/validate_commonmark.py  # Validate Markdown formatting
```

Use `python` instead of `python3` on Windows.

## Additional Resources

- FAQ: `docs/guides/FAQ.md`
- Quick Start: `docs/guides/QUICK_START.md`
- Collaboration Guide: `docs/guides/COLLABORATION_GUIDE.md`
- Module Flow Diagram: `docs/diagrams/module-flow.md` (text-based; use a Mermaid preview extension or paste into [mermaid.live](https://mermaid.live) to render)
- Data Flow Diagram: `docs/diagrams/data-flow.md` (text-based ASCII art, viewable in any editor)
- Example Projects: `examples/` — architectural blueprints (not runnable code) for simple single source, multi-source, and production deployment patterns

## Senzing Contact Information

- Support: <support@senzing.com> / <https://senzing.com/support/>
- Sales: <sales@senzing.com> / <https://senzing.com/contact/>
- Docs: <https://docs.senzing.com>
