# MCP Tool Inventory Drift Bugfix Design

## Overview

This design fixes the documented MCP tool inventory drift in the `senzing-bootcamp`
power. It is written *after* executing the bootcamp's own mandatory first step — a
live `get_capabilities(version="current")` call against the Senzing MCP server (the
endpoint configured in `senzing-bootcamp/mcp.json`). Per `bugfix.md`'s source-of-truth
constraint, the **live capabilities response is authoritative and supersedes the
inventory recorded in `bugfix.md` where they differ.**

The live call materially changed the scope of this fix. It is documented in full in
[Mandatory First Step](#mandatory-first-step-live-capabilities-confirmation) below, but
the headline is:

- The live server (`sz-mcp-coworker` v1.24.0) exposes **13 tools**, `tool_count: 13`.
- There is **no `lint_record` tool**. It does not exist on the live server.
- The live `analyze_record` description is: *"Get the Senzing JSON analyzer script with
  commands to analyze and validate mapped data files client-side. Examines feature
  distribution, attribute coverage, and data quality. **Also validates records against the
  Entity Specification.** No source data is sent to the server. REQUIRED parameter:
  `workspace_dir`."* So on the live server, `analyze_record` **is** the validation tool.

`bugfix.md` was written from the *senzing power's bundled tool reference*, not a live
call (it says so explicitly). That bundled reference is itself drifted — it claims 14
tools and a `lint_record` tool that the live server does not expose. `bugfix.md`
inherited that error. The bootcamp power, by contrast, currently lists exactly the live
13 tools and already describes `analyze_record` as the validation tool — so for the
inventory, count, and validation-routing dimensions, **the bootcamp is already correct
and aligned with the live server.**

Consequently, several `bugfix.md` defect clauses are **refuted** by ground truth, and
"fixing" them as originally written (adding `lint_record`, bumping counts to 14,
re-routing validation away from `analyze_record`) would *inject* drift into a
currently-correct power and document a non-existent tool. The bug-condition methodology
anticipates exactly this: the Hypothesized Root Cause / Exploratory phase exists to
**confirm or refute** the hypothesis, and here it refutes the central premise.

What survives as genuine, ground-truth-confirmed bugs:

1. **`analyze_record` call-signature contradiction** (clauses 1.4 / 2.4) — three
   different, mutually inconsistent signatures across the docs, none matching the live
   schema. This is a real defect and is fixed by normalizing to the single live
   signature.
2. **Brittle, unguarded test inventory** (clauses 1.5 / 2.5) — the tests encode a
   hand-maintained "12-tool" list with no guard that cross-checks the documented
   inventory against a single source of truth, so drift in *either* direction (dropping
   a real tool, or adding a phantom one like `lint_record`) passes CI silently. This is
   fixed by introducing a single canonical inventory and a guard test.

Everything else — the 13-tool listing, the "13 tools" count statements, validation
routing to `analyze_record`, `submit_feedback` disabled-by-default, the
`analyze-after-mapping` hook, the hook-sync gates, CI gates, steering token budgets,
CommonMark compliance, the stdlib-only constraint, and MCP-URL confinement — is
**preserved unchanged**, because under live truth it is not buggy.

## Glossary

- **Bug_Condition (C)**: A documented inventory entry, tool count, validation-routing
  rule, `analyze_record` call signature, or test assertion that contradicts the **live**
  Senzing MCP server's authoritative capabilities response.
- **Property (P)**: The desired behavior — every such claim matches the live server: the
  13-tool inventory, a consistent `analyze_record` signature, validation routed to
  `analyze_record`, and tests that fail if the documented inventory drifts from the
  canonical source.
- **Preservation**: Every already-correct claim (the 13 tools and their descriptions,
  the validation routing, `submit_feedback` disabled-by-default, hooks, CI gates, token
  budgets) must remain byte-for-byte unchanged except where a signature normalization is
  required.
- **F** / **F'**: The current (drifted) power and the reconciled power.
- **Live capabilities response**: The JSON returned by `get_capabilities(version="current")`
  from the Senzing MCP server configured in `mcp.json` — the single authoritative source
  of truth for tool names, count, signatures, and semantics.
- **`analyze_record`**: The live MCP tool that returns a client-side Python analyzer
  script which validates mapped Senzing JSON/JSONL against the Entity Specification and
  reports feature distribution, attribute coverage, and data quality. Required parameter
  `workspace_dir`; optional `file_paths` (array) and `version`.
- **`lint_record`**: A tool named in `bugfix.md` and the senzing power's bundled docs
  that **does not exist** on the live server. It is not added by this fix.
- **Drift guard**: A stdlib-only test (backed by a single canonical inventory module)
  that cross-checks the documented tool inventory across `POWER.md`,
  `mcp-tool-decision-tree.md`, and `ARCHITECTURE.md`, failing CI on any divergence.

## Mandatory First Step: Live Capabilities Confirmation

This is a hard gate and was executed before any design conclusions were drawn.

**Procedure (also the implementation prerequisite):**

1. Call `get_capabilities(version="current")` against the Senzing MCP server (the
   endpoint configured in `senzing-bootcamp/mcp.json`) — the bootcamp's own mandatory
   first step.
2. Treat the returned `tools[]` array, `server_info.tool_count`, and each tool's
   `description` as the authoritative inventory, count, and semantics.
3. Where the live response differs from `bugfix.md`, **the live response wins** and
   `bugfix.md`'s inventory is treated as stale evidence.
4. Confirm the `analyze_record` signature against the live tool schema (and, if any
   ambiguity remains, `get_sdk_reference`). Use that exact shape everywhere.

**Live result captured during design (authoritative):**

- `server_info`: `{ server_name: "sz-mcp-coworker", server_version: "1.24.0",
  senzing_version: "current", tool_count: 13 }`
- The 13 tools (verbatim names): `get_capabilities`, `mapping_workflow`,
  `analyze_record`, `download_resource`, `explain_error_code`, `search_docs`,
  `find_examples`, `generate_scaffold`, `get_sample_data`, `get_sdk_reference`,
  `sdk_guide`, `reporting_guide`, `submit_feedback`.
- **No `lint_record`.**
- `analyze_record` is the data-mapping validation tool (validates against the Entity
  Specification *and* reports feature distribution / attribute coverage / data quality);
  required param `workspace_dir`, optional `file_paths` and `version`.

**If the server is unreachable: BLOCK. Do not guess.** The implementation MUST NOT
proceed from `bugfix.md`'s inventory, the senzing power's bundled docs, or training data
when the live call fails. The correct behavior on an unreachable server is to stop and
surface the MCP connection-troubleshooting steps already documented in `POWER.md`
(verify connectivity, test the MCP endpoint, allowlist it behind a proxy, check DNS,
restart the connection), and resume only once a live `get_capabilities` response is
obtained. This mirrors the bootcamp's existing hard-gate behavior: there is no offline
fallback. Guessing is what produced this drift in the first place.

## Bug Details

### Bug Condition

After live confirmation, a documented claim is buggy when it contradicts the **live**
13-tool inventory/semantics. The original `bugfix.md` condition was anchored to a
non-existent 14-tool / `lint_record` model; the corrected condition below is anchored to
ground truth.

**Formal Specification:**

```text
FUNCTION isBugCondition(X)
  INPUT:  X of type PowerArtifactClaim   // a documented inventory entry, tool count,
                                         // routing rule, call signature, or test assertion
  OUTPUT: boolean

  // LIVE is the authoritative get_capabilities(version="current") response:
  //   LIVE.tools      = 13 names (see Mandatory First Step)
  //   LIVE.count      = 13
  //   LIVE.validation = analyze_record
  //   LIVE.signature(analyze_record) = file_paths (optional array),
  //                                    workspace_dir (required), version (optional)

  RETURN
       (X asserts the MCP tool inventory AND X's tool set <> LIVE.tools)
       // includes: omitting a live tool, OR naming a tool not in LIVE (e.g. lint_record)
    OR (X states a tool count AND X.count <> LIVE.count)              // <> 13
    OR (X routes "validate a mapped record" to a tool <> LIVE.validation)
    OR (X documents the analyze_record signature
        AND X.signature is not the single agreed signature confirmed against LIVE)
    OR (X is a test assertion that encodes an inventory <> LIVE.tools
        OR provides no guard against future divergence from the canonical inventory)
END FUNCTION
```

### Classification of `bugfix.md`'s clauses against live truth

| `bugfix.md` clause | Original premise | Live verdict | Disposition |
|---|---|---|---|
| 1.1 / 2.1 inventory omits `lint_record` | 14 tools, `lint_record` missing | **Refuted** — live has 13, no `lint_record`; bootcamp already lists all 13 | **Preserve** (no change; adding `lint_record` would inject drift) |
| 1.2 / 2.2 tool count wrong | should be 14 | **Refuted** — live count is 13; `POWER.md` (13), `ARCHITECTURE.md` ("13 tools") already correct | **Preserve count = 13**; optionally de-confuse the decision-tree's "12 active + 13th" phrasing without changing the total |
| 1.3 / 2.3 validation mis-routed to `analyze_record` | should route to `lint_record` | **Refuted** — `analyze_record` *is* the live validation tool | **Preserve** routing to `analyze_record` |
| 1.4 / 2.4 `analyze_record` signature contradiction | real | **Confirmed** — three inconsistent signatures, none matching live | **Fix** — normalize to the live signature |
| 1.5 / 2.5 tests encode stale model / no drift guard | real | **Confirmed** — brittle hand-kept list, no cross-doc guard | **Fix** — canonical inventory + guard test asserting 13 tools and the validation tool |

### Examples (ground-truth confirmed)

- **Signature contradiction (real bug).** `mcp-tool-decision-tree.md` shows
  `{ "tool": "analyze_record", "record": "{...json...}" }`;
  `docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md` shows
  `analyze_record(record=transformed_record, data_source="CUSTOMERS")`;
  `steering/troubleshooting-commands.md` shows
  `analyze_record(file_paths=["data/transformed/output.jsonl"])`. The live schema has
  **no** `record` or `data_source` parameter and **requires** `workspace_dir`. Expected:
  one signature, `analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")`.
- **Phantom tool (refuted premise → preservation).** `bugfix.md` expects `lint_record`
  to be added as a 14th tool. Live truth: it does not exist. Expected behavior: the
  bootcamp keeps its 13-tool inventory; `lint_record` is **not** introduced.
- **Unguarded inventory (real bug).** `tests/test_mcp_tool_decision_tree.py` and
  `tests/test_no_direct_sql_preservation.py` each hard-code a 12-name list with no
  cross-check against `POWER.md` / `ARCHITECTURE.md` and no canonical source. Expected: a
  single canonical inventory and a guard that fails if any doc surface diverges (dropping
  a real tool *or* adding a phantom one).
- **Already-correct count (refuted premise → preservation).** `ARCHITECTURE.md` already
  states "The Senzing MCP server exposes 13 tools" and lists `analyze_record` as "Validate
  a mapped record against the Entity Spec." Expected behavior: unchanged.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors (must NOT change):**

- The 13-tool inventory in `POWER.md` "Available MCP Tools" — names, order, and
  descriptions of all 13 tools — stays as-is. No tool is added or removed.
- All "13 tools" / 13-total count statements stay at 13 (`POWER.md`, `ARCHITECTURE.md`,
  and the decision-tree's coverage statement). The total is **not** changed to 14.
- Validation of a mapped record continues to route to `analyze_record`; `analyze_record`
  continues to be described as Entity-Specification validation plus feature-distribution,
  attribute-coverage, and data-quality analysis (this already matches live).
- `submit_feedback` remains disabled-by-default via `disabledTools` in `mcp.json`.
- The `analyze-after-mapping` hook keeps using `analyze_record` (it is already correct);
  the hook-sync gates (`sync_hook_registry.py --verify`) stay green, and
  `hook-registry.md` / `hook-registry-modules.md` stay in sync.
- CI stays green: `validate_power.py`, `measure_steering.py --check`,
  `validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest.
- Steering token budgets in `steering-index.yaml` are respected; CommonMark compliance is
  preserved; Python scripts remain stdlib-only (PyYAML only where already used); the MCP
  URL stays confined to `mcp.json`; no static SDK code is introduced.

**Scope:** Any claim that does NOT trigger `isBugCondition` is out of scope and must be
byte-for-byte identical between F and F'. This explicitly includes the 12 unaffected
tools' descriptions and every doc surface that already states 13 tools or routes
validation to `analyze_record`.

> The genuine corrected behavior (one `analyze_record` signature; tests that guard the
> 13-tool inventory) is defined in [Correctness Properties](#correctness-properties).

## Hypothesized Root Cause

The Exploratory phase (the live `get_capabilities` call) already executed and **refuted**
`bugfix.md`'s root-cause hypothesis ("a 14th `lint_record` tool exists and its validation
role was folded into `analyze_record`"). The corrected, evidence-based root causes are:

1. **Upstream documentation drift, not bootcamp drift (for inventory/count/routing).**
   The senzing power's bundled tool reference claims 14 tools / `lint_record`, but its own
   live server exposes 13 with no `lint_record`. `bugfix.md` was authored from that
   bundled reference rather than a live call, so it inherited a phantom tool. The bootcamp
   power was never wrong on this axis — it matches the live server.

2. **Copy-paste signature divergence (for the real signature bug).** `analyze_record`
   call examples were written independently in three files at different times, before the
   `workspace_dir`-required, `file_paths`-based schema was settled, producing three
   mutually inconsistent signatures, none matching live.

3. **No single source of truth for the inventory (for the real test/guard bug).** Each
   test hard-codes its own tool list, and no validator cross-checks the documented
   inventory across `POWER.md`, the decision tree, and `ARCHITECTURE.md`. Nothing fails
   when the lists diverge — which is precisely why drift (in either direction) is
   invisible to CI.

## Correctness Properties

Property 1: Bug Condition — Documented inventory and `analyze_record` signature match the live server

_For any_ documented claim X where the bug condition holds (`isBugCondition(X)` is true —
i.e., X contradicts the live `get_capabilities(version="current")` response), the
reconciled power F' SHALL make X correct: the documented inventory lists exactly the live
13 tools (no phantom `lint_record`, none dropped), every stated total tool count equals
13, validation routing targets `analyze_record`, and the `analyze_record` call signature
is identical across every file and equals the single signature confirmed against the live
schema — `analyze_record(file_paths=[...], workspace_dir="<writable-dir>", version="current")`.
The test suite SHALL assert the canonical 13-tool inventory and the validation tool such
that reintroducing a stale 12/14-tool model, dropping a real tool, or adding a phantom
tool causes a test failure.

**Validates: Requirements 2.4, 2.5** (and resolves 2.1–2.3 by confirming the bootcamp
already satisfies them against live truth)

Property 2: Preservation — Already-correct claims are unchanged

_For any_ documented claim X where the bug condition does NOT hold
(`isBugCondition(X)` is false), the reconciled power F' SHALL produce exactly the same
result as the original power F, preserving: the 13-tool listing and all 13 tool
descriptions, every "13 tools" count, validation routing to `analyze_record`,
`submit_feedback` disabled-by-default, the `analyze-after-mapping` hook and the
hook-sync gates, the full CI pipeline, steering token budgets, CommonMark compliance, the
stdlib-only constraint, and MCP-URL confinement to `mcp.json`.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### The single agreed `analyze_record` signature

Confirmed against the live `get_capabilities` tool schema (and re-confirmable via
`get_sdk_reference`):

```text
analyze_record(file_paths=["data/transformed/<file>.jsonl"], workspace_dir="<writable-dir>", version="current")
```

- `file_paths` — array of mapped Senzing JSON/JSONL paths (optional in the schema, but the
  bootcamp always analyzes a concrete file, so examples include it).
- `workspace_dir` — **required**; a writable directory for the analyzer script and reports.
  Examples use a project-relative path (never `/tmp`), consistent with the bootcamp's file
  storage policy.
- `version` — optional; `"current"` per bootcamp convention.

There is **no** `record=` and **no** `data_source=` parameter. Every documented signature
is normalized to the form above.

### Changes Required — grouped by type

#### A. Signature normalization (the one genuine doc fix) — 3 files

1. **`senzing-bootcamp/steering/mcp-tool-decision-tree.md`** — `### analyze_record` call
   example. Replace the JSON `{ "tool": "analyze_record", "record": "{...}" }` block with
   the agreed signature (expressed in the same JSON call-pattern style as its neighbors,
   using `file_paths` + `workspace_dir` + `version`). Keep the surrounding prose's intent
   (validate a mapped record + attribute coverage) — it already matches live semantics.
2. **`senzing-bootcamp/docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md`** — Step 5
   "Validate Quality" example. Replace `analyze_record(record=transformed_record,
   data_source="CUSTOMERS")` with the agreed signature. The following prose ("validates
   records against the Entity Specification and examines feature distribution, attribute
   coverage, and data quality") already matches live and is preserved.
3. **`senzing-bootcamp/steering/troubleshooting-commands.md`** — "Mapping issues"
   bullet. Update `analyze_record(file_paths=["data/transformed/output.jsonl"])` to add the
   required `workspace_dir` (and `version="current"`), matching the agreed signature.

> All other `analyze_record` references (`common-pitfalls.md`,
> `module-05-phase2-data-mapping.md`, `module-05-phase3-test-load.md`,
> `data-processing-reference.md`, `troubleshooting-decision-tree.md`,
> `docs/guides/AFTER_BOOTCAMP.md`, the `analyze-after-mapping` hook, `hooks/README.md`)
> are **prose that names the tool without showing a signature and routes validation to
> `analyze_record`**. Under live truth that routing is correct, so these are
> **preserved unchanged** (no re-routing, no `lint_record`).

#### B. Inventory / count / routing — NO change (preservation, post-refutation)

- **`senzing-bootcamp/POWER.md`** "Available MCP Tools" (13 tools) and the
  `disabledTools: ["submit_feedback"]` config: **unchanged**. (`bugfix.md` asked to add
  `lint_record` and re-describe `analyze_record`; both are refuted by live truth.)
- **`senzing-bootcamp/docs/guides/ARCHITECTURE.md`** "MCP Tool Categories" ("13 tools" +
  the five category tables): **unchanged** — already correct.
- **`senzing-bootcamp/steering/mcp-tool-decision-tree.md`** Data Preparation routing node
  (validation → `analyze_record`): **unchanged** — correct under live truth. The only
  optional, non-semantic clean-up permitted here is de-confusing the header sentence
  *"covers all 12 MCP tools ... (A 13th tool, `submit_feedback` ...)"* into a clearer
  "12 active routable tools + `submit_feedback` (disabled-by-default) = 13 total" — this
  preserves the total (13) and must not be expressed as 14.

#### C. Hook — NO change (preservation)

The `analyze-after-mapping` hook prompt already says to "use the `analyze_record` MCP
tool to validate a sample of records ... Check feature distribution, attribute coverage,
and data quality ... verify that records conform to the Senzing Generic Entity
Specification." That is exactly the live `analyze_record` role, so the hook stays as-is.

**Mechanism notes for accuracy (and in case any future edit is needed):**

- The `analyze-after-mapping` hook is **not** fragment-composed. `compose_hook_prompts.py`
  only composes the three Module 3 gate hooks (`gate-module3-visualization`,
  `enforce-mandatory-gate`, `enforce-gate-on-stop`) from `hook_prompt_fragments.py`. The
  user-supplied instruction conflated this hook with the fragment composer; this design
  corrects that.
- The hook's authoritative source is `senzing-bootcamp/hooks/analyze-after-mapping.kiro.hook`
  itself. It is mirrored into `steering/hook-registry.md` and
  `steering/hook-registry-modules.md` by `scripts/sync_hook_registry.py`.
- Therefore, **were** a hook-prompt edit ever required, the rule is: edit the
  `.kiro.hook` source, then run `python3 senzing-bootcamp/scripts/sync_hook_registry.py
  --write`, and confirm `--verify` is clean so the CI gate stays green. Because this fix
  makes no hook change, `sync_hook_registry.py --verify` remains green untouched.
- Decision on the hook's tool usage (recommendation requested): the hook should call
  **`analyze_record` only** — on the live server it owns both validation (Entity-Spec
  conformance) and quality (feature distribution / coverage / data quality), so a single
  call covers the hook's full intent. There is no `lint_record` to add.

#### D. Tests + drift guard (the second genuine fix)

Single source of truth (lightest stdlib-only approach, consistent with the existing
`scripts/` + `sys.path` test pattern):

1. **New `senzing-bootcamp/scripts/mcp_tool_inventory.py`** — a tiny stdlib-only module
   (follows the `scripts/` conventions: shebang, `from __future__ import annotations`,
   module docstring, no CLI needed) exposing the canonical inventory as constants:
   - `ACTIVE_TOOLS: tuple[str, ...]` — the 12 routable tools.
   - `DISABLED_TOOLS: tuple[str, ...]` — `("submit_feedback",)`.
   - `ALL_TOOLS: tuple[str, ...]` — the 13 live tools.
   - `TOTAL_COUNT: int = 13`.
   - `VALIDATION_TOOL: str = "analyze_record"`.
   - A module docstring stating these values are confirmed against
     `get_capabilities(version="current")` (server v1.24.0) and must be re-confirmed live
     before any change.

2. **New `senzing-bootcamp/tests/test_mcp_tool_inventory.py`** — the drift guard,
   importing the canonical module. It asserts:
   - `POWER.md` "Available MCP Tools" lists exactly `ALL_TOOLS` (no extra, none missing) —
     fails if `lint_record` (or any phantom) is added or a real tool dropped.
   - `mcp-tool-decision-tree.md` references every tool in `ACTIVE_TOOLS`.
   - `ARCHITECTURE.md` "MCP Tool Categories" lists exactly `ALL_TOOLS` and states the
     `TOTAL_COUNT` ("13 tools").
   - The total-count statements across `POWER.md`, `ARCHITECTURE.md`, and the decision
     tree are mutually consistent and equal `TOTAL_COUNT` (no "14", no bare "12 tools"
     as a *total*).
   - Validation routing asserts `VALIDATION_TOOL == "analyze_record"` and that the
     decision-tree Data Preparation node routes "validate" to `analyze_record` — so a
     future re-introduction of a phantom validation tool fails CI.
   - The `analyze_record` signature in the three normalized files contains `file_paths`
     and `workspace_dir` and does **not** contain `record=` or `data_source=`.

3. **Refactor `senzing-bootcamp/tests/test_mcp_tool_decision_tree.py`** — replace the
   local `_ALL_TOOLS` list with an import of `ACTIVE_TOOLS`; rename
   `test_all_12_tools_present` → `test_all_active_tools_present` and update its docstring
   /the "All 12 MCP tools" comments to reference the canonical count rather than a frozen
   literal `12`.

4. **Refactor `senzing-bootcamp/tests/test_no_direct_sql_preservation.py`** — replace the
   hard-coded `_MCP_TOOL_PATTERNS` list and the "These are the 12 MCP tools..." comment
   with an import of `ACTIVE_TOOLS`; update `test_decision_tree_references_all_tools`'s
   docstring accordingly. Preserve all of this file's SQL-preservation behavior unchanged
   (it validates a *different* bugfix; only the tool-list source changes).

5. **Optional, recommended belt-and-suspenders:** add a `check_mcp_tool_inventory()`
   function to `scripts/validate_power.py` (it already has `check_power_md_references` and
   `check_steering_index_metadata`) that imports `mcp_tool_inventory` and performs the same
   `POWER.md`/`ARCHITECTURE.md` cross-check, so the guard also runs in the
   `validate_power.py` CI gate, not only pytest. The pytest guard (item 2) is the required
   minimum; this is the lightest way to also cover the non-pytest gate.

### Token-budget impact

The only steering file edited is `mcp-tool-decision-tree.md` (one call-pattern block and,
optionally, one clarified sentence). The token delta is small, but it is still nonzero,
so the implementation MUST run `python3 senzing-bootcamp/scripts/measure_steering.py` to
recompute and update the `token_count` for `mcp-tool-decision-tree.md` in
`steering-index.yaml` (currently `2305`, `size_category: large`), then confirm
`python3 senzing-bootcamp/scripts/measure_steering.py --check` passes within tolerance.
No other steering file changes, so no other budget entries move. (Because this fix does
*not* add `lint_record` content anywhere, the large token increase `bugfix.md` /
point 5 anticipated does not occur — the budget note still applies, just at a much smaller
magnitude.)

## Testing Strategy

### Validation Approach

Two phases: first, the Exploratory live call (already executed) that surfaced the refuted
premise and pinned ground truth; then verify the fix (signature normalized, guard catches
drift) and confirm all already-correct content and CI gates are preserved.

### Exploratory Bug Condition Checking

**Goal**: Confirm or refute the root-cause hypothesis before changing anything.
**Outcome (already executed):** `get_capabilities(version="current")` returned 13 tools,
no `lint_record`, with `analyze_record` as the validation tool — **refuting** the
14-tool/`lint_record` hypothesis and **confirming** the signature-contradiction and
missing-guard defects. The design was re-scoped accordingly.

**Test Plan**: For the surviving signature bug, write an assertion that scans the three
signature-bearing files for `analyze_record` examples and checks them against the live
schema. Run it on the **unfixed** docs to observe the failures (the `record=` /
`data_source=` forms and the missing `workspace_dir`).

**Test Cases (expected to fail on unfixed code):**
1. **Decision-tree signature** — `analyze_record` example uses `record=` (no
   `workspace_dir`). Fails.
2. **Module 5 doc signature** — uses `record=` + `data_source=`. Fails.
3. **Troubleshooting-commands signature** — uses `file_paths` but omits required
   `workspace_dir`. Fails.
4. **Drift guard against the phantom tool** — a guard that asserts `POWER.md` lists exactly
   the live 13 tools would (correctly) reject any attempt to add `lint_record`.

**Expected Counterexamples**: three divergent `analyze_record` signatures; none matches
`file_paths` + required `workspace_dir`.

### Fix Checking

**Goal**: For all inputs where the bug condition holds, the fixed power produces the
expected behavior.

```text
FOR ALL X WHERE isBugCondition(X) DO
  result := F'(X)
  ASSERT
       (documented inventory = LIVE.tools, i.e. exactly the 13 tools, no lint_record)
   AND (every stated total tool count = 13)
   AND (validation routing targets analyze_record)
   AND (analyze_record signature is identical across all files
        = analyze_record(file_paths=[...], workspace_dir="<dir>", version="current"))
   AND (tests assert the canonical 13-tool inventory and the validation tool,
        failing if a tool is dropped OR a phantom tool is added OR a stale count returns)
   AND (all names/signatures/semantics were confirmed against the live
        get_capabilities(version="current") response)
END FOR
```

### Preservation Checking

**Goal**: For all inputs where the bug condition does NOT hold, the fixed power behaves
identically to the original.

```text
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

**Testing Approach**: Property-based testing is well-suited to preservation here because
the existing `test_no_direct_sql_preservation.py` already snapshots unfixed content and
asserts it is preserved across many generated inputs. We keep that approach: the 13 tool
names, their descriptions, validation routing, and the hook/registry text are snapshotted
and asserted unchanged.

**Test Plan**: Observe the unfixed content for the non-buggy surfaces (the 13-tool listing,
the "13 tools" counts, validation→`analyze_record` routing, `submit_feedback`
disabled-by-default, the `analyze-after-mapping` hook text, the registry sync) and assert
it is byte-for-byte preserved after the fix.

**Test Cases:**
1. **Inventory preservation** — `POWER.md` still lists exactly the 13 tools, unchanged
   descriptions; no `lint_record` introduced.
2. **Count preservation** — `ARCHITECTURE.md` and `POWER.md` still state 13; never 14.
3. **Routing preservation** — decision-tree Data Preparation node still routes validation
   to `analyze_record`.
4. **Hook / registry preservation** — `analyze-after-mapping.kiro.hook` text unchanged and
   `sync_hook_registry.py --verify` clean.
5. **Other-tool preservation** — the 12 unaffected tools' names/purposes/call patterns
   unchanged (the existing PBT in `test_no_direct_sql_preservation.py`, now sourcing its
   list from the canonical module).

### Unit Tests

- `analyze_record` signature normalization is correct in all three files (presence of
  `file_paths` + `workspace_dir`; absence of `record=` / `data_source=`).
- `POWER.md`, `ARCHITECTURE.md`, and the decision tree list exactly the canonical 13 tools.
- All total-count statements equal 13 and are mutually consistent.
- `VALIDATION_TOOL` resolves to `analyze_record` and the decision tree routes validation
  there.

### Property-Based Tests

- For any tool name in the canonical `ALL_TOOLS`, it appears in `POWER.md`,
  `ARCHITECTURE.md`, and (for `ACTIVE_TOOLS`) the decision tree — and adding any name not
  in `ALL_TOOLS` (e.g., `lint_record`) to a doc surface fails the guard.
- For any non-buggy snapshotted section, content is preserved between F and F'
  (reuse/extend the existing preservation PBTs).

### Integration Tests

- Full CI sequence stays green: `validate_power.py` (incl. the optional new inventory
  check), `measure_steering.py --check`, `validate_commonmark.py`,
  `sync_hook_registry.py --verify`, then pytest (incl. the new guard and refactored
  inventory tests).
- `measure_steering.py` recomputes `mcp-tool-decision-tree.md`'s token count and
  `--check` passes within tolerance.

## Requirements Traceability

| `bugfix.md` clause | Design handling | Property |
|---|---|---|
| 1.1 / 2.1 inventory (`lint_record`) | **Refuted by live truth** — bootcamp already lists the live 13; `lint_record` not added | Property 2 (Preservation) |
| 1.2 / 2.2 tool count | **Refuted** — count already 13; kept at 13 (optional decision-tree wording clean-up) | Property 2 (Preservation) |
| 1.3 / 2.3 validation routing | **Refuted** — `analyze_record` is the live validation tool; routing preserved | Property 2 (Preservation) |
| 1.4 / 2.4 `analyze_record` signature | **Fixed** — normalized to `analyze_record(file_paths=[...], workspace_dir=..., version=...)` in 3 files (§A) | Property 1 (Fix-Checking) |
| 1.5 / 2.5 tests / drift | **Fixed** — canonical `mcp_tool_inventory.py` + new guard test + refactored existing tests (§D) | Property 1 (Fix-Checking) |
| 3.1 12 unaffected tools | Unchanged; tests source names from canonical module | Property 2 (Preservation) |
| 3.2 `analyze_record` genuine role | Preserved (validation + feature/coverage/quality) | Property 2 (Preservation) |
| 3.3 `submit_feedback` disabled-by-default | Unchanged in `mcp.json`; encoded in `DISABLED_TOOLS` | Property 2 (Preservation) |
| 3.4 hook-sync gates | No hook change; `sync_hook_registry.py --verify` stays green | Property 2 (Preservation) |
| 3.5 CI gates / token budgets / stdlib | All gates green; `measure_steering.py` rerun; stdlib-only guard | Property 2 (Preservation) |
| 3.6 MCP URL confinement / no static SDK | MCP URL stays in `mcp.json`; no SDK code added | Property 2 (Preservation) |
