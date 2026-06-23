# Module Sequencing Order Bugfix Design

## Overview

The Senzing Bootcamp presents a numbered sequence of modules (1–11) grouped into tracks (Core
Bootcamp = `[1,2,3,4,5,6,7]`, Advanced Topics = `[1..11]`). There is no standalone "sequencer"
program: the running order is produced by the **agent** following the sequencing steering plus the
machine-readable dependency graph in `config/module-dependencies.yaml`. The order is currently
derived from *dependencies and completion state alone*, with **no numeric-order-by-default rule** and
with **Module 3 (System Verification) declared a *soft* prerequisite of Module 4 (Data Collection)**.

Because Module 4 only *hard*-requires Module 1 and treats Module 3 as a soft (warn-but-don't-block)
prerequisite, a dependency-respecting order can legitimately produce `1 → 4 → 5 → 2 → 6 → 7` —
interleaving the preparatory modules (SDK Setup, System Verification) with solution-building modules
and silently skipping Module 3 before real data is loaded in Module 6.

The fix establishes **numeric-order-by-default sequencing** and guarantees **Module 3 runs after
Module 2 and before any data loading (Module 6)** unless the bootcamper explicitly requests to skip
verification. It does this with two reinforcing mechanisms plus documentation reconciliation:

1. **Dependency-graph mechanism** — promote Module 3 from a *soft* to a *hard* prerequisite of
   Module 4 in `module-dependencies.yaml` (`4.requires = [1, 3]`, drop `4.soft_requires`). With
   Module 3 hard-required by Module 4 and Module 2 hard-required by Module 3, any
   dependency-respecting order necessarily places `2 → 3 → 4`, which also forces Module 3 before
   Module 6 (Module 6 follows Module 5 follows Module 4). Module 3 remains explicitly skippable via
   its existing module-level `skip_if`.
2. **Steering mechanism** — add an explicit **Numeric-Order-by-Default Sequencing** rule to the
   always-included `module-transitions.md`: present and run the selected track's modules in ascending
   numeric order, deviating only when there is a clear, stated dependency reason, and run Module 3
   immediately after Module 2 and before any data loading unless explicitly skipped.

The remaining surfaces are documentation/consistency: the `module-prerequisites.md` table cell and
its "Soft Prerequisite Behavior" section, the `module-artifacts.yaml` Module 4 comment, and the one
existing unit test that asserts the old `soft_requires` shape. The `assess_entry_point.py`
recommender already chooses the first incomplete module in **ascending order** — it is the existing
evidence that numeric order is the intended default, and it is **preserved unchanged** by this fix.

`validate_dependencies.py` cross-references the graph against the prerequisites table by comparing
`sorted(requires + soft_requires)` to the module numbers parsed from the table. Moving Module 3 from
`soft_requires` to `requires` keeps that union at `[1, 3]`, so the cross-reference stays green with no
script change.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — for a selected track, the produced
  running `order` is not ascending numeric, OR Module 3 is in the track but missing from `order`
  with no explicit skip request, OR Module 3 appears after data loading (Module 6). Formalized as
  `isBugCondition(X)` below (mirrors `bugfix.md`).
- **Property (P)**: The desired behavior — the produced order is ascending numeric over the modules
  present, and Module 3 runs after Module 2 and before Module 6 unless explicitly skipped.
- **Preservation**: All non-buggy behavior that must remain unchanged — track membership, genuine
  hard-dependency enforcement, explicit-skip handling, the Module 7 → Module 5 quality feedback loop,
  and path-completion detection.
- **F**: The original (unfixed) sequencing logic — order derived from dependencies/completion state
  with no numeric-order default and Module 3 as a *soft* prerequisite of Module 4.
- **F'**: The fixed sequencing logic — numeric-order-by-default with Module 3 a *hard* prerequisite
  of Module 4, guaranteed after Module 2 and before any data loading.
- **track.modules**: The ordered set of module numbers in the selected track (e.g.,
  `[1,2,3,4,5,6,7]`), defined by `tracks` in `module-dependencies.yaml`.
- **order**: The running order the agent produces for the track (the sequence modules are actually
  presented/run in).
- **Hard prerequisite**: A `requires` edge — the dependent module is blocked until the prerequisite
  is complete (or the prerequisite was explicitly skipped by the bootcamper).
- **Soft prerequisite**: A `soft_requires` edge — the agent recommends but does not block; the
  prerequisite may be silently bypassed. **Removed for Module 4 → Module 3 by this fix.**
- **Explicit skip**: A bootcamper request to skip verification ("skip verification" / "I've already
  verified"), recorded against Module 3's `skip_if`. The only permitted way to omit Module 3.
- **Data loading**: Module 6 (Data Processing) — the first module that loads real data into the
  Senzing engine. Module 3 must precede it.

## Bug Details

### Bug Condition

The bug manifests whenever the agent, sequencing a selected track, produces an `order` that is not
ascending numeric, or that silently omits Module 3, or that places Module 3 after data loading
(Module 6). This is possible under F because the only edges forcing Module 3's placement are absent
(Module 4 soft-requires, not hard-requires, Module 3) and no numeric-order default exists.

**Formal Specification (mirrors `bugfix.md`):**

```
FUNCTION isBugCondition(X)
  INPUT: X = (track, order)  // track.modules = selected modules; order = produced running order
  OUTPUT: boolean

  notNumericOrder ← EXISTS i WHERE order[i] > order[i+1]

  module3Skipped ← (3 IN track.modules)
                   AND (3 NOT IN order)
                   AND NOT bootcamperRequestedSkip(3)

  module3AfterLoading ← (3 IN order) AND (6 IN order)
                        AND positionOf(3, order) > positionOf(6, order)

  RETURN notNumericOrder OR module3Skipped OR module3AfterLoading
END FUNCTION

FUNCTION bootcamperRequestedSkip(moduleNumber)
  // True only when the bootcamper explicitly asked to skip the module.
  RETURN explicit skip request present for moduleNumber
END FUNCTION
```

### Examples

- **Interleaved order (BUG — `notNumericOrder`)**: Core track produces `1 → 4 → 5 → 2 → 6 → 7`.
  Module 4 (and 5) run before Modules 2 and 3 because Module 4 only hard-requires Module 1.
  *Expected (F'):* `1 → 2 → 3 → 4 → 5 → 6 → 7`.
- **Silently skipped Module 3 (BUG — `module3Skipped`)**: Core track produces `1 → 2 → 4 → 5 → 6 → 7`
  with no explicit skip request; Module 3 was dropped because it was only a soft prerequisite.
  *Expected (F'):* Module 3 present, running after Module 2 and before Module 6.
- **Module 3 after loading (BUG — `module3AfterLoading`)**: order `1 → 2 → 4 → 5 → 6 → 3 → 7` — real
  data is loaded (Module 6) before the environment is verified (Module 3).
  *Expected (F'):* Module 3 before Module 6.
- **Numeric order already (NOT a bug)**: Core track order `1 → 2 → 3 → 4 → 5 → 6 → 7`. Produced
  identically by F and F'. **Preserved.**
- **Explicit skip of Module 3 (NOT a bug)**: bootcamper said "skip verification"; `order` omits
  Module 3 (`1 → 2 → 4 → 5 → 6 → 7`). `bootcamperRequestedSkip(3)` is true, so this is not the bug
  condition. **Preserved.**
- **Module 7 → Module 5 quality loop (NOT a bug)**: a deliberate backward transition for remapping;
  governed by the quality feedback loop, not the forward sequencing default. **Preserved.**

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- **Track membership unchanged** — the Core track still contains `[1,2,3,4,5,6,7]` and Advanced
  still contains `[1..11]`; this fix changes ordering/strength of a dependency edge, never the
  `tracks` lists. *(Requirement 3.1)*
- **Genuine hard dependencies still enforced** — every existing `requires` edge (e.g., Module 6
  requires Module 5's transformed data) continues to block until satisfied. *(Requirement 3.2)*
- **Explicit skip still honored** — when the bootcamper explicitly requests to skip Module 3, the
  agent honors it; the new hard `requires` edge is satisfied by the explicit skip exactly as the
  general "warn-but-allow on insisted skip" agent behavior already provides. *(Requirement 3.3)*
- **Module 7 → Module 5 quality feedback loop preserved** — the valid backward transition for
  mapping refinement is unchanged; it is not subject to the forward numeric-order default.
  *(Requirement 3.4)*
- **Path-completion detection preserved** — completing the final module of the selected track still
  triggers path-completion detection and the completion celebration. *(Requirement 3.5)*
- **`assess_entry_point.py` recommender unchanged** — it already recommends the first incomplete
  module in ascending order; the fix does not touch it.

**Scope:**

All inputs where `isBugCondition(X)` is false must be completely unaffected. This includes:

- Orders that are already ascending numeric with Module 3 correctly placed.
- Orders where Module 3 was explicitly skipped.
- The Module 7 → Module 5 quality loop and other valid backward transitions.

> **Note:** The expected correct behavior for buggy inputs is defined in Property 1 below. This
> section focuses on what must NOT change.

## Hypothesized Root Cause

The out-of-order / skipped-Module-3 behavior stems from a single design decision plus a missing rule,
replicated across data, steering, and documentation surfaces:

1. **Module 3 declared a *soft* prerequisite of Module 4** in `config/module-dependencies.yaml`
   (`4.soft_requires: [3]`). A soft edge does not constrain ordering and does not block, so a
   dependency-respecting order can place Module 4 (and its successors 5/6) before Modules 2/3 and can
   omit Module 3 entirely. **This is the primary defect.**
2. **No numeric-order-by-default rule** in the always-included sequencing steering
   (`module-transitions.md`). The agent is told how to render the journey map and transitions but is
   never instructed to default to ascending numeric order, so it is free to follow a raw
   dependency/completion order.
3. **Documentation reinforces the soft semantics** — `module-prerequisites.md` carries a "Soft
   Prerequisite Behavior" section ("Warn but do not block") and a "(soft prerequisite)" table
   annotation; `module-artifacts.yaml` has a Module 4 comment "Module 3 is a soft prerequisite —
   warn if missing but do not block." These keep the wrong behavior consistent across surfaces.
4. **A unit test pins the soft shape** — `test_module3_default_on_unit.py::test_module_dependencies_soft_requires`
   asserts `4.soft_requires` contains `3`, encoding the defective design as "correct."

The fix promotes the edge to hard (`4.requires = [1, 3]`, surface 1), adds the numeric-order-by-default
rule (surface 2), reconciles the documentation (surface 3), and updates the pinning test (surface 4)
so all surfaces consistently present numeric-order-by-default sequencing with Module 3 placed after
Module 2 and before data loading.

## Correctness Properties

### Property 1: Fix Checking — Numeric-Order-by-Default Sequencing

_For any_ input where the bug condition holds (`isBugCondition(X)` returns true), the fixed logic F'
SHALL produce an order that:

1. is ascending numeric over the modules present (`FOR ALL i: order'[i] < order'[i+1]`), and
2. places Module 3 after Module 2 and before any data loading (Module 6) — i.e.,
   `(3 NOT IN track.modules) OR bootcamperRequestedSkip(3) OR (positionOf(2, order') <
   positionOf(3, order') AND positionOf(3, order') < positionOf(6, order'))`.

Realized by: Module 3 becoming a hard `requires` edge of Module 4 (so no dependency-respecting order
can place 4/5/6 before 3, nor omit 3 without an explicit skip), plus the numeric-order-by-default
steering rule (so the agent's produced order is ascending unless a stated dependency reason forces a
deviation), plus the reconciled documentation that states the same.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

### Property 2: Preservation — Non-Buggy Sequences Unchanged

_For any_ input where the bug condition does NOT hold (`isBugCondition(X)` returns false), the fixed
logic SHALL produce the same order as the original (`F(X) = F'(X)`), preserving: track membership for
Core and Advanced (3.1); genuine hard-dependency enforcement (3.2); explicit-skip handling for
Module 3 (3.3); the Module 7 → Module 5 quality feedback loop (3.4); and path-completion detection
(3.5). CI checks (`validate_dependencies.py`, `validate_commonmark.py`, `measure_steering.py --check`)
SHALL stay green, and all unrelated graph entries, steering, config, and scripts SHALL stay untouched.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming the root-cause analysis is correct, five surfaces change. The dependency graph and the
prerequisites-table cell must stay mutually consistent (CI runs `validate_dependencies.py`), so they
are edited together; moving Module 3 from `soft_requires` to `requires` keeps the parsed union
(`[1, 3]`) identical, so the cross-reference passes.

---

#### 1. `senzing-bootcamp/config/module-dependencies.yaml`

**Change — promote Module 3 to a hard prerequisite of Module 4 (reqs 2.1, 2.2, 2.3):**

- *Before:*

  ```yaml
  4:
    name: "Data Collection"
    requires: [1]
    soft_requires: [3]
    skip_if: null
  ```

- *After:*

  ```yaml
  4:
    name: "Data Collection"
    requires: [1, 3]
    skip_if: null
  ```

  Remove the `soft_requires` key entirely. Module 3 keeps its own module-level `skip_if`
  ("Bootcamper explicitly requests skip ...") so an explicit skip still satisfies the new hard edge
  (req 3.3). No other module entry, the `tracks` lists, or the `gates` block changes (reqs 3.1, 3.2).

#### 2. `senzing-bootcamp/steering/module-transitions.md`

**Change — add a Numeric-Order-by-Default Sequencing rule (reqs 2.1, 2.4):**

- Add a new section (e.g., after "Journey Map") that states the sequencing default explicitly:
  - Present and run the selected track's modules in **ascending numeric order**
    (`1 → 2 → 3 → … → N` for the modules in the track).
  - Deviate from ascending numeric order **only** when there is a clear, stated dependency reason.
  - **Module 3 (System Verification) runs immediately after Module 2 and before any data loading
    (Module 6)**, unless the bootcamper explicitly requested to skip verification.
  - This default governs forward sequencing only; it does not override the documented Module 7 →
    Module 5 quality feedback loop or other explicit backward transitions (req 3.4).
- Keep the existing journey-map, transition-integrity, and quality-feedback-loop content intact;
  keep CommonMark valid (CI `validate_commonmark.py`) and within the steering token budget
  (`measure_steering.py --check`).

#### 3. `senzing-bootcamp/steering/module-prerequisites.md`

**Change A — Module 4 table cell (req 2.2):**

- *Before:* `| 4 — Data Collection | Module 1 + Module 3 (soft prerequisite) | — |`
- *After:* `| 4 — Data Collection | Module 1 + Module 3 | — |`

  The parser in `validate_dependencies.py` extracts `[1, 3]` from both forms, so the cross-reference
  stays green; this only removes the now-inaccurate "(soft prerequisite)" annotation.

**Change B — replace the "Soft Prerequisite Behavior" section (reqs 2.2, 2.3, 2.4, 3.3):**

- Replace the `### Soft Prerequisite Behavior` block (which currently says "Warn but do not block")
  with a section describing the corrected behavior, e.g. `### Module 3 Sequencing`:
  - Module 3 is a prerequisite of Module 4 and, by default, runs **after Module 2 and before
    Module 4** (and therefore before data loading in Module 6).
  - Modules run in ascending numeric order by default; preparatory Modules 2 and 3 complete before
    solution-building begins at Module 4.
  - Module 3 may be omitted **only** when the bootcamper explicitly requests to skip verification
    ("skip verification" / "I've already verified"). It is never silently skipped or reordered after
    data loading.
  - When the bootcamper insists on skipping, warn about the downstream risk (unverified environments
    can cause hard-to-diagnose issues in Modules 5–7) but allow it — preserving the explicit-skip
    behavior (req 3.3).

#### 4. `senzing-bootcamp/config/module-artifacts.yaml`

**Change — Module 4 comment (req 2.2):**

- *Before:* `# Module 3 is a soft prerequisite — warn if missing but do not block`
- *After:* a comment reflecting the hard prerequisite, e.g. `# Module 3 is a prerequisite — runs
  before Module 4 by default; only an explicit bootcamper skip omits it`.

  The `requires_from` mapping itself (`3: ["docs/progress/MODULE_3_COMPLETE.md"]`) is unchanged —
  Module 3's completion marker is still the artifact Module 4 depends on; only the comment's
  "soft / do not block" wording is corrected.

#### 5. `senzing-bootcamp/tests/test_module3_default_on_unit.py`

**Change — update the pinning test (reqs 2.2, 3.2):**

- `test_module_dependencies_soft_requires` currently asserts `"soft_requires" in module_4` and
  `3 in module_4["soft_requires"]`. Update it (rename as appropriate, e.g.
  `test_module_dependencies_module4_hard_requires_module3`) to assert Module 4 hard-requires Module 3
  — `3 in module_4["requires"]` and `1 in module_4["requires"]`, and that `soft_requires` is absent
  or does not list Module 3. **Updated, not deleted.**
  > Tradeoff note: `test_module3_default_on_properties.py` traverses both `requires` and
  > `soft_requires` edges backward and asserts Module 4 → Module 3 → Module 2 reachability; because
  > Module 3 is now reachable via `requires`, that property test still passes with no change.

## Testing Strategy

### Validation Approach

Two phases: first surface counterexamples that demonstrate the bug on the UNFIXED configuration
(exploration / fix-checking authored to FAIL before the fix), then verify the fix works and preserves
existing behavior (preservation authored to PASS before and after). New property-based test files
live in `senzing-bootcamp/tests/` and follow `python-conventions.md` (pytest + Hypothesis, stdlib +
Hypothesis only — except the dependency graph is loaded with PyYAML exactly as
`validate_dependencies.py` does — class-based, `st_`-prefixed strategies,
`@settings(max_examples=20)`, `from __future__ import annotations`, type hints using `X | None` and
lowercase generics).

A shared domain model mirrors `isBugCondition` from `bugfix.md` and a small reference sequencer
derives the produced order from the dependency graph:

```python
@dataclass
class SeqInput:
    track: list[int]            # selected track modules, e.g. [1,2,3,4,5,6,7]
    order: list[int]            # produced running order
    requested_skip: set[int]    # modules the bootcamper explicitly skipped

def is_bug_condition(x: SeqInput) -> bool:
    not_numeric = any(a > b for a, b in zip(x.order, x.order[1:]))
    m3_skipped = (3 in x.track) and (3 not in x.order) and (3 not in x.requested_skip)
    pos = {m: i for i, m in enumerate(x.order)}
    m3_after_load = (3 in pos) and (6 in pos) and pos[3] > pos[6]
    return not_numeric or m3_skipped or m3_after_load
```

The graph is loaded from `config/module-dependencies.yaml`; a reference sequencer
(`numeric_order_with_deps(track, graph, requested_skip)`) returns the ascending order subject to
hard `requires` edges (a topological tiebreak that prefers the smallest eligible module number) —
this is the executable model of F'.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix; confirm or
refute the root-cause analysis (Module 3 soft-prerequisite + missing numeric default). If refuted,
re-hypothesize.

**Test Plan**: Load the dependency graph and parse the steering, then assert (a) Module 4
hard-requires Module 3, (b) the numeric-order-by-default rule is present in `module-transitions.md`,
and (c) for the Core track a dependency-respecting order can no longer place 4/5/6 before 3. Run on
UNFIXED config to observe failures.

**Test Cases** (will fail on unfixed config):

1. **Module 4 hard-requires Module 3**: `graph.modules[4].requires` contains `3` (and `1`); Module 3
   is not merely in `soft_requires`.
2. **Numeric-order rule present**: `module-transitions.md` contains an explicit ascending /
   numeric-order-by-default sequencing instruction and the "Module 3 after Module 2 and before data
   loading" guarantee.
3. **Prerequisites doc reconciled**: `module-prerequisites.md` no longer contains the "Warn but do
   not block" Soft Prerequisite Behavior section for Module 3.
4. **No interleaving possible (property)**: for every `SeqInput` whose `order` is the reference
   sequencer's output for the Core track with no explicit skip, `is_bug_condition` is false — i.e.,
   the order is `1 → 2 → 3 → 4 → 5 → 6 → 7` with Module 3 before Module 6.

**Expected Counterexamples**: On unfixed config, Module 4 has `soft_requires: [3]` (test 1 fails),
`module-transitions.md` lacks the numeric-order rule (test 2 fails), and the prerequisites doc still
carries the Soft Prerequisite Behavior section (test 3 fails) — confirming the root cause.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, F' produces a corrected order.

**Pseudocode:**

```
FOR ALL X WHERE isBugCondition(X) DO
  order' := numeric_order_with_deps(X.track, graph, X.requested_skip)
  ASSERT FOR ALL i: order'[i] < order'[i+1]                       // ascending numeric
  ASSERT (3 NOT IN X.track) OR (3 IN X.requested_skip)
         OR (positionOf(2, order') < positionOf(3, order')
             AND positionOf(3, order') < positionOf(6, order'))   // M3 after M2, before M6
END FOR
```

Implemented in `test_module_sequencing_order_exploration.py` (Property 1) — authored to FAIL on the
unfixed config (Module 4 soft-requires Module 3; no numeric rule) and PASS after the fix.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, F' behaves identically to
F.

**Pseudocode:**

```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X.track) = F'(X.track)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation because it generates
many cases across the input domain, catches edge cases manual tests miss, and gives strong guarantees
that behavior is unchanged for all non-buggy inputs.

**Test Cases**:

1. **Track membership preserved (3.1)**: `graph.tracks.core_bootcamp.modules == [1,2,3,4,5,6,7]` and
   `graph.tracks.advanced_topics.modules == [1..11]` — unchanged on unfixed and fixed config.
2. **Hard dependencies preserved (3.2)**: every pre-existing `requires` edge (e.g.,
   `6.requires == [2, 5]`, `5.requires == [4]`, `3.requires == [2]`) is unchanged; the only edge
   change is Module 4 gaining `3` as a hard requirement.
3. **Explicit-skip preserved (3.3)**: for a `SeqInput` with `requested_skip == {3}`, `order` omitting
   Module 3 is NOT a bug condition, and the reference sequencer with `requested_skip={3}` omits
   Module 3 while keeping the rest ascending.
4. **Quality feedback loop preserved (3.4)**: the Module 7 → Module 5 backward transition described
   in `module-transitions.md` is intact and is not classified as a numeric-order violation by the
   forward-sequencing default.
5. **Path-completion detection preserved (3.5)**: `module-completion-track.md` still maps Core →
   complete after Module 7 and Advanced → complete after Module 11.
6. **Already-numeric orders unchanged (`F(X) = F'(X)`)**: for any track whose `order` is already
   ascending numeric with Module 3 correctly placed (or explicitly skipped), the reference sequencer
   reproduces it identically.

**Testing Approach (note)**: Observe behavior on UNFIXED config first (track lists, existing hard
edges, completion mapping), then encode those as properties in
`test_module_sequencing_order_preservation.py` (Property 2) — authored to PASS on unfixed config.

### Unit Tests

- **Update** `senzing-bootcamp/tests/test_module3_default_on_unit.py::test_module_dependencies_soft_requires`
  — invert from asserting `4.soft_requires` contains `3` to asserting `4.requires` contains `1` and
  `3` (and that Module 3 is no longer a soft requirement). Updated, not deleted.
- **Review** `senzing-bootcamp/tests/test_module3_default_on_properties.py` — its backward-reachability
  property follows both `requires` and `soft_requires`, so Module 4 → 3 → 2 reachability still holds
  with no change; confirm it stays green.

### Property-Based Tests

- `test_module_sequencing_order_exploration.py` (Property 1 / Fix Checking): generates `SeqInput`
  values satisfying `is_bug_condition`, loads the dependency graph, parses the steering, and exercises
  the reference sequencer; asserts the produced order is ascending numeric and Module 3 is placed
  after Module 2 and before Module 6 (or explicitly skipped). Authored to FAIL on unfixed config.
- `test_module_sequencing_order_preservation.py` (Property 2 / Preservation): generates non-buggy
  `SeqInput` values and asserts track membership, existing hard edges, explicit-skip handling, the
  quality loop, and the completion mapping are unchanged, and that already-numeric orders are
  reproduced identically. Authored to PASS on unfixed config.

### Integration Tests

- Run `python senzing-bootcamp/scripts/validate_dependencies.py` — confirms the graph is internally
  consistent and the `module-prerequisites.md` table still matches the graph
  (`sorted(requires + soft_requires) == [1, 3]` for Module 4) after the edits.
- Run `python senzing-bootcamp/scripts/validate_commonmark.py` — confirms the edited
  `module-transitions.md` and `module-prerequisites.md` stay valid CommonMark.
- Run `python senzing-bootcamp/scripts/measure_steering.py --check` — confirms steering token budgets
  stay within limits after adding the numeric-order section.
- Run the existing Module 3 default-on suites
  (`senzing-bootcamp/tests/test_module3_default_on_unit.py`,
  `test_module3_default_on_properties.py`) to confirm no regressions.

## Security & Convention Compliance

- **No hardcoded MCP server URLs**: no surface in this fix introduces an MCP server URL or any
  external URL; the power's `mcp.json` remains the single source of truth.
- **No prompt-injection / security-bypass instructions**: the steering edit adds an ordering rule and
  removes a soft-skip escape; no user-input interpolation is added.
- **stdlib + PyYAML only**: the new tests load the graph with PyYAML exactly as
  `validate_dependencies.py` does (the documented exception in `tech.md`); all other logic is stdlib +
  Hypothesis.
- **No PII / no real data**: tests use synthetic track/order inputs only.
- **Single source of truth**: the dependency graph (`module-dependencies.yaml`) is edited first; the
  prerequisites table, artifacts comment, and steering are reconciled to it, and
  `validate_dependencies.py` enforces the graph↔table consistency.
- **Requirement alignment**: Property 1 validates Expected Behavior clauses 2.1–2.5; Property 2
  validates Preservation clauses 3.1–3.5 — matching the EARS requirements in `bugfix.md`.
