# Implementation Plan: Multi-Language Entity Resolution Guide

## Overview

Create a documentation guide covering multi-language entity resolution with Senzing, integrate it into the Module 5 steering cross-reference and the guides README. All deliverables are Markdown files authored using MCP-sourced Senzing content. Tests are example-based pytest validations of file structure, content presence, and cross-references.

## Tasks

- [x] 1. Create the multi-language guide document
  - [x] 1.1 Create `docs/guides/MULTI_LANGUAGE_DATA.md` with level-1 heading and introduction
    - Create the file at `senzing-bootcamp/docs/guides/MULTI_LANGUAGE_DATA.md`
    - Open with `# Multi-Language Entity Resolution` heading
    - Write an introductory paragraph explaining why multi-language data presents unique challenges for ER (customer databases spanning multiple countries, compliance screening across jurisdictions)
    - Follow the same heading and layout conventions as `DATA_UPDATES_AND_DELETIONS.md` and `QUALITY_SCORING_METHODOLOGY.md`
    - _Requirements: 1.1, 1.2, 1.3_

  - [x] 1.2 Write the Non-Latin Character Support section
    - Add `## Non-Latin Character Support` section
    - Explain how Senzing processes non-Latin characters natively without requiring pre-translation
    - Use `search_docs` to retrieve supported script families for name matching
    - Explain how Senzing stores and indexes names in original script alongside transliterated forms
    - Include at least one SGES JSON example with `NAME_FULL` in Chinese or Arabic containing non-ASCII characters and standard SGES attributes (`DATA_SOURCE`, `RECORD_ID`, `NAME_FULL`)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 6.1_

  - [x] 1.3 Write the UTF-8 Encoding Requirements section
    - Add `## UTF-8 Encoding Requirements` section
    - Explain that Senzing requires all input data to be UTF-8 encoded
    - Describe common encoding problems: Latin-1, Shift-JIS, GB2312, BOM, mojibake from double-encoding
    - Provide a checklist of steps to verify and convert file encoding with CLI examples (e.g., `file`, `iconv`, `chardet`)
    - Use `search_docs` to document Senzing's behavior on invalid UTF-8 input
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.1_

  - [x] 1.4 Write the Transliteration and Cross-Script Name Matching section
    - Add `## Transliteration and Cross-Script Name Matching` section
    - Explain Senzing's transliteration and cross-script matching capabilities using `search_docs` for technical details
    - Include at least three cross-script matching examples with different script pairs:
      - Latin/Chinese pair (e.g., "John Smith" / "约翰·史密斯")
      - Latin/Cyrillic pair
      - Latin/Arabic pair
    - Explain limitations — scenarios where automatic matching may not succeed
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 6.1, 6.2_

  - [x] 1.5 Write the Multi-Language Data Quality Best Practices section
    - Add `## Multi-Language Data Quality Best Practices` section
    - Recommend preserving original-script names rather than pre-transliterating
    - Describe using multiple `NAME_FULL` attributes for original + transliterated forms
    - Address multi-language data quality issues: inconsistent romanization, mixed-script fields, honorifics
    - Explain how Module 5 quality scoring applies to multi-language data
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 1.6 Write the Further Reading section
    - Add `## Further Reading` section
    - Include `search_docs` references with example queries (e.g., "globalization", "transliteration", "multi-language")
    - Direct bootcampers to use `search_docs` for the latest Senzing documentation on multi-language support
    - _Requirements: 6.3_

- [x] 2. Add Module 5 cross-reference and Guides README entry
  - [x] 2.1 Add cross-reference in Module 5 steering file
    - Edit `senzing-bootcamp/steering/module-05-data-quality-mapping.md`
    - Add a callout block referencing `docs/guides/MULTI_LANGUAGE_DATA.md` as optional supplementary reading
    - Place it in the existing reference block alongside the `QUALITY_SCORING_METHODOLOGY.md` reference
    - Describe the guide as covering UTF-8 encoding, non-Latin character support, cross-script name matching, and multi-language data quality best practices
    - Frame as optional — not a required step in the Module 5 workflow
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 2.2 Add entry in Guides README
    - Edit `senzing-bootcamp/docs/guides/README.md`
    - Add `MULTI_LANGUAGE_DATA.md` entry in the "Reference Documentation" section with filename as Markdown link, bold title, and 2-3 line description covering non-Latin character support, UTF-8 encoding, cross-script name matching, and multi-language data quality best practices
    - Add `MULTI_LANGUAGE_DATA.md` to the Documentation Structure tree in alphabetical position under `guides/`
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 3. Checkpoint - Validate guide content and integration
  - Ensure all JSON code blocks in the guide are valid JSON
  - Ensure the guide file is valid UTF-8
  - Verify all Markdown links resolve to existing files
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Write example-based pytest tests
  - [x] 4.1 Create test file `senzing-bootcamp/tests/test_multi_language_guide.py`
    - Create the test module with class-based organization following existing test patterns (see `test_incremental_loading_guide.py`)
    - Include helper functions to locate and read the guide, README, and steering files
    - _Requirements: 1.1_

  - [x] 4.2 Write guide structure tests
    - Test that `MULTI_LANGUAGE_DATA.md` exists at the expected path
    - Test that the file starts with a level-1 heading
    - Test that all required section headings are present (Non-Latin Character Support, UTF-8 Encoding Requirements, Transliteration and Cross-Script Name Matching, Multi-Language Data Quality Best Practices, Further Reading)
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1, 4.1, 5.1, 6.3_

  - [x] 4.3 Write content validation tests
    - Test that at least one JSON code block contains non-ASCII characters and SGES attributes (`DATA_SOURCE`, `RECORD_ID`, `NAME_FULL`)
    - Test that at least three cross-script matching examples exist with different script pairs
    - Test that the Further Reading section contains `search_docs` references
    - Test that all JSON code blocks in the guide are valid JSON
    - Test that the guide file is valid UTF-8
    - _Requirements: 2.4, 3.3, 4.3, 6.2, 6.3_

  - [x] 4.4 Write cross-reference and README integration tests
    - Test that `module-05-data-quality-mapping.md` references `MULTI_LANGUAGE_DATA.md` as optional supplementary reading
    - Test that `README.md` contains `MULTI_LANGUAGE_DATA.md` in the Reference Documentation section with a Markdown link
    - Test that `README.md` includes `MULTI_LANGUAGE_DATA.md` in the Documentation Structure tree
    - Test that the README entry mentions key topics (non-Latin, UTF-8, cross-script)
    - _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.3_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Run `pytest senzing-bootcamp/tests/test_multi_language_guide.py -v` and verify all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This feature is pure documentation — no application code, no runtime behavior
- All Senzing technical content must be sourced from `search_docs` MCP tool, not training data
- Property-based testing does not apply (no computable properties)
- The existing CI pipeline (`validate_commonmark.py`, `measure_steering.py --check`) will automatically validate the new and modified Markdown files
- Tests follow the same pattern as `test_incremental_loading_guide.py`
