# Tasks

## Task 1: Create triage script with data structures and parser

- [x] 1.1 Create `senzing-bootcamp/scripts/triage_feedback.py` with the `FeedbackEntry` dataclass (title, date, module, priority, category, what_happened, why_problem, suggested_fix, workaround), constants for `VALID_CATEGORIES`, `VALID_PRIORITIES`, `REQUIRED_FIELDS`, and the `to_kebab_case(title)` function that converts strings to kebab-case (lowercase, special characters to hyphens, consecutive hyphens collapsed, leading/trailing hyphens stripped)
- [x] 1.2 Implement `extract_field(section, field_name)` that extracts content for a named field from a feedback section by matching `**Field Name:**` or `### Field Name` patterns, handling multi-paragraph content by capturing until the next field heading, and preserving all markdown formatting (bold, italic, code blocks, lists)
- [x] 1.3 Implement `parse_feedback_file(content)` that: (a) splits content on `## Improvement: <title>` headings, (b) extracts all fields from each section using `extract_field`, (c) logs warnings for entries missing required fields (title, category) and skips them, (d) logs warnings for unrecognized categories and defaults to treating them as non-bug, (e) returns `(list[FeedbackEntry], list[str])` tuple of entries and warnings

## Task 2: Implement skeleton generators

- [x] 2.1 Implement `generate_bugfix_skeleton(entry)` that produces a `bugfix.md` string with sections: "Bug Report" (from what_happened), "Steps to Reproduce" (from module, date, and sequential steps in what_happened), "Expected Behavior" (derived from inverse of why_problem), "Suggested Fix" (from suggested_fix), and conditionally "Known Workaround" (from workaround, only if non-empty)
- [x] 2.2 Implement `generate_requirements_skeleton(entry)` that produces a `requirements.md` string with: an auto-generated comment at the top indicating it was created by the triage script and requires human review, "Introduction" section summarizing the entry using title/what_happened/why_problem, "Glossary" section with placeholder entries from title key terms, and "Requirements" section with one stub containing a user story derived from suggested_fix and empty acceptance criteria placeholders
- [x] 2.3 Implement `generate_config(workflow_type, spec_type)` that produces a JSON string with `specId` (unique UUID v4), `workflowType`, and `specType` fields

## Task 3: Implement directory creation and triage report

- [x] 3.1 Implement `create_spec_directory(entry, base_dir, dry_run)` that: (a) derives directory name using `to_kebab_case(entry.title)`, (b) checks if directory already exists and returns `(None, warning)` if so, (c) creates the directory under `base_dir`, (d) writes the appropriate skeleton file (`bugfix.md` for Bug category, `requirements.md` for others), (e) writes `.config.kiro` with correct `workflowType`/`specType` (`"bugfix"`/`"bugfix"` for bugs, `"requirements-first"`/`"feature"` for others), (f) handles filesystem errors by logging and returning `(None, error_message)`
- [x] 3.2 Implement `TriageResult` dataclass and `print_triage_report(generated, skipped, total_entries)` that: (a) lists each generated spec with path, title, doc type, and priority, (b) lists skipped entries with reasons, (c) prints summary line showing total processed, generated, and skipped counts, (d) prints "No improvement entries found" message when total_entries is 0

## Task 4: Implement CLI entry point

- [x] 4.1 Implement `main(argv)` with `argparse` supporting: (a) optional positional `path` argument defaulting to `SENZING_BOOTCAMP_POWER_FEEDBACK.md`, (b) `--dry-run` flag that prints report without creating files, (c) `--output-dir` flag that overrides default `.kiro/specs/` base directory; exit with code 1 if feedback file not found, exit with code 0 on success or zero entries
- [x] 4.2 Wire the full pipeline in `main()`: read feedback file → `parse_feedback_file` → iterate entries calling `create_spec_directory` → collect results → `print_triage_report` → exit with appropriate code

## Task 5: Property-based tests

- [x] 5.1 Create `senzing-bootcamp/tests/test_feedback_triage_properties.py` with Hypothesis strategies for generating random feedback markdown content (with `## Improvement:` headings, field sections with markdown formatting), random FeedbackEntry objects, and random title strings for kebab-case testing
- [x] 5.2 PBT: Property 1 — Heading-Based Entry Identification: for any markdown content, the parser identifies exactly the sections delimited by `## Improvement:` headings (Req 1.3)
- [x] 5.3 PBT: Property 2 — Field Extraction Completeness: for any valid feedback entry with all fields, the parser extracts all fields with complete content (Req 1.4)
- [x] 5.4 PBT: Property 3 — Missing Required Fields Cause Skip: for any entry missing title or category, the parser logs a warning and excludes it (Req 1.5)
- [x] 5.5 PBT: Property 4 — Kebab-Case Determinism: for any input string, `to_kebab_case` produces lowercase output with only alphanumeric chars and hyphens, no consecutive hyphens, no leading/trailing hyphens (Req 2.2)
- [x] 5.6 PBT: Property 5 — Bug Category Routes to Bugfix Skeleton: for any entry with category "Bug", generates `bugfix.md`; for non-bug, generates `requirements.md` (Req 3.1, 4.1)
- [x] 5.7 PBT: Property 6 — Bugfix Skeleton Content Mapping: for any bug entry, skeleton contains what_happened in "Bug Report", suggested_fix in "Suggested Fix", and "Known Workaround" iff workaround is non-empty (Req 3.2, 3.5, 3.6)
- [x] 5.8 PBT: Property 7 — Requirements Skeleton Content Mapping: for any non-bug entry, skeleton contains title and problem in "Introduction" and user story from suggested_fix in "Requirements" (Req 4.2, 4.4)
- [x] 5.9 PBT: Property 8 — Triage Report Accuracy: for any set of entries, summary counts satisfy total = generated + skipped (Req 5.2, 5.3, 5.4)
- [x] 5.10 PBT: Property 9 — Config File UUID Uniqueness: for any set of generated configs, all specId values are valid UUID v4 and distinct (Req 2.4, 2.5)
- [x] 5.11 PBT: Property 10 — Parser Round-Trip Content Preservation: for any valid entry, parsing and writing to skeleton preserves what_happened, why_problem, and suggested_fix content including markdown formatting (Req 7.1, 7.2, 7.4)

## Task 6: Example-based unit tests and integration tests

- [x] 6.1 Create `senzing-bootcamp/tests/test_feedback_triage_unit.py` with unit tests: (a) parse real feedback template structure, (b) default file path when no argument, (c) `--dry-run` creates no files, (d) `--output-dir` overrides base directory, (e) missing file exits with code 1, (f) filesystem error skips entry and continues, (g) auto-generated comment in requirements skeleton, (h) empty feedback file exits with code 0, (i) existing directory causes skip with warning
- [x] 6.2 Add integration test: full triage run on a sample feedback file produces correct directory structure, skeleton files, and config files; script runs with no third-party imports
- [x] 6.3 Run all tests (`pytest senzing-bootcamp/tests/test_feedback_triage_properties.py senzing-bootcamp/tests/test_feedback_triage_unit.py`) and verify they pass
