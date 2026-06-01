# Implementation Plan: Governance Rule Conformance

## Overview

This plan builds the governance-rule-conformance feature as a single stdlib-only Python
validator plus a canonical YAML registry, wired into CI and covered by pytest + Hypothesis
tests. Work proceeds in dependency order — **parser → schema → assertion evaluators →
orchestration/CLI → seed registry → CI → conformance** — so each step builds on the last and
ends fully integrated. Tests are written close to the code they validate to catch errors early.

The validator lives at `senzing-bootcamp/scripts/validate_governance_rules.py` (stdlib only,
no PyYAML). The registry lives at `senzing-bootcamp/config/governance-rules.yaml`. Tests live
in `senzing-bootcamp/tests/`. All code follows the repo's python-conventions: `from __future__
import annotations`, `X | None` / `list[str]` type hints, dataclasses, argparse `main(argv=None)`,
class-based pytest, `st_`-prefixed Hypothesis strategies, and `@settings(max_examples=20)`.

## Tasks

- [ ] 1. Scaffold the validator module and core data model
  - [ ] 1.1 Create `senzing-bootcamp/scripts/validate_governance_rules.py` skeleton
    - Add `#!/usr/bin/env python3` shebang and a module docstring with CLI usage examples
    - Add `from __future__ import annotations` and stdlib-only imports (`argparse`, `json`, `re`, `sys`, `dataclasses`, `pathlib.Path`)
    - Define the `Assertion`, `RuleEntry`, `Violation`, and `RunResult` `@dataclass(frozen=True)` types exactly as in the design's Data Models section (fields, defaults, and type hints)
    - Add an argparse-based `main(argv: list[str] | None = None) -> int` skeleton with `--registry` and `--repo-root` options, repo-root inference via `Path(__file__).resolve().parent.parent.parent`, default registry path `<repo_root>/senzing-bootcamp/config/governance-rules.yaml`
    - Add `if __name__ == "__main__": sys.exit(main())`
    - Do NOT introduce any MCP/external URL anywhere in the module
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 4.8_

- [ ] 2. Implement the minimal-YAML registry parser
  - [ ] 2.1 Implement `load_registry(path: Path) -> list[dict]`
    - Parse the constrained YAML subset from the design: a single top-level `rules:` block-sequence; list items are mappings of double-quoted scalar values; `enforced_by` as a block-sequence of scalars; `assertions` as a block-sequence of mappings; `static_checkable` as a bare boolean
    - Decode the fixed escape table inside double quotes (`\\`, `\"`, `\n`, `\t`, `\uXXXX`) and accept the 👉 emoji written literally (UTF-8 text)
    - Ignore comments (`#`) and blank lines; assume two-space indentation per level
    - Raise a typed load error when the file is missing, unreadable, or not parseable (unterminated quote, bad indentation, non-`rules` top key)
    - _Requirements: 4.1, 4.7, 3.8_

  - [ ]* 2.2 Write parser round-trip property test
    - Create `senzing-bootcamp/tests/test_governance_rules_properties.py` with the shared `st_assertion`, `st_rule_entry`, and `st_registry` Hypothesis strategies (values may contain backslashes, double quotes, newlines, and the 👉 emoji) and a YAML-subset renderer helper for generated entries
    - Import the script via `sys.path` insertion of the `scripts/` directory
    - **Property 1: Parser round-trip preserves structure (including regex and emoji)**
    - Assert that render → `load_registry` → `validate_schema` yields `RuleEntry`/`Assertion` structures equal to the originals
    - **Validates: Requirements 4.1**

- [ ] 3. Implement registry schema validation
  - [ ] 3.1 Implement `validate_schema(raw_entries: list[dict]) -> tuple[list[RuleEntry], list[Violation]]`
    - Convert raw mappings into `RuleEntry`/`Assertion` dataclasses while collecting schema `Violation`s
    - Enforce required fields (`id`, `rule`, `category`, `enforced_by`, `assertions`); treat empty `enforced_by`/`assertions` as missing, except `assertions` may be empty when `static_checkable` is `false`
    - Enforce non-empty, unique `id` across entries (duplicate-id violation)
    - Detect unsupported assertion types FIRST and return before any content evaluation (precedence + halt)
    - Detect assertions missing a parameter required by their type (malformed-assertion violation)
    - Schema-level problems are collected here and HALT before content evaluation; the run exits with status code 1
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8, 2.9, 3.9, 3.10_

  - [ ]* 3.2 Write schema property tests
    - Add to `test_governance_rules_properties.py`
    - **Property 2: Schema requires every required field** — _Validates: Requirements 2.1, 2.3, 2.4, 2.5, 2.6, 2.8_
    - **Property 3: Duplicate ids are rejected** — _Validates: Requirements 2.2, 2.9_
    - **Property 9: Unsupported assertion type halts at schema stage** (even amid other errors; no content evaluation) — _Validates: Requirements 3.9_
    - **Property 10: Missing required parameter is a malformed-assertion violation** — _Validates: Requirements 3.10_
    - Decorate each property with `@settings(max_examples=20)` and tag the property number + validated requirements

  - [ ]* 3.3 Write schema example tests
    - Create `senzing-bootcamp/tests/test_governance_rules_schema.py` (class-based)
    - Cover concrete cases: missing each required field individually, duplicate `id`, an unsupported assertion `type`, and an assertion missing its required parameter
    - _Requirements: 2.1, 2.2, 2.8, 2.9, 3.9, 3.10, 11.4_

- [ ] 4. Implement the assertion evaluator
  - [ ] 4.1 Implement `evaluate_assertion(assertion: Assertion, repo_root: Path) -> Violation | None`
    - Dispatch on `assertion.type` for all seven types: `substring_present`, `substring_absent`, `regex_present` (via `re.search`), `regex_absent`, `file_exists`, `hook_field_equals` (via `json.load` + dotted `key_path` traversal, terminal value stringified for comparison), `yaml_key_present` (dotted `key_path` existence check)
    - Apply the missing-file rule: for every type except `file_exists`, a non-existent target file fails the assertion and names the missing file as the cause
    - Catch internal evaluation errors (invalid regex raising `re.error`, malformed JSON during `hook_field_equals`) and convert them into a content `Violation` describing the cause rather than crashing
    - Resolve every `file` path relative to `repo_root`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.5_

  - [ ]* 4.2 Write assertion-evaluator property tests
    - Add to `test_governance_rules_properties.py`, using oracle comparison (Python `in`, `re.search`, filesystem, dotted traversal) with `tmp_path`-backed files
    - **Property 4: Substring assertions agree with the membership oracle** (both polarities) — _Validates: Requirements 3.1, 3.2_
    - **Property 5: Regex assertions agree with the re.search oracle** (both polarities) — _Validates: Requirements 3.3, 3.4_
    - **Property 6: file_exists matches filesystem reality** — _Validates: Requirements 3.5_
    - **Property 7: hook_field_equals matches dotted JSON traversal** — _Validates: Requirements 3.6_
    - **Property 8: yaml_key_present matches dotted key existence** — _Validates: Requirements 3.7_
    - **Property 11: Missing target file fails non-existence-tolerant assertions** (violation names the missing file) — _Validates: Requirements 4.5_

- [ ] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement orchestration, reporting, and the CLI
  - [ ] 6.1 Implement `evaluate_rule` and `run` orchestration with exit-code logic
    - `evaluate_rule(entry, repo_root) -> list[Violation]`: evaluate all assertions of one rule; skip behavioral-only entries (`static_checkable: false`) without failing on them
    - `run(registry_path, repo_root) -> RunResult`: orchestrate load → schema → evaluate-all; on a structurally valid registry, evaluate every assertion of every statically-checkable rule (collect-all, never stop at the first failure)
    - Compute the canonical exit code: 0 iff the registry is structurally valid AND every evaluated assertion holds AND no internal error occurred; 1 in every other case
    - Set `RunResult.completed` True only when evaluation ran to completion (a schema/load halt leaves it False)
    - _Requirements: 4.2, 4.3, 4.4, 4.4a, 4.6, 8.4, 5.5_

  - [ ] 6.2 Implement violation reporting and wire `main`
    - Render each `Violation` separately to **stderr**, including the failing rule `id`, the failing assertion's type and parameters, and the file path involved (for content violations)
    - On success, write the success message and completion counts (Rule Entries checked, Violations found) to **stdout**; emit completion counts ONLY after a full evaluation pass (suppress on load/schema halt)
    - Wire `main` to resolve paths, call `run`, route reporting, and return the exit code
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 4.8, 6.4_

  - [ ]* 6.3 Write orchestration and reporting property tests
    - Add to `test_governance_rules_properties.py`, using `capsys`/`tmp_path` and registries with deliberately failing assertions and interspersed `static_checkable: false` entries
    - **Property 12: Structurally valid registries are evaluated completely (collect-all, behavioral-skip)** — _Validates: Requirements 4.2, 4.6, 8.2, 8.4_
    - **Property 13: Canonical exit-code contract** — _Validates: Requirements 4.3, 4.4, 6.4, 11.2_
    - **Property 14: Violation reporting is complete and on stderr** — _Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.6, 11.5_
    - **Property 15: Completion counts are emitted only on full completion** — _Validates: Requirements 5.5_

  - [ ]* 6.4 Write load-error and CLI example tests
    - Create `senzing-bootcamp/tests/test_governance_rules_validator.py` (class-based)
    - Cover load errors (missing/unreadable/unparseable registry → exit 1, no completion counts), `main([])` and `main(["--registry", ...])` behavior, stderr-vs-stdout routing, and behavioral-only skip; assert the eight seed-rule `id`s are present in the shipped registry
    - _Requirements: 4.7, 8.2, 11.2, 11.5_

- [ ] 7. Author the seed registry
  - [ ] 7.1 Create `senzing-bootcamp/config/governance-rules.yaml`
    - Add the documented header comment block: PATH BASE (repository root), ASSERTION VALUES encoding/escape table, BEHAVIORAL-ONLY convention, and the 👉 `validate_behavior_rules.py` OVERLAP NOTE
    - Add the eight statically-checkable rule entries using the exact verified paths/markers from the design's Seed Registry Content table: `pointer-prefix`, `mcp-first`, `rule-06-license-mcp`, `rule-15-module3-visualization-gate`, `hook-name-form` (one `regex_present` per `*.kiro.hook` file with `name` beginning `to `), `feedback-file-path`, `frontmatter-inclusion`, `graduation-completion-summary`
    - Add the behavioral-only entries with `static_checkable: false` and empty `assertions` (e.g. `no-ambiguous-yes-no`)
    - Use only paths/markers/strings that exist in the real repository (no invented facts)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.1, 8.2, 8.3, 1.1, 1.2, 1.3, 1.4, 1.5, 2.7_

- [ ] 8. Verify the shipped registry is conformant
  - [ ]* 8.1 Write the conformance test
    - Create `senzing-bootcamp/tests/test_governance_rules_conformance.py` (class-based)
    - Run the validator over the real repository with the shipped `governance-rules.yaml` (default paths) and assert exit code 0 — the conformance layer is itself conformant
    - _Requirements: 7.9, 11.8_

- [ ] 9. Wire the validator into CI
  - [ ] 9.1 Add the "Validate governance rules" step to `.github/workflows/validate-power.yml`
    - Insert `run: python senzing-bootcamp/scripts/validate_governance_rules.py` immediately after the "Validate mandatory gates" step and before the "Validate YAML schemas" step, keeping it grouped with the existing validation steps
    - Rely on default path resolution so it loads the shipped registry and infers the repo root
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 10. Final checkpoint - Ensure all checks pass
  - Run the new test files (`test_governance_rules_properties.py`, `_schema.py`, `_validator.py`, `_conformance.py`) and confirm they pass
  - Run `python senzing-bootcamp/scripts/validate_governance_rules.py` and confirm exit 0
  - Run `ruff check` on the new script and test files
  - Run `validate_power.py`, `validate_commonmark.py`, `validate_yaml_schemas.py`, and `sync_hook_registry.py --verify` to confirm nothing regressed
  - Confirm no PyYAML import and no MCP/external URL was added
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional test tasks and can be skipped for a faster MVP; core implementation, the seed registry, and CI wiring are never marked optional.
- Each task references specific requirement sub-clauses for traceability.
- Property test sub-tasks each name the design property number(s) and the requirement clauses they validate; all property tests live in `test_governance_rules_properties.py` and use `@settings(max_examples=20)`.
- Schema errors halt before content evaluation; content violations are collected across the whole run (collect-all).
- The validator and registry are stdlib-only (no PyYAML) and introduce no external endpoints.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "3.1"] },
    { "id": 3, "tasks": ["3.2", "3.3", "4.1"] },
    { "id": 4, "tasks": ["4.2", "6.1", "7.1"] },
    { "id": 5, "tasks": ["6.2"] },
    { "id": 6, "tasks": ["6.3", "6.4", "9.1"] },
    { "id": 7, "tasks": ["8.1"] }
  ]
}
```
