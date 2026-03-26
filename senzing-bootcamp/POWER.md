---
name: "senzing-bootcamp"
displayName: "Senzing Boot Camp"
description: "Comprehensive guided boot camp for Senzing entity resolution. Covers data mapping, SDK setup, loading, performance testing, security hardening, monitoring, and production deployment."
keywords: ["senzing", "bootcamp", "training", "tutorial", "learning-path", "entity-resolution", "guided-workflow"]
author: "Senzing"
---

# Senzing Boot Camp

## 🚨 CRITICAL: Agent Must Read This First 🚨

**TO THE AGENT:** Before you do ANYTHING else - before greeting the user, before asking questions, before presenting options - you MUST create the project directory structure. This is MANDATORY. See the "Agent Behavior" section under "Project Directory Structure" below for exact commands. DO NOT SKIP THIS.

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

The agent will execute:
```bash
mkdir -p data/{raw,transformed,samples,backups}
mkdir -p database
mkdir -p src/{transform,load,query,utils}
mkdir -p tests
mkdir -p docs/feedback
mkdir -p config
mkdir -p docker/scripts
mkdir -p logs
mkdir -p monitoring
mkdir -p scripts
```

And create initial files: `.gitignore`, `.env.example`, `README.md`

**Why first?** This ensures all generated files go to the correct locations throughout the boot camp.

### New to Senzing?

1. **Check Prerequisites:** Run `./scripts/check_prerequisites.sh` to validate your environment
2. **Read the Quick Start:** See `docs/guides/QUICK_START.md` for three fast paths (10 min, 30 min, or 2 hours)
3. **Check the Onboarding Checklist:** Complete `docs/guides/ONBOARDING_CHECKLIST.md` before starting
4. **Review FAQ:** See `docs/guides/FAQ.md` for 100+ common questions and answers
5. **Learn Terminology:** Check `docs/guides/GLOSSARY.md` for Senzing-specific terms
6. **Choose Your Path:**
   - **Demo** (10 min): Module 0 with sample data
   - **Fast Track** (30 min): Modules 5-6 with SGES data
   - **Complete** (2-3 hrs): Modules 1-6, 8
   - **Production** (10-18 hrs): All modules 0-12

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

## Available MCP Tools

This boot camp connects to the Senzing MCP server and provides access to all entity resolution tools.

**MCP Server Configuration:** This power uses a public Senzing MCP server at `https://mcp.senzing.com/mcp`. No API keys, tokens, or configuration placeholders are needed - the server is ready to use immediately after installing the power.

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

- **Module 0: Quick Demo (Optional)**
  - **FIRST:** Agent creates project directory structure automatically
  - Experience entity resolution with sample data
  - See how Senzing resolves duplicate records automatically
  - 10-15 minutes

- **Module 1: Understand Business Problem**
  - **FIRST:** Agent creates project directory structure automatically (if not already created in Module 0)
  - Define your problem and identify data sources
  - View design pattern gallery
  - **NEW:** Calculate costs and ROI
  - Create problem statement document
  - 20-30 minutes

- **Module 2: Identify and Collect Data Sources**
  - Upload or link to data source files
  - Store data in data/raw/ directory
  - **NEW:** Track data lineage
  - Document data source locations
  - 10-15 minutes per data source

- **Module 3: Evaluate Data Quality**
  - **NEW:** Automated quality scoring (0-100)
  - **NEW:** Attribute completeness metrics
  - **NEW:** Data consistency analysis
  - **NEW:** Visual quality dashboard
  - Create data quality report
  - 15-20 minutes per data source

- **Module 4: Map Your Data**
  - Create transformation programs
  - **NEW:** Track transformation lineage
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
  - **NEW:** Incremental loading strategies
  - **NEW:** Delta/CDC patterns
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
  - **NEW:** User Acceptance Testing (UAT) framework
  - **NEW:** Results validation criteria
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
  - **NEW:** Multi-environment strategy
  - **NEW:** Automated code quality gates
  - **NEW:** Disaster recovery playbook
  - **NEW:** API gateway integration
  - Create deployment artifacts
  - 2-3 hours

**Total Time:** 10-18 hours for a comprehensive production-ready project

**Note:** While the modules are presented in order, you can move back and forth between steps as needed. Discovery is iterative — you might need to revisit earlier steps as you learn more about your data or refine your approach.

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

The Senzing Boot Camp agent will create this organized directory structure for you at the start of Module 1:

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
│   └── backups/                   # Database backups (created by user)
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
├── requirements.txt               # Python dependencies for your project
└── README.md                      # Project description

**Important**: All generated source code (transformation programs, loading programs, query programs, utilities, and scripts) should be placed in the `src/` directory structure, not in the project root. Docker files should be placed in the `docker/` directory, never in the project root.

**Note on backups**: The `data/backups/` directory is created by users in their project for storing database backups. This is NOT part of the power distribution itself.

**Note on requirements.txt**: Users should create a `requirements.txt` file in their project root to manage Python dependencies. See `examples/` for reference implementations.

**CRITICAL - SQLite Database Location**: All SQLite databases MUST be placed in `database/G2C.db` (project-relative path). Never use `/tmp/sqlite` or system-wide locations. This allows multiple bootcamp instances to run concurrently on the same machine. See `docs/policies/SQLITE_DATABASE_LOCATION.md` for complete policy.
```

**Agent behavior**:
- **🚨 MANDATORY - EXECUTE FIRST 🚨**: Before ANY other action, check if project structure exists
- **🚨 MANDATORY - EXECUTE FIRST 🚨**: If structure doesn't exist, create it immediately using commands above
- **🚨 MANDATORY - EXECUTE FIRST 🚨**: Do not greet user, do not ask questions, do not present options until structure is created
- **🚨 MANDATORY - EXECUTE FIRST 🚨**: This happens BEFORE everything else - no exceptions
- Inform user that structure has been created
- As you generate programs throughout the boot camp, save them in the appropriate folders

**Trigger points for directory creation** (create structure at ANY of these):
- User says "start the boot camp"
- User mentions any module number (0-12)
- User selects any path (A, B, C, D)
- User asks to begin
- ANY indication they want to use the power

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
  
- **steering/cost-estimation.md** — Pricing, ROI, deployment costs
  - Load when: Module 1 (planning), Module 4 (deployment choice)
  
- **steering/lessons-learned.md** — Post-project retrospective template
  - Load when: After Module 6, project completion
  
- **steering/common-pitfalls.md** — Common mistakes and how to avoid them
  - Load when: Any module, troubleshooting, user is stuck
  
- **steering/troubleshooting-decision-tree.md** — Visual flowchart for diagnosing issues
  - Load when: User encounters errors, systematic troubleshooting needed
  
- **steering/complexity-estimator.md** — Estimate time based on data characteristics
  - Load when: Module 1 (planning), user asks "how long will this take?"

**Note**: For testing, performance monitoring, integration patterns, disaster recovery, and collaboration guidance, use MCP server tools:
- Testing strategies → Use `search_docs(query="testing best practices")`
- Performance monitoring → Use `search_docs(query="performance monitoring", category="performance")`
- Integration patterns → Use `find_examples(query="API integration")` or `search_docs(query="integration patterns")`
- Disaster recovery → Use `search_docs(query="backup and recovery")`
- Collaboration → Standard software engineering practices

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
- Module 7: Multi-Source Orchestration
- Module 8: Query and Validate Results (with UAT Framework)
- Module 9: Performance Testing and Benchmarking
- Module 10: Security Hardening
- Module 11: Monitoring and Observability
- Module 12: Package and Deploy
- Troubleshooting and Error Resolution
- Explore Code Examples

## Troubleshooting

**Boot camp-specific troubleshooting**:

- **Module stuck?** Check prerequisites in module description
- **Directory structure missing?** Agent should create it automatically at start of Module 0 or 1
- **Code not PEP-8 compliant?** Use the agent's validation feature
- **Lost progress?** Run `./scripts/status.sh` or check `docs/guides/PROGRESS_TRACKER.md`
- **Can't find generated files?** Check the `src/` directory structure
- **Module prerequisites not met?** Review the "Module Prerequisites" section above
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

6. **Confirm and offer next steps**:
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
**Last Updated**: March 23, 2026

See [CHANGELOG.md](CHANGELOG.md) for complete version history and release notes.

## What's New in v1.0.0 (March 2026)

**Complete Learning Path:**
- 13 focused modules from quick demo to production deployment
- Automated data quality scoring
- Multi-source orchestration
- Performance testing and optimization
- Security hardening
- Monitoring and observability
- UAT framework
- Cost calculator
- Data lineage tracking

**Senzing MCP Server Integration:**
- Live, always-current Senzing documentation
- SDK code generation and scaffolding
- Interactive data mapping workflow (8 steps)
- Sample data access (CORD datasets)
- Error code explanations (456+ codes)
- Working code examples (27 GitHub repositories)

**Kiro Features:**
- 4 automation hooks for quality and validation
- 12 ready-to-use code templates
- 16 steering files for guided workflows
- 8 user guides
- 14 module documentation files
- 3 complete example projects

**Streamlined Distribution:**
- 50% smaller than initial development version
- Focused exclusively on boot camp-specific content
- MCP server provides all Senzing documentation
- No static content that can become outdated
