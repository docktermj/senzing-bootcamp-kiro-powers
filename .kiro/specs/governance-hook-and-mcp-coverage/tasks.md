# Implementation Plan: governance-hook-and-mcp-coverage

## Overview

This is a focused, additive change to the existing `governance-rule-conformance` layer. The work is:

1. Append five new Rule Entries to the canonical registry
   `senzing-bootcamp/config/governance-rules.yaml`, using only the existing seven assertion types in
   the constrained YAML subset (double-quoted scalars, two-space indentation, repository-root
   `Path_Base`). The literal YAML blocks are given verbatim in the design's Data Models section.
2. Update one hard-coded literal in an existing test so the suite stays green (the five new
   statically-checkable entries raise the validator's rule-count from 8 to 13).
3. Add a new stdlib-only, class-based test file asserting the new entries are present and conformant.
4. Verify the shipped registry stays at exit 0 over the real repo and that the validator script and CI
   workflow are untouched.

The validator (`senzing-bootcamp/scripts/validate_governance_rules.py`) and the CI workflow
(`.github/workflows/validate-power.yml`) are NOT modified — the existing "Validate governance rules"
step already runs the validator over the whole registry. There are no property tests (the design omits
a Correctness Properties section intentionally; Hypothesis is not used here).

## Tasks

- [ ] 1. Extend the governance registry with the five new Rule Entries
  - [ ] 1.1 Append the five Rule Entries to `senzing-bootcamp/config/governance-rules.yaml`
    - Add the five entries verbatim from the design's Data Models section, appended to the existing
      `rules:` block sequence after the seed/behavioral entries, in the constrained YAML subset
      (double-quoted `value`/`pattern` scalars, two-space indentation, repository-root-relative `file`
      paths) so the existing stdlib parser reads them unchanged.
    - `agentstop-hook-set` — category `hook-architecture`; `enforced_by` lists the five agentStop hook
      files; five `file_exists` assertions, one per hook file. Exclude
      `senzing-bootcamp/hooks/session-log-events.kiro.hook` (it is `postToolUse`, not a member).
      _Requirements: 1.1, 1.2, 1.3, 1.4_
    - `agentstop-trigger-type` — category `hook-architecture`; five `hook_field_equals` assertions with
      `key_path: when.type` and `value: agentStop`, one per member hook; no assertion for
      `session-log-events`. _Requirements: 2.1, 2.2, 2.3, 2.4_
    - `agentstop-contract-doc` — category `hook-architecture`; `file_exists` for
      `steering/hook-architecture.md`; two `substring_present` anchors against it (the five-hook
      statement and the precedence sentence, exact strings from the file); `yaml_key_present` with
      `key_path: agentstop_order` against `hooks/hook-categories.yaml`; five `substring_present`
      `id: <hook-id>` anchors (one per member). Do NOT statically assert the numeric `order` integers —
      rely on documentation presence plus the existing repo-root set-equality test (no new assertion
      type). _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4_
    - `mcp-server-name` — category `mcp-integrity`; `enforced_by` lists `mcp.json` and `POWER.md`;
      `yaml_key_present` with `key_path: mcpServers.senzing-mcp-server` against `mcp.json`;
      `substring_present` `senzing-mcp-server` against `POWER.md`. _Requirements: 5.1, 5.2, 5.3, 5.4_
    - `mcp-disabled-tool` — category `mcp-integrity`; `enforced_by` lists `mcp.json` and `POWER.md`;
      `regex_present` against `mcp.json` matching the `disabledTools` array containing
      `submit_feedback` (escaped per the registry escape table); `substring_present` `submit_feedback`
      against `POWER.md`. _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
    - Use only the existing seven assertion types; assign each entry an `id` unique across the whole
      registry; reference only paths, keys, and strings that exist in the real repository so every
      assertion holds (exit 0). Do not modify any referenced enforcement point, introduce any external
      endpoint, or place any developer-only file under `senzing-bootcamp/`.
      _Requirements: 7.1, 7.2, 7.3, 8.1, 8.2, 8.4, 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 2. Add and update test coverage for the new Rule Entries
  - [ ] 2.1 Update the rule-count literal in the existing validator test
    - In `senzing-bootcamp/tests/test_governance_rules_validator.py`, change the hard-coded
      `"Rule Entries checked: 8"` literal (in the `main([])`-over-real-repo case) to
      `"Rule Entries checked: 13"` to reflect the five new statically-checkable entries.
    - Test-data change only — do NOT modify `validate_governance_rules.py` and do not touch any other
      assertion in the file. _Requirements: 8.3, 10.3_

  - [ ]* 2.2 Add the presence + conformance test file
    - Create `senzing-bootcamp/tests/test_governance_hook_and_mcp_coverage.py`: class-based,
      stdlib-only (no Hypothesis / no property tests), `from __future__ import annotations`, type hints
      (`X | None`, `list[str]`), scripts imported via `sys.path` insertion of the `scripts/` directory.
    - `TestNewRuleEntriesPresent`: load the shipped registry via `load_registry`, collect entry ids,
      assert each of `agentstop-hook-set`, `agentstop-trigger-type`, `agentstop-contract-doc`,
      `mcp-server-name`, `mcp-disabled-tool` is present, and assert all registry ids are unique.
      _Requirements: 11.1, 8.4_
    - `TestNewRuleEntriesConformant`: call `run(shipped_registry, repo_root)` over the real checkout;
      assert `exit_code == 0` and `completed is True`; assert no violation's `rule_id` is one of the
      five new ids. Reuse the existing conformance `run` entry point; do not duplicate the validator's
      own behavioral property tests. _Requirements: 11.2, 11.3, 11.5_

- [ ] 3. Checkpoint — verify conformance, tests, lint, and no enforcement/CI drift
  - Run `python senzing-bootcamp/scripts/validate_governance_rules.py`; confirm it prints
    `Governance rule conformance: PASS`, `Rule Entries checked: 13`, `Violations found: 0`, and exits 0.
    If any new assertion fails (e.g. an anchor string is not exactly present), fix the offending
    registry entry to match the real repository — never weaken or remove the enforcement file.
  - Run the three relevant pytest files (single execution, no watch mode):
    `python -m pytest senzing-bootcamp/tests/test_governance_hook_and_mcp_coverage.py
    senzing-bootcamp/tests/test_governance_rules_validator.py
    senzing-bootcamp/tests/test_governance_rules_conformance.py`; confirm all pass (the existing
    conformance test stays green and transitively covers the new entries).
  - Run `ruff check` on the new and edited test files; confirm clean.
  - Confirm the broader CI validators are unaffected (`validate_power`, `validate_commonmark` scoped to
    `senzing-bootcamp`, `sync_hook_registry --verify`, `validate_yaml_schemas`).
  - Confirm NO change was made to `senzing-bootcamp/scripts/validate_governance_rules.py` or to
    `.github/workflows/validate-power.yml` (no new CI step).
  - Ensure all tests pass, ask the user if questions arise.
  - _Requirements: 7.3, 8.2, 8.3, 9.x, 10.1, 10.2, 10.3, 10.4_

## Notes

- The sub-task marked with `*` (2.2) is the added example/conformance test coverage and can be skipped
  for a faster MVP; the registry change (1.1) and the rule-count literal fix (2.1) are core and are not
  optional — skipping 2.1 would break the existing test suite and fail CI (Requirement 10.3).
- Each task references the specific requirement clauses it implements for traceability.
- No property-based tests are included: the design intentionally omits a Correctness Properties section
  because the change is additive registry data over an unchanged validator, so the test shape is
  presence + conformance, not generated-input properties.
- Every new assertion must hold against the real repository. When verification surfaces a mismatch, the
  fix is to correct the registry entry to match reality, never to weaken the enforcement file.
- The validator script and the CI workflow are deliberately left untouched.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] }
  ]
}
```
