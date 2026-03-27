---
name: "senzing-bootcamp"
displayName: "Senzing Boot Camp"
description: "Comprehensive guided boot camp for Senzing entity resolution. Covers data mapping, SDK setup, loading, performance testing, security hardening, monitoring, and production deployment."
keywords: ["senzing", "bootcamp", "training", "tutorial", "learning-path", "entity-resolution", "guided-workflow"]
author: "Senzing"
---

# Senzing Boot Camp

## 🚨 CRITICAL: Agent Must Read This First 🚨

**TO THE AGENT:** Before you do ANYTHING else - before greeting the user, before asking questions, before presenting options - you MUST create the project directory structure. This is MANDATORY. See the "Project Directory Structure" section below and load `steering/project-structure.md` for exact commands. DO NOT SKIP THIS.

---

## Quick Start

**New users:**

1. Say "start the boot camp" to begin
2. Choose your path: Demo (10 min), Fast Track (30 min), Complete (2-3 hrs), or Production (10-18 hrs)
3. Agent will create project structure automatically
4. Follow module-by-module guidance

**Experienced users:**

- Skip to Module 5 if you have SGES-compliant data
- Skip to Module 6 if Senzing is already installed
- Jump to Module 8 if data is already loaded

**Need help?** See `docs/guides/QUICK_START.md` for detailed fast paths.

---

## Overview

This power provides a **guided boot camp experience** for learning Senzing entity resolution through a structured 13-module curriculum. It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

## Relationship to Senzing Power

This boot camp power **complements** the **senzing** Kiro Power:

- **senzing power:** Quick reference documentation, tool catalog, troubleshooting guide
- **senzing-bootcamp power:** Structured 13-module learning curriculum with project guidance

**Both powers connect to the same MCP server**, so this boot camp is fully functional on its own. The senzing power is optional and provides additional quick-reference documentation if you prefer a condensed tool catalog and troubleshooting guide.

**When to use each:**

- Use **senzing-bootcamp** for structured learning and building your first project
- Use **senzing** (optional) for quick tool lookup and troubleshooting reference

## What Makes This Boot Camp Unique

Unlike the senzing reference power, this boot camp provides:

✅ **Structured Learning**: 13 progressive modules (0-12)
✅ **Project Scaffolding**: Automatic directory structure creation
✅ **Design Patterns**: Gallery of 10 common entity resolution patterns
✅ **Example Projects**: 3 complete reference implementations
✅ **Code Templates**: Ready-to-use transformation, loading, query templates
✅ **Progress Tracking**: Built-in progress tracker
✅ **Quality Standards**: PEP-8 compliance checking
✅ **Feedback Loop**: Structured feedback collection

**Use this power when:** You're learning Senzing or building your first project
**Use senzing power when:** You need quick reference or troubleshooting

## Available Steering Files

This power includes detailed steering files for specific workflows. Load these on-demand when needed:

**Core Workflows:**

- **steering.md** - Complete workflows for all modules (0-12)
- **agent-instructions.md** - Consolidated agent behavior guide
- **quick-reference.md** - MCP tool quick reference card

**Project Setup:**

- **project-structure.md** - Detailed directory structure and setup commands
- **environment-setup.md** - Version control, Python venv, Docker setup

**Planning and Design:**

- **design-patterns.md** - 10 common entity resolution patterns with use cases
- **module-prerequisites.md** - Prerequisites and dependencies for each module
- **complexity-estimator.md** - Time estimation based on data characteristics
- **cost-estimation.md** - Pricing, ROI, deployment costs

**Advanced Workflows:**

- **modules-7-12-workflows.md** - Detailed workflows for advanced modules
- **data-lineage.md** - Track data transformations and lineage
- **incremental-loading.md** - Delta/CDC loading patterns
- **uat-framework.md** - User acceptance testing framework
- **docker-deployment.md** - Container deployment strategies

**Troubleshooting and Best Practices:**

- **common-pitfalls.md** - Common mistakes and solutions
- **troubleshooting-decision-tree.md** - Visual diagnostic flowchart
- **security-privacy.md** - Data privacy, PII protection, compliance
- **lessons-learned.md** - Post-project retrospective template

## Code Quality Standards

All Python code generated during the boot camp follows **PEP-8** standards for consistency, readability, and maintainability:

- **Maximum line length:** 100 characters
- **No trailing whitespace**
- **4 spaces for indentation** (no tabs)
- **Proper docstrings** for all functions and classes
- **Organized imports** (standard library, third-party, local)
- **Consistent naming:** `snake_case` for functions, `PascalCase` for classes

The agent will automatically generate PEP-8 compliant code and check user-provided code for compliance. See `docs/policies/PEP8_COMPLIANCE.md` for complete details.

## Getting Started

### CRITICAL FIRST STEP: Create Directory Structure

**Before doing anything else**, the agent will automatically create the project directory structure. This happens at the very beginning of Module 0 or Module 1, whichever you start with.

**Why first?** This ensures all generated files go to the correct locations throughout the boot camp.

**For complete details**, load the steering file:

```text
readSteering: powerName="senzing-bootcamp", steeringFile="project-structure.md"
```

### New to Senzing?

1. **Check Prerequisites:** Run `./scripts/check_prerequisites.sh` to validate your environment
2. **Read the Quick Start:** See `docs/guides/QUICK_START.md` for three fast paths (10 min, 30 min, or 2 hours)
3. **Check the Onboarding Checklist:** Complete `docs/guides/ONBOARDING_CHECKLIST.md` before starting
4. **Review FAQ:** See `docs/guides/FAQ.md` for 100+ common questions and answers
5. **Learn Terminology:** Check `docs/guides/GLOSSARY.md` for Senzing-specific terms

### Track Your Progress

Use `docs/guides/PROGRESS_TRACKER.md` to track completion manually, or run `./scripts/status.sh` for automated progress checking with visual progress bar and next steps.

### Example Projects

See `examples/` directory for three complete reference projects:

- **Simple Single Source:** Basic customer deduplication (2-3 hours)
- **Multi-Source Project:** Customer 360 with three sources (6-8 hours)
- **Production Deployment:** Complete production-ready system (12-15 hours)

Clone examples to your workspace: `./scripts/clone_example.sh`

### Templates

Use utility templates from `templates/` directory:

- Database management (backup, restore, rollback)
- Data collection (CSV, JSON, API, database)
- Validation and testing (schema validation, performance baseline, troubleshooting)
- Planning and analysis (cost calculator)

**Note:** Transformation, loading, and query code should be generated via MCP server tools (`mapping_workflow`, `generate_scaffold`) rather than using templates. See `templates/README.md` for details.

## MCP Server Configuration

This power connects to the Senzing MCP server via the following configuration:

```json
{
  "mcpServers": {
    "senzing-mcp-server": {
      "url": "https://mcp.senzing.com/mcp",
      "disabled": false,
      "autoApprove": [],
      "timeout": 60000,
      "env": {
        "SENZING_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**No API keys or tokens required** - the server is publicly accessible and ready to use immediately after installing the power.

**Server name**: When using MCP tools, the server name is `senzing-mcp-server`.

## Available MCP Tools

This boot camp connects to the Senzing MCP server and provides access to all entity resolution tools.

**Most commonly used tools in this boot camp:**

- `get_capabilities` — Discover all available tools and workflows (call this first)
  - Use in: Module 0, Module 1
  - Returns: Complete list of tools, workflows, and server capabilities

- `mapping_workflow` — Interactive 7-step data mapping to Senzing JSON format
  - Use in: Module 4
  - Guides you through mapping source data fields to Senzing attributes

- `generate_scaffold` — Generate SDK code (Python, Java, C#, Rust) for common workflows
  - Use in: Modules 5, 6, 8
  - Creates complete, working code for loading, querying, and pipelines

- `get_sample_data` — Download sample datasets for testing (Las Vegas, London, Moscow)
  - Use in: Module 0
  - Returns: Ready-to-use sample records in Senzing JSON format

- `search_docs` — Search indexed Senzing documentation
  - Use in: All modules
  - Finds relevant documentation for any Senzing topic

- `explain_error_code` — Diagnose Senzing errors (456 error codes)
  - Use in: Troubleshooting
  - Provides detailed explanations and solutions for error codes

- `lint_record` — Validate mapped data format and structure
  - Use in: Module 4
  - Checks if your mapped data is valid Senzing JSON

- `analyze_record` — Analyze mapped data quality and coverage
  - Use in: Module 4
  - Provides quality metrics and completeness analysis

- `sdk_guide` — Platform-specific SDK installation and setup instructions
  - Use in: Module 5
  - Returns installation steps for your platform and language

- `find_examples` — Working code examples from 27 Senzing GitHub repositories
  - Use in: All modules
  - Shows real-world code patterns and implementations

- `get_sdk_reference` — SDK method signatures and flags
  - Use in: Modules 5, 6, 8
  - Provides exact method signatures for SDK calls

- `submit_feedback` — Report issues or suggestions
  - Use in: Any time
  - Send feedback about tools or documentation

**For additional quick-reference documentation**, you can optionally install the **senzing** power, which provides a condensed tool catalog and troubleshooting guide.

## Boot Camp Learning Path

The boot camp follows a progressive learning path with 13 focused modules (0-12). Each module has a single, clear purpose.

**Modules:**

- **Module 0: Quick Demo (Optional)** - 10-15 minutes
  - Experience entity resolution with sample data
  - See how Senzing resolves duplicate records automatically

- **Module 1: Understand Business Problem** - 20-30 minutes
  - Define your problem and identify data sources
  - View design pattern gallery
  - Calculate costs and ROI

- **Module 2: Identify and Collect Data Sources** - 10-15 minutes per source
  - Upload or link to data source files
  - Track data lineage

- **Module 3: Evaluate Data Quality** - 15-20 minutes per source
  - Automated quality scoring (0-100)
  - Attribute completeness metrics
  - Data consistency analysis

- **Module 4: Map Your Data** - 1-2 hours per source
  - Create transformation programs
  - Track transformation lineage
  - Validate data quality

- **Module 5: Set Up SDK** - 30 minutes - 1 hour
  - Install and configure Senzing
  - Set up database (SQLite or PostgreSQL)

- **Module 6: Load Single Data Source** - 30 minutes per source
  - Load ONE data source and verify
  - Incremental loading strategies

- **Module 7: Multi-Source Orchestration** - 1-2 hours
  - Manage dependencies between sources
  - Optimize load order
  - Parallel loading strategies

- **Module 8: Query and Validate Results** - 1-2 hours
  - Create query programs
  - User Acceptance Testing (UAT) framework

- **Module 9: Performance Testing and Benchmarking** - 1-2 hours
  - Benchmark transformation and loading
  - Query response time testing
  - Scalability testing

- **Module 10: Security Hardening** - 1-2 hours
  - Secrets management
  - API authentication/authorization
  - PII handling compliance

- **Module 11: Monitoring and Observability** - 1-2 hours
  - Distributed tracing setup
  - Structured logging
  - Metrics collection

- **Module 12: Package and Deploy** - 2-3 hours
  - Refactor code into deployable package
  - Multi-environment strategy
  - Disaster recovery playbook

**Total Time:** 10-18 hours for a comprehensive production-ready project

**Note:** While the modules are presented in order, you can move back and forth between steps as needed. Discovery is iterative — you might need to revisit earlier steps as you learn more about your data or refine your approach.

### Skip Ahead Options

Experienced users can skip modules based on their situation:

- **Have SGES-compliant data?** → Skip Module 4, go directly to Module 5
- **Senzing already installed?** → Skip Module 5, go directly to Module 6
- **Just want to explore?** → Start with Module 0 (Quick Demo)
- **Single data source only?** → Skip Module 7 (Multi-Source Orchestration)
- **Already loaded data?** → Jump directly to Module 8
- **Not deploying to production?** → Skip Modules 9-12

### Module Prerequisites

Before starting each module, ensure prerequisites are met. For complete details, load the steering file:

```text
readSteering: powerName="senzing-bootcamp", steeringFile="module-prerequisites.md"
```

**Quick reference:**

- Module 0: No prerequisites
- Module 1: No prerequisites
- Module 2: Requires Module 1
- Module 3: Requires Module 2
- Module 4: Requires Module 3
- Module 5: Requires Module 4 (or SGES data)
- Module 6: Requires Module 5
- Module 7: Requires Module 6 (skip if single source)
- Module 8: Requires Module 6 or 7
- Module 9-12: Sequential, but can be skipped if not deploying to production

## Project Directory Structure

The agent will create an organized directory structure at the start of Module 0 or Module 1. This ensures all generated files go to the correct locations throughout the boot camp.

**For complete details and agent behavior**, load the steering file:

```text
readSteering: powerName="senzing-bootcamp", steeringFile="project-structure.md"
```

**Key directories:**

- `data/` - Raw, transformed, and sample data
- `database/` - SQLite database files
- `src/` - Generated program source code
- `docs/` - Design documents and specifications
- `config/` - Configuration files
- `docker/` - Container definitions
- `logs/` - Log files
- `monitoring/` - Monitoring and dashboards

## Entity Resolution Design Patterns

When starting Module 1, users can choose from 10 common entity resolution patterns to guide their project.

**For complete pattern gallery with use cases and matching strategies**, load the steering file:

```text
readSteering: powerName="senzing-bootcamp", steeringFile="design-patterns.md"
```

**Available patterns:**

- Customer 360 - Unified customer view
- Fraud Detection - Identify fraud rings
- Data Migration - Merge legacy systems
- Compliance Screening - Watchlist matching
- Marketing Dedup - Eliminate duplicates
- Patient Matching - Unified medical records
- Vendor MDM - Clean vendor master
- Claims Fraud - Detect staged accidents
- KYC/Onboarding - Verify identity
- Supply Chain - Unified supplier view

## Recommended Hooks

Install pre-configured hooks to automate quality checks and reminders. See `hooks/README.md` and `docs/guides/HOOKS_INSTALLATION_GUIDE.md` for details.

Available hooks:

- **pep8-check** — Ensures Python code follows PEP-8 standards (100 char limit)
- **data-quality-check** — Validates quality when transformations change
- **backup-before-load** — Reminds to backup before loading
- **backup-project-on-request** — Auto-backup when you say "backup my project"
- **validate-senzing-json** — Validates output format against SGES

Quick Installation:

```bash
# Interactive installation (recommended)
./scripts/install_hooks.sh

# Or manual installation
mkdir -p .kiro/hooks
cp senzing-bootcamp/hooks/*.hook .kiro/hooks/
```

**Agent behavior**:

- When installing hooks, always verify the `.kiro/hooks/` directory exists first
- Create it if needed with `mkdir -p .kiro/hooks` before copying hook files
- **Proactively suggest hooks** at the start of Module 4 (data mapping)
- Remind users about backup hook before Module 6 (loading)
- Emphasize PEP-8 hook for maintaining code quality throughout

## Best Practices

### Presenting Path Options to Users

When offering users a choice of paths, use letter labels (A, B, C, D) instead of numbers (1, 2, 3, 4) to avoid confusion with module numbers.

**Example**:

```text
Which path would you like to take?

A) Quick Demo (10 min) - Module 0
   See REAL entity resolution in action - actually runs Senzing SDK with sample data

B) Fast Track (30 min) - Modules 5-6
   For users with SGES-compliant data

C) Complete Beginner (2-3 hrs) - Modules 1-6, 8
   Work with your raw data from start to finish

D) Full Production (10-18 hrs) - All Modules 0-12
   Complete production-ready deployment

Please respond with A, B, C, or D
```

**Why letters?** If you use numbers (1, 2, 3) and the user responds "1", it's ambiguous whether they mean "option 1" or "Module 1". Letters eliminate this confusion.

**Handling ambiguous responses**: If user enters a number when you presented letters, clarify: "Did you mean option A (Quick Demo) or Module 1 (Business Problem)?"

### General Best Practices

This boot camp follows Senzing best practices.

**Boot camp-specific practices**:

- Complete modules in order for first-time users
- Use letter labels (A, B, C, D) when presenting path options to avoid confusion with module numbers
- Create project directory structure before starting Module 1
- All Python code must be PEP-8 compliant (see `docs/policies/PEP8_COMPLIANCE.md`)
- Track progress using `docs/guides/PROGRESS_TRACKER.md`
- Use CORD sample data (Module 0) before working with real data
- Start with SQLite for evaluation; use PostgreSQL for production

### MCP Tool Usage Patterns

**Always start with capabilities:**

```text
get_capabilities() → Returns all available tools
```

**For data mapping:**

```text
mapping_workflow(source_data, data_source_code) → Interactive 7-step mapping
lint_record(record) → Validate mapped data
analyze_record(record) → Quality metrics
```

**For code generation:**

```text
generate_scaffold(language, workflow_type) → Complete working code
sdk_guide(platform, language) → Installation instructions
get_sdk_reference(method_name) → Method signatures
```

**For troubleshooting:**

```text
explain_error_code(code) → Error diagnosis and solutions
search_docs(query, category) → Find relevant documentation
find_examples(query) → Working code examples
```

**Senzing tool best practices**:

- Always call `get_capabilities` first when starting a Senzing session
- Never hand-code Senzing JSON mappings — use `mapping_workflow` for validated attribute names
- Never guess SDK method signatures — use `generate_scaffold` or `sdk_guide` for correct code
- Use `search_docs` with category `anti_patterns` before recommending installation or deployment approaches

## Common Workflows

See [steering/steering.md](steering/steering.md) for detailed step-by-step workflows covering:

- Module 0: Quick Demo (Optional)
- Module 1: Discover the Business Problem (with Cost Calculator)
- Module 2: Identify and Collect Data Sources (with Lineage Tracking)
- Module 3: Evaluate Data Quality (with Automated Scoring)
- Module 4: Data Mapping End-to-End (with Lineage Tracking)
- Module 5: Install Senzing SDK
- Module 6: Load Single Data Source (with Incremental Loading)

For Modules 7-12, see [steering/modules-7-12-workflows.md](steering/modules-7-12-workflows.md):

- Module 7: Multi-Source Orchestration
- Module 8: Query and Validate Results (with UAT Framework)
- Module 9: Performance Testing and Benchmarking
- Module 10: Security Hardening
- Module 11: Monitoring and Observability
- Module 12: Package and Deploy

Additional workflows:

- Troubleshooting and Error Resolution
- Explore Code Examples

## Troubleshooting

**Boot camp-specific troubleshooting**:

- **Module stuck?** Check prerequisites in module description or load `steering/module-prerequisites.md`
- **Directory structure missing?** Agent should create it automatically at start of Module 0 or 1
- **Code not PEP-8 compliant?** Use the agent's validation feature
- **Lost progress?** Run `./scripts/status.sh` or check `docs/guides/PROGRESS_TRACKER.md`
- **Can't find generated files?** Check the `src/` directory structure
- **Module prerequisites not met?** Load `steering/module-prerequisites.md` for details
- **Environment issues?** Run `./scripts/check_prerequisites.sh` to validate setup

**MCP tool troubleshooting**:

- **Wrong attribute names**: Never guess Senzing attribute names. Always use `mapping_workflow` for validated mappings
- **Wrong method signatures**: Never guess SDK methods. Always use `generate_scaffold` or `sdk_guide` for correct code
- **Error codes**: Use `explain_error_code` with the code (accepts `SENZ0005`, `0005`, or `5`)
- **Configuration issues**: Use `search_docs` with category `configuration` or `database`
- **MCP server connection**: Check internet connection and firewall settings for `mcp.senzing.com` (port 443)

**Additional resources**:

- **FAQ**: See `docs/guides/FAQ.md` for 100+ common questions
- **Glossary**: Check `docs/guides/GLOSSARY.md` for terminology
- **Visual guides**: Review `docs/diagrams/module-flow.md` and `docs/diagrams/data-flow.md`
- **Troubleshooting index**: See `docs/guides/TROUBLESHOOTING_INDEX.md`
- **Decision tree**: Load `steering/troubleshooting-decision-tree.md` for visual diagnostic flowchart
- **Senzing power**: Optionally install for quick reference and top 5 common issues

## Providing Feedback

Your feedback helps improve the Senzing Boot Camp for future users!

### Triggering Feedback Workflow

When a user says any of these phrases:

- "power feedback"
- "bootcamp feedback"
- "submit feedback"
- "provide feedback"
- "I have feedback"
- "report an issue"

The agent should immediately follow the feedback workflow below.

### Feedback Workflow (Agent Instructions)

When user requests to provide feedback:

1. **Check if feedback file exists**:

   ```bash
   if [ -f "docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md" ]; then
       echo "Feedback file exists"
   else
       echo "Creating feedback file from template"
   fi
   ```

2. **Create feedback file if needed**:
   - Copy template from `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md`
   - Save as `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`
   - Fill in the header with current date and user information (if available)

3. **Ask user what type of feedback**:
   - "What would you like to provide feedback about?"
   - Present categories: Documentation, Workflow, Tools, UX, Bug, Performance, Security

4. **Gather feedback details**:
   - Which module? (0-12)
   - What happened? (the issue)
   - Why is it a problem? (impact)
   - Suggested fix? (if they have one)
   - Priority? (High/Medium/Low)

5. **Add feedback to file**:
   - Use the improvement template from the file
   - Fill in all sections with user's responses
   - Add to the "Your Feedback" section

6. **Confirm to user**:
   - "I've added your feedback to `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`"
   - "Would you like to add more feedback, or continue with the boot camp?"

7. **Remind about submission**:
   - "When you complete the boot camp, please share this file with the power author"
   - "You can add more feedback anytime by saying 'power feedback'"

### Manual Feedback Process (For Reference)

As you work through the boot camp, document any issues, confusion points, or improvement suggestions:

1. **Create feedback file**: Copy the template from `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md`
2. **Save as**: `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` in your project
3. **Document issues**: Add entries as you encounter problems or have suggestions
4. **Send to author**: Share the completed file with the power author after finishing

### What to Include

- Unclear or confusing instructions
- Steps that don't work as documented
- Missing information or prerequisites
- Awkward or inefficient workflows
- Unclear error messages
- Outdated documentation
- Better approaches you discovered
- Missing tools or templates

### Feedback Categories

- **Documentation**: Clarity, accuracy, completeness
- **Workflow**: Step ordering, prerequisites, transitions
- **Tools**: Missing utilities, template improvements
- **UX**: Confusion points, navigation issues
- **Bugs**: Incorrect behavior, errors
- **Performance**: Slow operations, optimization opportunities
- **Security**: Security concerns, compliance issues

**Agent behavior**:

- At the start of Module 1, inform users: "If you encounter any issues or have suggestions during the boot camp, just say 'power feedback' or 'bootcamp feedback' and I'll help you document them"
- When user says "power feedback", "bootcamp feedback", "submit feedback", "provide feedback", "I have feedback", or "report an issue", immediately trigger the feedback workflow (see Feedback Workflow section above)
- Remind users at the end of Module 12 to share their completed feedback file with the power author

---

## Useful Commands

Quick reference for common tasks:

```bash
# Check project status and progress
./scripts/status.sh

# Validate prerequisites
./scripts/check_prerequisites.sh

# Install hooks
./scripts/install_hooks.sh

# Clone example project
./scripts/clone_example.sh

# Backup project
./scripts/backup_project.sh

# Restore project
./scripts/restore_project.sh <backup-file>
```

## Additional Resources

### Documentation

- **FAQ**: `docs/guides/FAQ.md` - 100+ questions and answers
- **Glossary**: `docs/guides/GLOSSARY.md` - A-Z Senzing terminology
- **Collaboration Guide**: `docs/guides/COLLABORATION_GUIDE.md` - Team workflows
- **Quick Start**: `docs/guides/QUICK_START.md` - Fast paths to get started
- **Troubleshooting**: `docs/guides/TROUBLESHOOTING_INDEX.md` - Common issues

### Visual Guides

- **Module Flow**: `docs/diagrams/module-flow.md` - Visual module progression
- **Data Flow**: `docs/diagrams/data-flow.md` - Data pipeline visualization

### For Teams

- **Collaboration Guide**: `docs/guides/COLLABORATION_GUIDE.md`
  - Git workflows and branch strategies
  - Code review processes
  - Team roles and responsibilities
  - Communication guidelines

## Boot Camp Complete! 🎉

After completing all modules, you'll have:

- ✅ Clear business problem statement with cost estimates
- ✅ Collected data sources with lineage tracking
- ✅ Data quality scores and metrics
- ✅ Transformation programs for each source
- ✅ Installed and configured Senzing SDK
- ✅ Single and multi-source loading orchestration
- ✅ Query programs with UAT validation
- ✅ Performance benchmarks and optimization
- ✅ Security-hardened configuration
- ✅ Monitoring and observability setup
- ✅ Production-ready deployment package

### Next Steps

1. **Deploy to production**: Use the packaged deployment artifacts from Module 12
2. **Monitor performance**: Use dashboards from Module 11
3. **Respond to alerts**: Follow runbooks from Module 11
4. **Iterate and improve**: Use performance data from Module 9
5. **Expand**: Add more data sources using Modules 2-7
6. **Maintain security**: Regular audits using Module 10 checklist
7. **Scale**: Use benchmarks from Module 9 to plan capacity
8. **Share feedback**: Send your `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` file to the power author

### Getting Help

- **For module workflows**: Review steering guides in this power
- **For code examples**: Check `examples/` directory or use `find_examples` tool
- **For tool documentation**: Use `search_docs` tool or `get_capabilities` for tool list
- **For error diagnosis**: Use `explain_error_code` tool
- **For quick reference**: Optionally install the **senzing** power for condensed documentation
- **For licensing questions**: See `licenses/README.md` or contact Senzing support
- **For production issues**: Contact Senzing support

### Senzing Contact Information

**Support** (Technical assistance, evaluation licenses):

- Email: [support@senzing.com](mailto:support@senzing.com)
- Website: [https://senzing.com/support/](https://senzing.com/support/)

**Sales** (Production licenses, pricing):

- Email: [sales@senzing.com](mailto:sales@senzing.com)
- Website: [https://senzing.com/contact/](https://senzing.com/contact/)

**General**:

- Website: [https://senzing.com](https://senzing.com)
- Documentation: [https://docs.senzing.com](https://docs.senzing.com)

---

## Version Information

**Current Version**: 1.0.0
**Senzing Compatibility**: V4.0
**Last Updated**: March 27, 2026

See [CHANGELOG.md](CHANGELOG.md) for complete version history and release notes.
