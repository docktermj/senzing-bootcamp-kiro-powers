# Senzing Bootcamp Templates

Templates are no longer shipped as static Python files. Instead, the bootcamp generates language-specific code on the fly using the Senzing MCP server's `generate_scaffold` and `sdk_guide` tools, tailored to the bootcamper's chosen programming language.

## Supported Languages

- Python
- Java
- C#
- Rust
- TypeScript / Node.js

## What Gets Generated

During the bootcamp, the MCP server produces current, version-correct code for whichever language the bootcamper selects. The types of code generated include:

- **Transformation programs** — data mapping and conversion via `mapping_workflow`
- **Loading programs** — record ingestion with batch processing and error handling
- **Query programs** — entity search, get-entity, why-entity, and export patterns
- **Demo scripts** — quick-start demonstrations of entity resolution
- **Backup/restore utilities** — database backup, restore, and rollback helpers
- **Performance tests** — baseline benchmarks and load-testing scaffolds
- **SDK initialization** — engine configuration and startup boilerplate
- **Redo processing** — deferred-resolution and redo-record handlers
- **Configuration management** — data source registration and config updates
- **Troubleshooting utilities** — diagnostic and validation helpers

## How Code Is Generated

### `generate_scaffold`

Produces complete, runnable code for a specific workflow:

```text
generate_scaffold(language="python", workflow="add_records", version="current")
generate_scaffold(language="java",   workflow="full_pipeline", version="current")
generate_scaffold(language="csharp", workflow="initialize",   version="current")
```

Available workflows: `initialize`, `configure`, `add_records`, `delete`, `query`, `redo`, `stewardship`, `information`, `error_handling`, `full_pipeline`.

### `sdk_guide`

Provides platform-specific install commands, configuration code, and loading templates:

```text
sdk_guide(topic="load",      language="python", platform="linux_apt")
sdk_guide(topic="configure", language="rust",   platform="macos_arm")
```

### `mapping_workflow`

Interactive data-mapping workflow that profiles source files and generates transformation code:

```text
mapping_workflow(action="start", file_paths=["data/raw/customers.csv"])
```

## Why Dynamic Generation

- Code is always current with the latest Senzing SDK version
- No stale templates to maintain or version-lock
- Bootcampers work in their preferred language from day one
- Generated code follows current Senzing best practices and correct method names
- Automatically adapts when the SDK introduces breaking changes

## Creating Your Own Reusable Templates

As you work through the bootcamp, the agent generates code tailored to your data. To turn that generated code into reusable templates for future projects:

1. **After Module 5** — your transformation programs in `src/transform/` are already templates. Copy them to a new project and change the field mappings for different data sources.
2. **After Module 6** — your loading programs in `src/load/` work for any JSONL file. The only thing that changes between projects is the file path and DATA_SOURCE name.
3. **After Module 8** — your query programs in `src/query/` are reusable patterns. The search attributes change, but the structure stays the same.

To save a template for reuse:

```text
# Copy a working program to a templates directory in your own project
mkdir -p my-templates/
cp src/transform/transform_customers.[ext] my-templates/transform_template.[ext]
cp src/load/load_customers.[ext] my-templates/load_template.[ext]
cp src/query/find_duplicates.[ext] my-templates/query_template.[ext]
```

Then for your next project, copy the template and customize the data-specific parts (file paths, field mappings, DATA_SOURCE names).
