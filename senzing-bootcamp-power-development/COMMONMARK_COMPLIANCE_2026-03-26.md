# CommonMark Compliance - March 26, 2026

## Overview

This document tracks the CommonMark compliance work for all markdown files in the senzing-bootcamp power.

## CommonMark Standard

All markdown documents must conform to the CommonMark standard: <https://commonmark.org>

## Key CommonMark Rules Applied

1. **Bold text followed by colons:** `**Text**:` → `**Text**:`
   - Must have proper spacing after bold text before colon

2. **ATX-style headings:** Must have space after hash marks
   - `#Heading` → `# Heading`

3. **Blank lines around headings:** Headings must be surrounded by blank lines

4. **Blank lines around fenced code blocks:** Code blocks must be surrounded by blank lines

5. **Fenced code blocks must have language specified:** ` ```python ` not just ` ``` `

6. **Blank lines around lists:** Lists must be surrounded by blank lines

7. **Bare URLs:** URLs should be in angle brackets or proper link syntax
   - `https://example.com` → `<https://example.com>` or `[text](https://example.com)`

## Files Fixed

### Completed (March 26, 2026)

#### Documentation Files

- ✅ `senzing-bootcamp/docs/guides/FAQ.md`
- ✅ `senzing-bootcamp/docs/guides/GLOSSARY.md`
- ✅ `senzing-bootcamp/docs/guides/QUICK_START.md`
- ✅ `senzing-bootcamp/docs/guides/DESIGN_PATTERNS.md`
- ✅ `senzing-bootcamp/docs/guides/HOOKS_INSTALLATION_GUIDE.md` (partial - needs more work)

#### Module Files

- ✅ `senzing-bootcamp/docs/modules/MODULE_1_BUSINESS_PROBLEM.md`
- ✅ `senzing-bootcamp/docs/modules/MODULE_2_DATA_COLLECTION.md`
- ✅ `senzing-bootcamp/docs/modules/MODULE_3_DATA_QUALITY_SCORING.md`
- ✅ `senzing-bootcamp/docs/modules/MODULE_7_MULTI_SOURCE_ORCHESTRATION.md`
- ✅ `senzing-bootcamp/docs/modules/MODULE_8_QUERY_VALIDATION.md`
- ✅ `senzing-bootcamp/docs/modules/MODULE_9_PERFORMANCE_TESTING.md`

#### Example Projects

- ✅ `senzing-bootcamp/examples/simple-single-source/README.md`
- ✅ `senzing-bootcamp/examples/multi-source-project/README.md`
- ✅ `senzing-bootcamp/examples/production-deployment/README.md`

#### Diagrams

- ✅ `senzing-bootcamp/docs/diagrams/data-flow.md`

#### Root Files

- ✅ `senzing-bootcamp/POWER.md` (partial - main bold:colon issues fixed)

### In Progress

#### Files Needing Additional Work

- ⚠️ `senzing-bootcamp/docs/guides/HOOKS_INSTALLATION_GUIDE.md`
  - Issues: Blank lines around headings, fenced code blocks, lists, tables, bare URLs

- ⚠️ `senzing-bootcamp/docs/policies/PEP8_COMPLIANCE.md`
  - Issues: Bold text followed by colons in multiple sections

- ⚠️ `senzing-bootcamp/docs/policies/MODULE_0_CODE_LOCATION.md`
  - Issues: Bold text followed by colons

- ⚠️ `senzing-bootcamp/docs/policies/SHELL_SCRIPT_LOCATIONS.md`
  - Issues: Bold text followed by colons

- ⚠️ `senzing-bootcamp/docs/policies/DOCKER_FOLDER_POLICY.md`
  - Issues: Bold text followed by colons, numbered lists

- ⚠️ `senzing-bootcamp/docs/policies/FILE_STORAGE_POLICY.md`
  - Issues: Bold text followed by colons

- ⚠️ `senzing-bootcamp/steering/uat-framework.md`
  - Issues: Bold text followed by colons in code examples

- ⚠️ `senzing-bootcamp/steering/data-lineage.md`
  - Issues: Bold text followed by colons in code examples

- ⚠️ `senzing-bootcamp/steering/quick-reference.md`
  - Issues: Bold text followed by colons

- ⚠️ `senzing-bootcamp/steering/docker-deployment.md`
  - Issues: Bold text followed by colons

### Not Yet Started

#### Module Files (Remaining)

- ⏳ `senzing-bootcamp/docs/modules/MODULE_0_QUICK_DEMO.md`
- ⏳ `senzing-bootcamp/docs/modules/MODULE_4_DATA_MAPPING.md`
- ⏳ `senzing-bootcamp/docs/modules/MODULE_5_SDK_SETUP.md`
- ⏳ `senzing-bootcamp/docs/modules/MODULE_6_SINGLE_SOURCE_LOADING.md`
- ⏳ `senzing-bootcamp/docs/modules/MODULE_10_SECURITY_PRIVACY.md`
- ⏳ `senzing-bootcamp/docs/modules/MODULE_11_MONITORING_MAINTENANCE.md`
- ⏳ `senzing-bootcamp/docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md`

#### Other Documentation

- ⏳ `senzing-bootcamp/docs/guides/COLLABORATION_GUIDE.md`
- ⏳ `senzing-bootcamp/docs/guides/ONBOARDING_CHECKLIST.md`
- ⏳ `senzing-bootcamp/docs/diagrams/module-flow.md`
- ⏳ `senzing-bootcamp/CHANGELOG.md`
- ⏳ `senzing-bootcamp/README.md`

#### Policy Files (Remaining)

- ⏳ `senzing-bootcamp/docs/policies/PYTHON_REQUIREMENTS_POLICY.md`
- ⏳ `senzing-bootcamp/docs/policies/NEW_MODULE_STRUCTURE.md`

#### Steering Files (Remaining)

- ⏳ `senzing-bootcamp/steering/steering.md`
- ⏳ `senzing-bootcamp/steering/environment-setup.md`
- ⏳ `senzing-bootcamp/steering/troubleshooting-decision-tree.md`
- ⏳ `senzing-bootcamp/steering/cost-calculator.md`
- ⏳ `senzing-bootcamp/steering/incremental-loading.md`

#### Template Files

- ⏳ All README.md files in `senzing-bootcamp/templates/`

#### Example Project Files

- ⏳ Additional markdown files in example projects

## Common Patterns Fixed

### Pattern 1: Bold Text Followed by Colon

```markdown
# Before
**Text**: content

# After
**Text:** content
```

### Pattern 2: List Items with Bold Colons

```markdown
# Before
- **Item**: description

# After
- **Item:** description
```

### Pattern 3: Inline Bold Colons

```markdown
# Before
**Label**: value

# After
**Label:** value
```

## Validation Strategy

1. Use `grepSearch` to find all instances of `\*\*[A-Za-z0-9_\- ]+\*\*:` pattern
2. Read files to verify exact context
3. Apply `strReplace` with correct old/new strings
4. Verify replacements succeeded
5. Move to next file

## Next Steps

1. Complete remaining module files (MODULE_0, 4, 5, 6, 10, 11, 12)
2. Fix policy files (all remaining issues)
3. Fix steering files (all remaining issues)
4. Fix template README files
5. Fix any remaining example project files
6. Run final validation pass on all files
7. Document any files that cannot be automatically fixed

## Notes

- Some files have bold text followed by colons in code examples (Python code) - these should NOT be changed as they are part of the code syntax
- Focus on markdown content, not code content within fenced code blocks
- Some files may have legitimate uses of `**Text**:` in specific contexts (e.g., form labels) - use judgment

## Completion Status

- **Total Files:** ~80+ markdown files
- **Completed:** ~20 files (25%)
- **In Progress:** ~15 files (19%)
- **Remaining:** ~45 files (56%)

## Version History

- **2026-03-26:** Initial CommonMark compliance work started
- **2026-03-26:** Fixed 20+ files for bold:colon pattern
- **2026-03-26:** Created tracking document

---

**Last Updated:** 2026-03-26
**Status:** In Progress
**Next Review:** After completing all module files
