---
inclusion: always
---

# Tech Stack

**Scripts**: Python 3.11+, stdlib only (no third-party deps). Exception: `validate_dependencies.py` uses PyYAML.
**Tests**: pytest + Hypothesis for property-based testing. Tests live in `senzing-bootcamp/tests/` (power tests) and `tests/` (repo-level hook tests).
**Config**: YAML for structured data (`steering-index.yaml`, `data_sources.yaml`, `module-dependencies.yaml`, `hook-categories.yaml`). JSON for hook files (`.kiro.hook`).
**CI**: GitHub Actions (`.github/workflows/validate-power.yml`) — runs `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest.
**Steering**: Markdown with YAML frontmatter in `senzing-bootcamp/steering/`. Token budgets tracked in `steering-index.yaml`.
**MCP**: Senzing MCP server at `mcp.senzing.com` — all Senzing facts come from MCP tools, never training data.
