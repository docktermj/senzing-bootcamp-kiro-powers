---
inclusion: auto
description: "Project directory layout and naming conventions"
---

# Project Structure

```text
senzing-bootcamp/           # The distributed power (everything lives here)
├── POWER.md                # Power manifest and documentation
├── mcp.json                # MCP server config
├── CHANGELOG.md            # Version history
├── config/                 # Machine-readable configs (module-dependencies.yaml)
├── docs/                   # User-facing documentation
│   ├── modules/            # MODULE_N_*.md companion docs
│   ├── guides/             # GLOSSARY, FAQ, QUICK_START, etc.
│   ├── feedback/           # Feedback templates
│   ├── policies/           # Agent policies (CODE_QUALITY_STANDARDS, etc.)
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

## Naming Conventions

- Scripts: `snake_case.py` with `main()` entry point and argparse CLI
- Steering files: `kebab-case.md` with YAML frontmatter
- Module steering: `module-NN-description.md` (zero-padded two digits)
- Hook files: `hook-id.kiro.hook` (matches registry ID)
- Tests: `test_feature_name.py` with class-based organization
- Configs: `kebab-case.yaml` or `snake_case.yaml`
