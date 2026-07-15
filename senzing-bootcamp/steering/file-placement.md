---
inclusion: fileMatch
fileMatchPattern: "**/*"
description: "Project-root file prohibitions and whitelist — load when creating or writing any project file"
---

# File Placement Reference

The always-on summary lives in `agent-instructions.md` (`## File Placement`). This file carries the project-root prohibitions and the permitted-file whitelist.

## Canonical File-Placement Contract

The authoritative artifact→location map. Apply from the start of each module and reapply after session compaction.

| Artifact | Canonical location |
|---|---|
| Transformation / mapper code | `src/transform/` |
| Downloaded Senzing resources (from `mcp.senzing.com/resources`) | `src/resources/` |
| Mapping-phase Markdown (profile reports, schema hints, journals, mapper specs, quality reports) | `docs/mapping/` |
| Mapping working data / metadata (`*_mapping_spec.json`, `{source}_sample.jsonl`, intermediate analyzer output) | `data/mapping/` |
| Final transformed, load-ready JSONL (the durable deliverable Module 6 loads) | `data/transformed/` |
| Stakeholder summary | `docs/stakeholder_summary.md` (matches `templates/stakeholder_summary.md`, no module suffix) |

## Root Prohibitions

🚫 **NEVER place these file types in the project root:**

| Blocked Type | Reason | Correct Location |
|---|---|---|
| `.py` files | Source code belongs in `src/` | `src/transform/`, `src/load/`, `src/query/`, `src/scripts/`, or `src/resources/` (downloaded Senzing tooling) |
| `.md` files (except `README.md`) | Documentation belongs in `docs/` | `docs/` |
| `.jsonl` files | Data files belong in `data/` | `data/raw/`, `data/transformed/`, `data/mapping/`, `data/samples/`, `data/temp/` |
| `.csv` files | Data files belong in `data/` | `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/` |
| Non-config `.json` files | Data payloads belong in `data/` | `data/` or `config/` |

✅ **Only these files are permitted in the project root:**
`.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`
