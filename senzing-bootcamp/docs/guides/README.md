# User Guides

This directory contains essential user-facing guides for the Senzing Boot Camp.

## Available Guides (8 Essential Files)

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
- **[FEEDBACK_WORKFLOW.md](FEEDBACK_WORKFLOW.md)** - How to provide feedback about the boot camp

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

## Removed Guides (Moved to Development Repository)

The following 15 guides were moved because they either duplicate MCP server functionality or are internal documentation:

**Duplicates MCP Server:**
- COMPATIBILITY_MATRIX.md → Use `get_capabilities`
- PREREQUISITES.md → Use `sdk_guide`
- FAQ.md → Use `search_docs`
- PERFORMANCE_TUNING.md → Use `search_docs` with category="performance"
- DOCKER_QUICK_START.md → Use `sdk_guide` with platform="docker"
- DEPLOYMENT_CHECKLIST.md → Generic checklist

**Internal/Development:**
- PATH_SELECTION_FIX.md - Bug fix documentation
- MODULE_COMPLETION_TRACKER.md - Duplicate of PROGRESS_TRACKER.md
- INSTALLATION_VERIFICATION.md - Internal policy
- EXECUTIVE_SUMMARY.md + .pdf - Marketing material
- PREFLIGHT_CHECKLIST.md - Duplicate of ONBOARDING_CHECKLIST.md
- QUICK_REFERENCE_CARD.md - Duplicate of steering/quick-reference.md
- VISUAL_GUIDE.md - Optional diagrams

## Quick Reference

| Guide | When to Use | Time | Purpose |
|-------|-------------|------|---------|
| QUICK_START | Before Module 1 | 5 min | Choose your path |
| ONBOARDING_CHECKLIST | Before Module 1 | 15 min | Verify readiness |
| PROGRESS_TRACKER | Throughout | Ongoing | Track completion |
| DESIGN_PATTERNS | Module 1 | 10 min | Choose pattern |
| TROUBLESHOOTING_INDEX | When stuck | As needed | Find solutions |
| HOOKS_INSTALLATION_GUIDE | Before Module 4 | 15 min | Automate checks |
| FEEDBACK_WORKFLOW | Anytime | 5 min | Submit feedback |

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
- **Testing Strategy** → See `../../steering/testing-strategy.md`

### For Troubleshooting
- **Troubleshooting Index** → This directory
- **Common Pitfalls** → See `../../steering/common-pitfalls.md`
- **Troubleshooting Decision Tree** → See `../../steering/troubleshooting-decision-tree.md`
- **Recovery Procedures** → See `../../steering/recovery-procedures.md`

## For Agents

When users need guidance:
1. **Before starting** → Suggest QUICK_START and ONBOARDING_CHECKLIST
2. **Module 1** → Suggest DESIGN_PATTERNS
3. **Before Module 4** → Suggest HOOKS_INSTALLATION_GUIDE
4. **Throughout** → Remind about PROGRESS_TRACKER
5. **Troubleshooting** → Point to TROUBLESHOOTING_INDEX
6. **Feedback** → Explain FEEDBACK_WORKFLOW

For Senzing-specific questions, use MCP tools:
- Version compatibility → `get_capabilities`
- Prerequisites → `sdk_guide`
- FAQ → `search_docs`
- Performance → `search_docs` with category="performance"
- Docker setup → `sdk_guide` with platform="docker"

## For Maintainers

When adding new guides:
- ✅ **DO** add boot camp-specific workflows and processes
- ✅ **DO** add guides that reference multiple modules
- ✅ **DO** add guides for Kiro-specific features (hooks, steering, etc.)
- ❌ **DON'T** duplicate Senzing documentation (use MCP server instead)
- ❌ **DON'T** add generic checklists or reference cards
- ❌ **DON'T** add internal development notes (use development repository)

## Version History

- **2026-03-23**: Reduced from 23 guides to 8 essential guides, leveraging MCP server for Senzing documentation
- **2026-03-17**: Initial guide collection created with 23 guides

## Navigation

- [← Back to docs/](../)
- [→ Modules](../modules/)
- [→ Policies](../policies/)
- [→ Steering](../../steering/)
