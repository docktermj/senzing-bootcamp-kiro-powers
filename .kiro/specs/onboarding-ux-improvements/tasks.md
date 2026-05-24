# Implementation Plan: Onboarding UX Improvements

## Overview

Two targeted content edits to existing steering files: (1) add a hook files explanatory note as the last bullet in Step 4 of `onboarding-flow.md`, and (2) add a mandatory exploration gate at the end of `entity-resolution-intro.md`. Both are additive markdown insertions with no new files or infrastructure.

## Tasks

- [ ] 1. Add Hook Files Note to onboarding-flow.md
  - [ ] 1.1 Insert hook files explanatory bullet in Step 4 Overview
    - Open `senzing-bootcamp/steering/onboarding-flow.md`
    - Insert a new bullet point as the last item in the Step 4 overview list, after the "unfamiliar terms" bullet and before `### 4a`
    - The bullet must inform the bootcamper that hook files (`.kiro.hook` files) appearing in the editor panel are automated quality checks running in the background
    - The bullet must state hook files do not require review, can be safely closed, but must not be deleted
    - No ⛔ or 🛑 markers — the flow continues seamlessly to section 4a
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 1.2 Write pytest tests for hook files note placement and content
    - Create `senzing-bootcamp/tests/test_onboarding_ux_improvements.py`
    - Test that the hook files note appears after the "unfamiliar terms" bullet and before `### 4a`
    - Test that the note mentions automated quality checks, safe to close, and must not delete
    - Test that no ⛔ or 🛑 markers exist between the hook files note and `### 4a`
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Checkpoint - Verify hook files note
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Add Exploration Gate to entity-resolution-intro.md
  - [ ] 3.1 Insert mandatory exploration gate section
    - Open `senzing-bootcamp/steering/entity-resolution-intro.md`
    - Insert a new `## Explore Further` section after the "What entity resolution produces" section content and before the `## Sources` comment block
    - Include an HTML comment block (`<!-- AGENT INSTRUCTION -->`) with handling rules for follow-up questions, readiness signals, and ambiguous responses
    - The agent instruction must specify using `search_docs` from the Senzing MCP server to answer questions
    - The agent instruction must specify re-presenting the gate after answering a question
    - Include the ⛔ **MANDATORY GATE** marker with introductory text
    - Include three example questions: "How does Senzing match records without rules?", "What's the difference between matching and relating?", "What kinds of data does entity resolution work with?"
    - Include the 🛑 **STOP** instruction at the end
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 3.2 Write pytest tests for exploration gate placement and content
    - Add tests to `senzing-bootcamp/tests/test_onboarding_ux_improvements.py`
    - Test that the ⛔ gate exists after the "What entity resolution produces" section and before the Sources comment
    - Test that the gate contains all three example questions
    - Test that the gate contains agent instructions for MCP usage (`search_docs`)
    - Test that the gate contains the 🛑 stop instruction
    - Test that the agent instruction handles ambiguous responses (treats as follow-up question)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [ ] 4. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Both changes are purely additive markdown content — no new files, scripts, or infrastructure
- The hook files note is a standard bullet point matching the existing Overview_Bullets format
- The exploration gate follows the established `⛔ MANDATORY GATE` pattern from `onboarding-flow.md`
- Tests use pytest and parse the markdown files to verify content placement and structure

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "3.1"] },
    { "id": 1, "tasks": ["1.2", "3.2"] }
  ]
}
```
