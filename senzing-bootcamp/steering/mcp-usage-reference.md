---
inclusion: manual
---

# MCP Usage Reference

Detailed MCP tool usage patterns, SDK method discovery flow, and SQL redirect rules. Loaded on demand from `agent-instructions.md`.

## SDK Flags

SDK method calls that accept flags: look up available flags via `get_sdk_reference(topic='flags')`, select flags matching the bootcamper's intent, and explain the choice in one sentence. Reuse flag knowledge within a module session. Default flags are acceptable for simple lookups but note that detailed flags exist.

## Tool Selection

Uncertain which tool? Load `mcp-tool-decision-tree.md` for the full decision tree with anti-patterns and call examples.

Third-party software: consult Senzing MCP (`search_docs`) before recommending tools in a Senzing integration context.

MCP skepticism: flag data mart tables (`sz_dm_report`), beta features, or non-core SDK references.

## SQL Redirect Rules

Never generate direct SQL (SELECT, INSERT, UPDATE, DELETE) against the Senzing database (`database/G2C.db`) or its internal tables (RES_ENT, OBS_ENT, DSRC_RECORD, LIB_FEAT, RES_FEAT_STAT, RES_REL, etc.).

| Bootcamper Request | Redirect To |
|---|---|
| "count entities" | `reporting_guide` |
| "find duplicates" | `search_by_attributes` |
| "show entity details" | `get_entity` / `get_entity_by_record_id` |
| "why did these match" | `why_entities` / `why_records` |
| "how was entity built" | `how_entity` |
| "export entity data" | iterate SDK methods via MCP tools |

## SDK Method Discovery

When the bootcamper's request could map to multiple SDK methods in the same category:

1. **Trigger**: Request is ambiguous — multiple methods in a category could satisfy it.
2. **Discover**: Call `get_sdk_reference` with a category/topic filter.
3. **Disambiguate**: Multiple matches → ask a single 👉 question with numbered choice list.
4. **Proceed**: Single match → proceed directly, noting alternatives.

**Categories with multiple alternatives:**

- **Why/How**: `how_entity`, `why_entities`, `why_records`, `why_record_in_entity`
- **Entity retrieval**: `get_entity`, `get_entity_by_record_id`
- **Search**: `search_by_attributes`, `search_by_record_id`

**Skip discovery when:**

- Bootcamper explicitly names a method
- Request unambiguously maps to one method
- Methods already discovered in current module session
