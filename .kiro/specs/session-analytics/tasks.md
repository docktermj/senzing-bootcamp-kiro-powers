# Tasks

## Task 1: Create `session_logger.py` with log entry construction and serialization

- [x] 1.1 Create `senzing-bootcamp/scripts/session_logger.py` with `LogEntry` dataclass (`timestamp`, `session_id`, `module`, `step`, `event`, `duration_seconds`, `message`), `VALID_EVENTS` set (`turn`, `correction`, `module_start`, `module_complete`), and `LOG_PATH_DEFAULT` constant (`config/session_log.jsonl`)
- [x] 1.2 Implement `build_log_entry(session_id, module, step, event, duration_seconds, message)` that validates inputs (module in 1–11, event in VALID_EVENTS, duration_seconds >= 0, session_id non-empty) raising `ValueError` for invalid inputs, generates an ISO 8601 UTC timestamp, and returns a `LogEntry` instance
  _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
- [x] 1.3 Implement `serialize_entry(entry)` that converts a `LogEntry` to a compact JSON string (no trailing newline) using `json.dumps` with `separators=(",", ":")`
  _Requirements: 1.5_

## Task 2: Implement append logic with file creation and error handling

- [x] 2.1 Implement `append_entry(log_path, entry)` that serializes the entry, creates the file and parent directories if they don't exist, appends the JSON line followed by a newline character, and on any file-system error prints a warning to stderr and returns without raising
  _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

## Task 3: Create `analyze_sessions.py` with JSONL parsing

- [x] 3.1 Create `senzing-bootcamp/scripts/analyze_sessions.py` with `ParseResult` dataclass (`entries: list[dict]`, `error_count: int`) and `LOG_PATH_DEFAULT` constant
- [x] 3.2 Implement `parse_log(file_path)` that reads the JSONL file line by line, parses each line as independent JSON, skips invalid lines while incrementing `error_count`, and returns a `ParseResult`. If the file does not exist, return empty entries with error_count 0
  _Requirements: 3.1, 3.2, 3.3, 3.4_

## Task 4: Implement per-module summary and confusion ranking

- [x] 4.1 Implement `ModuleSummary` and `SummaryReport` dataclasses, and `compute_summary(entries)` that aggregates per-module turns, corrections, and total_seconds from the entry list, sorts modules in ascending order by module number, computes overall totals, and returns a `SummaryReport`. When entries is empty, return a report indicating no data available
  _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
- [x] 4.2 Implement confusion ranking within `compute_summary`: compute correction density (corrections / turns) for each module with non-zero turns, round to two decimal places, sort descending by density, and store as `confusion_ranking` list of `(module, density)` tuples. Exclude modules with zero turns
  _Requirements: 5.1, 5.2, 5.3_

## Task 5: Implement output formatting (text and JSON)

- [x] 5.1 Implement `format_text(report)` that produces a human-readable plain-text table with columns for module number, turns, corrections, total time, and a section for overall totals, followed by the confusion ranking
  _Requirements: 6.1_
- [x] 5.2 Implement `format_json(report)` that produces a single valid JSON object with `modules`, `overall`, and `confusion_ranking` keys matching the JSON output format in the design
  _Requirements: 6.2_

## Task 6: Implement pretty-print and module filter

- [x] 6.1 Implement `pretty_print_entries(entries, module_filter=None)` that formats each valid log entry as indented JSON (2-space indent) separated by a blank line. When `module_filter` is provided, include only entries where `module` equals the filter value
  _Requirements: 7.1, 7.2, 7.3_

## Task 7: Implement CLI entry point with argument parsing

- [x] 7.1 Implement `main(argv=None)` with `argparse`: positional `file_path` argument (default: `config/session_log.jsonl`), `--format` option (`text` or `json`, default `text`), `--output` option for file path, `--pretty` flag, and `--module N` filter. Route to the appropriate function based on flags and write output to stdout or the specified file
  _Requirements: 3.3, 6.1, 6.2, 6.3, 6.4, 7.1, 7.2_

## Task 8: Property-based tests (Hypothesis)

- [x] 8.1 Create `senzing-bootcamp/tests/test_session_analytics.py` with Hypothesis strategies for generating random valid LogEntry parameters (session_id as uuid strings, module in 1–11, step as int or string, event from VALID_EVENTS, duration_seconds as non-negative floats, message as text strings) and random JSONL content (mixes of valid and invalid lines)
- [x] 8.2 PBT: Property 1 — Append Preserves Existing Lines and Adds Exactly One: for any existing JSONL content and any valid LogEntry, appending does not modify existing lines and adds exactly one new line (Req 1.1, 1.3)
- [x] 8.3 PBT: Property 2 — Log Entry Schema and JSONL Format Validity: for any valid LogEntry built via build_log_entry, the serialized output is valid JSON containing all required fields with correct types and ranges (Req 1.5, 2.1–2.7)
- [x] 8.4 PBT: Property 3 — Write-Parse Round-Trip: for any valid LogEntry, serializing with serialize_entry and parsing the result with json.loads produces a dict with identical field names and values (Req 3.1, 3.4)
- [x] 8.5 PBT: Property 4 — Invalid Line Resilience: for any JSONL file with a random mix of valid JSON lines and invalid strings, parse_log returns exactly the valid entries and an error_count equal to the number of invalid lines (Req 3.2)
- [x] 8.6 PBT: Property 5 — Per-Module Aggregation Correctness: for any list of valid log entry dicts spanning multiple modules and sessions, compute_summary produces per-module turns, corrections, and total_seconds that match manual sums (Req 4.1, 4.4)
- [x] 8.7 PBT: Property 6 — Summary Report Structure Invariant: for any non-empty set of log entries, the summary modules list is in ascending order by module number and overall totals equal the sum of per-module values (Req 4.2, 4.3)
- [x] 8.8 PBT: Property 7 — Confusion Ranking Correctness: for any set of log entries with at least one module having non-zero turns, the confusion ranking lists only modules with non-zero turns, sorted descending by correction density rounded to two decimal places (Req 5.1, 5.2, 5.3)
- [x] 8.9 PBT: Property 8 — JSON Output Validity: for any summary report, format_json produces a string that parses as valid JSON containing modules, overall, and confusion_ranking keys (Req 6.2)
- [x] 8.10 PBT: Property 9 — Pretty-Print Round-Trip: for any valid log entry dict, pretty-printing as indented JSON and then stripping whitespace and re-parsing produces an identical dict (Req 7.1, 7.3)
- [x] 8.11 PBT: Property 10 — Module Filter Correctness: for any set of log entry dicts and any module number N, filtering returns exactly the entries with module == N (Req 7.2)

## Task 9: Example-based unit tests

- [x] 9.1 Unit test: `build_log_entry` with valid inputs returns a LogEntry with correct field values
- [x] 9.2 Unit test: `build_log_entry` raises ValueError for module 0, module 12, invalid event, and negative duration_seconds
- [x] 9.3 Unit test: `append_entry` creates missing directories and file on first write (Req 1.2)
- [x] 9.4 Unit test: `append_entry` prints warning to stderr on file-system error and does not raise (Req 1.4)
- [x] 9.5 Unit test: `parse_log` uses default path `config/session_log.jsonl` when no path given (Req 3.3)
- [x] 9.6 Unit test: `compute_summary` with empty entries returns report indicating no data (Req 4.5)
- [x] 9.7 Unit test: `format_text` produces output with column headers and aligned data (Req 6.1)
- [x] 9.8 Unit test: default format is text when no `--format` flag provided (Req 6.3)
- [x] 9.9 Unit test: `--output` flag writes to specified file instead of stdout (Req 6.4)
- [x] 9.10 Unit test: `--pretty --module 5` outputs only module 5 entries (Req 7.2)

## Task 10: Integration tests

- [x] 10.1 Integration test: write 10 entries via session_logger then run analyze_sessions, verify summary matches expected aggregation
- [x] 10.2 Integration test: write entries with 2 different session_ids, verify summary aggregates across both sessions (Req 4.4)
- [x] 10.3 Integration test: write entries then run `--pretty`, verify indented JSON output with blank line separation
