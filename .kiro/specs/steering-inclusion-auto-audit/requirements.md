# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power ships 100+ steering files in `senzing-bootcamp/steering/`.
Each file declares an `inclusion:` mode in its YAML frontmatter. Standard, documented Kiro
steering supports three inclusion modes: `always` (loaded into every session), `fileMatch`
(loaded when an edited file matches a glob), and `manual` (loaded only on explicit reference).
Eleven files in this project instead declare a fourth, non-standard value: `inclusion: auto`.

The eleven `auto` files (agent-behavior-rules.md, agent-context-management.md,
conversation-protocol.md, design-patterns.md, file-placement.md, mcp-response-caching.md,
module-prerequisites.md, project-structure.md, qa-transcript.md, session-resume.md,
verbosity-control.md) total approximately 18,000 measured tokens. Only three files declare
`inclusion: always` (agent-instructions.md, module-transitions.md, security-privacy.md),
giving an intended always-loaded baseline of approximately 6,668 tokens.

The project's own tooling treats `auto` as a first-class valid value. `validate_power.py`
and `lint_steering.py` both accept `auto` in their `VALID_INCLUSIONS` set, while
`measure_steering.py` computes the always-loaded Baseline_Footprint by summing only files
that declare `inclusion: always`. The budget accounting in `steering-index.yaml` therefore
assumes the eleven `auto` files are NOT always-loaded.

This creates an unverified risk. If the Kiro runtime does not recognize `auto` and falls
back to the default (`always`), the eleven files become always-on context and the real
baseline rises from approximately 6,668 tokens to approximately 25,000 tokens, silently
invalidating the budget accounting. If the runtime instead treats an unknown value as
`manual` or ignores it, steering the project expects to be reliably present (for example,
conversation-protocol.md) may fail to load when needed, degrading the guided workflow. The
actual runtime interpretation of `auto` could not be determined during analysis and must be
established. This spec covers verifying that behavior, deciding the correct standard modes,
re-classifying the affected files, and realigning the project's validators and budget
accounting with the verified truth.

## Glossary

- **Steering_File**: A Markdown file in `senzing-bootcamp/steering/` with YAML frontmatter
  containing an `inclusion` value and optional `description` and `fileMatchPattern` fields.
- **Inclusion_Mode**: The frontmatter value that governs when a Steering_File is loaded into
  an agent session. Standard Kiro values are `always`, `fileMatch`, and `manual`.
- **Auto_File**: A Steering_File that currently declares `inclusion: auto`. There are eleven
  Auto_Files.
- **Runtime_Behavior**: The manner in which the Kiro runtime loads a Steering_File given its
  declared Inclusion_Mode, expressed as one of: `loads-always`, `loads-on-file-match`,
  `loads-manual-only`, or `ignored`.
- **Audit_Finding**: The documented, evidence-backed record of the verified Runtime_Behavior
  of the `auto` value, including its source of evidence.
- **Decision_Record**: The documented mapping of each Auto_File to a target standard
  Inclusion_Mode, with rationale.
- **Inclusion_Validator**: The project's frontmatter validation logic in `validate_power.py`
  and `lint_steering.py`, including their `VALID_INCLUSIONS` sets.
- **Budget_Analyzer**: The always-loaded budget accounting logic in `measure_steering.py`.
- **Baseline_Footprint**: The summed measured `token_count` of all Steering_Files that the
  Kiro runtime loads into every session.
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file, including its
  `budget` block and per-file `token_count`/`size_category` metadata and keyword routing map.
- **CI_Pipeline**: The GitHub Actions workflow `.github/workflows/validate-power.yml`.
- **Guided_Bootcamp_Workflow**: The runtime behavior of the 11-module bootcamp that depends
  on specific Steering_Files being present at specific moments.

## Requirements

### Requirement 1: Verify the runtime interpretation of `inclusion: auto`

**User Story:** As a power maintainer, I want the actual Kiro runtime interpretation of
`inclusion: auto` established with evidence, so that all downstream decisions rest on verified
behavior rather than assumption.

#### Acceptance Criteria

1. THE Audit_Finding SHALL record the verified Runtime_Behavior of the `auto` Inclusion_Mode as exactly one value from the set {`loads-always`, `loads-on-file-match`, `loads-manual-only`, `ignored`}, together with the evidence source used to establish that value, expressed as exactly one of: a documentation citation or a runtime test.
2. IF authoritative Kiro steering documentation defines the handling of the `auto` value, THEN THE Audit_Finding SHALL record the documented behavior together with a concrete citation consisting of the documentation title and the section or locator within that documentation.
3. IF authoritative Kiro steering documentation does not define the handling of the `auto` value, THEN THE Audit_Finding SHALL record the Runtime_Behavior observed from a runtime test that observes whether the `auto`-declared Steering_File's content is present across three defined session conditions — (a) a session with no matching-file edit and no explicit reference, (b) a session in which a file the Steering_File could plausibly match is edited, and (c) a session with an explicit reference to the file — such that the observed result maps to exactly one Runtime_Behavior value.
4. THE Audit_Finding SHALL record a specific calendar date of verification and a Kiro version identifier against which the behavior was verified, or, WHERE no Kiro version identifier is available, an environment description in place of the version identifier.
5. WHERE the verified Runtime_Behavior is `loads-always`, THE Audit_Finding SHALL state the resulting Baseline_Footprint as a numeric token total computed as the summed measured `token_count` of the always-loaded Steering_Files per the Baseline_Footprint glossary definition when the eleven Auto_Files are counted as always-loaded.

### Requirement 2: Decide the target standard inclusion mode for each `auto` file

**User Story:** As a power maintainer, I want each `auto` file mapped to a documented standard inclusion mode, so that steering loads exactly when the bootcamp workflow intends.

#### Acceptance Criteria

1. WHEN the Audit_Finding is recorded, THE Decision_Record SHALL assign each of the eleven Auto_Files exactly one target Inclusion_Mode from the set {`always`, `fileMatch`, `manual`}.
2. THE Decision_Record SHALL state, for each of the eleven Auto_Files, an intended loading condition expressed as exactly one of: present in every session; present only when an edited file matches a stated glob pattern; or present only on explicit reference.
3. THE Decision_Record SHALL record, for each of the eleven Auto_Files, a written rationale that references the file's stated intended loading condition and explains why the assigned target Inclusion_Mode produces that condition.
4. WHERE an Auto_File's intended loading condition is presence only when an edited file matches a glob pattern, THE Decision_Record SHALL assign the `fileMatch` mode and specify a single non-empty glob pattern that identifies the files whose editing triggers loading.
5. WHERE an Auto_File's intended loading condition is presence in every session, THE Decision_Record SHALL assign the `always` mode and include the file's measured `token_count` in the projected Baseline_Footprint total stated in tokens.
6. WHERE an Auto_File's intended loading condition is presence only on explicit reference, THE Decision_Record SHALL assign the `manual` mode.

### Requirement 3: Re-classify the affected steering files to standard modes

**User Story:** As a power maintainer, I want the eleven `auto` files rewritten to their
decided standard modes, so that the shipped steering matches documented Kiro behavior without
losing intended conditional loading.

#### Acceptance Criteria

1. WHEN each of the eleven Auto_Files is re-classified, THE Steering_File SHALL declare in its frontmatter the target Inclusion_Mode assigned by the Decision_Record, constrained to exactly one value from the set {`always`, `fileMatch`, `manual`}.
2. WHEN an Auto_File is re-classified, THE Steering_File SHALL preserve its `description` frontmatter value unchanged from its pre-reclassification value, and WHERE the Auto_File has no existing `description` value, THE Steering_File SHALL neither add nor remove a `description` value.
3. WHERE an Auto_File is re-classified to `fileMatch`, THE Steering_File SHALL include a `fileMatchPattern` frontmatter value exactly equal to the glob pattern specified in the Decision_Record.
4. WHEN an Auto_File that participates in keyword routing in the Steering_Index is re-classified, THE Steering_Index SHALL retain that file's keyword routing entry unchanged.
5. WHEN an Auto_File is re-classified, THE Steering_File's Markdown body content SHALL be preserved unchanged from its pre-reclassification content.
6. WHEN re-classification of all eleven Auto_Files is complete, THE steering directory SHALL contain zero Steering_Files declaring `inclusion: auto`.

### Requirement 4: Align the project validators with standard inclusion modes

**User Story:** As a power maintainer, I want the project's own validators to accept only documented inclusion modes, so that CI enforces the verified standard and prevents reintroduction of `auto`.

#### Acceptance Criteria

1. THE Inclusion_Validator SHALL treat exactly the three values `always`, `fileMatch`, and `manual`, compared as case-sensitive exact strings, as its accepted set of Inclusion_Mode values, and SHALL treat every other value as not accepted.
2. IF a Steering_File declares an Inclusion_Mode outside {`always`, `fileMatch`, `manual`}, or omits the inclusion value, or leaves the inclusion value empty, THEN THE Inclusion_Validator SHALL report a validation failure that names the offending Steering_File and the offending value.
3. THE Inclusion_Validator SHALL enforce the identical accepted set {`always`, `fileMatch`, `manual`} in both `validate_power.py` and `lint_steering.py`.
4. IF the Inclusion_Validator reports one or more Inclusion_Mode validation failures, THEN THE Inclusion_Validator SHALL produce an unsuccessful overall result so that the CI_Pipeline check does not pass.
5. THE Inclusion_Validator SHALL continue to use only the Python standard library.

### Requirement 5: Realign budget accounting with the true always-loaded footprint

**User Story:** As a power maintainer, I want the budget accounting to reflect the files the runtime actually always-loads, so that the token budget reported in CI is trustworthy.

#### Acceptance Criteria

1. THE Budget_Analyzer SHALL compute the Baseline_Footprint by summing, over every Steering_File whose declared Inclusion_Mode is established by the Audit_Finding to cause the Kiro runtime to load that file into every session, the `token_count` derived from that file's current on-disk content rather than any value stored in the Steering_Index.
2. WHEN the Budget_Analyzer computes the Baseline_Footprint, THE Budget_Analyzer SHALL compare the Baseline_Footprint, in tokens, against the always-loaded ceiling, where the ceiling in tokens equals `budget.always_loaded_ceiling_pct` percent of the warn threshold, and the warn threshold in tokens equals `budget.warn_threshold_pct` percent of `budget.reference_window`, all read from the Steering_Index.
3. IF the Baseline_Footprint is strictly greater than the always-loaded ceiling in tokens, THEN THE Budget_Analyzer SHALL report an over-budget failure, as a non-passing check result, that states both the Baseline_Footprint and the ceiling in tokens.
4. WHEN a Steering_File is re-classified, THE Steering_Index per-file `token_count` for that file SHALL be within 10 percent of the file's measured token count, and its `size_category` SHALL match the size category into which that measured token count falls.
5. THE Budget_Analyzer SHALL continue to use only the Python standard library.

### Requirement 6: Preserve CI success and workflow behavior after the change

**User Story:** As a power maintainer, I want the audit changes to leave CI green and the guided bootcamp intact, so that shipping the change introduces no regression for users.

#### Acceptance Criteria

1. WHEN the audit changes are complete, THE CI_Pipeline SHALL conclude its run with every configured check reporting a success result and zero configured checks reporting a failure result.
2. WHEN a re-classified Steering_File's intended loading condition recorded in the Decision_Record is met during a session, THE Guided_Bootcamp_Workflow SHALL have that Steering_File's content present in the session.
3. WHERE a Steering_File was loaded into every active session before the change, as determined from the file's pre-change Inclusion_Mode together with the Audit_Finding, THE re-classified Steering_File SHALL be loaded into every active session after the change.
4. THE audit changes SHALL modify only files within the repository and SHALL modify no resource outside the repository.
5. WHEN the audit changes are complete, every Steering_File that ships to users under `senzing-bootcamp/` SHALL declare an Inclusion_Mode from the set {`always`, `fileMatch`, `manual`}.
