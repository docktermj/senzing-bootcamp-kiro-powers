# Senzing Boot Camp Templates

Templates are no longer shipped as static Python files. Instead, the boot camp generates language-specific code on the fly using the Senzing MCP server's `generate_scaffold` and `sdk_guide` tools, tailored to the bootcamper's chosen programming language.

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
