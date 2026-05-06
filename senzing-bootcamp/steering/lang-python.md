---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# Python + Senzing SDK

- Use `python3` on Linux, `python` on Windows
- Platform support for Python is determined by the Senzing MCP server — relay any warnings it provides about the user's platform

## Senzing SDK Best Practices

- Always obtain SDK method signatures from the MCP server (`get_sdk_reference`) — never guess method names or parameters
- Use context managers (`with` statements) for Senzing engine lifecycle — ensures `destroy()` is called on exit and exceptions
- Load engine configuration from JSON files using `json.load()` — never hardcode configuration strings
- Use `json.dumps()` with `ensure_ascii=False` for record payloads containing international characters
- Wrap all SDK calls in try/except blocks catching the Senzing-specific exception type — use `explain_error_code` for diagnosis
- Initialize the engine once and reuse — do not create/destroy per record

## Common Pitfalls

- **Forgetting engine cleanup:** Always pair `init()` with `destroy()` — use a context manager wrapper or `try/finally` to guarantee cleanup
- **GIL blocking on CPU-bound ER:** Python threads share the GIL — use `multiprocessing` or `concurrent.futures.ProcessPoolExecutor` for parallel loading, not `threading`
- **Silent encoding errors:** Use `encoding='utf-8'` explicitly when opening data files — default encoding varies by platform and can corrupt names/addresses
- **Catching bare `Exception`:** Catch the specific Senzing exception class so SDK errors are distinguishable from bugs in your code
- **Mutable default arguments:** Never use `def load_records(records=[])` — use `None` and assign inside the function

## Performance Considerations

- Use `multiprocessing.Pool` or `ProcessPoolExecutor` for parallel record loading — each process gets its own engine instance to bypass the GIL
- Process records in batches of 100-1000 — balances throughput against memory usage
- Use generator functions (`yield`) to stream large CSV/JSONL files instead of loading entire datasets into memory
- For JSONL input, use `line.rstrip('\n')` before `json.loads()` — avoids unnecessary string copies
- Profile with `cProfile` before optimizing — Senzing SDK calls dominate runtime, not Python overhead
- Set `SENZING_ENGINE_CONFIGURATION_JSON` once at startup — repeated config parsing adds latency

## Code Style for Generated Code

- Project layout: `src/` for application code, `scripts/` for one-off utilities, `config/` for JSON configs, `data/` for input/output
- Use `logging` module (not `print()`) — configure with level, format, and timestamp at program entry
- Store configuration paths in a `config/` directory — load with `pathlib.Path` for cross-platform compatibility
- Use `argparse` for CLI programs — provide `--help`, `--input`, `--config`, and `--batch-size` flags
- Type hints on all function signatures — enables `mypy` checking and improves agent-generated code clarity

## Platform Notes

- Linux: use `python3` and `pip3` commands — `python` may point to Python 2 on older distributions
- Windows: use `python` and `pip` — ensure Python is on `PATH` via installer checkbox. Use `pyenv-win` for version management if needed
- macOS: use `python3` — system Python is outdated; recommend `brew install python` or `pyenv`
- Virtual environments: always create with `python3 -m venv .venv` (or `python -m venv .venv` on Windows) and activate before installing dependencies
- Senzing native libraries: path varies by OS — follow `sdk_guide` output exactly for `LD_LIBRARY_PATH` (Linux), `DYLD_LIBRARY_PATH` (macOS), or `PATH` (Windows — add Senzing `lib` directory)

## Common Environment Issues

### Virtual Environment Activation Failures

**Symptom**: Running `activate` produces "command not found" or "not recognized" errors
**Cause**: The activation script path differs between Windows (`Scripts\activate`) and Unix (`bin/activate`)
**Fix**:

1. On Linux/macOS: `source .venv/bin/activate`
2. On Windows CMD: `.venv\Scripts\activate.bat`
3. On Windows PowerShell: `.venv\Scripts\Activate.ps1` (may require `Set-ExecutionPolicy RemoteSigned`)
4. Verify with: `which python` (Unix) or `where python` (Windows) — should point to `.venv`

### pip vs pip3 Confusion

**Symptom**: Packages install globally instead of into the virtual environment, or `pip` installs to Python 2
**Cause**: System Python and venv Python have different `pip` executables; using the wrong one installs to the wrong location
**Fix**:

1. Always activate the virtual environment first (`source .venv/bin/activate`)
2. Use `python -m pip install` instead of bare `pip` — guarantees the correct interpreter
3. Verify with: `python -m pip --version` — should show the venv path

### Python Version Conflicts

**Symptom**: `SyntaxError` on match statements, f-string features, or Senzing SDK imports fail with version errors
**Cause**: The system Python is older than 3.11, which is the minimum required for Senzing bootcamp exercises
**Fix**:

1. Check current version: `python3 --version`
2. Install Python 3.11+ via package manager (`brew install python@3.11`, `sudo apt install python3.11`, or download from python.org)
3. Create venv with the correct version: `python3.11 -m venv .venv`
4. Verify with: `python3 --version` — should show 3.11 or higher

### ModuleNotFoundError for Senzing Bindings

**Symptom**: `ModuleNotFoundError: No module named 'senzing'` when running scripts
**Cause**: The Senzing Python package is not installed in the currently active virtual environment
**Fix**:

1. Ensure the virtual environment is activated (check prompt prefix)
2. Install the package: `python -m pip install senzing`
3. If using a requirements file: `python -m pip install -r requirements.txt`
4. Verify with: `python -c "import senzing; print(senzing.__version__)"`

### PATH Issues for Senzing Libraries

**Symptom**: `OSError: cannot load library` or `ImportError: libSz.so: cannot open shared object file`
**Cause**: The Senzing native shared libraries are not on the system library search path for the current platform
**Fix**:

1. On Linux: `export LD_LIBRARY_PATH=/opt/senzing/lib:$LD_LIBRARY_PATH`
2. On macOS: `export DYLD_LIBRARY_PATH=/opt/senzing/lib:$DYLD_LIBRARY_PATH`
3. On Windows: add the Senzing `lib` directory to `PATH` in System Environment Variables
4. Verify with: `python -c "from senzing import SzEngine; print('OK')"`
