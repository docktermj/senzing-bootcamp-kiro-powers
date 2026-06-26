# Requirements Document

## Introduction

The `senzing-bootcamp` Kiro power tracks a steering-file context budget in
`senzing-bootcamp/steering/steering-index.yaml`. The `budget` block declares a
`split_threshold_tokens` value (currently `5000`): the per-file token count
above which a steering file should be divided into phases via
`split_steering.py`. The linter `senzing-bootcamp/scripts/lint_steering.py`
already enforces the companion `router_ceiling` budget (via
`get_router_ceiling` and `check_router_convention`) so Router_Root files stay
thin, but it does **not** enforce `split_threshold_tokens`. As a result several
phase files have grown well past the declared threshold with no CI signal — for
example `hook-registry-critical.md` (~8,592 tokens, 72% over), `graduation.md`
(~5,394 tokens), `module-05-phase2-data-mapping.md` (~5,355 tokens), and
`module-01-phase1-discovery.md` (~5,027 tokens). Because the whole steering
corpus is ~186,004 tokens against a 200,000-token reference window, unchecked
growth erodes the routing budget.

This feature adds a new lint check that reads the configured
`split_threshold_tokens` from the steering index, classifies each measured
steering file against it, and emits a `LintViolation` (consistent with the
existing ERROR/WARNING pattern) so over-threshold files are flagged during the
CI "Lint steering files" gate (`.github/workflows/validate-power.yml`). To avoid
forcing splits on files that are intentionally large, the feature also provides
an exemption/allowlist mechanism. Token counts are sourced from
`steering-index.yaml` `file_metadata` (produced by `measure_steering.py`); the
threshold is never hardcoded.

## Open Design Decisions

The following decision is intentionally deferred to the design phase. The
acceptance criteria below are written so the design can resolve it without
re-opening requirements:

1. **Violation severity (ERROR vs WARNING).** Whether an over-threshold file is
   a hard `ERROR` (fails the PR immediately, matching `check_router_convention`)
   or a soft `WARNING` (advisory, only failing under `--warnings-as-errors`).
   Requirement 3 specifies a configurable, default-soft behavior so either gate
   strength can be selected without changing the rest of the specification.

## Glossary

- **Linter**: The `senzing-bootcamp/scripts/lint_steering.py` script that runs
  structural and budget lint rules over steering files and exits non-zero when a
  failing violation is present.
- **Steering_Index**: The `senzing-bootcamp/steering/steering-index.yaml` file
  containing the `budget` block and the `file_metadata` mapping.
- **Split_Threshold**: The integer token count read from
  `budget.split_threshold_tokens` in the Steering_Index, above which a steering
  file is a split candidate.
- **File_Metadata**: The `file_metadata` mapping in the Steering_Index, keyed by
  steering filename, where each entry records a `token_count` (and
  `size_category`) produced by `measure_steering.py`.
- **Token_Count**: The integer `token_count` recorded for a steering file in
  File_Metadata.
- **Split_Check**: The new lint rule, added to the Linter, that classifies
  steering files against the Split_Threshold and produces violations.
- **LintViolation**: The existing dataclass in the Linter carrying a `level`
  (`"ERROR"` or `"WARNING"`), `file`, `line`, and `message`.
- **Allowlist**: The configured set of steering filenames that are exempt from
  the Split_Check because they are intentionally permitted to exceed the
  Split_Threshold.
- **CI_Gate**: The "Lint steering files" step in
  `.github/workflows/validate-power.yml` that runs the Linter.
- **Default_Threshold**: The fallback Split_Threshold value (5000 tokens) the
  Linter uses when `budget.split_threshold_tokens` is absent or invalid.

## Requirements

### Requirement 1: Read the configured Split_Threshold from the Steering_Index

**User Story:** As a power maintainer, I want the Split_Check to read the
threshold from the Steering_Index budget block, so that enforcement always
matches the single declared budget value and is never hardcoded in the Linter.

#### Acceptance Criteria

1. WHEN the Split_Check runs, THE Linter SHALL read the Split_Threshold from the
   `budget.split_threshold_tokens` value in the Steering_Index using a localized
   regular-expression lookup, mirroring the approach used by `get_router_ceiling`.
2. WHERE the Steering_Index contains a `budget.split_threshold_tokens` value that
   is a positive integer (1 or greater), THE Linter SHALL use that integer as the
   Split_Threshold.
3. IF the Steering_Index file does not exist, THEN THE Linter SHALL use the
   Default_Threshold of 5000 tokens as the Split_Threshold.
4. IF `budget.split_threshold_tokens` is absent from the Steering_Index, THEN
   THE Linter SHALL use the Default_Threshold of 5000 tokens as the Split_Threshold.
5. IF `budget.split_threshold_tokens` is present but its value is not a positive
   integer (non-numeric, zero, or negative), THEN THE Linter SHALL use the
   Default_Threshold of 5000 tokens as the Split_Threshold.
6. WHERE `budget.split_threshold_tokens` appears more than once in the
   Steering_Index, THE Linter SHALL use the first matched positive-integer value
   as the Split_Threshold.
7. THE Linter SHALL NOT contain a hardcoded Split_Threshold value other than the
   Default_Threshold fallback of 5000 tokens.

### Requirement 2: Classify steering files against the Split_Threshold

**User Story:** As a power maintainer, I want every measured steering file
compared to the Split_Threshold, so that files exceeding the budget are
identified using the same Token_Count data that the index already tracks.

#### Acceptance Criteria

1. WHEN the Split_Check runs, THE Linter SHALL evaluate every File_Metadata entry
   present in the Steering_Index against the Split_Threshold using that entry's
   recorded Token_Count, evaluating each entry exactly once.
2. IF a File_Metadata entry's Token_Count is an integer strictly greater than the
   Split_Threshold, THEN THE Split_Check SHALL produce exactly one LintViolation
   that names the steering filename, the entry's integer Token_Count, and the
   Split_Threshold.
3. WHILE a File_Metadata entry's Token_Count is an integer less than or equal to
   the Split_Threshold, including the boundary case where Token_Count equals the
   Split_Threshold, THE Split_Check SHALL produce no LintViolation for that entry.
4. IF a File_Metadata entry's Token_Count is absent or is not an integer value,
   THEN THE Split_Check SHALL produce exactly one LintViolation that names the
   steering filename and indicates that the file cannot be classified against the
   Split_Threshold, retaining the entry's existing index data, and mirroring the
   missing-count handling in `check_router_convention`.
5. WHEN every File_Metadata entry in the Steering_Index has an integer
   Token_Count less than or equal to the Split_Threshold, THE Split_Check SHALL
   produce zero LintViolations.
6. WHEN the Steering_Index contains zero File_Metadata entries, THE Split_Check
   SHALL produce zero LintViolations.

### Requirement 3: Configurable violation severity (ERROR vs WARNING)

**User Story:** As a power maintainer, I want to control whether an
over-threshold file fails the build or is advisory, so that I can adopt soft
warnings first and promote to a hard gate without changing the rule.

#### Acceptance Criteria

1. WHERE no severity override is configured, THE Split_Check SHALL emit each
   over-threshold LintViolation with its `level` field set to `WARNING`.
2. WHEN the Linter is run with the `--warnings-as-errors` flag, THE Linter SHALL
   count each `WARNING`-level Split_Check violation as a failing violation for
   exit-code determination, consistent with the existing `run_all_checks`
   exit-code logic.
3. WHERE a severity override designates Split_Check violations as `ERROR`, THE
   Split_Check SHALL emit each over-threshold LintViolation with its `level`
   field set to `ERROR`.
4. WHEN at least one Split_Check violation with `level` `ERROR` exists, THE Linter
   SHALL return a non-zero exit code.
5. WHEN no `ERROR`-level Split_Check violation exists and the `--warnings-as-errors`
   flag is absent, THE Split_Check SHALL not by itself cause a non-zero exit code.
6. THE Split_Check SHALL emit every LintViolation through the existing
   LintViolation dataclass, populating its `level`, `file`, `line`, and `message`
   fields so that violation formatting and reporting remain consistent with all
   other lint rules.
7. IF a severity override value is provided that is neither `WARNING` nor `ERROR`,
   THEN THE Linter SHALL reject it with an error indication rather than silently
   defaulting.

### Requirement 4: Exemption/Allowlist for intentionally large files

**User Story:** As a power maintainer, I want to exempt specific steering files
that are intentionally large, so that legitimate files are not forced to split
while every other file remains enforced.

#### Acceptance Criteria

1. THE Split_Check SHALL read an Allowlist of steering filenames from the
   Steering_Index, where each entry consists of an exact, case-sensitive filename
   and a non-empty justification string of 1 to 280 characters.
2. WHERE a steering filename exactly matches an Allowlist entry, THE Split_Check
   SHALL produce no over-threshold LintViolation for that file even when its
   Token_Count is strictly greater than the Split_Threshold.
3. WHERE a steering filename does not exactly match any Allowlist entry, THE
   Split_Check SHALL evaluate that file against the Split_Threshold per
   Requirement 2.
4. WHEN the Allowlist is empty, absent, or unconfigured, THE Split_Check SHALL
   evaluate every measured steering file in File_Metadata against the
   Split_Threshold per Requirement 2.
5. IF the Allowlist references a filename that is not present in File_Metadata,
   THEN THE Split_Check SHALL produce a LintViolation identifying the stale
   Allowlist entry by filename and indicating that the exemption is obsolete, and
   SHALL retain the remaining Allowlist entries for evaluation.
6. IF an Allowlist entry is missing its justification string or the justification
   string is empty or exceeds 280 characters, THEN THE Split_Check SHALL produce a
   LintViolation identifying the entry by filename and indicating the
   justification is invalid, and SHALL NOT exempt that file from Split_Threshold
   enforcement.

### Requirement 5: CI integration in the "Lint steering files" gate

**User Story:** As a power maintainer, I want the Split_Check to run inside the
existing CI lint step, so that over-threshold growth is caught on every pull
request without adding a new workflow step.

#### Acceptance Criteria

1. WHEN the Linter is executed, THE Linter SHALL run the Split_Check within the
   same invocation as the existing lint rules in `run_all_checks` and include its
   result in the aggregated results.
2. WHEN the CI_Gate runs `python senzing-bootcamp/scripts/lint_steering.py` on the
   Python 3.11, 3.12, and 3.13 matrix, THE Split_Check SHALL execute without any
   added, modified, or newly required step in `.github/workflows/validate-power.yml`.
3. IF a failing-level Split_Check violation is present during the CI_Gate, THEN
   THE Linter SHALL terminate with a non-zero exit code so that the pull request
   fails.
4. WHEN no failing-level Split_Check violation is present during the CI_Gate, THE
   Split_Check SHALL not by itself cause the Linter to terminate with a non-zero
   exit code.
5. WHEN the Split_Check produces violations, THE Linter SHALL print each
   LintViolation using the existing violation output format, identifying the file
   path, Token_Count, and Split_Threshold.
6. WHILE the corpus contains files whose Token_Count is strictly greater than the
   Split_Threshold and that are not on the Allowlist — including
   `hook-registry-critical.md`, `graduation.md`, `module-05-phase2-data-mapping.md`,
   and `module-01-phase1-discovery.md` — THE Split_Check SHALL report each such
   file so the CI_Gate surfaces the known over-threshold files.

### Requirement 6: Test coverage

**User Story:** As a power maintainer, I want automated tests for the Split_Check,
so that the enforcement behavior is verified and protected against regression
following the project's test conventions.

#### Acceptance Criteria

1. THE test suite SHALL include tests for the Split_Check located in
   `senzing-bootcamp/tests/` in a file named `test_<feature>.py` and organized as
   one or more test classes, each containing test methods named with a `test_`
   prefix.
2. WHEN the Split_Check evaluates a file whose Token_Count is strictly greater
   than the Split_Threshold, THE test suite SHALL assert that exactly one
   LintViolation is produced and that its content contains the file path, the
   integer Token_Count, and the integer Split_Threshold.
3. WHEN the Split_Check evaluates a file whose Token_Count is less than or equal
   to the Split_Threshold, THE test suite SHALL assert that zero LintViolations
   are produced.
4. WHEN the Split_Check evaluates an Allowlisted file whose Token_Count is
   strictly greater than the Split_Threshold, THE test suite SHALL assert that
   zero over-threshold LintViolations are produced.
5. WHEN the Steering_Index contains a `budget.split_threshold_tokens` value, THE
   test suite SHALL assert that the Split_Check uses that value as the
   Split_Threshold.
6. WHEN the Steering_Index does not contain a `budget.split_threshold_tokens`
   value, THE test suite SHALL assert that the Split_Check uses the
   Default_Threshold of 5000 as the Split_Threshold.
7. WHERE property-based testing applies, THE test suite SHALL use Hypothesis
   `@given` strategies, decorated with `@settings(max_examples=20)` and using
   `st_`-prefixed strategy names, to assert that for every generated pair of
   integer Token_Count (ranging from 0 to 1,000,000) and integer Split_Threshold
   (ranging from 1 to 1,000,000) a LintViolation is produced if and only if
   Token_Count is strictly greater than Split_Threshold.
8. THE test suite SHALL import `lint_steering.py` using the same `sys.path`
   manipulation pattern used by the other test files in `senzing-bootcamp/tests/`.
