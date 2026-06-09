---
inclusion: manual
---

# MCP Tool Decision Tree

This file maps common bootcamp tasks to the correct Senzing MCP tool. Use it when deciding which tool to call for a given bootcamper request. The decision tree covers all 12 MCP tools organized by task category, with anti-pattern warnings and call-pattern examples. (A 13th tool, `submit_feedback`, is the disabled-by-default tool listed in `disabledTools` in `mcp.json`, so this routing covers the 12 active tools.)

## Session Start

Before using any other MCP tool in a new session, call `get_capabilities` to discover available tools and confirm the MCP server is responsive. This ensures tool names and parameters are current.

## What Is the Bootcamper Trying to Do?

```text
What is the bootcamper trying to do?
├─→ Preparing or mapping data       → Data Preparation
├─→ Writing SDK code                 → SDK Development
├─→ Diagnosing errors or failures    → Troubleshooting
├─→ Looking up docs or reporting     → Reference & Reporting
└─→ Exploring entity resolution data → Data Exploration (use SDK, never direct SQL)
```

### Data Preparation

```text
Data preparation task?
├─→ Mapping raw source data to Senzing JSON format?
│   └─→ mapping_workflow
├─→ Validating a mapped record for correctness?
│   └─→ analyze_record
├─→ Need sample datasets to practice with?
│   └─→ get_sample_data
└─→ Downloading entity spec or analyzer script?
    └─→ download_resource
```

### SDK Development

```text
SDK development task?
├─→ Need a code scaffold for a Senzing workflow?
│   └─→ generate_scaffold
├─→ Installing or configuring the SDK?
│   └─→ sdk_guide
├─→ Looking up method signatures or flags?
│   └─→ get_sdk_reference
└─→ Need working code examples?
    └─→ find_examples
```

### Troubleshooting

```text
Troubleshooting an issue?
├─→ Have a Senzing error code (SENZ####)?
│   └─→ explain_error_code
└─→ Searching for solutions or documentation?
    └─→ search_docs
```

### Reference and Reporting

```text
Reference or reporting task?
├─→ Searching Senzing documentation?
│   └─→ search_docs
├─→ Need reporting or visualization guidance?
│   └─→ reporting_guide
└─→ Discovering what tools are available?
    └─→ get_capabilities
```

### Data Exploration

```text
Exploring or querying entity resolution results?
├─→ Counting entities or getting statistics?
│   └─→ reporting_guide (NEVER direct SQL against Senzing database)
├─→ Finding duplicates or matching records?
│   └─→ search_by_attributes (NEVER SELECT from RES_ENT/OBS_ENT)
├─→ Retrieving entity details?
│   └─→ get_entity or get_entity_by_record_id (NEVER query G2C.db directly)
└─→ Exporting or visualizing resolved data?
    └─→ reporting_guide (NEVER open sqlite3 connection to Senzing database)
```

## Anti-Patterns: When NOT to Use

| Instead of | Use | Consequence of Wrong Approach |
|---|---|---|
| Hand-coding Senzing JSON mappings | `mapping_workflow` | Wrong attribute names, silent data loss |
| Guessing SDK method names or signatures | `generate_scaffold` or `sdk_guide` | Non-existent methods, wrong parameters, runtime errors |
| Relying on training data for SDK method signatures and flags | `get_sdk_reference` | Outdated or incorrect signatures, missing flags |
| Recommending integration approaches without checking | `search_docs` with `category='anti_patterns'` | Recommending deprecated or harmful patterns |
| Guessing Senzing error code meanings | `explain_error_code` | Misdiagnosis, wrong fix applied |
| Fabricating sample datasets | `get_sample_data` | Invalid record structures, wrong attribute names |
| Passing None/default flags without checking | `get_sdk_reference(topic='flags')` | Missing detail needed for visualizations, no teaching moment about flag system |
| Writing direct SQL against the Senzing database | Use SDK methods via MCP tools (`get_entity`, `search_by_attributes`, `reporting_guide`) | Bypasses SDK abstraction, produces non-portable results, may return incorrect data from internal tables |

## Call Pattern Examples

### get_capabilities

```json
{ "tool": "get_capabilities" }
```

Session start — discover available tools and confirm MCP server is responsive.

### mapping_workflow

```json
{ "tool": "mapping_workflow", "source_file": "data/customers.csv", "data_source": "CUSTOMERS" }
```

Map raw CSV/JSON data to Senzing format. Optional: pass `state` from a previous checkpoint to resume.

### generate_scaffold

```json
{ "tool": "generate_scaffold", "workflow": "add_records", "language": "python" }
```

Generate a working code scaffold for a Senzing workflow. Optional: `database_type` for non-SQLite setups.

### get_sample_data

```json
{ "tool": "get_sample_data", "format": "senzing_json" }
```

Get sample datasets for practice. Optional: `record_count` to control dataset size.

### search_docs

```json
{ "tool": "search_docs", "query": "batch loading best practices" }
```

Search Senzing documentation. Optional: `category` (e.g., `"anti_patterns"`, `"performance"`, `"installation"`).

### explain_error_code

```json
{ "tool": "explain_error_code", "error_code": "SENZ7007" }
```

Diagnose a Senzing error code — get meaning, common causes, and fix steps.

### analyze_record

```json
{ "tool": "analyze_record", "record": "{\"DATA_SOURCE\":\"TEST\",\"RECORD_ID\":\"1\",\"NAME_FULL\":\"John Smith\"}" }
```

Validate a mapped record for correctness and attribute coverage.

### sdk_guide

```json
{ "tool": "sdk_guide", "topic": "installation", "language": "python" }
```

Get SDK installation, configuration, or usage guidance for a specific language.

### find_examples

```json
{ "tool": "find_examples", "topic": "entity_search", "language": "python" }
```

Find working code examples for a specific SDK operation.

### get_sdk_reference

```json
{ "tool": "get_sdk_reference", "method": "add_record", "language": "python" }
```

Look up exact method signatures, parameters, and flags. Optional: `topic` for flag groups (e.g., `"flags"`).

### reporting_guide

```json
{ "tool": "reporting_guide", "topic": "entity_summary" }
```

Get guidance on reporting, visualization, or result presentation.

### download_resource

```json
{ "tool": "download_resource", "resource": "entity_spec" }
```

Download the entity spec, analyzer script, or other workflow resources.

## Flag Selection Protocol

Before any SDK method call that accepts a `flags` parameter, follow this protocol:

1. **Discover** — Look up available flags:
   `get_sdk_reference(method='<method_name>', topic='flags')`
2. **Select** — Choose flags matching the bootcamper's intent:
   - High-level overview → default flags
   - Scoring / explanation → `SZ_INCLUDE_FEATURE_SCORES`
   - Match key breakdown → `SZ_INCLUDE_MATCH_KEY_DETAILS`
   - Visualization → both `SZ_INCLUDE_FEATURE_SCORES` and `SZ_INCLUDE_MATCH_KEY_DETAILS`
3. **Explain** — Tell the bootcamper which flags you chose and why in one sentence
4. **Cache** — Reuse flag knowledge within the same module session without re-querying

### When to Skip Flag Lookup

- Bootcamper explicitly specifies flags
- Method has no flags parameter
- Flags already looked up for this method during the current module session

## Method Discovery Protocol

Before selecting an SDK method when the bootcamper's request is ambiguous (could map to multiple methods in the same category), follow this protocol:

1. **Detect** — Recognize when the bootcamper's request is ambiguous and could map to multiple SDK methods in the same category (e.g., "explain why entity 74 resolved" could use `how_entity`, `why_entities`, `why_records`, or `why_record_in_entity`)
2. **Discover** — Call `get_sdk_reference(topic='functions', filter='<category>')` to enumerate available methods in the relevant category
3. **Disambiguate** — If multiple methods match, present a 👉 numbered choice list with one-line descriptions so the bootcamper can select the appropriate method
4. **Proceed** — Use the bootcamper's chosen method (or the single matching method if unambiguous)
5. **Cache** — Remember discovered methods for the rest of the module session; do not re-query for the same category

### When to Skip Method Discovery

- Bootcamper explicitly specifies a method name (e.g., "use why_records on records A and B")
- Request maps to exactly one method with no alternatives in the category
- Methods for this category already discovered during the current module session

### Examples

**Ambiguous** — "explain why entity 74 resolved"

The request could map to `how_entity`, `why_entities`, `why_records`, or `why_record_in_entity`. Discover the why/how category, then present choices:

```text
👉 Which level of detail do you want?
1. how_entity — shows how a single entity was constructed from its records
2. why_entities — explains why two entities resolved together
3. why_records — explains why two specific records resolved together
4. why_record_in_entity — explains why a specific record belongs to an entity
```

**Unambiguous** — "get entity 42 by record ID"

Only `get_entity_by_record_id` matches this request. Proceed directly without presenting choices.

**Explicit** — "use why_records on records A and B"

The bootcamper named the method explicitly. Proceed directly with `why_records`.
