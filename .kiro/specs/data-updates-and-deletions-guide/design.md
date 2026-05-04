# Design Document

## Overview

This feature adds a dedicated guide at `senzing-bootcamp/docs/guides/DATA_UPDATES_AND_DELETIONS.md` covering record updates, record deletions, entity re-evaluation, and redo processing implications in Senzing. The guide targets bootcampers who have completed Module 6 (Load Data) and need to understand how to handle source data changes after initial loading.

Three files are affected:

1. **New file**: `senzing-bootcamp/docs/guides/DATA_UPDATES_AND_DELETIONS.md` — the guide itself
2. **Modified file**: `senzing-bootcamp/steering/module-06-load-data.md` — cross-reference to the guide as optional advanced reading
3. **Modified file**: `senzing-bootcamp/docs/guides/README.md` — index entry for the new guide

No application code is involved. All artifacts are static markdown. Code examples within the guide are placeholders that instruct the agent to call MCP tools (`generate_scaffold`, `get_sdk_reference`, `search_docs`) at runtime to produce authoritative, up-to-date SDK code.

## Architecture

### File Layout

```text
senzing-bootcamp/
├── docs/
│   └── guides/
│       ├── README.md                          # Modified — add index entry
│       └── DATA_UPDATES_AND_DELETIONS.md      # New — the guide
└── steering/
    └── module-06-load-data.md                 # Modified — add cross-reference
```

### Guide Document Structure

The guide follows the heading and layout conventions established by existing guides in the `docs/guides/` directory (level-1 heading, introductory paragraph, then sections).

```text
DATA_UPDATES_AND_DELETIONS.md
├── # Data Updates and Deletions              (L1 — title)
├── Introduction paragraph                     (why updates/deletions matter)
├── ## Updating Records                        (L2 — Requirement 2)
│   ├── Explanation of replace semantics
│   ├── Concrete scenario (address change)
│   ├── Before/after record data
│   └── Code example placeholder (generate_scaffold)
├── ## Deleting Records                        (L2 — Requirement 3)
│   ├── Explanation of delete by DATA_SOURCE + RECORD_ID
│   ├── Entity impact (shrink, split, remove)
│   ├── Concrete scenario (account closure)
│   └── Code example placeholder (generate_scaffold / get_sdk_reference)
├── ## Entity Re-evaluation After Changes      (L2 — Requirement 4)
│   ├── How Senzing recalculates entity composition
│   ├── Update vs deletion re-evaluation differences
│   ├── Verifying entity changes after operations
│   └── Code example placeholder (query method)
├── ## Redo Processing Implications            (L2 — Requirement 5)
│   ├── Why updates/deletions generate redo records
│   ├── Cascading redo records explanation
│   ├── Recommended pattern: check → process → drain
│   └── Code example placeholder (generate_scaffold redo workflow)
└── ## Further Reading                         (L2 — Requirement 6.4)
    └── Pointers to search_docs and get_sdk_reference
```

### Code Example Strategy

The guide does **not** contain hard-coded Senzing API calls. Instead, each code example section includes an agent instruction block directing the agent to call the appropriate MCP tool at render time:

- **Record update**: `generate_scaffold(language='<chosen_language>', workflow='add_records', version='current')` — since updates use the same `add_record` call with the same DATA_SOURCE + RECORD_ID
- **Record deletion**: `get_sdk_reference(topic='functions', filter='delete_record', version='current')` for the method signature
- **Entity query after change**: `generate_scaffold(language='<chosen_language>', workflow='query', version='current')` or `get_sdk_reference(topic='functions', filter='get_entity', version='current')`
- **Redo processing**: `generate_scaffold(language='<chosen_language>', workflow='redo', version='current')`

This ensures code examples always reflect the current SDK version.

### Module 6 Cross-Reference Placement

The cross-reference is added to `module-06-load-data.md` at the bottom of the file, after the Phase Sub-Files section. It is presented as optional advanced reading — not a required step in the module workflow.

Format:

```markdown
## Advanced Reading

> **After completing Module 6**, see `docs/guides/DATA_UPDATES_AND_DELETIONS.md` for guidance on record updates, deletions, entity re-evaluation, and redo processing implications — relevant for production systems where source data changes over time.
```

### Guides README Integration

Two modifications to `senzing-bootcamp/docs/guides/README.md`:

1. **Available Guides section**: Add an entry under "Reference Documentation" following the existing format (bold link, bullet list of coverage areas)
2. **Documentation Structure tree**: Add `DATA_UPDATES_AND_DELETIONS.md` under the `guides/` directory listing

## Components and Interfaces

This feature has no software components or interfaces. All artifacts are static markdown files consumed by humans (bootcampers) and the agent (MCP tool instruction blocks).

| Artifact | Type | Consumer |
| --- | --- | --- |
| `DATA_UPDATES_AND_DELETIONS.md` | User guide | Bootcampers, agent |
| Module 6 cross-reference | Steering addition | Agent |
| README index entry | Documentation index | Bootcampers |

## Data Models

No data models. All content is static markdown text.

## Error Handling

Not applicable — no application code is involved. The guide's code example placeholders rely on MCP tool availability. If the MCP server is unavailable, the agent follows the existing `mcp-offline-fallback.md` steering for graceful degradation.

## Testing Strategy

**Property-based testing does not apply to this feature.** The deliverables are static markdown files with no functions, data transformations, or logic to test. There are no inputs to vary and no outputs to assert properties over.

**Appropriate testing approach:**

- **Manual review**: Verify guide content covers all acceptance criteria sections (updates, deletions, re-evaluation, redo processing, further reading)
- **Structural validation**: Existing CI pipeline (`validate_commonmark.py`) validates markdown formatting
- **Cross-reference verification**: Confirm the Module 6 steering file contains the advanced reading reference and the guides README contains the index entry
- **MCP instruction verification**: Confirm each code example section contains the correct MCP tool call instruction rather than hard-coded Senzing API calls
