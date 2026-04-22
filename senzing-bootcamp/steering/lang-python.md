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

- **Forgetting engine cleanup**: Always pair `init()` with `destroy()` — use a context manager wrapper or `try/finally` to guarantee cleanup
- **GIL blocking on CPU-bound ER**: Python threads share the GIL — use `multiprocessing` or `concurrent.futures.ProcessPoolExecutor` for parallel loading, not `threading`
- **Silent encoding errors**: Use `encoding='utf-8'` explicitly when opening data files — default encoding varies by platform and can corrupt names/addresses
- **Catching bare `Exception`**: Catch the specific Senzing exception class so SDK errors are distinguishable from bugs in your code
- **Mutable default arguments**: Never use `def load_records(records=[])` — use `None` and assign inside the function

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
- Windows: use `python` and `pip` — ensure Python is on `PATH` via installer checkbox
- macOS: use `python3` — system Python is outdated; recommend `brew install python` or `pyenv`
- Virtual environments: always create with `python3 -m venv .venv` and activate before installing dependencies
- Senzing native libraries: path varies by OS — follow `sdk_guide` output exactly for `LD_LIBRARY_PATH` (Linux) or `DYLD_LIBRARY_PATH` (macOS)
