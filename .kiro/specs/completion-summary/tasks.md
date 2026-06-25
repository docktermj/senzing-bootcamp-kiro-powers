# Implementation Plan: Completion Summary

## Overview

Extend the existing session logger with new completion event types, build a narrative formatter and PDF generator, add a steering file for stopping point detection, and wire everything together with an integration hook. Implementation uses Python 3.11+ stdlib (plus fpdf2 for PDF), tested with pytest + Hypothesis.

## Tasks

- [x] 1. Extend Session Logger with completion event types
  - [x] 1.1 Add CompletionLogEntry dataclass, COMPLETION_EVENT_TYPES set, and validation logic to `senzing-bootcamp/scripts/session_logger.py`
    - Add `COMPLETION_EVENT_TYPES = {"question", "answer", "action", "artifact"}`
    - Add `CompletionLogEntry` dataclass with fields: `event_type`, `module`, `timestamp`, `data`
    - Implement `build_completion_entry()` with validation: event_type in set, module 0–11, required data fields per event type
    - Implement `generate_question_id()` returning UUID4 hex prefix
    - Implement `truncate_field(value, max_length)` returning `value[:max_length]`
    - Implement `serialize_completion_entry()` producing compact JSON
    - Implement `append_completion_entry()` with directory creation and stderr warning on failure
    - Preserve existing `LogEntry`, `VALID_EVENTS`, and all existing functions for backward compatibility
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [x] 1.2 Write property test: Entry serialization produces valid schema-compliant JSON
    - **Property 1: Entry serialization produces valid schema-compliant JSON**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7**

  - [x] 1.3 Write property test: Invalid entries are rejected
    - **Property 2: Invalid entries are rejected**
    - **Validates: Requirements 6.7, 6.8**

  - [x] 1.4 Write property test: Truncation preserves prefix and enforces limit
    - **Property 3: Truncation preserves prefix and enforces limit**
    - **Validates: Requirements 1.9**

  - [x] 1.5 Write property test: Append-only JSONL integrity
    - **Property 4: Append-only JSONL integrity**
    - **Validates: Requirements 1.6**

- [x] 2. Checkpoint - Ensure session logger tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement Narrative Formatter
  - [x] 3.1 Create `senzing-bootcamp/scripts/generate_completion_summary.py` with narrative formatting logic
    - Implement `parse_session_log(log_path)` to read JSONL and return list of `CompletionLogEntry`
    - Implement `filter_secrets(text)` to remove key=value patterns where key contains sensitive terms (secret, password, token, key, credential, connection_string)
    - Implement `build_narrative(entries, progress_path, preferences_path)` to organize entries by module, pair questions/answers by question_id, compute cover metadata
    - Implement `render_markdown(narrative)` to produce the markdown document with cover section, summary statistics, and per-module narrative sections
    - Implement `write_narrative(output_path, content, max_size_bytes=512000)` with size limit enforcement via truncation of earliest entries
    - Handle missing session log (return error, do not write partial output)
    - Handle modules with no events (include with "unavailable" note)
    - Output path: `docs/completion_summary.md`, overwrite if exists
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10_

  - [x] 3.2 Write property test: Narrative sections ordered by module number ascending
    - **Property 5: Narrative sections are ordered by module number ascending**
    - **Validates: Requirements 4.1**

  - [x] 3.3 Write property test: Every module with events gets all four subsections
    - **Property 6: Every module with events gets all four subsections**
    - **Validates: Requirements 4.2**

  - [x] 3.4 Write property test: Question-answer pairing via question_id
    - **Property 7: Question-answer pairing via question_id**
    - **Validates: Requirements 4.3**

  - [x] 3.5 Write property test: Narrative metadata completeness
    - **Property 8: Narrative metadata completeness**
    - **Validates: Requirements 4.4, 4.5**

  - [x] 3.6 Write property test: Secret filtering removes sensitive key-value patterns
    - **Property 9: Secret filtering removes sensitive key-value patterns**
    - **Validates: Requirements 4.8**

  - [x] 3.7 Write property test: Narrative output respects 500 KB size limit
    - **Property 10: Narrative output respects 500 KB size limit**
    - **Validates: Requirements 4.10**

- [x] 4. Implement PDF Generator
  - [x] 4.1 Add PDF rendering functions to `senzing-bootcamp/scripts/generate_completion_summary.py`
    - Implement `ensure_fpdf2(timeout=30)` to attempt pip install with timeout, return bool
    - Implement `render_completion_pdf(narrative, output_path)` with cover page, per-module pages, monospace for code spans, numbered lists for Q&A, bulleted lists for actions/artifacts
    - Implement `generate_pdf_with_fallback(md_path, pdf_path)` orchestrating install check, rendering, and fallback messaging
    - Handle empty narrative content (inform bootcamper, no PDF generated)
    - Output to `docs/completion_summary.pdf` (separate from `docs/bootcamp_recap.pdf`)
    - Add argparse CLI with `--input`, `--output` flags and `main()` entry point
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 7.4_

  - [x] 4.2 Write unit tests for PDF generator
    - Test `ensure_fpdf2` returns True when fpdf2 available
    - Test `generate_pdf_with_fallback` returns fallback message when fpdf2 unavailable
    - Test empty narrative handling returns appropriate message
    - Test output path is separate from recap PDF
    - _Requirements: 5.5, 5.6, 5.7, 5.8, 5.9, 7.4_

- [x] 5. Checkpoint - Ensure narrative and PDF tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create Stopping Point Detection steering file
  - [x] 6.1 Create `senzing-bootcamp/steering/completion-summary-offer.md` with YAML frontmatter and detection rules
    - Define stopping point conditions: Module 7 completion, Module 11 completion, explicit stop request, track switch at boundary
    - Specify the summary offer message format: names "Completion Summary PDF", lists four content categories
    - Specify binary yes/no prompt requirement
    - Specify ordering: after celebration message, before export results offer (track completion); immediately after acknowledgment (mid-session stop)
    - Include guard against false positives: stop phrase embedded in longer substantive request should not trigger
    - Include guard against missing progress file: do not detect stopping point, log warning
    - Specify that offer is presented at every stopping point regardless of prior generation
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2, 7.3, 7.5_

- [x] 7. Create Integration Hook
  - [x] 7.1 Create `senzing-bootcamp/hooks/session-log-events.kiro.hook` as a postToolUse hook
    - Define hook JSON with `name`, `version`, `when` (postToolUse, toolTypes for write operations), and `then` (askAgent prompt)
    - Prompt instructs agent to log the completed tool action as a session log event using `append_completion_entry`
    - Ensure hook captures file create/modify/delete and MCP tool calls
    - _Requirements: 1.3, 1.4_

  - [x] 7.2 Write unit tests for hook file structure
    - Validate hook JSON schema (name, version, when, then fields present)
    - Validate toolTypes configuration
    - _Requirements: 1.3, 1.4_

- [x] 8. Wire components together and add integration tests
  - [x] 8.1 Add integration test for full pipeline in `senzing-bootcamp/tests/test_completion_summary_integration.py`
    - Test end-to-end: log events → parse session log → build narrative → render markdown → verify output
    - Test steering file content matches requirements (offer text includes four categories, binary prompt)
    - Test hook file structure is valid JSON with required fields
    - Test that `docs/completion_summary.pdf` path does not collide with `docs/bootcamp_recap.pdf`
    - _Requirements: 3.2, 5.1, 7.3, 7.4_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The design explicitly uses Python — no language selection needed
- All property tests go in `senzing-bootcamp/tests/test_completion_summary_properties.py`
- Unit/integration tests go in `senzing-bootcamp/tests/test_completion_summary_unit.py` and `test_completion_summary_integration.py`
- Existing `session_logger.py` functions must remain unchanged for backward compatibility
- fpdf2 is the only external dependency (consistent with existing `generate_recap_pdf.py` pattern)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "1.4", "1.5"] },
    { "id": 2, "tasks": ["3.1", "6.1", "7.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "4.1", "7.2"] },
    { "id": 4, "tasks": ["4.2", "8.1"] }
  ]
}
```
