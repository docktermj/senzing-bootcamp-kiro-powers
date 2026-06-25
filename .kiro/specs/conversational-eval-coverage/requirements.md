# Requirements Document

## Introduction

The Senzing Bootcamp Power has roughly 2,600 tests, but the overwhelming majority parse steering markdown and assert that strings or markers are PRESENT ("does the file say X"). Those tests prove the governing rules are *written*; they do not prove that an agent *following* the steering behaves correctly at runtime. A behavioral conversational-eval harness already exists to close that gap — `senzing-bootcamp/scripts/eval_conversations.py` loads version-controlled JSON Scenario_Fixtures from `senzing-bootcamp/tests/eval/`, evaluates declarative Behavioral_Assertions against recorded agent-turn text, and exits 0/1. It is wired into CI as the "Conversational eval harness" step. The harness, its 9 Assertion_Types, its fixture schema, and its starter fixtures are specified by the existing `conversational-eval-harness` spec.

The problem this feature solves is **coverage breadth, not harness architecture**. The existing harness ships only four starter fixtures and exercises only a handful of the governing rules. Many high-value governing rules — ones that today are verified ONLY by string-presence tests — have no behavioral scenario at all. A behavioral regression against those rules would pass the entire suite.

This feature ADDS behavioral Scenario_Fixtures (and, only where strictly necessary, ONE new Assertion_Type) for a justified seed set of governing rules that currently lack behavioral coverage. It does NOT redesign the harness, the fixture schema, the loader, the reporter, the exit-code contract, or the existing 9 Assertion_Types. Every new fixture reuses the existing schema (`scenario`, `description`, `rule_ref`, `turns` with `role`/`content`/`assertions`) and, wherever the existing 9 Assertion_Types suffice, reuses them.

### Verification performed before writing these requirements

The following facts were confirmed by reading the codebase, so the requirements match the real harness rather than an assumed one:

- **Harness driver and schema** (`senzing-bootcamp/scripts/eval_conversations.py`): the fixture schema, the `(turn, ctx, params)` predicate signature, the `REGISTRY` of 9 Assertion_Types, the `REQUIRED_PARAMS` map, the collect-all evaluation, the summary line, and the `main(argv=None)` / exit 0/1 contract are all as described.
- **The 9 existing Assertion_Types**: `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer`, `contains_marker` (param `marker`), `absent_marker` (param `marker`), `mentions_tool` (param `tool`), `transition_response_completeness`, `gate_not_bypassed` (param `step`).
- **The 4 existing fixtures** in `senzing-bootcamp/tests/eval/`: `single_question_stop.json`, `module_transition_completeness.json`, `module3_gate_not_bypassed.json`, `license_insufficient_search_docs.json`.
- **Harness tests**: `senzing-bootcamp/tests/test_eval_conversations.py` (class-based, `st_`-prefixed strategies, `@settings(max_examples=20)`, `from __future__ import annotations`, type hints, `sys.path` import shim).
- **CI**: `.github/workflows/validate-power.yml` runs `validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, `validate_dependencies.py`, `compose_hook_prompts.py --verify`, `sync_hook_registry.py --verify`, `validate_prerequisites.py`, `validate_progress_ci.py`, `validate_mandatory_gates.py`, `validate_governance_rules.py`, `validate_yaml_schemas.py`, `ruff check`, the "Conversational eval harness" step (`python senzing-bootcamp/scripts/eval_conversations.py`), then pytest — across Python 3.11/3.12/3.13.
- **Every targeted governing rule exists in steering** (citations are in the per-requirement `rule_ref` text below), so no rule is invented.

### V1 seed set selection (justified)

The candidate rules were each checked against the existing 9 Assertion_Types. The v1 seed set is chosen to maximize behavioral coverage of high-value rules while reusing the existing vocabulary wherever possible, and is deliberately small:

1. **MCP-First Invariant** (Requirement 2) — agent calls an MCP tool before presenting Senzing facts (SDK method / attribute-name case). REUSE-ONLY (`mentions_tool`, `ends_with_question_then_stop`). Complements `license_insufficient_search_docs.json` by covering the SDK-reference / attribute-name branch rather than the licensing branch. Rule: `agent-instructions.md#mcp-first-invariant`, `agent-instructions.md#mcp-rules`.
2. **No-direct-SQL redirect** (Requirement 3) — agent redirects a SQL-tempting question to SDK/MCP tools and never emits direct SQL against the Senzing database. REUSE-ONLY (`mentions_tool`, `absent_marker`, `ends_with_question_then_stop`). Complements the repo string-presence test `test_no_direct_sql_preservation.py`. Rule: `mcp-usage-reference.md#sql-redirect-rules`, `agent-instructions.md` SQL-redirect line, `mcp-tool-decision-tree.md`.
3. **👉 question disambiguation / no follow-up appended to a confirmation** (Requirement 4) — every 👉 question has one unambiguous yes/no meaning and no follow-up question is appended to a confirmation. REUSE-ONLY (`exactly_one_pointer`, `no_compound_question`, `ends_with_question_then_stop`, `no_self_answer`). Rule: `conversation-protocol.md#question-disambiguation`, `agent-behavior-rules.md` Rule 3, `agent-instructions.md` question rules.
4. **Substantive response to a pending answer / no Minimal_Output after a Transition_Confirmation** (Requirement 5 + Requirement 6) — the agent must produce substantive output (not ".", "OK", empty, or anything under 50 characters) when acting on a pending 👉 answer or after a Transition_Confirmation. The existing 9 Assertion_Types CANNOT express "the turn is substantive" — `transition_response_completeness` requires the four module-transition markers (banner/journey/before-after/first-step) and so is far too specific for a general substantive-response check, and there is no length/non-trivial-content predicate. This rule therefore justifies exactly ONE new Assertion_Type, `substantive_response` (Requirement 6). Rule: `conversation-protocol.md#answer-processing-priority` (Substantive output requirement), `agent-instructions.md#answer-processing-priority` (Minimal_Output protocol violation), `conversation-protocol.md` Transition_Confirmation <50-character rule.

### Candidates deferred to a later iteration (explicitly out of scope for v1)

- **Hook-silence rule** (`hook-architecture.md`, `silent-hook-architecture`) — "when a hook check passes, zero visible tokens". Whether agent silence is expressible as a transcript assertion is genuinely uncertain (a passing hook produces an *absence* of a turn, which the current per-agent-turn model does not naturally represent). FLAGGED FOR DESIGN; not committed to v1.
- **Additional mandatory-gate "never offer to skip a ⛔ step" scenarios** beyond the existing Module 3 Step 9 fixture (for example other `⛔ MANDATORY` offers such as the Module 6 results-dashboard gate). The pattern is already proven by `module3_gate_not_bypassed.json`; broadening it is incremental and deferred.
- **A dedicated MCP-First scenario for additional branches** (error-code lookup via `explain_error_code`, scaffold generation via `generate_scaffold`) beyond the single SDK-reference/attribute-name branch chosen for v1.

### Cross-cutting scope decisions

- **Positive exemplars only (no negative-example support in v1).** The current harness asserts that recorded agent turns are CORRECT — a fixture passes when its assertions hold. Every new fixture's agent turns SHALL represent correct behavior that PASSES its assertions, so the "Conversational eval harness" CI step continues to exit 0. Introducing negative-example (expected-fail) support would change the harness contract and is therefore a design-level decision flagged here, not a requirement of this feature.
- **Reuse over extension.** A new Assertion_Type is required only when a targeted rule's behavioral check genuinely cannot be expressed with the existing 9. Exactly one such type (`substantive_response`) is justified in v1.
- **No harness redesign.** The fixture schema, loader, registry mechanism, reporter, summary line, CLI, and exit-code contract are unchanged. The only code change to `eval_conversations.py` is the additive registration of the one new Assertion_Type and its predicate; its tests are extended in `test_eval_conversations.py`.

## Glossary

- **The_Harness**: The existing conversational-eval harness (driver `eval_conversations.py`, fixture schema, Assertion_Type registry, and tests) that this feature expands. Defined by the `conversational-eval-harness` spec.
- **The_Coverage_Feature**: The work defined by THIS document — new Scenario_Fixtures, one new Assertion_Type, and their tests, expanding The_Harness's behavioral coverage.
- **The_Checker**: The script `senzing-bootcamp/scripts/eval_conversations.py` that loads Scenario_Fixtures and evaluates Behavioral_Assertions.
- **Scenario_Fixture**: A version-controlled JSON file under the Eval_Directory describing one conversational scenario as an ordered list of Turns, with Behavioral_Assertions attached to Agent_Turns. Schema: top-level `scenario` (non-empty string), `description` (string), optional `rule_ref` (string), and `turns` (non-empty list).
- **Eval_Directory**: The directory `senzing-bootcamp/tests/eval/` where Scenario_Fixtures are stored and from which The_Checker discovers them by default.
- **Turn**: A single transcript entry with a `role` (exactly `agent` or `bootcamper`) and string `content`.
- **Agent_Turn**: A Turn whose `role` is `agent`. Only Agent_Turns may carry `assertions`.
- **Bootcamper_Turn**: A Turn whose `role` is `bootcamper`, representing the learner's input.
- **Behavioral_Assertion**: A declarative, named check (`type` plus optional named parameters) attached to an Agent_Turn and evaluated against that turn's `content` (and, where the predicate is context-aware, the surrounding Transcript).
- **Assertion_Type**: The kind of check a Behavioral_Assertion performs. The_Harness ships 9 existing types; this feature adds one (`substantive_response`).
- **Existing_Assertion_Set**: The 9 Assertion_Types already in The_Harness: `exactly_one_pointer`, `ends_with_question_then_stop`, `no_compound_question`, `no_self_answer`, `contains_marker`, `absent_marker`, `mentions_tool`, `transition_response_completeness`, `gate_not_bypassed`.
- **Pointer**: The 👉 marker that prefixes every input-requiring prompt in the bootcamp.
- **MCP_Tool**: A Senzing MCP server tool (for example `search_docs`, `get_sdk_reference`, `generate_scaffold`, `sdk_guide`, `explain_error_code`, `find_examples`, `mapping_workflow`, `get_capabilities`) that supplies Senzing facts.
- **MCP_First_Invariant**: The governing rule that the agent SHALL call at least one MCP_Tool in a turn before presenting Senzing SDK method names, attribute names, config options, error codes, or entity-resolution technical details (`agent-instructions.md#mcp-first-invariant`).
- **SQL_Redirect_Rule**: The governing rule that the agent SHALL NOT generate direct SQL (SELECT/INSERT/UPDATE/DELETE) against the Senzing database (`database/G2C.db`) or its internal tables, and SHALL redirect SQL-tempting requests to SDK methods via MCP_Tools (`mcp-usage-reference.md#sql-redirect-rules`).
- **Question_Disambiguation_Rule**: The governing rule that every 👉 question has exactly one unambiguous meaning for "yes" and one for "no", with no follow-up question appended to a confirmation (`conversation-protocol.md#question-disambiguation`).
- **Transition_Confirmation**: A Bootcamper_Turn affirmatively confirming readiness to start the next module, after which the agent must produce a full module start, not Minimal_Output.
- **Minimal_Output**: An agent response that is a dot, empty, whitespace-only, a single-word acknowledgment, or under 50 characters — prohibited as a response to a pending 👉 answer or a Transition_Confirmation (`agent-instructions.md#answer-processing-priority`).
- **Substantive_Response**: An Agent_Turn that is NOT Minimal_Output — at least 50 characters of non-trivial content that acknowledges and acts upon the pending answer.
- **Positive_Exemplar**: A Scenario_Fixture whose Agent_Turns encode CORRECT agent behavior, so all attached Behavioral_Assertions pass and The_Checker exits 0.

## Requirements

### Requirement 1: Reuse the Existing Harness, Schema, and Vocabulary

**User Story:** As a power maintainer, I want this feature to expand behavioral coverage using the existing harness, fixture schema, and assertion vocabulary, so that no harness architecture is redesigned and the existing verification contract is preserved.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL author every new Scenario_Fixture using the existing Scenario_Fixture schema: a top-level `scenario` non-empty string, a `description` string, an optional `rule_ref` string, and a `turns` non-empty ordered list of Turn objects.
2. THE_Coverage_Feature SHALL store every new Scenario_Fixture in the Eval_Directory `senzing-bootcamp/tests/eval/`.
3. THE_Coverage_Feature SHALL reuse an Assertion_Type from the Existing_Assertion_Set for any behavioral check that the Existing_Assertion_Set can express.
4. WHERE a targeted governing rule's behavioral check cannot be expressed by any Assertion_Type in the Existing_Assertion_Set, THE_Coverage_Feature SHALL define a new Assertion_Type, and THE definition SHALL record the justification and the rule the new type serves.
5. THE_Coverage_Feature SHALL NOT modify the Scenario_Fixture schema, the loader, the reporter, the summary output, the CLI, or the exit-code contract of The_Checker.
6. THE_Coverage_Feature SHALL NOT alter the evaluation behavior of any Assertion_Type in the Existing_Assertion_Set.
7. THE_Coverage_Feature SHALL NOT relocate, duplicate, or modify enforcement logic contained in steering files, hooks, or other existing scripts.

### Requirement 2: MCP-First Invariant Scenario (SDK / Attribute-Name Branch)

**User Story:** As a power maintainer, I want a behavioral scenario proving the agent consults an MCP_Tool before stating Senzing SDK or attribute facts, so that the MCP_First_Invariant has behavioral coverage beyond the existing licensing fixture.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL ship a Scenario_Fixture exercising the MCP_First_Invariant for an SDK-method-or-attribute-name request, distinct from the existing `license_insufficient_search_docs.json` licensing branch.
2. THE Scenario_Fixture SHALL include a Bootcamper_Turn that asks for a Senzing SDK method signature, attribute name, or config option.
3. THE Scenario_Fixture SHALL include an Agent_Turn that names an MCP_Tool appropriate to the request (for example `get_sdk_reference` or `mapping_workflow`) using the `mentions_tool` Assertion_Type before presenting the Senzing fact.
4. THE Agent_Turn SHALL end on a single Pointer prompt and stop, verified by the `exactly_one_pointer` and `ends_with_question_then_stop` Assertion_Types, so the turn is a Positive_Exemplar.
5. THE Scenario_Fixture SHALL set `rule_ref` to a value naming the MCP_First_Invariant steering source (`agent-instructions.md#mcp-first-invariant`).
6. WHEN The_Checker evaluates this Scenario_Fixture, THE_Checker SHALL report every attached Behavioral_Assertion as passing.

### Requirement 3: No-Direct-SQL Redirect Scenario

**User Story:** As a power maintainer, I want a behavioral scenario proving the agent redirects a SQL-tempting question to SDK/MCP tools and emits no direct SQL, so that the SQL_Redirect_Rule has behavioral coverage complementing the existing string-presence test.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL ship a Scenario_Fixture exercising the SQL_Redirect_Rule.
2. THE Scenario_Fixture SHALL include a Bootcamper_Turn that poses a SQL-tempting request (for example counting entities, finding duplicates, or querying entity details).
3. THE Scenario_Fixture SHALL include an Agent_Turn that names the redirected MCP_Tool or SDK method (for example `reporting_guide`, `search_by_attributes`, `get_entity`, or `get_entity_by_record_id`) using the `mentions_tool` Assertion_Type.
4. THE Agent_Turn SHALL be verified by `absent_marker` Assertion_Types asserting that direct-SQL keywords (for example `SELECT` and `RES_ENT`) do not appear in the turn content.
5. THE Agent_Turn SHALL end on a single Pointer prompt and stop, verified by the `exactly_one_pointer` and `ends_with_question_then_stop` Assertion_Types, so the turn is a Positive_Exemplar.
6. THE Scenario_Fixture SHALL set `rule_ref` to a value naming the SQL_Redirect_Rule steering source (`mcp-usage-reference.md#sql-redirect-rules`).
7. WHEN The_Checker evaluates this Scenario_Fixture, THE_Checker SHALL report every attached Behavioral_Assertion as passing.

### Requirement 4: 👉 Question Disambiguation Scenario

**User Story:** As a power maintainer, I want a behavioral scenario proving a confirmation 👉 question carries exactly one unambiguous yes/no meaning with no follow-up appended, so that the Question_Disambiguation_Rule has behavioral coverage.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL ship a Scenario_Fixture exercising the Question_Disambiguation_Rule, distinct from the existing `single_question_stop.json` fixture in that it targets a confirmation question that must not carry an appended follow-up.
2. THE Scenario_Fixture SHALL include an Agent_Turn that poses a single confirmation 👉 question.
3. THE Agent_Turn SHALL be verified by the `exactly_one_pointer`, `no_compound_question`, and `no_self_answer` Assertion_Types so that the turn contains exactly one Pointer, no conjunction joining alternatives, no second question mark, and no self-answer.
4. THE Agent_Turn SHALL end on the Pointer prompt and stop, verified by the `ends_with_question_then_stop` Assertion_Type, so the turn is a Positive_Exemplar.
5. THE Scenario_Fixture SHALL set `rule_ref` to a value naming the Question_Disambiguation_Rule steering source (`conversation-protocol.md#question-disambiguation`).
6. WHEN The_Checker evaluates this Scenario_Fixture, THE_Checker SHALL report every attached Behavioral_Assertion as passing.

### Requirement 5: Substantive-Response-After-Confirmation Scenario

**User Story:** As a power maintainer, I want a behavioral scenario proving the agent produces a Substantive_Response after a Transition_Confirmation rather than Minimal_Output, so that the answer-processing substantive-output rule has behavioral coverage.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL ship a Scenario_Fixture exercising the rule that the agent produces a Substantive_Response (not Minimal_Output) after a Transition_Confirmation.
2. THE Scenario_Fixture SHALL include a Bootcamper_Turn that affirmatively confirms readiness to start the next module (a Transition_Confirmation).
3. THE Scenario_Fixture SHALL include an Agent_Turn that is a Substantive_Response, verified by the `substantive_response` Assertion_Type defined in Requirement 6.
4. THE Scenario_Fixture SHALL set `rule_ref` to a value naming the answer-processing substantive-output steering source (`conversation-protocol.md#answer-processing-priority`).
5. WHEN The_Checker evaluates this Scenario_Fixture, THE_Checker SHALL report every attached Behavioral_Assertion as passing.

### Requirement 6: New `substantive_response` Assertion_Type

**User Story:** As a power maintainer, I want a single new assertion type that checks an agent turn is substantive rather than Minimal_Output, so that the substantive-output rule can be expressed, since the existing 9 assertion types cannot express it.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL define a new Assertion_Type named `substantive_response` because no Assertion_Type in the Existing_Assertion_Set can verify that an Agent_Turn is not Minimal_Output.
2. THE `substantive_response` Assertion_Type SHALL pass WHEN the Agent_Turn content is a Substantive_Response.
3. IF the Agent_Turn content is Minimal_Output — empty, whitespace-only, a single-word acknowledgment, or fewer than 50 characters of content — THEN THE `substantive_response` Assertion_Type SHALL fail with a human-readable message describing why.
4. THE `substantive_response` Assertion_Type SHALL be a pure function of its inputs, evaluating deterministically with no network, filesystem, clock, or random-source access, consistent with the existing predicates.
5. THE_Coverage_Feature SHALL register the `substantive_response` Assertion_Type in The_Checker's Assertion_Type registry by adding one registry entry and its predicate, without modifying the evaluation of any Assertion_Type in the Existing_Assertion_Set.
6. WHERE the `substantive_response` Assertion_Type takes no parameters, THE_Coverage_Feature SHALL NOT add a required-parameter entry for it.
7. THE_Coverage_Feature SHALL document the `substantive_response` Assertion_Type with its name, purpose, and (absence of) required parameters alongside the existing Assertion_Type documentation in The_Checker.

### Requirement 7: New Fixtures Are Passing Positive Exemplars

**User Story:** As a power maintainer, I want every new fixture to encode correct agent behavior that passes its assertions, so that the "Conversational eval harness" CI step continues to exit 0.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL author every new Scenario_Fixture as a Positive_Exemplar whose Agent_Turns represent correct agent behavior.
2. WHEN The_Checker evaluates the full Eval_Directory after the new Scenario_Fixtures are added, THE_Checker SHALL report zero failures and SHALL exit with exit code 0.
3. THE_Coverage_Feature SHALL NOT introduce negative-example or expected-fail fixtures, because the current harness contract asserts that recorded Agent_Turns are correct.
4. THE_Coverage_Feature SHALL preserve passing evaluation of the four existing Scenario_Fixtures (`single_question_stop.json`, `module_transition_completeness.json`, `module3_gate_not_bypassed.json`, `license_insufficient_search_docs.json`).
5. WHERE a new Scenario_Fixture references a governing rule, THE Scenario_Fixture SHALL declare a `rule_ref` field naming the steering rule it exercises.

### Requirement 8: Test Coverage for the New Assertion Type and Fixtures

**User Story:** As a power maintainer, I want pytest and Hypothesis tests for the new assertion type and the new fixtures, so that the expanded harness is verified and protected against regression.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL add tests to `senzing-bootcamp/tests/test_eval_conversations.py` covering the `substantive_response` Assertion_Type.
2. THE tests SHALL include a property-based test verifying that `substantive_response` passes for generated Substantive_Response content and fails for generated Minimal_Output content.
3. THE tests SHALL verify that The_Checker reports every Behavioral_Assertion in each new Scenario_Fixture as passing.
4. THE tests SHALL follow the repository test convention: `from __future__ import annotations`, class-based organization, `st_`-prefixed Hypothesis strategies, `@settings(max_examples=20)`, and type hints using `X | None` and `list[str]` forms.
5. THE property tests SHALL document which requirement each test class validates.

### Requirement 9: CI Stays Green

**User Story:** As a power maintainer, I want all existing CI steps to keep passing after this feature, so that expanding coverage never breaks the pipeline.

#### Acceptance Criteria

1. WHEN the "Conversational eval harness" CI step runs `python senzing-bootcamp/scripts/eval_conversations.py`, THE_Checker SHALL exit with exit code 0.
2. WHEN the pytest CI step runs over `senzing-bootcamp/tests/` and `tests/`, THE new and existing tests SHALL pass.
3. WHEN the `ruff check` CI step runs over `senzing-bootcamp/scripts/`, `senzing-bootcamp/tests/`, and `tests/`, THE new and modified files SHALL report no lint violations.
4. WHEN the `validate_commonmark.py` CI step runs, THE new files SHALL not introduce CommonMark violations within the power directory.
5. WHEN the `validate_power.py` CI step runs, THE power integrity check SHALL pass with the new files present.
6. THE_Coverage_Feature SHALL keep all CI steps passing on Python 3.11, 3.12, and 3.13.

### Requirement 10: Non-Functional and Distribution Constraints

**User Story:** As a power maintainer, I want the new code and fixtures to follow the power's stdlib-only, ship-with-power conventions, so that they integrate cleanly and ship safely to users.

#### Acceptance Criteria

1. THE new predicate and any supporting code in `eval_conversations.py` SHALL use only the Python standard library and SHALL NOT import any third-party dependency.
2. THE_Coverage_Feature SHALL keep all new artifacts within the power tree — Scenario_Fixtures in `senzing-bootcamp/tests/eval/`, the predicate and registration in `senzing-bootcamp/scripts/eval_conversations.py`, and tests in `senzing-bootcamp/tests/`.
3. THE new Scenario_Fixtures SHALL contain no secrets, credentials, personally identifiable information, or MCP server URLs.
4. THE new Scenario_Fixtures SHALL contain no real user data, consistent with the power-distribution safety rule that everything under `senzing-bootcamp/` ships to users.
5. WHEN The_Checker evaluates the full Eval_Directory including the new Scenario_Fixtures, THE_Checker SHALL complete within a few seconds on a developer machine without network access.

### Requirement 11: Deferred Coverage Candidates Recorded

**User Story:** As a power maintainer, I want the coverage candidates not built in v1 recorded as deferred, so that future iterations have a clear backlog and the v1 scope boundary is explicit.

#### Acceptance Criteria

1. THE_Coverage_Feature SHALL record the hook-silence rule (zero visible tokens when a hook check passes) as a deferred candidate, noting the open design question of whether agent silence is expressible as a transcript assertion.
2. THE_Coverage_Feature SHALL record additional mandatory-gate "never offer to skip a ⛔ step" scenarios beyond the existing Module 3 Step 9 fixture as deferred candidates.
3. THE_Coverage_Feature SHALL record additional MCP_First_Invariant branches (for example `explain_error_code` and `generate_scaffold`) beyond the v1 SDK-reference/attribute-name branch as deferred candidates.
4. THE_Coverage_Feature SHALL NOT implement the deferred candidates in v1.
