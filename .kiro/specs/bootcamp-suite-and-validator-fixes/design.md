# Bootcamp Suite and Validator Fixes — Bugfix Design

## Overview

This design fixes the "broken or incomplete" defects that the prior `bootcamp-consistency-fixes`
spec missed or deferred. All work is **additive** and **non-reverting** with respect to that prior
spec (Requirement 13.3). The defects fall into four independent groups, and within Group A into five
independent lanes:

| Lane | Severity | Fix side | File(s) |
|------|----------|----------|---------|
| **A1** | real product bug | product code | `scripts/preferences_utils.py` |
| **A2** | test-logic bug | test | `tests/test_assess_entry_point.py` |
| **A3** | test-logic bug | test | `tests/test_generate_recap_pdf.py` |
| **A4** | test-logic bug | test | `tests/test_token_budget_optimization.py` |
| **A5** | flaky timing | test | `tests/test_track_reorganization.py` |
| **B** | validator coverage hole | product code + new test | `scripts/validate_mandatory_gates.py` + new regression test |
| **C** | docs out of sync | docs | `CHANGELOG.md` |
| **D** | spurious warning | config (or extraction) | `config/module-dependencies.yaml` (or `scripts/validate_prerequisites.py`) |

Every lane is **separable**: A1, A2, A3, A4, A5, B, C, and D touch disjoint files (the only shared
file is `module-dependencies.yaml`, read by D and by A5's structural tests, but D only edits one gate
requirement string and A5 does not edit the file at all). They can therefore be implemented and
verified in parallel, each behind its own exploration → fix → preservation cycle.

The fix strategy follows the **bug-condition methodology**. For each lane we define:

- **C(X)** — the Bug Condition: the set of inputs that trigger the defect.
- **P** — the Property the fixed code/test must satisfy for every input in C(X).
- **Preservation** — every input where `NOT C(X)` must be **behavior-identical** (and, where the fix
  is in product code, byte-identical output) between the original `F` and the fixed `F'`.

Per the global constraints (Requirements 13.1–13.3): scripts stay stdlib-only (PyYAML only in
`validate_dependencies.py`); no currently-passing validator is weakened; the real ±10% per-file token
tolerance in `measure_steering.py` is left untouched.

### Convergence Gate

The work is complete only when **all** of the following hold deterministically:

```text
python3 -m pytest senzing-bootcamp/tests/ tests/    ->  0 failed (deterministic, incl. A5 across repeated runs)
python3 senzing-bootcamp/scripts/validate_mandatory_gates.py
                                                    ->  parses shipped gates (non-vacuous), covered by a test
CHANGELOG.md [Unreleased]                           ->  documents committed consistency-fix work + this spec's fixes
all 14 standalone validators + CI validator set     ->  continue to pass (validate_power.py, measure_steering --check,
                                                       validate_commonmark.py, sync_hook_registry.py --verify, ...)
scripts                                             ->  remain stdlib-only; +/-10% per-file token check unchanged
```

## Glossary

- **Bug_Condition (C)**: The set of inputs `X` for which `isBugCondition(X)` is true — i.e. the inputs
  that currently trigger a defect. Each lane has its own `C`.
- **Property (P)**: The desired behavior the fixed function/test must satisfy for every `X` in `C(X)`.
- **Preservation**: For every input where `NOT C(X)`, the fixed `F'` must produce the same observable
  result as the original `F`. For product-code fixes (A1, B, D) this is byte/behavior identity; for
  test-only fixes (A2–A5) it means the production code under test is unchanged and previously-passing
  tests still pass.
- **F / F'**: Original (unfixed) code-or-test / fixed code-or-test.
- **Round-trip**: `read(write(x))` for preferences (A1) or `parse(format(x))` for recap documents (A3).
- **`_parse_scalar` / `_serialize_yaml_value`**: The read side / write side of the minimal stdlib YAML
  codec in `preferences_utils.py`. The A1 bug is that these two sides disagree on boolean-like strings.
- **Mandatory gate**: A `⛔ MANDATORY GATE` marker in a steering file that pins a step as non-skippable.
  The validator (`validate_mandatory_gates.py`) parses these and cross-references progress checkpoints.
- **Vacuous pass**: A validator that exits `0` because it found nothing to check, rather than because
  everything it should check passed. Group B fixes a vacuous pass.
- **Observation-first regeneration rule**: Any pinned snapshot, baseline, or "expected set" must be
  produced by *observing the actual current behavior/corpus first*, then encoding that observation as
  the assertion — never by hand-guessing values. Applied to B's expected-gate set and any A3/A4 baseline.

---

## Bug Details

The defects are grouped into independent lanes (A1–A5, B, C, D). Each lane's **Bug Condition**
`C(X)` — the formal `isBugCondition` specification plus concrete examples of manifestation — is
documented in full within that lane's section below. This umbrella section is the index into them:

| Lane | Bug Condition C(X) (summary) | Detail |
|------|------------------------------|--------|
| **A1** | A `str` whose lowercased form is `true`/`false` but whose casing is non-canonical is coerced to `bool` on write->read round-trip | see Group A1 below |
| **A2** | A segment list collapsing to the current directory (`['.']`) makes the test assert `parts == raw segments` and fail | see Group A2 below |
| **A3** | The timestamp strategy emits sections whose timestamps are not actually non-decreasing | see Group A3 below |
| **A4** | The test generates `stored` that can deviate >10% from `measured` then asserts <=10% | see Group A4 below |
| **A5** | Per-example wall time of the corpus scan exceeds the Hypothesis deadline | see Group A5 below |
| **B** | Gates under H2 `## Step N:` or the bold-blockquote marker form are invisible to the H3-only parser (vacuous pass) | see Group B below |
| **C** | `[Unreleased]` omits committed consistency-fix work | see Group C below |
| **D** | The `3->4` requirement string splits into a comma fragment absent verbatim from module 3, causing a spurious warning | see Group D below |

Each lane below contains its own `### Bug Condition` (formal `isBugCondition` pseudocode) and
`### Examples` subsections.

## Expected Behavior

### Preservation Requirements (what must NOT change)

The fixes are surgical. The following existing behaviors MUST remain identical (full per-lane
preservation properties are in each lane's `### Correctness Properties` and in the consolidated
`## Correctness Properties` section):

**Unchanged behaviors:**
- A1: genuine Python `bool`, `int`, canonical-lowercase `'true'`/`'false'` strings, plain strings, and `None` round-trip unchanged in value and type (Req 9.1).
- A2: `_normalize_path` source is byte-identical; all non-degenerate segment inputs still pass (Req 9.2).
- A3: `format_recap_document` / `parse_recap_markdown` are byte-identical; all other recap tests pass (Req 9.3).
- A4: the real ±10% per-file token check and the additive "Budget total mismatch" check in `measure_steering.py` are byte-identical and still pass (Req 9.4).
- A5: detection coverage of real legacy identifiers is unchanged (Req 9.5).
- B: files with genuinely no gate marker still report zero; per-gate cross-reference, `skipped_steps`, `NON_SKIPPABLE_GATES`, and exit-code logic are unchanged; existing gate suites pass (Req 10.1–10.3).
- C: prior `[Unreleased]`/`[0.12.0]`/`[0.11.0]` entries are intact; `validate_commonmark.py` still passes (Req 11.1, 11.2).
- D: all other gates produce the same findings; `module-dependencies.yaml` consumers still parse/pass (Req 12.1, 12.2).
- All groups: the 4816 currently-passing tests still pass; all 14 validators + CI set pass; scripts stay stdlib-only; no prior-spec change is reverted (Req 9.6, 13.1–13.3).

**Scope:** every input where `NOT isBugCondition(X)` for the relevant lane must be byte/behavior
identical between `F` and `F'`.

The desired *correct* behavior on buggy inputs (the Bug-Condition property `P` for each lane) is
defined in the per-lane `### Correctness Properties` subsections and consolidated in the
`## Correctness Properties` section.

## Hypothesized Root Cause

Root causes were confirmed against HEAD (`56b91b4`) by reading the cited functions and, for A1, B,
and D, by running the code. Each lane's `### Hypothesized Root Cause` subsection has the file +
function + line-region citations. Summary:

- **A1** — `preferences_utils.py`: `_parse_scalar` coerces any-case `true`/`false` to `bool`; `_serialize_yaml_value` only quotes the exact-lowercase tokens, so non-canonical-case boolean-looking strings are emitted bare and read back as `bool`. Read and write sides disagree.
- **A2** — test-only: `_normalize_path('.')` correctly yields a `Path` with empty `.parts`; the test's `parts == segments` expectation is wrong for the degenerate `'.'` segment.
- **A3** — test-only: `st_sorted_timestamps` sorts at minute granularity then draws `second` independently after sorting (and clamps month/day), so emitted timestamps aren't monotonic.
- **A4** — test-only: `stored = round(measured*(1+factor))` can deviate >10% for small `measured`, but the assertion demands <=10% and the small-count allowance forgives only abs diff 1.
- **A5** — test-only: full-corpus `os.walk`+`read_text` runs inside the per-example body, exceeding the 200 ms Hypothesis deadline.
- **B** — `validate_mandatory_gates.py`: `step_pattern` matches H3 only; marker detection doesn't tolerate the bold-blockquote form; and the Module 3 marker sits in a `## ⚠️ DO NOT SKIP` preamble *above* `## Step 9:`. No test exercises the validator's own parser.
- **C** — the prior consistency-fix commit didn't update `CHANGELOG.md` `[Unreleased]`.
- **D** — `validate_prerequisites.py` `extract_keywords` comma-splits the `3->4` requirement into a fragment with a parenthetical that doesn't appear verbatim in module 3 content.

## Fix Implementation

Each lane's `### Fix Implementation` subsection specifies the exact file(s), function(s), and minimal
stdlib-only change. Summary of fix surfaces (disjoint — see the Lane Independence note in the matrix):

- **A1** — `scripts/preferences_utils.py`: align `_serialize_yaml_value` (quote any string whose lowercased form is a YAML bool/null literal) and `_parse_scalar` (parse only exact bare `true`/`false` to bool).
- **A2** — `tests/test_assess_entry_point.py`: normalize the expected segments (drop `.`/empty) in `test_result_is_valid_path`; `_normalize_path` untouched.
- **A3** — `tests/test_generate_recap_pdf.py`: make `st_sorted_timestamps`/`st_chronological_sections` emit genuinely non-decreasing timestamps; product round-trip untouched.
- **A4** — `tests/test_token_budget_optimization.py`: generate `stored` provably within ±10%; `measure_steering.py` untouched.
- **A5** — `tests/test_track_reorganization.py`: add `@settings(deadline=None)` and hoist corpus reads to module/class scope; detection logic unchanged.
- **B** — `scripts/validate_mandatory_gates.py`: broaden `step_pattern` to `^#{2,3}\s+Step\s+(\d+):`, tolerate `⛔\s*\**\s*MANDATORY\s*GATE`, associate the Module 3 preamble gate with Step 9; plus a new regression test `tests/test_mandatory_gates_parser_regression.py`.
- **C** — `CHANGELOG.md`: add `[Unreleased]` bullets for the four committed items + this spec's A/B/D fixes (additive).
- **D** — `config/module-dependencies.yaml`: reword the `3->4` requirement so each comma-split keyword appears verbatim in module 3 content (validated candidate provided).

---

## Group A1 — Boolean-like String Coercion (product code)

### Bug Condition

The bug manifests when a preference *string* value whose lowercased form is the YAML literal `true`
or `false`, but whose original casing/spelling is non-canonical (e.g. `'FalSe'`, `'TRUE'`, `'False'`),
is written and then read back. The write side (`_serialize_yaml_value`) emits such a string
**unquoted** (it only quotes the exactly-lowercase tokens `"true"`/`"false"`), and the read side
(`_parse_scalar`) coerces **any-case** `true`/`false` to a Python `bool`. The two sides disagree, so
the string is silently destroyed into a boolean on round-trip.

**Formal Specification:**

```text
FUNCTION isBugCondition(X)
  INPUT: X = a stored preference value (possibly nested in a dict/list)
  OUTPUT: boolean

  RETURN type(X) is str
         AND lower(X) IN {"true", "false"}
         AND X NOT IN {"true", "false"}        // non-canonical casing/spelling
END FUNCTION
```

### Examples

- `write_preference('pacing_overrides', {'0': 'FalSe'})` then read -> got `{'0': False}` (bool), expected `{'0': 'FalSe'}` (str). **(the failing test case)**
- `'TRUE'` (str) -> reads back as `True` (bool). Bug.
- `'False'` (str) -> reads back as `False` (bool). Bug.
- `'true'` / `'false'` (exact lowercase str) — already quoted by the serializer today, so already round-trip as str. **Not** in C(X).
- `True` / `False` (genuine Python bool) — must continue to round-trip as bool. **Not** in C(X) (preservation).
- `18` (int), `'python'` (plain str) — round-trip unchanged. **Not** in C(X) (preservation).

### Hypothesized Root Cause

Confirmed empirically on HEAD (`56b91b4`):

```text
_serialize_yaml_value('FalSe') -> 'FalSe'   (unquoted)
_parse_scalar('FalSe')         -> False     (bool)   <-- data loss
_serialize_yaml_value(True)    -> 'true'    (canonical lowercase, for genuine bool)
_parse_scalar('true')          -> True      (bool)   <-- correct
```

1. **Read side too permissive** (`preferences_utils.py` `_parse_scalar`, ~lines 600–620): uses
   `value.lower() == "true"` / `value.lower() == "false"`, so it coerces *any* casing to bool.
2. **Write side under-quotes** (`preferences_utils.py` `_serialize_yaml_value`, ~lines 290–305): the
   string-quoting guard `if value in ("true", "false", "null", "~", "")` only matches the exactly
   lowercase tokens, so `'FalSe'` / `'TRUE'` are emitted bare and become indistinguishable from a real
   bool on the next read.

The correct contract is a **closed round-trip**: a genuine Python `bool` serializes to a canonical
bare `true`/`false` and parses back to `bool`; every `str` (including boolean-looking ones of any
casing) serializes so that it parses back to the identical `str`.

### Fix Implementation

**File**: `senzing-bootcamp/scripts/preferences_utils.py`. Stdlib-only, minimal, both sides aligned.

1. **Write side — `_serialize_yaml_value`**: broaden the string-quoting guard so it quotes **any**
   string whose lowercased form is a YAML boolean/null literal (case-insensitive), not only the exact
   lowercase tokens. Concretely, replace the membership test on
   `("true", "false", "null", "~", "")` with one that also quotes when `value.lower() in {"true",
   "false", "null"}`. Genuine Python `bool` continues to serialize via the existing
   `isinstance(value, bool)` branch (which emits bare `true`/`false`) — that branch precedes the
   `str` branch and is unaffected.
2. **Read side — `_parse_scalar`**: parse **only** the exact bare tokens `true` / `false` (lowercase,
   unquoted) to `bool`. A quoted token (`"FalSe"`, `"true"`) falls through to the existing
   quote-stripping branch and returns the inner `str`. Keep `null`/`~`/empty -> `None` and the
   `int(value)` branch unchanged. Because the writer now quotes every non-canonical-case
   boolean-looking string, the reader parses bare tokens to bool using exact-lowercase match
   (`value == "true"` / `value == "false"`); bare mixed-case tokens then remain `str`. This is the
   minimal change that makes read and write agree.

The agreement to verify after editing: for the serializer `S` and parser `Pr`,
`Pr(S(x)) == x and type(Pr(S(x))) == type(x)` for every scalar `x` in {genuine bool, any str, int,
None}. This is exactly Property A1-P below.

### Correctness Properties

**Property A1-P (Bug Condition — string fidelity through write->read round-trip)**

_For any_ string `X` where `isBugCondition(X)` holds (lowercased form is `true`/`false` but casing is
non-canonical), the fixed codec SHALL satisfy `read(write(X)) == X` and `type(read(write(X))) is str`.
Equivalently, every boolean-looking string survives a `write_preference` -> `load_preferences`
round-trip unchanged regardless of case.

**Validates: Requirements 5.1**

**Property A1-Pres (Preservation — non-buggy scalars round-trip unchanged)**

_For any_ value `X` where `isBugCondition(X)` does NOT hold — a genuine Python `bool` (e.g.
`license_guidance_deferred: true`), an `int`, the canonical lowercase strings `'true'`/`'false'`, a
plain string, or `None` — the fixed codec SHALL produce the same round-trip result and type as the
original codec: `read_F(write_F(X)) == read_F'(write_F'(X))` with identical Python type.

**Validates: Requirements 9.1**

---

## Group A2 — Degenerate "." Path Segment (test)

### Bug Condition

`test_assess_entry_point.py::TestPathSeparatorNormalization::test_result_is_valid_path` asserts
`list(result.parts) == segments`. For the degenerate segment list `['.']` (or any segment list whose
joined string normalizes to "current directory"), `_normalize_path('.')` correctly returns a `Path`
whose `.parts == ()`, so the assertion `[] == ['.']` fails. The defect is in the test's expectation,
not in `_normalize_path`.

**Formal Specification:**

```text
FUNCTION isBugCondition(segments)
  INPUT: segments = list of path segments fed to the test strategy
  OUTPUT: boolean
  // The normalized path has no parts even though `segments` is non-empty,
  // because the only segment(s) collapse to the current directory.
  RETURN _normalize_path(join(segments)).parts == ()
         AND segments != list(_normalize_path(join(segments)).parts)
END FUNCTION
```

### Examples

- `segments == ['.']` -> `_normalize_path('.')` = `Path('.')`, `.parts == ()`; test asserts `[] == ['.']` -> **fails** (the failing case).
- `segments == ['data', 'raw']` -> `.parts == ('data', 'raw')`; assertion holds. **Not** in C(X).
- `segments == ['data', 'raw', 'file.csv']` -> parts match. **Not** in C(X).

`_normalize_path` is correct: `project_dir / Path('.') == project_dir`, the intended "current
directory" semantics. `Path(PurePosixPath('.'))` has empty `.parts` by Python design.

### Hypothesized Root Cause

`senzing-bootcamp/scripts/assess_entry_point.py` `_normalize_path` (~lines 102–118) does
`Path(PurePosixPath(manifest_path.replace("\\", "/").rstrip("/")))`. For input `'.'` this yields
`Path('.')` whose `.parts == ()` — semantically correct. The test's
`st_path_segments` strategy can draw a single segment `'.'` (the segment char set includes `.`), and
the assertion `list(result.parts) == segments` does not account for the degenerate collapse.

### Fix Implementation

**File**: `senzing-bootcamp/tests/test_assess_entry_point.py`, `TestPathSeparatorNormalization::test_result_is_valid_path` only. `_normalize_path` stays **byte-identical**.

Normalize the *expected* segments the same way `Path` does before comparing — i.e. compare against the
parts that `_normalize_path` of the canonical forward-slash join produces, dropping pure `.`/empty
segments. Minimal options (choose the smallest that keeps the property meaningful):

1. Compute `expected = [s for s in segments if s not in (".", "")]` and assert `list(result.parts) ==
   expected` (drops the degenerate current-dir segment), **or**
2. Compare `result` against `_normalize_path("/".join(segments))` directly (the canonical-separator
   reference), which already encodes the correct collapse, **or**
3. `assume`/filter the `'.'`-only segment case out of `st_path_segments` for this one assertion.

Option 1 is preferred: it keeps full coverage for all real segments and only forgives the
path-semantics-correct collapse. The two sibling tests
(`test_separator_style_produces_same_result`, `test_trailing_slashes_are_stripped`) are unchanged.

### Correctness Properties

**Property A2-P (Bug Condition — test accepts correct path semantics for degenerate input)**

_For any_ segment list where `isBugCondition(segments)` holds (the normalized path collapses to the
current directory), the fixed test SHALL accept the result of `_normalize_path` rather than asserting
parts equal the raw segments.

**Validates: Requirements 5.2**

**Property A2-Pres (Preservation — normal paths unchanged)**

_For any_ segment list where `isBugCondition(segments)` does NOT hold, `_normalize_path` SHALL return
the identical platform-native `Path` as before (source byte-identical) and the fixed
`test_result_is_valid_path` SHALL pass exactly as the original did for all non-degenerate segments.

**Validates: Requirements 9.2**

---

## Group A3 — Chronological Ordering Round-Trip (test)

### Bug Condition

`test_generate_recap_pdf.py::TestModuleOrdering::test_sections_preserve_chronological_order` asserts
parsed section timestamps are non-decreasing after a `format -> parse` round-trip. The round-trip
faithfully preserves **document order**, so the assertion can only fail when the generating strategy
emits sections whose timestamps are *not actually* non-decreasing — which `st_sorted_timestamps` does,
because it sorts at **minute** granularity but then draws `second` independently per timestamp **after**
sorting.

**Formal Specification:**

```text
FUNCTION isBugCondition(sections)
  INPUT: sections produced by st_chronological_sections / st_sorted_timestamps
  OUTPUT: boolean
  // The strategy claims sorted order but the emitted timestamps are not
  // actually non-decreasing once `second` is appended.
  RETURN NOT is_non_decreasing([s.timestamp for s in sections])
END FUNCTION
```

### Examples

- Two timestamps one minute-bucket apart get seconds `01` and `00`: emitted as `...T00:00:01` then `...T00:00:00` -> not non-decreasing -> assertion fails. (Matches Requirement 1.3's example.)
- Sections whose generated seconds happen to be non-decreasing -> test passes by luck. **Not** in C(X).

### Hypothesized Root Cause

`senzing-bootcamp/tests/test_generate_recap_pdf.py` `st_sorted_timestamps` (~lines 926–977): it sorts
`base_minutes` (unique, ascending) then, inside the per-timestamp loop, draws
`second = draw(st.integers(min_value=0, max_value=59))` **independently**. Two adjacent minutes can be
equal only if `unique=True` prevents it — but the seconds are appended without re-sorting, and the
month/day clamps (`min(month, 12)`, `min(day, 28)`) can further collapse distinct minute values to the
same wall-clock prefix, after which the independent seconds break monotonicity. The product round-trip
(`format_recap_document` / `parse_recap_markdown`) is correct and preserves document order.

### Fix Implementation

**File**: `senzing-bootcamp/tests/test_generate_recap_pdf.py`, the `st_sorted_timestamps` /
`st_chronological_sections` strategies only. `format_recap_document` / `parse_recap_markdown` stay
**byte-identical**.

Make the strategy emit *genuinely* non-decreasing timestamps. Minimal options:

1. **Build full datetimes, then sort the final strings.** Construct each complete
   `YYYY-MM-DDTHH:MM:SS` (including the independently-drawn second) from a single monotonic integer
   seconds-from-epoch source, then derive Y/M/D/H/M/S by integer division that never clamps
   distinct sources to the same prefix; with a fixed timezone suffix, lexicographic order equals
   chronological order. Generate `count` **unique** epoch-seconds, sort them, and map each to a
   timestamp string. This removes the independent post-sort `second` draw entirely.
2. **Sort after assembling.** Keep drawing components but collect the assembled
   `YYYY-MM-DDTHH:MM:SS` strings and `sorted(...)` them before building sections (so seconds
   participate in the sort).
3. **Sort sections by timestamp** in `st_chronological_sections` right before returning.

Option 1 is preferred — it fixes the strategy at the source so the "sorted" invariant is structural,
and keeps a single same-timezone suffix so lexicographic == chronological. Use day range 1–28 and
month 1–12 as today to avoid invalid dates. Per the **observation-first regeneration rule**, do not
hand-pin any expected timestamp list; let the corrected strategy generate them and assert monotonicity.

### Correctness Properties

**Property A3-P (Bug Condition — strategy guarantees its own invariant)**

_For any_ section list generated by the fixed strategy, the timestamps SHALL be non-decreasing, and
after `parse(format(sections))` the parsed section order SHALL equal the input order (so
`test_sections_preserve_chronological_order` holds for all generated inputs).

**Validates: Requirements 5.3**

**Property A3-Pres (Preservation — product round-trip unchanged)**

_For any_ recap document, `format_recap_document` / `parse_recap_markdown` SHALL behave exactly as
before (source byte-identical), and every other test in `test_generate_recap_pdf.py` (round-trip,
structural completeness, Q&A pairing, append preservation, timestamp format) SHALL continue to pass.

**Validates: Requirements 9.3**

---

## Group A4 — Self-Falsifying Tolerance Test (test)

### Bug Condition

`test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_stored_token_count_within_tolerance_of_measured`
generates `stored = round(measured * (1 + tolerance_factor))` with `tolerance_factor` up to `0.09`,
then asserts `deviation = abs(stored - measured) / measured <= 0.10`. For small `measured`, rounding
can push the absolute difference to `2`, giving a deviation `> 10%`, while the test's small-count
allowance only forgives an absolute difference of `1`. The test self-falsifies on a value it
generated.

**Formal Specification:**

```text
FUNCTION isBugCondition(measured, tolerance_factor)
  INPUT: generated measured count and tolerance_factor in [0.0, 0.09]
  OUTPUT: boolean
  stored = round(measured * (1 + tolerance_factor))
  RETURN measured > 0
         AND deviation(stored, measured) > 0.10        // assertion would fail
         AND NOT (measured < 50 AND abs(stored - measured) <= 1)  // small-count allowance does not save it
END FUNCTION
```

### Examples

- `content_length=70` -> `measured=18`, `tolerance_factor=0.0859` -> `stored=round(18*1.0859)=20`, `abs=2`, `deviation=11.11% > 10%`, and `abs=2 > 1` so the small-count allowance does not forgive it -> **assertion fails** (the failing case from Requirement 1.4).
- `measured=1000`, `tolerance_factor=0.05` -> `stored=1050`, `deviation=5% <= 10%` -> passes. **Not** in C(X).
- `measured=40`, `tolerance_factor=0.02` -> `stored=41`, `abs=1`, small-count allowance applies -> passes. **Not** in C(X).

### Hypothesized Root Cause

`senzing-bootcamp/tests/test_token_budget_optimization.py`
`test_stored_token_count_within_tolerance_of_measured` (~lines 555–585). The generation
`stored = round(measured * (1 + tolerance_factor))` and the assertion threshold `0.10` are not
mutually consistent: at small `measured`, the rounding step introduces an absolute error of up to
`~1` token that can be `> 10%` in relative terms, and the special-case branch
(`if measured < 50 and abs(stored - measured) <= 1: pass`) forgives only `abs == 1`, not the `abs == 2`
that `tolerance_factor` near `0.09` can produce. The production ±10% per-file check in
`measure_steering.py` is correct and is **not** involved.

### Fix Implementation

**File**: `senzing-bootcamp/tests/test_token_budget_optimization.py`,
`test_stored_token_count_within_tolerance_of_measured` only. `measure_steering.py` is **untouched**.

Make generation and assertion mutually consistent so the test cannot self-falsify. Minimal options:

1. **Generate `stored` provably within tolerance.** Instead of `round(measured * (1 + factor))`, pick
   `stored` from the closed integer interval that is guaranteed within ±10%:
   `lo = ceil(measured * 0.90)`, `hi = floor(measured * 1.10)`, and draw `stored` in `[lo, hi]`
   (always non-empty for `measured >= 1` since `lo <= measured <= hi`). Then assert
   `deviation <= 0.10` with no special-case branch needed.
2. **Align the small-count allowance with the rounding it generates.** Keep the current generation but
   change the allowance to forgive the actual rounding error it can produce — i.e. allow
   `abs(stored - measured) <= 1` to become the *defining* tolerance for small `measured` consistent
   with how `check_counts`/`check_phase_counts` use `abs(stored - measured) / max(measured, 1)`.

Option 1 is preferred: it removes the self-falsification at the source and keeps the asserted
invariant (the real ±10% contract) crisp, mirroring the production check
(`abs(stored - calc) / max(calc, 1) > 0.10`) without weakening it. Per the **observation-first
regeneration rule**, the concrete companion tests (`test_actual_steering_files_token_counts_within_tolerance`,
`test_actual_steering_index_total_tokens_equals_sum`) that read the real `steering-index.yaml` are
**not** changed — they already encode observed real values.

### Correctness Properties

**Property A4-P (Bug Condition — generated `stored` cannot exceed the asserted threshold)**

_For any_ `(measured, tolerance_factor)` the fixed test generates, the generated `stored` SHALL
satisfy `abs(stored - measured) / measured <= 0.10` by construction, so the test's generation and
assertion are mutually consistent and the test cannot self-falsify.

**Validates: Requirements 5.4**

**Property A4-Pres (Preservation — production ±10% check unchanged)**

_For any_ steering file, the per-file ±10% tolerance check in `measure_steering.py`
(`abs(stored - calc) / max(calc, 1) > 0.10`) and the additive aggregate "Budget total mismatch" check
(`parse_budget_total` vs `sum(file_metadata)`) SHALL remain byte-identical and continue to pass
against the real index. `measure_steering.py` is not edited.

**Validates: Requirements 9.4**

---

## Group A5 — Flaky Hypothesis Deadline (test)

### Bug Condition

`test_track_reorganization.py::TestProperty1NoLegacyIdentifiersInFiles::test_no_legacy_id_in_bootcamp_files`
walks `config/`, `steering/`, `docs/`, `scripts/`, `tests/` and reads every file **inside the
per-example body**. The repeated full-corpus scan per generated example exceeds Hypothesis's default
200 ms deadline (~284 ms observed), raising `DeadlineExceeded` intermittently in CI.

**Formal Specification:**

```text
FUNCTION isBugCondition(run)
  INPUT: a CI execution of test_no_legacy_id_in_bootcamp_files
  OUTPUT: boolean
  RETURN per_example_wall_time(run) > hypothesis_deadline   // default 200 ms
END FUNCTION
```

### Examples

- CI run where one example's corpus scan takes 284.63 ms -> `DeadlineExceeded` (the flaky failure in Requirement 1.5).
- A fast local run where each example happens to finish under 200 ms -> passes by luck. **Not** in C(X), but still vulnerable.

### Hypothesized Root Cause

`senzing-bootcamp/tests/test_track_reorganization.py`
`TestProperty1NoLegacyIdentifiersInFiles::test_no_legacy_id_in_bootcamp_files` (~lines 110–148). The
strategy `st_legacy_scannable_id` draws from a 3-element set, but the expensive `os.walk` + per-file
`read_text` over five directories runs once **per generated example** (up to `max_examples=10`),
multiplying I/O. Hypothesis times the per-example body against its deadline, so the repeated file I/O
trips `DeadlineExceeded` non-deterministically. This is a timing artifact, not a product defect.

### Fix Implementation

**File**: `senzing-bootcamp/tests/test_track_reorganization.py`, this test only. Detection logic and
coverage are preserved.

Two complementary, minimal changes (apply both for determinism without losing coverage):

1. **Disable/relax the deadline**: add `@settings(deadline=None)` (or a generous deadline such as
   `deadline=1000`) to the test, since the work is legitimately I/O-bound and not a performance
   regression.
2. **Hoist the corpus read out of the per-example body**: read each scannable file's content **once**
   at module/class scope (e.g. a module-level cached list of `(rel_path, content)` built from the
   same five scan dirs and `_EXCLUDED_FILES` set), and have the per-example body only run the
   `re.compile(rf"\b{legacy_id}\b").search(content)` over the cached contents. This keeps the exact
   same detection set and exclusions, but removes repeated disk I/O so the test is deterministic.

The scan directory set (`config/`, `steering/`, `docs/`, `scripts/`, `tests/`), the
`_EXCLUDED_FILES` exclusions (`scripts/validate_dependencies.py`,
`tests/test_track_reorganization.py`), and the word-boundary regex are unchanged, so detection
coverage is identical.

### Correctness Properties

**Property A5-P (Bug Condition — determinism without DeadlineExceeded)**

_For any_ CI/local run where `isBugCondition(run)` would have held (per-example wall time exceeds the
default deadline), the fixed test SHALL complete without raising `DeadlineExceeded`, verified by
repeated runs all passing.

**Validates: Requirements 5.5**

**Property A5-Pres (Preservation — detection coverage unchanged)**

_For any_ legacy identifier injected into a file under the scanned directories (outside the excluded
files), the fixed test SHALL still detect it (a word-boundary match SHALL still fail the test),
i.e. `detection_coverage(F') == detection_coverage(F)`.

**Validates: Requirements 9.5**

---

## Group B — Vacuous Mandatory-Gate Validator (product code + new test)

### Bug Condition

`validate_mandatory_gates.py` finds **zero** gates against the shipped corpus and exits `0`
vacuously, even though gates ship. Its `_parse_gates_from_file` only matches H3 `### Step N:` headings
and then looks for `⛔ MANDATORY GATE` *within* that step section. The real shipped gates live under
**H2** `## Step N:` headings, and the Module 3 gate uses the **bold-blockquote** form
`> ⛔ **MANDATORY GATE`.

**Formal Specification:**

```text
FUNCTION isBugCondition(corpus)
  INPUT: shipped steering corpus (module-*.md)
  OUTPUT: boolean
  // A gate exists that the H3-only step_pattern + plain inline marker cannot see.
  RETURN EXISTS gate IN corpus SUCH THAT
            gate is under an H2 "## Step N:" heading
            OR gate uses the "> marker **MANDATORY GATE" bold-blockquote form
         AND parse_mandatory_gates(corpus) does NOT include gate
END FUNCTION
```

### Examples (observed on HEAD)

- `module-02-sdk-setup.md` `## Step 5: Configure License` -> `⛔ MANDATORY GATE — Never skip this step...` (H2 heading, inline marker). **Missed today.**
- `module-03-phase2-visualization.md` `## Step 9: Web Service + Visualization Page` with `> ⛔ **MANDATORY GATE — UNCONDITIONAL EXECUTION REQUIREMENT**`. (H2 heading; bold-blockquote marker.) **Missed today.**
- `python3 validate_mandatory_gates.py` -> prints `No mandatory gates found in steering files.` exit `0`. (Confirmed empirically.)
- A genuinely gate-free file (e.g. `module-06-data-processing.md`) -> correctly yields zero gates. **Not** in C(X) (preservation).

> **Critical structural finding (confirmed by inspection):** in
> `module-03-phase2-visualization.md` the gate marker is at line 35, inside a
> `## ⚠️ DO NOT SKIP — Phase 2 Execution Is Mandatory` preamble section that sits **above** the
> `## Step 9:` heading at line 64. So even after broadening the heading regex to H2, a naive
> "marker must fall *within* the Step N section" rule will still miss this gate, because the marker
> precedes its step heading. The fix must associate the Module 3 Step 9 gate correctly. See Fix
> Implementation below.

### Hypothesized Root Cause

`senzing-bootcamp/scripts/validate_mandatory_gates.py` `_parse_gates_from_file` (~lines 140–185):

1. `step_pattern = re.compile(r"^###\s+Step\s+(\d+):", re.MULTILINE)` — **H3 only**. Shipped gates use
   H2 `## Step N:`. Result: `step_matches` is empty for the gate-bearing files, so no section is ever
   scanned and zero gates are returned.
2. Even with H2 added, the marker detection `re.search(r"⛔\s*MANDATORY\s*GATE", section)` does not
   tolerate the `**` bold markers interleaved as in `> ⛔ **MANDATORY GATE` — and, for Module 3, the
   marker is in a sibling section *above* `## Step 9`, not inside it.
3. No test calls the validator's own parser against the real corpus, so the vacuous pass is invisible
   (`test_mandatory_gate_preservation.py` uses its own regex `r"marker\s*\**\s*MANDATORY\s*GATE"` and
   never invokes `parse_mandatory_gates`/`_parse_gates_from_file`).

### Fix Implementation

**File**: `senzing-bootcamp/scripts/validate_mandatory_gates.py` + a new regression test (in
`senzing-bootcamp/tests/` — it validates a real shipped script against the real shipped corpus).

**Parser changes (`_parse_gates_from_file`):**

1. **Broaden the step heading regex** to match H2 and H3:
   `step_pattern = re.compile(r"^#{2,3}\s+Step\s+(\d+):", re.MULTILINE)`. This makes the shipped
   `## Step 5:` and `## Step 9:` headings visible while still matching any `### Step N:`.
2. **Tolerate the bold-blockquote marker form** in gate detection: change the inline check to the same
   shape the preservation tests use, e.g. `re.search(r"⛔\s*\**\s*MANDATORY\s*GATE", section)`, which
   matches both `⛔ MANDATORY GATE` and `⛔ **MANDATORY GATE`. The leading `> ` blockquote prefix does
   not sit between the marker glyph and `MANDATORY`, so it does not interfere; this regex covers both
   shipped forms.
3. **Associate the Module 3 preamble gate with Step 9.** Because the Module 3 gate marker is in the
   `## ⚠️ DO NOT SKIP` section immediately preceding `## Step 9:`, scope the per-step section to
   include any preamble between the prior step heading (or top-of-file) and the step heading itself,
   OR detect gate markers that appear in a `## ...` section whose body explicitly references the step.
   The minimal, robust approach: when computing a step's `section`, extend its start backwards to
   include an immediately-preceding non-Step H2 preamble block (a `## ` heading that is not itself a
   `Step N`/`Phase` heading) so the marker in the `## ⚠️ DO NOT SKIP` block is attributed to the
   following `## Step 9:`. This preserves the existing "section ends at next Step/Phase" end logic.
   (Equivalent acceptable alternative: keep a small, explicitly-documented mapping that the Module 3
   visualization gate binds to Step 9 — but the structural preamble-association is preferred because it
   generalizes.)

Keep **unchanged**: `_get_required_checkpoints` (Module 3 Step 9 -> `["web_service", "web_page"]`),
`NON_SKIPPABLE_GATES = {"3.9"}`, `validate_progress`, `_check_gate`, the `skipped_steps` logic, and the
CLI/exit-code flow. The module-number extraction (`module-(\d+)`) is unchanged.

**New regression test** (`senzing-bootcamp/tests/test_mandatory_gates_parser_regression.py`, new file):

- Import the validator via the standard `sys.path` insert and call its **own**
  `parse_mandatory_gates(steering_dir)` against the **real** `senzing-bootcamp/steering/` corpus.
- Assert the parsed gate set is **non-empty** and **includes** at least the known shipped gates:
  Module 2 Step 5 (license) and Module 3 Step 9 (visualization). Per the **observation-first
  regeneration rule**, derive the "expected non-empty set" from observing the corpus after the fix
  (Module 2 Step 5 + Module 3 Step 9 are the confirmed minimum), and assert membership rather than
  an exact-equality snapshot that would be brittle to future gate additions.
- Assert that the *pre-fix* behavior (zero gates) would fail this test — i.e. include an assertion
  that `len(gates) >= 2` so a regression back to the H3-only parser (zero gates) trips it.
- Add a complementary synthetic case: a file with **no** marker yields `[]` (preservation 10.1),
  and a file with a gate under H2 and another under the blockquote form are both detected.

### Correctness Properties

**Property B-P (Bug Condition — non-vacuous parsing of shipped gates)**

_For any_ corpus where `isBugCondition(corpus)` holds (a gate exists under an H2 `## Step N:` heading
or in the bold-blockquote marker form), the fixed `parse_mandatory_gates` SHALL return a **non-empty**
set that **includes** those gates — at minimum the Module 2 Step 5 license gate and the Module 3
Step 9 visualization gate — so the validator no longer prints `No mandatory gates found` for the
shipped corpus.

**Validates: Requirements 6.1, 6.2, 6.3**

**Property B-Pres (Preservation — gate-free files and downstream checks unchanged)**

_For any_ steering file where `isBugCondition` does NOT hold (no `MANDATORY GATE` marker in any
form), the fixed parser SHALL return `[]` for that file exactly as before, and the existing per-gate
checkpoint cross-reference, `skipped_steps` / `NON_SKIPPABLE_GATES` logic, and exit codes SHALL behave
identically. The existing `test_mandatory_gate_preservation.py` and related suites SHALL continue to
pass.

**Validates: Requirements 10.1, 10.2, 10.3**

---

## Group C — CHANGELOG Out of Sync (docs)

### Bug Condition

`CHANGELOG.md` `[Unreleased]` does not document the consistency-fix work already committed on this
branch (commit `56b91b4`), nor the fixes this spec introduces. A reader of `[Unreleased]` therefore
gets an inaccurate picture of shipped changes.

**Formal Specification:**

```text
FUNCTION isBugCondition(changelog)
  OUTPUT: boolean
  RETURN [Unreleased] OMITS any of:
           lint_steering.py union-registry-source fix,
           measure_steering.py additive aggregate check (parse_budget_total + "Budget total mismatch"),
           steering-index.yaml budget.total_tokens 169633 -> 169576 correction,
           147-test onboarding-split re-target
END FUNCTION
```

### Examples

- Current `[Unreleased]` lists `module-transitions.md` revert, a test rename, and a Module 4 index entry expansion — but **none** of the four committed consistency-fix items. -> in C(X).
- After the fix, `[Unreleased]` contains all four items (plus this spec's A/B/D fixes) -> NOT in C(X).

### Hypothesized Root Cause

The prior `bootcamp-consistency-fixes` work was committed without updating `CHANGELOG.md`
`[Unreleased]`. The four committed items are documented nowhere in the changelog.

### Fix Implementation

**File**: `senzing-bootcamp/CHANGELOG.md`, `[Unreleased]` section only. Additive — existing
`[Unreleased]`, `[0.12.0]`, and `[0.11.0]` content stays intact.

Add bullets under the existing `[Unreleased]` `### Changed` / `### Fixed` subsections (creating
subsections only if needed) documenting:

1. `lint_steering.py` union-registry-source fix.
2. `measure_steering.py` additive aggregate check (`parse_budget_total` + the "Budget total mismatch"
   enforcement against `sum(file_metadata)`).
3. `steering-index.yaml` `budget.total_tokens` correction `169633 -> 169576`.
4. The 147-test onboarding-split re-target.
5. The fixes **this** spec introduces: A1 boolean-string round-trip fidelity in `preferences_utils.py`;
   B non-vacuous mandatory-gate parsing (H2/H3 + blockquote) plus new regression test; D removal of the
   spurious `3->4` prerequisites keyword warning. (The A2–A5 test-only fixes may be summarized as a
   single "stabilized property tests" bullet.)

Keep the markdown CommonMark-clean (the file must continue to pass `validate_commonmark.py`): use the
existing bullet style, language-tagged code fences if any, and no bare URLs. Do not reorder or remove
prior entries.

### Correctness Properties

**Property C-P (Bug Condition — `[Unreleased]` documents the committed + new work)**

_For any_ reading of the post-fix `CHANGELOG.md` `[Unreleased]`, it SHALL contain entries describing
all four committed consistency-fix items (lint_steering union fix, measure_steering additive aggregate
check, `total_tokens` 169633 -> 169576, 147-test onboarding-split re-target) and this spec's A/B/D
fixes.

**Validates: Requirements 7.1**

**Property C-Pres (Preservation — prior entries intact and CommonMark-clean)**

_For any_ pre-existing `[Unreleased]`, `[0.12.0]`, or `[0.11.0]` entry, it SHALL remain present and
unchanged after the edit (additive only, no reverts), and `validate_commonmark.py` SHALL continue to
pass on the updated file.

**Validates: Requirements 11.1, 11.2**

---

## Group D — Spurious 3->4 Prerequisites Keyword Warning (config/extraction)

### Bug Condition

`validate_prerequisites.py` emits `WARNING: Gate '3->4': keyword 'including the step 9 web service +
visualization (cannot be skipped)' not found in module 3 steering content`. The gate's requirement
string in `module-dependencies.yaml` is split on commas by `extract_keywords`, producing a fragment
that does not appear verbatim in module 3 steering, even though the underlying requirement *is*
satisfied.

**Formal Specification:**

```text
FUNCTION isBugCondition(gate)
  OUTPUT: boolean
  RETURN gate.key == "3->4"
         AND EXISTS a comma-split keyword fragment of gate.requires
             that is absent verbatim from the concatenated module-3 steering content
         AND the requirement is in fact satisfied (the warning is spurious)
END FUNCTION
```

### Examples (observed on HEAD)

- Requirement: `"System verification passed, including the Step 9 web service + visualization (cannot be skipped)"`. `extract_keywords` splits on commas into `["system verification passed", "including the step 9 web service + visualization (cannot be skipped)"]`. The first is present; the second is absent verbatim -> **spurious WARNING**.
- Verbatim presence check on module 3 content (confirmed): `system verification passed` -> present; `web service + visualization` -> present; `step 9` -> present; but `including the step 9 web service + visualization (cannot be skipped)` -> absent.

### Hypothesized Root Cause

`senzing-bootcamp/scripts/validate_prerequisites.py` `extract_keywords` (~lines 90–101) splits the
requirement on commas and lowercases each fragment; `_validate_keyword_presence` (~lines 470–500) then
does a substring `in content_lower` test. The `3->4` requirement string contains a long parenthetical
clause and an internal comma boundary that produces a fragment too specific to appear verbatim, even
though the salient tokens ("system verification passed", "web service + visualization", "step 9") all
appear in module 3 content.

### Fix Implementation

Two viable approaches; **reword the config** is preferred because it is the most local change, keeps
`extract_keywords` general (so it still catches genuine mismatches for other gates), and was validated
empirically.

**Preferred — reword the requirement string** in `senzing-bootcamp/config/module-dependencies.yaml`,
gate `"3->4"`, so each comma-split keyword appears **verbatim** in module 3 steering content. Validated
candidate (every comma-split fragment confirmed present in module 3 content):

```yaml
"3->4":
  requires:
    - "System verification passed, web service + visualization, Step 9"
```

Confirmed: `extract_keywords` yields `["system verification passed", "web service + visualization",
"step 9"]`, and all three are substrings of the concatenated module-3 steering content — so the
spurious warning disappears while the requirement's intent (Step 9 web service + visualization, part of
system verification) is preserved.

**Alternative — refine extraction matching** in `validate_prerequisites.py` `extract_keywords` /
`_validate_keyword_presence`: strip parenthetical clauses and match on salient tokens. This is more
invasive and risks changing behavior for other gates, so it is not preferred. If chosen, it must be
shown not to suppress genuine mismatches (verified by a negative example).

Either way, `validate_dependencies.py` (the PyYAML consumer) and the `module-dependencies.yaml`
structural tests in `test_track_reorganization.py` must continue to parse and pass — the reword does
not alter the YAML structure, gate keys, module lists, or track registry.

### Correctness Properties

**Property D-P (Bug Condition — no spurious 3->4 warning; genuine mismatches still caught)**

_For any_ run of `validate_prerequisites.py` after the fix, the `3->4` keyword-mismatch warning SHALL
NOT be emitted (its comma-split keywords appear verbatim in module 3 content), while a genuinely
absent keyword in any gate SHALL still produce a WARNING.

**Validates: Requirements 8.1**

**Property D-Pres (Preservation — other gates and config consumers unchanged)**

_For any_ other gate, `validate_prerequisites.py` SHALL produce the same findings as before (the only
change to its output is the removal of the one spurious `3->4` warning; exit code unchanged), and any
consumer of `module-dependencies.yaml` (e.g. `validate_dependencies.py`, the `test_track_reorganization.py`
structural tests) SHALL continue to parse and pass unchanged.

**Validates: Requirements 12.1, 12.2**

---

## Correctness Properties

This is the single, numbered source of truth for all correctness properties, for PBT traceability.
Each group contributes one Bug-Condition property and one Preservation property. (The detailed
narrative for each lives in its group section above; the canonical numbered list follows.)

Property 1: Bug Condition — A1 boolean-string round-trip fidelity

_For any_ input where `isBugCondition` holds (a string whose lowercased form is `true`/`false` but
whose casing/spelling is non-canonical), the fixed `preferences_utils` codec SHALL satisfy
`read(write(X)) == X` with `type str`.

**Validates: Requirements 5.1**

Property 2: Preservation — A1 non-buggy scalars unchanged

_For any_ input where `isBugCondition` does NOT hold (genuine bool, int, canonical-lowercase
`'true'`/`'false'`, plain string, None), the fixed codec SHALL round-trip identically in value and
type to the original.

**Validates: Requirements 9.1**

Property 3: Bug Condition — A2 test accepts correct degenerate path semantics

_For any_ segment list whose normalized path collapses to the current directory, the fixed test SHALL
accept the `_normalize_path` result instead of demanding `parts == raw segments`.

**Validates: Requirements 5.2**

Property 4: Preservation — A2 normal paths unchanged

_For any_ non-degenerate segment list, `_normalize_path` SHALL be byte-identical and the fixed test
SHALL pass exactly as before.

**Validates: Requirements 9.2**

Property 5: Bug Condition — A3 strategy emits genuinely sorted timestamps

_For any_ section list from the fixed strategy, timestamps SHALL be non-decreasing and survive
`parse(format(...))` in order.

**Validates: Requirements 5.3**

Property 6: Preservation — A3 recap round-trip unchanged

_For any_ recap document, `format_recap_document`/`parse_recap_markdown` SHALL be byte-identical and
all other recap tests SHALL pass.

**Validates: Requirements 9.3**

Property 7: Bug Condition — A4 generated `stored` within asserted tolerance

_For any_ `(measured, tolerance_factor)` the fixed test generates, `stored` SHALL satisfy
`abs(stored - measured)/measured <= 0.10` by construction.

**Validates: Requirements 5.4**

Property 8: Preservation — A4 production ±10% check unchanged

_For any_ steering file, the `measure_steering.py` per-file ±10% check and the additive aggregate
"Budget total mismatch" check SHALL be byte-identical and pass against the real index.

**Validates: Requirements 9.4**

Property 9: Bug Condition — A5 deterministic, no DeadlineExceeded

_For any_ run that previously risked exceeding the deadline, the fixed test SHALL complete without
`DeadlineExceeded` across repeated runs.

**Validates: Requirements 5.5**

Property 10: Preservation — A5 detection coverage unchanged

_For any_ legacy identifier injected into a scanned (non-excluded) file, the fixed test SHALL still
detect it.

**Validates: Requirements 9.5**

Property 11: Bug Condition — B non-vacuous gate parsing

_For any_ corpus containing gates under H2 `## Step N:` headings or the bold-blockquote marker form,
the fixed `parse_mandatory_gates` SHALL return a non-empty set including the Module 2 Step 5 and
Module 3 Step 9 gates.

**Validates: Requirements 6.1, 6.2, 6.3**

Property 12: Preservation — B gate-free files and downstream logic unchanged

_For any_ file with no gate marker, the fixed parser SHALL return `[]`, and the per-gate
cross-reference / `skipped_steps` / `NON_SKIPPABLE_GATES` / exit-code logic SHALL be unchanged; the
existing preservation suites SHALL pass.

**Validates: Requirements 10.1, 10.2, 10.3**

Property 13: Bug Condition — C CHANGELOG documents committed + new work

_For any_ reading of `[Unreleased]` after the fix, it SHALL document all four committed
consistency-fix items and this spec's A/B/D fixes.

**Validates: Requirements 7.1**

Property 14: Preservation — C prior entries intact, CommonMark-clean

_For any_ pre-existing changelog entry, it SHALL remain unchanged and `validate_commonmark.py` SHALL
pass.

**Validates: Requirements 11.1, 11.2**

Property 15: Bug Condition — D no spurious 3->4 warning; genuine mismatches still caught

_For any_ run of `validate_prerequisites.py` after the fix, the `3->4` keyword-mismatch warning SHALL
NOT appear, while genuinely absent keywords SHALL still warn.

**Validates: Requirements 8.1**

Property 16: Preservation — D other gates and config consumers unchanged

_For any_ other gate, findings SHALL be unchanged (only the spurious `3->4` warning removed), and all
`module-dependencies.yaml` consumers SHALL parse/pass.

**Validates: Requirements 12.1, 12.2**

Property 17: Preservation — whole-suite + validator convergence

_For any_ run of `python3 -m pytest senzing-bootcamp/tests/ tests/` and the full validator set, all
previously-passing tests (4816) SHALL still pass, all 14 standalone validators + the CI validator set
SHALL pass, scripts SHALL remain stdlib-only, and no prior-spec change SHALL be reverted.

**Validates: Requirements 9.6, 13.1, 13.2, 13.3**

---

## Testing Strategy

### Validation Approach

Two phases per lane, applied independently: **(1) Exploration** — surface a counterexample that
demonstrates the bug on the *unfixed* code/test and capture a *preservation baseline* before touching
anything; **(2) Verification** — after the fix, the exploration test passes (Fix Checking) and the
preservation baseline is unchanged (Preservation Checking). Because the lanes are independent, each
can be driven through this cycle in parallel.

**Observation-first regeneration rule** (applies to every pinned value): any "expected set",
snapshot, or baseline is produced by *observing actual current behavior first* (run the code/parser,
capture output), then encoding that observation as the assertion. Never hand-guess pinned values.
This governs B's expected-gate set and any A3/A4/preservation baseline.

### Per-Lane Exploration → Fix → Verification

**A1 (product code)**
- Exploration (fails pre-fix): the existing
  `test_session_persistence_properties.py::TestPropertyFieldPreservation::test_writing_one_field_preserves_others`
  already fails on `pacing_overrides={'0': 'FalSe'}`. Add/keep a focused property test asserting
  `read(write(s)) == s` and `type str` for boolean-looking strings of any case.
- Preservation baseline (capture pre-fix): genuine bool / int / plain-string round-trips
  (`license_guidance_deferred: true` etc.) — record current behavior.
- Verify: `python3 -m pytest senzing-bootcamp/tests/test_session_persistence_properties.py -q` green;
  preservation property green; `validate_preferences_schema` tests unaffected.

**A2 (test)**
- Exploration: `test_assess_entry_point.py::TestPathSeparatorNormalization::test_result_is_valid_path`
  fails on `segments == ['.']`.
- Preservation baseline: the two sibling separator/trailing-slash tests pass pre-fix.
- Verify: `python3 -m pytest senzing-bootcamp/tests/test_assess_entry_point.py -q` green;
  `assess_entry_point.py` source unchanged (diff is empty).

**A3 (test)**
- Exploration: `test_generate_recap_pdf.py::TestModuleOrdering::test_sections_preserve_chronological_order`
  fails on the one-second-apart counterexample.
- Preservation baseline: all other tests in `test_generate_recap_pdf.py` pass pre-fix.
- Verify: `python3 -m pytest senzing-bootcamp/tests/test_generate_recap_pdf.py -q` green;
  `generate_recap_pdf.py` source unchanged.

**A4 (test)**
- Exploration: `test_token_budget_optimization.py::TestProperty3SteeringIndexConsistency::test_stored_token_count_within_tolerance_of_measured`
  fails on `content_length=70`.
- Preservation baseline: `measure_steering.py --check` passes pre-fix; concrete real-index tests pass.
- Verify: `python3 -m pytest senzing-bootcamp/tests/test_token_budget_optimization.py -q` green;
  `measure_steering.py` source unchanged; `python3 senzing-bootcamp/scripts/measure_steering.py --check` still passes.

**A5 (test)**
- Exploration: run the class repeatedly to reproduce `DeadlineExceeded`, e.g.
  `python3 -m pytest "senzing-bootcamp/tests/test_track_reorganization.py::TestProperty1NoLegacyIdentifiersInFiles" -q` in a loop.
- Preservation baseline: inject a temporary file containing `fast_track` under a scanned dir and
  confirm the test fails (detection works) — then remove it.
- Verify: 10 consecutive runs of that class all green (deterministic); the injected-identifier check
  still fails the test (coverage preserved).

**B (product code + new test)**
- Exploration (fails pre-fix): the **new** `test_mandatory_gates_parser_regression.py` asserts
  `len(parse_mandatory_gates(real_steering_dir)) >= 2` and membership of Module 2 Step 5 + Module 3
  Step 9 — this fails on the unfixed H3-only parser (returns 0). Confirmed today:
  `python3 senzing-bootcamp/scripts/validate_mandatory_gates.py` prints `No mandatory gates found`.
- Preservation baseline: a synthetic gate-free file yields `[]`; existing
  `test_mandatory_gate_preservation.py` passes pre-fix.
- Verify: the new regression test green; `python3 senzing-bootcamp/scripts/validate_mandatory_gates.py`
  is non-vacuous; `test_mandatory_gate_preservation.py` and friends still green.

**C (docs)**
- Exploration: a check that the four committed items appear in `[Unreleased]` fails pre-fix.
- Preservation baseline: capture current `[0.12.0]`/`[0.11.0]` content; `validate_commonmark.py` passes.
- Verify: `python3 senzing-bootcamp/scripts/validate_commonmark.py` passes post-edit; prior entries
  present (diff is additive).

**D (config)**
- Exploration: `python3 senzing-bootcamp/scripts/validate_prerequisites.py | grep "3->4"` shows the
  spurious warning pre-fix (confirmed today).
- Preservation baseline: capture the full set of findings pre-fix (so we can prove only the one `3->4`
  warning is removed).
- Verify post-fix: `python3 senzing-bootcamp/scripts/validate_prerequisites.py` no longer emits the
  `3->4` warning, exit code unchanged, and the finding set equals the baseline minus that one warning;
  `validate_dependencies.py` and `test_track_reorganization.py` structural tests still pass.

### Fix Checking (general form)

```text
FOR ALL input WHERE isBugCondition(input) DO
  result := fixed(input)          // F' = fixed code-or-test
  ASSERT property_P(result)
END FOR
```

### Preservation Checking (general form)

```text
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT original_F(input) == fixed_F'(input)   // byte/behavior identical
END FOR
```

Property-based testing is used for preservation where the input domain is large (A1 scalar round-trips,
A2 path segments, A3 ordering, A5 identifier scanning, B gate-free/synthetic corpora). Where the fix is
"no production change" (A2–A5 product code, A4 `measure_steering.py`), preservation is additionally
proven by an **empty source diff** plus the relevant validator run.

### Unit Tests

- A1: focused round-trip unit cases for `'FalSe'`, `'TRUE'`, `'False'`, `'true'`(str), `True`(bool), `18`, `'python'`, `None`.
- A2: `_normalize_path('.')`, `_normalize_path('data/raw/')`, mixed/backslash separators.
- B: synthetic single-file parser cases (H2 inline gate; H2 blockquote gate; preamble-before-Step-9 gate; no-gate file).
- D: assert the specific `3->4` warning string is absent; assert a deliberately bogus injected keyword still warns.

### Property-Based Tests (Hypothesis)

- A1 Property 1/2; A2 Property 3/4; A3 Property 5/6; A4 Property 7; A5 Property 9/10; B Property 11/12
  (synthetic corpora). Use `@settings(max_examples=20)` per repo convention; A5 uses `deadline=None`.

### Integration Tests

- B: end-to-end `validate_mandatory_gates.py` run against the real corpus with a constructed progress
  file (gate satisfied vs violated) -> asserts exit code and violation messages (Requirement 6.2).
- Whole-suite convergence: `python3 -m pytest senzing-bootcamp/tests/ tests/` -> 0 failed; full
  validator set (`validate_power.py`, `measure_steering.py --check`, `validate_commonmark.py`,
  `sync_hook_registry.py --verify`, all 14 standalone validators) -> pass (Requirement 13.1).
- stdlib-only check: no new third-party import added to any script (Requirement 13.2).

### Exact Commands

```text
# Full convergence gate (run last)
python3 -m pytest senzing-bootcamp/tests/ tests/

# Per-lane focused runs
python3 -m pytest senzing-bootcamp/tests/test_session_persistence_properties.py -q          # A1
python3 -m pytest senzing-bootcamp/tests/test_assess_entry_point.py -q                       # A2
python3 -m pytest senzing-bootcamp/tests/test_generate_recap_pdf.py -q                        # A3
python3 -m pytest senzing-bootcamp/tests/test_token_budget_optimization.py -q                 # A4
python3 -m pytest senzing-bootcamp/tests/test_track_reorganization.py -q                      # A5 (repeat x10 for determinism)
python3 -m pytest senzing-bootcamp/tests/test_mandatory_gates_parser_regression.py -q         # B (new)
python3 -m pytest senzing-bootcamp/tests/test_mandatory_gate_preservation.py -q               # B preservation

# Validator / script checks
python3 senzing-bootcamp/scripts/validate_mandatory_gates.py        # B: must be non-vacuous
python3 senzing-bootcamp/scripts/measure_steering.py --check        # A4 preservation: +/-10% unchanged
python3 senzing-bootcamp/scripts/validate_commonmark.py             # C preservation
python3 senzing-bootcamp/scripts/validate_prerequisites.py          # D: no spurious 3->4 warning
```

---

## Preservation / Regression Matrix

| Lane | Fix surface | Bug-Condition C(X) (must be fixed) | Preservation set ¬C(X) (must be identical) | How preservation is proven |
|------|-------------|-------------------------------------|----------------------------------------------|----------------------------|
| **A1** | `preferences_utils.py` (`_serialize_yaml_value` + `_parse_scalar`) | boolean-looking strings, non-canonical case | genuine bool, int, `'true'`/`'false'` str, plain str, None | PBT round-trip (Prop 2) + schema-validation tests pass |
| **A2** | `test_assess_entry_point.py` (one test) | segments collapsing to current dir (`['.']`) | all non-degenerate segment lists | sibling separator tests green; `assess_entry_point.py` diff empty |
| **A3** | `test_generate_recap_pdf.py` (strategies) | strategy-emitted non-monotonic timestamps | all already-chronological docs | all other recap tests green; `generate_recap_pdf.py` diff empty |
| **A4** | `test_token_budget_optimization.py` (one test) | small `measured` where rounding deviates >10% | every real steering file's ±10% check | `measure_steering.py --check` green; `measure_steering.py` diff empty |
| **A5** | `test_track_reorganization.py` (one test) | per-example wall time > deadline | detection of any real legacy id | 10x green; injected-id check still fails the test |
| **B** | `validate_mandatory_gates.py` (`_parse_gates_from_file`) + new test | gates under H2 / blockquote / preamble-before-Step | files with no gate marker; cross-ref/skip/exit logic | synthetic no-gate -> `[]`; `test_mandatory_gate_preservation.py` green |
| **C** | `CHANGELOG.md` `[Unreleased]` | `[Unreleased]` omits committed/new work | `[0.12.0]`, `[0.11.0]`, existing `[Unreleased]` lines | `validate_commonmark.py` green; additive diff only |
| **D** | `module-dependencies.yaml` `3->4` requires | spurious `3->4` keyword warning | all other gates; YAML consumers | finding set == baseline minus the one warning; `validate_dependencies.py` + structural tests green |

### Lane Independence (parallelizable)

- **A1** edits `preferences_utils.py` only.
- **A2** edits `test_assess_entry_point.py` only.
- **A3** edits `test_generate_recap_pdf.py` only.
- **A4** edits `test_token_budget_optimization.py` only.
- **A5** edits `test_track_reorganization.py` only.
- **B** edits `validate_mandatory_gates.py` + new `test_mandatory_gates_parser_regression.py` only.
- **C** edits `CHANGELOG.md` only.
- **D** edits `module-dependencies.yaml` (one gate string) only.

No two lanes edit the same file. `module-dependencies.yaml` is *read* by A5's structural tests and by
D, but only D edits it, and the edit does not touch structure/keys/module lists — so A5 and D remain
independent. Each lane can be implemented, tested, and merged on its own; the convergence gate is the
single point where all lanes must hold simultaneously.

### Convergence Gate (definition of done)

```text
python3 -m pytest senzing-bootcamp/tests/ tests/          ->  0 failed, deterministic (incl. A5 across repeated runs)
python3 senzing-bootcamp/scripts/validate_mandatory_gates.py
                                                          ->  non-vacuous (finds shipped gates), covered by new test
CHANGELOG.md [Unreleased]                                 ->  documents committed consistency-fix work + A/B/D fixes
all 14 standalone validators + CI validator set           ->  pass
scripts                                                   ->  stdlib-only; measure_steering.py +/-10% per-file check unchanged
prior bootcamp-consistency-fixes changes                  ->  not duplicated, not reverted (additive only)
```
