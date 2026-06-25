# Requirements Document

## Introduction

The Senzing Bootcamp Power has roughly 2,600 tests, but nearly all of them parse steering markdown and assert that strings or markers are PRESENT ("does the file say X"). They prove the instructions are authored correctly; they do NOT prove that an agent following the steering actually behaves correctly at runtime. Several governing rules are behavioral and only observable in a live conversation — for example: "ALWAYS prefix prompts with 👉", "exactly one question per turn / never compound", "STOP after a 👉 question and wait", "never self-answer", mandatory-gate stops, and "always offer or continue the next step". Today a behavioral regression (like the prose-only MCP licensing gap or the Module 3 visualization skip escape hatch that were both fixed recently) can pass the entire existing suite.

This feature adds a lightweight conversational-evaluation harness. Maintainers author scripted transcripts (fixtures) of an agent and bootcamper exchange. Each agent turn carries a set of declarative behavioral assertions describing the moves the agent is expected to make at decision points (gates, 👉 questions, module transitions). A checker/runner loads the fixtures and evaluates the assertions against the recorded agent turn text. Behavioral expectations therefore become testable, version-controlled artifacts that complement the existing string-presence tests and the static governance-rule-conformance checker.

The harness is **offline and deterministic**: it does NOT call an LLM or the Senzing MCP server in CI. It evaluates RECORDED transcripts authored by maintainers against declarative assertions. "Evaluating agent behavior" here means: given a recorded agent turn (text), do the structural/behavioral assertions hold? Generating fresh agent transcripts from a live model is explicitly OUT OF SCOPE for the automated suite — it may be described only as an optional manual authoring step that produces a fixture, never as something CI executes.

This feature consists of four parts that ship with the power:

1. A **transcript/scenario fixture format** (a JSON-based, stdlib-parseable format under `senzing-bootcamp/tests/eval/`) describing an ordered sequence of turns and, at each agent turn, the expected behavioral assertions.
2. A **checker/runner** (`senzing-bootcamp/scripts/eval_conversations.py`, stdlib-only, `main(argv=None)`, argparse, exit 0/1) that loads the fixtures and evaluates a declarative assertion vocabulary against the recorded agent turns.
3. A **starter set of scenario fixtures** covering the highest-value behavioral rules, encoding the EXPECTED agent behavior as the oracle.
4. **Tests** (`senzing-bootcamp/tests/`, pytest + Hypothesis) that run the checker over the shipped fixtures and assert they pass, plus property tests over the assertion-evaluation logic.

CI wiring is an optional fifth concern handled at the end.

### Scope decisions resolved in these requirements

- **No live calls in CI**: The harness never calls an LLM or the MCP server during automated testing. It only evaluates recorded fixtures. Live transcript generation is out of scope for the automated suite (Requirement 8).
- **Concrete assertion vocabulary**: The assertion vocabulary is concrete and checkable on transcript text. The starter set is enumerated in Requirement 3, and the format leaves room to extend it (Requirement 4).
- **Relationship to existing tests**: This harness complements — does not replace — the string-presence tests and the static governance-rule-conformance checker. String-presence and static checks verify the steering SAYS the rule; this harness verifies that a RECORDED conversation HONORS the rule (Requirement 9).
- **Placement and format**: Per `structure.md`, the script goes in `senzing-bootcamp/scripts/`, the fixtures go in `senzing-bootcamp/tests/eval/`, and the tests go in `senzing-bootcamp/tests/`. The fixture format is stdlib-parseable; requirements fix the stdlib-only constraint and leave the concrete file syntax (JSON) to be confirmed in design (Requirement 1, Requirement 11).
- **Stdlib-only**: The checker uses only the Python standard library. The test layer may use pytest and Hypothesis, consistent with the repository convention (Requirement 11).

## Glossary

- **The_Harness**: The conversational-eval-harness feature as a whole (fixture format + checker/runner + starter fixtures + tests).
- **The_Checker**: The script `senzing-bootcamp/scripts/eval_conversations.py` that loads fixtures and evaluates assertions.
- **Scenario_Fixture**: A version-controlled file describing one conversational scenario as an ordered sequence of turns, with behavioral assertions attached to agent turns.
- **Transcript**: The ordered sequence of turns inside a Scenario_Fixture.
- **Turn**: A single entry in a Transcript with a `role` (one of `agent` or `bootcamper`) and the textual `content` of that turn.
- **Agent_Turn**: A Turn whose `role` is `agent`. Only Agent_Turns may carry behavioral assertions.
- **Bootcamper_Turn**: A Turn whose `role` is `bootcamper`, representing the learner's input.
- **Behavioral_Assertion**: A declarative, named check attached to an Agent_Turn that The_Checker evaluates against that turn's `content` (and, where specified, prior turns in the same Transcript).
- **Assertion_Type**: The kind of check a Behavioral_Assertion performs, drawn from the Starter_Assertion_Set (Requirement 3) or a registered extension (Requirement 4).
- **Starter_Assertion_Set**: The enumerated set of Assertion_Types The_Harness ships with in its first version (Requirement 3).
- **Pointer**: The 👉 marker that prefixes every input-requiring prompt in the bootcamp.
- **Gate**: A ⛔ mandatory gate step in the steering that must be executed and must not be bypassed or skipped.
- **Module_Transition**: The point where the agent moves from one module to the next after a bootcamper confirms readiness; per the steering it must produce a module banner, journey map, before/after framing, and the first step's content.
- **Assertion_Result**: The outcome of evaluating one Behavioral_Assertion against one Agent_Turn: either pass or fail, with a human-readable message on failure.
- **Failure_Report**: The output The_Checker produces when one or more Behavioral_Assertions fail, naming the scenario, the turn, and the failed assertion.
- **Eval_Directory**: The directory `senzing-bootcamp/tests/eval/` where Scenario_Fixtures are stored.

## Requirements

### Requirement 1: Scenario Fixture Format

**User Story:** As a power maintainer, I want a well-defined, stdlib-parseable fixture format for conversational scenarios, so that I can encode an agent/bootcamper exchange and its expected behavioral assertions as a version-controlled artifact.

#### Acceptance Criteria

1. THE_Harness SHALL define a Scenario_Fixture format that stores data in a stdlib-parseable serialization format requiring no third-party dependency to load.
2. THE Scenario_Fixture SHALL contain a top-level `scenario` field holding a non-empty string identifier for the scenario.
3. THE Scenario_Fixture SHALL contain a top-level `description` field holding a human-readable string describing what behavioral rule the scenario exercises.
4. THE Scenario_Fixture SHALL contain a top-level `turns` field holding an ordered list of one or more Turn entries.
5. THE_Harness SHALL store every Scenario_Fixture under the Eval_Directory `senzing-bootcamp/tests/eval/`.
6. WHERE a Scenario_Fixture references a governing rule, THE Scenario_Fixture SHALL record a `rule_ref` field naming the rule or steering source the scenario exercises.

### Requirement 2: Turn Structure and Assertion Attachment

**User Story:** As a power maintainer, I want each turn to declare its role and content, with behavioral assertions attached to agent turns, so that the checker knows which text to evaluate and which checks to apply.

#### Acceptance Criteria

1. THE_Harness SHALL represent each Turn with a `role` field whose value is exactly one of `agent` or `bootcamper`.
2. THE_Harness SHALL represent each Turn with a `content` field holding the textual content of that Turn as a string.
3. WHERE a Turn is an Agent_Turn, THE Turn MAY contain an `assertions` field holding a list of zero or more Behavioral_Assertion entries.
4. IF a Bootcamper_Turn contains an `assertions` field, THEN THE_Checker SHALL report a fixture-validity error naming the scenario and the offending turn.
5. THE_Harness SHALL represent each Behavioral_Assertion with a `type` field naming an Assertion_Type.
6. WHERE a Behavioral_Assertion requires a parameter, THE Behavioral_Assertion SHALL carry that parameter in a named field defined for that Assertion_Type.
7. IF a Turn omits the `role` field or omits the `content` field, THEN THE_Checker SHALL report a fixture-validity error naming the scenario and the offending turn.

### Requirement 3: Starter Assertion Vocabulary

**User Story:** As a power maintainer, I want a concrete set of behavioral assertion types that operate on transcript text, so that I can express the highest-value conversation rules as checkable conditions.

#### Acceptance Criteria

1. THE_Harness SHALL support an `exactly_one_pointer` Assertion_Type that passes WHEN the count of Pointer (👉) occurrences in the Agent_Turn content equals exactly one.
2. THE_Harness SHALL support an `ends_with_question_then_stop` Assertion_Type that passes WHEN the Agent_Turn content contains a Pointer question and no substantive agent content follows the question text within the same turn.
3. THE_Harness SHALL support a `no_compound_question` Assertion_Type that passes WHEN the Agent_Turn content contains at most one question mark and contains no prose conjunction (for example "or", "alternatively", "or would you rather", "or should we") joining two question alternatives.
4. THE_Harness SHALL support a `no_self_answer` Assertion_Type that passes WHEN the Agent_Turn content contains no agent-authored answer to its own Pointer question following that question in the same turn.
5. THE_Harness SHALL support a `contains_marker` Assertion_Type that passes WHEN the Agent_Turn content contains a specified marker string.
6. THE_Harness SHALL support an `absent_marker` Assertion_Type that passes WHEN the Agent_Turn content does not contain a specified marker string.
7. THE_Harness SHALL support a `mentions_tool` Assertion_Type that passes WHEN the Agent_Turn content names a specified tool (for example `search_docs`).
8. THE_Harness SHALL support a `transition_response_completeness` Assertion_Type that passes WHEN the Agent_Turn content contains a module banner marker, a journey map marker, a before/after framing marker, a first-step content marker, and has length greater than 50 characters.
9. THE_Harness SHALL support a `gate_not_bypassed` Assertion_Type that passes WHEN an Agent_Turn that advances past a Gate step shows the Gate was executed and contains no skip or bypass offer for that Gate.
10. WHEN The_Checker evaluates any Assertion_Type in the Starter_Assertion_Set, THE_Checker SHALL evaluate the assertion deterministically against the recorded turn text and produce the same Assertion_Result on repeated runs over the same fixture.

### Requirement 4: Assertion Vocabulary Extensibility

**User Story:** As a power maintainer, I want to add new assertion types without rewriting the checker, so that the harness can grow to cover additional behavioral rules over time.

#### Acceptance Criteria

1. THE_Checker SHALL resolve each Behavioral_Assertion's `type` field against a registry of known Assertion_Types.
2. IF a Behavioral_Assertion names an Assertion_Type that is not in the registry, THEN THE_Checker SHALL report a fixture-validity error naming the scenario, the turn, and the unknown Assertion_Type.
3. WHERE a maintainer adds a new Assertion_Type, THE_Harness SHALL allow registration of the new type without modifying the evaluation of existing Assertion_Types.
4. THE_Harness SHALL document each supported Assertion_Type with its name, purpose, and required parameters.

### Requirement 5: Checker Loading Behavior

**User Story:** As a power maintainer, I want the checker to load scenario fixtures from a directory, so that I can run the full behavioral suite or a single scenario.

#### Acceptance Criteria

1. WHEN The_Checker is invoked without an explicit path argument, THE_Checker SHALL load every Scenario_Fixture in the Eval_Directory.
2. WHERE The_Checker is invoked with a path to a single Scenario_Fixture, THE_Checker SHALL load and evaluate only that fixture.
3. IF a fixture file cannot be parsed by the stdlib loader, THEN THE_Checker SHALL report a parse error naming the file and SHALL exit with a non-zero exit code.
4. IF the Eval_Directory contains no Scenario_Fixture when The_Checker is invoked without a path argument, THEN THE_Checker SHALL report that no fixtures were found and SHALL exit with a non-zero exit code.
5. WHEN The_Checker loads a Scenario_Fixture, THE_Checker SHALL validate the fixture against the structure defined in Requirement 1 and Requirement 2 before evaluating assertions.

### Requirement 6: Assertion Evaluation and Reporting

**User Story:** As a power maintainer, I want the checker to evaluate every assertion and report clear failures, so that I can identify exactly which scenario, turn, and assertion failed.

#### Acceptance Criteria

1. WHEN The_Checker evaluates a Scenario_Fixture, THE_Checker SHALL evaluate every Behavioral_Assertion attached to every Agent_Turn in the Transcript.
2. WHEN a Behavioral_Assertion passes, THE_Checker SHALL record a passing Assertion_Result for that assertion.
3. IF a Behavioral_Assertion fails, THEN THE_Checker SHALL produce a Failure_Report that names the scenario identifier, the turn index or identifier, and the failed Assertion_Type.
4. THE Failure_Report SHALL include a human-readable message describing why the assertion failed.
5. WHEN The_Checker finishes evaluating all loaded fixtures, THE_Checker SHALL print a summary stating the number of scenarios evaluated, the number of assertions evaluated, and the number of failures.

### Requirement 7: Exit Codes

**User Story:** As a power maintainer, I want the checker to signal success or failure through its exit code, so that CI can gate on behavioral conformance.

#### Acceptance Criteria

1. WHEN every Behavioral_Assertion across all evaluated fixtures passes, THE_Checker SHALL exit with exit code 0.
2. IF one or more Behavioral_Assertions fail, THEN THE_Checker SHALL exit with exit code 1.
3. IF a fixture-validity error or parse error occurs, THEN THE_Checker SHALL exit with exit code 1.
4. THE_Checker SHALL expose a `main(argv=None)` entry point parsed with argparse, consistent with the repository script convention.

### Requirement 8: Offline and Deterministic Operation

**User Story:** As a power maintainer, I want the harness to run fully offline and deterministically, so that CI never depends on a live model or network and never produces flaky results.

#### Acceptance Criteria

1. THE_Checker SHALL evaluate only recorded Scenario_Fixture content and SHALL NOT issue any network request during evaluation.
2. THE_Checker SHALL NOT invoke an LLM and SHALL NOT call the Senzing MCP server during evaluation.
3. THE_Harness SHALL treat live generation of fresh agent transcripts as outside the scope of the automated suite, and any manual transcript authoring step SHALL produce a version-controlled Scenario_Fixture before The_Checker evaluates it.
4. WHEN The_Checker evaluates the same set of Scenario_Fixtures more than once without changes, THE_Checker SHALL produce the same Assertion_Results and the same exit code on each run.
5. THE Scenario_Fixtures SHALL be version-controlled files stored within the power directory tree.

### Requirement 9: Relationship to Existing Verification Layers

**User Story:** As a power maintainer, I want the harness to clearly complement the existing string-presence tests and the static governance-rule-conformance checker, so that the three layers have distinct, non-overlapping responsibilities.

#### Acceptance Criteria

1. THE_Harness SHALL verify that a recorded conversation HONORS a behavioral rule, distinct from string-presence tests that verify the steering text contains a marker.
2. THE_Harness SHALL verify behavioral conformance against recorded transcripts, distinct from the static governance-rule-conformance checker that verifies steering files reference their enforcement points.
3. THE_Harness SHALL NOT relocate, duplicate, or modify the enforcement logic contained in steering files, hooks, or existing scripts.
4. THE_Harness documentation SHALL state the distinction between verifying that the steering SAYS a rule and verifying that a recorded conversation HONORS the rule.

### Requirement 10: Starter Scenario Set

**User Story:** As a power maintainer, I want a starter set of scenario fixtures tied to the highest-value behavioral rules, so that the most consequential regressions are caught immediately and new fixtures have working examples to follow.

#### Acceptance Criteria

1. THE_Harness SHALL ship a Scenario_Fixture exercising the single-question, Pointer-prefix, STOP-and-wait, and no-self-answer rules using the `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, and `no_self_answer` Assertion_Types.
2. THE_Harness SHALL ship a Scenario_Fixture exercising the mandatory-gate-not-skipped rule at Module 3 Step 9 using the `gate_not_bypassed` Assertion_Type.
3. THE_Harness SHALL ship a Scenario_Fixture exercising the Module_Transition completeness rule using the `transition_response_completeness` Assertion_Type, asserting the transition turn produces a banner, journey map, before/after framing, and first step rather than a bare acknowledgment.
4. THE_Harness SHALL ship a Scenario_Fixture exercising the license-insufficient path using the `mentions_tool` Assertion_Type to assert the agent consults `search_docs`.
5. WHEN The_Checker evaluates the shipped starter Scenario_Fixtures, THE_Checker SHALL report all assertions as passing and SHALL exit with exit code 0.
6. THE starter Scenario_Fixtures SHALL encode the EXPECTED agent behavior as the oracle that the assertions validate.

### Requirement 11: Non-Functional Constraints

**User Story:** As a power maintainer, I want the harness to follow the power's stdlib-only, fast, ship-with-power conventions, so that it integrates cleanly with the existing codebase and distribution.

#### Acceptance Criteria

1. THE_Checker SHALL use only the Python standard library and SHALL NOT import any third-party dependency.
2. THE_Checker SHALL follow the repository script convention: `#!/usr/bin/env python3` shebang, `from __future__ import annotations`, a module docstring with usage examples, dataclasses for structured data, and an `if __name__ == "__main__"` entry point.
3. THE_Harness SHALL place The_Checker in `senzing-bootcamp/scripts/`, the Scenario_Fixtures in `senzing-bootcamp/tests/eval/`, and its tests in `senzing-bootcamp/tests/`, so that all artifacts ship with the power.
4. THE Scenario_Fixtures SHALL contain no secrets, credentials, personally identifiable information, or MCP server URLs.
5. WHEN The_Checker evaluates the full shipped starter set, THE_Checker SHALL complete within a few seconds on a developer machine without network access.

### Requirement 12: Test Coverage

**User Story:** As a power maintainer, I want pytest and Hypothesis tests covering the checker and the assertion-evaluation logic, so that the harness itself is verified and protected against regression.

#### Acceptance Criteria

1. THE_Harness SHALL include a test that runs The_Checker over every shipped starter Scenario_Fixture and asserts every assertion passes.
2. THE_Harness SHALL include property-based tests over the assertion-evaluation logic for the Starter_Assertion_Set using Hypothesis with `@settings(max_examples=20)`.
3. THE property tests SHALL verify that `exactly_one_pointer` passes for generated agent turns containing exactly one Pointer and fails for generated turns containing zero or more than one Pointer.
4. THE property tests SHALL verify that `no_compound_question` fails for generated turns containing two question alternatives joined by a prose conjunction and passes for generated single questions.
5. THE_Harness tests SHALL follow the repository test convention: class-based organization, `st_`-prefixed strategies, `from __future__ import annotations`, and type hints using `X | None` and `list[str]` forms.
6. THE_Harness SHALL include a test that asserts an unknown Assertion_Type and a malformed fixture each cause The_Checker to report an error and exit with exit code 1.
