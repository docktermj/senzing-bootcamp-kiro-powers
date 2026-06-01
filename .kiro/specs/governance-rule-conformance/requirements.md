# Requirements Document

## Introduction

The Senzing Bootcamp Power is governed by a set of high-level "governing rules" (for example: "ALWAYS prefix bootcamper prompts with 👉", the MCP-First Invariant requiring Senzing facts to come from MCP tool calls, Rule 6 "If the current Senzing license is insufficient, consult the Senzing MCP server for a temporary license", Rule 15 "In Module 3, ALWAYS create the visualization", "all hook names are of the form 'to (verb phrase)'", and "graduation ALWAYS creates the completion-summary"). Today these rules are enforced by scattered steering files, hooks, and scripts, but no single artifact enumerates the governing rules or maps each rule to the file(s), hook(s), or marker(s) that enforce it. Enforcement can therefore silently drift from the stated rule — recent real examples include a rule satisfied only by prose instead of an enforced MCP call, and a mandatory gate that contained an escape hatch contradicting the rule. Drift stays invisible until a human manually audits.

This feature adds a machine-checkable conformance layer that ties each governing rule to its enforcement point(s) and fails CI when the linkage is broken. It consists of four parts:

1. A canonical **registry** file (`senzing-bootcamp/config/governance-rules.yaml`) that enumerates each governing rule with a stable id, the rule text, a category, the enforcement points (`enforced_by`), and one or more checkable `assertions`.
2. A **validator** script (`senzing-bootcamp/scripts/validate_governance_rules.py`, stdlib-only) that loads the registry and evaluates every assertion against the actual repository files, reporting any rule whose enforcement assertion fails.
3. **CI wiring** in `.github/workflows/validate-power.yml` that runs the validator alongside the existing validation steps.
4. **Tests** in `senzing-bootcamp/tests/` (pytest + Hypothesis) covering the validator behavior and the registry schema.

This feature ADDS a verification layer. It does NOT move existing enforcement logic, and it complements rather than replaces the existing validators (`validate_power.py`, `validate_mandatory_gates.py`, `sync_hook_registry.py`, `validate_behavior_rules.py`). The registry becomes the single source that lists the governing rules and points at where each is enforced.

### Scope decisions resolved in these requirements

- **Seed set for v1**: The registry is seeded with the mechanically-checkable subset of governing rules proven this session (enumerated in Requirement 7). Behavioral rules that can only be verified by observing a live agent conversation are explicitly out of scope for static checking and are recorded as documented-but-not-statically-checkable (Requirement 8).
- **Single source, no enforcement move**: The registry lists the rules and references existing enforcement; the existing scattered enforcement stays exactly where it is (Requirement 1).
- **Relationship to `validate_behavior_rules.py`**: That script validates the four `agent-behavior-rules.md` rules by scanning steering content for behavioral anti-patterns. This feature is broader — a rule→enforcement registry with declarative assertions. These requirements flag the overlap (notably the 👉 pointer rule, which both touch) and require the design phase to decide whether to extend the existing script or stay separate; the requirements do not pre-decide that (Requirement 9).
- **Parser constraint**: The validator is stdlib-only (no PyYAML). The repository convention is custom minimal YAML parsers except `validate_dependencies.py`. The requirements fix the stdlib-only constraint and the declarative assertion vocabulary; the design phase decides the concrete parser approach (Requirement 6, Requirement 10).

## Glossary

- **Governing Rule**: A high-level, human-readable rule that governs the behavior or structure of the Senzing Bootcamp Power (e.g., "ALWAYS prefix prompts with 👉").
- **Registry**: The canonical YAML file `senzing-bootcamp/config/governance-rules.yaml` that enumerates governing rules and their enforcement linkage.
- **Rule Entry**: A single entry in the Registry describing one governing rule, with fields `id`, `rule`, `category`, `enforced_by`, and `assertions`.
- **Rule Id**: A stable, unique string identifier for a Rule Entry (e.g., `pointer-prefix`, `mcp-first`, `rule-06-license-mcp`).
- **Enforcement Point**: A file path, hook id, or marker that enforces a governing rule, listed in a Rule Entry's `enforced_by` field.
- **Assertion**: A declarative, checkable condition attached to a Rule Entry that the Validator evaluates against repository files (e.g., "file X contains string Y", "string S is absent from file X").
- **Assertion Type**: The kind of check an Assertion performs. The supported set is: substring present, substring absent, regex match present, regex match absent, file exists, hook JSON field equals value, and YAML/JSON key present.
- **Validator**: The script `senzing-bootcamp/scripts/validate_governance_rules.py` that loads the Registry and evaluates all Assertions.
- **Violation**: A reported failure where a Rule Entry's Assertion does not hold against the actual repository files.
- **Statically-Checkable Rule**: A governing rule whose conformance can be verified by inspecting repository files without observing a live agent conversation.
- **Behavioral-Only Rule**: A governing rule whose conformance can only be verified by observing live agent runtime behavior, and which is therefore out of scope for static checking in this feature.
- **The_System**: The governance-rule-conformance feature as a whole (Registry + Validator + CI wiring + tests).
- **Bootcamp_Root**: The `senzing-bootcamp/` directory; all Enforcement Point paths in the Registry are interpreted relative to a documented base (repository root or Bootcamp_Root) as fixed in Requirement 2.

## Requirements

### Requirement 1: Canonical Governance Rules Registry

**User Story:** As a power maintainer, I want a single canonical registry file that lists every governing rule and points at where it is enforced, so that there is one authoritative place to see the rules and their enforcement linkage instead of relying on scattered files.

#### Acceptance Criteria

1. THE_System SHALL provide a Registry file at the path `senzing-bootcamp/config/governance-rules.yaml`.
2. THE Registry SHALL be the single artifact that enumerates the governing rules covered by this feature; no other file is required to list them.
3. THE Registry SHALL store data in YAML using a kebab-case filename, consistent with the repository configuration naming convention.
4. THE Registry SHALL reference existing enforcement points by path, hook id, or marker WITHOUT relocating, duplicating, or modifying the enforcement logic those points contain.
5. WHERE a governing rule is added, changed, or removed in the power, THE Registry SHALL be the location updated to reflect that change.

### Requirement 2: Rule Entry Schema and Required Fields

**User Story:** As a power maintainer, I want each rule entry to have a well-defined structure with required fields, so that every rule is described consistently and is machine-checkable.

#### Acceptance Criteria

1. THE Registry SHALL represent each governing rule as a Rule Entry containing the fields `id`, `rule`, `category`, `enforced_by`, and `assertions`.
2. THE `id` field SHALL be a non-empty string that is unique across all Rule Entries in the Registry.
3. THE `rule` field SHALL contain the human-readable governing rule text.
4. THE `category` field SHALL contain a non-empty string classifying the rule.
5. THE `enforced_by` field SHALL contain a list of one or more Enforcement Points, where each Enforcement Point is a repository file path and/or a hook id.
6. THE `assertions` field SHALL contain a list of one or more Assertions.
7. THE Registry SHALL document the base directory against which Enforcement Point paths and Assertion file paths are resolved, so that path interpretation is unambiguous.
8. IF a Rule Entry is missing any required field (`id`, `rule`, `category`, `enforced_by`, or `assertions`), THEN THE Validator SHALL report the Rule Entry as a schema violation and exit with a non-zero status.
9. IF two Rule Entries share the same `id`, THEN THE Validator SHALL report a duplicate-id schema violation and exit with a non-zero status.

### Requirement 3: Assertion Vocabulary

**User Story:** As a power maintainer, I want a small, declarative set of assertion types, so that I can express the conformance checks needed for the seed rules without writing imperative code per rule.

#### Acceptance Criteria

1. THE Registry SHALL support an Assertion that checks a specified substring is PRESENT in a specified file (substring present).
2. THE Registry SHALL support an Assertion that checks a specified substring is ABSENT from a specified file (substring absent).
3. THE Registry SHALL support an Assertion that checks a specified regular expression MATCHES content in a specified file (regex match present).
4. THE Registry SHALL support an Assertion that checks a specified regular expression does NOT match content in a specified file (regex match absent).
5. THE Registry SHALL support an Assertion that checks a specified file EXISTS (file exists).
6. THE Registry SHALL support an Assertion that checks a specified field in a hook JSON file EQUALS a specified value (hook JSON field equals value), where the field is addressable by a documented key path.
7. THE Registry SHALL support an Assertion that checks a specified key is PRESENT in a YAML or JSON file (YAML/JSON key present).
8. THE Assertion vocabulary SHALL be declarative and parseable using the Python standard library only, without requiring third-party YAML or schema libraries.
9. IF an Assertion specifies an Assertion Type that is not in the supported set, THEN THE Validator SHALL stop processing immediately, report an unsupported-assertion-type schema violation, and exit with a non-zero status, even when other validation errors are also present.
10. IF an Assertion is missing a parameter required by its Assertion Type (for example, a missing target file or missing search value), THEN THE Validator SHALL report a malformed-assertion schema violation and exit with a non-zero status.

### Requirement 4: Validator Load and Evaluate Behavior

**User Story:** As a power maintainer, I want a validator that loads the registry and evaluates every assertion against the actual repository files, so that broken rule-to-enforcement linkage is detected automatically.

#### Acceptance Criteria

1. THE Validator SHALL load and parse the Registry file using the Python standard library only.
2. WHEN the Validator runs, THE Validator SHALL evaluate every Assertion of every Rule Entry against the actual repository files.
3. WHEN every Assertion of every Rule Entry holds, THE Validator SHALL report success and exit with status code 0.
4. IF at least one Assertion does not hold, THEN THE Validator SHALL report each failing Assertion and exit with status code 1.
4a. WHEN the Registry is structurally valid AND the Validator completes evaluating every Assertion without an internal error AND no Violation is found, THE Validator SHALL exit with status code 0; in every other case (an internal evaluation error, a load or schema error, or at least one Violation) THE Validator SHALL exit with status code 1.
5. WHEN an Assertion references a file that does not exist and the Assertion Type is not "file exists", THE Validator SHALL treat the Assertion as failed and report the missing file as the cause.
6. WHEN the Registry is structurally valid, THE Validator SHALL evaluate all Rule Entries before exiting, so that a single run reports all content Violations rather than stopping at the first failing Assertion. (Schema-level errors are handled separately per Requirement 2 and Requirement 3, which may halt processing immediately.)
7. IF the Registry file is missing, unreadable, or not parseable, THEN THE Validator SHALL report the load error and exit with status code 1.
8. THE Validator SHALL expose a `main(argv=None)` entry point and an argparse-based command-line interface, consistent with the repository script conventions.

### Requirement 5: Violation Reporting

**User Story:** As a power maintainer, I want each violation message to clearly identify the rule and the failing assertion, so that I can locate and fix drift quickly.

#### Acceptance Criteria

1. WHEN the Validator reports a Violation, THE Validator SHALL include the Rule Id of the failing Rule Entry in the message.
2. WHEN the Validator reports a Violation, THE Validator SHALL include the failing Assertion (its Assertion Type and parameters) in the message.
3. WHEN the Validator reports a Violation caused by file content, THE Validator SHALL include the file path involved in the message.
4. WHEN the Validator reports multiple Violations, THE Validator SHALL list each Violation separately.
5. WHEN the Validator fully completes a run, THE Validator SHALL report the count of Rule Entries checked and the count of Violations found; IF the run is interrupted or aborted before completion, THEN THE Validator SHALL NOT emit the completion counts.
6. WHEN the Validator exits with status code 1 due to Violations, THE Validator SHALL write the Violation details to standard error.

### Requirement 6: Non-Functional Constraints

**User Story:** As a power maintainer, I want the validator to follow the repository's stdlib-only conventions, so that it ships cleanly with the power and runs reliably in CI.

#### Acceptance Criteria

1. THE Validator SHALL be implemented in Python 3.11+ using the Python standard library only, with no third-party dependencies.
2. THE Validator SHALL be named `validate_governance_rules.py` using snake_case, and SHALL reside in `senzing-bootcamp/scripts/`.
3. THE Validator SHALL follow the repository script pattern: `#!/usr/bin/env python3` shebang, module docstring with usage examples, `from __future__ import annotations`, dataclasses for structured data, an argparse CLI, and a `if __name__ == "__main__": main()` entry point.
4. THE Validator SHALL exit with status code 0 on success and status code 1 on any error or Violation.
5. THE Validator SHALL NOT introduce any MCP server URL or hardcoded external endpoint outside `senzing-bootcamp/mcp.json`.
6. WHEN the Validator runs over the full seed Registry in CI, THE Validator SHALL complete within a duration acceptable for the existing CI validation pipeline.
7. THE Registry and Validator SHALL reside within the established `senzing-bootcamp/` structure, with no developer-only files placed outside that structure.

### Requirement 7: Seed Rule Set for v1

**User Story:** As a power maintainer, I want the v1 registry seeded with the concrete, mechanically-checkable governing rules proven this session, so that the conformance layer provides immediate value and prevents the specific drift already observed.

#### Acceptance Criteria

1. THE Registry SHALL include a Rule Entry for the **👉 pointer prefix rule**, asserting that the pointer indicator requirement is present in its enforcement point(s) (for example, `senzing-bootcamp/steering/agent-behavior-rules.md`).
2. THE Registry SHALL include a Rule Entry for the **MCP-First Invariant**, asserting that the MCP-first requirement is present in its enforcement point (for example, `senzing-bootcamp/steering/agent-instructions.md`).
3. THE Registry SHALL include a Rule Entry for **Rule 6 (insufficient license → consult Senzing MCP server)**, asserting that an MCP consultation reference (for example, `search_docs`) is present in each of the license-insufficient steering sections involved (the Module 1 and Module 2 license-insufficient paths in `module-01-business-problem.md` and `module-02-sdk-setup.md`).
4. THE Registry SHALL include a Rule Entry for **Rule 15 (Module 3 Step 9 visualization gate is unconditional)**, asserting that the Module 3 Step 9 gate has no skip escape hatch — for example, that `NON_SKIPPABLE_GATES` in `validate_mandatory_gates.py` contains `"3.9"` and that the contradicting "CONDITION B" escape hatch is ABSENT from `gate-module3-visualization.kiro.hook`.
5. THE Registry SHALL include a Rule Entry for the **hook-name "to (verb phrase)" rule**, asserting that hook `name` fields conform to the "to (verb phrase)" form.
6. THE Registry SHALL include a Rule Entry for the **feedback-file-path rule**, asserting that the required feedback file path is present in its enforcement point(s).
7. THE Registry SHALL include a Rule Entry for the **frontmatter inclusion rules**, asserting that the relevant steering files declare the expected YAML frontmatter `inclusion` value (for example, `inclusion: manual` or `inclusion: auto`) for the files governed by that rule.
8. THE Registry SHALL include a Rule Entry for the **graduation "always generate completion-summary" rule**, asserting that graduation enforcement unconditionally creates the completion-summary (for example, that the unconditional-generation contract is present in the graduation/completion-summary steering and that a decline escape hatch suppressing artifact creation is ABSENT).
9. WHERE a seed Rule Entry references an Enforcement Point or Assertion value, THE Registry SHALL use paths, markers, and strings that exist in the actual repository, and SHALL NOT invent unverified facts.

### Requirement 8: Out-of-Scope Behavioral Rules

**User Story:** As a power maintainer, I want behavioral-only rules to be explicitly recorded as not statically checkable, so that the registry's coverage boundary is clear and no one assumes a runtime rule is being verified statically.

#### Acceptance Criteria

1. THE_System SHALL classify governing rules whose conformance can only be verified by observing a live agent conversation as Behavioral-Only Rules that are out of scope for static checking in this feature.
2. WHERE a governing rule is a Behavioral-Only Rule (for example, "never ask an ambiguous yes/no question" evaluated at runtime), THE_System SHALL document it as documented-but-not-statically-checkable rather than attaching a static Assertion that cannot verify the runtime behavior.
3. THE_System SHALL make the distinction between Statically-Checkable Rules and Behavioral-Only Rules discoverable from the feature's documentation or the Registry, so that the coverage boundary is explicit.
4. THE Validator SHALL evaluate only Statically-Checkable Rule Entries and SHALL NOT fail a run on the basis of Behavioral-Only Rules that carry no static Assertion.

### Requirement 9: Relationship to Existing Validators

**User Story:** As a power maintainer, I want this feature to complement the existing validators without duplicating or replacing them, so that the validation suite stays coherent and the overlap with the behavior-rules validator is handled deliberately.

#### Acceptance Criteria

1. THE_System SHALL complement, and SHALL NOT replace, the existing validators `validate_power.py`, `validate_mandatory_gates.py`, `sync_hook_registry.py`, and `validate_behavior_rules.py`.
2. THE_System SHALL document how governance-rule-conformance differs from `validate_behavior_rules.py`, clarifying that the existing script validates the four `agent-behavior-rules.md` rules by scanning steering content, whereas this feature is a broader rule→enforcement registry with declarative Assertions.
3. WHERE the seed rule set overlaps with a rule already enforced by an existing validator (for example, the 👉 pointer prefix rule), THE_System SHALL note the overlap so the design phase can decide whether the Registry Assertion delegates to, references, or duplicates the existing check.
4. THE design phase SHALL decide whether governance-rule-conformance extends `validate_behavior_rules.py` or remains a separate script; THESE requirements SHALL NOT pre-decide that outcome and SHALL only require the overlap to be flagged.

### Requirement 10: CI Wiring

**User Story:** As a power maintainer, I want the validator wired into CI, so that broken rule-to-enforcement linkage fails the build automatically alongside the existing validation steps.

#### Acceptance Criteria

1. THE_System SHALL add a step to `.github/workflows/validate-power.yml` that runs `senzing-bootcamp/scripts/validate_governance_rules.py`.
2. THE new CI step SHALL run alongside the existing validation steps (`validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`, and `sync_hook_registry.py --verify`).
3. IF the Validator exits with status code 1 during CI, THEN THE CI job SHALL fail.
4. WHEN the Validator exits with status code 0 during CI, THE CI job SHALL treat the governance-rule-conformance step as passed.

### Requirement 11: Test Coverage

**User Story:** As a power maintainer, I want tests covering the validator and the registry schema, so that the conformance layer itself is verified and regressions are caught.

#### Acceptance Criteria

1. THE_System SHALL provide tests in `senzing-bootcamp/tests/` covering the Validator and the Registry schema, using pytest and Hypothesis with the Python standard library and Hypothesis only.
2. THE tests SHALL verify that the Validator exits with status code 0 when all Assertions hold and status code 1 when at least one Assertion fails.
3. THE tests SHALL verify each supported Assertion Type (substring present, substring absent, regex match present, regex match absent, file exists, hook JSON field equals value, YAML/JSON key present) for both passing and failing cases.
4. THE tests SHALL verify schema validation behavior, including missing required fields, duplicate `id` values, unsupported Assertion Types, and malformed Assertions.
5. THE tests SHALL verify that Violation messages include the Rule Id, the failing Assertion, and the relevant file path.
6. THE tests SHALL follow the repository test conventions: class-based organization, `from __future__ import annotations`, type hints (`X | None`, `list[str]`), `st_`-prefixed Hypothesis strategies, and `@settings(max_examples=20)` on property tests.
7. THE property tests SHALL document which requirements they validate.
8. WHERE the seed Registry is evaluated against the actual repository, THE tests SHALL verify that the shipped `governance-rules.yaml` passes the Validator (the conformance layer is itself conformant).
