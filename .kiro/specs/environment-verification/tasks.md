# Tasks

## Task 1: Create data model and report infrastructure

- [x] 1.1 Create `senzing-bootcamp/scripts/preflight.py` with `CheckResult` and `PreflightReport` dataclasses, including `pass_count`, `warn_count`, `fail_count`, and `verdict` properties
- [x] 1.2 Implement `OutputFormatter.to_json()` that serializes a `PreflightReport` to a JSON string with `checks` array and `summary` object (including `fixed` field per check)
- [x] 1.3 Implement `OutputFormatter.to_human()` that renders a grouped, colored report with banner, category headings, status indicators, fix instructions indented below warn/fail checks, and summary section
- [x] 1.4 Implement CLI entry point with `argparse` supporting `--json` and `--fix` flags, returning exit code 1 for FAIL verdict and 0 otherwise

## Task 2: Implement check functions

- [x] 2.1 Implement `check_language_runtimes()` — detect Python/Java/.NET/Rust/Node.js via `shutil.which`, report versions, check pip when Python found, fail if no runtimes found
- [x] 2.2 Implement `check_disk_space()` — use `shutil.disk_usage`, pass at ≥10GB, warn at <10GB, warn on exception
- [x] 2.3 Implement `check_network()` — HTTPS socket to `mcp.senzing.com:443` with 5s timeout, pass on success, warn on failure with offline mode reference
- [x] 2.4 Implement `check_senzing_sdk()` — subprocess import of `senzing` package, pass at version ≥4.0, warn at <4.0 or not importable, skip with warn if no Python
- [x] 2.5 Implement `check_write_permissions()` — create/remove temp dir in cwd, pass on success, fail on OSError
- [x] 2.6 Implement `check_required_tools()` — check git/curl (fail if missing), check zip/unzip on non-Windows (fail if missing), include install URLs in fix instructions
- [x] 2.7 Implement `check_directories()` — verify expected project dirs exist, warn if missing

## Task 3: Implement CheckRunner and AutoFixer

- [x] 3.1 Implement `CheckRunner.run()` that executes all check functions in category order and assembles a `PreflightReport`
- [x] 3.2 Implement `AutoFixer.try_fix()` that creates missing directories with `os.makedirs(exist_ok=True)` and returns updated `CheckResult`
- [x] 3.3 Wire `--fix` flag into `CheckRunner` so fixable checks are attempted before final reporting, with re-check after fix

## Task 4: Legacy script deprecation and documentation updates

- [x] 4.1 Replace `check_prerequisites.py` with a thin deprecation shim that prints a warning to stderr and delegates to `preflight.py`
- [x] 4.2 Replace `preflight_check.py` with a thin deprecation shim that prints a warning to stderr and delegates to `preflight.py`
- [x] 4.3 Update `onboarding-flow.md` Step 3 to run `preflight.py` as a mandatory gate before language selection, replacing inline `shutil.which()` checks
- [x] 4.4 Update `POWER.md` Useful Commands section to list `preflight.py` as the primary environment verification command and mark legacy scripts as deprecated

## Task 5: Property-based tests

- [x] 5.1 Create `senzing-bootcamp/scripts/test_preflight.py` with Hypothesis strategies for `CheckResult`, `PreflightReport`, runtime subsets, disk space values, and version strings
- [x] 5.2 PBT: Property 1 — Language runtime detection produces correct status per environment (Req 2.1, 2.2, 2.3, 2.4)
- [x] 5.3 PBT: Property 2 — Disk space threshold determines check status (Req 3.2, 3.3)
- [x] 5.4 PBT: Property 3 — Senzing SDK version threshold determines check status (Req 5.2, 5.3)
- [x] 5.5 PBT: Property 4 — Required tool presence determines check status (Req 7.1, 7.2, 7.3)
- [x] 5.6 PBT: Property 5 — Human-readable report rendering is complete (Req 8.2, 8.3, 8.4)
- [x] 5.7 PBT: Property 6 — Report verdict and exit code are consistent with check statuses (Req 8.5, 8.6, 8.7)
- [x] 5.8 PBT: Property 7 — JSON output round-trip and structural completeness (Req 9.1-9.5, 10.6)

## Task 6: Unit tests for edge cases and integration points

- [x] 6.1 Unit test: banner text appears in human output (Req 8.1)
- [x] 6.2 Unit test: network check uses correct host/port/timeout parameters (Req 4.1, 4.2, 4.3)
- [x] 6.3 Unit test: SDK check skipped when no Python runtime (Req 5.5)
- [x] 6.4 Unit test: write permissions pass/fail (Req 6.1, 6.2, 6.3)
- [x] 6.5 Unit test: --fix failure retains original status and appends error reason (Req 10.4)
- [x] 6.6 Unit test: zip/unzip checked only on non-Windows platforms (Req 7.4)
- [x] 6.7 Unit test: legacy scripts print deprecation warning and delegate (Req 12.2, 12.3)
- [x] 6.8 Unit test: disk_usage exception produces warn (Req 3.4)
