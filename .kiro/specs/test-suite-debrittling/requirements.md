# Requirements Document

## Introduction

The senzing-bootcamp Kiro Power ships with a large pytest + Hypothesis test suite
(~4,868 tests across `senzing-bootcamp/tests/` and the repo-root `tests/`). A
recurring maintenance cost comes from **brittle assertions** — tests that pin
exact, incidental facts about the codebase rather than the behavior they intend to
guard. The CHANGELOG records this churn directly: an onboarding-split target was
"re-pointed to the current 147-test layout … so the count assertion tracks the live
147 tests", and "Preservation snapshot hashes refreshed in
`test_module2_license_question.py` and `test_module_closing_question_ownership.py`
for edits made in the Module 3 rename pass". Many paired `*_exploration.py` /
`*_preservation.py` regression tests lock down exact byte content via whole-file
SHA-256 digests (e.g. `_HASH_ONBOARDING_FLOW`, `_HASH_UNAFFECTED`), section-level
content snapshots (e.g. `_SNAP_*` in `test_always_create_completion_summary_preservation.py`),
exact heading-sequence lists, and exact total-test counts (e.g. `_PASSING_BASELINE == 4648`).

Each benign, unrelated edit forces a reflexive "refresh the hash / re-point the
count" change. This erodes the tests' value as regression guards: a test that must
be edited on every unrelated change stops signalling real regressions and starts
signalling "someone touched a file".

This feature reduces that brittleness while **preserving the genuine
regression-protection intent** of the preservation tests. It defines what makes an
assertion brittle versus structural/invariant for this codebase, provides a
detection tool (a stdlib-only scanner under `senzing-bootcamp/scripts/`, wired into
CI) so new brittle assertions do not creep in, and remediates existing brittle
assertions by replacing exact total-test counts, whole-file/section content-hash
snapshots, and overly specific string snapshots with structural/invariant
assertions that still catch real regressions. No existing real-bug regression
coverage is lost.

## Glossary

- **Test_Suite**: The combined pytest + Hypothesis tests under
  `senzing-bootcamp/tests/` (power tests) and the repo-root `tests/` (hook prompt
  tests).
- **Assertion**: A single pytest/Hypothesis check (an `assert` statement or
  equivalent) within a test.
- **Brittle_Assertion**: An Assertion that fails on benign, unrelated changes
  because it pins an incidental, non-behavioral fact. For this codebase the
  recognized brittle categories are: (a) **Exact_Count_Assertion** — equality
  against a hard-coded total-test count or whole-suite passing count; (b)
  **Whole_File_Snapshot_Assertion** — equality of a SHA-256 digest of an entire
  tracked file's bytes/text; (c) **Section_Snapshot_Assertion** — equality of a
  SHA-256 digest of a section/block of a tracked file; (d)
  **Exact_Sequence_Snapshot_Assertion** — equality against a hard-coded ordered
  list of every heading/line in a file.
- **Structural_Assertion**: An Assertion that verifies a behavioral invariant
  without coupling to incidental content. Recognized forms include membership
  checks (a required marker is present), threshold checks (a count is at least /
  at most a bound, or does not regress below a recorded floor), canonical-source
  checks (an expectation is derived from an imported single source of truth rather
  than a literal), and structural-shape checks (required headings exist in order,
  ignoring unrelated additions).
- **Brittleness_Scanner**: A new Python script,
  `senzing-bootcamp/scripts/scan_brittle_assertions.py`, that scans Test_Suite
  files and reports Brittle_Assertions.
- **Finding**: A single Brittle_Assertion reported by the Brittleness_Scanner,
  including file path, line number, and brittle category.
- **Allowlist_Marker**: An inline comment marker on a test line or block that
  records an explicit, reviewed decision to exempt an otherwise-flagged Assertion
  from being reported as a Finding.
- **Preservation_Test**: A test (typically in a `*_preservation.py` file) whose
  intent is to confirm that a prior bug fix did not regress and that unrelated
  content was not disturbed.
- **Exploration_Test**: A test (typically in a `*_exploration.py` or `*_bug.py`
  file) that reproduces a specific historical bug condition.
- **Regression_Coverage**: The set of historical bug conditions that the
  Test_Suite currently detects. Measured as the set of Exploration_Tests and the
  behavioral invariants asserted by Preservation_Tests.
- **CI_Pipeline**: The GitHub Actions workflow `.github/workflows/validate-power.yml`.
- **Legitimate_Hash_Use**: A use of hashing that is part of the behavior under
  test (e.g. `cord_metadata` content-hash round-trip properties), not a
  Whole_File_Snapshot_Assertion against a tracked source file.

## Requirements

### Requirement 1: Brittleness Classification Taxonomy

**User Story:** As a power maintainer, I want a documented, unambiguous definition
of what makes a test assertion brittle versus structural in this codebase, so that
I can consistently identify and avoid brittle assertions.

#### Acceptance Criteria

1. THE Test_Suite_Debrittling_Feature SHALL define the Brittle_Assertion taxonomy
   as exactly the following four categories: (a) Exact_Count_Assertion — equality
   (`==`) between a test expression and a hard-coded integer that represents a
   total test count or whole-suite passing count; (b) Whole_File_Snapshot_Assertion
   — equality between a computed SHA-256 digest of an entire tracked file's bytes
   or text and a hard-coded digest literal; (c) Section_Snapshot_Assertion —
   equality between a computed SHA-256 digest of a substring, section, or block
   extracted from a tracked file and a hard-coded digest literal; (d)
   Exact_Sequence_Snapshot_Assertion — equality between a list of every heading or
   every line extracted from a tracked file and a hard-coded ordered list literal.
2. THE Test_Suite_Debrittling_Feature SHALL define, for each Brittle_Assertion
   category, at least one Structural_Assertion replacement form that preserves the
   behavioral intent without coupling to incidental content.
3. WHERE a Legitimate_Hash_Use computes a hash of test-generated data as part of
   the behavior under test, THE Test_Suite_Debrittling_Feature SHALL classify the
   Assertion as a Structural_Assertion rather than a Whole_File_Snapshot_Assertion.

### Requirement 2: Brittleness Scanner Detection

**User Story:** As a power maintainer, I want a tool that detects brittle
assertions in the test suite, so that I can find existing brittle assertions and
prevent new ones from being introduced.

#### Acceptance Criteria

1. THE Brittleness_Scanner SHALL be implemented as a Python 3.11+ script at
   `senzing-bootcamp/scripts/scan_brittle_assertions.py` using only the Python
   standard library.
2. WHEN the Brittleness_Scanner is run, THE Brittleness_Scanner SHALL scan every
   `test_*.py` file under `senzing-bootcamp/tests/` and the repo-root `tests/`.
3. WHEN the Brittleness_Scanner encounters an Assertion matching the
   Exact_Count_Assertion category, THE Brittleness_Scanner SHALL emit a Finding
   identifying the file path, line number, and category.
4. WHEN the Brittleness_Scanner encounters an Assertion matching the
   Whole_File_Snapshot_Assertion category, THE Brittleness_Scanner SHALL emit a
   Finding identifying the file path, line number, and category.
5. WHEN the Brittleness_Scanner encounters an Assertion matching the
   Section_Snapshot_Assertion category, THE Brittleness_Scanner SHALL emit a
   Finding identifying the file path, line number, and category.
6. WHEN the Brittleness_Scanner encounters an Assertion matching the
   Exact_Sequence_Snapshot_Assertion category, THE Brittleness_Scanner SHALL emit
   a Finding identifying the file path, line number, and category.
7. WHERE an Assertion is annotated with an Allowlist_Marker, THE
   Brittleness_Scanner SHALL exclude that Assertion from reported Findings and
   SHALL count it separately as an allowlisted exemption.
8. IF a scanned file cannot be parsed as valid Python, THEN THE Brittleness_Scanner
   SHALL report the file path and the parse error and SHALL exit with a non-zero
   status code.
9. WHERE a Legitimate_Hash_Use is present, THE Brittleness_Scanner SHALL NOT emit
   a Finding for that Assertion.

### Requirement 3: Scanner CLI and CI Integration

**User Story:** As a power maintainer, I want the scanner to run in CI with a clear
pass/fail signal, so that new brittle assertions are blocked before merge.

#### Acceptance Criteria

1. THE Brittleness_Scanner SHALL provide an `argparse`-based command-line interface
   with a `main(argv=None)` entry point.
2. WHEN the Brittleness_Scanner is invoked with the `--check` flag and at least one
   non-allowlisted Finding is present, THE Brittleness_Scanner SHALL exit with a
   non-zero status code.
3. WHEN the Brittleness_Scanner is invoked with the `--check` flag and zero
   non-allowlisted Findings are present, THE Brittleness_Scanner SHALL exit with
   status code 0.
4. WHEN the Brittleness_Scanner completes a scan, THE Brittleness_Scanner SHALL
   print a summary reporting the number of files scanned, the number of Findings by
   category, and the number of allowlisted exemptions.
5. THE CI_Pipeline SHALL invoke the Brittleness_Scanner with the `--check` flag as
   a validation step before the pytest step.
6. WHEN the Brittleness_Scanner exits with a non-zero status code in the
   CI_Pipeline, THE CI_Pipeline SHALL fail the run.
7. IF the Brittleness_Scanner terminates before completing a scan of all target
   files, THEN THE Brittleness_Scanner SHALL exit with a non-zero status code.

### Requirement 4: Remediate Exact Total-Test-Count Assertions

**User Story:** As a power maintainer, I want exact total-test-count assertions
replaced with non-regression thresholds, so that adding or splitting tests does not
force count edits while a genuine drop in coverage is still caught.

#### Acceptance Criteria

1. WHEN an existing Exact_Count_Assertion pins a total-test count or whole-suite
   passing count, THE Test_Suite_Debrittling_Feature SHALL replace the equality
   check with a non-regression threshold check that fails only when the observed
   count falls below a recorded floor.
2. THE Test_Suite_Debrittling_Feature SHALL preserve the original intent of each
   replaced Exact_Count_Assertion as a comment or docstring referencing the
   behavior being guarded.
3. WHEN tests are added or an existing test file is split into more tests, THE
   remediated count assertion SHALL continue to pass without modification.
4. IF the observed total or passing count falls below the recorded floor, THEN THE
   remediated count assertion SHALL fail.
5. AFTER remediation, THE Brittleness_Scanner SHALL report zero non-allowlisted
   Exact_Count_Assertion Findings.

### Requirement 5: Remediate Whole-File and Section Content-Hash Snapshots

**User Story:** As a power maintainer, I want whole-file and section content-hash
snapshot assertions replaced with structural assertions, so that benign edits to
steering and documentation files do not force hash refreshes while real content
regressions are still caught.

#### Acceptance Criteria

1. WHEN an existing Whole_File_Snapshot_Assertion compares a tracked file's SHA-256
   digest against a literal, THE Test_Suite_Debrittling_Feature SHALL replace the
   digest-equality check with one or more Structural_Assertions that verify the
   required markers, cross-references, or invariants the snapshot was protecting.
2. WHEN an existing Section_Snapshot_Assertion compares a section's SHA-256 digest
   against a literal, THE Test_Suite_Debrittling_Feature SHALL replace the
   digest-equality check with Structural_Assertions that verify the required
   content of that section.
3. WHEN an existing Exact_Sequence_Snapshot_Assertion compares a full heading or
   line list against a literal, THE Test_Suite_Debrittling_Feature SHALL replace
   the full-list-equality check with a Structural_Assertion that verifies the
   required headings are present in the required relative order, tolerating
   unrelated additions.
4. WHEN a benign, unrelated edit is made to a file previously covered by a
   remediated snapshot assertion, THE remediated assertion SHALL continue to pass
   without modification.
5. IF a required marker, cross-reference, or invariant protected by a remediated
   assertion is removed or reordered, THEN THE remediated assertion SHALL fail.
6. AFTER remediation, THE Brittleness_Scanner SHALL report zero non-allowlisted
   Whole_File_Snapshot_Assertion, Section_Snapshot_Assertion, and
   Exact_Sequence_Snapshot_Assertion Findings.

### Requirement 6: Preserve Regression Coverage

**User Story:** As a power maintainer, I want every existing real-bug regression to
remain covered after debrittling, so that reducing brittleness does not weaken the
suite's protection against known bugs.

#### Acceptance Criteria

1. THE Test_Suite_Debrittling_Feature SHALL retain every Exploration_Test that
   reproduces a historical bug condition.
2. WHEN a Preservation_Test's snapshot assertion is remediated, THE remediated test
   SHALL continue to assert the behavioral invariant that the original
   Preservation_Test protected.
3. WHEN the full Test_Suite is run after remediation, THE Test_Suite SHALL pass.
4. IF a remediation would cause any previously-passing test to fail, THEN THE
   Test_Suite_Debrittling_Feature SHALL block that remediation until the failure is
   resolved.
5. THE Test_Suite_Debrittling_Feature SHALL NOT reduce the set of historical bug
   conditions detected by the Test_Suite.
6. IF a remediation would remove coverage of a historical bug condition, THEN THE
   Test_Suite_Debrittling_Feature SHALL retain an equivalent Structural_Assertion
   that detects the same bug condition.

### Requirement 7: Scanner Self-Validation

**User Story:** As a power maintainer, I want the scanner's own classification logic
to be tested, so that the scanner reliably distinguishes brittle from structural
assertions.

#### Acceptance Criteria

1. THE Test_Suite_Debrittling_Feature SHALL provide pytest tests for the
   Brittleness_Scanner that follow the project's test conventions (class-based
   organization, `sys.path` import of the script, Hypothesis where applicable).
2. WHEN the Brittleness_Scanner classification logic is given a known
   Brittle_Assertion example for each category, THE classification logic SHALL
   classify it into the matching category.
3. WHEN the Brittleness_Scanner classification logic is given a known
   Structural_Assertion example, THE classification logic SHALL NOT classify it as
   a Brittle_Assertion.
4. WHEN the Brittleness_Scanner classification logic is given an Assertion
   annotated with an Allowlist_Marker, THE classification logic SHALL treat it as
   an allowlisted exemption rather than a Finding.
