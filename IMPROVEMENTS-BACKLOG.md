# Senzing Bootcamp Power — Improvements Backlog

Saved state for a batch of power improvements (items #1, #2, #3, #5, #6, #7, #8 from an
earlier review). This file is a planning note for resuming work later. It lives at the repo
root intentionally — it is NOT part of the distributed `senzing-bootcamp/` power.

> Numbering note: items are kept at their original review numbers (#4 was "CI tests only one
> Python version" and is NOT part of this batch).

## Packaging decision (already made)

The seven items were grouped into **5 specs**, to be **created first, then implemented**:

| Spec | Covers | Type | Status |
|------|--------|------|--------|
| `steering-index-token-count-sync` | #1 | bugfix | Fully drafted — ready to implement |
| `governance-rule-conformance` | #2 | feature | Fully drafted — ready to implement |
| `hook-architecture-improvements` | #5 + #6 + #7 | feature | Fully drafted — ready to implement |
| `steering-corpus-split` | #3 | optimization | Fully drafted — ready to implement |
| `conversational-eval-harness` | #8 | feature | Fully drafted — ready to implement |

**Spec-creation phase: COMPLETE.** All five specs have requirements/bugfix + design + tasks,
all format-clean. Next phase: implementation, in order #1 -> #2 -> hook-arch -> #3 -> #8.

Implementation order chosen: #1 -> #2 -> hook-arch(#5/#6/#7) -> #3 -> #8.

## The items

### #1 — Stale token counts in `steering-index.yaml` (bugfix)
`modules.<N>.phases.<phase>.token_count` has drifted from `file_metadata.<file>.token_count`
for the same file (e.g. `module-03-phase2-visualization.md`: phases=2035 vs measured 5312, a
2.6x under-count). The agent uses the phase values for context-budget math on split modules,
so it under-counts load and can exceed the 60%/80% thresholds. `measure_steering.py --check`
validates only `file_metadata`, never the `phases` map, so the drift is silent in CI.
Fix: extend `measure_steering.py` so `--check` AND update mode also process phase entries
(stdlib-only, no PyYAML); reconcile the data by running the fixed update mode (not hand-edit).
Confirmed drifted phases (live re-measure): module-03 phase2-visualization (2035->5312),
module-01 phase1 (3257->4527), module-05 phase2 (1894->3128, medium->large), module-06 phaseA
(662->1219), module-07 phase1 (3183->3591). module-11 phase1 (3214 vs 3289) is WITHIN tolerance.

### #2 — Governance-rule conformance check (feature)
No artifact maps each governing rule to its enforcement point, so drift is invisible until a
manual audit (how the last three bugs were found). Add `config/governance-rules.yaml`
(registry: id, rule text, category, enforced_by, assertions), a stdlib-only validator
`scripts/validate_governance_rules.py`, a CI step in `validate-power.yml`, and pytest+Hypothesis
tests. Seed v1 with the mechanically-checkable rules: pointer (emoji) prefix, MCP-first, Rule 6
(search_docs on the 3 license-insufficient sections), Rule 15 (NON_SKIPPABLE_GATES has "3.9" +
CONDITION B absent), hook-name "to (verb phrase)", feedback-file path, frontmatter inclusion,
graduation always-creates completion-summary. Behavioral-only rules (e.g. runtime
ambiguous-question avoidance) are recorded as documented-but-not-statically-checkable.

### #3 — Steering corpus near the context ceiling (optimization)
Total steering ~= 166,655 / 200,000 tokens (~83%). Several files exceed the documented
`split_threshold_tokens` (5000): `onboarding-flow.md` (5438), `module-03-system-verification.md`
(6419), `module-03-phase2-visualization.md` (5312), `hook-registry-critical.md` (8169),
`hook-registry-modules.md` (8476), `agent-instructions.md` (5013). The split machinery exists
but isn't applied to its own threshold violators. Trim/split, prioritizing early-loaded files.
NOTE: depends on / overlaps #1 — do #1 first so the token counts are trustworthy before deciding
what to split.

### #5 — agentStop hook stacking (hook architecture)
Six hooks fire on `agentStop` (`ask-bootcamper`, `module-completion-celebration`,
`module-recap-append`, `enforce-gate-on-stop`, `enforce-visualization-offers`,
`session-log-events`), each reading progress files and running prompt logic every turn-end.
Confirm deterministic ordering, document the intended fire order, and assess combined
latency/cost.

### #6 — Hook-prompt duplication (hook architecture)
Gate logic (the CONDITION A/B blocks) was duplicated verbatim across 3 hook files + the registry
mirror — exactly how an escape hatch hid in one place. Introduce a shared prompt-fragment
mechanism so gate logic has a single source. `sync_hook_registry.py` keeps the mirror aligned but
the 3 hooks still hand-duplicate large prompt blocks.

### #7 — Capture hooks are opt-in (hook architecture)
Completion-summary / journey fidelity (Rules 13/16) depends on `session-log-events` being
installed, but hook install is opt-in via `install_hooks.py`. If skipped, capture degrades
silently. Auto-install the capture-critical hooks, or warn at onboarding when they're absent.
(`module-recap-append` is a postTaskExecution backstop, so Q&A survives, but the live
action/artifact stream relies on the hook.)

### #8 — Tests assert document content, not agent behavior (feature)
The ~2,600-test suite mostly parses steering markdown and asserts strings are present ("does the
file say X"), proving instructions are written correctly, not that an agent follows them. Add a
small conversational-eval harness: scripted transcripts checked against expected agent moves at
gates / pointer questions, to catch behavioral regressions the string tests can't.

## Resume instructions

1. **Finish creating specs (current phase).** All 5 specs should be fully drafted before
   implementing (per the chosen plan).
   - Next action: regenerate Spec 2 (`governance-rule-conformance`) **design.md** — requirements
     are done. The design subagent was cancelled mid-run, so design.md does not exist yet.
   - Then Spec 2 **tasks.md**.
   - Then create Spec 3 `hook-architecture-improvements` (#5+#6+#7), Spec 4 `steering-corpus-split`
     (#3), Spec 5 `conversational-eval-harness` (#8) — each requirements -> design -> tasks.
   - Specs must be created one at a time (no parallel spec creation).
2. **Then implement**, in order: #1, #2, hook-arch, #3, #8. Each spec follows the repo's
   two-phase PBT pattern (exploration test that fails on unfixed code -> preservation test ->
   fix -> verify -> CI checkpoint).

## Conventions to honor (from workspace steering)
- Scripts: Python 3.11+, **stdlib only** (no PyYAML except `validate_dependencies.py`),
  snake_case, `main(argv=None)`, argparse, exit 0/1.
- Tests: pytest + Hypothesis, class-based, `st_`-prefixed strategies, `@settings(max_examples=20)`,
  `from __future__ import annotations`, type hints (`X | None`, `list[str]`), in `senzing-bootcamp/tests/`.
- Hook JSON schema: `name`, `version`, `when`, `then`; names in "to (verb phrase)" form.
- CI (`.github/workflows/validate-power.yml`) must stay green: `validate_power`,
  `measure_steering --check`, `validate_commonmark`, `validate_dependencies`,
  `sync_hook_registry --verify`, `validate_prerequisites`, `validate_progress_ci`,
  `validate_mandatory_gates`, `validate_yaml_schemas`, ruff, pytest.
- No MCP server URL hardcoded outside `mcp.json`.
- Everything in `senzing-bootcamp/` ships to users — no dev-only files there (this backlog lives
  at repo root for that reason).
