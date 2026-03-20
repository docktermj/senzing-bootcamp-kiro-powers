# Senzing — Steering Guide

This document provides detailed guidance for the Senzing power. The agent loads this on-demand when users engage with Senzing activities.

## MCP Tool Catalog

Always call `get_capabilities` first to discover available tools and workflows.

| Tool | Purpose | When to Use |
| --- | --- | --- |
| `get_capabilities` | Discover all tools and workflows | First call in any Senzing session |
| `mapping_workflow` | 7-step interactive data mapping to Senzing JSON | Mapping source data to Senzing format |
| `lint_record` | Validate mapped records | After creating or editing mapped JSON |
| `analyze_record` | Analyze mapped data quality | After mapping, before loading |
| `generate_scaffold` | Generate SDK code (Python, Java, C#, Rust) | Creating loader, query, or pipeline code |
| `sdk_guide` | Platform-specific SDK installation and setup | Installing Senzing, setting up pipelines |
| `get_sample_data` | Sample datasets (Las Vegas, London, Moscow) | Testing and learning |
| `find_examples` | Working code from 27 Senzing GitHub repos | Looking for real-world patterns |
| `search_docs` | Search indexed Senzing documentation | Any Senzing question |
| `explain_error_code` | Diagnose Senzing errors (456 codes) | When errors occur |
| `get_sdk_reference` | SDK method signatures and flags | Checking method names, parameters, flags |
| `download_resource` | Download SDK packages and resources | Installing SDK components |
| `submit_feedback` | Submit feedback about the MCP server | Reporting issues or suggestions |

**Key principle**: Tools like `mapping_workflow`, `generate_scaffold`, and `sdk_guide` produce validated, version-correct output. Always prefer them over hand-coding.

## Best Practices and Anti-Patterns

### Always Do

- Call `get_capabilities` at the start of any Senzing session
- Use `mapping_workflow` for all data mapping — never hand-code Senzing JSON attribute names
- Use `generate_scaffold` or `sdk_guide` for SDK code — never guess method signatures
- Use `search_docs` with category `anti_patterns` before recommending installation, architecture, or deployment approaches
- Use `lint_record` to validate records before loading
- Start with SQLite for evaluation; recommend PostgreSQL for production
- Test with sample data (via `get_sample_data`) before working with real data
- Back up the database before any loading operation
- Test loads with a small batch (100 records) before running full loads

### Never Do

- Hand-code Senzing attribute names from memory (they are frequently wrong)
- Guess SDK method signatures (method names differ across versions)
- Skip the `DATA_SOURCE` or `RECORD_ID` fields in mapped records
- Use SQLite for production workloads (it doesn't scale past ~100K records)
- Load data without validating with `lint_record` first
- Ignore error codes — always investigate with `explain_error_code`

## Common Pitfalls

### Wrong Attribute Names

The most common mistake is guessing Senzing attribute names. Examples of frequently incorrect names:

| Wrong | Correct |
| --- | --- |
| `BUSINESS_NAME_ORG` | `NAME_ORG` |
| `EMPLOYER_NAME` | `NAME_ORG` |
| `PHONE` | `PHONE_NUMBER` |
| `EMAIL` | `EMAIL_ADDRESS` |
| `SSN` | `SSN_NUMBER` |

**Fix**: Always use `mapping_workflow` — it returns validated attribute names.

### Wrong SDK Method Names

SDK method names differ across versions and languages. Common mistakes:

| Wrong | Correct |
| --- | --- |
| `close_export` | `close_export_report` |
| `init` | `initialize` |
| `whyEntityByEntityID` | `why_entities` (V4) |

**Fix**: Always use `generate_scaffold` or `get_sdk_reference` for method signatures.

### Missing Required Fields

Every Senzing record MUST have:

- `DATA_SOURCE` — unique identifier for the data source
- `RECORD_ID` — unique within the data source

Records without these fields will fail to load.

### Lost Mapping Workflow State

When using `mapping_workflow`, always pass the exact `state` JSON from the previous response to the next call. Losing or modifying the state object causes errors.

### Missing Environment Configuration

SDK initialization fails without proper configuration. The `SENZING_ENGINE_CONFIGURATION_JSON` environment variable (or equivalent configuration) must be set. Use `sdk_guide` with the correct platform parameter for exact setup steps.

## Troubleshooting

| Symptom | Tool to Use | Details |
| --- | --- | --- |
| Wrong attribute names in mapped data | `mapping_workflow` | Re-map using the interactive workflow |
| SDK method not found or wrong signature | `generate_scaffold` or `get_sdk_reference` | Get validated method signatures |
| Senzing error code (e.g., SENZ0005) | `explain_error_code` | Accepts `SENZ0005`, `0005`, or `5` |
| Configuration or database issues | `search_docs` | Use category `configuration` or `database` |
| Installation problems | `sdk_guide` | Specify your platform for correct steps |
| Anti-pattern concerns | `search_docs` | Use category `anti_patterns` |
| Understanding why records matched | `get_sdk_reference` | Look up `why_entities` method and flags |
| Need working code examples | `find_examples` | Search 27 Senzing GitHub repositories |

## Entity Resolution Design Patterns

Common business problems that Senzing entity resolution addresses:

| Pattern | Use Case | Key Matching Criteria |
| --- | --- | --- |
| Customer 360 | Unified customer view across systems | Names, emails, phones, addresses |
| Fraud Detection | Identify fraud rings and suspicious networks | Names, addresses, devices, IPs |
| Data Migration | Merge and deduplicate during system consolidation | All available identifiers |
| Compliance Screening | Watchlist and sanctions matching | Names, DOB, nationalities, IDs |
| Marketing Dedup | Eliminate duplicate contacts | Names, addresses, emails |
| Patient Matching | Unified medical records across providers | Names, DOB, SSN, MRNs |
| Vendor MDM | Clean vendor/supplier master data | Company names, tax IDs, addresses |
| Claims Fraud | Detect staged accidents and fraud rings | Names, vehicles, providers |
| KYC/Onboarding | Verify identity during account opening | Names, DOB, SSN, government IDs |
| Supply Chain | Unified supplier view across divisions | Company names, GLNs, tax IDs |

When a user describes their problem, help them identify which pattern best fits their situation. This sets realistic expectations for matching criteria, data sources, and outcomes.
