---
inclusion: manual
---

# Module Prerequisites

Before starting each module, ensure prerequisites are met. This guide helps you verify you're ready to proceed.

## Module 0: Set Up SDK

**Prerequisites**:

- ✅ Module 5 complete (all sources mapped) OR
- ✅ All sources are SGES-compliant
- ✅ Platform/environment ready

**Recommended**:

- Admin/sudo access for installation
- 10GB free disk space
- Internet connection for downloads

**Ready to proceed when**:

- You have transformed data ready to load OR
- You have SGES-compliant data ready to load
- You have installation permissions
- You've chosen database type (SQLite or PostgreSQL)

**Common blockers**:

- Missing admin access → Request permissions from IT
- Insufficient disk space → Free up space or use external storage
- Network restrictions → Work with IT to allow downloads

**Skip if**:

- Senzing is already installed → Verify with `G2ConfigMgr.py` or similar

## Module 1: Quick Demo (Optional)

**Prerequisites**:

- No prerequisites

**Recommended**:

- 10-15 minutes of uninterrupted time
- Curiosity about entity resolution

**Skip if**:

- You're already familiar with Senzing
- You want to dive directly into your own project

## Module 2: Understand Business Problem

**Prerequisites**:

- No prerequisites

**Recommended**:

- Have business problem in mind
- Understand your organization's pain points
- Know who will use the entity resolution results

**Ready to proceed when**:

- You can articulate the business problem in 2-3 sentences
- You know what success looks like

## Module 3: Identify and Collect Data Sources

**Prerequisites**:

- ✅ Module 2 complete (business problem defined)
- ✅ Data sources identified in Module 2

**Recommended**:

- Access to data source systems
- Permissions to extract sample data
- Understanding of data formats (CSV, JSON, database, API)

**Ready to proceed when**:

- You have a list of data sources to work with
- You know where each data source is located
- You have access permissions to extract data

**Common blockers**:

- Missing access permissions → Request access from data owners
- Unknown data locations → Review Module 2 problem statement
- Too many sources → Start with 1-2 most important sources

## Module 4: Evaluate Data Quality

**Prerequisites**:

- ✅ Module 3 complete (data sources collected)
- ✅ Data files in `data/raw/` directory
- ✅ Sample data available for evaluation

**Recommended**:

- Representative sample of each data source (1000-10000 records)
- Understanding of expected data quality
- Knowledge of critical attributes for matching

**Ready to proceed when**:

- Data files are in `data/raw/` directory
- You can open and view the data files
- You understand the data format (CSV, JSON, etc.)

**Common blockers**:

- Data files too large → Extract representative sample
- Data in proprietary format → Convert to CSV or JSON
- Missing data files → Return to Module 3

## Module 5: Map Your Data

**Prerequisites**:

- ✅ Module 4 complete (sources evaluated)
- ✅ Non-compliant sources identified
- ✅ Quality scores reviewed

**Recommended**:

- Understanding of source data fields
- Knowledge of which fields are important for matching
- Sample records for testing transformations

**Ready to proceed when**:

- You know which sources need mapping (non-SGES sources)
- You understand the source data structure
- You have quality scores from Module 4

**Common blockers**:

- Unclear field meanings → Consult data source documentation
- Complex data structures → Start with simple fields first
- Poor data quality → Document quality issues, proceed with mapping

**Skip if**:

- All sources are already SGES-compliant → Go directly to Module 0

## Module 6: Load Single Data Source

**Prerequisites**:

- ✅ Module 0 complete (SDK installed)
- ✅ Database configured
- ✅ At least one transformed data source ready

**Recommended**:

- Backup of empty database (before first load)
- Understanding of data source size
- Time estimate for loading (based on record count)

**Ready to proceed when**:

- SDK is installed and verified
- Database is initialized
- You have at least one transformed data file in `data/transformed/`
- You've tested SDK with a small sample

**Common blockers**:

- SDK not working → Return to Module 0, verify installation
- Database not initialized → Run initialization commands
- No transformed data → Return to Module 5

**Skip if**:

- Data is already loaded → Verify with query, then go to Module 8

## Module 7: Multi-Source Orchestration

**Prerequisites**:

- ✅ Module 6 complete (first source loaded successfully)
- ✅ Multiple data sources to orchestrate
- ✅ Loading statistics reviewed for first source

**Recommended**:

- Understanding of data source dependencies
- Knowledge of data source sizes
- Plan for load order

**Ready to proceed when**:

- First data source is loaded successfully
- You have 2+ additional sources to load
- You understand which sources depend on others

**Common blockers**:

- First load failed → Return to Module 6, troubleshoot
- Only one data source → Skip this module, go to Module 8
- Unclear dependencies → Document assumptions, proceed

**Skip if**:

- Only working with single data source → Go directly to Module 8

## Module 8: Query and Validate Results

**Prerequisites**:

- ✅ Module 7 complete (all sources loaded) OR
- ✅ Module 6 complete (single source loaded)
- ✅ No critical loading errors

**Recommended**:

- Understanding of expected results
- Test cases or validation criteria
- Business users available for UAT

**Ready to proceed when**:

- Data is loaded successfully
- Loading statistics look reasonable
- No critical errors in loading logs

**Common blockers**:

- Loading errors → Review logs, fix issues, reload
- Unexpected entity counts → Investigate with queries
- Missing data → Verify transformation and loading

**Skip if**:

- You've already validated results → Go to Module 9 or 12

## Module 9: Performance Testing and Benchmarking

**Prerequisites**:

- ✅ Module 8 complete (queries working)
- ✅ Representative data loaded
- ✅ Test environment available

**Recommended**:

- Performance requirements defined
- Baseline metrics captured
- Monitoring tools available

**Ready to proceed when**:

- Queries are working correctly
- You have representative data volume
- You know performance requirements

**Common blockers**:

- Queries not working → Return to Module 8
- Insufficient data volume → Load more data or use projections
- No performance requirements → Define acceptable thresholds

**Skip if**:

- Performance is not critical for your use case
- You're doing proof-of-concept only

## Module 10: Security Hardening

**Prerequisites**:

- ✅ Module 9 complete (performance validated)
- ✅ Security requirements identified
- ✅ Compliance needs documented

**Recommended**:

- Understanding of security requirements
- Knowledge of compliance needs (GDPR, HIPAA, etc.)
- Security scanning tools available

**Ready to proceed when**:

- Performance is acceptable
- You know security requirements
- You understand compliance obligations

**Common blockers**:

- Unclear security requirements → Consult security team
- No compliance documentation → Research applicable regulations
- Missing security tools → Identify and install tools

**Skip if**:

- Internal use only with no sensitive data
- Proof-of-concept environment only

## Module 11: Monitoring and Observability

**Prerequisites**:

- ✅ Module 10 complete (security hardened)
- ✅ Monitoring tools selected
- ✅ Production environment identified

**Recommended**:

- Monitoring platform available (Prometheus, Datadog, etc.)
- Logging infrastructure in place
- Alerting system configured

**Ready to proceed when**:

- Security is hardened
- You have monitoring tools available
- You know what metrics to track

**Common blockers**:

- No monitoring platform → Select and install platform
- Unclear metrics → Define key performance indicators
- No alerting system → Set up basic alerting

**Skip if**:

- Basic monitoring is sufficient
- Not deploying to production

## Module 12: Package and Deploy

**Prerequisites**:

- ✅ Module 11 complete (monitoring configured)
- ✅ All tests passing
- ✅ Deployment target confirmed

**Recommended**:

- Deployment environment ready
- CI/CD pipeline configured
- Rollback plan documented

**Ready to proceed when**:

- All previous modules complete
- Tests are passing
- You have deployment target identified
- You have deployment permissions

**Common blockers**:

- Tests failing → Fix issues, return to relevant module
- No deployment target → Identify target environment
- Missing permissions → Request deployment access

**Skip if**:

- Not deploying to production
- Staying in development/test environment

## Quick Reference: Module Dependencies

```text
Module 0 (Set Up SDK) → Requires Module 5 (or SGES data)
Module 1 (Optional) → No dependencies
Module 2 → No dependencies
Module 3 → Requires Module 2
Module 4 → Requires Module 3
Module 5 → Requires Module 4 (or skip if SGES-compliant)
Module 6 → Requires Module 0
Module 7 → Requires Module 6 (or skip if single source)
Module 8 → Requires Module 6 or 7
Module 9 → Requires Module 8 (or skip if not needed)
Module 10 → Requires Module 9 (or skip if not needed)
Module 11 → Requires Module 10 (or skip if not needed)
Module 12 → Requires Module 11 (or skip if not deploying)
```

## Agent Behavior

When user wants to start a module:

1. Check prerequisites for that module
2. If prerequisites not met, inform user and suggest completing prerequisite modules first
3. If prerequisites met, proceed with the module
4. If user insists on skipping prerequisites, warn about potential issues but allow them to proceed

When user is stuck:

1. Review prerequisites for current module
2. Identify which prerequisite is not met
3. Guide user back to complete missing prerequisite
4. Once prerequisite is met, return to current module
