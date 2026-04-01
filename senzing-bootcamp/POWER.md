---
name: "senzing-bootcamp"
displayName: "Senzing Boot Camp"
description: "Guided 13-module boot camp for learning Senzing entity resolution, from first demo to production deployment."
keywords: ["senzing", "bootcamp", "entity-resolution", "senzing-bootcamp", "learning-path"]
author: "Senzing"
---

# Senzing Boot Camp

## Overview

This power provides a guided boot camp for learning Senzing entity resolution through a structured 13-module curriculum (Modules 0-12). It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

## Quick Start

**New users:** Say "start the boot camp" to begin. Choose your path:

- A) Quick Demo (10 min) — Module 1
- B) Fast Track (30 min) — Modules 5-6 (for users with SGES-compliant data)
- C) Complete Beginner (2-3 hrs) — Modules 2-6, 8
- D) Full Production (10-18 hrs) — All Modules 0-12

**Experienced users:** Skip to Module 5 (have SGES data), Module 6 (SDK + data ready), or Module 8 (data loaded).

## Relationship to Senzing Power

This boot camp complements the optional **senzing** Kiro Power. Both connect to the same MCP server. Use this power for structured learning; use the senzing power for quick reference and troubleshooting.

## Available Steering Files

Load these on-demand when needed:

**Module Workflows (load the one you need):**

- `module-00-sdk-setup.md` — Module 0: SDK Setup
- `module-01-quick-demo.md` — Module 1: Quick Demo (Optional)
- `module-02-business-problem.md` — Module 2: Business Problem
- `module-03-data-collection.md` — Module 3: Data Collection
- `module-04-data-quality.md` — Module 4: Data Quality + Hook Installation
- `module-05-data-mapping.md` — Module 5: Data Mapping
- `module-06-single-source.md` — Module 6: Single Source Loading
- `module-07-multi-source.md` — Module 7: Multi-Source Orchestration
- `module-08-query-validation.md` — Module 8: Query and Validation
- `module-09-performance.md` — Module 9: Performance Testing
- `module-10-security.md` — Module 10: Security Hardening
- `module-11-monitoring.md` — Module 11: Monitoring
- `module-12-deployment.md` — Module 12: Deployment

**Agent Behavior:**

- `agent-instructions.md` — Consolidated agent behavior guide (always loaded)
- `security-privacy.md` — Data privacy and PII protection (always loaded)
- `feedback-workflow.md` — Feedback collection workflow

**Planning and Design:**

- `design-patterns.md` — 10 entity resolution patterns with use cases
- `module-prerequisites.md` — Prerequisites and dependencies for each module
- `complexity-estimator.md` — Time estimation based on data characteristics

**Project Setup:**

- `project-structure.md` — Directory structure and setup commands
- `environment-setup.md` — Version control, language-specific environment setup

**Advanced Topics:**

- `data-lineage.md` — Track data transformations and lineage
- `uat-framework.md` — User acceptance testing framework

**Troubleshooting:**

- `common-pitfalls.md` — Common mistakes and solutions
- `troubleshooting-decision-tree.md` — Visual diagnostic flowchart
- `lessons-learned.md` — Post-project retrospective template

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

**Server name**: `senzing-mcp-server`

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

## Boot Camp Modules

| Module | Topic                              | Time                           |
|--------|------------------------------------|--------------------------------|
| 0      | Set Up SDK                         | 30 min - 1 hr                  |
| 1      | Quick Demo (Optional)              | 10-15 min                      |
| 2      | Understand Business Problem        | 20-30 min                      |
| 3      | Identify and Collect Data Sources  | 10-15 min/source               |
| 4      | Evaluate Data Quality              | 15-20 min/source               |
| 5      | Map Your Data                      | 1-2 hrs/source                 |
| 6      | Load Single Data Source            | 30 min/source                  |
| 7      | Multi-Source Orchestration         | 1-2 hrs                        |
| 8      | Query and Validate Results         | 1-2 hrs                        |
| 9      | Performance Testing                | 1-2 hrs                        |
| 10     | Security Hardening                 | 2-8 hrs (varies by compliance) |
| 11     | Monitoring and Observability       | 60-90 min                      |
| 12     | Package and Deploy                 | 2-4 hrs (varies by target)     |

Modules are progressive but iterative. Skip ahead options: have SGES data (skip 5), single source (skip 7), not deploying to production (skip 9-12). Modules 9-12 are production-focused and optional for learning/evaluation.

## Code Quality Standards

All generated code follows language-appropriate coding standards based on the bootcamper's chosen language. The boot camp supports Python, Java, C#, Rust, and TypeScript/Node.js — the agent queries the Senzing MCP server for the current list and asks the bootcamper to choose at the start. See `docs/policies/CODE_QUALITY_STANDARDS.md`.

## Recommended Hooks

Install pre-configured hooks for automated quality checks:

```bash
mkdir -p .kiro/hooks
cp senzing-bootcamp/hooks/*.kiro.hook .kiro/hooks/
```

Available: Code Style Check (`code-style-check`), `data-quality-check`, `backup-before-load`, `validate-senzing-json`, `backup-project-on-request`, `commonmark-validation`, `verify-senzing-facts`, `analyze-after-mapping`, `run-tests-after-change`.

## Project Directory Structure

The agent creates an organized directory structure at boot camp start. Key directories: `data/`, `database/`, `src/`, `docs/`, `config/`, `logs/`, `monitoring/`. Load `project-structure.md` for details.

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

```bash
./scripts/status.sh              # Check progress
./scripts/check_prerequisites.sh # Validate prerequisites
./scripts/install_hooks.sh       # Install hooks
./scripts/clone_example.sh       # Clone example project
./scripts/backup_project.sh      # Backup project
```

## Additional Resources

- FAQ: `docs/guides/FAQ.md`
- Quick Start: `docs/guides/QUICK_START.md`
- Collaboration Guide: `docs/guides/COLLABORATION_GUIDE.md`
- Module Flow Diagram: `docs/diagrams/module-flow.md`
- Data Flow Diagram: `docs/diagrams/data-flow.md`
- Example Projects: `examples/` (simple single source, multi-source, production deployment)

## Senzing Contact Information

- Support: <support@senzing.com> / <https://senzing.com/support/>
- Sales: <sales@senzing.com> / <https://senzing.com/contact/>
- Docs: <https://docs.senzing.com>
