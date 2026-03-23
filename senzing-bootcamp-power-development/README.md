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

### Removed Guides (`guides/`)

Guide files removed from Power distribution (Phase 2):
- Files duplicating MCP server functionality
- Internal/development documentation
- See `GUIDES_REORGANIZATION_2026-03-23.md` for details

### Removed Demo Scripts (`quickstart_demo/`)

Static demo scripts removed from Power distribution (Phase 3):
- Replaced by MCP-generated code
- See `DEMO_SCRIPTS_REMOVAL_2026-03-23.md` for details

### Removed Steering Files (`steering/`)

Steering files removed from Power distribution (Phase 5):
- Generic best practices files
- Generic pattern files
- Advanced operations files
- See `STEERING_FILES_CLEANUP_2026-03-23.md` for details

### Build Artifacts

Build artifacts removed from Power distribution (Phase 4):
- `mdpdf.log` - PDF generation tool log
- See `BUILD_ARTIFACTS_CLEANUP_2026-03-23.md` for details

### Reorganization Documentation

- `REORGANIZATION_SUMMARY.md` - Phase 1: Development documentation (34 files)
- `GUIDES_REORGANIZATION_2026-03-23.md` - Phase 2: Guide files (17 files)
- `DEMO_SCRIPTS_REMOVAL_2026-03-23.md` - Phase 3: Demo scripts (3 files)
- `BUILD_ARTIFACTS_CLEANUP_2026-03-23.md` - Phase 4: Build artifacts (1 file)
- `STEERING_FILES_ANALYSIS_2026-03-23.md` - Phase 5 analysis
- `STEERING_FILES_CLEANUP_2026-03-23.md` - Phase 5: Steering files (9 files)
- `COMPLETE_REORGANIZATION_SUMMARY.md` - Complete overview (64 files total)

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
5. **Eliminate duplication** - MCP server provides Senzing documentation dynamically
6. **Always current** - MCP-generated content stays up-to-date automatically

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

- **2026-03-23**: Complete reorganization (5 phases, 64 files moved)
  - Phase 1: Moved 34 internal development files
  - Phase 2: Moved 17 guide files (duplicates and internal docs)
  - Phase 3: Moved 3 static demo scripts
  - Phase 4: Moved 1 build artifact (mdpdf.log)
  - Phase 5: Moved 9 generic steering files
- **2026-03-17**: Major v3.0.0 improvements (Modules 7-12, enhanced workflows)
- **Earlier**: Various phases of development tracked in `development/` folder

---

**Note**: This is internal documentation. Users of the Senzing Boot Camp Power should refer to the documentation included with the Power itself.
