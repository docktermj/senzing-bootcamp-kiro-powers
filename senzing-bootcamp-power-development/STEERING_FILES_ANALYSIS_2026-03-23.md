# Steering Files Analysis - March 23, 2026

## Question

Are all 25 steering files in `senzing-bootcamp/steering/` necessary for the boot camp?

## Analysis

### Files by Inclusion Type

**Always Included (9 files)** - Loaded automatically:

1. agent-instructions.md - Core agent behavior and workflows
2. common-pitfalls.md - Troubleshooting guidance
3. complexity-estimator.md - Project complexity assessment
4. logging-standards.md - Logging best practices
5. modules-7-12-workflows.md - Advanced module workflows
6. quick-reference.md - MCP tool quick reference
7. security-privacy.md - Security and privacy guidance
8. steering.md - Main workflow guide (2355 lines)
9. troubleshooting-decision-tree.md - Diagnostic decision tree

**Manual Inclusion (15 files)** - Loaded only when explicitly referenced:
10. api-gateway-patterns.md - API integration patterns
11. collaboration.md - Team collaboration guidance
12. cost-estimation.md - Cost calculation guidance
13. data-lineage.md - Data lineage tracking
14. disaster-recovery.md - Backup and recovery procedures
15. docker-deployment.md - Docker deployment patterns
16. environment-setup.md - Environment configuration
17. incremental-loading.md - Incremental update patterns
18. integration-patterns.md - System integration patterns
19. lessons-learned.md - Post-project reflection
20. multi-environment-strategy.md - Dev/staging/prod strategy
21. performance-monitoring.md - Performance tracking
22. recovery-procedures.md - Error recovery procedures
23. testing-strategy.md - Testing approaches
24. uat-framework.md - User acceptance testing

**Uncategorized (1 file)**:
25. NEW_WORKFLOWS_PHASE5.md - Module 7-12 workflow additions

## Evaluation Criteria

For each file, assess:

1. **Boot camp-specific?** - Is this unique to the boot camp learning experience?
2. **MCP server duplicate?** - Does the MCP server provide this information?
3. **Generic best practice?** - Is this general software engineering guidance?
4. **Actually used?** - Is it referenced in workflows or documentation?

## Detailed Analysis

### KEEP - Boot Camp-Specific (Core Workflows)

#### 1. steering.md (2355 lines)

- **Status**: KEEP
- **Reason**: Core boot camp workflows for all 13 modules
- **Boot camp-specific**: Yes - guides users through structured learning path
- **Usage**: Referenced constantly throughout boot camp

#### 2. agent-instructions.md

- **Status**: KEEP
- **Reason**: Agent behavior specific to boot camp workflows
- **Boot camp-specific**: Yes - directory structure creation, module transitions, progress tracking
- **Usage**: Core agent behavior guide

#### 3. quick-reference.md

- **Status**: KEEP
- **Reason**: Quick reference for MCP tools in boot camp context
- **Boot camp-specific**: Yes - organized by boot camp modules
- **Usage**: Frequently referenced during modules

#### 4. modules-7-12-workflows.md

- **Status**: KEEP
- **Reason**: Advanced module workflows (performance, security, monitoring, deployment)
- **Boot camp-specific**: Yes - structured learning for production readiness
- **Usage**: Modules 7-12

#### 5. NEW_WORKFLOWS_PHASE5.md

- **Status**: KEEP (but should be merged into steering.md or modules-7-12-workflows.md)
- **Reason**: Contains Module 7 orchestration workflow
- **Boot camp-specific**: Yes
- **Action**: Merge into appropriate file, then move to development

### KEEP - Boot Camp-Specific (Support Files)

#### 6. common-pitfalls.md

- **Status**: KEEP
- **Reason**: Boot camp-specific troubleshooting (common mistakes during learning)
- **Boot camp-specific**: Yes - addresses issues learners encounter
- **Usage**: Referenced when users get stuck

#### 7. troubleshooting-decision-tree.md

- **Status**: KEEP
- **Reason**: Diagnostic tree for boot camp issues
- **Boot camp-specific**: Yes - guides learners through problem-solving
- **Usage**: Referenced during troubleshooting

#### 8. complexity-estimator.md

- **Status**: KEEP
- **Reason**: Helps users estimate project scope during Module 1
- **Boot camp-specific**: Yes - part of business problem workflow
- **Usage**: Module 1

#### 9. cost-estimation.md

- **Status**: KEEP
- **Reason**: Helps users estimate costs during Module 1
- **Boot camp-specific**: Yes - part of business problem workflow
- **Usage**: Module 1

#### 10. lessons-learned.md

- **Status**: KEEP
- **Reason**: Post-boot camp reflection template
- **Boot camp-specific**: Yes - captures learning experience
- **Usage**: After Module 12

### QUESTIONABLE - Generic Best Practices

#### 11. logging-standards.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic logging best practices, not boot camp-specific
- **MCP duplicate**: Partially - `search_docs` covers logging
- **Generic**: Yes - standard software engineering practice
- **Usage**: Referenced in code generation
- **Recommendation**: Could be replaced by MCP search_docs queries

#### 12. security-privacy.md

- **Status**: KEEP (but could be simplified)
- **Reason**: Important reminders for learners handling sensitive data
- **MCP duplicate**: Partially - `search_docs` covers security
- **Generic**: Partially - some boot camp-specific guidance
- **Usage**: Module 2 (data collection)
- **Recommendation**: Keep but simplify to boot camp-specific reminders

#### 13. testing-strategy.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic testing best practices
- **MCP duplicate**: No
- **Generic**: Yes - standard software engineering
- **Usage**: Modules 9-12
- **Recommendation**: Could be replaced by general testing resources

#### 14. performance-monitoring.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic monitoring best practices
- **MCP duplicate**: Partially - `search_docs` covers performance
- **Generic**: Yes - standard DevOps practice
- **Usage**: Module 11
- **Recommendation**: Could be replaced by MCP search_docs queries

### QUESTIONABLE - Deployment Patterns

#### 15. docker-deployment.md

- **Status**: KEEP (critical for boot camp)
- **Reason**: Contains boot camp-specific Docker patterns and critical schema fixes
- **MCP duplicate**: Partially - `sdk_guide` covers Docker, but not schema issues
- **Boot camp-specific**: Yes - addresses common learner issues (SENZ1001 errors)
- **Usage**: Module 5 (SDK setup with Docker)
- **Recommendation**: KEEP - contains critical troubleshooting for Docker deployments

#### 16. api-gateway-patterns.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic API integration patterns
- **MCP duplicate**: Partially - `find_examples` provides code examples
- **Generic**: Yes - standard API patterns
- **Usage**: Module 12 (optional)
- **Recommendation**: Move to development - too generic

#### 17. integration-patterns.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic system integration patterns
- **MCP duplicate**: Partially - `find_examples` provides examples
- **Generic**: Yes - standard integration patterns
- **Usage**: Module 12 (optional)
- **Recommendation**: Move to development - too generic

#### 18. multi-environment-strategy.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic dev/staging/prod strategy
- **MCP duplicate**: No
- **Generic**: Yes - standard DevOps practice
- **Usage**: Module 12
- **Recommendation**: Move to development - too generic

### QUESTIONABLE - Advanced Topics

#### 19. disaster-recovery.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic DR best practices
- **MCP duplicate**: No
- **Generic**: Yes - standard operations practice
- **Usage**: Module 11 (optional)
- **Recommendation**: Move to development - too generic for boot camp

#### 20. recovery-procedures.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic error recovery procedures
- **MCP duplicate**: Partially - `explain_error_code` handles errors
- **Generic**: Yes - standard error handling
- **Usage**: Throughout (optional)
- **Recommendation**: Move to development - MCP tools handle this

#### 21. incremental-loading.md

- **Status**: KEEP (but could be simplified)
- **Reason**: Important pattern for production deployments
- **MCP duplicate**: Partially - `search_docs` covers incremental loading
- **Generic**: Partially - Senzing-specific patterns
- **Usage**: Module 7
- **Recommendation**: Keep but verify it's not duplicating MCP content

#### 22. data-lineage.md

- **Status**: KEEP
- **Reason**: Important for Module 2 (data collection)
- **MCP duplicate**: No
- **Generic**: Partially - but important for boot camp
- **Usage**: Module 2
- **Recommendation**: Keep - helps learners track data sources

### QUESTIONABLE - Team/Process

#### 23. collaboration.md

- **Status**: CONSIDER MOVING
- **Reason**: Generic team collaboration guidance
- **MCP duplicate**: No
- **Generic**: Yes - standard team practices
- **Usage**: Rarely (team projects)
- **Recommendation**: Move to development - too generic

#### 24. environment-setup.md

- **Status**: KEEP (but verify not duplicate)
- **Reason**: Environment configuration guidance
- **MCP duplicate**: Yes - `sdk_guide` covers this
- **Generic**: Partially
- **Usage**: Module 5
- **Recommendation**: Verify not duplicating sdk_guide, simplify if needed

#### 25. uat-framework.md

- **Status**: KEEP
- **Reason**: User acceptance testing framework for Module 8
- **MCP duplicate**: No
- **Generic**: Partially - but structured for boot camp
- **Usage**: Module 8
- **Recommendation**: Keep - helps learners validate results

## Recommendations

### Files to KEEP (17 files)

**Core Workflows (5)**:

1. steering.md
2. agent-instructions.md
3. quick-reference.md
4. modules-7-12-workflows.md
5. NEW_WORKFLOWS_PHASE5.md (merge into steering.md, then archive)

**Boot Camp Support (12)**:
6. common-pitfalls.md
7. troubleshooting-decision-tree.md
8. complexity-estimator.md
9. cost-estimation.md
10. lessons-learned.md
11. docker-deployment.md (critical for Docker troubleshooting)
12. security-privacy.md (simplify to boot camp reminders)
13. incremental-loading.md (verify not duplicate)
14. data-lineage.md
15. environment-setup.md (verify not duplicate)
16. uat-framework.md

### Files to MOVE to Development (8 files)

**Generic Best Practices**:

1. logging-standards.md - Generic logging (use MCP search_docs instead)
2. testing-strategy.md - Generic testing (use general resources)
3. performance-monitoring.md - Generic monitoring (use MCP search_docs)

**Generic Patterns**:
4. api-gateway-patterns.md - Generic API patterns (use find_examples)
5. integration-patterns.md - Generic integration (use find_examples)
6. multi-environment-strategy.md - Generic DevOps (too generic)

**Advanced Operations**:
7. disaster-recovery.md - Generic DR (too generic for boot camp)
8. recovery-procedures.md - Generic recovery (MCP handles this)
9. collaboration.md - Generic team practices (too generic)

## Impact

### If We Move 8 Files

**Before**: 25 steering files
**After**: 17 steering files
**Reduction**: 32% fewer files

**Benefits**:

- Clearer focus on boot camp-specific content
- Less duplication with MCP server
- Easier maintenance
- Faster loading times

**Risks**:

- Users might miss generic best practices
- Need to ensure MCP server covers removed topics
- May need to add references to external resources

## Verification Needed

Before moving files, verify:

1. **MCP Coverage**: Does `search_docs` adequately cover:
   - Logging best practices?
   - Performance monitoring?
   - Testing strategies?

2. **References**: Are these files referenced in:
   - steering.md workflows?
   - agent-instructions.md?
   - Module documentation?

3. **User Impact**: Will removing these files hurt the learning experience?

## Next Steps

1. Verify MCP server coverage for topics in files to be moved
2. Check all references to these files in documentation
3. Update workflows to use MCP tools instead of steering files
4. Move files to development repository
5. Update documentation to reference MCP tools
6. Test boot camp workflows without moved files

## Conclusion

**Recommendation**: Move 8-9 generic files to development repository, keeping 16-17 boot camp-specific files.

The steering directory should focus on:

- Boot camp-specific workflows and guidance
- Learning path structure
- Progress tracking
- Boot camp troubleshooting
- Critical deployment patterns (Docker)

Generic best practices should be:

- Provided by MCP server (`search_docs`, `find_examples`)
- Referenced from external resources
- Documented in development repository for reference
