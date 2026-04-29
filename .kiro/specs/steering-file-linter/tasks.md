# Tasks

## Task 1: Create linter script with core data structures and utility functions

- [x] 1.1 Create `senzing-bootcamp/scripts/lint_steering.py` with the `LintViolation` dataclass (`level`, `file`, `line`, `message`, `format()` method), module-level constants for paths (`STEERING_DIR`, `HOOKS_DIR`, `INDEX_PATH`), valid inclusion values (`VALID_INCLUSIONS`), and regex patterns for cross-references, module filenames, numbered steps, checkpoints, WAIT instructions, prose references, and frontmatter delimiters
- [x] 1.2 Implement utility functions: `parse_frontmatter(content)` returning `(dict|None, end_line)`, `is_in_code_block(lines, line_index)` that tracks fenced code block state, `parse_steering_index(index_path)` returning structured dict with modules/file_metadata/keywords sections, and `get_final_substantive_line(lines)` returning `(index, content)` of the last non-blank non-comment line

## Task 2: Implement Rule 1 — Orphaned Cross-Reference Detection

- [x] 2.1 Implement `check_cross_references(steering_dir, index_data)` that scans all steering files for `#[[file:path]]` include references and backtick-quoted `.md` filenames (skipping content inside fenced code blocks), verifies each referenced path exists, and returns `LintViolation` errors for missing targets with source file, line number, and target path
  _Requirements: 1.1, 1.2, 1.3_
- [x] 2.2 Add steering index reference validation: scan all mapping sections (modules, keywords, languages, deployment) in the index data for file references and verify each exists in the steering directory, returning `LintViolation` errors for missing files with the mapping key and filename
  _Requirements: 1.4, 1.5_

## Task 3: Implement Rule 2 — Module Numbering Consistency

- [x] 3.1 Implement `check_module_numbering(steering_dir, index_data)` that: (a) verifies every module number in the index has a corresponding `module-NN-*.md` file on disk, (b) reports warnings for module files on disk not listed in the index, (c) verifies the `NN` in each filename is a zero-padded two-digit integer matching its index entry, and (d) detects gaps in the module number sequence and reports warnings
  _Requirements: 2.1, 2.2, 2.3, 2.4_

## Task 4: Implement Rule 3 — WAIT Instruction and Hook Ownership Conflict Detection

- [x] 4.1 Implement `check_wait_conflicts(steering_dir, hooks_dir)` that: (a) scans each steering file for `WAIT for` patterns (case-sensitive), (b) reports a warning when a WAIT instruction appears on the final substantive line (ignoring trailing blanks/comments) unless preceded by a `👉` question, (c) treats WAIT instructions inside hook prompts associated with `agentStop` event type as valid, and (d) treats `👉` + WAIT pairs as valid mid-conversation interactions
  _Requirements: 3.1, 3.2, 3.3, 3.4_

## Task 5: Implement Rule 4 — Missing Checkpoint Instruction Detection

- [x] 5.1 Implement `check_checkpoints(steering_dir)` that: (a) parses each `module-NN-*.md` file to identify top-level numbered steps (`1. `, `2. `, etc.), (b) reports errors for steps without a corresponding `**Checkpoint:** Write step N` instruction before the next step or end of file, (c) reports errors when a checkpoint's step number doesn't match the step it follows, and (d) skips checkpoint validation for files with zero numbered steps
  _Requirements: 4.1, 4.2, 4.3, 4.4_

## Task 6: Implement Rule 5 — Steering Index Completeness

- [x] 6.1 Implement `check_index_completeness(steering_dir, index_data)` that: (a) verifies every `.md` file in the steering directory has a `file_metadata` entry, (b) reports errors for files missing from metadata, (c) validates each metadata entry has a `token_count` (positive integer) and `size_category` (one of `small`, `medium`, `large`), and (d) reports errors for invalid or missing fields
  _Requirements: 5.1, 5.2, 5.3, 5.4_

## Task 7: Implement Rule 6 — Hook Registry and Hook File Consistency

- [x] 7.1 Implement `check_hook_consistency(steering_dir, hooks_dir)` that: (a) extracts hook IDs from `hook-registry.md` by scanning for `- id:` lines, (b) reports errors for registry IDs without corresponding `.kiro.hook` files, (c) reports warnings for `.kiro.hook` files not documented in the registry, and (d) reports errors when the event type in the registry doesn't match the `when.type` field in the hook file
  _Requirements: 6.1, 6.2, 6.3, 6.4_

## Task 8: Implement Rule 7 — Frontmatter Validation

- [x] 8.1 Implement `check_frontmatter(steering_dir)` that: (a) verifies every steering file (excluding `steering-index.yaml`) begins with a `---` delimited YAML frontmatter block, (b) reports errors for files lacking frontmatter, (c) validates the `inclusion` field is one of `always`, `auto`, `fileMatch`, `manual`, (d) when `inclusion` is `fileMatch`, verifies a non-empty `fileMatchPattern` field exists, and (e) reports errors for missing or unrecognized inclusion values
  _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

## Task 9: Implement Rule 9 — Internal Link Validation and CLI Entry Point

- [x] 9.1 Implement `check_internal_links(steering_dir)` that: (a) scans steering files for prose references matching `load \`filename.md\``, `follow \`filename.md\``, or `see \`filename.md\`` patterns, (b) skips references inside fenced code blocks, (c) verifies each referenced file exists in the steering directory, and (d) reports errors for missing targets with source file, line number, and target
  _Requirements: 9.1, 9.2, 9.3_
- [x] 9.2 Implement `run_all_checks(steering_dir, hooks_dir, index_path, warnings_as_errors)` that calls all rule functions, collects violations, and returns `(violations, exit_code)` where exit_code is 0 if no errors (or no errors+warnings when flag set), else 1
- [x] 9.3 Implement `main()` CLI entry point with `argparse` supporting `--warnings-as-errors` flag, printing each violation in `{level}: {file}:{line}: {message}` format, printing a summary line with error and warning counts, and exiting with the computed exit code
  _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

## Task 10: Verify linter on real corpus

- [x] 10.1 Run `python senzing-bootcamp/scripts/lint_steering.py` on the actual steering corpus and verify it completes without crashing, produces correctly formatted output, and the exit code reflects the violation state
- [x] 10.2 Fix any false positives or false negatives discovered during the real corpus run by adjusting regex patterns or rule logic

## Task 11: Property-based tests (Hypothesis)

- [x] 11.1 Create `senzing-bootcamp/tests/test_lint_steering_properties.py` with Hypothesis strategies for generating random steering file content (with embedded references, numbered steps, checkpoints, WAIT instructions, frontmatter blocks), random steering index structures, and random sets of file/hook IDs
- [x] 11.2 PBT: Property 1 — Cross-Reference Detection Completeness: for any file content with `#[[file:path]]` references, the linter reports an error for every non-existing target and no error for existing targets (Req 1.1, 1.3)
- [x] 11.3 PBT: Property 2 — Bidirectional Module Numbering Consistency: for any set of module numbers in index and on disk, the linter reports every number in one set but not the other (Req 2.1, 2.2)
- [x] 11.4 PBT: Property 3 — Module Sequence Gap Detection: for any sequence of module numbers, the linter reports a warning for every integer gap (Req 2.4)
- [x] 11.5 PBT: Property 4 — WAIT-at-End-of-File Detection: for any file content, the linter warns iff the final substantive line contains `WAIT for` without a preceding `👉` question (Req 3.2, 3.4)
- [x] 11.6 PBT: Property 5 — Step-Checkpoint Matching: for any module content with numbered steps, the linter reports errors for steps missing checkpoints and for mismatched step numbers (Req 4.2, 4.3)
- [x] 11.7 PBT: Property 6 — File Metadata Completeness: for any set of files and metadata entries, the linter reports errors for missing entries and invalid fields (Req 5.1, 5.2, 5.3, 5.4)
- [x] 11.8 PBT: Property 7 — Bidirectional Hook Registry Consistency: for any set of registry IDs and hook file IDs, the linter reports all mismatches in both directions and event type discrepancies (Req 6.2, 6.3, 6.4)
- [x] 11.9 PBT: Property 8 — Frontmatter Inclusion Validation: for any file content, the linter reports errors for missing frontmatter, invalid inclusion values, and missing fileMatchPattern when inclusion is fileMatch (Req 7.1, 7.2, 7.3, 7.4, 7.5)
- [x] 11.10 PBT: Property 9 — Exit Code Correctness: for any set of violations, exit code is 0 iff no errors (or no errors+warnings with flag), else 1 (Req 8.2, 8.3, 8.6)
- [x] 11.11 PBT: Property 10 — Violation Output Format: for any LintViolation, formatted output matches `{ERROR|WARNING}: {file}:{line}: {message}` (Req 8.4)
- [x] 11.12 PBT: Property 11 — Code-Block-Aware Reference Validation: for any file content with references inside and outside code blocks, the linter validates only outside references (Req 9.3)

## Task 12: Example-based unit tests

- [x] 12.1 Unit test: real steering corpus has no orphaned `#[[file:]]` references (Req 1.1)
- [x] 12.2 Unit test: real module numbering is consistent between index and files (Req 2.1)
- [x] 12.3 Unit test: real module files have checkpoints for all numbered steps (Req 4.1)
- [x] 12.4 Unit test: real steering files have valid YAML frontmatter (Req 7.1)
- [x] 12.5 Unit test: real hook registry matches hook files bidirectionally (Req 6.1)
- [x] 12.6 Unit test: `--warnings-as-errors` flag changes exit code when warnings are present (Req 8.6)
- [x] 12.7 Unit test: output format matches `{level}: {file}:{line}: {message}` for known violations (Req 8.4)
- [x] 12.8 Unit test: summary line shows correct error and warning counts (Req 8.5)

## Task 13: Integration tests

- [x] 13.1 Integration test: full linter run on real corpus — `python scripts/lint_steering.py` completes and exit code reflects violation state
- [x] 13.2 Integration test: linter runs with no third-party imports (only Python standard library)
- [x] 13.3 Integration test: summary line format is `{N} error(s), {M} warning(s)`
