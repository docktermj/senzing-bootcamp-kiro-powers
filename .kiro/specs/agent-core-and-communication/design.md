# Design Document

## Overview

The agent core rules and communication patterns are implemented entirely as steering files — no application code. The primary file is `senzing-bootcamp/steering/agent-instructions.md` (inclusion: always), which contains the compact core rules loaded every session. Onboarding was split into a separate `onboarding-flow.md` file in v0.3.0 to reduce context usage. Five language-specific steering files use `fileMatch` inclusion to load automatically when the Bootcamper edits code in a supported language.

## Architecture

### Steering File Structure

```text
agent-instructions.md (inclusion: always — loaded every session)
├── File Placement table
├── MCP Rules (tool routing, skepticism, failure/retry)
├── Module Steering table (module → steering file mapping)
├── State & Progress rules
├── Communication rules (👉 markers, one-question-at-a-time, data viz offers)
└── Hooks installation reference

onboarding-flow.md (loaded manually — new Bootcampers only)
session-resume.md (loaded manually — returning Bootcampers only)
```

### Session Entry Decision

```text
Session Start
  └─ agent-instructions.md loads automatically (inclusion: always)
  └─ Check config/bootcamp_progress.json
       ├─ EXISTS → load session-resume.md
       └─ NOT EXISTS → load onboarding-flow.md
```

### Language Steering Files

| File | fileMatch Pattern | Language |
| ---- | ----------------- | -------- |
| `lang-python.md` | `*.py` | Python |
| `lang-java.md` | `*.java` | Java |
| `lang-csharp.md` | `*.cs` | C# |
| `lang-rust.md` | `*.rs` | Rust |
| `lang-typescript.md` | `*.ts` | TypeScript |

Each file provides language-specific SDK patterns, import conventions, error handling idioms, and code generation templates.

### MCP Tool Routing

| Need | MCP Tool |
| ---- | -------- |
| Attribute names / mapping | `mapping_workflow` |
| SDK code generation | `generate_scaffold` / `sdk_guide` |
| Method signatures | `get_sdk_reference` |
| Error explanations | `explain_error_code` |
| Documentation search | `search_docs` |
| Code examples | `find_examples` |
| Session init | `get_capabilities` |

MCP failure: retry once → load `common-pitfalls.md` "MCP Server Unavailable" section → never fabricate.

MCP skepticism: flag `sz_dm_report` tables, beta features, non-core SDK references.

### File Placement Layout

| Content | Location | Content | Location |
| ------- | -------- | ------- | -------- |
| Source code | `src/` | SQLite DB | `database/` |
| Scripts | `scripts/` | Config | `config/` |
| Docs | `docs/` | Temp files | `data/temp/` |
| Data | `data/` | | |

Rejected paths: `/tmp`, `%TEMP%`, `~/Downloads`. MCP-generated paths overridden to project-relative equivalents.

### Data Visualization Flow

```text
Agent presents data results
  └─ Offer: "👉 Would you like me to visualize this as a web page?"
       ├─ YES → Ask what interactive features → generate HTML → save to docs/ or data/temp/
       └─ NO → continue with text output
```

### Special Handling Rules

- **Zero matches (Module 8):** When entity resolution returns no matches, explain the outcome, suggest checking data quality, mapping accuracy, and threshold configuration.
- **SQLite ≤1,000 records (v0.8.0):** Recommend staying under 1,000 records for best bootcamp experience on SQLite.
- **AWS CDK guidance (v0.4.0):** When deploying to AWS, recommend CDK for infrastructure-as-code.

## Constraints

- No application code — all behavior is steering-file-driven.
- `agent-instructions.md` must remain compact; detailed flows belong in separate steering files.
- `get_capabilities` must be called at the start of every new session.
- All Senzing facts must come from MCP tools, never from training data.
