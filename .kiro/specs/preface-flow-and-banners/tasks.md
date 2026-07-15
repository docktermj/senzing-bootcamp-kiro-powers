# Implementation Plan: Preface Flow and Banners

## Overview

Edit onboarding and graduation steering files to add the ENTITY RESOLUTION CONCEPTS and GRADUATION banners and to reorder the preface (track before language, language after the welcome banner, any-questions after language). Then update and add tests to lock in the corrected behavior. All banners use the 56-`━` / triple-emoji pattern from `module-transitions.md`.

## Tasks

- [x] 1. Add the ENTITY RESOLUTION CONCEPTS banner
  - Prepend the ER_Concepts_Banner (`🧩🧩🧩  ENTITY RESOLUTION CONCEPTS  🧩🧩🧩`, 56 `━` borders, in a ` ```text ` fenced block) as the first presented output of `steering/entity-resolution-intro.md`.
  - Add an agent note that the banner is shown once per Preface run and NOT re-shown when a follow-up question re-presents the exploration gate.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2. Reorder the preface sequence
  - [x] 2.1 Remove Language_Selection from phase 1b
    - Cut the Step 4 "Programming Language Selection" block (including its ⛔ gate and `🛑 STOP` directives) from `steering/onboarding-phase1b-intro-language.md`.
    - Renumber the remaining phase-1b steps (Welcome_Banner + overview, Detail_Level_Step) and update the handoff pointer at the bottom of the file.
    - _Requirements: 3.2, 3.6, 5.2, 5.3_
  - [x] 2.2 Move the Any_Questions_Step out of phase 1b
    - Relocate the comprehension check (Step 5b / Any_Questions_Step) so it is presented AFTER Language_Selection.
    - _Requirements: 3.1, 3.4_
  - [x] 2.3 Insert Language_Selection after Track_Selection in phase 2
    - In `steering/onboarding-phase2-track-setup.md`, place the Language_Selection block immediately after Track_Selection, preserving its ⛔ gate verbatim and its "load the language steering file on confirmation" and "persist to preferences" behavior.
    - Place the Any_Questions_Step after Language_Selection.
    - Keep Advanced_Knowledge_Check as the final step before Module 1.
    - _Requirements: 3.1, 3.3, 3.4, 3.5, 3.7, 5.1, 5.2, 5.3_
  - [x] 2.4 Update the flow summary and cross-references
    - Update the "Sequence:" line and Phase Sub-File pointers in `steering/onboarding-flow.md` to reflect the new order and step ownership.
    - Add a one-line note at the top of each phase file clarifying its (historical) name vs. current contents.
    - Update the missing-field prompt ordering note in `steering/session-resume.md` to match the new capture order.
    - _Requirements: 3.1, 5.5_

- [x] 3. Add the GRADUATION banner
  - [x] 3.1 Add the Graduation_Banner to the graduation workflow
    - Display the Graduation_Banner (`🎓🎓🎓  GRADUATION  🎓🎓🎓`, 56 `━` borders, ` ```text ` fenced block) at the start of the graduation celebration output in `steering/graduation.md`, before Step 0, without altering artifact guarantees or the mandatory closing question.
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.4_
  - [x] 3.2 Add the Graduation_Banner to the track-completion celebration
    - Display the Graduation_Banner at the start of the Path Completion Celebration in `steering/module-completion-track.md`, so a bootcamper who declines graduation or has `skip_graduation` set still sees it exactly once.
    - _Requirements: 2.1, 2.4, 2.5, 4.1, 4.2, 4.3, 5.4_

- [x] 4. Update and add tests
  - [x] 4.1 Update onboarding sequence/ownership tests
    - Update `test_onboarding_question_ownership.py`, `test_comprehension_check.py`, `test_onboarding_split_preservation.py`, `test_remove_duplicate_module_table.py`, `test_onboarding_session_ux.py`, `test_version_unit.py`, and `test_module_closing_question_ownership.py` to assert the reordered sequence (Track before Language; Language after Welcome_Banner; Any_Questions after Language).
    - _Requirements: 6.1, 6.4_
  - [x] 4.2 Add banner-presence tests
    - Add assertions that the ER_Concepts_Banner appears at the start of `entity-resolution-intro.md` and the Graduation_Banner appears in both `graduation.md` and `module-completion-track.md`, each with 56 `━` borders and the correct title.
    - _Requirements: 6.2, 6.3_
  - [x] 4.3 Add a relative-order test
    - Add a test asserting the Track_Selection prompt precedes the Language_Selection prompt, and the Language_Selection prompt precedes the Any_Questions_Step, across the phase files.
    - _Requirements: 3.1, 3.3, 3.4, 6.1_

- [x] 5. Checkpoint - Verify
  - Grep each edited steering file for the banner literals (correct title, 56 `━`, correct emoji) at the intended locations, exactly once each.
  - Run `python -m pytest senzing-bootcamp/tests/` and confirm green.
  - Run `python3 senzing-bootcamp/scripts/validate_commonmark.py` on edited Markdown.
  - Trace the phase files end-to-end to confirm the target sequence.
  - _Requirements: 3.1, 6.4_

## Notes

- Language selection now lives in the track-setup phase file; file names are intentionally NOT renamed to avoid rippling `#[[file:]]` and fixture changes (see design Decision).
- All gate markers (⛔, 🛑 STOP) move with their steps unchanged — this is a reorder, not a semantics change.
- Coordinate with any conversational-eval harness that encodes onboarding order if it is run in CI.
