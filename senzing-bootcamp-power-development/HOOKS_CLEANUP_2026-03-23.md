# Hooks Cleanup - Phase 7

**Date**: 2026-03-23
**Phase**: 7 of 7
**Purpose**: Remove generic hooks that conflict with agent instructions or aren't boot camp-specific

## Summary

Removed 2 generic hooks from the Power distribution, keeping only 4 boot camp-specific hooks.

## Files Moved to Development Repository

### Generic Hooks (2 files)

1. **test-before-commit.kiro.hook**
   - **Why removed**: Conflicts with agent instructions ("DO NOT automatically add tests unless explicitly requested")
   - **Why removed**: Assumes pytest is installed (not guaranteed in boot camp)
   - **Why removed**: Disruptive - blocks commits on test failures
   - **Replacement**: Users can add their own test hooks if desired

2. **update-documentation.kiro.hook**
   - **Why removed**: Generic reminder, not boot camp-specific
   - **Why removed**: Triggers on every file save (too frequent)
   - **Why removed**: Standard software engineering practice, doesn't need automation
   - **Replacement**: None needed - documentation updates are part of normal workflow

## Hooks Remaining in Power (4 files)

All remaining hooks are boot camp-specific and provide value:

1. **pep8-check.kiro.hook**
   - Boot camp-specific: Enforces PEP-8 compliance policy
   - Referenced in: docs/policies/PEP8_COMPLIANCE.md
   - Triggers: On save of Python files
   - Action: Reminds agent to check PEP-8 compliance

2. **data-quality-check.kiro.hook**
   - Boot camp-specific: Module 3 data transformation workflow
   - Triggers: On save of transformation programs
   - Action: Reminds to validate data quality
   - Module: 3 (Data Mapping)

3. **backup-before-load.kiro.hook**
   - Boot camp-specific: Module 5 data loading workflow
   - Triggers: On save of loading programs
   - Action: Reminds to backup database before loading
   - Module: 5 (Data Loading)

4. **validate-senzing-json.kiro.hook**
   - Boot camp-specific: Module 3 data transformation workflow
   - Triggers: On save of transformed data files
   - Action: Validates Senzing JSON format using lint_record
   - Module: 3 (Data Mapping)

## References Updated

### senzing-bootcamp/hooks/README.md

- ✅ Removed references to test-before-commit.kiro.hook
- ✅ Removed references to update-documentation.kiro.hook
- ✅ Updated hook count from 6 to 4

### senzing-bootcamp/POWER.md

- ✅ Updated hook count from 6 to 4
- ✅ Listed only remaining hooks

### senzing-bootcamp/docs/guides/HOOKS_INSTALLATION_GUIDE.md

- ✅ Updated table to show only 4 remaining hooks
- ✅ Removed test-before-commit and update-documentation from table
- ✅ Added pep8-check to table (was missing)

## Design Philosophy

This cleanup follows the Power's design philosophy:

> **Keep only boot camp-specific content in the Power distribution.**

### What Makes a Hook Boot Camp-Specific?

✅ **Include:**

- Enforces boot camp policies (PEP-8 compliance)
- Supports specific module workflows (data quality, backup, validation)
- Uses boot camp tools (lint_record, MCP server)
- Referenced in boot camp documentation

❌ **Exclude:**

- Generic software engineering practices (testing, documentation)
- Assumes tools not guaranteed in boot camp (pytest)
- Conflicts with agent instructions
- Too frequent/disruptive

## Impact

### Before

- 6 hooks total
- 2 generic hooks that could conflict with workflows
- Potential confusion about which hooks are essential

### After

- 4 hooks total (33% reduction)
- All hooks are boot camp-specific
- Clear purpose for each hook
- No conflicts with agent instructions

## Verification

### No Broken References

```bash
# Verified no broken references to removed hooks
grep -r "test-before-commit\|update-documentation" senzing-bootcamp/**/*.md
# Result: No matches ✅
```

### Hook Files Verified

```bash
# Verified only 4 hooks remain in Power
ls senzing-bootcamp/hooks/*.hook
# Result: 4 files ✅
```

## Related Documentation

- **HOOKS_ANALYSIS_2026-03-23.md** - Analysis of all hooks
- **COMPLETE_REORGANIZATION_SUMMARY.md** - Complete overview (updated with Phase 7)
- **senzing-bootcamp/hooks/README.md** - Updated hook documentation
- **senzing-bootcamp-power-development/hooks/README.md** - Removed hooks documentation

## For Future Maintainers

### When Adding New Hooks

Ask these questions:

1. **Is this boot camp-specific?**
   - If no → Don't add it

2. **Does it support a specific module workflow?**
   - If no → Probably too generic

3. **Does it conflict with agent instructions?**
   - If yes → Don't add it

4. **Does it assume tools are installed?**
   - If yes → Verify they're guaranteed in boot camp

5. **Is it too frequent/disruptive?**
   - If yes → Consider userTriggered instead of fileEdited

### Hook Design Guidelines

- **Specific over generic**: Target specific workflows, not general practices
- **Helpful over disruptive**: Remind, don't block
- **Boot camp tools only**: Use MCP server, lint_record, etc.
- **Document clearly**: Explain when and why to use each hook

## Version History

- **2026-03-23**: Phase 7 - Removed 2 generic hooks
  - Moved test-before-commit.kiro.hook to development
  - Moved update-documentation.kiro.hook to development
  - Updated all references
  - Created comprehensive documentation
  - Verified no broken links
