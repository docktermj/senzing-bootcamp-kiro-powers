# Documentation Reorganization - March 24, 2026

**Date**: 2026-03-24
**Purpose**: Separate user-facing documentation from agent/developer documentation
**Impact**: Cleaner structure, clearer purpose for each document

## Problem Statement

The `senzing-bootcamp/docs/` directory contained a mix of:

- User-facing guides (for bootcamp participants)
- Agent implementation guides (for AI agents running the bootcamp)
- Development documentation (for power developers)

This created confusion about the audience and purpose of each document.

## Solution

Reorganized documentation into two clear categories:

### User-Facing Documentation

**Location**: `senzing-bootcamp/docs/`
**Audience**: Bootcamp users
**Purpose**: Help users complete the bootcamp successfully

### Developer Documentation

**Location**: `senzing-bootcamp-power-development/`
**Audience**: Power developers and AI agents
**Purpose**: Implementation details and development notes

## Files Moved

### From `senzing-bootcamp/docs/guides/` to `senzing-bootcamp-power-development/guides/`

1. **MODULE_0_AGENT_GUIDE.md**
   - **Why moved**: Agent implementation guide, not user guide
   - **Audience**: AI agents implementing Module 0
   - **Contents**: Step-by-step workflow, critical requirements, success indicators

2. **FEEDBACK_WORKFLOW.md**
   - **Why moved**: Agent workflow documentation, not user instructions
   - **Audience**: AI agents collecting feedback
   - **Contents**: Feedback collection process, question templates

### From `senzing-bootcamp/docs/feedback/` to `senzing-bootcamp-power-development/feedback/`

1. **IMPROVEMENT_MODULE_0_LIVE_DEMO.md**
   - **Why moved**: Development documentation, not user feedback
   - **Audience**: Power developers
   - **Contents**: Implementation details, technical decisions, impact analysis

## What Remains in User-Facing Docs

### `senzing-bootcamp/docs/guides/` (6 files)

1. **QUICK_START.md** - Choose your bootcamp path
2. **ONBOARDING_CHECKLIST.md** - Pre-flight checklist
3. **PROGRESS_TRACKER.md** - Track module completion
4. **DESIGN_PATTERNS.md** - Entity resolution patterns
5. **TROUBLESHOOTING_INDEX.md** - Common issues and solutions
6. **HOOKS_INSTALLATION_GUIDE.md** - Install automation hooks

### `senzing-bootcamp/docs/modules/` (13 files)

All module documentation (MODULE_0 through MODULE_12) - these are essential for users.

### `senzing-bootcamp/docs/policies/` (7 files)

All policy documents - agents need these during bootcamp execution.

### `senzing-bootcamp/docs/feedback/` (1 file)

**SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md** - User feedback template

## What's in Developer Docs

### `senzing-bootcamp-power-development/guides/`

- **MODULE_0_AGENT_GUIDE.md** - Agent implementation for Module 0
- **FEEDBACK_WORKFLOW.md** - Agent feedback collection workflow
- **[15 historical files]** - Previously removed guides (for reference)

### `senzing-bootcamp-power-development/feedback/`

- **IMPROVEMENT_MODULE_0_LIVE_DEMO.md** - Module 0 improvement documentation

## Directory Structure

### Before

```text
senzing-bootcamp/docs/
├── guides/
│   ├── MODULE_0_AGENT_GUIDE.md (agent guide)
│   ├── FEEDBACK_WORKFLOW.md (agent workflow)
│   ├── QUICK_START.md (user guide)
│   └── ... (other user guides)
├── feedback/
│   ├── IMPROVEMENT_MODULE_0_LIVE_DEMO.md (dev docs)
│   └── SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md (user template)
└── modules/ (user docs)
```

### After

```text
senzing-bootcamp/docs/
├── guides/ (6 user guides only)
│   ├── QUICK_START.md
│   ├── ONBOARDING_CHECKLIST.md
│   └── ...
├── feedback/ (user feedback only)
│   └── SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md
└── modules/ (13 module docs)

senzing-bootcamp-power-development/
├── guides/ (agent/developer guides)
│   ├── MODULE_0_AGENT_GUIDE.md
│   ├── FEEDBACK_WORKFLOW.md
│   └── ... (historical files)
└── feedback/ (development docs)
    └── IMPROVEMENT_MODULE_0_LIVE_DEMO.md
```

## Benefits

### For Users

✅ Clear separation: only user-facing docs in bootcamp directory
✅ Less confusion about document purpose
✅ Easier to find relevant guides
✅ Cleaner documentation structure

### For Developers

✅ Agent implementation guides in one place
✅ Development documentation separate from user docs
✅ Easier to maintain and update
✅ Clear distinction between audiences

### For Maintainers

✅ Obvious where new docs should go
✅ Reduced risk of mixing audiences
✅ Better organization for future additions

## Updated README Files

1. **senzing-bootcamp/docs/guides/README.md**
   - Updated to list 6 guides (was 8)
   - Removed FEEDBACK_WORKFLOW and MODULE_0_AGENT_GUIDE
   - Added note about agent guides in development repo

2. **senzing-bootcamp/docs/feedback/README.md** (created)
   - Explains user feedback process
   - Notes that dev docs moved to development repo

3. **senzing-bootcamp-power-development/guides/README.md**
   - Added section for agent implementation guides
   - Explains why these guides are here
   - Updated file counts

4. **senzing-bootcamp-power-development/feedback/README.md** (created)
   - Explains purpose of development feedback directory
   - Lists improvement documentation

## Decision Criteria

When deciding where a document belongs:

### User-Facing (`senzing-bootcamp/docs/`)

- Helps users complete bootcamp modules
- Explains bootcamp features and workflows
- Provides troubleshooting for users
- Tracks user progress
- Collects user feedback

### Developer (`senzing-bootcamp-power-development/`)

- Agent implementation details
- Development notes and decisions
- Improvement documentation
- Internal workflows
- Historical reference material

## Future Guidelines

When adding new documentation:

**Ask**: Who is the primary audience?

- **Users** → `senzing-bootcamp/docs/`
- **Agents/Developers** → `senzing-bootcamp-power-development/`

**Ask**: What is the purpose?

- **Help users complete bootcamp** → User docs
- **Help agents implement bootcamp** → Developer docs
- **Document development decisions** → Developer docs

## Files Changed

### Moved

- `senzing-bootcamp/docs/guides/MODULE_0_AGENT_GUIDE.md` → `senzing-bootcamp-power-development/guides/`
- `senzing-bootcamp/docs/guides/FEEDBACK_WORKFLOW.md` → `senzing-bootcamp-power-development/guides/`
- `senzing-bootcamp/docs/feedback/IMPROVEMENT_MODULE_0_LIVE_DEMO.md` → `senzing-bootcamp-power-development/feedback/`

### Updated

- `senzing-bootcamp/docs/guides/README.md`
- `senzing-bootcamp-power-development/guides/README.md`

### Created

- `senzing-bootcamp/docs/feedback/README.md`
- `senzing-bootcamp-power-development/feedback/README.md`
- `senzing-bootcamp-power-development/DOCS_REORGANIZATION_2026-03-24.md` (this file)

## Impact Assessment

### Breaking Changes

❌ None - all files still exist, just in different locations

### Agent Impact

✅ Agents can still access implementation guides
✅ Location is more logical for agent documentation
✅ Clearer separation of concerns

### User Impact

✅ Users see only relevant documentation
✅ Less confusion about document purpose
✅ Cleaner docs directory

## Testing Recommendations

1. ✅ Verify all moved files are accessible
2. ✅ Check README files are accurate
3. ✅ Confirm no broken references
4. ✅ Test user documentation flow
5. ✅ Verify agent can find implementation guides

## Version History

- **2026-03-24**: Reorganized documentation by audience (user vs developer)
- **2026-03-23**: Initial documentation structure created

## Related Changes

This reorganization complements:

- Module 0 live demo implementation (v0.26.0)
- Previous guide cleanup (2026-03-23)
- MCP server integration

## Conclusion

Documentation is now clearly organized by audience:

- **Users** → `senzing-bootcamp/docs/`
- **Developers/Agents** → `senzing-bootcamp-power-development/`

This makes it easier for everyone to find the documentation they need and reduces confusion about document purpose.
