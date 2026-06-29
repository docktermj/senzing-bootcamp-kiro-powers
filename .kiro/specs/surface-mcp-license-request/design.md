# Design Document

## Overview

This feature surfaces the Senzing MCP server's in-flow license-request capability inside
Module 2 Step 5 (Configure License), where today the no-license branch (Step 5c) offers
only external paths. The work is **guidance and documentation only** — no application or
runtime code changes — and it mirrors the already-implemented, tested Module 1 Step 6d
licensing branch so the two modules behave identically.

Three artifacts change:

1. `senzing-bootcamp/steering/module-02-sdk-setup.md` — Step 5c gains the in-flow MCP
   license-request path, a `get_capabilities` availability gate, the disabled-by-default
   enablement instructions, the single `submit_feedback` invocation, and MCP-sourced
   license facts.
2. `senzing-bootcamp/docs/modules/MODULE_2_SDK_SETUP.md` — the "Senzing License
   Requirements" section documents the in-flow option outside the conversational flow.
3. `senzing-bootcamp/tests/test_module2_license_request_option.py` (new) — a
   guidance-validation test mirroring `test_license_request_option.py`.

The canonical behavior already exists in Module 1 Step 6d; this design adapts it to the
Module 2 Step 5 structure (5b ask → 5c branch → 5d configure) rather than inventing new
behavior. All Senzing facts (validity period, record capacity) are retrieved from the MCP
server at runtime, never hardcoded.

## Architecture

The licensing decision flow in the Step 5c no-license branch, after the fix:

```text
Step 5b: "Do you have a .lic file or Base64 key?"
   ├── Yes (file / Base64)  ──> apply-an-existing-license path only (5c omits in-flow)   [R1.3, R7.5]
   └── No                    ──> Step 5c no-license branch
            │
            ▼
   get_capabilities (within this interaction; wait <=30s)                                 [R2.1, R7.1]
            │
   ┌────────┴───────────────────────────────────────────────┐
   │ submit_feedback reported available                       │ else: unavailable / error / timeout
   ▼                                                          ▼
 Present 3 paths (ordered):                            Present 2 paths:
  1. In-flow MCP request   [R1.1, R1.2]                  - external request
  2. external request                                    - apply existing
  3. apply existing                                     + message: in-session capability
            │                                              unavailable this session         [R2.3, R2.4, R2.5]
            ▼
   Bootcamper selects one path  [R1.4]; unrecognized => re-present unchanged  [R1.5]
            │
   -- In-flow chosen -------------------------------------------┐
   │ submit_feedback in disabledTools?                          │
   │   -> state it requires submit_feedback, disabled by default│ [R3.1]
   │   -> instruct: edit mcp.json, remove from disabledTools, save│ [R3.2]
   │   -> on "re-enabled": re-verify via get_capabilities (<=30s)│ [R3.3]
   │       fail/unavailable/timeout => present remaining 2 paths │ [R3.4, R4.5]
   │       declines => present remaining 2 paths                │ [R3.5]
   │   -> confirmed available: invoke submit_feedback ONCE       │ [R4.1, R4.6]
   │       (license_request category)                           │
   │       no-error => "check email for license + download link" │ [R4.2]
   │         on receipt => route to Step 5d configuration       │ [R4.3]
   │       error / no response in 30s => "did not complete",     │ [R4.4]
   │         present remaining 2 paths, no auto re-invoke        │
   └────────────────────────────────────────────────────────-─┘
```

License facts (validity period, record capacity) presented anywhere in this branch are
retrieved from an MCP server tool at request time; if unavailable, the figure is omitted
and the bootcamper is told it is unavailable from the MCP server — never a hardcoded
value (R6.1–R6.3).

## Components and Interfaces

### C1 — Module 2 Step 5c no-license branch (steering)

**File:** `senzing-bootcamp/steering/module-02-sdk-setup.md`, the `### 5c. Handle the
response` → "IF the bootcamper has no license" block.

Today this block confirms the 500-record evaluation license and lists only external
contacts plus a `search_docs` consult. The redesign restructures the no-license
sub-branch to mirror Module 1 Step 6d:

- **Availability gate (R2.1, R7.1):** before presenting paths, call `get_capabilities`
  within the same Step 5 interaction; wait for a response, error, or 30s.
- **Path presentation (R1.1, R1.2, R2.2):** when `submit_feedback` is reported available,
  present three ordered, individually selectable paths — in-flow MCP request first,
  external request second, apply-existing third — with the in-flow path identifying the
  MCP server, evaluation-license generation, email delivery, and download link.
- **Omit + notify (R2.3, R2.4, R2.5):** on unavailable / error / timeout / unrecognized
  `submit_feedback` value, present only external + apply-existing and tell the bootcamper
  the in-session capability is unavailable this session.
- **Selection handling (R1.4, R1.5):** act only on the selected path; on an unrecognized
  response, re-present the same options unchanged and do not advance past Step 5c.
- **Disabled-by-default + enablement (R3.1–R3.5):** state the option requires
  `submit_feedback` (disabled by default); instruct editing `senzing-bootcamp/mcp.json` to
  remove it from `disabledTools` and save; re-verify via `get_capabilities` after
  re-enablement; fall back to remaining paths on decline / failure.
- **Invocation (R4.1–R4.6):** invoke `submit_feedback` exactly once with the
  `license_request` category; on success instruct an email check and route to Step 5d on
  receipt; on error/timeout report non-completion and present remaining paths without
  auto-retry; never run a concurrent second invocation.
- **Already-licensed routing (R7.5):** if a license was already configured/applied earlier
  in the session, omit the in-flow option and route to apply-existing.

The existing external-contact text is retained as the "external request path"; the Step 5d
configuration steps are the "apply-an-existing-license path" target.

### C2 — Module 2 Step 5b cross-reference reuse

Step 5b's existing pointing question ("Do you have a Senzing license file (.lic) or a
Base64-encoded license key?") is the Module 2 analogue of Module 1 Step 6b. No new pointing
question is added in 5b; the in-flow option is introduced inside the 5c no-license branch,
matching Module 1's structure where 6d holds the branch. This preserves the module's
Sequential Execution Rule and existing STOP/pointing-question counts.

### C3 — Module 2 companion documentation

**File:** `senzing-bootcamp/docs/modules/MODULE_2_SDK_SETUP.md`, "Senzing License
Requirements" section.

That section already lists "Request one in-flow during the bootcamp — when available, the
agent can request an evaluation license without you leaving the workflow." The redesign
expands this into an explicit description that satisfies R5.1–R5.5: identifies it as an
in-flow MCP path available outside the Step 5 flow, states email delivery with a download
link, names the `submit_feedback` tool + `license_request` category, states the tool is
disabled by default (non-functional until enabled), and gives the enable instruction
(remove `submit_feedback` from `disabledTools` in `senzing-bootcamp/mcp.json`). Existing
external-channel and base64/`.lic` instructions are preserved.

### C4 — Guidance-validation test

**File:** `senzing-bootcamp/tests/test_module2_license_request_option.py` (new).
Mirrors `test_license_request_option.py`: stdlib + Hypothesis, class-based, region
extraction over the Step 5c no-license sub-branch and the Module 2 doc license section.
Asserts the behaviors above and the scope/security guards (no hardcoded MCP URL, no
hardcoded validity figures, unchanged pointing-question / STOP counts in Step 5).

## Data Models

No code data models. The conceptual entities (already established in Module 1):

| Concept | Representation |
|---|---|
| Availability gate result | `get_capabilities` reports `submit_feedback` available / unavailable / error / timeout |
| Licensing paths | In-flow MCP request, external request, apply-an-existing-license |
| Tool-enable state | `submit_feedback` present in / absent from `disabledTools` in `mcp.json` |
| License facts | validity period, record capacity — MCP-sourced at runtime, never hardcoded |

## Correctness Properties

### Property 1: In-flow option offered only when available

In the Step 5c no-license branch, the in-flow MCP request path is presented if and only if
a `get_capabilities` check within the same Step 5 interaction reports `submit_feedback`
available; on unavailable / error / 30s-timeout / unrecognized value it is omitted and the
bootcamper is notified.

**Validates: Requirements 1.1, 2.1, 2.2, 2.3, 2.4, 2.5, 7.1, 7.4**

### Property 2: Single invocation, no auto-retry

When the in-flow path is chosen and availability is confirmed, `submit_feedback` is invoked
exactly once with the `license_request` category; no concurrent or automatic second
invocation occurs, and failure/timeout falls back to the remaining paths.

**Validates: Requirements 4.1, 4.4, 4.5, 4.6**

### Property 3: Disabled-by-default is surfaced and re-verified

Whenever the in-flow path is presented while `submit_feedback` is in `disabledTools`, the
guidance states the dependency and disabled-by-default status, instructs enablement via
`mcp.json`, and re-verifies availability before invoking.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

### Property 4: License facts are MCP-sourced

Any validity-period or record-capacity figure shown comes from an MCP tool at runtime; when
unavailable it is omitted with an unavailable note, never replaced by a hardcoded value.

**Validates: Requirements 6.1, 6.2, 6.3**

### Property 5: Consistency with Module 1 and existing license routing

The Module 2 gate, invocation, and enable instructions match Module 1 Step 6d; when a
license is already present or configured, the in-flow option is omitted and the bootcamper
is routed to the apply-an-existing-license path.

**Validates: Requirements 1.3, 7.2, 7.3, 7.5**

## Error Handling

| Condition | Behavior | Requirement |
|---|---|---|
| `get_capabilities` unavailable / error / no response in 30s / unrecognized value | Omit in-flow path; present external + apply-existing; notify capability unavailable this session | R2.3, R2.4, R2.5, R7.4 |
| Bootcamper response doesn't match a presented path | Re-present same options unchanged; indicate not recognized; do not advance | R1.5 |
| `submit_feedback` still in `disabledTools` when in-flow chosen | State requirement + disabled-by-default; give enable instructions | R3.1, R3.2 |
| Re-verify after re-enable fails / unavailable / timeout | Do not invoke; present remaining paths | R3.4, R4.5 |
| Bootcamper declines to re-enable | Present remaining paths | R3.5 |
| `submit_feedback` invocation error or no response in 30s | Report non-completion; present remaining paths; no auto re-invoke | R4.4 |
| MCP tool returns no validity/capacity value or unreachable | Omit the figure; state it's unavailable from MCP; never substitute hardcoded value | R6.3 |

## Testing Strategy

Guidance-validation tests (not runtime execution), consistent with the Module 1
license-request lock-in pattern in `test_license_request_option.py`:

| Requirement | Verification |
|---|---|
| 1.1, 1.2, 1.4, 1.5 | Assert Step 5c presents three ordered selectable paths with the in-flow description (MCP server, evaluation license, email, download link); selection/unrecognized handling present |
| 1.3, 7.5 | Assert the has-license / already-configured routes omit the in-flow option |
| 2.1–2.5, 7.1, 7.4 | Assert the `get_capabilities` gate (30s), available vs unavailable/error/timeout branches, and the unavailable-session message |
| 3.1–3.5 | Assert disabled-by-default messaging, `mcp.json`/`disabledTools` enable instructions, re-verify, decline fallback |
| 4.1–4.6 | Assert single `license_request` invocation, success email guidance, route to Step 5d, failure no-retry fallback |
| 5.1–5.5 | Assert the Module 2 doc license section documents the in-flow option fully |
| 6.1–6.3 | Assert MCP-sourced facts and a negative check for hardcoded validity figures |
| 7.1–7.5 | Cross-checks that Module 2 wording matches the Module 1 gate / invocation / enable instruction |
| Security/scope | No hardcoded MCP URL in edited regions; Step 5 pointing-question and STOP marker counts unchanged |

Run via the CI pipeline (`validate_power.py`, `measure_steering.py --check`,
`validate_commonmark.py`, `sync_hook_registry.py --verify`, then pytest) to confirm no
steering token-budget or CommonMark regressions from the added guidance.
