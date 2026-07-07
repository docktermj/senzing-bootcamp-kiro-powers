# Design Document

## Overview

This feature advertises the in-flow temporary-license request path **earlier** in Module 2 —
inside the upfront Step 5a "Explain the built-in evaluation license" explanation — so that
bootcampers with datasets larger than the built-in evaluation license's record limit learn the
path exists *before* they reach the Step 5c no-license branch, where it is the only place it
currently appears.

Today, Step 5a (`senzing-bootcamp/steering/module-02-sdk-setup.md`, subsection
`### 5a. Explain the built-in evaluation license`) tells the bootcamper about the built-in
evaluation license and that larger datasets need a custom `licenses/g2.lic`. Its only acquisition
direction is to "consult the Senzing MCP server" via `search_docs`. It never states that the
bootcamp itself can initiate an in-flow temporary-license request through the MCP server's
`submit_feedback` tool with the `license_request` category. This feature adds that mention,
alongside the existing apply-an-existing-license and Senzing-support paths, carrying an
availability caveat because `submit_feedback` ships disabled by default.

The work is **guidance and documentation only** — no application or runtime code changes. It is
deliberately narrow in scope:

- It changes only the **upfront explanatory content of Step 5a** and the agent's **summarized
  presentation** of that explanation.
- It does **not** change the Step 5c branch's interactive option-selection, capability
  verification, invocation, or enablement behavior — those are owned by the existing
  `surface-mcp-license-request` spec. This feature instead keeps Step 5a *consistent* with that
  already-implemented Step 5c behavior.

Two artifacts change:

1. `senzing-bootcamp/steering/module-02-sdk-setup.md` — the `### 5a.` subsection gains the in-flow
   MCP license-request mention, names the three acquisition paths, states the
   `submit_feedback`/`license_request` mechanism, carries the availability caveat on that path
   only, keeps the Step 5a mention informational (no selection prompt), directs selection/execution
   to Step 5c, and continues to source license figures from MCP tools at runtime.
2. `senzing-bootcamp/tests/test_module2_license_acquisition_info.py` (new) — a guidance-validation
   test (stdlib + region extraction) asserting the Step 5a content above and the scope/security
   guards (informational-only, no new pointing question, no hardcoded MCP URL, no hardcoded license
   figures, consistency with the Step 5c branch).

All Senzing-specific license facts (record capacity, validity period) presented in the explanation
are retrieved from MCP tools at runtime, never hardcoded from training data — consistent with the
bootcamp's core MCP-first constraint (`tech.md`, `security.md`).

## Architecture

The change is confined to one steering subsection. The Step 5a explanation flow, after the change:

```text
Step 5a (upfront, informational — no pointing question, no STOP)
  │
  ├── Explain built-in evaluation license (existing text retained)
  │      └── Record_Limit / validity period figures: retrieved from MCP tool at runtime   [R4.1, R4.2]
  │             └── tool returns no value OR MCP unreachable / >30s  → omit figure,
  │                  state value unavailable from MCP server (never hardcode)              [R4.3, R4.4]
  │
  └── "If you need more than the built-in limit" — name the three acquisition paths:       [R1.2, R3.5]
         1. In-flow MCP license request  ── via submit_feedback + license_request category [R1.1, R1.3, R3.1]
              └── Availability_Caveat: depends on submit_feedback being enabled AND
                   reported available; disabled by default; may be unavailable this
                   session; not guaranteed                                                 [R2.1, R2.2, R3.2]
         2. Apply an existing license (.lic / Base64 → licenses/g2.lic)   — no caveat       [R2.4]
         3. Request via Senzing support (external channel)                — no caveat       [R2.4]
         │
         └── Mention is informational only; do NOT prompt to choose/confirm/initiate
              at Step 5a; direct selection + execution to the Step 5c branch                [R1.4, R3.3, R3.4]

Summarized_Explanation (agent's spoken/condensed delivery at Step 5a)
  └── States: when more than the Record_Limit is needed, the bootcamp can request a
       temporary evaluation license in-flow via the MCP server, in addition to
       apply-existing and support paths                                                     [R1.5]
       + caveat: in-flow path depends on submit_feedback being available and may be
         unavailable this session                                                          [R2.3]
```

Key architectural decisions:

- **Placement, not behavior.** The in-flow path already works at Step 5c. This feature only
  *announces* it upstream at Step 5a. Step 5a remains a one-way informational explanation — it adds
  no STOP, no pointing question (`👉`), and no option-selection prompt. This preserves the module's
  Sequential Execution Rule and the existing pointing-question/STOP counts.
- **Single source of mechanism.** Step 5a describes the in-flow path using the *same* mechanism and
  availability wording that Step 5c already uses (`submit_feedback` + `license_request`; depends on
  the tool being available; disabled by default). Step 5a does not introduce any mechanism or path
  absent from Step 5c, which prevents the two locations from drifting.
- **Caveat scoping.** Only the in-flow path carries the availability caveat. The apply-existing and
  support paths are presented without it, since their availability does not depend on
  `submit_feedback`.
- **MCP-sourced facts.** Any record-capacity or validity figure in the explanation is retrieved from
  an MCP tool at presentation time; on absence or unreachability (30s), the figure is omitted with
  an "unavailable from the MCP server" note rather than a remembered/hardcoded value.

## Components and Interfaces

### C1 — Module 2 Step 5a explanation (steering)

**File:** `senzing-bootcamp/steering/module-02-sdk-setup.md`, subsection
`### 5a. Explain the built-in evaluation license`.

This is the primary change. The existing built-in-evaluation-license explanation is retained. The
"if a larger or temporary evaluation license is needed" guidance is expanded from a single
`search_docs` consult into an explicit, informational naming of three acquisition paths:

- **In-flow MCP license request (R1.1, R1.3, R3.1):** state that, when more than the built-in
  Record_Limit is needed, the bootcamp can request a temporary evaluation license in-flow through
  the MCP server, initiated by the bootcamp invoking the `submit_feedback` MCP tool with the
  `license_request` category — described with the same mechanism Step 5c uses, and no mechanism
  absent from Step 5c.
- **Availability caveat on the in-flow path only (R2.1, R2.2, R2.4, R3.2):** immediately qualify the
  in-flow path with the Availability_Caveat — it depends on `submit_feedback` being both enabled and
  reported available by the MCP server; `submit_feedback` is disabled by default; the path may
  therefore be unavailable in a given session and is not guaranteed. This caveat is attached only to
  the in-flow path; the apply-existing and support paths are presented without it. The dependency
  wording matches Step 5c (depends on `submit_feedback` availability; disabled by default) and does
  not contradict it.
- **Apply-an-existing-license path (R1.2, R3.5):** name the path of applying a license the
  bootcamper already holds (`.lic` file or Base64 key placed at `licenses/g2.lic`).
- **Support-request path (R1.2, R3.5):** name the path of requesting an evaluation license through
  Senzing support's external channel.
- **Informational only, no selection at 5a (R1.4, R3.3):** present all three as information; do not
  open an option-selection, confirmation, or execution prompt at Step 5a; add no `👉` pointing
  question and no STOP marker in 5a.
- **Direct selection/execution to Step 5c (R3.4):** state that choosing and carrying out an
  acquisition path happens at Step 5c (the no-license branch), not here.
- **MCP-sourced figures (R4.1–R4.4):** keep the existing instruction that any Record_Limit or
  validity-period figure is retrieved from an MCP tool during the current session and presented
  exactly as returned; on a missing value or an MCP server that is unreachable (no response within
  30 seconds), omit the figure and tell the bootcamper the current value is unavailable from the MCP
  server — never substitute a hardcoded or remembered figure.

The three Step 5a paths are the same three the Step 5c branch offers (in-flow MCP request, support
request, apply-existing); no additional path is introduced (R3.5).

### C2 — Summarized explanation (agent presentation contract)

**Where:** the agent's spoken/condensed delivery of the Step 5a explanation (not a separate file —
a behavioral instruction embedded in the 5a subsection so the agent's summary stays faithful).

The steering text instructs the agent that, when it summarizes Step 5a, the summary must:

- State that, when more than the Record_Limit is needed, the bootcamp can help request a temporary
  evaluation license in-flow through the MCP server, in addition to the apply-existing and support
  paths (R1.5).
- Carry the caveat that the in-flow path depends on `submit_feedback` being available and may be
  unavailable in a given session (R2.3).

This guarantees the condensed presentation does not drop the in-flow option or its caveat.

### C3 — Step 5c cross-reference (consistency anchor)

**File:** `senzing-bootcamp/steering/module-02-sdk-setup.md`, the existing
`### 5c. Handle the response` no-license branch (owned by `surface-mcp-license-request`).

No change is made to Step 5c. It is the source of truth for the mechanism, the availability
dependency, and the three-path set that Step 5a must mirror. The Step 5a wording is written to be
consistent with this branch and to direct selection/execution to it.

### C4 — Guidance-validation test

**File:** `senzing-bootcamp/tests/test_module2_license_acquisition_info.py` (new).

Mirrors `test_license_request_option.py`: stdlib only, class-based, region extraction over the
Step 5a subsection. It asserts the Step 5a content (three named paths, in-flow mechanism, caveat on
the in-flow path only, informational-only framing, direction to Step 5c, MCP-sourced figures) and
the scope/security guards (no new `👉`/STOP in 5a, no hardcoded MCP URL, no hardcoded license
figures, mechanism/path-set consistent with the Step 5c branch).

## Data Models

No code data models — this feature edits steering Markdown. The conceptual entities (from the
requirements glossary):

| Concept | Representation |
|---|---|
| License_Explanation | The Step 5a `### 5a.` subsection text in `module-02-sdk-setup.md` |
| Summarized_Explanation | The agent's spoken/condensed delivery of Step 5a, governed by an embedded instruction |
| Acquisition paths | In-flow MCP request, Apply-an-existing-license, Support request |
| Availability_Caveat | Depends on `submit_feedback` enabled + reported available; disabled by default; not guaranteed |
| License facts | Record_Limit, validity period — MCP-sourced at runtime, never hardcoded |
| Step_5c_Branch | The existing `### 5c.` no-license branch (consistency source of truth) |

## Testing Approach Rationale (Why No Correctness Properties)

Property-based testing is **not applicable** to this feature, so the Correctness Properties section
is intentionally omitted in favor of guidance-validation (example-based) tests.

Reasoning: every acceptance criterion is about the **presence, wording, and scoping of static
steering content** (R1, R2, R3) or about an **agent runtime behavior that consults an external MCP
tool** (R4). There is no pure function with a varying input space over which a universal "for all
inputs" property would hold — the License_Explanation is a fixed document, and the MCP-sourcing
behavior is an external-service interaction whose result does not vary meaningfully with generated
input. Per the workflow's PBT-applicability guidance (documentation/content and external-dependency
behavior are not PBT candidates), these criteria are best verified with example-based
guidance-validation tests over the steering file plus, for R4, the existing Step 5c MCP-sourcing
guarantee that this feature reuses unchanged. See the Testing Strategy below.

## Error Handling

| Condition | Behavior | Requirement |
|---|---|---|
| MCP tool returns no Record_Limit / validity value, or MCP server is unreachable | Omit the specific figure; tell the bootcamper the current value is unavailable from the MCP server; never substitute a hardcoded/remembered figure | R4.4 |
| MCP tool does not respond within 30 seconds | Treat the MCP server as unreachable and apply the omit-and-notify behavior above | R4.3 |
| `submit_feedback` may be disabled/unavailable in the session | Step 5a presents the in-flow path with the Availability_Caveat (disabled by default; may be unavailable; not guaranteed) rather than promising it; actual availability handling occurs at Step 5c | R2.1, R2.2, R2.3 |
| Bootcamper tries to act on a path at Step 5a | Step 5a is informational only; it does not prompt for or accept a selection — selection/execution is directed to Step 5c | R1.4, R3.3, R3.4 |

## Testing Strategy

Verification is **guidance-validation (example-based) testing**, consistent with
`test_license_request_option.py` and the `surface-mcp-license-request` spec. No property-based tests
are written for this feature (see Correctness Properties above for why). The runtime MCP-sourcing
behavior (R4) is already implemented and tested by the Step 5c / `surface-mcp-license-request` work;
this feature reuses it unchanged at Step 5a, so the new test asserts the *guidance* requires
MCP-sourced figures rather than re-testing live MCP calls.

**Test file:** `senzing-bootcamp/tests/test_module2_license_acquisition_info.py` — stdlib only,
class-based, region extraction over the Step 5a subsection of `module-02-sdk-setup.md`.

| Requirement | Verification |
|---|---|
| 1.1, 1.3 | Step 5a region presents the in-flow license-request path and names the `submit_feedback` tool + `license_request` category |
| 1.2, 3.5 | Step 5a region names all three paths (in-flow, apply-existing, support) and no path absent from the Step 5c branch |
| 1.4, 3.3 | Step 5a region contains no `👉` pointing question and no STOP marker; the module-wide pointing-question / STOP counts are unchanged |
| 1.5, 2.3 | Step 5a region contains the summarized-explanation instruction covering the in-flow path and its caveat |
| 2.1, 2.2 | Step 5a region states the Availability_Caveat (depends on `submit_feedback` enabled + available; disabled by default; may be unavailable; not guaranteed) on the in-flow path |
| 2.4 | Assert the caveat phrasing is attached only to the in-flow path; the apply-existing and support paths appear without it |
| 3.1, 3.2 | Step 5a mechanism + availability wording match the Step 5c branch (`submit_feedback`/`license_request`; disabled by default); a cross-check against the 5c region confirms no contradiction |
| 3.4 | Step 5a region directs selection/execution to Step 5c |
| 4.1, 4.2, 4.3, 4.4 | Step 5a region instructs MCP-sourced figures with the 30s-unreachable omit-and-notify behavior; negative check for hardcoded record/validity figures |
| Security / scope | No hardcoded MCP server URL in the edited region; figures not hardcoded |

**Hypothesis profiles:** if any incidental property test is added it must follow the repo profile
convention (no inline `@settings(max_examples=...)` restating the baseline; baseline supplied by the
active profile). For this feature, the assertions are deterministic content checks and do not need
Hypothesis.

**CI:** run via the existing pipeline (`validate_power.py`, `measure_steering.py --check`,
`validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest) to confirm the added Step 5a
guidance introduces no steering token-budget or CommonMark regressions.
