# Senzing Bootcamp Documentation

This directory contains all documentation for the Senzing Bootcamp.

## Directory Structure

### `/modules/`

Module-specific documentation files. Each module has detailed documentation about its purpose, workflow, and implementation.

**Files:**

- `MODULE_0_SDK_SETUP.md` - SDK installation and configuration
- `MODULE_1_QUICK_DEMO.md` - Quick demo with sample data (optional)
- `MODULE_2_BUSINESS_PROBLEM.md` - Business problem definition
- `MODULE_3_DATA_COLLECTION.md` - Data collection and source management
- `MODULE_4_DATA_QUALITY_AND_MAPPING.md` - Data quality assessment and mapping
- `MODULE_5_SINGLE_SOURCE_LOADING.md` - Single source loading patterns
- `MODULE_6_MULTI_SOURCE_ORCHESTRATION.md` - Multi-source orchestration
- `MODULE_7_QUERY_VALIDATION.md` - Query and validation with UAT
- `MODULE_8_PERFORMANCE_TESTING.md` - Performance testing and benchmarking
- `MODULE_9_SECURITY_HARDENING.md` - Security hardening for production
- `MODULE_10_MONITORING_OBSERVABILITY.md` - Monitoring and observability
- `MODULE_11_DEPLOYMENT_PACKAGING.md` - Deployment packaging

### `/policies/`

Policy documents that define standards and conventions for the bootcamp.

**Files:**

- `FILE_STORAGE_POLICY.md` - Where to store all project files (includes shell scripts, database, and demo code rules)
- `CODE_QUALITY_STANDARDS.md` - Coding standards and quality guidelines
- `DEPENDENCY_MANAGEMENT_POLICY.md` - Dependency management policy
- `SENZING_INFORMATION_POLICY.md` - MCP-only Senzing facts policy

### `/guides/`

User guides and installation instructions.

**Files:**

- `AFTER_BOOTCAMP.md` - Post-bootcamp guide for production and next steps
- `COLLABORATION_GUIDE.md` - Team collaboration workflows
- `COMMON_MISTAKES.md` - Most frequent bootcamp mistakes with real examples
- `DESIGN_PATTERNS.md` - Entity resolution design patterns
- `FAQ.md` - Frequently asked questions
- `GETTING_HELP.md` - Support hierarchy and when to use each resource
- `GLOSSARY.md` - Senzing entity resolution terminology
- `HOOKS_INSTALLATION_GUIDE.md` - Guide for installing Kiro hooks
- `OFFLINE_MODE.md` - What works without MCP and reconnection steps
- `ONBOARDING_CHECKLIST.md` - Pre-bootcamp checklist
- `PERFORMANCE_BASELINES.md` - Reference throughput and hardware requirements
- `PROGRESS_TRACKER.md` - Module completion tracking
- `QUALITY_SCORING_METHODOLOGY.md` - How quality scores are calculated
- `QUICK_START.md` - Three fast paths to get started

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

- Review per-module steering files in `steering/` for detailed workflows

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
