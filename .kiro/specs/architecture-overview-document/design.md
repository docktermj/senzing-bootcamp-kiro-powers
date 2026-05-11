# Design Document

## Overview

This design describes the creation of `senzing-bootcamp/docs/guides/ARCHITECTURE.md` — a comprehensive architecture overview document for the senzing-bootcamp Kiro Power. The document serves as the single entry point for contributors and advanced bootcampers to understand how the system's components (steering files, hooks, scripts, MCP server, configuration files, and modules) relate to each other.

The document is pure Markdown with ASCII/box-drawing diagrams. It has no runtime dependencies, no external images, and must be valid CommonMark. It will be integrated into the existing documentation index at `docs/guides/README.md` and `docs/README.md`.

### Design Decisions

1. **ASCII diagrams over Mermaid**: The requirements mandate no external rendering tools. All diagrams use Unicode box-drawing characters (`─`, `│`, `┌`, `┐`, `└`, `┘`, `├`, `┤`, `┬`, `┴`, `┼`) and standard ASCII (`+`, `-`, `|`, `>`, `<`). This ensures readability in any text editor or terminal.

2. **Single file, not split**: The architecture document is a reference guide, not a steering file. It lives in `docs/guides/` and is not subject to context budget splitting. A single file with a table of contents provides the best navigation experience.

3. **Two audiences**: The document addresses both contributors (who modify the power) and advanced bootcampers (who want to understand the system). Contributor-specific details (like file format internals) are clearly labeled.

4. **Cross-references over duplication**: Where existing documentation covers a topic in depth (GLOSSARY.md, STEERING_INDEX.md, PROGRESS_FILE_SCHEMA.md), the architecture document provides a summary and links to the detailed guide rather than duplicating content.

## Architecture

The ARCHITECTURE.md document itself has no software architecture — it is a static documentation artifact. The "architecture" here refers to the document's internal structure and how it maps to the system it describes.

### Document Structure

```
ARCHITECTURE.md
├── Table of Contents (anchor links)
├── Component Overview
│   ├── Component table (directory, format, responsibility)
│   └── ASCII diagram: top-level layout
├── Data Flow
│   ├── Session start decision logic
│   ├── End-to-end flow narrative
│   └── ASCII diagram: session lifecycle
├── Module Lifecycle
│   ├── State machine description
│   ├── Split module phase loading
│   └── ASCII diagram: module states
├── Hook Architecture
│   ├── Categories (critical vs module)
│   ├── Trigger flow
│   └── ASCII diagram: hook evaluation
├── Configuration Relationships
│   ├── File dependency graph
│   ├── Read-only vs mutable classification
│   └── ASCII diagram: config data flow
├── MCP Integration
│   ├── Tool categories
│   ├── Local vs remote boundary
│   └── ASCII diagram: MCP boundary
└── Context Budget Management
    ├── Budget states and thresholds
    ├── Retention priority tiers
    └── ASCII diagram: budget state machine
```

### System Components Covered

The document describes these system components and their relationships:

| Component | Directory | Key Files |
|-----------|-----------|-----------|
| Steering | `steering/` | `*.md`, `steering-index.yaml` |
| Hooks | `hooks/` | `*.kiro.hook`, `hook-categories.yaml` |
| Scripts | `scripts/` | `*.py` |
| Config | `config/` | `module-dependencies.yaml`, `bootcamp_progress.json`, `bootcamp_preferences.yaml` |
| MCP | `mcp.json` | Remote server at `mcp.senzing.com` |
| Modules | Curriculum units 1-11 | Steering files + config gates |
| Docs | `docs/` | Guides, diagrams, policies |

## Components and Interfaces

### Input Sources (for document content)

The architecture document synthesizes information from these authoritative sources:

1. **`config/module-dependencies.yaml`** — Module prerequisite graph, track definitions, gate conditions
2. **`steering/steering-index.yaml`** — File metadata (token counts, size categories), module-to-file mappings, keyword index, budget thresholds
3. **`hooks/hook-categories.yaml`** — Critical vs module hook classification
4. **`steering/agent-context-management.md`** — Context budget states, retention priority, unload rules
5. **`steering/onboarding-flow.md`** — Session start logic, hook installation, directory setup
6. **`steering/session-resume.md`** — Resume detection, state file reading
7. **`POWER.md`** — MCP server description, module overview
8. **`steering/mcp-offline-fallback.md`** — MCP failure behavior

### Output Artifacts

1. **`senzing-bootcamp/docs/guides/ARCHITECTURE.md`** — The primary deliverable
2. **Updated `senzing-bootcamp/docs/guides/README.md`** — New entry in the reference documentation section
3. **Updated `senzing-bootcamp/docs/README.md`** — New entry in the guides listing

### Cross-References (outbound links from ARCHITECTURE.md)

- `POWER.md` (relative: `../../POWER.md`)
- `docs/guides/GLOSSARY.md` (relative: `GLOSSARY.md`)
- `docs/guides/STEERING_INDEX.md` (relative: `STEERING_INDEX.md`)
- `docs/guides/PROGRESS_FILE_SCHEMA.md` (relative: `PROGRESS_FILE_SCHEMA.md`)
- `docs/guides/HOOKS_INSTALLATION_GUIDE.md` (relative: `HOOKS_INSTALLATION_GUIDE.md`)
- `docs/guides/OFFLINE_MODE.md` (relative: `OFFLINE_MODE.md`)

## Data Models

This feature produces a static Markdown file. There are no runtime data models, schemas, or state objects. The "data" is the document content itself, structured as CommonMark with the following constraints:

- **Headings**: H1 for title, H2 for major sections, H3 for subsections
- **Diagrams**: Fenced code blocks (` ```text `) containing ASCII art
- **Tables**: Pipe-delimited CommonMark tables
- **Links**: Relative paths using `[text](path)` syntax
- **Table of Contents**: Manually maintained list of `[Section Name](#anchor)` links

### Diagram Style Guide

All diagrams follow these conventions:
- Box-drawing characters for structure: `┌─┐ │ └─┘ ├ ┤ ┬ ┴ ┼`
- Arrows for flow: `→ ← ↓ ↑` or `-->` for ASCII-only contexts
- Maximum width: 78 characters (fits standard terminal)
- Labels inside boxes, centered or left-aligned
- Consistent spacing: 2-character minimum between elements

## Error Handling

Since this is a documentation artifact, "errors" are limited to:

1. **Invalid CommonMark**: Caught by the existing `validate_commonmark.py` CI script. The document must pass this validation.
2. **Broken relative links**: Cross-references must point to files that exist. Verified by checking file existence.
3. **Stale information**: If the source files (module-dependencies.yaml, steering-index.yaml, etc.) change, the architecture document may become outdated. A comment at the top of the document notes the version/date and which source files it reflects.

## Testing Strategy

**PBT is NOT applicable** for this feature. The deliverable is a static Markdown documentation file — there are no functions, data transformations, or logic to test with property-based testing. The document's correctness is verified through:

### Validation Approach

1. **CommonMark compliance** (automated): Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` against the new file. This is already part of CI.

2. **Link integrity** (manual verification): Confirm all relative links in the document point to existing files.

3. **Structural completeness** (checklist): Verify the document contains all required sections per the requirements:
   - Table of Contents with anchor links
   - Component Overview with ASCII diagram
   - Data Flow with ASCII diagram
   - Module Lifecycle with ASCII diagram
   - Hook Architecture with ASCII diagram
   - Configuration Relationships with ASCII diagram
   - MCP Integration with ASCII diagram
   - Context Budget Management with ASCII diagram

4. **Diagram width** (automated): No line in the document exceeds 120 characters (generous limit for code blocks with diagrams).

5. **Index integration**: Verify `docs/guides/README.md` and `docs/README.md` reference the new file.

### Test Commands

```bash
# CommonMark validation
python3 senzing-bootcamp/scripts/validate_commonmark.py senzing-bootcamp/docs/guides/ARCHITECTURE.md

# Line length check (no line > 120 chars)
awk 'length > 120 { print NR": "length" chars - "$0; found++ } END { exit (found>0) }' senzing-bootcamp/docs/guides/ARCHITECTURE.md

# Link existence check
grep -oP '\[.*?\]\(\K[^)]+' senzing-bootcamp/docs/guides/ARCHITECTURE.md | while read link; do
  test -f "senzing-bootcamp/docs/guides/$link" || echo "BROKEN: $link"
done
```
