# Removed Steering Files

This directory contains steering files that were removed from the Power distribution because they contain generic best practices rather than boot camp-specific content.

## Why These Were Removed

These files were moved to the development repository on March 23, 2026 because:

1. **Generic Content**: They contain standard software engineering practices, not boot camp-specific guidance
2. **MCP Server Coverage**: The Senzing MCP server provides this information dynamically through `search_docs` and `find_examples`
3. **Maintenance Burden**: Keeping static copies of generic best practices creates unnecessary maintenance
4. **Always Current**: MCP tools provide up-to-date information automatically

## Files in This Directory (9 files)

### Generic Best Practices (3 files)

1. **logging-standards.md** - Generic logging best practices
   - **Replacement**: Use `search_docs(query="logging best practices")`
   - **Reason**: Standard software engineering practice

2. **testing-strategy.md** - Unit tests, integration tests, data quality tests
   - **Replacement**: Use `search_docs(query="testing best practices")`
   - **Reason**: Standard software engineering practice

3. **performance-monitoring.md** - Benchmarking, monitoring dashboards, health checks
   - **Replacement**: Use `search_docs(query="performance monitoring", category="performance")`
   - **Reason**: Generic monitoring practices

### Generic Patterns (3 files)

4. **api-gateway-patterns.md** - API integration patterns
   - **Replacement**: Use `find_examples(query="API gateway")` or `search_docs(query="API integration")`
   - **Reason**: Generic API patterns, not boot camp-specific

5. **integration-patterns.md** - REST API, batch export, streaming, database sync
   - **Replacement**: Use `find_examples(query="integration patterns")`
   - **Reason**: Generic integration patterns

6. **multi-environment-strategy.md** - Dev/staging/prod strategy
   - **Replacement**: Use `search_docs(query="multi-environment deployment")`
   - **Reason**: Generic DevOps practice

### Advanced Operations (3 files)

7. **disaster-recovery.md** - Backup, rollback, disaster recovery
   - **Replacement**: Use `search_docs(query="disaster recovery")`
   - **Reason**: Generic DR best practices, too advanced for boot camp

8. **recovery-procedures.md** - Error recovery procedures
   - **Replacement**: Use `search_docs(query="backup and recovery")` or `explain_error_code`
   - **Reason**: MCP server handles error diagnosis

9. **collaboration.md** - Team workflows, code review, handoff procedures
   - **Replacement**: Standard software engineering practices
   - **Reason**: Generic team practices, not Senzing-specific

## What Remains in Power (16 files)

The Power distribution now contains only boot camp-specific steering files:

**Core Workflows (5 files)**:
- steering.md - Main workflow guide
- agent-instructions.md - Agent behavior
- quick-reference.md - MCP tool reference
- modules-7-12-workflows.md - Advanced modules
- NEW_WORKFLOWS_PHASE5.md - Module 7 orchestration (to be merged)

**Boot Camp Support (11 files)**:
- common-pitfalls.md - Boot camp troubleshooting
- troubleshooting-decision-tree.md - Diagnostic tree
- complexity-estimator.md - Project estimation
- cost-estimation.md - Cost calculation
- lessons-learned.md - Post-project reflection
- docker-deployment.md - Critical Docker patterns
- security-privacy.md - Data privacy reminders
- incremental-loading.md - Senzing-specific patterns
- data-lineage.md - Data tracking
- environment-setup.md - Environment configuration
- uat-framework.md - UAT framework

## Impact

**Before**: 25 steering files  
**After**: 16 steering files  
**Reduction**: 36% fewer files

## For Future Maintainers

When considering adding new steering files, ask:

1. **Is this boot camp-specific?** If no, don't add it
2. **Does the MCP server provide this?** If yes, use MCP tools instead
3. **Is this generic best practice?** If yes, reference external resources
4. **Is this critical for learners?** If no, move to development

## References Updated

All references to these files have been updated in:
- POWER.md
- agent-instructions.md
- Module documentation (MODULE_6, MODULE_8, MODULE_9, MODULE_11, MODULE_12)
- docs/guides/README.md
- docs/guides/TROUBLESHOOTING_INDEX.md
- steering/uat-framework.md
- steering/steering.md
- steering/NEW_WORKFLOWS_PHASE5.md

## Date

**Moved**: March 23, 2026  
**Phase**: 5 (Steering Files Cleanup)  
**Files Moved**: 9 files

