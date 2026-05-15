# Implementation Plan: TypeScript/Node.js Language Maturity Alignment

## Overview

This plan implements documentation-only changes to improve TypeScript/Node.js language support accuracy across the senzing-bootcamp power. The work involves updating four steering files with maturity notes, TypeScript-specific pitfalls, and support depth disclaimers, then writing property-based and unit tests to validate the changes.

## Tasks

- [x] 1. Add maturity notes to lang-typescript.md and POWER.md
  - [x] 1.1 Add SDK Maturity Notes section to lang-typescript.md
    - Add a new `## SDK Maturity Notes` section after the existing `## Common Environment Issues` section
    - Include the blockquote noting that TypeScript/Node.js SDK support may have fewer `find_examples` results compared to Python and Java
    - Note that `generate_scaffold` and `sdk_guide` produce equivalent-quality output for all supported workflows
    - Include guidance to use `search_docs` or ask for help if a gap is encountered
    - _Requirements: 2_

  - [x] 1.2 Add language support depth note to POWER.md Code Generation section
    - Add a note after the existing paragraph in the `## Code Generation` section
    - Acknowledge that supplementary example coverage (via `find_examples`) varies across languages
    - Clarify that Python and Java currently have the most extensive example coverage
    - State this does not affect `generate_scaffold` or `sdk_guide` output quality
    - _Requirements: 2_

- [x] 2. Add TypeScript/Node.js pitfalls section to common-pitfalls.md
  - [x] 2.1 Add TypeScript/Node.js Pitfalls section to common-pitfalls.md
    - Add a new `## TypeScript/Node.js Pitfalls` section in `common-pitfalls.md`
    - Add to the Quick Navigation links at the top of the file
    - Use the standard pitfall table format (`| Pitfall | Fix |`)
    - Include entries covering: async patterns (unhandled promise rejections, blocking event loop), type definitions (using `any` for Senzing data, strict mode issues), and ESM/CJS module resolution (import/require mismatches)
    - _Requirements: 4_

- [x] 3. Update onboarding-flow.md with support depth disclaimer
  - [x] 3.1 Add support depth disclaimer to onboarding-flow.md Step 2
    - Add a blockquote note after the language selection presentation in Step 2 (Programming Language Selection)
    - Use the format specified in the design: note that all languages produce working code via `generate_scaffold`, but `find_examples` depth varies
    - Clarify that Python and Java have the most extensive example coverage and this does not affect the bootcamp workflow
    - _Requirements: 6_

- [x] 4. Verify lang-typescript.md Platform Notes section completeness
  - [x] 4.1 Verify and update Platform Notes section in lang-typescript.md
    - Audit the existing `## Platform Notes` section for coverage of Linux, Windows, and macOS
    - Ensure each platform has at least one specific note (library paths, build tools, DLL loading)
    - Add any missing platform-specific notes discovered during audit (e.g., Node.js version requirements, native module compilation per platform)
    - _Requirements: 5_

- [x] 5. Checkpoint - Verify all steering file changes
  - Ensure all modified files pass CommonMark validation (`python3 senzing-bootcamp/scripts/validate_commonmark.py`), ask the user if questions arise.

- [x] 6. Write property-based and unit tests
  - [x] 6.1 Create test file with Property 1: Language steering file structural parity
    - Create `senzing-bootcamp/tests/test_typescript_language_maturity.py`
    - Implement Property 1 using Hypothesis `@given` with `st.sampled_from` over the set of language files {lang-python.md, lang-java.md, lang-csharp.md, lang-rust.md, lang-typescript.md}
    - Verify each file contains all required section headings: `## Senzing SDK Best Practices`, `## Common Pitfalls`, `## Performance Considerations`, `## Code Style for Generated Code`, `## Platform Notes`, `## Common Environment Issues`
    - Verify the Platform Notes section references Linux, Windows, and macOS
    - Use `@settings(max_examples=20)` per project conventions
    - **Property 1: Language steering file structural parity**
    - **Validates: Requirements 1, 5**

  - [x] 6.2 Write property test for Property 2: Maturity notes presence
    - Add Property 2 test class to the same test file
    - Use Hypothesis `@given` with `st.sampled_from` over {lang-typescript.md, POWER.md}
    - Verify each file contains a support depth or maturity note acknowledging varying `find_examples` coverage
    - Use regex to match key phrases: `find_examples`, coverage/maturity/depth language
    - **Property 2: Maturity notes presence in designated files**
    - **Validates: Requirements 2**

  - [x] 6.3 Write property test for Property 3: TypeScript pitfall topic coverage
    - Add Property 3 test class to the same test file
    - Use Hypothesis `@given` with `st.sampled_from` over required topics {async patterns, type definitions, ESM/CJS module resolution}
    - Verify `common-pitfalls.md` TypeScript/Node.js section contains an entry addressing each topic
    - Use regex patterns to match topic keywords in the pitfall table
    - **Property 3: TypeScript pitfall topic coverage**
    - **Validates: Requirements 4**

  - [x] 6.4 Write unit test for onboarding disclaimer presence
    - Add a unit test class verifying `onboarding-flow.md` Step 2 contains the support depth disclaimer
    - Check for key phrases: `find_examples`, `generate_scaffold`, coverage variation language
    - _Requirements: 6_

  - [x] 6.5 Write unit test for common-pitfalls.md TypeScript section heading
    - Add a unit test verifying `common-pitfalls.md` contains a `## TypeScript/Node.js Pitfalls` heading
    - _Requirements: 4_

- [x] 7. Final checkpoint - Ensure all tests pass
  - Run `pytest senzing-bootcamp/tests/test_typescript_language_maturity.py -v` and ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties across all language files
- Unit tests validate specific content presence and format in individual files
- The implementation is documentation-only — all changes are to Markdown steering files
- Tests use Python (pytest + Hypothesis) per project conventions

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "3.1", "4.1"] },
    { "id": 1, "tasks": ["6.1"] },
    { "id": 2, "tasks": ["6.2", "6.3", "6.4", "6.5"] }
  ]
}
```
