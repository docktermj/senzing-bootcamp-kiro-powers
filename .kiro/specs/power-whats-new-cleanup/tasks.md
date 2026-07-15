# Implementation Plan: Power What's New Cleanup

## Overview

This is a documentation-only cleanup of `senzing-bootcamp/POWER.md`. The plan is a single
targeted text edit (append the CHANGELOG pointer to the retained `0.2.0` section and remove
the four Older_Whats_New_Sections), an optional read-only regression-guard test, and a
verification pass that runs the CI gate sequence and inspects the git diff for byte-for-byte
preservation of every frozen region. No script, hook, steering, or generator logic changes.

## Tasks

- [x] 1. Prune the What's New run in POWER.md
  - [x] 1.1 Edit `senzing-bootcamp/POWER.md` What's New sections
    - Append a blank line and the exact sentence `See the CHANGELOG for the full release history.` as its own paragraph at the end of the retained `## What's New in 0.2.0` section (the last line before `## What's New in 0.1.3`)
    - Remove every line from the `## What's New in 0.1.3` heading through the last line before `## What This Bootcamp Does` — deleting the `0.1.3`, `1.0.0` (including the withdrawn-tag blockquote), `0.12.1`, and `0.12.0` sections in full
    - Leave a single blank line between the retained `0.2.0` section and `## What This Bootcamp Does` so headings keep blank-line-around spacing (valid CommonMark)
    - Do not touch the YAML frontmatter (incl. `version: 0.2.0`), any Generated_Region marker/body, or any section outside the What's New run
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 4.3, 5.1, 6.3, 6.4_

- [x] 2. Add the optional regression-guard test
  - [x] 2.1 Create `senzing-bootcamp/tests/test_whats_new_sections.py` with helpers and example-based guard assertions
    - Class-based pytest module following repo conventions; read-only, reads `POWER.md` and `CHANGELOG.md` from disk; stdlib-only helpers (no production API)
    - Implement pure helpers: `whats_new_versions(text)` returning the ordered versions matching `^## What's New in (\d+\.\d+\.\d+)$`, `frontmatter_version(text)` reading the leading YAML `version` field (mirror/reuse existing `version.read_version_from_frontmatter` behavior), and `retained_section_body(text)` returning the sole retained section body
    - Assert `whats_new_versions(power_md)` equals exactly `[frontmatter_version(power_md)]` (exactly one section and it is `0.2.0`)
    - Assert no version other than the frontmatter version has a What's New section
    - Assert the retained section's final non-empty line equals `See the CHANGELOG for the full release history.`
    - Assert the retained section contains no Point_In_Time_Metric_Claim (digits paired with `passed`/`failed`/`violations`)
    - Fail loudly (naming the missing element) if no frontmatter `version` or no What's New heading is found
    - _Requirements: 7.1, 7.2, 7.3, 1.1, 1.2, 2.1, 3.1_

  - [x] 2.2 Write Property 1 test (What's New version detection round-trips)
    - `# Feature: power-whats-new-cleanup, Property 1: What's New version detection round-trips`
    - Hypothesis: generate sets of distinct semver strings, synthesize a document with a `## What's New in v` heading plus arbitrary body per version, assert `whats_new_versions` returns exactly that set (no version missed, none spurious); do not hand-set `@settings(max_examples=...)`
    - **Validates: Requirements 1.1, 1.3, 7.2**

  - [x] 2.3 Write Property 2 test (only the current version has a What's New section)
    - `# Feature: power-whats-new-cleanup, Property 2: Only the current version has a What's New section`
    - Hypothesis: generate semver strings `!= frontmatter_version(power_md)` and assert the real POWER.md contains no `## What's New in v` heading for them
    - **Validates: Requirements 1.2, 1.3, 7.2**

  - [x] 2.4 Write Property 3 test (no release information is lost)
    - `# Feature: power-whats-new-cleanup, Property 3: No release information is lost`
    - Iterate the removed-version set `["0.1.3", "1.0.0", "0.12.1", "0.12.0"]` and assert each has a matching `## [version]` release entry in `senzing-bootcamp/CHANGELOG.md`
    - **Validates: Requirements 2.3**

- [x] 3. Verify documentation-only, valid, and CI-green
  - [x] 3.1 Run the CI validation suite gate sequence
    - Run in order, exactly as `.github/workflows/validate-power.yml`: `python senzing-bootcamp/scripts/validate_power.py`, `python senzing-bootcamp/scripts/measure_steering.py --check`, `python senzing-bootcamp/scripts/validate_commonmark.py`, `python senzing-bootcamp/scripts/sync_hook_registry.py --verify`, then `python -m pytest senzing-bootcamp/tests/ tests/`
    - All steps must complete with zero failures (Generated_Regions intact, steering budgets and hook registry unchanged, POWER.md valid CommonMark, full suite incl. new guard green)
    - _Requirements: 6.1, 6.2, 7_

  - [x] 3.2 Review the git diff for byte-for-byte preservation
    - Confirm the only content-bearing changes are the removal of the `0.1.3`/`1.0.0`/`0.12.1`/`0.12.0` sections and the appended pointer line in the `0.2.0` section — all inside the What's New run
    - Confirm no frontmatter line changed and `version` is still `0.2.0`; no Generated_Region marker or body was touched
    - Confirm `senzing-bootcamp/steering/whats-new.md` is absent from the changeset and the changeset touches only `senzing-bootcamp/POWER.md` and, optionally, `senzing-bootcamp/tests/test_whats_new_sections.py`
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 6.4_

## Notes

- Tasks marked with `*` are optional (the regression guard, Requirement 7) and can be skipped for a faster MVP; core tasks 1.1, 3.1, and 3.2 are never skipped.
- Each task references specific requirement clauses for traceability.
- Property tests are tagged with their design property number and validate the listed requirements clauses.
- Task 1.1 must land before the guard test reads the file and before verification; the property/example tests in 2.x each edit the same test module and are therefore sequenced across separate waves.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3"] },
    { "id": 4, "tasks": ["2.4"] },
    { "id": 5, "tasks": ["3.1", "3.2"] }
  ]
}
```
