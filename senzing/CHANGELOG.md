# Changelog

All notable changes to the Senzing Kiro Power will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Additional language examples (TypeScript, Go)
- Video tutorial references
- Interactive tutorials
- Community-contributed content

## [1.0.0] - 2026-03-22

### Added

#### User Experience Enhancements
- **Table of Contents** in POWER.md for easier navigation (12 sections)
- **Prerequisites section** with clear requirements checklist before starting
- **5-Minute Quick Start** for rapid onboarding with 5 practical steps and working examples
- **Code Examples section** with 4 copy-paste ready examples:
  - Map and validate data
  - Generate and use SDK code
  - Search for help
  - Get sample data for testing
- **Troubleshooting Quick Reference** in POWER.md with top 5 common issues:
  - Cannot connect to MCP server (with symptoms, quick fixes, solutions)
  - Wrong attribute names in mapped data (with common mistakes)
  - SDK method not found / wrong signature
  - Error codes (SENZ####)
  - Slow performance / timeouts
- **Table of Contents** in large steering files for better navigation:
  - advanced-topics.md (8 sections, 855 lines)
  - monitoring.md (9 sections, 834 lines)
  - security-compliance.md (7 sections, 803 lines)
  - use-cases.md (5 use cases, 790 lines)

#### Core Documentation
- POWER.md with comprehensive metadata (17 fields)
- MCP server configuration (mcp.json)
- Comprehensive CHANGELOG.md
- Automated validation script (validate_power.py, 400+ lines)

#### Steering Guides (19 files)
- **steering.md** - Navigation hub with quick links and task-based index
- **getting-started.md** - Quick start, workflows, decision trees, ASCII diagrams
- **quick-reference.md** - Copy-paste ready commands and one-liners
- **best-practices.md** - Do's, don'ts, common pitfalls
- **performance.md** - Optimization, tuning, scaling strategies
- **troubleshooting.md** - Error handling, debugging, typical sessions
- **examples.md** - Code examples (Python, Java, C#, Rust)
- **use-cases.md** - 5 real-world implementation walkthroughs with metrics
- **security-compliance.md** - GDPR, CCPA, PII handling, access control
- **advanced-topics.md** - Custom config, network analysis, graph traversal
- **monitoring.md** - Metrics, Prometheus, Grafana, alerting, dashboards
- **data-sources.md** - 20+ system integrations (CRM, ERP, e-commerce)
- **cicd.md** - GitHub Actions, GitLab CI, Jenkins, deployment automation
- **faq.md** - 100+ questions covering all topics
- **community.md** - Resources, support, learning materials
- **reference.md** - Tool parameters, checklists, glossary (50+ terms)
- **config-examples.md** - Configuration examples for 8+ scenarios
- **smoke-test.md** - Quick and detailed validation procedures
- **offline-mode.md** - Offline usage and air-gapped deployment guidance

#### Metadata and Quality
- Enhanced frontmatter with 17 fields (version, license, maturity, compatibility, etc.)
- Visual badges (version, maturity, license, Senzing compatibility)
- Quick links bar (homepage, documentation, support, GitHub)
- Metadata reference table with field descriptions
- 22 keywords for discoverability
- 5 categorical tags
- Maturity indicator: stable
- License: Apache-2.0
- Senzing compatibility: 4.0+

#### Features and Content
- 4 interactive checklists (100+ items total)
- 3 ASCII workflow diagrams
- 5 integration patterns
- 5 real-world use cases with business metrics
- 50+ glossary terms
- 100+ FAQ items
- 50+ code examples across multiple languages (Python, Java, C#, Rust)
- 20+ data source integration examples
- 5 CI/CD platform configurations
- MCP server configuration with timeout (30s) and log level control

### Changed
- **BREAKING**: Updated license from CC-BY-4.0 to Apache-2.0 for consistency
- **BREAKING**: Removed Senzing V3 compatibility (V4 only)
- Reorganized file structure for clarity:
  - Moved user-facing guides to `steering/` directory (19 files)
  - Moved power development documentation to `senzing-development/docs/` directory
  - Cleaner root with only 4 essential files (POWER.md, CHANGELOG.md, mcp.json, validate_power.py)
- Updated all internal references to reflect new file locations
- Updated validation script to check files in new locations
- Updated last_updated date to 2026-03-22

### Removed
- V3 compatibility references from documentation
- `version: "3.x"` parameter mentions
- `steering/test-examples.md` - Redundant with smoke-test.md and validate_power.py
- Development documentation from user-facing power (moved to senzing-development/)

### Documentation Coverage
- Getting started and quick reference
- Best practices and common pitfalls
- Performance optimization and tuning
- Troubleshooting and error handling (with quick reference)
- Security and compliance (GDPR, CCPA)
- Advanced techniques and network analysis
- Monitoring and observability
- Data source integration (20+ systems)
- CI/CD integration (5 platforms)
- Community resources and support
- Offline and air-gapped deployment

### Quality Assurance
- Automated validation script with 6 validation categories
- File structure validation
- Metadata validation
- Internal link validation
- MCP configuration validation
- Steering file completeness validation
- File size checks
- Smoke test procedures (5-minute and 15-minute)
- All validations pass: 0 errors, 0 warnings

### Statistics
- **Total files**: 23 (4 core + 19 steering guides)
- **Total size**: 360KB (clean and optimized)
- **Documentation**: 10,000+ lines
- **Steering guides**: 19 comprehensive guides
- **FAQ items**: 100+
- **Code examples**: 50+
- **Glossary terms**: 50+
- **Data source integrations**: 20+
- **CI/CD examples**: 5 platforms
- **Use cases**: 5 detailed walkthroughs
- **Checklists**: 4 interactive (100+ items)
- **Diagrams**: 3 ASCII workflows

## Version History

### Version Numbering

This power follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes or breaking changes
- **MINOR** version: New functionality in a backward compatible manner
- **PATCH** version: Backward compatible bug fixes

### Release Process

1. Update version in POWER.md frontmatter
2. Update last_updated date
3. Document changes in CHANGELOG.md under [Unreleased]
4. Run validation: `python validate_power.py`
5. Run smoke tests
6. Move [Unreleased] changes to new version section
7. Tag release in version control

## Migration Guides

### Migrating to 1.0.0

**From 0.x versions**: This is the first stable release.

**Breaking Changes**:
1. **License Change**: CC-BY-4.0 → Apache-2.0
   - No action required for users
   - More permissive license

2. **V3 Removed**: Senzing V3 references removed
   - Use Senzing SDK 4.0+
   - Use `version: "current"` or `version: "4.0"` in MCP tool calls
   - Do not use `version: "3.x"` parameter

**File Structure Changes**:
- Development docs moved to `senzing-development/` (not part of user-facing power)
- All user guides now in `steering/` directory
- No action required - all links updated automatically

## Breaking Changes

### 1.0.0
- License changed from CC-BY-4.0 to Apache-2.0
- Senzing V3 compatibility removed (V4 only)

## Deprecations

### 1.0.0
- None

## Known Issues

### 1.0.0
- None reported

## Contributors

### 1.0.0
- Complete power development and documentation
- 19 comprehensive steering guides
- Validation and testing infrastructure
- User experience enhancements (TOCs, quick start, examples, troubleshooting)
- File structure reorganization
- Quality assurance and production readiness

## Support

For questions about specific versions:
- Check the version's section in this changelog
- Use `submit_feedback` MCP tool
- Contact Senzing support: [https://senzing.zendesk.com](https://senzing.zendesk.com/hc/en-us/requests/new)

## Links

- [Homepage](https://senzing.com)
- [Documentation](https://senzing.com/documentation)
- [Support](https://senzing.zendesk.com/hc/en-us/requests/new)
- [GitHub](https://github.com/senzing)

## Changelog Maintenance

This changelog is manually maintained. When making changes:

1. **Add entries under [Unreleased]** for work in progress
2. **Move to versioned section** when releasing
3. **Use categories**: Added, Changed, Deprecated, Removed, Fixed, Security
4. **Be specific**: Include file names, feature names, and impacts
5. **Link issues**: Reference issue numbers when applicable
6. **Date releases**: Use ISO 8601 format (YYYY-MM-DD)

### Categories

- **Added**: New features, files, or capabilities
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed in future versions
- **Removed**: Features that have been removed
- **Fixed**: Bug fixes
- **Security**: Security-related changes

## Notes

- This power integrates with Senzing MCP server (Apache-2.0)
- Power documentation is licensed under Apache-2.0
- Compatible with Senzing SDK 4.0+
- Requires internet connection for MCP server access (see steering/offline-mode.md for alternatives)
- Production ready and validated (0 errors, 0 warnings)

---

**Note**: This changelog tracks changes to the Senzing Kiro Power itself, not changes to the Senzing SDK or MCP server. For Senzing product changes, see official Senzing release notes.
