# PEP-8 Compliance Guide

**Date**: 2026-03-17
**Status**: All scripts compliant

## Overview

All Python scripts in the Senzing Boot Camp power follow PEP-8 coding standards for consistency, readability, and maintainability.

## Compliance Status

✅ **All 14 Python scripts are PEP-8 compliant**

### Demo Scripts (3)
- ✓ `src/quickstart_demo/demo_customer_360.py`
- ✓ `src/quickstart_demo/demo_fraud_detection.py`
- ✓ `src/quickstart_demo/demo_vendor_mdm.py`

### Template Scripts (11)
- ✓ `templates/validate_schema.py`
- ✓ `templates/collect_from_csv.py`
- ✓ `templates/collect_from_json.py`
- ✓ `templates/collect_from_api.py`
- ✓ `templates/collect_from_database.py`
- ✓ `templates/backup_database.py`
- ✓ `templates/restore_database.py`
- ✓ `templates/rollback_load.py`
- ✓ `templates/cost_calculator.py`
- ✓ `templates/performance_baseline.py`
- ✓ `templates/troubleshoot.py`

## PEP-8 Standards Applied

### Line Length
- **Maximum**: 100 characters per line
- **Rationale**: More readable than strict 79, accommodates modern displays
- **Breaking long lines**: Use parentheses, not backslashes

### Whitespace
- **No trailing whitespace** on any line
- **Two blank lines** between top-level functions and classes
- **One blank line** between methods in a class
- **One space** after commas in lists, tuples, and function arguments
- **No spaces** around = in keyword arguments

### Indentation
- **4 spaces** for indentation (never tabs)
- Consistent indentation throughout

### Naming Conventions
- `snake_case` for functions, variables, and module names
- `PascalCase` for class names
- `UPPER_CASE` for constants
- Descriptive names (avoid single letters except in loops)

### Imports
- All imports at top of file
- Grouped: standard library, third-party, local
- One import per line (except `from x import a, b`)
- Alphabetical order within groups

### Documentation
- Module docstring at top of file
- Docstring for every function and class
- Triple quotes for docstrings
- Include purpose, parameters, and return values

## Example: PEP-8 Compliant Code

```python
#!/usr/bin/env python3
"""
Module for transforming customer data to Senzing format.

This module provides functions to read CSV files and transform
them into Senzing JSON format.
"""

import json
import sys
from pathlib import Path

# Constants
DATA_SOURCE = "CUSTOMERS"
MAX_RECORDS = 10000


def transform_record(source_record):
    """
    Transform a source record to Senzing JSON format.

    Args:
        source_record (dict): Source data record

    Returns:
        dict: Senzing-formatted record
    """
    return {
        "DATA_SOURCE": DATA_SOURCE,
        "RECORD_ID": source_record.get("id"),
        "NAME_FULL": source_record.get("name"),
        "EMAIL_ADDRESS": source_record.get("email")
    }


def main():
    """Main entry point."""
    # Implementation here
    pass


if __name__ == "__main__":
    sys.exit(main())
```

## Validation Tools

### Recommended Tools

1. **pycodestyle** (formerly pep8)
   ```bash
   pip install pycodestyle
   pycodestyle --max-line-length=100 src/
   ```

2. **flake8** (combines pycodestyle, pyflakes, mccabe)
   ```bash
   pip install flake8
   flake8 --max-line-length=100 src/
   ```

3. **black** (automatic formatter)
   ```bash
   pip install black
   black --line-length=100 src/
   ```

4. **pylint** (comprehensive code quality)
   ```bash
   pip install pylint
   pylint src/
   ```

5. **mypy** (type checking)
   ```bash
   pip install mypy
   mypy src/
   ```

### Quick Validation Script

```bash
#!/bin/bash
# validate_pep8.sh

echo "Checking PEP-8 compliance..."

# Check with pycodestyle
if command -v pycodestyle &> /dev/null; then
    pycodestyle --max-line-length=100 src/ templates/
    if [ $? -eq 0 ]; then
        echo "✅ PEP-8 compliant"
    else
        echo "❌ PEP-8 violations found"
        exit 1
    fi
else
    echo "⚠️  pycodestyle not installed"
    echo "Install with: pip install pycodestyle"
    exit 1
fi
```

## Common PEP-8 Issues and Fixes

### Issue 1: Line Too Long

**Problem**:
```python
result = some_function(arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8)
```

**Fix**:
```python
result = some_function(
    arg1, arg2, arg3, arg4,
    arg5, arg6, arg7, arg8
)
```

### Issue 2: Trailing Whitespace

**Problem**:
```python
def my_function():  
    return True  
```

**Fix**:
```python
def my_function():
    return True
```

### Issue 3: Inconsistent Indentation

**Problem**:
```python
def my_function():
  return True  # 2 spaces
```

**Fix**:
```python
def my_function():
    return True  # 4 spaces
```

### Issue 4: Missing Docstrings

**Problem**:
```python
def transform_record(record):
    return {"DATA_SOURCE": "TEST"}
```

**Fix**:
```python
def transform_record(record):
    """Transform a record to Senzing format."""
    return {"DATA_SOURCE": "TEST"}
```

### Issue 5: Import Organization

**Problem**:
```python
from pathlib import Path
import sys
import json
import pandas as pd
from senzing import G2Engine
```

**Fix**:
```python
# Standard library
import json
import sys
from pathlib import Path

# Third-party
import pandas as pd

# Local
from senzing import G2Engine
```

## Agent Behavior

When generating Python code, the agent will:

1. **Always generate PEP-8 compliant code** from the start
2. **Use proper indentation** (4 spaces)
3. **Add docstrings** to all functions and classes
4. **Keep lines under 100 characters**
5. **Remove trailing whitespace**
6. **Use proper naming conventions**
7. **Organize imports** correctly

When users provide code, the agent will:

1. **Check for PEP-8 compliance**
2. **Suggest fixes** if non-compliant
3. **Explain why compliance matters**
4. **Offer to fix issues** automatically

## Benefits of PEP-8 Compliance

### Readability
- Consistent style across all code
- Easier to understand and maintain
- Faster code reviews

### Maintainability
- Easier to modify and extend
- Reduces cognitive load
- Fewer bugs from formatting issues

### Collaboration
- Team members can read each other's code
- Consistent expectations
- Professional appearance

### Tool Support
- Better IDE support
- Automatic formatting
- Static analysis tools work better

## Continuous Compliance

### Pre-commit Hooks

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pycodestyle --max-line-length=100 src/ templates/
if [ $? -ne 0 ]; then
    echo "❌ PEP-8 violations found. Commit aborted."
    exit 1
fi
```

### CI/CD Integration

Add to CI/CD pipeline:
```yaml
# .github/workflows/lint.yml
name: Lint
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: pip install pycodestyle
      - name: Check PEP-8
        run: pycodestyle --max-line-length=100 src/ templates/
```

### IDE Configuration

**VS Code** (`.vscode/settings.json`):
```json
{
    "python.linting.enabled": true,
    "python.linting.pycodestyleEnabled": true,
    "python.linting.pycodestyleArgs": ["--max-line-length=100"],
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=100"],
    "editor.formatOnSave": true
}
```

**PyCharm**:
- Settings → Editor → Code Style → Python
- Set "Hard wrap at" to 100
- Enable "Reformat code" on save

## References

- [PEP 8 -- Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
- [pycodestyle documentation](https://pycodestyle.pycqa.org/)
- [flake8 documentation](https://flake8.pycqa.org/)
- [black documentation](https://black.readthedocs.io/)

## Version History

- **v1.0** (2026-03-17): Initial compliance documentation, all scripts verified

---

**Maintained by**: Senzing Boot Camp Team
**Last Verified**: 2026-03-17
**Next Review**: 2026-06-17
