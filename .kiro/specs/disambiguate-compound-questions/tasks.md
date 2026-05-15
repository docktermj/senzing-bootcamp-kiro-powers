# Implementation Plan

## Phase 1: Write Test First

- [x] 1. Create compound question detection test
  - Create `senzing-bootcamp/tests/test_question_disambiguation.py`
  - Implement `TestQuestionDisambiguation` class with `_find_compound_questions()` scanner
  - Pattern: question mark followed within 80 chars by a question-starting word (Does, Is, Are, Would, Should, Could, Can, Will, Anything, Or)
  - Only scan 👉 question blocks (not code blocks, not "WRONG" violation examples)
  - Test method: `test_no_compound_questions_in_steering_files`
  - Clear failure messages: file name, line number, offending text
  - This test will FAIL initially (compound questions exist in steering files)
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

## Phase 2: Protocol and Rule Updates

- [x] 2. Add Question Disambiguation section to conversation-protocol.md
  - Add new section after "Choice Formatting" and before "Violation Examples"
  - Define the Compound_Question anti-pattern
  - State the confirmation-first pattern: confirm alone → if no → ask what to change
  - Prohibit appending "or should we adjust?" / "Anything I missed?" to confirmations
  - Prohibit combining "Would you like X?" with "Or would you prefer Y?" in prose
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 3. Add compound question violation examples to conversation-protocol.md
  - Add "Compound Confirmation (WRONG)" example: "Does that summary sound right? Anything I missed or got wrong?"
  - Add "Compound Confirmation (CORRECT)" example: "Does that summary capture your situation accurately?"
  - Add "Compound Either/Or (WRONG)" example: "Would you like me to create a summary, or would you prefer to skip that and move on?"
  - Add "Compound Either/Or (CORRECT)" example: numbered choice list
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 4. Add disambiguation bullet to agent-instructions.md Communication section
  - Add bullet: "Every 👉 question must have one unambiguous meaning for 'yes' and one for 'no.' Never append a follow-up question to a confirmation (see conversation-protocol.md Question Disambiguation). When both confirmation and correction are needed: confirm first, ask for corrections only if the answer is no."
  - Place after the existing "Never combine questions with conjunctions" bullet
  - _Requirements: 5.1, 5.2, 5.3_

## Phase 3: Steering File Audit and Rewrites

- [x] 5. Audit all steering files for compound questions
  - Run the test from Task 1 to get the initial list of violations
  - Additionally scan manually for patterns the regex might miss: "? Or ", "? Does ", "? Should "
  - Document all findings: file, step number, original text, proposed rewrite
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 6. Rewrite compound questions in module-01-business-problem.md
  - Step 9: Change `Does that sound right? Anything I missed or got wrong?"` to `Does that summary capture your situation accurately?"`
  - Preserve the 🛑 STOP marker and question_pending behavior
  - Verify "yes" = confirmed, "no" = needs changes (agent asks what to fix next turn)
  - _Requirements: 3.1, 3.3, 3.4_

- [x] 7. Rewrite compound questions in module-01-phase2-document-confirm.md
  - Step 16: Change `"Does this accurately capture your problem? Does the [pattern name] pattern seem like a good fit, or should we adjust anything?"` to `"Does this accurately capture your problem and approach?"`
  - Preserve the 🛑 STOP marker and question_pending behavior
  - Verify "yes" = confirmed, "no" = needs changes (agent asks what to fix next turn)
  - _Requirements: 3.2, 3.3, 3.4_

- [x] 8. Rewrite compound questions in remaining steering files
  - Fix all other violations identified in the audit (Task 5)
  - Each rewrite follows the same pattern: single unambiguous question, one meaning for yes, one for no
  - For either/or questions: convert to numbered choice lists
  - Preserve all 🛑 STOP markers and checkpoint behavior
  - _Requirements: 4.4, 4.5_

## Phase 4: Verification

- [x] 9. Verify disambiguation test passes
  - Run: `pytest senzing-bootcamp/tests/test_question_disambiguation.py -v`
  - Test should now PASS (zero compound questions found)
  - If any false positives remain, add to allowlist with justification comment
  - _Requirements: 6.3_

- [x] 10. Run full CI validation
  - Run: `python3 senzing-bootcamp/scripts/validate_commonmark.py`
  - Run: `python3 senzing-bootcamp/scripts/measure_steering.py --check`
  - Run: `pytest senzing-bootcamp/tests/ -v` (full test suite)
  - All must pass
  - Update `steering-index.yaml` token counts if any file changed significantly
  - _Requirements: 7.1, 7.2, 7.3, 7.4_
