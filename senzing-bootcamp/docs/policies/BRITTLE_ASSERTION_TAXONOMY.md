# Brittle Assertion Taxonomy

## Overview

The Senzing Bootcamp ships a large pytest + Hypothesis test suite across
`senzing-bootcamp/tests/` (power tests) and the repo-root `tests/` (hook prompt
tests). A recurring maintenance cost comes from **brittle assertions** — tests
that pin exact, incidental facts about the codebase rather than the behavior they
intend to guard. Every benign, unrelated edit then forces a reflexive "refresh the
hash" or "re-point the count" change, which erodes the test's value as a regression
guard: a test that must be edited on every unrelated change stops signalling real
regressions and starts signalling "someone touched a file".

This document defines, for this codebase, exactly what makes an assertion **brittle**
versus **structural**, so maintainers can consistently identify and avoid brittle
assertions. It pairs each brittle category with at least one structural replacement
that preserves the original behavioral intent without coupling to incidental
content. It is the human-readable companion to the brittleness scanner
(`scripts/scan_brittle_assertions.py`), which detects these categories statically and
runs in CI.

**Applies To**: The combined pytest + Hypothesis test suite under
`senzing-bootcamp/tests/` and the repo-root `tests/`.

## Definitions

- **Brittle assertion**: An assertion that fails on benign, unrelated changes
  because it pins an incidental, non-behavioral fact.
- **Structural assertion**: An assertion that verifies a behavioral invariant
  without coupling to incidental content — membership checks, threshold checks,
  canonical-source checks, and structural-shape checks.

## The Four Brittle Categories

For this codebase the recognized brittle categories are **exactly** the following
four. An assertion outside these four shapes is not classified as brittle.

### 1. Exact_Count_Assertion

An equality (`==`) between a test expression and a hard-coded integer that
represents a **total test count or whole-suite passing count**.

```python
_PASSING_BASELINE = 4648
assert collected_passing == _PASSING_BASELINE
```

This breaks whenever a test is added or an existing test file is split into more
tests, even though coverage did not regress. Note the scope: only whole-suite or
total test counts are brittle. A domain count such as "13 MCP tools" or a computed,
test-generated value like `record_count == expected_count` is **not** a whole-suite
count and is not brittle.

### 2. Whole_File_Snapshot_Assertion

An equality between a computed SHA-256 digest of an **entire tracked file's** bytes
or text and a hard-coded digest literal (often via a `*_HASH*` / `*_DIGEST*`
module-level constant).

```python
_HASH_ONBOARDING_FLOW = "…64 hex chars…"
assert _sha256(content) == _HASH_ONBOARDING_FLOW
```

This breaks on any edit to the file — a fixed typo, a reworded sentence, a renamed
heading — regardless of whether the protected behavior changed.

### 3. Section_Snapshot_Assertion

An equality between a computed SHA-256 digest of a **substring, section, or block**
extracted from a tracked file and a hard-coded digest literal.

```python
_SNAP_LICENSE_BLOCK = "…64 hex chars…"
assert _snapshot_section_content(content, "License") == _SNAP_LICENSE_BLOCK
```

Same failure mode as the whole-file snapshot, narrowed to one section. It still
breaks on benign edits anywhere inside that section.

### 4. Exact_Sequence_Snapshot_Assertion

An equality between a list of **every** heading or **every** line extracted from a
tracked file and a hard-coded ordered list literal.

```python
_HEADINGS_MODULE_01 = ["Overview", "Setup", "Run the Demo", "Next Steps"]
assert _extract_headings(content) == _HEADINGS_MODULE_01
```

This breaks whenever any heading is added, removed, or reordered — even an unrelated
addition that does not disturb the headings the test actually cares about.

## Structural Replacements

Every brittle category has at least one structural replacement that preserves the
behavioral intent the original assertion was protecting. When remediating, keep the
original intent as a comment or docstring naming the behavior being guarded, and
retain any historical bug-condition coverage via an equivalent structural assertion.

| Brittle category | Structural replacement |
|---|---|
| Exact_Count_Assertion | **Non-regression threshold** |
| Whole_File_Snapshot_Assertion | **Marker / cross-reference membership** |
| Section_Snapshot_Assertion | **Section content invariants** |
| Exact_Sequence_Snapshot_Assertion | **Ordered-subsequence check** |

### Non-regression threshold (replaces Exact_Count_Assertion)

Replace the equality with a check that fails only when the observed count falls
below a recorded floor. Adding or splitting tests keeps it green; a genuine drop in
coverage still fails it.

```python
# Guards against losing onboarding-flow coverage. Floor recorded 2026-06; raising
# it is fine, dropping below it means tests went missing.
_PASSING_FLOOR = 4648
assert collected_passing >= _PASSING_FLOOR
```

### Marker / cross-reference membership (replaces Whole_File_Snapshot_Assertion)

Assert that the required markers, headings, cross-references, or counts the snapshot
was protecting are **present**, tolerating unrelated edits elsewhere in the file.

```python
# The onboarding flow must keep its license gate and the Module 3 hand-off link.
assert "## License Agreement" in content
assert "see Module 3" in content
```

### Section content invariants (replaces Section_Snapshot_Assertion)

Assert that the section contains its required markers or sentinels in the required
relation, rather than hashing the whole block.

```python
license_section = _extract_section(content, "License")
assert "must accept" in license_section
assert "EULA" in license_section
```

### Ordered-subsequence check (replaces Exact_Sequence_Snapshot_Assertion)

Assert that the required headings appear in the required **relative order**,
tolerating unrelated additions interleaved between them.

```python
headings = _extract_headings(content)
required = ["Overview", "Run the Demo", "Next Steps"]
positions = [headings.index(h) for h in required]  # raises if any is missing
assert positions == sorted(positions)               # required order preserved
```

## The Legitimate_Hash_Use Exclusion

Not every use of hashing is a brittle snapshot. A **Legitimate_Hash_Use** computes a
hash of **test-generated data** as part of the behavior under test — for example a
content-hash round-trip property where the test builds the input itself, a
Hypothesis-drawn value, or a file the test wrote earlier under `tmp_path`. These are
classified as **structural assertions**, never as Whole_File_Snapshot_Assertions,
because they are not coupled to a tracked source file's literal digest.

```python
# Legitimate: hashes data the test generated, verifying a round-trip invariant —
# not a snapshot of a tracked source file. NOT brittle.
payload = build_cord_metadata(record)
assert content_hash(payload) == content_hash(round_trip(payload))
```

A related non-brittle pattern is comparing **two freshly computed** digests or
snapshots where neither side is a hard-coded literal (for example, asserting a tool
"wrote nothing" by comparing a before-and-after directory snapshot). The
distinguishing rule is **literal-anchored**: a snapshot category requires a
hard-coded digest or list literal (or a constant resolved to one) on one side.
"Compare two computed values" is never brittle by this definition.

## Allowlisting a Deliberate Exception

When a maintainer makes a reviewed decision that a flagged assertion must stay (for
example, legal text that genuinely must be byte-exact), annotate the assert line with
the `brittle-allow` marker. The scanner then counts it as an allowlisted exemption
rather than a finding.

```python
assert _sha256(content) == _HASH_LEGAL_NOTICE  # brittle-allow: legal text must be byte-exact
```

## For Agents

When writing or reviewing test assertions:

1. Prefer the structural replacement over the brittle shape from the start.
2. Preserve the original guarded intent as a comment or docstring when remediating.
3. Do not weaken regression coverage — keep an equivalent structural assertion for
   any historical bug condition a snapshot was protecting.
4. Use `brittle-allow` only for reviewed, deliberate exemptions.

## Related Documentation

- **Brittleness scanner**: `../../scripts/scan_brittle_assertions.py`
- **Code Quality Standards**: [CODE_QUALITY_STANDARDS.md](CODE_QUALITY_STANDARDS.md)
- **Policies index**: [README.md](README.md)

## Version History

- **v1.0.0** (2026-06): Initial brittleness taxonomy — four brittle categories,
  structural replacements, and the Legitimate_Hash_Use exclusion.

## Navigation

- [← Back to policies](README.md)
- [→ docs/](../)
