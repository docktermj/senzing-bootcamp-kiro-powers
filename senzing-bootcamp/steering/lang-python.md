---
inclusion: conditional
fileMatchPattern: "**/*.py"
---

# Python Standards

- PEP-8, max 100 chars/line, 4-space indent
- `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants
- Triple-quote docstrings on all functions and classes
- Imports: stdlib → third-party → local, one per line, alphabetical
- Use `python3` on Linux, `python` on Windows
- Platform support for Python is determined by the Senzing MCP server — relay any warnings it provides about the user's platform
- Validate with: `pycodestyle`, `flake8`, `black`, `mypy`
