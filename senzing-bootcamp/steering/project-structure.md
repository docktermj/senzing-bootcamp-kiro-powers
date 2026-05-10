---
inclusion: auto
---

# Project Directory Structure

```text
my-senzing-project/
├── data/{raw,transformed,samples,backups,temp}
├── database/G2C.db
├── licenses/
├── src/{quickstart_demo,transform,load,query,utils}
├── scripts/
├── tests/
├── backups/
├── docs/feedback/
├── config/{bootcamp_preferences.yaml,bootcamp_progress.json}
├── logs/
├── monitoring/
└── README.md
```

## Rules

- All source code in `src/`, never project root
- SQLite DB at `database/G2C.db` — never `/tmp/` or system-wide
- Dependency file in project root (requirements.txt, pom.xml, .csproj, Cargo.toml, package.json)
- See `docs/policies/FILE_STORAGE_POLICY.md` for complete policy
- All Markdown documentation files (`*.md`) belong in `docs/` or a subdirectory of `docs/`. The `scripts/` directory is reserved for executable code only — no `.md` files.

## Create Structure (execute before any other action)

Detect the operating system first. Use the platform-specific command below that matches the detected OS.

### Preferred (all platforms)

```python
import os
for d in [
    "data/raw", "data/transformed", "data/samples", "data/backups", "data/temp",
    "database", "licenses", "src/transform", "src/load", "src/query", "src/utils",
    "tests", "backups", "docs/feedback", "config", "logs", "monitoring", "scripts",
]:
    os.makedirs(d, exist_ok=True)
```

### On Linux / macOS

Linux/macOS: `mkdir -p data/{raw,transformed,samples,backups,temp} database licenses src/{transform,load,query,utils} tests backups docs/feedback config logs monitoring scripts`

### On Windows (PowerShell)

`'data/raw','data/transformed','data/samples','data/backups','data/temp','database','licenses','src/transform','src/load','src/query','src/utils','tests','backups','docs/feedback','config','logs','monitoring','scripts' | ForEach-Object { New-Item -ItemType Directory -Force -Path $_ | Out-Null }`

NEVER use `mkdir path1 path2 path3` on Windows — PowerShell's mkdir does not accept multiple positional arguments.

Also create: `.gitignore`, `.env.example`, `README.md`
