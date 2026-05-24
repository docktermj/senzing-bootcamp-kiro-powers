# Implementation Plan:

## Overview

This plan implements the module-recap-document feature: a running recap file appended at each module completion, plus a PDF generation script for graduation. Tasks are ordered to build the core script first, then tests, then the hook and steering integrations.

## Tasks

- [x] 1. Create `senzing-bootcamp/scripts/generate_recap_pdf.py` with `main()` entry point and argparse CLI accepting `--input` and `--output` arguments with defaults (`docs/bootcamp_recap.md` and `docs/bootcamp_recap.pdf`)
- [x] 2. Implement markdown parser in `generate_recap_pdf.py` using stdlib `re` module to extract RecapHeader (bootcamper, started, total_duration) and RecapSection (module_number, module_name, timestamp, information_shared, questions_asked, answers_given, actions_taken, duration) dataclasses
- [x] 3. Implement PDF renderer in `generate_recap_pdf.py` using `fpdf2` that generates a cover page (title, bootcamper name, dates, duration) and per-module pages with formatted headings, lists, and code blocks
- [x] 4. Implement graceful error handling in `generate_recap_pdf.py`: exit code 1 with clear messages for missing fpdf2, missing input file, empty file, and write failures; exit code 0 with success message on completion
- [x] 5. Create `senzing-bootcamp/tests/test_generate_recap_pdf.py` with Hypothesis strategies for generating valid RecapHeader and RecapSection data
- [x] 6. Write property test: markdown parser correctly extracts all module sections from generated recap content (structural completeness) [PBT]
- [x] 7. Write property test: all timestamps in parsed output match ISO 8601 format with timezone [PBT]
- [x] 8. Write property test: question-answer pairing integrity — output preserves 1:1 Q&A correspondence [PBT]
- [x] 9. Write property test: round-trip — format recap data to markdown, parse it back, verify structural equivalence [PBT]
- [x] 10. Write property test: appending a new RecapSection preserves all existing file content byte-for-byte [PBT]
- [x] 11. Write property test: total duration is monotonically non-decreasing across sequential appends [PBT]
- [x] 12. Write property test: module sections appear in chronological order of completion timestamps [PBT]
- [x] 13. Write edge case tests: empty sections, special markdown characters, unicode content, very long content
- [x] 14. Create `senzing-bootcamp/hooks/module-recap-append.kiro.hook` as a `postTaskExecution` hook with prompt instructions for detecting module completion, gathering session content, and appending a structured Recap_Section to `docs/bootcamp_recap.md`
- [x] 15. Add "Recap Append" section to `senzing-bootcamp/steering/module-completion.md` between the existing progress update reference and the "Bootcamp Journal" section, documenting the non-blocking recap workflow
- [x] 16. Add "Step 0: Recap PDF Generation" section to `senzing-bootcamp/steering/graduation.md` after pre-checks and before Step 1, documenting the PDF generation step with error handling
- [x] 17. Verify the hook JSON is valid, the PDF script passes ruff linting, and the full test suite passes without regressions

## Task Dependency Graph

```json
{
  "waves": [
    {"tasks": [1]},
    {"tasks": [2]},
    {"tasks": [3]},
    {"tasks": [4]},
    {"tasks": [5, 14]},
    {"tasks": [6, 7, 8, 9, 10, 11, 12, 13, 15, 16]},
    {"tasks": [17]}
  ]
}
```

## Notes

- The PDF script uses `fpdf2` as an optional dependency — this is the one exception to the "stdlib only" rule, justified because PDF generation genuinely requires it. The script exits gracefully if `fpdf2` is not installed.
- Property-based tests (marked [PBT]) use Hypothesis to generate arbitrary valid recap data and verify invariants hold.
- The hook and steering changes are agent-facing (they instruct the agent what to do at module completion) — they don't execute Python code directly.
- Tasks 6-12 can be implemented in parallel once task 5 is complete.
