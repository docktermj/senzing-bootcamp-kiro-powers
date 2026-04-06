---
inclusion: always
---

# Repository Organization - Senzing Bootcamp Power

This steering file defines the organizational structure for the Senzing Bootcamp Power repository.

## Core Principle

**All documents that are not part of the "senzing-bootcamp" power but are part of developing the power should be placed in "senzing-bootcamp-power-development".**

## Directory Structure

### `senzing-bootcamp/` - The Power Distribution

**Purpose**: Contains ONLY files that are part of the distributed power
**Audience**: Bootcamp users and AI agents running the bootcamp
**Contents**:

- Power configuration (`POWER.md`, `mcp.json`, `icon.png`)
- User-facing documentation (`docs/`)
- Module documentation (`docs/modules/`)
- User guides (`docs/guides/`)
- User feedback templates (`docs/feedback/`)
- Policies for agents (`docs/policies/`)
- Steering files for agents (`steering/`)
- Code templates (`templates/`)
- Example projects (`examples/`)
- Hooks (`hooks/`)
- Scripts (`scripts/`)

**What belongs here**:

- ✅ Files users need to complete the bootcamp
- ✅ Files agents need to run the bootcamp
- ✅ Templates and examples for users
- ✅ User-facing documentation
- ✅ Power configuration files

**What does NOT belong here**:

- ❌ Development notes and decisions
- ❌ Agent implementation guides
- ❌ Improvement documentation
- ❌ Historical reference material
- ❌ Build artifacts and cleanup notes
- ❌ Power development workflows

### `senzing-bootcamp-power-development/` - Development Repository

**Purpose**: Contains everything related to developing and maintaining the power
**Audience**: Power developers, maintainers, and contributors
**Contents**:

- Development documentation
- Agent implementation guides
- Improvement notes and decisions
- Historical reference material
- Build and cleanup notes
- Development workflows
- Testing documentation
- Reorganization summaries

**What belongs here**:

- ✅ Agent implementation guides (e.g., `MODULE_0_AGENT_GUIDE.md`)
- ✅ Development workflows (e.g., `FEEDBACK_WORKFLOW.md`)
- ✅ Improvement documentation (e.g., `IMPROVEMENT_MODULE_0_LIVE_DEMO.md`)
- ✅ Reorganization notes (e.g., `DOCS_REORGANIZATION_2026-03-24.md`)
- ✅ Build artifacts and cleanup summaries
- ✅ Historical removed files (for reference)
- ✅ Development guides and workflows

**What does NOT belong here**:

- ❌ User-facing documentation
- ❌ Module documentation
- ❌ Power configuration files
- ❌ Templates and examples for users

## Decision Tree

When creating or moving a file, ask:

### Question 1: Is this file part of the distributed power?

- **YES** → Consider `senzing-bootcamp/`
- **NO** → Goes in `senzing-bootcamp-power-development/`

### Question 2: Who is the primary audience?

- **Bootcamp users** → `senzing-bootcamp/docs/`
- **AI agents running bootcamp** → `senzing-bootcamp/steering/` or `senzing-bootcamp/docs/policies/`
- **Power developers** → `senzing-bootcamp-power-development/`

### Question 3: What is the purpose?

- **Help users complete bootcamp** → `senzing-bootcamp/docs/guides/`
- **Document modules** → `senzing-bootcamp/docs/modules/`
- **Provide templates** → `senzing-bootcamp/templates/`
- **Show examples** → `senzing-bootcamp/examples/`
- **Guide agent implementation** → `senzing-bootcamp-power-development/guides/`
- **Document development decisions** → `senzing-bootcamp-power-development/feedback/` or root
- **Historical reference** → `senzing-bootcamp-power-development/`

## Examples

### Correctly Placed Files

#### In `senzing-bootcamp/`

```text
✅ docs/modules/MODULE_0_QUICK_DEMO.md - User-facing module documentation
✅ docs/guides/QUICK_START.md - User guide for getting started
✅ docs/guides/DESIGN_PATTERNS.md - User reference for patterns
✅ docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md - User feedback template
✅ templates/demo_quick_start.py - Template for users
✅ steering/steering.md - Agent workflow instructions
✅ POWER.md - Power configuration
✅ CHANGELOG.md - User-facing version history
```

#### In `senzing-bootcamp-power-development/`

```text
✅ guides/MODULE_0_AGENT_GUIDE.md - Agent implementation guide
✅ guides/FEEDBACK_WORKFLOW.md - Agent development workflow
✅ feedback/IMPROVEMENT_MODULE_0_LIVE_DEMO.md - Development notes
✅ DOCS_REORGANIZATION_2026-03-24.md - Reorganization summary
✅ BUILD_ARTIFACTS_CLEANUP_2026-03-23.md - Cleanup notes
✅ COMPLETE_REORGANIZATION_SUMMARY.md - Development summary
```

### Incorrectly Placed Files (Examples to Avoid)

```text
❌ senzing-bootcamp/docs/guides/MODULE_0_AGENT_GUIDE.md
   → Should be: senzing-bootcamp-power-development/guides/MODULE_0_AGENT_GUIDE.md
   → Reason: Agent implementation guide, not user guide

❌ senzing-bootcamp/docs/feedback/IMPROVEMENT_MODULE_0_LIVE_DEMO.md
   → Should be: senzing-bootcamp-power-development/feedback/IMPROVEMENT_MODULE_0_LIVE_DEMO.md
   → Reason: Development documentation, not user feedback

❌ senzing-bootcamp/BUILD_ARTIFACTS_CLEANUP.md
   → Should be: senzing-bootcamp-power-development/BUILD_ARTIFACTS_CLEANUP.md
   → Reason: Development note, not part of power distribution
```

## Special Cases

### Agent Implementation Guides

**Location**: `senzing-bootcamp-power-development/guides/`
**Reason**: These guide developers on how agents should implement features, not users on how to use the bootcamp

**Examples**:

- `MODULE_0_AGENT_GUIDE.md` - How agents should run Module 0
- `FEEDBACK_WORKFLOW.md` - How agents should collect feedback

### Agent Workflow Instructions

**Location**: `senzing-bootcamp/steering/`
**Reason**: These are loaded by agents during bootcamp execution and are part of the power

**Examples**:

- `steering.md` - Main workflow instructions
- `environment-setup.md` - Setup workflows
- `troubleshooting-decision-tree.md` - Troubleshooting workflows

### Policies

**Location**: `senzing-bootcamp/docs/policies/`
**Reason**: Agents need these during bootcamp execution, so they're part of the power

**Examples**:

- `PEP8_COMPLIANCE.md` - Code quality standards
- `FILE_STORAGE_POLICY.md` - Where to store files
- `MODULE_0_CODE_LOCATION.md` - Module 0 file locations

### User Feedback

**Location**: `senzing-bootcamp/docs/feedback/`
**Reason**: Users fill these out during bootcamp

**Examples**:

- `SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md` - User feedback template

### Development Feedback

**Location**: `senzing-bootcamp-power-development/feedback/`
**Reason**: Documentation of improvements and development decisions

**Examples**:

- `IMPROVEMENT_MODULE_0_LIVE_DEMO.md` - Development notes on improvements

## Maintenance Guidelines

### When Adding New Files

1. **Ask**: Is this file part of the distributed power?
   - If NO → `senzing-bootcamp-power-development/`
   - If YES → Continue to step 2

2. **Ask**: Who is the primary audience?
   - Users → `senzing-bootcamp/docs/`
   - Agents (runtime) → `senzing-bootcamp/steering/` or `senzing-bootcamp/docs/policies/`
   - Developers → `senzing-bootcamp-power-development/`

3. **Ask**: What type of file is it?
   - Module documentation → `senzing-bootcamp/docs/modules/`
   - User guide → `senzing-bootcamp/docs/guides/`
   - Template → `senzing-bootcamp/templates/`
   - Example → `senzing-bootcamp/examples/`
   - Agent implementation → `senzing-bootcamp-power-development/guides/`
   - Development note → `senzing-bootcamp-power-development/`

### When Moving Files

Before moving a file, verify:

1. ✅ The new location follows the core principle
2. ✅ README files are updated
3. ✅ No broken references
4. ✅ Related files are in consistent locations

### When Reviewing Pull Requests

Check that:

1. ✅ New files are in the correct directory
2. ✅ Development files are not in `senzing-bootcamp/`
3. ✅ User-facing files are not in `senzing-bootcamp-power-development/`
4. ✅ README files are updated if directory contents change

## Benefits of This Organization

### For Users

- ✅ Clean, focused documentation
- ✅ No confusion from development notes
- ✅ Easier to find relevant guides
- ✅ Smaller power distribution

### For Developers

- ✅ Clear separation of concerns
- ✅ Development notes in one place
- ✅ Historical reference preserved
- ✅ Easier to maintain

### For Maintainers

- ✅ Obvious where files belong
- ✅ Consistent organization
- ✅ Reduced risk of mixing audiences
- ✅ Better long-term maintainability

## Common Mistakes to Avoid

### ❌ Mistake 1: Putting agent implementation guides in user docs

```text
❌ senzing-bootcamp/docs/guides/MODULE_0_AGENT_GUIDE.md
✅ senzing-bootcamp-power-development/guides/MODULE_0_AGENT_GUIDE.md
```

### ❌ Mistake 2: Putting development notes in power distribution

```text
❌ senzing-bootcamp/IMPROVEMENT_MODULE_0_LIVE_DEMO.md
✅ senzing-bootcamp-power-development/feedback/IMPROVEMENT_MODULE_0_LIVE_DEMO.md
```

### ❌ Mistake 3: Putting cleanup summaries in power distribution

```text
❌ senzing-bootcamp/BUILD_ARTIFACTS_CLEANUP.md
✅ senzing-bootcamp-power-development/BUILD_ARTIFACTS_CLEANUP.md
```

### ❌ Mistake 4: Putting user guides in development repository

```text
❌ senzing-bootcamp-power-development/guides/QUICK_START.md
✅ senzing-bootcamp/docs/guides/QUICK_START.md
```

## Quick Reference

| File Type              | Location                                       | Reason                 |
|------------------------|------------------------------------------------|------------------------|
| Module documentation   | `senzing-bootcamp/docs/modules/`               | Users need this        |
| User guides            | `senzing-bootcamp/docs/guides/`                | Users need this        |
| User feedback template | `senzing-bootcamp/docs/feedback/`              | Users fill this out    |
| Templates              | `senzing-bootcamp/templates/`                  | Users use these        |
| Examples               | `senzing-bootcamp/examples/`                   | Users reference these  |
| Agent workflows        | `senzing-bootcamp/steering/`                   | Agents load at runtime |
| Policies               | `senzing-bootcamp/docs/policies/`              | Agents need at runtime |
| Agent implementation   | `senzing-bootcamp-power-development/guides/`   | For developers         |
| Development notes      | `senzing-bootcamp-power-development/feedback/` | For developers         |
| Cleanup summaries      | `senzing-bootcamp-power-development/`          | For developers         |
| Historical reference   | `senzing-bootcamp-power-development/`          | For developers         |

## Version History

- **2026-03-24**: Created repository organization steering file
- **2026-03-24**: Reorganized documentation by audience (user vs developer)
- **2026-03-23**: Initial documentation structure created

## Related Documentation

- `senzing-bootcamp/docs/guides/README.md` - User guides index
- `senzing-bootcamp-power-development/guides/README.md` - Developer guides index
- `senzing-bootcamp-power-development/DOCS_REORGANIZATION_2026-03-24.md` - Reorganization details

---

**Remember**: When in doubt, ask "Is this part of the distributed power?" If NO, it goes in `senzing-bootcamp-power-development/`.
