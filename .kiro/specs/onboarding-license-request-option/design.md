# Design Document

## Overview

This is a small, documentation-only change to one steering file plus a focused test. The
onboarding overview in `senzing-bootcamp/steering/onboarding-phase1b-intro-language.md` (Step 5,
"Bootcamp Introduction") lists orientation points the agent covers before track selection. One
of those points is the licensing summary:

> - Built-in 500-record eval license; bring your own for more

The change rewrites this single bullet so it names three options — the built-in default, applying
an existing license, and requesting a temporary evaluation license in-flow through the Senzing
MCP server — and points to Module 1 as the place where the in-flow request is actually offered
and gated. No new flow logic is added to onboarding; the authoritative availability check and
branching stay in `module-01-phase1-discovery.md` (Steps 6a–6e), which this overview defers to.

This design reuses the framing already standardized by the `module1-license-request-option` and
`license-capacity-framing` specs, keeping the onboarding mention consistent with the rest of the
bootcamp.

## Architecture

The change touches two surfaces:

1. **`senzing-bootcamp/steering/onboarding-phase1b-intro-language.md`** — rewrite the licensing
   bullet in the Step 5 overview list.
2. **`senzing-bootcamp/tests/test_onboarding_license_request_option.py`** (new) — assert the
   licensing content references the in-flow MCP request path and contains no URLs.

No scripts, hooks, configs, or other steering files change. The `steering-index.yaml` token
budget for `onboarding-phase1b-intro-language.md` is re-checked via `measure_steering.py --check`;
the rewrite is roughly budget-neutral (a single bullet expands by one short clause), but if it
pushes the file over budget the index entry is updated to match.

## Components and Interfaces

### Licensing bullet rewrite

Current:

```markdown
- Built-in 500-record eval license; bring your own for more
```

Proposed (wording may be tuned for tone and budget, but must satisfy all acceptance criteria):

```markdown
- Licensing: you already have a built-in 500-record evaluation license — plenty for the
  bootcamp's demos. If you need more capacity you have options: apply an existing license, or
  ask the Senzing MCP server to issue a temporary evaluation license for you. Module 1 walks
  through these options and checks which are available in your session.
```

This wording:

- Frames the built-in license as the default the bootcamper already has (Req 1.3).
- Presents three options: built-in, apply existing, in-flow MCP request (Req 1.1).
- Names the in-flow path as "ask the Senzing MCP server to issue a temporary evaluation license"
  without restating the `get_capabilities` gating (Req 1.2).
- Points to Module 1 as the authoritative place for the offer and gating (Req 1.4).
- Uses the existing 500-record orientation figure but introduces no new validity/capacity figure
  for the requested license (Req 2.1).
- Refers to the Senzing MCP server by name only — no URL (Req 3.1).
- Makes no "always available / always succeeds" claim (Req 3.2).

## Correctness Properties

This is a documentation change; correctness is verified by content assertions rather than
algorithmic properties.

### Property 1: Three options present

The onboarding licensing content references all three licensing paths — the built-in evaluation
license, applying an existing license, and the in-flow MCP request — and a pointer to Module 1.

**Validates: Requirements 1.1, 1.2, 1.4**

### Property 2: No URLs introduced

The onboarding licensing content contains no MCP server URL and no external URL.

**Validates: Requirements 3.1**

## Data Models

Not applicable — this feature adds no data structures, schemas, or persisted state. The change is
a single edited Markdown bullet in a steering file plus a content test. (Licensing facts such as
record capacity and validity period are sourced at runtime from the Senzing MCP server by the
Module 1 flow and are not modeled here.)

## Error Handling

Not applicable — no executable logic is added. The only failure modes are CI checks
(`validate_commonmark.py`, `measure_steering.py --check`) which are addressed by keeping the
edit CommonMark-valid and within budget.

## Testing Strategy

A single new test module `senzing-bootcamp/tests/test_onboarding_license_request_option.py`
(stdlib + pytest, per `python-conventions.md`):

- **test_overview_mentions_in_flow_mcp_request** — read the steering file, locate the Step 5
  overview, and assert the licensing content mentions requesting an evaluation license through
  the Senzing MCP server (e.g., contains both an MCP-server reference and a "request"/"temporary
  evaluation license" phrase). Validates Property 1.
- **test_overview_mentions_apply_existing_license** — assert the licensing content still presents
  the apply/bring-your-own path. Validates Property 1.
- **test_no_urls_in_licensing_content** — assert the licensing region contains no MCP URL and no
  external URL. Validates Property 2.

CI integration: the existing `validate_commonmark.py` and `measure_steering.py --check` steps in
`.github/workflows/validate-power.yml` cover CommonMark validity and token budget; no new CI step
is required. Tests run under the existing `pytest senzing-bootcamp/tests/` invocation.
