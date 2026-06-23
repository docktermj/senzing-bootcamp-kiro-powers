---
inclusion: auto
description: "Project-root file prohibitions and whitelist — load when creating or writing any project file"
---

# File Placement Reference

The always-on summary lives in `agent-instructions.md` (`## File Placement`). This file carries the project-root prohibitions and the permitted-file whitelist.

## Root Prohibitions

🚫 **NEVER place these file types in the project root:**

| Blocked Type | Reason | Correct Location |
|---|---|---|
| `.py` files | Source code belongs in `src/` or `scripts/` | `src/transform/`, `src/load/`, `src/query/`, or `scripts/` |
| `.md` files (except `README.md`) | Documentation belongs in `docs/` | `docs/` |
| `.jsonl` files | Data files belong in `data/` | `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/` |
| `.csv` files | Data files belong in `data/` | `data/raw/`, `data/transformed/`, `data/samples/`, `data/temp/` |
| Non-config `.json` files | Data payloads belong in `data/` | `data/` or `config/` |

✅ **Only these files are permitted in the project root:**
`.gitignore`, `.env`, `.env.example`, `README.md`, `requirements.txt`, `pom.xml`, `*.csproj`, `Cargo.toml`, `package.json`
