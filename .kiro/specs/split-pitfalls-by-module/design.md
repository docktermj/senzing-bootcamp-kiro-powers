# Design Document

## Overview

This feature adds in-file navigation to `senzing-bootcamp/steering/common-pitfalls.md` to reduce context waste when the agent loads the file for a specific module issue. Instead of splitting into separate files (which would break the existing `agent-instructions.md` reference), we add a Quick Navigation table of contents at the top with anchor links, HTML anchor tags on each section heading, and a navigation reminder in the Guided Troubleshooting section.

## Architecture

### Approach

This is a content-only change to a single steering file. Three additions are made:

1. **Quick Navigation section**: Inserted after the introductory paragraph and before the "Guided Troubleshooting" section. Contains a compact list of anchor links to every major section in the file.

2. **HTML anchor tags**: An `<a id="..."></a>` tag is added immediately before each module section heading. Anchor IDs follow a consistent kebab-case convention.

3. **Navigation reminder**: A short note is added to the Guided Troubleshooting section (after the existing diagnostic questions) reminding the agent to jump to the relevant module section and present only the matching pitfall.

### File Modified

- `senzing-bootcamp/steering/common-pitfalls.md` — add navigation structure

### No Files Modified

- `senzing-bootcamp/steering/agent-instructions.md` — no changes needed; the existing "load `common-pitfalls.md`" reference remains valid

### Section Structure

The additions fit into the existing document as follows:

```markdown
---
inclusion: manual
---

# Common Pitfalls Quick Reference

Load on errors, when user is stuck, or preventively at module start. ...

## Quick Navigation                          ← NEW SECTION
- [Module 0: SDK Setup](#module-0)
- [Module 1: Quick Demo](#module-1)
- ...
- [General Pitfalls](#general-pitfalls)
- [MCP Server Unavailable](#mcp-unavailable)
- [Recovery Quick Reference](#recovery)
- [Pre-Module Checklist](#pre-module-checklist)

## Guided Troubleshooting — Ask Before Scanning
(existing diagnostic questions)
Then use their answers to jump to the relevant section...
**Navigation tip:** Use the anchor links above...  ← NEW NOTE

<a id="module-0"></a>                        ← NEW ANCHOR
## Module 0: SDK Setup
(existing content unchanged)

<a id="module-1"></a>                        ← NEW ANCHOR
## Module 1: Quick Demo
(existing content unchanged)

... (same pattern for all sections)
```

### Anchor ID Convention

| Section | Anchor ID |
| --- | --- |
| Module 0: SDK Setup | `module-0` |
| Module 1: Quick Demo | `module-1` |
| Module 2: Business Problem | `module-2` |
| Module 3: Data Collection | `module-3` |
| Module 4: Data Quality | `module-4` |
| Module 5: Data Mapping | `module-5` |
| Module 6: Single Source Loading | `module-6` |
| Module 7: Multi-Source Orchestration | `module-7` |
| Module 8: Query and Validation | `module-8` |
| Modules 9-12: Production Readiness | `modules-9-12` |
| General Pitfalls | `general-pitfalls` |
| MCP Server Unavailable | `mcp-unavailable` |
| Recovery Quick Reference | `recovery` |
| Pre-Module Checklist | `pre-module-checklist` |

## Correctness Properties

Since this is a markdown content change (not code), correctness is verified by checking the output file:

1. **Quick Navigation present**: The file contains a "Quick Navigation" section with anchor links to all module sections
2. **All anchors present**: The file contains `<a id="module-0"></a>` through `<a id="modules-9-12"></a>`, plus `general-pitfalls`, `mcp-unavailable`, `recovery`, and `pre-module-checklist`
3. **Navigation reminder present**: The Guided Troubleshooting section contains a note about using anchor links to jump to the relevant section
4. **Existing content preserved**: All existing sections (Module 0 through Modules 9-12, General Pitfalls, MCP Server Unavailable, Recovery Quick Reference, Pre-Module Checklist) remain in the file with their content unchanged
5. **YAML front matter preserved**: The file begins with `inclusion: manual` front matter
6. **Anchor-link consistency**: Every href in the Quick Navigation section has a matching `<a id="..."></a>` tag in the document
