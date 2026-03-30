# Senzing Boot Camp Documentation

This directory contains all documentation for the Senzing Boot Camp.

## Directory Structure

### `/modules/`

Module-specific documentation files. Each module has detailed documentation about its purpose, workflow, and implementation.

**Files:**

- `MODULE_3_DATA_COLLECTION.md` - Data collection and source management
- `MODULE_4_DATA_QUALITY_SCORING.md` - Automated data quality assessment
- `MODULE_6_SINGLE_SOURCE_LOADING.md` - Single source loading patterns
- `MODULE_7_MULTI_SOURCE_ORCHESTRATION.md` - Multi-source orchestration
- `MODULE_8_QUERY_VALIDATION.md` - Query and validation with UAT
- `MODULE_9_PERFORMANCE_TESTING.md` - Performance testing and benchmarking
- `MODULE_10_SECURITY_HARDENING.md` - Security hardening for production
- `MODULE_11_MONITORING_OBSERVABILITY.md` - Monitoring and observability
- `MODULE_12_DEPLOYMENT_PACKAGING.md` - Deployment packaging

### `/policies/`

Policy documents that define standards and conventions for the boot camp.

**Files:**

- `MODULE_1_CODE_LOCATION.md` - Policy for Module 1 demo code location
- `PYTHON_REQUIREMENTS_POLICY.md` - Python dependency management policy
- `SHELL_SCRIPT_LOCATIONS.md` - Shell script organization policy

### `/guides/`

User guides and installation instructions.

**Files:**

- `DESIGN_PATTERNS.md` - Entity resolution design patterns
- `HOOKS_INSTALLATION_GUIDE.md` - Guide for installing Kiro hooks

### `/development/`

Development progress tracking and implementation documentation.

**Files:**

- `IMPROVEMENTS.md` - Complete summary of all improvements
- `NEW_MODULE_STRUCTURE.md` - Documentation of new 13-module structure
- Per-module steering files (`module-00-quick-demo.md` through `module-12-deployment.md`)
- `V3_IMPLEMENTATION_STATUS.md` - Overall implementation status
- `PHASE_1_COMPLETE.md` - Phase 1 completion summary
- `PHASE_2_COMPLETE.md` - Phase 2 completion summary
- `PHASE_2_PROGRESS.md` - Phase 2 progress tracking
- `PHASE_3_COMPLETE.md` - Phase 3 completion summary
- `PHASE_4_COMPLETE.md` - Phase 4 completion summary
- `PHASE_5_COMPLETE.md` - Phase 5 completion summary
- `PHASE_5_STATUS.md` - Phase 5 status tracking
- `TASK_7_COMPLETION_SUMMARY.md` - Task 7 completion summary

## Root Level Files

The following files remain in the root `senzing-bootcamp/` directory:

- `POWER.md` - Main power definition file (required by Kiro)
- `icon.png` - Power icon (required by Kiro)
- `mcp.json` - MCP server configuration (required by Kiro)
- `README.md` - Main README (if exists)
- `LICENSE` - License file (if exists)

## Navigation

### For Users

- Start with the main `POWER.md` in the root directory
- Refer to `/guides/` for installation and setup help
- Refer to `/modules/` for module-specific documentation
- Refer to `/policies/` for coding standards and conventions

### For Developers

- Review `/development/IMPROVEMENTS.md` for complete change history
- Review `/development/NEW_MODULE_STRUCTURE.md` for architecture
- Review `/development/V3_IMPLEMENTATION_STATUS.md` for current status
- Review per-module steering files for detailed workflows

### For Agents

- Load per-module steering files as needed (e.g., `module-00-sdk-setup.md`)
- Load `steering/agent-instructions.md` for behavior guidance
- Refer to `/policies/` for file organization rules
- Refer to `/modules/` for module-specific details

## File Organization Principles

1. **Root directory** - Only essential files (POWER.md, icon.png, mcp.json, README, LICENSE)
2. **docs/modules/** - Module-specific documentation
3. **docs/policies/** - Standards and conventions
4. **docs/guides/** - User-facing guides
5. **docs/feedback/** - Feedback template for users
6. **steering/** - Agent steering files and workflows
7. **hooks/** - Kiro hook definitions

## Version History

- **v1.0.0**: Original flat structure
- **v2.0.0**: Organized into subdirectories (2026-03-17)

## Related Documentation

- Main documentation: `../POWER.md`
- Steering files: `../steering/`
- Hook definitions: `../hooks/`
