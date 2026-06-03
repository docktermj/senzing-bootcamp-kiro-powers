# Requirements Document

## Introduction

The Senzing Bootcamp Power already ships a machine-checkable governance conformance layer
(the **governance-rule-conformance** feature): a canonical registry
(`senzing-bootcamp/config/governance-rules.yaml`) that enumerates governing rules and points each
one at its enforcement point(s), a stdlib-only validator
(`senzing-bootcamp/scripts/validate_governance_rules.py`) that evaluates declarative assertions
against the real repository files, a CI step ("Validate governance rules") in
`.github/workflows/validate-power.yml`, and tests in `senzing-bootcamp/tests/test_governance_rules_*.py`.
The validator supports exactly seven assertion types: `substring_present`, `substring_absent`,
`regex_present`, `regex_absent`, `file_exists`, `hook_field_equals` (dotted `key_path` into a JSON
file, terminal value stringified and compared), and `yaml_key_present` (dotted `key_path` existence
in a YAML or JSON file).

This feature is a **focused, additive extension** of that conformance layer. It adds new Rule
Entries to the existing registry to close two coverage gaps that the registry does not currently
describe, so that drift in these two areas fails CI through the same canonical artifact instead of
remaining invisible to the governance layer until a manual audit. It does **not** redesign the
validator, change the assertion vocabulary (see the explicit reuse constraint in Requirement 7), or
move any existing enforcement logic.

### Gap 1 — the governance registry does not cover the agentStop hook contract

Exactly five hooks fire on `agentStop` (verified against the real hook files):

- `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`
- `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook`
- `senzing-bootcamp/hooks/module-recap-append.kiro.hook`
- `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook`
- `senzing-bootcamp/hooks/enforce-visualization-offers.kiro.hook`

Each of these five declares `when.type` equal to `agentStop`. The hook
`senzing-bootcamp/hooks/session-log-events.kiro.hook` declares `when.type` equal to `postToolUse`
(not `agentStop`) and is therefore **not** a member of the agentStop hook set.

**Verified existing state (this is a correction to the original gap framing):** the intended
ordering and contract of these five hooks is **already documented** in
`senzing-bootcamp/steering/hook-architecture.md` (a `manual`-inclusion steering file authored by the
**hook-architecture-improvements** feature), and the precedence order is **already represented
machine-readably** by the `agentstop_order` mapping in `senzing-bootcamp/hooks/hook-categories.yaml`
(each entry carries an integer `order` and a `rationale`). A repo-root property test
(`tests/test_agentstop_order_properties.py`) already asserts that the set of `agentstop_order` ids
equals the set of hooks whose `when.type` is `agentStop`.

The remaining, accurate gap is therefore narrower than "undocumented and unchecked": the
**governance registry itself contains no Rule Entry** linking the agentStop hook contract to its
enforcement points. Within the canonical conformance layer — the single artifact that is supposed to
enumerate governing rules and their enforcement — this linkage is absent, so the registry/validator
would not catch a silently added sixth agentStop hook, a removed or re-typed member, a deleted
`hook-architecture.md`, or a missing `agentstop_order` mapping. This feature adds registry coverage
so the governance layer asserts: the five hook files exist, each declares `when.type` equal to
`agentStop`, the contract documentation exists and states the five-hook membership and precedence,
and the machine-readable order mapping exists and references each of the five hooks.

Because the existing assertion vocabulary cannot extract and compare the integer `order` fields in a
list-of-mappings, the **statically-checkable** governance assertions are SET membership plus
trigger-type plus documentation presence; whether the numeric ordering itself should be statically
asserted is flagged as a design-phase decision in Requirement 4 (the recommendation is to rely on
documentation presence and the existing repo-root set-equality test rather than expand the
validator).

### Gap 2 — the governance registry does not cover MCP config drift between docs and `mcp.json`

`senzing-bootcamp/mcp.json` is the single source of truth for MCP configuration. It declares the
server name `senzing-mcp-server` and `disabledTools` equal to `["submit_feedback"]` (verified).
`senzing-bootcamp/POWER.md` documents both facts: it states the server name `senzing-mcp-server`
and that `submit_feedback` is disabled. No Rule Entry currently asserts that these stay consistent,
so documentation could drift from `mcp.json` without the governance layer noticing. This feature
adds registry coverage so the governance layer asserts that `mcp.json` keeps the `senzing-mcp-server`
server, keeps `submit_feedback` configured as a disabled tool, and that `POWER.md` remains
consistent with both facts.

### Scope decisions resolved in these requirements

- **Additive only.** This feature adds Rule Entries to the existing registry and (if needed) the
  test coverage for those entries. It does not modify the validator, the assertion vocabulary, or
  the existing CI step (Requirement 7, Requirement 9).
- **Existing assertion vocabulary only.** Both gaps are expressible with the existing seven
  assertion types; no new Assertion Type is introduced (Requirement 7).
- **No new CI step.** The "Validate governance rules" step in `.github/workflows/validate-power.yml`
  already runs the validator over the whole registry, so the new Rule Entries are exercised by the
  existing step with no workflow change (Requirement 10).
- **Conformance preserved.** Every new assertion holds against the real current repository, so the
  shipped registry still passes the validator (exit 0) and the existing conformance test stays green
  (Requirement 8).
- **Ordering decision deferred.** Whether the numeric agentStop precedence order is statically
  asserted is left to the design phase, bounded by Requirement 4; these requirements do not
  pre-decide it and do not require a new Assertion Type for it.

## Glossary

- **The_System**: The governance-hook-and-mcp-coverage feature — the set of new Rule Entries added
  to the existing governance registry (plus any test coverage for those entries) that close Gap 1
  and Gap 2.
- **Registry**: The existing canonical file `senzing-bootcamp/config/governance-rules.yaml` that
  enumerates governing rules and their enforcement linkage.
- **Validator**: The existing script `senzing-bootcamp/scripts/validate_governance_rules.py` that
  loads the Registry and evaluates every Assertion against the actual repository files.
- **Rule_Entry**: A single entry in the Registry describing one governing rule, with the fields
  `id`, `rule`, `category`, `enforced_by`, and `assertions`.
- **Assertion**: A declarative, checkable condition attached to a Rule_Entry that the Validator
  evaluates against repository files.
- **Assertion_Type**: One of the seven existing kinds of Assertion: `substring_present`,
  `substring_absent`, `regex_present`, `regex_absent`, `file_exists`, `hook_field_equals`, and
  `yaml_key_present`.
- **AgentStop_Hook_Set**: The exactly five hook files whose `when.type` equals `agentStop`:
  `ask-bootcamper`, `module-completion-celebration`, `module-recap-append`, `enforce-gate-on-stop`,
  and `enforce-visualization-offers` (each at `senzing-bootcamp/hooks/<id>.kiro.hook`).
- **Hook_Architecture_Documentation**: The existing steering file
  `senzing-bootcamp/steering/hook-architecture.md` that records the AgentStop_Hook_Set membership,
  the intended precedence order, and the per-hook contract.
- **AgentStop_Order_Mapping**: The existing `agentstop_order` mapping in
  `senzing-bootcamp/hooks/hook-categories.yaml`, the machine-readable record of the agentStop
  precedence order.
- **MCP_Config**: The single source of truth for MCP configuration,
  `senzing-bootcamp/mcp.json`, a JSON document.
- **Power_Documentation**: The power overview document `senzing-bootcamp/POWER.md`.
- **Path_Base**: The repository root (the directory containing `senzing-bootcamp/` and `.github/`),
  against which every Registry `file` path is resolved, as documented in the Registry header.

## Requirements

### Requirement 1: AgentStop Hook Set Membership Rule Entry

**User Story:** As a power maintainer, I want the governance registry to assert that exactly the five
known agentStop hook files exist, so that silent removal of a member becomes a CI failure visible in
the canonical conformance layer.

#### Acceptance Criteria

1. THE Registry SHALL include a Rule_Entry that covers the AgentStop_Hook_Set, with a unique `id`,
   the rule text, a `category`, an `enforced_by` list naming the five hook files, and one or more
   `assertions`.
2. THE Rule_Entry for the AgentStop_Hook_Set SHALL include a `file_exists` Assertion for each of the
   five hook files: `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`,
   `senzing-bootcamp/hooks/module-completion-celebration.kiro.hook`,
   `senzing-bootcamp/hooks/module-recap-append.kiro.hook`,
   `senzing-bootcamp/hooks/enforce-gate-on-stop.kiro.hook`, and
   `senzing-bootcamp/hooks/enforce-visualization-offers.kiro.hook`.
3. THE Rule_Entry for the AgentStop_Hook_Set SHALL exclude
   `senzing-bootcamp/hooks/session-log-events.kiro.hook` from both its `enforced_by` list and its
   `assertions`, because that hook declares `when.type` equal to `postToolUse`.
4. WHEN the Validator evaluates the AgentStop_Hook_Set Rule_Entry against the real repository, THE
   Validator SHALL exit with status code 0 for that Rule_Entry, because all five files exist.

### Requirement 2: AgentStop Trigger-Type Rule Entry

**User Story:** As a power maintainer, I want the governance registry to assert that each of the five
agentStop hooks still declares the `agentStop` trigger, so that a member silently re-typed to a
different trigger becomes a CI failure.

#### Acceptance Criteria

1. THE Registry SHALL assert, for each of the five members of the AgentStop_Hook_Set, that the hook
   file's `when.type` field equals the string `agentStop`, using the `hook_field_equals`
   Assertion_Type with `key_path` equal to `when.type` and `value` equal to `agentStop`.
2. THE trigger-type assertions SHALL reference each hook file by its repository path resolved against
   the Path_Base (for example, `senzing-bootcamp/hooks/ask-bootcamper.kiro.hook`).
3. WHEN the Validator evaluates the trigger-type assertions against the real repository, THE
   Validator SHALL exit with status code 0 for those assertions, because each of the five hooks
   declares `when.type` equal to `agentStop`.
4. THE Registry SHALL NOT add a trigger-type Assertion for
   `senzing-bootcamp/hooks/session-log-events.kiro.hook` expecting `agentStop`, because that hook
   declares `when.type` equal to `postToolUse`.

### Requirement 3: AgentStop Contract Documentation Rule Entry

**User Story:** As a power maintainer, I want the governance registry to assert that the agentStop
hook contract remains documented and machine-represented, so that deleting the documentation or the
order mapping becomes a CI failure visible in the conformance layer.

#### Acceptance Criteria

1. THE Registry SHALL include an Assertion that the Hook_Architecture_Documentation file
   `senzing-bootcamp/steering/hook-architecture.md` exists, using the `file_exists` Assertion_Type.
2. THE Registry SHALL include one or more `substring_present` Assertions against
   `senzing-bootcamp/steering/hook-architecture.md` confirming that the file states the
   five-member AgentStop_Hook_Set and its intended precedence, using anchor text that exists in the
   actual file (for example, the statement that exactly five hooks fire on `agentStop`).
3. THE Registry SHALL include a `yaml_key_present` Assertion against
   `senzing-bootcamp/hooks/hook-categories.yaml` with `key_path` equal to `agentstop_order`,
   confirming that the AgentStop_Order_Mapping is present.
4. THE Registry SHALL include `substring_present` Assertions against
   `senzing-bootcamp/hooks/hook-categories.yaml` confirming that the AgentStop_Order_Mapping
   references each of the five AgentStop_Hook_Set member ids, using anchor text that exists in the
   actual file (for example, an `id: <hook-id>` line per member).
5. WHEN the Validator evaluates the contract-documentation Assertions against the real repository,
   THE Validator SHALL exit with status code 0 for those Assertions, because the documentation and
   the order mapping exist and contain the asserted anchor text.

### Requirement 4: AgentStop Ordering — Design-Phase Decision Boundary

**User Story:** As a power maintainer, I want the requirements to bound how the agentStop precedence
order is treated without pre-deciding the design, so that the conformance layer stays consistent
with the existing validator and is not expanded unnecessarily.

#### Acceptance Criteria

1. THE_System SHALL treat the SET membership of the AgentStop_Hook_Set (Requirement 1), the
   trigger-type of each member (Requirement 2), and the presence of the contract documentation and
   order mapping (Requirement 3) as the statically-checkable governance assertions for the agentStop
   contract.
2. THE design phase SHALL decide whether the numeric precedence order recorded in the
   AgentStop_Order_Mapping is statically asserted; THESE requirements SHALL NOT pre-decide that
   outcome.
3. WHERE the existing seven Assertion_Types cannot express an ordered-integer comparison over a
   list-of-mappings, THE_System SHALL rely on documentation-presence Assertions for the intended
   order (Requirement 3) rather than verifying the integer order values.
4. THE_System SHALL NOT introduce a new Assertion_Type solely to verify the numeric agentStop
   ordering, given that the order is recorded in the Hook_Architecture_Documentation and the
   AgentStop_Order_Mapping and that set-equality is already covered by the existing repo-root test
   `tests/test_agentstop_order_properties.py`.

### Requirement 5: MCP Server Name Consistency Rule Entry

**User Story:** As a power maintainer, I want the governance registry to assert that the MCP server
name in `mcp.json` is the documented `senzing-mcp-server` and that `POWER.md` stays consistent, so
that server-name drift between docs and the single source of truth becomes a CI failure.

#### Acceptance Criteria

1. THE Registry SHALL include a Rule_Entry that covers MCP server-name consistency, with a unique
   `id`, the rule text, a `category`, an `enforced_by` list naming
   `senzing-bootcamp/mcp.json` and `senzing-bootcamp/POWER.md`, and one or more `assertions`.
2. THE Registry SHALL include a `yaml_key_present` Assertion against `senzing-bootcamp/mcp.json` with
   `key_path` equal to `mcpServers.senzing-mcp-server`, confirming the server name key is present in
   the single source of truth.
3. THE Registry SHALL include a `substring_present` Assertion against `senzing-bootcamp/POWER.md`
   with `value` equal to `senzing-mcp-server`, confirming the Power_Documentation references the same
   server name.
4. WHEN the Validator evaluates the server-name Assertions against the real repository, THE Validator
   SHALL exit with status code 0 for those Assertions, because `mcp.json` declares the
   `senzing-mcp-server` server and `POWER.md` references it.

### Requirement 6: MCP Disabled-Tool Consistency Rule Entry

**User Story:** As a power maintainer, I want the governance registry to assert that `submit_feedback`
remains configured as a disabled tool in `mcp.json` and is documented as disabled in `POWER.md`, so
that re-enabling it silently, or docs drifting from `mcp.json`, becomes a CI failure.

#### Acceptance Criteria

1. THE Registry SHALL include a Rule_Entry that covers MCP disabled-tool consistency, with a unique
   `id`, the rule text, a `category`, an `enforced_by` list naming `senzing-bootcamp/mcp.json` and
   `senzing-bootcamp/POWER.md`, and one or more `assertions`.
2. THE Registry SHALL assert, using an existing Assertion_Type, that `submit_feedback` is configured
   as a disabled tool in `senzing-bootcamp/mcp.json` — for example, a `hook_field_equals` Assertion
   with `key_path` equal to `mcpServers.senzing-mcp-server.disabledTools` and `value` equal to the
   stringified disabled-tools list, or a `regex_present` Assertion matching the `disabledTools` array
   containing `submit_feedback`.
3. THE Registry SHALL include a `substring_present` Assertion against `senzing-bootcamp/POWER.md`
   with `value` equal to `submit_feedback`, confirming the Power_Documentation references the
   disabled tool.
4. WHEN the Validator evaluates the disabled-tool Assertions against the real repository, THE
   Validator SHALL exit with status code 0 for those Assertions, because `mcp.json` lists
   `submit_feedback` in `disabledTools` and `POWER.md` references it.
5. THE design phase SHALL choose the exact existing Assertion_Type and parameters used to express the
   `mcp.json` disabled-tool check; THESE requirements SHALL NOT pre-decide between the
   `hook_field_equals` and `regex_present` formulations, provided the chosen form uses an existing
   Assertion_Type and holds against the real repository.

### Requirement 7: Reuse of the Existing Assertion Vocabulary

**User Story:** As a power maintainer, I want this feature to use only the existing seven assertion
types, so that the validator and its tests are not expanded for an additive, focused change.

#### Acceptance Criteria

1. THE_System SHALL express every new Assertion using one of the existing seven Assertion_Types
   (`substring_present`, `substring_absent`, `regex_present`, `regex_absent`, `file_exists`,
   `hook_field_equals`, `yaml_key_present`).
2. THE_System SHALL NOT introduce a new Assertion_Type for Gap 1 or Gap 2.
3. THE_System SHALL NOT modify `senzing-bootcamp/scripts/validate_governance_rules.py` to add,
   remove, or change the supported Assertion_Types.
4. IF the design phase determines that a gap genuinely cannot be expressed with the existing seven
   Assertion_Types, THEN THE_System SHALL document the explicit justification, SHALL note that the
   change expands the Validator and its tests, and SHALL surface the decision for review before
   implementation.

### Requirement 8: Shipped Registry Remains Conformant

**User Story:** As a power maintainer, I want every new assertion to hold against the real repository,
so that the shipped registry still passes the validator and the existing conformance test stays
green.

#### Acceptance Criteria

1. THE_System SHALL reference, in every new Assertion, only paths, keys, and strings that exist in
   the actual current repository, and SHALL NOT invent unverified facts.
2. WHEN the Validator runs over the full Registry including the new Rule_Entries against the real
   repository, THE Validator SHALL exit with status code 0.
3. THE existing conformance test in `senzing-bootcamp/tests/` (which asserts the shipped
   `governance-rules.yaml` passes the Validator) SHALL continue to pass with the new Rule_Entries
   present.
4. THE_System SHALL assign each new Rule_Entry an `id` that is unique across the entire Registry.

### Requirement 9: Additive, Non-Disruptive Change

**User Story:** As a power maintainer, I want this feature to stay tightly scoped to the two gaps, so
that the validator design, the enforcement logic, and the power distribution rules are untouched.

#### Acceptance Criteria

1. THE_System SHALL implement Gap 1 and Gap 2 by adding Rule_Entries to the existing Registry
   `senzing-bootcamp/config/governance-rules.yaml`.
2. THE_System SHALL reference existing enforcement points (hook files, steering files, `mcp.json`,
   `POWER.md`, `hook-categories.yaml`) WITHOUT relocating, duplicating, or modifying the enforcement
   logic those points contain.
3. THE_System SHALL NOT introduce any MCP server URL or hardcoded external endpoint outside
   `senzing-bootcamp/mcp.json`.
4. THE_System SHALL place all new and changed shipped artifacts within the `senzing-bootcamp/`
   structure, with no developer-only files placed there.
5. WHERE the new Rule_Entries are stored, THE Registry SHALL keep the existing constrained YAML
   subset format (double-quoted assertion `value`/`pattern` scalars, two-space indentation,
   repository-root Path_Base) so the existing stdlib-only Validator parses them unchanged.

### Requirement 10: CI Remains Green

**User Story:** As a power maintainer, I want the new registry entries to keep the full CI pipeline
green through the existing governance step, so that no workflow change is required and broken linkage
fails the build automatically.

#### Acceptance Criteria

1. THE_System SHALL rely on the existing "Validate governance rules" step in
   `.github/workflows/validate-power.yml` to evaluate the new Rule_Entries, WITHOUT adding a new CI
   step.
2. WHEN CI runs the existing governance step over the real repository with the new Rule_Entries
   present, THE governance step SHALL pass.
3. THE_System SHALL keep the following CI checks green with the new Rule_Entries present:
   `validate_power`, `measure_steering --check`, `validate_commonmark`, `validate_dependencies`,
   `sync_hook_registry --verify`, `validate_prerequisites`, `validate_progress_ci`,
   `validate_mandatory_gates`, `validate_governance_rules`, `validate_yaml_schemas`, `ruff`, and
   `pytest`.
4. IF the Validator exits with status code 1 during CI because a new Assertion fails, THEN the CI job
   SHALL fail.

### Requirement 11: Test Coverage for the New Rule Entries

**User Story:** As a power maintainer, I want test coverage confirming the new rule entries are
present and conformant, so that accidental removal or drift of these entries is caught.

#### Acceptance Criteria

1. THE_System SHALL provide test coverage in `senzing-bootcamp/tests/` verifying that the new
   Rule_Entries for the AgentStop_Hook_Set, the agentStop trigger-type, the agentStop contract
   documentation, MCP server-name consistency, and MCP disabled-tool consistency are present in the
   shipped Registry by their `id`.
2. THE test coverage SHALL verify that the Validator exits with status code 0 over the real
   repository with the new Rule_Entries present (conformance), reusing or extending the existing
   conformance test rather than duplicating the Validator's own behavioral property tests.
3. THE test coverage SHALL follow the repository test conventions: class-based organization,
   `from __future__ import annotations`, type hints (`X | None`, `list[str]`), `st_`-prefixed
   Hypothesis strategies where property tests are used, and `@settings(max_examples=20)` on any
   property test.
4. WHERE a property test is added, THE test SHALL document which requirements it validates.
5. THE test coverage SHALL reside in `senzing-bootcamp/tests/` and SHALL use the Python standard
   library and Hypothesis only.
