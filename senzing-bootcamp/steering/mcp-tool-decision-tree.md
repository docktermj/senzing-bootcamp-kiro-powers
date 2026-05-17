---
inclusion: manual
---

# MCP Tool Decision Tree

This file maps common bootcamp tasks to the correct Senzing MCP tool. Use it when deciding which tool to call for a given bootcamper request. The decision tree covers all 12 MCP tools organized by task category, with anti-pattern warnings and call-pattern examples.

## Session Start

Before using any other MCP tool in a new session, call `get_capabilities` to discover available tools and confirm the MCP server is responsive. This ensures tool names and parameters are current.

## What Is the Bootcamper Trying to Do?

```text
What is the bootcamper trying to do?
├─→ Preparing or mapping data       → Data Preparation
├─→ Writing SDK code                 → SDK Development
├─→ Diagnosing errors or failures    → Troubleshooting
└─→ Looking up docs or reporting     → Reference & Reporting
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
