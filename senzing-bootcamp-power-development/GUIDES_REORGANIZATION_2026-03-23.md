# Guide Files Reorganization Summary

**Date**: 2026-03-23
**Purpose**: Remove duplicate and internal guide files, leverage MCP server for Senzing documentation

## Executive Summary

Reduced guide files from 23 to 8 (65% reduction) by:

1. Removing guides that duplicate MCP server functionality
2. Moving internal/development documentation to development repository
3. Keeping only boot camp-specific guides in Power distribution

## Files Moved (15 files)

### Duplicates MCP Server (6 files + 2 PDFs)

| File                    | MCP Alternative                        | Reason                                       |
|-------------------------|----------------------------------------|----------------------------------------------|
| COMPATIBILITY_MATRIX.md | `get_capabilities`                     | MCP provides current version info            |
| PREREQUISITES.md + .pdf | `sdk_guide`                            | MCP provides platform-specific prerequisites |
| FAQ.md                  | `search_docs`                          | MCP has comprehensive searchable docs        |
| PERFORMANCE_TUNING.md   | `search_docs` (category="performance") | MCP provides current performance guidance    |
| DOCKER_QUICK_START.md   | `sdk_guide` (platform="docker")        | MCP provides current Docker instructions     |
| DEPLOYMENT_CHECKLIST.md | N/A                                    | Generic checklist, not boot camp-specific    |

### Internal/Development (7 files)

| File                         | Reason                                   |
|------------------------------|------------------------------------------|
| PATH_SELECTION_FIX.md        | Internal bug fix documentation           |
| MODULE_COMPLETION_TRACKER.md | Duplicate of PROGRESS_TRACKER.md         |
| INSTALLATION_VERIFICATION.md | Internal policy document                 |
| EXECUTIVE_SUMMARY.md + .pdf  | Marketing material, not operational      |
| PREFLIGHT_CHECKLIST.md       | Duplicate of ONBOARDING_CHECKLIST.md     |
| QUICK_REFERENCE_CARD.md      | Duplicate of steering/quick-reference.md |
| VISUAL_GUIDE.md              | Optional diagrams, not essential         |

## Files Remaining (8 files)

Boot camp-specific guides that don't duplicate MCP server:

1. ✅ **QUICK_START.md** - Boot camp-specific quick start paths
2. ✅ **ONBOARDING_CHECKLIST.md** - Boot camp pre-flight checklist
3. ✅ **PROGRESS_TRACKER.md** - Track progress through 13 modules
4. ✅ **DESIGN_PATTERNS.md** - Boot camp-specific pattern gallery for Module 1
5. ✅ **TROUBLESHOOTING_INDEX.md** - Boot camp-specific troubleshooting
6. ✅ **HOOKS_INSTALLATION_GUIDE.md** - Kiro hooks installation
7. ✅ **FEEDBACK_WORKFLOW.md** - Boot camp feedback process
8. ✅ **README.md** - Guide index

## References Updated

### Files Modified

1. **senzing-bootcamp/POWER.md**
   - Removed reference to COMPATIBILITY_MATRIX.md

2. **senzing-bootcamp/README.md**
   - Removed reference to COMPATIBILITY_MATRIX.md

3. **senzing-bootcamp/docs/README.md**
   - Removed reference to INSTALLATION_VERIFICATION.md

4. **senzing-bootcamp/docs/guides/README.md**
   - Complete rewrite to reflect new structure
   - Added MCP tool alternatives
   - Documented removed files

5. **senzing-bootcamp/docs/guides/TROUBLESHOOTING_INDEX.md**
   - Updated reference to COMPATIBILITY_MATRIX.md → Use MCP tool

## Benefits

### 1. Reduced Duplication

- MCP server is single source of truth for Senzing documentation
- No need to maintain static copies of dynamic information
- Documentation stays current automatically

### 2. Smaller Distribution

- 65% reduction in guide files (23 → 8)
- Cleaner, more focused Power package
- Easier to navigate and understand

### 3. Better Maintenance

- Fewer files to keep in sync
- Changes to Senzing docs automatically reflected via MCP
- Focus maintenance on boot camp-specific content

### 4. Clearer Purpose

- Guides focus exclusively on boot camp workflows
- No confusion about what's boot camp-specific vs. general Senzing
- Better separation of concerns

### 5. Always Current

- MCP server provides up-to-date Senzing documentation
- No risk of outdated static guides
- Users always get latest information

## MCP Server Replaces Static Guides

| User Need                   | Old Approach                 | New Approach                                |
|-----------------------------|------------------------------|---------------------------------------------|
| Check version compatibility | Read COMPATIBILITY_MATRIX.md | Call `get_capabilities`                     |
| Review prerequisites        | Read PREREQUISITES.md        | Call `sdk_guide`                            |
| Find answers to questions   | Read FAQ.md                  | Call `search_docs`                          |
| Optimize performance        | Read PERFORMANCE_TUNING.md   | Call `search_docs` (category="performance") |
| Set up Docker               | Read DOCKER_QUICK_START.md   | Call `sdk_guide` (platform="docker")        |

## Design Philosophy

This reorganization aligns with the Power's core design philosophy:

> **Leverage the MCP server for Senzing documentation, keep only boot camp-specific guides in the Power distribution.**

### What Belongs in Power Guides?

✅ **Include:**

- Boot camp-specific workflows
- Kiro-specific features (hooks, steering)
- Progress tracking and checklists
- Boot camp troubleshooting
- Feedback processes

❌ **Exclude:**

- Senzing documentation (use MCP server)
- Generic checklists
- Internal development notes
- Marketing materials
- Duplicate content

## Verification

### No Broken References

```bash
# Verified no broken references to removed files
grep -r "COMPATIBILITY_MATRIX\|PREREQUISITES\|FAQ\.md" senzing-bootcamp/**/*.md
# Result: Only references in README.md explaining what was removed ✅
```

### File Counts

- **Before**: 23 guide files
- **After**: 8 guide files
- **Moved**: 15 files (+ 2 PDFs)
- **Reduction**: 65%

### All References Updated

- ✅ POWER.md
- ✅ README.md
- ✅ docs/README.md
- ✅ docs/guides/README.md
- ✅ docs/guides/TROUBLESHOOTING_INDEX.md

## For Future Maintainers

When considering adding a new guide, ask:

1. **Is this boot camp-specific?**
   - If no → Don't add it

2. **Does the MCP server provide this information?**
   - If yes → Use MCP tool instead

3. **Is this a Kiro-specific feature?**
   - If yes → Add to guides

4. **Does this duplicate existing content?**
   - If yes → Don't add it

5. **Is this internal documentation?**
   - If yes → Add to development repository

## Related Documentation

- **REORGANIZATION_SUMMARY.md** - Overall documentation reorganization (docs/development + docs/guides)
- **senzing-bootcamp-development/guides/README.md** - Index of removed guide files
- **senzing-bootcamp/docs/guides/README.md** - Index of remaining guide files

## Version History

- **2026-03-23**: Initial guide reorganization
  - Moved 15 guide files to development repository
  - Updated all references
  - Created new README structure
  - Documented MCP tool alternatives
