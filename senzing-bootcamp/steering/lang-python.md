---
inclusion: conditional
fileMatchPattern: "**/*.py"
---

# Python Standards

- PEP-8, max 100 chars/line, 4-space indent
- `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants
- Triple-quote docstrings on all functions and classes
- Imports: stdlib → third-party → local, one per line, alphabetical
- Use `python3` on Linux/macOS, `python` on Windows
- Senzing Python SDK is Linux-only — macOS/Windows need Docker or WSL2
- Validate with: `pycodestyle`, `flake8`, `black`, `mypy`
