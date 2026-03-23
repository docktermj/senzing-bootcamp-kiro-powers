# Removed Guide Files

These guide files were removed from the Senzing Boot Camp Power distribution because they either duplicate MCP server functionality or are internal documentation.

## Files in This Directory (15 files)

### Duplicates MCP Server Functionality (6 files)

These guides duplicate information that the Senzing MCP Server provides dynamically:

1. **COMPATIBILITY_MATRIX.md** - Version and platform compatibility
   - **MCP Alternative**: Use `get_capabilities` tool
   - **Why Removed**: MCP server provides current version info

2. **PREREQUISITES.md** + **PREREQUISITES.pdf** - Hardware/software requirements
   - **MCP Alternative**: Use `sdk_guide` tool
   - **Why Removed**: MCP server provides platform-specific prerequisites

3. **FAQ.md** - Frequently asked questions
   - **MCP Alternative**: Use `search_docs` tool
   - **Why Removed**: MCP server has comprehensive searchable documentation

4. **PERFORMANCE_TUNING.md** - Performance optimization guide
   - **MCP Alternative**: Use `search_docs` with category="performance"
   - **Why Removed**: MCP server provides current performance guidance

5. **DOCKER_QUICK_START.md** - Docker setup guide
   - **MCP Alternative**: Use `sdk_guide` with platform="docker"
   - **Why Removed**: MCP server provides current Docker setup instructions

6. **DEPLOYMENT_CHECKLIST.md** - Generic deployment checklist
   - **Why Removed**: Generic checklist, not boot camp-specific

### Internal/Development Documentation (7 files)

These are internal development notes, not user-facing guides:

7. **PATH_SELECTION_FIX.md** - Bug fix documentation
   - **Why Removed**: Internal development note about fixing path selection ambiguity

8. **MODULE_COMPLETION_TRACKER.md** - Detailed completion tracker
   - **Why Removed**: Duplicate of PROGRESS_TRACKER.md

9. **INSTALLATION_VERIFICATION.md** - Installation verification policy
   - **Why Removed**: Internal policy document, not a user guide

10. **EXECUTIVE_SUMMARY.md** + **EXECUTIVE_SUMMARY.pdf** - Marketing material
    - **Why Removed**: Marketing/sales material, not operational guide

11. **PREFLIGHT_CHECKLIST.md** - Pre-flight checklist
    - **Why Removed**: Duplicate of ONBOARDING_CHECKLIST.md

12. **QUICK_REFERENCE_CARD.md** - One-page reference
    - **Why Removed**: Duplicate of steering/quick-reference.md

13. **VISUAL_GUIDE.md** - Diagrams and flowcharts
    - **Why Removed**: Optional visual aids, not essential

## What Remains in the Power

Only 8 essential boot camp-specific guides remain:

1. **QUICK_START.md** - Boot camp-specific quick start paths
2. **ONBOARDING_CHECKLIST.md** - Boot camp-specific pre-flight checklist
3. **PROGRESS_TRACKER.md** - Track progress through 13 modules
4. **DESIGN_PATTERNS.md** - Boot camp-specific pattern gallery
5. **TROUBLESHOOTING_INDEX.md** - Boot camp-specific troubleshooting
6. **HOOKS_INSTALLATION_GUIDE.md** - Kiro hooks for boot camp
7. **FEEDBACK_WORKFLOW.md** - Boot camp feedback process
8. **README.md** - Guide index

## Benefits of Removal

1. **Reduced duplication** - MCP server is the single source of truth for Senzing documentation
2. **Always current** - MCP server documentation stays up-to-date automatically
3. **Smaller distribution** - Power package is more focused
4. **Clearer purpose** - Guides focus on boot camp-specific workflows
5. **Better maintenance** - Fewer files to keep in sync

## For Maintainers

If you need to reference these guides:
- They're preserved here for historical context
- Consider whether new guides duplicate MCP server functionality
- Ask: "Can the MCP server provide this information dynamically?"
- If yes, use MCP tools instead of creating static guides

## MCP Server Tools Reference

Instead of static guides, use these MCP tools:

| Removed Guide | MCP Tool | Parameters |
|---------------|----------|------------|
| COMPATIBILITY_MATRIX | `get_capabilities` | version="current" |
| PREREQUISITES | `sdk_guide` | topic="install", platform=... |
| FAQ | `search_docs` | query=..., version="current" |
| PERFORMANCE_TUNING | `search_docs` | query=..., category="performance" |
| DOCKER_QUICK_START | `sdk_guide` | topic="install", platform="docker" |

## Version History

- **2026-03-23**: Moved 15 guide files from Power distribution to development repository
