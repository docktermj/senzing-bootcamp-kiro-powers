---
inclusion: auto
description: "Project directory layout and naming conventions"
---

# Project Structure

```text
senzing-bootcamp/           # Distributed power root
├── POWER.md / mcp.json     # Power config (root level)
├── CHANGELOG.md
├── config/                 # Machine-readable configs
├── docs/
│   ├── modules/            # MODULE_N_*.md companion docs
│   ├── guides/             # GLOSSARY, FAQ, QUICK_START, etc.
│   ├── feedback/           # Feedback templates
│   ├── policies/           # Agent policies (CODE_QUALITY_STANDARDS)
│   └── diagrams/           # Architecture and flow diagrams
├── hooks/                  # .kiro.hook JSON files + hook-categories.yaml
├── scripts/                # Python CLI tools (stdlib only)
├── steering/               # Agent steering files + steering-index.yaml
├── templates/              # User templates (checklists, lineage, UAT)
└── tests/                  # pytest + Hypothesis test suites
tests/                      # Repo-level tests (hook prompt validation)
.github/workflows/          # CI pipeline
.kiro/specs/                # Spec-driven development artifacts
```

## File Placement

| Content Type | Location | Audience |
|---|---|---|
| Module docs | `docs/modules/` | Users |
| User guides | `docs/guides/` | Users |
| Feedback templates | `docs/feedback/` | Users |
| Agent steering | `steering/` | Agents |
| Agent policies | `docs/policies/` | Agents |
| Code templates | `templates/` | Users |
| Hooks | `hooks/` | Agents |
| Scripts | `scripts/` | Both |
| Tests (power) | `tests/` | Developers |
| Power config | root (`POWER.md`, `mcp.json`) | Framework |

All paths above are relative to `senzing-bootcamp/`.

## Naming Conventions

- Scripts: `snake_case.py` with `main()` entry point and argparse CLI
- Steering files: `kebab-case.md` with YAML frontmatter
- Module steering: `module-NN-description.md` (zero-padded two digits)
- Hook files: `hook-id.kiro.hook` (matches registry ID)
- Tests: `test_feature_name.py` with class-based organization
- Configs: `kebab-case.yaml` or `snake_case.yaml`

## Rules

- Never place dev notes, build artifacts, or historical files in the repo — use git history.
- Power config files (`POWER.md`, `mcp.json`, `icon.png`) stay at `senzing-bootcamp/` root.
- Hook tests validating real hook files go in repo-root `tests/`, not `senzing-bootcamp/tests/`.
