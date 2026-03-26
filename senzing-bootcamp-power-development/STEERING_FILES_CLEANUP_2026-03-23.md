# Steering Files Cleanup - March 23, 2026

## Summary

Moved 9 generic steering files from the Power distribution to the development repository. These files contained standard software engineering practices rather than boot camp-specific guidance. The MCP server provides this information dynamically.

## Files Moved (9 files)

### Generic Best Practices (3 files)

1. **logging-standards.md**
   - Generic logging best practices
   - Replacement: `search_docs(query="logging best practices")`

2. **testing-strategy.md**
   - Unit tests, integration tests, data quality tests
   - Replacement: `search_docs(query="testing best practices")`

3. **performance-monitoring.md**
   - Benchmarking, monitoring dashboards, health checks
   - Replacement: `search_docs(query="performance monitoring", category="performance")`

### Generic Patterns (3 files)

4. **api-gateway-patterns.md**

   - API integration patterns
   - Replacement: `find_examples(query="API gateway")`

5. **integration-patterns.md**

   - REST API, batch export, streaming, database sync
   - Replacement: `find_examples(query="integration patterns")`

6. **multi-environment-strategy.md**

   - Dev/staging/prod strategy
   - Replacement: `search_docs(query="multi-environment deployment")`

### Advanced Operations (3 files)

7. **disaster-recovery.md**

   - Backup, rollback, disaster recovery
   - Replacement: `search_docs(query="disaster recovery")`

8. **recovery-procedures.md**

   - Error recovery procedures
   - Replacement: `search_docs(query="backup and recovery")`

9. **collaboration.md**

   - Team workflows, code review, handoff procedures
   - Replacement: Standard software engineering practices

## Rationale

### Why Remove These Files?

1. **Generic Content**: These files contain standard software engineering practices, not boot camp-specific guidance
2. **MCP Server Coverage**: The Senzing MCP server provides this information dynamically
3. **Maintenance Burden**: Static copies of generic best practices require unnecessary maintenance
4. **Always Current**: MCP tools provide up-to-date information automatically
5. **Duplication**: These topics are covered better by external resources and MCP server

### What Makes Content "Generic"?

Content is considered generic if:

- It applies to any software project, not just Senzing boot camp
- It's standard industry practice (logging, testing, monitoring, DR)
- It's not specific to the boot camp learning experience
- The MCP server or external resources cover it adequately

## Files Kept (16 files)

### Core Workflows (5 files)

1. steering.md - Main workflow guide (2355 lines, boot camp-specific)
2. agent-instructions.md - Agent behavior for boot camp
3. quick-reference.md - MCP tool reference organized by modules
4. modules-7-12-workflows.md - Advanced module workflows
5. NEW_WORKFLOWS_PHASE5.md - Module 7 orchestration (to be merged)

### Boot Camp Support (11 files)

6. common-pitfalls.md - Boot camp-specific troubleshooting
7. troubleshooting-decision-tree.md - Diagnostic tree for learners
8. complexity-estimator.md - Project estimation for Module 1
9. cost-estimation.md - Cost calculation for Module 1
10. lessons-learned.md - Post-boot camp reflection
11. docker-deployment.md - Critical Docker patterns and schema fixes
12. security-privacy.md - Data privacy reminders for learners
13. incremental-loading.md - Senzing-specific loading patterns
14. data-lineage.md - Data source tracking for Module 2
15. environment-setup.md - Environment configuration
16. uat-framework.md - UAT framework for Module 8

## References Updated

Updated all references in:

### Core Documentation

- **POWER.md** - Removed 5 file references, added MCP tool guidance
- **agent-instructions.md** - Updated steering file loading section

### Module Documentation

- **MODULE_6_SINGLE_SOURCE_LOADING.md** - 2 references updated
- **MODULE_8_QUERY_VALIDATION.md** - 1 reference updated
- **MODULE_9_PERFORMANCE_TESTING.md** - 1 reference updated
- **MODULE_11_MONITORING_OBSERVABILITY.md** - 1 reference updated
- **MODULE_12_DEPLOYMENT_PACKAGING.md** - 1 reference updated

### Guides

- **docs/guides/README.md** - 2 references updated
- **docs/guides/TROUBLESHOOTING_INDEX.md** - 4 references updated

### Steering Files

- **steering/uat-framework.md** - 1 reference updated
- **steering/steering.md** - 3 references updated
- **steering/NEW_WORKFLOWS_PHASE5.md** - 6 references updated

**Total References Updated**: 22 locations

## Impact

### Distribution Size

- **Before**: 25 steering files
- **After**: 16 steering files
- **Reduction**: 36% fewer files

### Benefits

1. **Clearer Focus**: Steering files now focus exclusively on boot camp-specific content
2. **Less Duplication**: No overlap with MCP server functionality
3. **Easier Maintenance**: Fewer files to keep in sync
4. **Always Current**: MCP server provides up-to-date information
5. **Better User Experience**: Users get dynamic, current information instead of static docs

### MCP Tool Replacements

| Removed File | MCP Tool Replacement |
|--------------|---------------------|
| logging-standards.md | `search_docs(query="logging best practices")` |
| testing-strategy.md | `search_docs(query="testing best practices")` |
| performance-monitoring.md | `search_docs(query="performance monitoring", category="performance")` |
| api-gateway-patterns.md | `find_examples(query="API gateway")` |
| integration-patterns.md | `find_examples(query="integration patterns")` |
| multi-environment-strategy.md | `search_docs(query="multi-environment deployment")` |
| disaster-recovery.md | `search_docs(query="disaster recovery")` |
| recovery-procedures.md | `search_docs(query="backup and recovery")` |
| collaboration.md | Standard software engineering practices |

## Verification

### No Broken References

```bash
# Verified all references updated
grep -r "logging-standards\|testing-strategy\|performance-monitoring" senzing-bootcamp/**/*.md
# Result: No matches ✅

grep -r "api-gateway-patterns\|integration-patterns\|multi-environment-strategy" senzing-bootcamp/**/*.md
# Result: No matches ✅

grep -r "disaster-recovery\|recovery-procedures\|collaboration\.md" senzing-bootcamp/**/*.md
# Result: No matches ✅
```

### File Counts Verified

- **Power steering/**: 16 files ✅
- **Development steering/**: 9 files ✅
- **Total**: 25 files (no files lost) ✅

## Design Philosophy

This cleanup reinforces the Power's core design philosophy:

> **Leverage the MCP server for generic content, keep only boot camp-specific content in the Power distribution.**

### What Belongs in Steering Files?

✅ **Include**:

- Boot camp-specific workflows and processes
- Learning path structure and guidance
- Progress tracking and module transitions
- Boot camp-specific troubleshooting
- Critical deployment patterns (Docker schema fixes)
- Data privacy reminders for learners

❌ **Exclude**:

- Generic software engineering practices
- Standard DevOps procedures
- Generic testing/monitoring/logging guidance
- API patterns available via MCP
- Content covered by MCP server

## For Future Maintainers

### When Adding New Steering Files

Ask these questions:

1. **Is this boot camp-specific?**
   - If no → Don't add it

2. **Does the MCP server provide this?**
   - If yes → Use MCP tool instead

3. **Is this generic best practice?**
   - If yes → Reference external resources

4. **Is this critical for learners?**
   - If no → Move to development repository

### MCP Server Tools Reference

Before creating static documentation, check if MCP provides it:

- `get_capabilities` - Version info, tool list
- `search_docs` - Comprehensive Senzing documentation
- `sdk_guide` - Platform-specific SDK setup
- `find_examples` - Working code examples
- `generate_scaffold` - SDK code generation
- `mapping_workflow` - Data mapping guidance
- `explain_error_code` - Error diagnosis
- `get_sample_data` - Sample datasets

## Related Reorganizations

This is Phase 5 of the ongoing cleanup effort:

- **Phase 1**: Moved 34 internal development files (March 17-21, 2026)
- **Phase 2**: Removed 15 redundant guide files (March 23, 2026)
- **Phase 3**: Removed 3 static demo scripts (March 23, 2026)
- **Phase 4**: Removed 1 build artifact (March 23, 2026)
- **Phase 5**: Removed 9 generic steering files (March 23, 2026) ← This document

## Total Reorganization Summary

**Files moved to development repository**: 64 files

- 34 internal development files
- 15 redundant guide files + 2 PDFs
- 3 static demo scripts
- 1 build artifact
- 9 generic steering files

**Result**: Significantly leaner Power distribution focused on boot camp-specific content with all generic content replaced by MCP server tools.

## Version

- **Date**: March 23, 2026
- **Phase**: 5 (Steering Files Cleanup)
- **Files Moved**: 9
- **Cumulative Total**: 64 files moved to development
