---
inclusion: always
---

# Repository Organization - Senzing Bootcamp Power

This steering file defines the organizational structure for the Senzing Bootcamp Power repository.

## Core Principle

**All files in this repository are part of the "senzing-bootcamp" power distribution. Keep the power directory clean and focused on what users and agents need.**

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

- ❌ Development notes and decisions (use git history)
- ❌ Build artifacts and cleanup notes
- ❌ Historical removed files

## Decision Tree

When creating or moving a file, ask:

### Question 1: Is this file part of the distributed power?

- **YES** → Place in `senzing-bootcamp/`
- **NO** → Do not add it to the repository (use git history for historical reference)

### Question 2: Who is the primary audience?

- **Bootcamp users** → `senzing-bootcamp/docs/`
- **AI agents running bootcamp** → `senzing-bootcamp/steering/` or `senzing-bootcamp/docs/policies/`

### Question 3: What is the purpose?

- **Help users complete bootcamp** → `senzing-bootcamp/docs/guides/`
- **Document modules** → `senzing-bootcamp/docs/modules/`
- **Provide templates** → `senzing-bootcamp/templates/`
- **Show examples** → `senzing-bootcamp/examples/`

## Examples

### Correctly Placed Files

```text
✅ docs/modules/MODULE_0_SDK_SETUP.md - User-facing module documentation
✅ docs/guides/QUICK_START.md - User guide for getting started
✅ docs/guides/DESIGN_PATTERNS.md - User reference for patterns
✅ docs/feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md - User feedback template
✅ steering/steering.md - Agent workflow instructions
✅ POWER.md - Power configuration
✅ CHANGELOG.md - User-facing version history
```

## Special Cases

### Agent Workflow Instructions

**Location**: `senzing-bootcamp/steering/`
**Reason**: These are loaded by agents during bootcamp execution and are part of the power

### Policies

**Location**: `senzing-bootcamp/docs/policies/`
**Reason**: Agents need these during bootcamp execution, so they're part of the power

### User Feedback

**Location**: `senzing-bootcamp/docs/feedback/`
**Reason**: Users fill these out during bootcamp

## Maintenance Guidelines

### When Adding New Files

1. **Ask**: Is this file part of the distributed power?
   - If NO → Do not add it
   - If YES → Continue to step 2

2. **Ask**: Who is the primary audience?
   - Users → `senzing-bootcamp/docs/`
   - Agents (runtime) → `senzing-bootcamp/steering/` or `senzing-bootcamp/docs/policies/`

3. **Ask**: What type of file is it?
   - Module documentation → `senzing-bootcamp/docs/modules/`
   - User guide → `senzing-bootcamp/docs/guides/`
   - Template → `senzing-bootcamp/templates/`
   - Example → `senzing-bootcamp/examples/`

## Quick Reference

| File Type              | Location                          | Reason                 |
|------------------------|-----------------------------------|------------------------|
| Module documentation   | `senzing-bootcamp/docs/modules/`  | Users need this        |
| User guides            | `senzing-bootcamp/docs/guides/`   | Users need this        |
| User feedback template | `senzing-bootcamp/docs/feedback/` | Users fill this out    |
| Templates              | `senzing-bootcamp/templates/`     | Users use these        |
| Examples               | `senzing-bootcamp/examples/`      | Users reference these  |
| Agent workflows        | `senzing-bootcamp/steering/`      | Agents load at runtime |
| Policies               | `senzing-bootcamp/docs/policies/` | Agents need at runtime |

## Related Documentation

- `senzing-bootcamp/docs/guides/README.md` - User guides index

---

**Remember**: Everything in this repository should be part of the distributed power. Use git history for development reference.
