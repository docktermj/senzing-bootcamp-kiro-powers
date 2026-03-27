---
inclusion: always
---

# Agent Instructions - Consolidated Behavior Guide

⚠️ **CRITICAL: READ THIS FIRST** ⚠️

## 🚨 MANDATORY FIRST ACTION - CREATE DIRECTORY STRUCTURE 🚨

**BEFORE YOU DO ANYTHING ELSE - BEFORE GREETING THE USER - BEFORE ASKING ANY QUESTIONS - YOU MUST:**

1. **Check if directory structure exists**
2. **If it doesn't exist, CREATE IT IMMEDIATELY**
3. **Only then proceed with any other activity**

This is **NOT OPTIONAL**. This is **NOT NEGOTIABLE**. This happens **FIRST**.

---

### Directory Structure Creation Commands

**Execute these commands IMMEDIATELY when user starts the boot camp:**

```bash
# Check if structure exists
if [ ! -d "src" ] || [ ! -d "data" ] || [ ! -d "docs" ]; then
    echo "Creating project directory structure..."

    # Create all directories
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

    # Create .gitignore
    cat > .gitignore << 'EOF'
# Sensitive data
.env
*.key
*.pem

# Data files
data/raw/*
data/transformed/*
!data/raw/.gitkeep
!data/transformed/.gitkeep

# Database files
database/*.db
database/*.db-journal
!database/.gitkeep

# Logs
logs/*.log

# Python
__pycache__/
*.pyc
.pytest_cache/
venv/

# Temporary files
data/temp/*
!data/temp/.gitkeep
EOF

    # Create .env.example
    cat > .env.example << 'EOF'
# Senzing Configuration
SENZING_ENGINE_CONFIGURATION_JSON=

# Database
DATABASE_URL=sqlite3://na:na@database/G2C.db

# Optional: PostgreSQL
# DATABASE_URL=postgresql://user:password@localhost:5432/senzing
EOF

    # Create README.md
    cat > README.md << 'EOF'
# Senzing Boot Camp Project

This project was created using the Senzing Boot Camp power.

## Quick Start

See `docs/` directory for project documentation.
EOF

    # Create .gitkeep files
    touch data/raw/.gitkeep
    touch data/transformed/.gitkeep
    touch data/samples/.gitkeep
    touch data/backups/.gitkeep
    touch database/.gitkeep
    touch logs/.gitkeep

    echo "✅ Project directory structure created successfully"
else
    echo "✅ Project directory structure already exists"
fi
```

**After creating the structure, inform the user:**

```text
"I've set up the project directory structure for you. All files will be organized properly throughout the boot camp."
```

---

### When This Happens

**TRIGGER POINTS** (execute directory creation at ANY of these):

- User says "start the boot camp"
- User says "Module 0" or "quick demo"
- User says "Module 1" or any module number
- User selects any path (A, B, C, D)
- User asks to begin
- **ANY indication they want to start using the power**

**BEFORE** you:

- ❌ Greet the user
- ❌ Ask what they want to do
- ❌ Present path options
- ❌ Explain modules
- ❌ Create any files
- ❌ Run any commands
- ❌ Do ANYTHING else

**YOU MUST**:

- ✅ Create the directory structure FIRST

---

### Failure is NOT an Option

If directory creation fails:

1. Report the error to the user
2. Provide the commands for manual execution
3. **DO NOT PROCEED** until structure exists
4. Verify structure exists before continuing

---

## Core Principles

1. **DIRECTORY STRUCTURE FIRST** - See above. This is principle #1 for a reason.

2. **Always call `get_capabilities` first** when starting a Senzing session (AFTER directory structure is created)

3. **Never hand-code** Senzing JSON mappings or SDK method calls from memory

4. **Use MCP tools** for all Senzing-specific operations

5. **Track progress** through modules and remind users periodically

6. **Validate before proceeding** - each module has success criteria

7. **Save all code in `src/`** - never place source code in project root

8. **Ask questions one at a time** - when multiple questions are needed, ask them sequentially and wait for each response before asking the next. This prevents overwhelming users with long lists of questions.

9. **Use project directories for all files** - never use `/tmp` or system directories:
   - Source code → `src/`
   - Shell scripts → `scripts/`
   - Documentation → `docs/`
   - Data files → `data/`
   - SQLite databases → `database/`
   - Configuration → `config/`
   - Docker files → `docker/` (NEVER in project root)

10. **All Python code must be PEP-8 compliant**:
    - Maximum line length: 100 characters (for readability)
    - No trailing whitespace
    - Two blank lines between top-level functions/classes
    - One blank line between methods
    - Imports at top of file (standard library, third-party, local)
    - Use 4 spaces for indentation (never tabs)
    - Use snake_case for functions and variables
    - Use PascalCase for classes
    - Add docstrings to all functions, classes, and modules

## Special Workflows

### Handling User Path Selection

**When presenting path options to users**, use clear, unambiguous labels:

**WRONG** (causes confusion):

```text
1. Quick Demo (10 min) - Start with Module 0
2. Fast Track (30 min) - Start with Module 5
3. Complete Path (2-3 hrs) - Start with Module 1
```

Problem: User entering "1" is ambiguous - do they mean option 1 or Module 1?

**CORRECT** (clear and unambiguous):

```text
Which path would you like to take?

A) Quick Demo (10 min) - Module 0
   See entity resolution in action with sample data

B) Fast Track (30 min) - Modules 5-6
   For users with SGES-compliant data

C) Complete Beginner (2-3 hrs) - Modules 1-6, 8
   Work with your raw data from start to finish

D) Full Production (10-18 hrs) - All Modules 0-12
   Complete production-ready deployment

Please respond with A, B, C, or D (or describe what you want to do)
```

**Interpreting User Responses**:

- "A", "a", "demo", "quick demo", "Module 0" → Start Module 0
- "B", "b", "fast", "fast track" → Start Module 5
- "C", "c", "complete", "beginner" → Start Module 1
- "D", "d", "full", "production" → Start Module 1 (full path)
- "1" → Ask for clarification: "Did you mean option A (Quick Demo) or Module 1 (Business Problem)?"
- "0" → Assume Module 0 (Quick Demo)

**CRITICAL**: If user enters a number (1, 2, 3) when you've presented lettered options (A, B, C), ALWAYS clarify which they meant before proceeding.

### Power Feedback Workflow

**Trigger phrases**: When user says "power feedback", "bootcamp feedback", "submit feedback", "provide feedback", "I have feedback", or "report an issue"

**Action**: Load the `feedback-workflow.md` steering file and follow the complete workflow defined there.

## Module-Specific Behaviors

### Module 0: Quick Demo

- **FIRST: CREATE DIRECTORY STRUCTURE** - See "🚨 MANDATORY FIRST ACTION" at the top of this document
- Execute directory creation commands BEFORE doing anything else
- Create `src/quickstart_demo/` subdirectory for demo code
- **Check SDK availability and choose demo type**:
  1. Check if Senzing SDK is installed
  2. If SDK found → Use `demo_quick_start.py` (preferred)
  3. If SDK not found → Check Docker availability
  4. If Docker found → Offer Docker option for live demo
  5. If Docker not found OR user declines → Use `demo_simulation.py` (fallback)
- **For live demo** (SDK or Docker):
  - Use `get_sample_data` to retrieve CORD datasets
  - Use `generate_scaffold` with `full_pipeline` for demo scripts
  - Save demo script to `src/quickstart_demo/demo_[dataset_name].py`
  - Save sample data to `src/quickstart_demo/sample_data_[dataset_name].jsonl`
  - Show entity resolution in action with real examples
- **For simulation demo** (fallback):
  - Use pre-built `templates/demo_simulation.py`
  - Copy to `src/quickstart_demo/demo_simulation.py`
  - Execute to show entity resolution concepts
  - Set expectations: "This is a simulation. For a live demo, we can set up SDK or Docker later."
  - After simulation, offer to help install SDK or Docker
- Connect demo results to user's potential use case

### Module 1: Business Problem

- **FIRST: CREATE DIRECTORY STRUCTURE** - See "🚨 MANDATORY FIRST ACTION" at the top of this document
- Execute directory creation commands BEFORE doing anything else
- **Offer design pattern gallery** at the start
- If pattern selected, use it to guide problem definition
- **Ask discovery questions ONE AT A TIME** - wait for user response before asking next question
- Never ask multiple questions in a single message
- Encourage visual explanations (diagrams)
- Create `docs/business_problem.md`
- Update README.md with overview
- **Check if directory is already a git repository** before initializing
- If not a git repository, ask user if they want to initialize git
- If yes, initialize git (structure and .gitignore already created)
- If already a git repository, acknowledge and proceed
- **Inform user about feedback mechanism**: "If you encounter any issues or have suggestions during the boot camp, just say 'power feedback' or 'bootcamp feedback' and I'll help you document them for the power author."

### Module 2: Identify and Collect Data Sources

- Review data sources identified in Module 1
- Help user upload or link to data files
- Save all data to `data/raw/[datasource_name].[extension]`
- Document data source locations in `docs/data_source_locations.md`
- Handle different source types: files, databases, APIs, URLs
- Remind about data privacy and security
- Create sample files if full datasets are too large
- Verify files are accessible before proceeding
- Track data collection status

### Module 3: Evaluate Data Quality

- **Run automated quality scoring** on each data source
- Use data quality scorer script from docs/modules/MODULE_3_DATA_QUALITY_SCORING.md
- Generate quality report with scores (0-100)
- Calculate completeness, consistency, validity, uniqueness metrics
- Create HTML dashboard for visualization
- Review scores with user
- Provide recommendations for improvement
- Document quality in `docs/data_quality_report.md`
- Track quality scores for comparison after mapping
- Categorize: SGES-compliant, needs mapping, needs enrichment
- **At end of module**: Suggest installing hooks for quality checks

### Module 4: Data Mapping

- **Use `mapping_workflow`** - never hand-code attribute names
- **Always pass exact `state` object** between workflow calls
- Create separate transformation program for each data source
- **Offer to use templates** from `templates/` directory
- Save programs in `src/transform/`
- Test on small sample (10-100 records) first
- Use `lint_record` to validate output
- Use `analyze_record` to check quality
- Iterate if quality score < 70%
- Document mappings in `docs/mapping_[datasource].md`
- Track which sources are mapped vs pending
- **At end of module**: Present module transition with completion checklist

### Module 5: SDK Setup

- Use `sdk_guide` with correct platform parameter
- **Check if Senzing is already installed before installing**
- Verify existing installation version and compatibility
- Skip installation if compatible version exists
- Check `anti_patterns` before recommending approaches
- Recommend SQLite for evaluation, PostgreSQL for production
- **For SQLite: Create `database/` directory and use `database/G2C.db` path**
- **Never use system paths like `/var/opt/senzing/sqlite/` for SQLite databases**
- Verify installation with test script
- Register all data sources from Module 1
- Create engine configuration
- Test database connection before proceeding

#### Docker Deployment Guidance

When user chooses Docker deployment:

- **Runtime images do NOT include PostgreSQL schema files** - cannot use `/opt/senzing/er/resources/schema/szcore-schema-postgresql-create.sql`
- **Use two-stage initialization pattern**:
  1. Create minimal SQL schema with correct column names (CRITICAL: sys_cfg.sys_create_dt NOT sys_create_date, sys_codes_used must have code_id)
  2. Insert sys_vars with VERSION='4.2.1' and SCHEMA_VERSION='4.0'
  3. Use SDK's `set_default_config()` to create remaining tables automatically
- **Critical schema requirements**:
  - sys_cfg table must use `sys_create_dt` column (NOT sys_create_date) or SDK fails with SENZ1001
  - sys_codes_used must include `code_id BIGSERIAL` column or SDK fails with SENZ1001
  - sys_vars must have correct structure: (var_group, var_code, var_value)
- **Container CMD should be `tail -f /dev/null`** to keep container running
- **Use `docker exec` to run commands** instead of container CMD
- **All Docker files must be in `docker/` directory** - never in project root
- Reference `steering/docker-deployment.md` for complete examples with correct schema
- Check `docs/guides/TROUBLESHOOTING_INDEX.md` for Docker-specific issues (SENZ1019, SENZ7223, SENZ1001 column errors)

### Module 6: Loading

- **Verify `.kiro/hooks/` exists** before installing hooks
- **Remind to backup** before loading (or use backup hook)
- **Offer to use loader templates** from `templates/` directory
- Create separate loading program for each data source
- Save programs in `src/load/`
- Test with small sample first (10-100 records)
- Use `generate_scaffold` for loading code
- Use `explain_error_code` for any errors
- Track loading statistics
- Generate dashboard showing results
- Track which sources are loaded vs pending
- **At end of module**: Present module transition with troubleshooting tips

### Module 7: Querying

- Review business problem from Module 1
- Design queries that answer specific business questions
- Use `generate_scaffold` for query code
- Save programs in `src/query/`
- Use `get_sdk_reference` for method signatures
- Never guess SDK method names
- Test queries and validate results
- Use `whyEntities` to understand matching behavior
- Document query programs
- Remind to complete lessons learned

## File Management

### Directory Structure

All source code must be in `src/`:

- `src/transform/` - Transformation programs (Python/Java/C#)
- `src/load/` - Loading programs (Python/Java/C#)
- `src/query/` - Query programs (Python/Java/C#)
- `src/utils/` - Utility modules (Python/Java/C#)
- `src/api/` - API endpoints (if applicable)

All shell scripts must be in `scripts/`:

- `scripts/deploy.sh` - Deployment automation
- `scripts/backup.sh` - Database backup
- `scripts/migrate_db.sh` - Database migration
- `scripts/run_pipeline.sh` - Pipeline execution
- `scripts/health_check.sh` - Health checks
- `scripts/setup_env.sh` - Environment setup

All data files must be in `data/`:

- `data/raw/` - Original source data
- `data/transformed/` - Senzing-formatted JSON
- `data/samples/` - Sample data for testing
- `data/backups/` - Database backups
- `data/temp/` - Temporary working files (gitignored)

All feedback files must be in `docs/feedback/`:

- `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` - User's improvement suggestions (created from template)
- `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md` - Template for feedback (provided by power)

**IMPORTANT**: Never place shell scripts (*.sh) in `src/` directory. Shell scripts are for automation and deployment, not application logic.

**CRITICAL**: Never use `/tmp` or other system temporary directories for project files. Always use appropriate project directories (`data/temp/` for temporary files, `~` for downloads).

### Documentation

Create and maintain:

- `docs/business_problem.md` - Module 1
- `docs/data_source_evaluation.md` - Module 2
- `docs/mapping_[datasource].md` - Module 3 (per source)
- `docs/query_specifications.md` - Module 6
- `docs/lessons_learned.md` - After Module 6
- `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md` - Throughout (user creates from template)
- `README.md` - Keep updated throughout

### Version Control

- Initialize git at start of Module 1
- Commit after each module completion
- Create .gitignore to exclude sensitive data
- Never commit .env files

## Progress Tracking

Maintain awareness of:

- Which module user is currently on
- Which modules are complete
- Which data sources need mapping
- Which data sources are loaded
- Any blockers or issues

Periodically remind users:

- "You've completed Module 3 for Customer CRM. Ready to move to Module 4?"
- "You have 2 more data sources to map before Module 4"
- "All data loaded! Let's create query programs in Module 6"

## Validation Gates

Before proceeding to next module, verify:

**Module 1 → Module 2**:

- ✅ Problem statement documented
- ✅ Data sources identified
- ✅ Success criteria defined

**Module 2 → Module 3**:

- ✅ All data sources collected
- ✅ Files in `data/raw/` or locations documented
- ✅ Data source locations documented

**Module 3 → Module 4**:

- ✅ All sources evaluated
- ✅ SGES compliance determined
- ✅ Sample data available

**Module 4 → Module 5**:

- ✅ All non-compliant sources mapped
- ✅ Transformation programs tested
- ✅ Quality validation passed (>70%)

**Module 5 → Module 6**:

- ✅ SDK installed
- ✅ Database configured
- ✅ Test script runs successfully

**Module 6 → Module 7**:

- ✅ All sources loaded
- ✅ No critical errors
- ✅ Loading statistics captured

**Module 7 → Complete**:

- ✅ Query programs answer business problem
- ✅ Results validated with user
- ✅ Documentation complete

## MCP Tool Usage

### Always Use MCP Tools For

- Attribute names → `mapping_workflow`
- SDK code → `generate_scaffold` or `sdk_guide`
- Method signatures → `get_sdk_reference`
- Error diagnosis → `explain_error_code`
- Documentation → `search_docs`
- Code examples → `find_examples`

### Never

- Hand-code Senzing JSON attribute names
- Guess SDK method names
- Use outdated patterns from training data
- Skip anti-pattern checks
- Proceed without validation

## Steering File Loading

Load steering files on-demand:

- `steering/steering.md` - Core workflows (always available)
- `steering/quick-reference.md` - MCP tool quick reference
- `steering/environment-setup.md` - Module 1, setup questions
- `steering/security-privacy.md` - Module 2, sensitive data
- `steering/cost-estimation.md` - Module 1 or 4, cost questions
- `steering/common-pitfalls.md` - Any module, troubleshooting
- `steering/lessons-learned.md` - After Module 6

**For generic topics, use MCP tools instead**:

- Testing strategies → `search_docs(query="testing best practices")`
- Performance monitoring → `search_docs(query="performance monitoring", category="performance")`
- Integration patterns → `find_examples(query="API integration")`
- Disaster recovery → `search_docs(query="backup and recovery")`
- Collaboration → Standard software engineering practices

## Error Handling

When user encounters errors:

1. Read error message carefully
2. Use `explain_error_code` if Senzing error
3. Check common pitfalls guide
4. Use `search_docs` for context
5. Provide specific solution, not generic advice
6. Verify fix before proceeding

## Communication Style

- Be supportive and encouraging
- Acknowledge progress and achievements
- Provide clear, actionable guidance
- Explain "why" not just "what"
- Use examples to illustrate concepts
- Admit when you need to use MCP tools
- Don't pretend to know - use tools to verify
- **Ask questions one at a time** - never present multiple questions in a single message
- **Wait for user response** before asking the next question
- When presenting options, ask which option they prefer rather than listing all details at once

## Quality Assurance

Before generating any code:

- Use appropriate MCP tool for guidance
- Include error handling
- Add progress logging
- Test with small sample first
- Document how to run it
- Save in correct `src/` directory

## Hooks Management

When installing hooks:

1. Check if `.kiro/hooks/` exists
2. Create with `mkdir -p .kiro/hooks` if needed
3. Copy hook files
4. Verify installation
5. Explain hook behavior
6. Commit to git

## State Management

For `mapping_workflow`:

- Always pass exact `state` from previous response
- Never modify or reconstruct state
- If state lost, start workflow over
- Each data source has separate workflow session

## Success Indicators

Recognize when modules are complete:

- Module 1: Problem statement + data sources + success metrics
- Module 2: All data sources collected + files in data/raw/ + locations documented
- Module 3: All sources categorized
- Module 4: Working transformation programs + quality >70%
- Module 5: SDK installed + test passes
- Module 6: All sources loaded + statistics captured
- Module 7: Query programs answer business problem

## When User is Stuck

1. Review what's been completed
2. Identify the blocker
3. Check common pitfalls
4. Use MCP tools to find solution
5. Provide step-by-step guidance
6. Offer to go back to previous module if needed

## Iterative Discovery

Remember:

- Users can move between modules
- Mapping is exploratory and iterative
- It's OK to go back and refine
- Discovery is non-linear
- Support flexibility while maintaining quality

### Module 8: Deployment Packaging

- Review all code from Modules 4, 6, and 7
- Guide user through deployment decisions:
  - Target database (PostgreSQL recommended)
  - Programming language (stick with boot camp language)
  - Deployment environment (Docker recommended)
  - Integration pattern (from Module 7)
- Refactor code into proper package structure
- Extract common functionality into utilities
- Add configuration management (YAML + environment variables)
- Implement comprehensive logging
- Create test suite with >80% coverage
- Apply language-specific packaging:
  - Python: setup.py + pyproject.toml + requirements.txt
  - Java: pom.xml or build.gradle
  - C#: .csproj with NuGet packages
  - Rust: Cargo.toml
- Generate deployment documentation:
  - docs/deployment.md
  - docs/configuration.md
  - docs/api.md (if REST API)
  - docs/monitoring.md
  - docs/troubleshooting.md
- Create deployment artifacts:
  - Dockerfile
  - docker-compose.yml
  - Deployment scripts
  - CI/CD pipeline configuration
  - Kubernetes manifests (if applicable)
- Validate package:
  - Run all tests
  - Check code quality (linting, type checking)
  - Test Docker build
  - Test deployment in staging
  - Verify documentation completeness
- Create release notes and tag version
- Document lessons learned
- Prepare handoff to operations team

### Module 12 Completion

- **Remind user to share feedback**: At the end of Module 12, say:
  - "🎉 Congratulations on completing the Senzing Boot Camp!"
  - "If you have any feedback about your experience, say 'power feedback' or 'bootcamp feedback' and I'll help you document it"
  - "If you've already documented feedback in `docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK.md`, please share that file with the power author"
  - "Your feedback helps improve the boot camp for future users!"
- Encourage them to include any final thoughts about the overall boot camp experience

## Code Quality Standards

All Python code must follow PEP-8 standards as defined in Core Principle #10 above. See `docs/policies/PEP8_COMPLIANCE.md` for complete details.

### Code Quality Checks

Before completing any module that generates code:

1. Verify PEP-8 compliance
2. Check for proper error handling
3. Verify logging is present
4. Ensure docstrings are complete
5. Check for security issues (no hardcoded credentials)
6. Verify file paths use Path objects, not strings
7. Check that all imports are used
8. Verify proper exception handling

### Tools for Validation

Recommend these tools to users:

- `pycodestyle` or `flake8` for PEP-8 checking
- `pylint` for code quality
- `black` for automatic formatting
- `mypy` for type checking
- `bandit` for security scanning

Example validation command:

```bash
# Check PEP-8 compliance
pycodestyle --max-line-length=100 src/

# Auto-format code
black --line-length=100 src/

# Check code quality
pylint src/
```
