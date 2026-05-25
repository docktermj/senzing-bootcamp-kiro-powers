# Implementation Plan: Graduation Certificate

## Overview

Implement a Python CLI script that generates graduation certificates in Markdown and HTML formats from bootcamp progress, preferences, and journal data. The script follows project conventions (stdlib-only, argparse, `main(argv=None)`) and is invoked by the module-completion steering file during path completion. Tests use pytest + Hypothesis for property-based verification.

## Tasks

- [x] 1. Create script skeleton with CLI interface and data models
  - [x] 1.1 Create `senzing-bootcamp/scripts/generate_graduation_certificate.py` with argparse CLI, `main(argv=None)` entry point, and all dataclass models (`ProgressData`, `PreferencesData`, `JournalEntry`, `ERMetrics`, `JournalData`, `ModuleRecord`, `CertificateData`)
    - Define `parse_args(argv)` with `--progress-file`, `--preferences-file`, `--journal-file`, `--output-dir` arguments and their defaults
    - Define all dataclasses from the design
    - Wire `main()` to parse args and return exit code 0/1
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [x] 1.2 Write unit tests for argument parsing
    - Test default values for all arguments
    - Test overriding each argument
    - _Requirements: 2.3, 2.4, 2.5, 2.6_

- [x] 2. Implement data loaders
  - [x] 2.1 Implement `load_progress(path)` to parse `bootcamp_progress.json`
    - Read JSON, extract completed module numbers and names
    - Exit with code 1 and stderr message if file missing or malformed
    - _Requirements: 5.1, 9.1, 9.4_

  - [x] 2.2 Implement `parse_simple_yaml(content)` and `load_preferences(path)` for preferences file
    - Line-by-line YAML parser for flat key:value pairs
    - Return defaults (track="Unknown", language="Unknown") if file missing or malformed
    - _Requirements: 4.3, 9.2, 9.4_

  - [x] 2.3 Implement `load_journal(path)` to parse journal markdown
    - Use regex patterns to extract module headings, outcomes, and ER metrics
    - Return empty data if file missing; parse whatever entries succeed if malformed
    - _Requirements: 5.2, 5.3, 6.1, 6.2, 6.3, 9.3, 9.4_

  - [x] 2.4 Write unit tests for data loaders
    - Test `load_progress` with valid JSON, missing file, malformed JSON
    - Test `load_preferences` with valid YAML, missing file, malformed content
    - Test `load_journal` with valid markdown, missing file, partial entries
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [x] 2.5 Write property test: no unhandled exceptions for any input (Property 8)
    - **Property 8: No unhandled exceptions for any input**
    - Generate random/malformed content for progress, preferences, and journal files
    - Assert the script never raises an unhandled exception
    - **Validates: Requirements 9.4**

- [x] 3. Implement content assembly and logic
  - [x] 3.1 Implement `assemble_certificate(progress, preferences, journal, project_name)` to build `CertificateData`
    - Combine modules with journal outcomes
    - Set completion date to today in ISO 8601 format
    - Derive project name from workspace directory
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_

  - [x] 3.2 Implement `MODULE_SKILLS` mapping and skills derivation logic
    - Static dict mapping module numbers to skill categories
    - Flatten skills for completed modules into deduplicated list
    - _Requirements: 7.1_

  - [x] 3.3 Implement `derive_next_steps(track)` function
    - Core Bootcamp → advanced topics recommendations
    - Advanced Topics → production deployment recommendations
    - Unknown → generic next steps
    - _Requirements: 7.2, 7.3, 7.4_

  - [x] 3.4 Write property test: skills and next-steps derived from completed track and modules (Property 7)
    - **Property 7: Skills and next-steps derived from completed track and modules**
    - Generate random sets of completed modules and valid track names
    - Assert certificate contains at least one skill per module and appropriate next-steps
    - **Validates: Requirements 7.1, 7.2**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement renderers
  - [x] 5.1 Implement `render_markdown(data)` to produce the Markdown certificate
    - Include title, identity section, modules table, ER results, skills, next steps
    - Use ER placeholder text when no metrics available
    - _Requirements: 3.1, 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 6.2, 6.3, 7.1, 7.2_

  - [x] 5.2 Implement `render_html(data)` to produce the HTML5 certificate
    - Valid HTML5 with DOCTYPE, head, body, inline CSS styling
    - Use `html.escape()` for all user-provided content
    - Include same content sections as Markdown renderer
    - _Requirements: 3.2, 3.4, 3.5, 4.1, 4.2, 4.3, 5.1, 5.2, 6.1, 6.2, 6.3, 7.1, 7.2_

  - [x] 5.3 Write property test: HTML output is valid HTML5 structure (Property 2)
    - **Property 2: HTML output is valid HTML5 structure**
    - Generate valid inputs and assert HTML contains DOCTYPE, html, head, style, body elements
    - **Validates: Requirements 3.5**

  - [x] 5.4 Write property test: certificate contains identity metadata (Property 3)
    - **Property 3: Certificate contains identity metadata**
    - Generate random project names, dates, and tracks
    - Assert both Markdown and HTML outputs contain project name, ISO date, and track name
    - **Validates: Requirements 4.1, 4.2, 4.3**

  - [x] 5.5 Write property test: all completed modules appear in certificate (Property 4)
    - **Property 4: All completed modules appear in certificate**
    - Generate random progress data with N modules
    - Assert all N module numbers and names appear in output
    - **Validates: Requirements 5.1**

  - [x] 5.6 Write property test: journal outcomes appear for matching modules (Property 5)
    - **Property 5: Journal outcomes appear for matching modules**
    - Generate journal entries for a subset of completed modules
    - Assert outcome text appears in certificate for matching modules
    - **Validates: Requirements 5.2**

  - [x] 5.7 Write property test: ER metrics from journal appear in certificate (Property 6)
    - **Property 6: ER metrics from journal appear in certificate**
    - Generate journal content with/without ER metrics
    - Assert metrics appear when present, placeholder appears when absent
    - **Validates: Requirements 6.1, 6.2**

- [x] 6. Implement file output and wire pipeline together
  - [x] 6.1 Implement output writing in `main()` — create output directory, write both files
    - Create `docs/graduation/` if it doesn't exist using `os.makedirs(exist_ok=True)`
    - Write `graduation_certificate.md` and `graduation_certificate.html`
    - Overwrite existing files without error
    - _Requirements: 3.1, 3.2, 3.3, 10.1_

  - [x] 6.2 Wire the full pipeline in `main()`: parse args → load → assemble → render → write
    - Top-level exception handler catches unexpected errors, prints to stderr, exits 1
    - Return 0 on success
    - _Requirements: 2.7, 9.4_

  - [x] 6.3 Write property test: successful generation produces both output files (Property 1)
    - **Property 1: Successful generation produces both output files**
    - Generate valid progress data and invoke main() with temp directories
    - Assert both files exist and exit code is 0
    - **Validates: Requirements 2.7, 3.1, 3.2**

  - [x] 6.4 Write property test: idempotent output (Property 9)
    - **Property 9: Idempotent output**
    - Run the generator twice with identical inputs
    - Assert output files are byte-identical
    - **Validates: Requirements 10.2**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Update steering file for integration
  - [x] 8.1 Update `senzing-bootcamp/steering/module-completion.md` to invoke the Certificate_Generator
    - Add certificate generation step in "Path Completion Celebration" section
    - Place after analytics offer, before graduation offer
    - Include success message: "🎓 Graduation certificate generated at docs/graduation/"
    - Include failure handling: log warning and continue
    - _Requirements: 1.1, 1.2, 1.3, 8.1, 8.2, 8.3_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The script uses only Python 3.11+ stdlib (no third-party dependencies)
- Tests use pytest + Hypothesis and live in `senzing-bootcamp/tests/`

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1", "2.2", "2.3"] },
    { "id": 2, "tasks": ["2.4", "2.5", "3.1", "3.2", "3.3"] },
    { "id": 3, "tasks": ["3.4", "5.1", "5.2"] },
    { "id": 4, "tasks": ["5.3", "5.4", "5.5", "5.6", "5.7"] },
    { "id": 5, "tasks": ["6.1", "6.2"] },
    { "id": 6, "tasks": ["6.3", "6.4"] },
    { "id": 7, "tasks": ["8.1"] }
  ]
}
```
