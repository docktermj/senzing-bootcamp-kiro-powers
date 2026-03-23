# Build Artifacts Cleanup - March 23, 2026

## Summary

Moved build artifacts from the Power distribution to the development repository to keep the Power clean and focused on user-facing content.

## Files Moved

### Build Artifacts (1 file)

1. **mdpdf.log** → `senzing-bootcamp-development/mdpdf.log`
   - PDF generation tool log file dated 2026-03-19
   - Generated when creating PDF versions of documentation
   - Not referenced anywhere in Power documentation
   - Not needed for Power distribution

## Files Analyzed But Kept

### requirements.txt and requirements-dev.txt

**Decision**: KEEP in Power distribution

**Rationale**:
- These files serve as reference examples for the Power itself
- Extensively referenced in PYTHON_REQUIREMENTS_POLICY.md (30+ references)
- Referenced in multiple module docs, steering files, and examples
- Show users what a proper requirements file should look like
- Demonstrate the dependency structure for Senzing projects
- Part of the documented project structure in POWER.md

**References**:
- `docs/policies/PYTHON_REQUIREMENTS_POLICY.md` - Complete policy document
- `docs/policies/README.md` - Policy overview
- `docs/modules/MODULE_12_DEPLOYMENT_PACKAGING.md` - Deployment guidance
- `examples/*/README.md` - Multiple example projects
- `steering/docker-deployment.md` - Docker deployment patterns

## Impact

### Power Distribution
- Removed 1 build artifact file
- No functional impact on Power capabilities
- Cleaner root directory

### Development Repository
- Added mdpdf.log for reference
- Preserves build history
- Documents PDF generation process

## Verification

No references to mdpdf.log found in:
- POWER.md
- README.md
- Any documentation files
- Any steering files
- Any policy files

## Related Reorganizations

This cleanup is part of the ongoing effort to separate:
1. **Power distribution** (user-facing content)
2. **Development artifacts** (internal tools and history)

Previous reorganizations:
- Phase 1: Moved 34 internal development files (March 17-21, 2026)
- Phase 2: Removed 15 redundant guide files (March 23, 2026)
- Phase 3: Removed 3 static demo scripts (March 23, 2026)
- Phase 4: Build artifacts cleanup (March 23, 2026) ← This document

## Total Reorganization Summary

**Files moved to development repository**: 55 files
- 34 internal development files
- 15 redundant guide files + 2 PDFs
- 3 static demo scripts
- 1 build artifact

**Result**: Leaner, more focused Power distribution with all historical content preserved in development repository.

## Version

- **Date**: March 23, 2026
- **Phase**: 4 (Build Artifacts Cleanup)
- **Files Moved**: 1
- **Cumulative Total**: 55 files moved to development

