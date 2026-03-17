# Python Requirements Policy

## Overview

When generating Python source code for the Senzing Boot Camp, a `requirements.txt` file must be created or updated in the project root to track all Python dependencies.

## Purpose

The `requirements.txt` file:
- Documents all Python package dependencies
- Enables reproducible environments
- Simplifies installation for other users
- Supports virtual environment setup
- Tracks dependency versions

## When to Create/Update

Create or update `requirements.txt` when generating Python code in:

- **Module 0**: Quick Demo scripts
- **Module 4**: Data transformation programs
- **Module 6**: Data loading programs
- **Module 7**: Query programs
- **Any utility scripts**: In `src/utils/`

## File Location

```
project/
├── requirements.txt        # ← Always in project root
├── src/
│   ├── quickstart_demo/
│   ├── transform/
│   ├── load/
│   ├── query/
│   └── utils/
└── ...
```

**IMPORTANT**: `requirements.txt` goes in the project root, NOT in subdirectories.

## Common Dependencies

### Senzing SDK Projects

Typical dependencies for Senzing projects:

```txt
# Senzing SDK
senzing>=4.0.0

# Data processing
pandas>=2.0.0
orjson>=3.9.0

# Database connectivity (if needed)
psycopg2-binary>=2.9.0  # PostgreSQL
```

### Transformation Programs

Additional dependencies for data transformation:

```txt
# CSV/JSON processing
pandas>=2.0.0
orjson>=3.9.0

# Data validation
jsonschema>=4.0.0

# Date/time handling
python-dateutil>=2.8.0
```

### API Integration

If integrating with APIs:

```txt
# HTTP requests
requests>=2.31.0

# Async support
aiohttp>=3.9.0
```

## Agent Behavior

When generating Python code, the agent should:

1. **Check if `requirements.txt` exists**
   - If not, create it in project root
   - If yes, update it with new dependencies

2. **Add dependencies based on code generated**
   - Senzing SDK: Always add `senzing>=4.0.0`
   - Data processing: Add `pandas`, `orjson` if used
   - Database: Add `psycopg2-binary` if PostgreSQL used
   - Other: Add any other imports used in the code

3. **Use version constraints**
   - Use `>=` for minimum version (e.g., `senzing>=4.0.0`)
   - Pin specific versions only if required (e.g., `senzing==4.0.0`)
   - Document why specific versions are pinned

4. **Organize by category**
   - Group related dependencies
   - Add comments to explain categories
   - Keep alphabetically sorted within categories

5. **Avoid duplicates**
   - Check if dependency already listed
   - Update version if newer version needed
   - Don't add same package twice

## Example requirements.txt

### Minimal Senzing Project

```txt
# Senzing SDK
senzing>=4.0.0

# Data processing
pandas>=2.0.0
orjson>=3.9.0
```

### Full Boot Camp Project

```txt
# Senzing SDK
senzing>=4.0.0

# Data processing
pandas>=2.0.0
orjson>=3.9.0
jsonschema>=4.0.0
python-dateutil>=2.8.0

# Database connectivity
psycopg2-binary>=2.9.0

# Logging and monitoring
colorlog>=6.7.0

# Testing (optional)
pytest>=7.4.0
pytest-cov>=4.1.0
```

### Module 0 Quick Demo

```txt
# Senzing SDK
senzing>=4.0.0

# JSON processing
orjson>=3.9.0
```

## Installation Instructions

After creating `requirements.txt`, users can install dependencies:

### Using pip

```bash
pip install -r requirements.txt
```

### Using virtual environment (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Using uv (fast alternative)

```bash
uv pip install -r requirements.txt
```

## Updating Dependencies

When adding new Python code that uses additional packages:

1. Add the new dependency to `requirements.txt`
2. Document why it's needed (comment)
3. Specify minimum version
4. Test that installation works
5. Commit updated `requirements.txt` to git

## Version Pinning Strategy

### Development/Evaluation
Use minimum version constraints:
```txt
senzing>=4.0.0
pandas>=2.0.0
```

**Benefits**: Get latest compatible versions, easier updates

### Production
Pin exact versions:
```txt
senzing==4.0.0
pandas==2.0.3
```

**Benefits**: Reproducible builds, no surprises

## Common Issues

### Issue: Missing Dependency
**Symptom**: `ModuleNotFoundError: No module named 'senzing'`
**Solution**: Add missing package to `requirements.txt` and run `pip install -r requirements.txt`

### Issue: Version Conflict
**Symptom**: `ERROR: Cannot install package-a and package-b because these package versions have conflicting dependencies`
**Solution**: Adjust version constraints or pin specific compatible versions

### Issue: requirements.txt Not Found
**Symptom**: `ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'`
**Solution**: Ensure you're in the project root directory where `requirements.txt` is located

## Integration with Other Modules

### Module 0: Quick Demo
- Create `requirements.txt` with minimal dependencies
- Include Senzing SDK and JSON processing

### Module 4: Data Mapping
- Update `requirements.txt` with data processing libraries
- Add pandas, orjson, jsonschema as needed

### Module 5: SDK Setup
- Verify Senzing SDK version in `requirements.txt` matches installed version
- Update if needed

### Module 6: Load Records
- Update `requirements.txt` with database drivers if needed
- Add psycopg2-binary for PostgreSQL

### Module 7: Query Results
- Update `requirements.txt` with any additional libraries for result formatting
- Add requests if building API integration

## Documentation

When creating `requirements.txt`, also document in:

1. **README.md**: Add installation instructions
   ```markdown
   ## Installation
   
   Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   ```

2. **docs/environment_setup.md**: Document dependency rationale
   - Why each dependency is needed
   - Version constraints explained
   - Alternative packages considered

## Git Integration

Always commit `requirements.txt` to version control:

```bash
git add requirements.txt
git commit -m "Add/update Python dependencies"
```

Include in `.gitignore`:
```
# Virtual environments
venv/
env/
.venv/

# Python cache
__pycache__/
*.pyc
*.pyo
```

## Quality Checklist

Before finalizing `requirements.txt`:

- [ ] All imported packages are listed
- [ ] Version constraints are appropriate
- [ ] Dependencies are organized by category
- [ ] Comments explain non-obvious dependencies
- [ ] No duplicate entries
- [ ] File is in project root
- [ ] Installation tested in clean environment
- [ ] Committed to git

## Related Documentation

- `POWER.md` - Project structure includes requirements.txt
- `steering/environment-setup.md` - Environment setup guidance
- `steering/agent-instructions.md` - Agent behavior for Python projects
- `MODULE_0_CODE_LOCATION.md` - Module 0 requirements

## Version History

- **v2.0.0** (2026-03-17): Python requirements policy added
