# User Guides

This directory contains essential user-facing guides for the Senzing Boot Camp.

## Available Guides (6 Essential Files)

### Getting Started

- **[QUICK_START.md](QUICK_START.md)** - Three fast paths to get started (10 min, 30 min, or 2 hours)
- **[ONBOARDING_CHECKLIST.md](ONBOARDING_CHECKLIST.md)** - Pre-flight checklist before starting the boot camp

### Progress Tracking

- **[PROGRESS_TRACKER.md](PROGRESS_TRACKER.md)** - Track your completion through all 13 modules

### Reference Guides

- **[DESIGN_PATTERNS.md](DESIGN_PATTERNS.md)** - Gallery of 10 common entity resolution patterns
- **[TROUBLESHOOTING_INDEX.md](TROUBLESHOOTING_INDEX.md)** - Quick reference for common issues and solutions

### Boot Camp Features

- **[HOOKS_INSTALLATION_GUIDE.md](HOOKS_INSTALLATION_GUIDE.md)** - Install pre-configured Kiro hooks for automation

## Why So Few Guides?

The Senzing Boot Camp leverages the **Senzing MCP Server** to provide most documentation dynamically through tools like:

- `get_capabilities` - Discover available tools and workflows
- `search_docs` - Search comprehensive Senzing documentation
- `sdk_guide` - Platform-specific SDK installation and setup
- `explain_error_code` - Diagnose errors with detailed explanations
- `find_examples` - Working code examples from GitHub repositories

This approach:
- ✅ Keeps documentation always up-to-date
- ✅ Provides context-aware guidance
- ✅ Reduces duplication
- ✅ Focuses guides on boot camp-specific workflows

## Guides Moved to Development Repository

The following guides were moved to `senzing-bootcamp-power-development/` because they are for power developers, not bootcamp users:

**Agent Implementation Guides:**
- MODULE_0_AGENT_GUIDE.md → Agent instructions for running Module 0
- FEEDBACK_WORKFLOW.md → Power development workflow

**Development Documentation:**
- IMPROVEMENT_MODULE_0_LIVE_DEMO.md → Development notes on improvements

These guides are still available for power developers and maintainers in the development repository.

## Quick Reference

| Guide | When to Use | Time | Purpose |
|-------|-------------|------|---------|
| QUICK_START | Before Module 1 | 5 min | Choose your path |
| ONBOARDING_CHECKLIST | Before Module 1 | 15 min | Verify readiness |
| PROGRESS_TRACKER | Throughout | Ongoing | Track completion |
| DESIGN_PATTERNS | Module 1 | 10 min | Choose pattern |
| TROUBLESHOOTING_INDEX | When stuck | As needed | Find solutions |
| HOOKS_INSTALLATION_GUIDE | Before Module 4 | 15 min | Automate checks |

## Related Documentation

### For Planning
- **Design Patterns** → Helps with Module 1 (Business Problem)
- **Cost Estimation** → See `../../steering/cost-estimation.md`
- **Complexity Estimator** → See `../../steering/complexity-estimator.md`

### For Setup
- **Environment Setup** → See `../../steering/environment-setup.md`
- **SDK Guide** → Use MCP tool `sdk_guide`

### For Automation
- **Hooks Installation** → Automates quality checks
- **Testing Strategy** → Use MCP: `search_docs(query="testing best practices")`

### For Troubleshooting
- **Troubleshooting Index** → This directory
- **Common Pitfalls** → See `../../steering/common-pitfalls.md`
- **Troubleshooting Decision Tree** → See `../../steering/troubleshooting-decision-tree.md`
- **Recovery Procedures** → Use MCP: `search_docs(query="backup and recovery")`

## For Agents

When users need guidance:
1. **Before starting** → Suggest QUICK_START and ONBOARDING_CHECKLIST
2. **Module 1** → Suggest DESIGN_PATTERNS
3. **Before Module 4** → Suggest HOOKS_INSTALLATION_GUIDE
4. **Throughout** → Remind about PROGRESS_TRACKER
5. **Troubleshooting** → Point to TROUBLESHOOTING_INDEX
6. **Feedback** → Users can add to `../feedback/SENZING_BOOTCAMP_POWER_FEEDBACK_TEMPLATE.md`

For Senzing-specific questions, use MCP tools:
- Version compatibility → `get_capabilities`
- Prerequisites → `sdk_guide`
- FAQ → `search_docs`
- Performance → `search_docs` with category="performance"
- Docker setup → `sdk_guide` with platform="docker"

For agent implementation details, see `senzing-bootcamp-power-development/guides/`

## For Maintainers

When adding new guides:
- ✅ **DO** add boot camp-specific workflows and processes
- ✅ **DO** add guides that reference multiple modules
- ✅ **DO** add guides for Kiro-specific features (hooks, steering, etc.)
- ❌ **DON'T** duplicate Senzing documentation (use MCP server instead)
- ❌ **DON'T** add generic checklists or reference cards
- ❌ **DON'T** add internal development notes (use development repository)

## Version History

- **2026-03-24**: Moved agent/developer guides to development repository (MODULE_0_AGENT_GUIDE, FEEDBACK_WORKFLOW, IMPROVEMENT_MODULE_0_LIVE_DEMO)
- **2026-03-23**: Reduced from 23 guides to 8 essential guides, leveraging MCP server for Senzing documentation
- **2026-03-17**: Initial guide collection created with 23 guides

## Navigation

- [← Back to docs/](../)
- [→ Modules](../modules/)
- [→ Policies](../policies/)
- [→ Steering](../../steering/)
