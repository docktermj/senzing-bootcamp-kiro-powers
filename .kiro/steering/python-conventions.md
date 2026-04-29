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
- Hypothesis PBT: `@given()` with `@settings(max_examples=100)`
- Strategies prefixed with `st_` (e.g., `st_hook_id()`, `st_v1_registry()`)
- Property test classes document which requirements they validate

## Style

- Type hints on all function signatures (use `X | None` not `Optional[X]`)
- `list[str]` not `List[str]` (lowercase generics, Python 3.11+)
- Docstrings: Google style, one-line summary + Args/Returns/Raises
- Line length: 100 chars max
- String formatting: f-strings preferred
- YAML parsing: custom minimal parsers (no PyYAML) except `validate_dependencies.py`
