# Implementation Plan

This bugfix is steering-driven — the defect lives in the steering files and the
oracle fixtures that encode expected agent behavior, not in an application code
path. The tasks therefore follow the bugfix **observation-first** methodology:
surface counterexamples that demonstrate the bug on the UNFIXED steering /
fixture tree first (tasks 1 and 2), record the behavior to preserve (task 3),
then apply the fix (task 4) and verify fix + preservation (task 4 sub-tasks and
task 5).

Ground rules for every task:

- Python 3.11+, stdlib only (harness + tests). pytest + Hypothesis for
  property-based tests. Do NOT set `@settings(max_examples=...)` to restate the
  baseline — the active Hypothesis profile (`fast`=5 default, `thorough`=100 in
  CI) supplies the baseline count; add an inline override only when a test needs
  a non-baseline depth.
- Steering files are Markdown with YAML frontmatter under
  `senzing-bootcamp/steering/`.
- The harness engine `senzing-bootcamp/scripts/eval_conversations.py` is NOT
  modified — it is the guiding constraint. Its `ends_with_question_then_stop`
  predicate already treats a turn ending on the 👉 line as correctly bounded,
  and `_is_boundary_line` still accepts a `🛑 STOP` line when one is present.
- The full shipped-fixture harness command is
  `python senzing-bootcamp/scripts/eval_conversations.py` and must exit 0. The
  CI pytest suite over `senzing-bootcamp/tests/` and `tests/` must stay green so
  the conversational-eval-harness CI step remains at exit code 0.

---

- [x] 1. Write bug-condition exploration test for the marker leak (BEFORE any fix)
  - **Property 1: Bug Condition** - Clean Question, No Leaked Internal Markers
  - **CRITICAL**: This test MUST FAIL on the UNFIXED steering / fixture tree — the failure confirms the bug (C1) exists.
  - **DO NOT attempt to fix the test or the steering when it fails** — the failure is the expected, correct outcome for this task.
  - **NOTE**: This test encodes the expected behavior (`expectedBehavior`) — it validates the fix when it passes in task 4.5.
  - **GOAL**: Surface counterexamples showing a `🛑 STOP` / `⛔ MANDATORY GATE` line rendered beside the 👉 question.
  - **Scoped PBT Approach**: This bug is deterministic per rendered turn, so scope the property to the concrete observed failing cases — the onboarding language-selection turn (`onboarding-phase1b-intro-language.md`: `🛑 STOP — Wait ...` and `⛔ **MANDATORY GATE** — ...`) and the Module 3 visualization gate (`module3_gate_not_bypassed.json`) — while still generating over the transcript-text domain via Hypothesis.
  - Author an exploration fixture (or inline transcript) that reproduces the CURRENT rendered turn: a 👉 question followed by a rendered `🛑 STOP` line, plus a gate turn rendering `⛔ MANDATORY GATE`.
  - Attach the fixed-behavior assertions and evaluate them via the harness predicates: `absent_marker "🛑"`, `absent_marker "⛔"`, `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer` (mirrors `expectedBehavior(result)` in the design).
  - Complement with the existing content-assertion tests (`test_bold_question_steering.py::test_protocol_stop_marker_is_plain`, `test_examples_stop_marker_is_plain`) to enumerate every rendered-marker occurrence across the steering set.
  - Run the exploration test on the UNFIXED tree.
  - **EXPECTED OUTCOME**: Test FAILS with `prohibited marker '🛑' present in turn` / `prohibited marker '⛔' present in turn` — this proves C1 exists.
  - Document the counterexamples found (e.g., "language-selection turn renders `🛑 STOP — Wait ...` after the 👉 question"; "gate turn renders `⛔ **MANDATORY GATE** — ...`").
  - Mark complete when the test is written, run, and the failure is documented.
  - _Bug_Condition: isBugCondition(X) C1 branch — hasQuestion AND leaksMarker("🛑" | "⛔" | "MANDATORY GATE")_
  - _Expected_Behavior: expectedBehavior(result) — exactly one 👉, ends on question, NOT contains "🛑"/"⛔"_
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 2. Write bug-condition exploration test for the duplicate question (BEFORE any fix)
  - **Property 2: Bug Condition** - Question Shown Exactly Once
  - **CRITICAL**: This test MUST FAIL on the UNFIXED tree — the failure confirms the bug (C2) exists.
  - **DO NOT attempt to fix the test or the steering when it fails.**
  - **NOTE**: This test encodes the expected behavior — it validates the fix when it passes in task 4.6.
  - **GOAL**: Surface the counterexample where the comprehension-check question reaches the bootcamper twice (a prose "or" compound composed first, then a regenerated clean question).
  - **Scoped PBT Approach**: Scope the property to the concrete observed case — the pre-track comprehension check — while generating over the transcript-text domain.
  - Author an exploration fixture (or inline transcript) modeling the CURRENT behavior: a turn where the compound `"Does everything make sense so far, or is there anything you'd like me to clarify?"` and its regenerated clean single question both appear.
  - Attach the fixed-behavior assertions via the harness predicates: `exactly_one_pointer` and `no_compound_question` (a clean, single, non-compound 👉 question shown exactly once).
  - Run the exploration test on the UNFIXED tree.
  - **EXPECTED OUTCOME**: Test FAILS (`expected exactly one pointer, found >1` and/or `compound question detected`) — this proves C2 exists.
  - Document the counterexample (e.g., "comprehension-check question rendered twice: the 'or ... clarify?' compound and its regeneration").
  - Mark complete when the test is written, run, and the failure is documented.
  - _Bug_Condition: isBugCondition(X) C2 branch — duplicated OR composedCompoundFirst AND regeneratedQuestionAlreadyShown_
  - _Expected_Behavior: expectedBehavior(result) — count_pointers == 1, NOT hasCompoundQuestion, questionShownExactlyOnce_
  - _Requirements: 1.4, 1.5, 2.4, 2.5_

- [x] 3. Write preservation property tests (BEFORE implementing the fix)
  - **Property 3: Preservation** - Turn Boundary, Gate, One Question Rule, and Harness Unchanged
  - **IMPORTANT**: Follow the observation-first methodology — run the UNFIXED tree first, record actual outputs, then assert those observed outputs.
  - Observe on the UNFIXED harness engine: `ends_with_question_then_stop` passes for a turn ending on the 👉 line (empty trailing) AND for a turn ending on a `🛑 STOP` boundary line — record both.
  - Observe on the UNFIXED tree: `module3_gate_not_bypassed.json` passes `gate_not_bypassed` via non-marker execution evidence ("Your visualization is running", "Checkpoint written: module_3_verification..."), not only via the `🛑 STOP` boundary — record this.
  - Observe: every shipped fixture ends with exactly one 👉 question (`exactly_one_pointer` / One Question Rule / leading-question guarantee) — record.
  - Observe: the preserved internal-directive presence tests pass (`test_business_case_offer_steering.py`, `test_licensing_guidance.py`, `test_module2_license_acquisition_info.py`) — record.
  - Observe: a turn that re-displays a question at the bootcamper's explicit request is NOT a duplicate violation (edge case, C(X) false) — record.
  - Write property-based tests (Hypothesis) capturing these observed patterns across the transcript-text domain: the harness predicates behave identically for all non-bug-condition inputs; the engine is unmodified; the full shipped-fixture run exits 0.
  - Run the preservation tests on the UNFIXED tree.
  - **EXPECTED OUTCOME**: Tests PASS (this confirms the baseline behavior to preserve).
  - Mark complete when the tests are written, run, and passing on the unfixed tree.
  - _Bug_Condition: NOT isBugCondition(X) — non-question turns, non-marker gate evidence, explicit re-display, harness-predicate inputs_
  - _Expected_Behavior: renderedTurn_original(X) == renderedTurn_fixed(X) for all X where NOT isBugCondition(X)_
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 4. Fix: make stop/gate markers internal-only and compose one clean question

  - [x] 4.1 Establish the internal-only directive convention in the governing steering files
    - `agent-behavior-rules.md` Rule 4: add a clause stating `🛑 STOP` and `⛔ MANDATORY GATE` are internal control directives defining the end-of-turn boundary and gate semantics, NEVER rendered to the bootcamper; the rendered boundary is "the single 👉 question is the final message; end immediately after it." Preserve the existing leading-question and bold-question wording.
    - `agent-behavior-rules.md` Rule 3: reinforce that the FIRST composed question must already be single and non-compound (compose-clean-first), not merely rewritten after the fact.
    - `agent-instructions.md` Communication section + Question Stop Protocol subsection: state the stop/gate boundary is internal and signaled by ending the turn after the 👉 question; the agent MUST NOT emit `🛑 STOP` / `⛔ MANDATORY GATE` text. Keep the "STOP and wait for real input" behavioral requirement intact.
    - `conversation-protocol.md`: replace the "The 🛑 STOP marker stays plain — never wrap 🛑 STOP in bold" rule with an internal-only-directive rule (the marker governs behavior but is not rendered); add a **no-duplicate re-display** rule and the compose-clean-first rule to Question Disambiguation / the Pre-Output Validation Checklist (an internal correction/regeneration pass must not re-emit a question already shown unless the bootcamper explicitly asked).
    - Keep the `config/.question_pending` mechanism and Rule 3 compound-rewrite protocol in force.
    - _Bug_Condition: isBugCondition(X) = C1 OR C2 from design (glyph overloading + compound-first composition root causes)_
    - _Expected_Behavior: expectedBehavior(result) — clean single 👉 question, no rendered "🛑"/"⛔", shown once; stop/gate semantics retained internally_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.3, 3.4_

  - [x] 4.2 Rewrite emitted-content examples so CORRECT question turns end on the 👉 question
    - `conversation-examples.md`: rewrite the Multi-Question / Not-Waiting / Self-Answering CORRECT examples so each ends on the 👉 question with no rendered `🛑 STOP` line; where the boundary must be shown, use a clearly non-rendered internal note (e.g., `> _(internal: end the turn here and wait — not shown to the bootcamper)_`).
    - `conversation-protocol.md` Violation Examples: apply the same rewrite to the CORRECT examples.
    - `feedback-workflow.md`: reframe the per-step `🛑 STOP — End your response here.` lines and the "🛑 STOP after each question" rule as internal directives; the emitted flow ends on each 👉 question with no rendered marker.
    - `track-switching.md`: keep the `🛑 STOP` stop semantics as an internal directive note; ensure no rendered marker sits beside the 👉 question.
    - `visualization-guide.md`: rewrite "end your response with: > 🛑 STOP", the delivery-mode `🛑 STOP` line, the 5-step "👉 + 🛑 STOP" example, and the Static-HTML `> **🛑 STOP ...**` blocks so the rendered offer/question ends on the 👉 line and the wait is expressed as an internal directive.
    - `module-01-phase1-discovery.md`: keep the `> **🛑 STOP — End your response here.** Do not answer ...` blockquotes after Steps 5, git, and license questions as internal directives (not rendered); confirm the emitted turn ends on the 👉 question.
    - `onboarding-phase1b-intro-language.md`: convert the `🛑 STOP — Wait ...` line and the `⛔ **MANDATORY GATE** — ...` block to internal-only directives; the rendered language prompt ends on the 👉 question.
    - `module-08-phaseA-requirements.md`: apply the same internal-directive treatment as `module-01` for consistency across the steering set (keep the directive, ensure no rendered marker beside the question).
    - Compose the pre-track comprehension check as a single, non-compound question the first time (e.g., `👉 **Does the overview make sense before we choose a track?**`), removing the prose "or ... clarify?" compound pattern.
    - _Bug_Condition: isBugCondition(X) C1 (glyph rendered as emitted content) + C2 (compound-first composition)_
    - _Expected_Behavior: expectedBehavior(result) — CORRECT examples end on the 👉 question, no rendered "🛑"/"⛔", single non-compound question_
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

  - [x] 4.3 Reconcile the shipped eval fixtures (no change to `eval_conversations.py`)
    - Do NOT modify `senzing-bootcamp/scripts/eval_conversations.py` — `ends_with_question_then_stop` already passes when the 👉 line is the last substantive line, and `_is_boundary_line` still accepts a `🛑 STOP` line, so the property tests that use the boundary keep working.
    - `single_question_stop.json`: remove the trailing `🛑 STOP — End your response here ...` line (the turn now ends on the 👉 question) AND change the assertion `{"type": "contains_marker", "marker": "🛑"}` to `{"type": "absent_marker", "marker": "🛑"}`. Retain `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer`.
    - `confirmation_question_disambiguation.json`: remove the trailing `🛑 STOP` line so the turn ends on the 👉 question; existing assertions still pass. Optionally add `absent_marker "🛑"` to guard the fix.
    - `module3_gate_not_bypassed.json`: remove the trailing `🛑 STOP` line and verify `gate_not_bypassed` (step 3.9) still passes via the retained non-marker execution evidence ("Your visualization is running", "Checkpoint written: module_3_verification.web_service = passed."). Optionally add `absent_marker "🛑"`.
    - Add a new regression fixture `senzing-bootcamp/tests/eval/clean_question_no_marker.json`: a question turn ending on the 👉 question with NO `🛑 STOP` / `⛔` line, asserting `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer`, `absent_marker "🛑"`, `absent_marker "⛔"`. Ensure it carries no forbidden URL/secret pattern.
    - _Bug_Condition: isBugCondition(X) C1 — the fixture oracle previously encoded the rendered marker as expected content_
    - _Expected_Behavior: expectedBehavior(result) — bounded question turn needs no rendered marker; harness engine unchanged_
    - _Requirements: 2.1, 2.3, 3.7_

  - [x] 4.4 Update the coupled content-assertion tests that encode the buggy expectation
    - `senzing-bootcamp/tests/test_bold_question_steering.py`:
      - `test_protocol_has_distinct_bold_rule_section`: drop the "stays plain" clause that requires a rendered `🛑 STOP` line in the bold rule; assert instead the internal-only-directive rule.
      - `test_protocol_stop_marker_is_plain` and `test_examples_stop_marker_is_plain`: replace the "a rendered `🛑 STOP` line must exist and be plain" assertions with assertions that CORRECT question examples end on the 👉 line and render no `🛑 STOP` / `⛔` marker beside a question. (These changes are part of the FIX — they encoded the old, buggy oracle — not a preservation regression.)
    - Marker audit: update any OTHER steering test surfaced during implementation that asserts a marker is rendered *adjacent to a 👉 question* the same way.
    - Preserve internal-directive presence tests unchanged: `test_business_case_offer_steering.py`, `test_licensing_guidance.py`, `test_module2_license_acquisition_info.py` (the internal directive glyphs remain).
    - _Bug_Condition: isBugCondition(X) C1 — the test oracle presumed the marker is emitted_
    - _Expected_Behavior: expectedBehavior(result) — CORRECT examples end on the 👉 question, no rendered "🛑"/"⛔"_
    - _Requirements: 2.1, 2.3_

  - [x] 4.5 Verify the marker-leak exploration test now passes
    - **Property 1: Expected Behavior** - Clean Question, No Leaked Internal Markers
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test. It encodes the expected behavior; when it passes it confirms the fix.
    - Re-run the task 1 exploration test/fixtures against the fixed steering and fixtures.
    - **EXPECTED OUTCOME**: Test PASSES — `absent_marker "🛑"`, `absent_marker "⛔"`, `exactly_one_pointer`, `ends_with_question_then_stop` all hold (confirms C1 is fixed).
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 4.6 Verify the duplicate-question exploration test now passes
    - **Property 2: Expected Behavior** - Question Shown Exactly Once
    - **IMPORTANT**: Re-run the SAME test from task 2 — do NOT write a new test.
    - Re-run the task 2 exploration test/fixtures against the fixed steering.
    - **EXPECTED OUTCOME**: Test PASSES — `exactly_one_pointer` and `no_compound_question` hold; the comprehension-check question is composed clean and shown exactly once (confirms C2 is fixed).
    - _Requirements: 2.4, 2.5_

  - [x] 4.7 Verify the preservation property tests still pass
    - **Property 3: Preservation** - Turn Boundary, Gate, One Question Rule, and Harness Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 3 — do NOT write new tests.
    - Re-run the task 3 preservation tests plus the preserved internal-directive presence tests (`test_business_case_offer_steering.py`, `test_licensing_guidance.py`, `test_module2_license_acquisition_info.py`).
    - Confirm the harness engine is byte-for-byte unmodified and its predicate property tests (`ends_with_question_then_stop`, `no_self_answer`, `no_compound_question`, `gate_not_bypassed`) still pass, including strategies that use a `🛑 STOP` boundary line.
    - Confirm `module3_gate_not_bypassed.json` still passes `gate_not_bypassed` via non-marker evidence after the `🛑 STOP` line was removed.
    - **EXPECTED OUTCOME**: Tests PASS (no regressions — One Question Rule, stop-and-wait, unconditional gate execution, `config/.question_pending`, and harness behavior preserved).
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 5. Checkpoint - Ensure all tests and CI gates pass
  - Run the full shipped-fixture harness: `python senzing-bootcamp/scripts/eval_conversations.py` — must print zero failures and exit 0 (CI parity; validates 3.7).
  - Run the CI pytest suite so the conversational-eval-harness step stays at exit 0:
    `python -m pytest senzing-bootcamp/tests/ tests/` (fast profile locally) and, matching CI coverage, `HYPOTHESIS_PROFILE=thorough python -m pytest senzing-bootcamp/tests/ tests/`.
  - Run the remaining CI gates that the steering rewrites touch: `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, and `sync_hook_registry.py --verify` — all must pass.
  - Confirm `validate_behavior_rules.py --check` reports zero Rule 4 (bold-question) violations across `steering/*.md` (the bold/leading-question guarantee is preserved).
  - Ensure all tests pass; ask the user if questions arise.
