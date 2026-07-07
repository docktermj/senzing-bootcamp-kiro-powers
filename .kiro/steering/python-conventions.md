---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
description: "Python script and test conventions for the senzing-bootcamp power"
---

# Python Conventions

## Script Pattern

Every script in `senzing-bootcamp/scripts/` follows this structure:
- Shebang: `#!/usr/bin/env python3`
- Module docstring with usage examples
- `from __future__ import annotations`
- Stdlib imports only (no pip dependencies)
- Dataclasses for structured data (`@dataclass`)
- `argparse` for CLI with `main(argv=None)` signature
- `if __name__ == "__main__": main()` entry point
- Exit code 0 on success, 1 on error

## Test Pattern

- Import scripts via `sys.path` manipulation (scripts aren't packages):
  ```python
  _SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
  if _SCRIPTS_DIR not in sys.path:
      sys.path.insert(0, _SCRIPTS_DIR)
  ```
- Class-based test organization: `class TestFeatureName:`
- Hypothesis PBT: decorate properties with `@given()`. Example counts come from the active Hypothesis profile baseline — do not hand-set `@settings(max_examples=...)` to match the default. Add an inline `@settings` override only when a specific test genuinely needs a non-baseline count (see Hypothesis Profiles below).
- Strategies prefixed with `st_` (e.g., `st_hook_id()`, `st_v1_registry()`)
- Property test classes document which requirements they validate

## Hypothesis Profiles

Hypothesis example counts are centralized in registered profiles instead of being set per test. Profiles are registered once in the repo-root module `hypothesis_profiles.py` and loaded by both `conftest.py` files (`senzing-bootcamp/tests/conftest.py` and `tests/conftest.py`).

- **Registered profiles** (name → `max_examples`):
  - `fast` → 5 (local default, quick iteration)
  - `thorough` → 100 (CI and full local runs)
  - `bootcamp` → alias of `thorough` (backward compatibility)
- **Selection env var**: `HYPOTHESIS_PROFILE`
- **Default profile** (when `HYPOTHESIS_PROFILE` is unset): `fast`
- Every profile preserves the existing timing behavior: `deadline=None` and the `too_slow` health check suppressed.

### Baseline vs. overrides

- The active profile supplies the baseline `max_examples` for any property test that has no inline `@settings(max_examples=...)`.
- An inline `@settings(max_examples=...)` is an **override**: it takes precedence over the profile baseline for that test only. Use it solely when a test needs a count different from the baseline (for example, a high-value property that should run deeper).
- Do not add inline `@settings(max_examples=20)` (or `=100`, etc.) merely to restate the baseline — let the profile control it.

### Local commands

- **Default fast run** (uses the `fast` profile automatically):
  ```bash
  python -m pytest senzing-bootcamp/tests/ tests/
  ```
- **Full thorough run** (matches CI coverage):
  ```bash
  HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/
  ```

Setting `HYPOTHESIS_PROFILE` to an unrecognized value fails fast at collection time with an error naming the offending value.

## Style

- Type hints on all function signatures (use `X | None` not `Optional[X]`)
- `list[str]` not `List[str]` (lowercase generics, Python 3.11+)
- Docstrings: Google style, one-line summary + Args/Returns/Raises
- Line length: 100 chars max
- String formatting: f-strings preferred
- YAML parsing: custom minimal parsers (no PyYAML) except `validate_dependencies.py`
- Optional third-party dep: `fpdf2` (`import fpdf`) is used only by `generate_recap_pdf.py` and `generate_completion_summary.py`. Import it lazily inside the rendering function (never at module top level) and degrade gracefully when it is absent — keep the Markdown output and print a `pip install fpdf2` hint. Do not make it a hard dependency.
