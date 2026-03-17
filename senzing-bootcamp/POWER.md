---
name: "senzing-bootcamp"
displayName: "Senzing Boot Camp"
version: "3.0.0"
description: "Comprehensive guided boot camp for Senzing entity resolution. Covers data mapping, SDK setup, loading, performance testing, security hardening, monitoring, and production deployment."
keywords: ["Entity Resolution", "Senzing", "Data Mapping", "SDK", "Identity Resolution", "Data Matching", "ER", "Performance", "Security", "Monitoring", "Deployment"]
author: "Senzing"
senzing_compatibility: ["4.0"]
last_updated: "2026-03-17"
---

# Power: Senzing Boot Camp

## Overview

This power provides a guided boot camp experience for learning Senzing entity resolution. It connects to the Senzing MCP server to provide interactive, tool-assisted workflows covering data mapping, SDK installation, record loading, and entity resolution exploration.

Senzing is an embeddable entity resolution engine that resolves records about people and organizations across data sources — matching, relating, and deduplicating without manual rules or model training.

**Power Version**: 3.0.0  
**Senzing Compatibility**: V4.0  
**Last Updated**: 2026-03-17

## Code Quality Standards

All Python code generated during the boot camp follows **PEP-8** standards for consistency, readability, and maintainability:

- **Maximum line length**: 100 characters
- **No trailing whitespace**
- **4 spaces for indentation** (no tabs)
- **Proper docstrings** for all functions and classes
- **Organized imports** (standard library, third-party, local)
- **Consistent naming**: `snake_case` for functions, `PascalCase` for classes

The agent will automatically generate PEP-8 compliant code and check user-provided code for compliance. See `docs/development/PEP8_COMPLIANCE.md` for complete details.

## Getting Started

### New to Senzing?

1. **Read the Quick Start**: See `docs/guides/QUICK_START.md` for three fast paths (10 min, 30 min, or 2 hours)
2. **Check the Onboarding Checklist**: Complete `docs/guides/ONBOARDING_CHECKLIST.md` before starting
3. **Review Compatibility**: Check `docs/guides/COMPATIBILITY_MATRIX.md` for version support
4. **Choose Your Path**:
   - **Demo** (10 min): Module 0 with sample data
   - **Fast Track** (30 min): Modules 5-6 with SGES data
   - **Complete** (2-3 hrs): Modules 1-6, 8
   - **Production** (10-18 hrs): All modules 0-12

### Track Your Progress

Use `docs/guides/PROGRESS_TRACKER.md` to track completion of each module and overall progress.

### Example Projects

See `examples/` directory for three complete reference projects:
- **Simple Single Source**: Basic customer deduplication (2-3 hours)
- **Multi-Source Project**: Customer 360 with three sources (6-8 hours)
- **Production Deployment**: Complete production-ready system (12-15 hours)

### Templates

Use ready-made templates from `templates/` directory:
- CSV/JSON transformation templates
- Batch/streaming loader templates
- Query and export templates
- Utility templates for common tasks

## Available MCP Servers

### senzing-mcp-server

- **URL**: `https://mcp.senzing.com/mcp`
- **Purpose**: AI-assisted entity resolution tools — data mapping, SDK code generation, documentation search, troubleshooting, and sample data access.
- **Key tools**:
  - `get_capabilities` — Discover all available tools and workflows (call this first)
  - `mapping_workflow` — 7-step interactive data mapping from source files to Senzing JSON format
  - `lint_record` / `analyze_record` — Validate and analyze mapped data quality
  - `generate_scaffold` — Generate SDK code (Python, Java, C#, Rust) for common workflows
  - `sdk_guide` — Platform-specific SDK installation and pipeline setup
  - `get_sample_data` — Sample datasets (Las Vegas, London, Moscow) for testing
  - `find_examples` — Working code examples from 27 Senzing GitHub repositories
  - `search_docs` — Search indexed Senzing documentation
  - `explain_error_code` — Diagnose Senzing errors (456 error codes)
  - `get_sdk_reference` — SDK method signatures and flags

## Boot Camp Learning Path

The boot camp follows a progressive learning path with 13 focused modules (0-12). Each module has a single, clear purpose.

**Modules**:

- **Module 0: Quick Demo (Optional)**
  - Experience entity resolution with sample data
  - See how Senzing resolves duplicate records automatically
  - 10-15 minutes

- **Module 1: Understand Business Problem**
  - Define your problem and identify data sources
  - View design pattern gallery
  - **NEW**: Calculate costs and ROI
  - Create problem statement document
  - 20-30 minutes

- **Module 2: Identify and Collect Data Sources**
  - Upload or link to data source files
  - Store data in data/raw/ directory
  - **NEW**: Track data lineage
  - Document data source locations
  - 10-15 minutes per data source

- **Module 3: Evaluate Data Quality**
  - **NEW**: Automated quality scoring (0-100)
  - **NEW**: Attribute completeness metrics
  - **NEW**: Data consistency analysis
  - **NEW**: Visual quality dashboard
  - Create data quality report
  - 15-20 minutes per data source

- **Module 4: Map Your Data**
  - Create transformation programs
  - **NEW**: Track transformation lineage
  - Validate data quality
  - Generate test files
  - 1-2 hours per data source

- **Module 5: Set Up SDK**
  - Check if Senzing is already installed
  - Install and configure Senzing (if needed)
  - Set up database (SQLite or PostgreSQL)
  - Verify installation
  - 30 minutes - 1 hour

- **Module 6: Load Single Data Source**
  - Load ONE data source and verify
  - **NEW**: Incremental loading strategies
  - **NEW**: Delta/CDC patterns
  - Generate loading statistics
  - 30 minutes per source

- **Module 7: Multi-Source Orchestration (NEW)**
  - Manage dependencies between sources
  - Optimize load order
  - Parallel loading strategies
  - Error handling across sources
  - Multi-source progress tracking
  - 1-2 hours

- **Module 8: Query and Validate Results**
  - Create query programs
  - **NEW**: User Acceptance Testing (UAT) framework
  - **NEW**: Results validation criteria
  - Business user testing
  - 1-2 hours

- **Module 9: Performance Testing and Benchmarking (NEW)**
  - Benchmark transformation speed
  - Benchmark loading performance
  - Query response time testing
  - Resource utilization profiling
  - Scalability testing (10K, 100K, 1M records)
  - 1-2 hours

- **Module 10: Security Hardening (NEW)**
  - Secrets management
  - API authentication/authorization
  - Data encryption
  - PII handling compliance
  - Security scanning
  - Vulnerability assessment
  - 1-2 hours

- **Module 11: Monitoring and Observability (NEW)**
  - Distributed tracing setup
  - Structured logging
  - Metrics collection
  - APM integration
  - Alerting rules
  - Health checks
  - 1-2 hours

- **Module 12: Package and Deploy**
  - Refactor code into deployable package
  - **NEW**: Multi-environment strategy
  - **NEW**: Automated code quality gates
  - **NEW**: Disaster recovery playbook
  - **NEW**: API gateway integration
  - Create deployment artifacts
  - 2-3 hours

**Total Time**: 10-18 hours for a comprehensive production-ready project

**Note**: While the modules are presented in order, you can move back and forth between steps as needed. Discovery is iterative — you might need to revisit earlier steps as you learn more about your data or refine your approach.

### Skip Ahead Options

Experienced users can skip modules based on their situation:

- **Have SGES-compliant data?** → Skip Module 4, go directly to Module 5
- **Senzing already installed?** → Skip Module 5, go directly to Module 6
- **Just want to explore?** → Start with Module 0 (Quick Demo)
- **Single data source only?** → Skip Module 7 (Multi-Source Orchestration)
- **Already loaded data?** → Jump directly to Module 8
- **Know your problem well?** → Skim Module 1, focus on Modules 2-12
- **Data already collected?** → Skip Module 2, go to Module 3
- **Not deploying to production?** → Skip Modules 9-12
- **Performance not critical?** → Skip Module 9
- **Internal use only?** → Simplify Module 10 (Security)
- **Basic monitoring sufficient?** → Simplify Module 11

### Module Prerequisites

Before starting each module, ensure prerequisites are met:

**Module 0** (Optional):
- No prerequisites

**Module 1**:
- No prerequisites
- Recommended: Have business problem in mind

**Module 2**:
- ✅ Module 1 complete (business problem defined)
- ✅ Data sources identified in Module 1

**Module 3**:
- ✅ Module 2 complete (data sources collected)
- ✅ Data files in `data/raw/` directory
- ✅ Sample data available for evaluation

**Module 4**:
- ✅ Module 3 complete (sources evaluated)
- ✅ Non-compliant sources identified
- ✅ Quality scores reviewed

**Module 5**:
- ✅ Module 4 complete (all sources mapped) OR
- ✅ All sources are SGES-compliant
- ✅ Platform/environment ready

**Module 6**:
- ✅ Module 5 complete (SDK installed)
- ✅ Database configured
- ✅ At least one transformed data source ready

**Module 7**:
- ✅ Module 6 complete (first source loaded successfully)
- ✅ Multiple data sources to orchestrate
- ✅ Loading statistics reviewed for first source

**Module 8**:
- ✅ Module 7 complete (all sources loaded) OR
- ✅ Module 6 complete (single source loaded)
- ✅ No critical loading errors

**Module 9**:
- ✅ Module 8 complete (queries working)
- ✅ Representative data loaded
- ✅ Test environment available

**Module 10**:
- ✅ Module 9 complete (performance validated)
- ✅ Security requirements identified
- ✅ Compliance needs documented

**Module 11**:
- ✅ Module 10 complete (security hardened)
- ✅ Monitoring tools selected
- ✅ Production environment identified

**Module 12**:
- ✅ Module 11 complete (monitoring configured)
- ✅ All tests passing
- ✅ Deployment target confirmed

## Project Directory Structure

Before starting, set up a project directory to organize all your boot camp artifacts:

```
my-senzing-project/
├── .git/                          # Version control (optional, but recommended)
├── .gitignore                     # Exclude sensitive data
├── .env.example                   # Template for environment variables
├── .env                           # Actual environment variables (not in git)
├── data/                          # User's data files
│   ├── raw/                       # Original source data
│   ├── transformed/               # Senzing-formatted JSON output
│   ├── samples/                   # Sample data for testing
│   └── backups/                   # Database backups
├── database/                      # SQLite database files
│   ├── G2C.db                     # Main Senzing database (SQLite)
│   └── .gitkeep                   # Keep directory in git
├── src/                           # Generated program source
│   ├── quickstart_demo/           # Module 0 demo code (optional)
│   ├── transform/                 # Transformation programs (Module 3)
│   ├── load/                      # Loading programs (Module 5)
│   ├── query/                     # Query programs (Module 6)
│   └── utils/                     # Shared utilities
├── tests/                         # Test files for project
├── docs/                          # Design documents
│   ├── business_problem.md        # Module 1 output
│   ├── data_source_evaluation.md  # Module 2 output
│   ├── mapping_specifications.md  # Module 3 mappings
│   ├── query_specifications.md    # Module 6 queries
│   └── lessons_learned.md         # Post-project retrospective
├── config/                        # Configuration files
├── docker/                        # Docker files (if using containers)
│   ├── Dockerfile                 # Container definition
│   ├── docker-compose.yml         # Multi-container setup
│   └── scripts/                   # Docker-specific scripts
├── logs/                          # Log files
├── monitoring/                    # Monitoring and dashboards
└── README.md                      # Project description

**Important**: All generated source code (transformation programs, loading programs, query programs, utilities, and scripts) should be placed in the `src/` directory structure, not in the project root. Docker files should be placed in the `docker/` directory, never in the project root.
```

**Agent behavior**:
- At the start of Module 1, help the user create this directory structure
- Check if the directory is already a git repository before initializing
- If not a git repository, ask the user if they want to initialize version control
- As you generate programs throughout the boot camp, save them in the appropriate folders

## When to Load Steering Files

The boot camp includes detailed steering files for specific topics. Load these on-demand when users need detailed guidance:

### Core Workflows (Always Available)
- **steering/steering.md** — Detailed workflows for all modules (Module 0-6)
- **steering/agent-instructions.md** — Consolidated agent behavior guide (load at start)
- **steering/quick-reference.md** — MCP tool quick reference card

### Supporting Topics (Load on Demand)
- **steering/environment-setup.md** — Version control, Python venv, Docker, environment variables
  - Load when: Starting Module 1, user asks about setup
  
- **steering/security-privacy.md** — Data privacy, PII protection, compliance, anonymization
  - Load when: Starting Module 2, working with sensitive data
  
- **steering/testing-strategy.md** — Unit tests, integration tests, data quality tests
  - Load when: Module 3 (transformation), user asks about testing
  
- **steering/performance-monitoring.md** — Benchmarking, monitoring dashboards, health checks
  - Load when: Module 5 (loading), performance optimization questions
  
- **steering/recovery-procedures.md** — Backup, rollback, disaster recovery
  - Load when: Before Module 5, user encounters errors
  
- **steering/collaboration.md** — Team workflows, code review, handoff procedures
  - Load when: Team projects, handoff questions
  
- **steering/cost-estimation.md** — Pricing, ROI, deployment costs
  - Load when: Module 1 (planning), Module 4 (deployment choice)
  
- **steering/integration-patterns.md** — REST API, batch export, streaming, database sync
  - Load when: Module 6, user asks about integration
  
- **steering/lessons-learned.md** — Post-project retrospective template
  - Load when: After Module 6, project completion
  
- **steering/common-pitfalls.md** — Common mistakes and how to avoid them
  - Load when: Any module, troubleshooting, user is stuck
  
- **steering/troubleshooting-decision-tree.md** — Visual flowchart for diagnosing issues
  - Load when: User encounters errors, systematic troubleshooting needed
  
- **steering/complexity-estimator.md** — Estimate time based on data characteristics
  - Load when: Module 1 (planning), user asks "how long will this take?"

## Recommended Hooks

Install pre-configured hooks to automate quality checks and reminders. See `hooks/README.md` and `docs/guides/HOOKS_INSTALLATION_GUIDE.md` for details.

Available hooks:
- **data-quality-check** — Validates quality when transformations change
- **backup-before-load** — Reminds to backup before loading
- **test-before-commit** — Runs tests automatically
- **validate-senzing-json** — Validates output format
- **update-documentation** — Reminds to update docs

Installation:
```bash
# Create .kiro directory structure if it doesn't exist
mkdir -p .kiro/hooks

# Copy hooks
cp senzing-bootcamp/hooks/*.hook .kiro/hooks/
```

**Agent behavior**:
- When installing hooks, always verify the `.kiro/hooks/` directory exists first
- Create it if needed with `mkdir -p .kiro/hooks` before copying hook files
- **Proactively suggest hooks** at the start of Module 3 (data mapping)
- Remind users about backup hook before Module 6 (loading)

## Entity Resolution Design Pattern Gallery

When starting Module 1, offer users a gallery of common entity resolution patterns:

| Pattern | Use Case | Key Matching | Typical ROI |
|---------|----------|--------------|-------------|
| **Customer 360** | Unified customer view | Names, emails, phones, addresses | Improved service, targeted marketing |
| **Fraud Detection** | Identify fraud rings | Names, addresses, devices, IPs | Loss prevention, faster detection |
| **Data Migration** | Merge legacy systems | All available identifiers | Reduced storage, simplified ops |
| **Compliance Screening** | Watchlist matching | Names, DOB, nationalities, IDs | Regulatory compliance, risk mitigation |
| **Marketing Dedup** | Eliminate duplicates | Names, addresses, emails | Reduced mailing costs, better metrics |
| **Patient Matching** | Unified medical records | Names, DOB, SSN, MRNs | Patient safety, care coordination |
| **Vendor MDM** | Clean vendor master | Company names, tax IDs, addresses | Better pricing, consolidated spend |
| **Claims Fraud** | Detect staged accidents | Names, vehicles, providers | Reduced fraudulent payouts |
| **KYC/Onboarding** | Verify identity | Names, DOB, SSN, gov IDs | Reduced fraud, compliance |
| **Supply Chain** | Unified supplier view | Company names, GLNs, tax IDs | Visibility, risk management |

**When to use each pattern**:
- **Customer 360**: Multiple customer touchpoints, CRM consolidation
- **Fraud Detection**: Financial services, insurance, e-commerce
- **Data Migration**: M&A, system consolidation, cloud migration
- **Compliance**: Banking, fintech, international trade
- **Marketing**: Email campaigns, direct mail, lead management
- **Healthcare**: Hospital networks, HIE, patient portals
- **Vendor MDM**: Procurement, AP, spend analysis
- **Claims Fraud**: Insurance, workers comp, auto claims
- **KYC**: Banking, fintech, account opening
- **Supply Chain**: Manufacturing, logistics, procurement

**Agent behavior**:
- Present this gallery when user requests it in Module 1
- Help them identify which pattern(s) match their situation
- Use the selected pattern to guide problem definition and set realistic expectations

## Best Practices

- Always call `get_capabilities` first when starting a Senzing session
- Never hand-code Senzing JSON mappings or SDK method calls from memory — use `mapping_workflow` and `generate_scaffold` for validated output
- Use `search_docs` with category `anti_patterns` before recommending installation, architecture, or deployment approaches
- For SDK code, use `generate_scaffold` or `sdk_guide` — these return version-correct method signatures
- Start with SQLite for evaluation; recommend PostgreSQL for production
- Use CORD sample data for learning before working with real data
- **All Python code must be PEP-8 compliant** — the agent will generate compliant code and check user code for compliance (see `docs/development/PEP8_COMPLIANCE.md`)

## Common Workflows

See [steering/steering.md](steering/steering.md) for detailed step-by-step workflows covering:

- Module 0: Quick Demo (Optional)
- Module 1: Discover the Business Problem (with Cost Calculator)
- Module 2: Identify and Collect Data Sources (with Lineage Tracking)
- Module 3: Evaluate Data Quality (with Automated Scoring)
- Module 4: Data Mapping End-to-End (with Lineage Tracking)
- Module 5: Install Senzing SDK
- Module 6: Load Single Data Source (with Incremental Loading)
- Module 7: Multi-Source Orchestration
- Module 8: Query and Validate Results (with UAT Framework)
- Module 9: Performance Testing and Benchmarking
- Module 10: Security Hardening
- Module 11: Monitoring and Observability
- Module 12: Package and Deploy
- Troubleshooting and Error Resolution
- Explore Code Examples

## Troubleshooting

- **Wrong attribute names**: Never guess Senzing attribute names (e.g., `NAME_ORG` not `BUSINESS_NAME_ORG`). Always use `mapping_workflow`.
- **Wrong method signatures**: Never guess SDK methods (e.g., `close_export_report` not `close_export`). Always use `generate_scaffold` or `get_sdk_reference`.
- **Error codes**: Use `explain_error_code` with the code (accepts `SENZ0005`, `0005`, or `5`).
- **Configuration issues**: Use `search_docs` with category `configuration` or `database`.

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

### Getting Help

- Use `search_docs` to find Senzing documentation
- Use `explain_error_code` for error diagnosis
- Use `find_examples` to see real-world code patterns
- Review steering guides for detailed workflows
- Contact Senzing support for production issues
