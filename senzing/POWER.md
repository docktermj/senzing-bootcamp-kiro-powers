---
name: "senzing"
displayName: "Senzing"
version: "0.1.0"
description: "Senzing entity resolution. Covers data mapping, SDK setup, loading, performance testing, security hardening, monitoring, and production deployment."
keywords: ["Senzing", "Entity Resolution", "Data Mapping", "SDK", "Identity Resolution", "Data Matching", "ER", "Performance", "Security", "Monitoring", "Deployment"]
author: "Senzing"
senzing_compatibility: ["4.0"]
last_updated: "2026-03-17"
---

# Power: Senzing

## License and support

This power integrates with senzing-mcp-server (Apache-2.0).

- [Privacy Policy](https://mcp.senzing.com/privacy)
- [Support](https://senzing.zendesk.com/hc/en-us/requests/new)

## Available MCP Tools

The Senzing MCP server provides these tools:

- `get_capabilities` — Discover all tools and workflows (call this first)
- `mapping_workflow` — 7-step interactive data mapping to Senzing JSON
- `lint_record` / `analyze_record` — Validate and analyze mapped data quality
- `generate_scaffold` — Generate SDK code (Python, Java, C#, Rust)
- `sdk_guide` — Platform-specific SDK installation and setup
- `get_sample_data` — Sample datasets for testing
- `find_examples` — Working code from 27 Senzing GitHub repos
- `search_docs` — Search indexed Senzing documentation
- `explain_error_code` — Diagnose Senzing errors (456 codes)
- `get_sdk_reference` — SDK method signatures and flags
- `download_resource` — Download SDK packages
- `submit_feedback` — Report issues or suggestions

## Best Practices

- Always call `get_capabilities` first when starting a Senzing session
- Never hand-code Senzing JSON mappings — use `mapping_workflow` for validated attribute names
- Never guess SDK method signatures — use `generate_scaffold` or `sdk_guide`
- Check `search_docs` with category `anti_patterns` before recommending installation or deployment approaches
- Start with SQLite for evaluation; recommend PostgreSQL for production

## Troubleshooting

- **Wrong attribute names**: Never guess Senzing attribute names (e.g., `NAME_ORG` not `BUSINESS_NAME_ORG`). Use `mapping_workflow`.
- **Wrong method signatures**: Never guess SDK methods. Use `generate_scaffold` or `get_sdk_reference`.
- **Error codes**: Use `explain_error_code` with the code (accepts `SENZ0005`, `0005`, or `5`).
- **Configuration issues**: Use `search_docs` with category `configuration` or `database`.

## Detailed Guidance

See [steering/steering.md](steering/steering.md) for detailed workflows covering MCP tool usage, common pitfalls, entity resolution design patterns, and troubleshooting.
