# Agent Instructions - Consolidated Behavior Guide

This document consolidates all agent behavior instructions from across the boot camp.

## Core Principles

1. **Always call `get_capabilities` first** when starting a Senzing session
2. **Never hand-code** Senzing JSON mappings or SDK method calls from memory
3. **Use MCP tools** for all Senzing-specific operations
4. **Track progress** through modules and remind users periodically
5. **Validate before proceeding** - each module has success criteria
6. **Save all code in `src/`** - never place source code in project root
7. **Ask questions one at a time** - when multiple questions are needed, ask them sequentially and wait for each response before asking the next. This prevents overwhelming users with long lists of questions.
8. **Use project directories for all files** - never use `/tmp` or system directories:
   - Source code → `src/`
   - Shell scripts → `scripts/`
   - Documentation → `docs/`
   - Data files → `data/`
   - SQLite databases → `database/`
   - Configuration → `config/`
   - Docker files → `docker/` (NEVER in project root)
9. **All Python code must be PEP-8 compliant**:
   - Maximum line length: 100 characters (for readability)
   - No trailing whitespace
   - Two blank lines between top-level functions/classes
   - One blank line between methods
   - Imports at top of file (standard library, third-party, local)
   - Use 4 spaces for indentation (never tabs)
   - Use snake_case for functions and variables
   - Use PascalCase for classes
   - Add docstrings to all functions, classes, and modules

## Module-Specific Behaviors

### Module 0: Quick Demo
- Use `get_sample_data` to retrieve CORD datasets
- Use `generate_scaffold` with `full_pipeline` for demo scripts
- **Create `src/quickstart_demo/` directory for all demo code**
- Save demo script to `src/quickstart_demo/demo_[dataset_name].py`
- Save sample data to `src/quickstart_demo/sample_data_[dataset_name].jsonl`
- Show entity resolution in action with real examples
- Connect demo results to user's potential use case

### Module 1: Business Problem
- **Offer design pattern gallery** at the start
- If pattern selected, use it to guide problem definition
- **Ask discovery questions ONE AT A TIME** - wait for user response before asking next question
- Never ask multiple questions in a single message
- Encourage visual explanations (diagrams)
- Create `docs/business_problem.md`
- Update README.md with overview
- Help create project directory structure
- **Check if directory is already a git repository** before initializing
- If not a git repository, ask user if they want to initialize git
- If yes, initialize git and create .gitignore
- If already a git repository, acknowledge and proceed

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

**IMPORTANT**: Never place shell scripts (*.sh) in `src/` directory. Shell scripts are for automation and deployment, not application logic.

**CRITICAL**: Never use `/tmp` or other system temporary directories for project files. Always use appropriate project directories (`data/temp/` for temporary files, `~` for downloads).

### Documentation
Create and maintain:
- `docs/business_problem.md` - Module 1
- `docs/data_source_evaluation.md` - Module 2
- `docs/mapping_[datasource].md` - Module 3 (per source)
- `docs/query_specifications.md` - Module 6
- `docs/lessons_learned.md` - After Module 6
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

### Always Use MCP Tools For:
- Attribute names → `mapping_workflow`
- SDK code → `generate_scaffold` or `sdk_guide`
- Method signatures → `get_sdk_reference`
- Error diagnosis → `explain_error_code`
- Documentation → `search_docs`
- Code examples → `find_examples`

### Never:
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
- `steering/testing-strategy.md` - Module 3, testing questions
- `steering/performance-monitoring.md` - Module 5, performance questions
- `steering/recovery-procedures.md` - Before Module 5, errors
- `steering/collaboration.md` - Team projects
- `steering/cost-estimation.md` - Module 1 or 4, cost questions
- `steering/integration-patterns.md` - Module 6, integration questions
- `steering/common-pitfalls.md` - Any module, troubleshooting
- `steering/lessons-learned.md` - After Module 6

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

## Code Quality Standards

### Python Code Standards (PEP-8 Compliance)

All Python code generated during the boot camp must follow PEP-8 standards:

**Line Length**:
- Maximum 100 characters per line (more readable than strict 79)
- Break long lines using parentheses, not backslashes
- Break long function calls across multiple lines

**Whitespace**:
- No trailing whitespace on any line
- Two blank lines between top-level functions and classes
- One blank line between methods in a class
- One space after commas in lists, tuples, and function arguments
- No spaces around = in keyword arguments

**Naming Conventions**:
- `snake_case` for functions, variables, and module names
- `PascalCase` for class names
- `UPPER_CASE` for constants
- Descriptive names (avoid single letters except in loops)

**Imports**:
- All imports at top of file
- Group imports: standard library, third-party, local
- One import per line (except `from x import a, b`)
- Alphabetical order within groups

**Documentation**:
- Module docstring at top of file
- Docstring for every function and class
- Use triple quotes for docstrings
- Include purpose, parameters, and return values

**Example of PEP-8 Compliant Code**:
```python
#!/usr/bin/env python3
"""
Module for transforming customer data to Senzing format.

This module provides functions to read CSV files and transform
them into Senzing JSON format.
"""

import json
import sys
from pathlib import Path

# Constants
DATA_SOURCE = "CUSTOMERS"
MAX_RECORDS = 10000


def transform_record(source_record):
    """
    Transform a source record to Senzing JSON format.

    Args:
        source_record (dict): Source data record

    Returns:
        dict: Senzing-formatted record
    """
    return {
        "DATA_SOURCE": DATA_SOURCE,
        "RECORD_ID": source_record.get("id"),
        "NAME_FULL": source_record.get("name"),
        "EMAIL_ADDRESS": source_record.get("email")
    }


def main():
    """Main entry point."""
    # Implementation here
    pass


if __name__ == "__main__":
    sys.exit(main())
```

**When Generating Code**:
1. Always generate PEP-8 compliant code from the start
2. Use proper indentation (4 spaces)
3. Add docstrings to all functions
4. Keep lines under 100 characters
5. Remove trailing whitespace
6. Use proper naming conventions

**When User Provides Code**:
1. Check for PEP-8 compliance
2. Suggest fixes if non-compliant
3. Explain why compliance matters (readability, maintainability)
4. Offer to fix issues automatically

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
