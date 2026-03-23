# Senzing Boot Camp - Development Documentation

This repository contains internal development documentation for the Senzing Boot Camp Kiro Power. These files are **not distributed with the Power** but are kept for historical reference and future development.

## Purpose

This documentation tracks:
- Development history and implementation phases
- Design decisions and rationale
- File reorganization history
- Improvement summaries
- Internal policies and guarantees

## Contents

### Development History (`development/`)

Complete history of the boot camp development including:
- Phase completion summaries (PHASE_1 through PHASE_5)
- Implementation plans and status
- File reorganization documentation
- Improvement tracking (v3.0.0 and beyond)
- PEP-8 compliance implementation
- Template cleanup history
- Workflow integration strategies

### Internal Documentation (Root)

- `DIRECTORY_STRUCTURE_GUARANTEE.md` - Internal guarantee about directory structure creation
- `DIRECTORY_STRUCTURE_FIRST.md` - Original documentation about directory-first approach
- `SENZING_BOOTCAMP_POWER_FEEDBACK.md` - Example/test feedback file

## Why Separate?

These files were moved out of the main Power distribution because:

1. **Users don't need them** - They document how the Power was built, not how to use it
2. **Reduce clutter** - Keep the Power focused on user-facing content
3. **Preserve history** - Maintain development context for future maintainers
4. **Clear separation** - Distinguish between user documentation and developer notes

## What's in the Power Distribution?

The actual Power includes only user-facing documentation:

- `docs/guides/` - User guides (Quick Start, FAQ, Troubleshooting, etc.)
- `docs/modules/` - Module-specific documentation (MODULE_0 through MODULE_12)
- `docs/policies/` - Standards and conventions (file storage, Python requirements, etc.)
- `docs/feedback/` - Feedback template for users
- `steering/` - Agent steering files and workflows
- `hooks/` - Kiro hook definitions
- `examples/` - Example projects
- `templates/` - Code templates

## For Maintainers

When developing the Power:

1. **Reference this documentation** to understand past decisions
2. **Add new development notes here** (not in the Power distribution)
3. **Update the Power's user-facing docs** when making changes
4. **Keep this history** for context on why things are the way they are

## Version History

- **2026-03-23**: Created development repository, moved internal docs from Power distribution
- **2026-03-17**: Major v3.0.0 improvements (Modules 7-12, enhanced workflows)
- **Earlier**: Various phases of development tracked in `development/` folder

---

**Note**: This is internal documentation. Users of the Senzing Boot Camp Power should refer to the documentation included with the Power itself.
