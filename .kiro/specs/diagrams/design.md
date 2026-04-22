# Design Document

## Overview

Three markdown files in `senzing-bootcamp/docs/diagrams/` provide text-based visual documentation of the bootcamp. All diagrams use ASCII art with Unicode box-drawing characters, requiring no special rendering tools.

## Architecture

### File Structure

```
senzing-bootcamp/docs/diagrams/
├── data-flow.md              # Data transformation and pipeline diagrams
├── module-flow.md            # Module progression and learning paths
├── module-prerequisites.md   # Module prerequisite reference
└── system-architecture.md    # Runtime architecture diagram
```

### Diagram Format

All diagrams use:
- Unicode box-drawing characters (`┌ ┐ └ ┘ │ ─ ┬ ┤ ├ ┴`) for boxes
- Arrow characters (`▼ ▶ ◀ ▲ →`) for flow direction
- Plain text labels inside boxes
- Standard markdown code fences (` ```text `) for rendering

### Content Summary

**data-flow.md** — 8 diagrams:
1. Complete data flow overview (source → transform → load → resolve → output)
2. Detailed transformation pipeline (field mapping example)
3. Loading pipeline (records → SDK → database)
4. Multi-source integration (3 sources → unified entities)
5. Query pipeline (request → SDK → results)
6. Backup pipeline (project files → ZIP → off-site)
7. Monitoring pipeline (logs → metrics → dashboards → alerts)
8. Data lineage tracking (metadata at each stage)

**module-flow.md** — 5 sections:
1. Complete module flow (modules 0–12 with activities)
2. Four learning paths (A: Quick Demo, B: Fast Track, C: Complete Beginner, D: Full Production)
3. Module dependencies list
4. Skip conditions table
5. Module outputs reference

**system-architecture.md** — 3 sections:
1. Runtime architecture (application → SDK → database with optional layers)
2. Data flow summary (raw → transform → SDK → query)
3. Module output reference (what each module produces)

## Constraints

- No Mermaid or other rendered diagram formats — ASCII art only
- Files must be readable in any text editor without extensions
- Diagrams must accurately reflect the bootcamp module structure (modules 0–12)
