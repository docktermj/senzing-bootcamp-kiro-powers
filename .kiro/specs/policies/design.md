# Design Document

## Overview

The policies feature consists of four markdown policy documents and an index page in `senzing-bootcamp/docs/policies/`. Each policy defines rules the agent follows during bootcamp execution. Policies are loaded by steering files and enforced by hooks.

## Architecture

### Policy Documents

All policies are standalone markdown files in `senzing-bootcamp/docs/policies/`. They are read by the agent at runtime via steering file references and hook prompts. No code execution is involved — policies are purely declarative documentation.

### Policy Coverage

| Policy | Governs | Audience |
|---|---|---|
| `CODE_QUALITY_STANDARDS.md` | Coding style, naming, docs, imports per language | Agent + Bootcamper |
| `FILE_STORAGE_POLICY.md` | File placement rules, directory structure | Agent + Bootcamper |
| `SENZING_INFORMATION_POLICY.md` | MCP-only sourcing for all Senzing facts | Agent |
| `DEPENDENCY_MANAGEMENT_POLICY.md` | Dependency file conventions per language | Agent |
| `README.md` | Index of all policies with summaries | Bootcamper |

### Language Coverage

Code quality and dependency policies cover five languages:

| Language | Style Guide | Dependency File | Indentation |
|---|---|---|---|
| Python | PEP-8 | `requirements.txt` | 4 spaces |
| Java | Standard conventions | `pom.xml` / `build.gradle` | 4 spaces |
| C# | .NET conventions | `*.csproj` | 4 spaces |
| Rust | rustfmt/clippy | `Cargo.toml` | 4 spaces |
| TypeScript | ESLint/Prettier | `package.json` | 2 spaces |

### File Storage Directory Map

The file storage policy defines these project-relative directories:

```
project-root/
├── src/              # Source code (transform/, load/, query/, utils/)
├── scripts/          # Python automation scripts
├── data/             # Data files (raw/, transformed/, samples/, backups/, temp/)
├── database/         # SQLite database files (G2C.db)
├── config/           # Configuration files
├── docs/             # Documentation
├── licenses/         # Senzing license files
├── backups/          # Project backup archives
└── requirements.txt  # (or language-equivalent dependency file)
```

### Enforcement Mechanisms

Policies are enforced through:
1. **Steering files** — agent instructions reference policies at runtime
2. **Hooks** — `verify-senzing-facts` (preToolUse) enforces MCP-only Senzing facts; `enforce-working-directory` (preToolUse) enforces file storage rules; `code-style-check` (fileEdited) enforces code quality standards
3. **Agent behavior** — policies define explicit Do/Don't rules the agent follows

### Senzing Information Policy Flow

```
User asks Senzing question
  → Agent reads SENZING_INFORMATION_POLICY.md
  → Agent calls MCP tool (search_docs, mapping_workflow, get_sdk_reference, etc.)
  → MCP returns authoritative answer → Agent presents to user
  → MCP returns no answer → Agent says "not found" and suggests docs.senzing.com
```

## File Structure

```
senzing-bootcamp/docs/policies/
├── README.md
├── CODE_QUALITY_STANDARDS.md
├── DEPENDENCY_MANAGEMENT_POLICY.md
├── FILE_STORAGE_POLICY.md
└── SENZING_INFORMATION_POLICY.md
```
