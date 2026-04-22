# Design Document

## Overview

The documentation-guides feature consists of five static markdown artifacts distributed within the senzing-bootcamp power. No application code is involved — all artifacts are markdown files placed in their appropriate directories per the repository organization policy. The troubleshooting decision tree is a manual-inclusion steering file; all others are user-facing documentation or templates.

## Architecture

### File Layout

```text
senzing-bootcamp/
├── docs/
│   ├── guides/
│   │   ├── COMMON_MISTAKES.md          # Mistake catalog with examples and fixes
│   │   └── GETTING_HELP.md             # Support hierarchy and quick-reference table
│   └── diagrams/
│       └── module-prerequisites.md     # Mermaid dependency diagram
├── templates/
│   └── lessons_learned.md              # Post-project retrospective template
└── steering/
    └── troubleshooting-decision-tree.md  # Diagnostic flowchart (inclusion: manual)
```

### Common Mistakes Guide Structure

Categories with real examples and fixes:

| Category         | Coverage                                        |
| ---------------- | ----------------------------------------------- |
| Data Preparation | Raw data loading, missing mappings, format issues |
| SDK Configuration | Connection strings, license paths, init errors  |
| Loading          | Duplicate records, batch size, error handling    |
| Query            | Wrong flags, missing entity IDs, result parsing  |
| Production       | Scaling, monitoring, deployment pitfalls         |

### Getting Help Guide Structure

Support hierarchy in priority order:

| Priority | Resource           | When to Use                        |
| -------- | ------------------ | ---------------------------------- |
| 1        | Agent              | First line — has full project context |
| 2        | FAQ                | Common questions with quick answers |
| 3        | MCP Tools          | Programmatic checks and validation |
| 4        | Guides             | Deep-dive reference material       |
| 5        | docs.senzing.com   | Official Senzing documentation     |
| 6        | Support            | Unresolved issues needing human help |

### Lessons Learned Template Sections

- Project Summary, What Went Well, What Could Be Improved
- Key Decisions and Rationale (table format)
- Data Insights, Recommendations for Next Time
- Artifacts Produced (table format), Team Notes

### Module Prerequisites Diagram

Mermaid `graph TD` showing module dependencies (e.g., Module 0 → Module 1, Module 0 → Module 6) with skip paths annotated.

### Troubleshooting Decision Tree

Mermaid flowchart with `inclusion: manual` frontmatter. Loaded by the Agent when systematic diagnosis is needed. Branches by problem type (setup, data, loading, query, performance) with resolution steps at leaf nodes.

## Constraints

- All files are static markdown — no application code.
- Troubleshooting decision tree uses `inclusion: manual` so it is loaded only when needed.
- Mermaid diagrams must render in standard markdown viewers.
- File placement follows the repository organization policy.
