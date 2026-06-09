# Bugfix Requirements Document

## Introduction

During the design phase for this bugfix, the bootcamp's own mandatory first step was
executed: a live `get_capabilities(version="current")` call against the Senzing MCP
server (`sz-mcp-coworker` v1.24.0). That live call established the **authoritative tool
inventory** and materially changed the scope of this fix:

- The live server exposes **13 tools** (`tool_count: 13`): `get_capabilities`,
  `mapping_workflow`, `analyze_record`, `download_resource`, `explain_error_code`,
  `search_docs`, `find_examples`, `generate_scaffold`, `get_sample_data`,
  `get_sdk_reference`, `sdk_guide`, `reporting_guide`, `submit_feedback`.
- There is **no `lint_record` tool** on the live server.
- The live `analyze_record` **is** the data-mapping validation tool: it returns a
  client-side analyzer script that validates mapped data against the Entity Specification
  *and* reports feature distribution, attribute coverage, and data quality (required
  parameter `workspace_dir`; optional `file_paths` array and `version`).

The original version of this document was authored from the senzing power's **bundled**
tool reference, not from a live call. That bundled reference is itself drifted — it
claims 14 tools and a `lint_record` tool that the live server does not expose — and this
document inherited that phantom-tool error. The `senzing-bootcamp` power, by contrast,
**already matches the live server**: it lists exactly the 13 live tools, states "13
tools" in its counts, and already routes record validation to `analyze_record`.

The original 14-tool / missing-`lint_record` premise is therefore **withdrawn**. Adding
`lint_record`, bumping counts to 14, or re-routing validation away from `analyze_record`
would *inject* drift into a currently-correct power and document a non-existent tool. Two
genuine, ground-truth-confirmed defects survive and are the entire scope of this fix:

1. The `analyze_record` call signature is documented inconsistently across steering and
   module docs — three mutually incompatible signatures, none matching the live schema.
2. The test suite hard-codes a tool inventory with no single source of truth and no
   cross-document guard, so drift in either direction (dropping a real tool *or* adding a
   phantom one like `lint_record`) passes CI silently.

**Source-of-truth constraint:** The live `get_capabilities(version="current")` response
is the authoritative source of truth for tool names, count, signatures, and semantics. It
supersedes the senzing power's bundled reference, any other documentation, and training
data wherever they differ. Before finalizing any tool name, signature, or description
during implementation, the work MUST be confirmed against a live
`get_capabilities(version="current")` call. **If the MCP server is unreachable, the work
MUST BLOCK and surface the MCP connection-troubleshooting steps — there is no offline
fallback, and guessing is what produced this drift in the first place.**

## Bug Analysis

### Current Behavior (Defect)

Two ground-truth-confirmed defects remain after the live capabilities call. Both concern
how `analyze_record` and the tool inventory are documented and tested — not the inventory
contents themselves, which are already correct.

1.1 WHEN the `analyze_record` call signature is documented THEN the system presents three
mutually inconsistent signatures, none matching the live schema:
`steering/mcp-tool-decision-tree.md` uses `analyze_record(record="{...}")`;
`docs/modules/MODULE_5_DATA_QUALITY_AND_MAPPING.md` uses
`analyze_record(record=..., data_source=...)`; and `steering/troubleshooting-commands.md`
uses `analyze_record(file_paths=[...])` while omitting the required `workspace_dir`
parameter. The live schema has no `record=` and no `data_source=` parameter and requires
`workspace_dir`.

1.2 WHEN the test suite is executed THEN the system passes while asserting a brittle,
hand-maintained tool inventory: `tests/test_mcp_tool_decision_tree.py` hard-codes an
"All 12 MCP tools" list (`test_all_12_tools_present`) and
`tests/test_no_direct_sql_preservation.py` hard-codes a parallel "These are the 12 MCP
tools" list (`test_decision_tree_references_all_tools`). There is no single source of
truth and no cross-document guard, so drift in either direction — dropping a real tool, or
adding a phantom tool such as `lint_record` — would pass CI undetected.

### Expected Behavior (Correct)

For each defect, the power's artifacts should present one live-confirmed `analyze_record`
signature and should guard the canonical 13-tool inventory against future drift.

2.1 WHEN the `analyze_record` call signature is documented THEN the system SHALL present
one consistent signature across all files, confirmed against the live schema:
`analyze_record(file_paths=[...], workspace_dir="<writable-dir>", version="current")`,
with no `record=` and no `data_source=` parameter, and with `workspace_dir` always
present.

2.2 WHEN the test suite is executed THEN the system SHALL assert the canonical 13-tool
inventory from a single source of truth and SHALL assert that `analyze_record` is the
validation tool, such that dropping a real tool, adding a phantom tool (e.g.
`lint_record`), or reintroducing a stale 12/14-tool count causes a test failure.

### Unchanged Behavior (Regression Prevention)

The two fixes must not alter the inventory, semantics, conventions, or CI gates that are
**already correct** under live truth. This section explicitly includes the subject matter
that the withdrawn defect clauses had wrongly proposed to change — the inventory, count,
and validation routing are already aligned with the live server and MUST be preserved.

3.1 WHEN the documented MCP tool inventory is read (`POWER.md` "Available MCP Tools",
`steering/mcp-tool-decision-tree.md`, `docs/guides/ARCHITECTURE.md`) THEN the system SHALL
CONTINUE TO list exactly the 13 live tools, with no tool added (no phantom `lint_record`)
and none removed.

3.2 WHEN a tool count is stated THEN the system SHALL CONTINUE TO report 13 tools across
`POWER.md`, `docs/guides/ARCHITECTURE.md`, and `steering/mcp-tool-decision-tree.md`, and
SHALL NEVER change the total to 14.

3.3 WHEN guidance is given for validating a mapped Senzing JSON/JSONL record THEN the
system SHALL CONTINUE TO route the agent to `analyze_record`, and SHALL CONTINUE TO
describe `analyze_record` as Entity-Specification validation plus feature-distribution,
attribute-coverage, and data-quality analysis.

3.4 WHEN the `submit_feedback` tool is described THEN the system SHALL CONTINUE TO treat
it as disabled-by-default via the `disabledTools` array in `mcp.json`.

3.5 WHEN the `analyze-after-mapping` hook is considered THEN the system SHALL CONTINUE TO
use `analyze_record` for record validation and quality analysis, and SHALL CONTINUE TO
keep the hook-sync gates (`scripts/sync_hook_registry.py --verify`) green with
`hook-registry.md` and `hook-registry-modules.md` in sync.

3.6 WHEN CI runs (`validate_power.py`, `measure_steering.py --check`,
`validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest) THEN the system
SHALL CONTINUE TO pass all gates, with steering token budgets in `steering-index.yaml`
respected, CommonMark compliance preserved, and Python scripts remaining stdlib-only.

3.7 WHEN the power is distributed THEN the system SHALL CONTINUE TO confine the MCP server
URL to `mcp.json` as the single source of truth and SHALL NOT introduce static SDK code
(the bootcamp ships no static code; the MCP server generates all SDK code dynamically).

## Bug Condition and Properties

The following structured pseudocode derives the bug condition and the fix/preservation
properties. The condition is anchored to the **live** 13-tool inventory established by the
`get_capabilities(version="current")` call. Here, the "input" `X` ranges over the power's
artifacts and the claims they make about the MCP tool inventory and semantics.

### Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type PowerArtifactClaim   // a documented inventory entry, tool count,
                                        // routing rule, call signature, or test assertion
  OUTPUT: boolean

  // LIVE is the authoritative get_capabilities(version="current") response:
  //   LIVE.tools      = the 13 names listed in the Introduction
  //   LIVE.count      = 13
  //   LIVE.validation = analyze_record
  //   LIVE.signature(analyze_record) = file_paths (optional array),
  //                                    workspace_dir (REQUIRED), version (optional);
  //                                    NO record= and NO data_source=

  RETURN
       (X documents the analyze_record signature
        AND X.signature <> LIVE.signature(analyze_record))
        // e.g. uses record=, uses data_source=, or omits required workspace_dir
    OR (X is a test assertion that encodes a tool inventory <> LIVE.tools
        OR provides no guard against future divergence from a canonical inventory)
END FUNCTION
```

> Note: claims about the *inventory contents*, the *tool count* (13), and *validation
> routing to `analyze_record`* are **NOT** bug conditions — they already match `LIVE`.
> The original 14-tool / `lint_record` premise was refuted by the live call and is
> withdrawn; treating those claims as buggy would inject drift.

### Property: Fix Checking

```pascal
// For every artifact claim that currently triggers the bug,
// the fixed power F' must make it correct.
FOR ALL X WHERE isBugCondition(X) DO
  result <- F'(X)
  ASSERT
       (analyze_record signature is identical across all files
        AND equals analyze_record(file_paths=[...], workspace_dir="<dir>", version="current")
        AND contains NO record= and NO data_source=)
   AND (tests assert the canonical 13-tool inventory from a single source of truth
        AND assert analyze_record is the validation tool
        AND fail if a real tool is dropped, a phantom tool (e.g. lint_record) is added,
            or a stale 12/14-tool count returns)
   AND (every name/signature/semantic was confirmed against a live
        get_capabilities(version="current") response)
END FOR
```

### Property: Preservation Checking

```pascal
// For every artifact claim that is NOT buggy, the fixed power F'
// must behave identically to the original power F.
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
END FOR
```

Where **F** is the current power and **F'** is the reconciled power. Preservation
guarantees that the already-correct content remains unchanged: the live 13-tool
inventory and all 13 tool descriptions, every "13 tools" count (never changed to 14),
validation routing to `analyze_record`, the absence of any phantom `lint_record`,
`submit_feedback` disabled-by-default, the `analyze-after-mapping` hook, the hook-sync
gates, the full CI pipeline, steering token budgets, CommonMark compliance, the
stdlib-only constraint, and MCP-URL confinement to `mcp.json`.
