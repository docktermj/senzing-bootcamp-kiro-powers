---
inclusion: always
description: "Tech stack choices: Python scripts, pytest+Hypothesis, YAML/JSON configs, GitHub Actions CI, Senzing MCP"
---

# Tech Stack

**Scripts**: Python 3.11+, stdlib only (no third-party deps). Exception: `validate_dependencies.py` uses PyYAML. Optional: `fpdf2` (`import fpdf`) is a lazily-imported, optional dependency used only by the two PDF-generation scripts (`generate_recap_pdf.py`, `generate_completion_summary.py`); they degrade gracefully (keep Markdown output) when it is absent and never import it at module top level.
**Tests**: pytest + Hypothesis for property-based testing. Tests live in `senzing-bootcamp/tests/` (power tests) and `tests/` (repo-level hook tests).
**Config**: YAML for structured data (`steering-index.yaml`, `data_sources.yaml`, `module-dependencies.yaml`, `hook-categories.yaml`). JSON for hook files (`.kiro.hook`).
**CI**: GitHub Actions (`.github/workflows/validate-power.yml`) — runs `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest.
**Steering**: Markdown with YAML frontmatter in `senzing-bootcamp/steering/`. Token budgets tracked in `steering-index.yaml`.
**MCP**: Senzing MCP server at `mcp.senzing.com` — all Senzing facts come from MCP tools, never training data.
