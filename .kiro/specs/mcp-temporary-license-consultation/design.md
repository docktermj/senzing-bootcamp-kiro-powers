# MCP Temporary License Consultation Bugfix Design

## Overview

Rule 6 of the Senzing Bootcamp Power states: *"If the current Senzing license is
insufficient, consult the Senzing MCP server for a temporary Senzing license."* The
implementation violates this rule. When a bootcamper's data exceeds the built-in
500-record evaluation limit (or a `SENZ9000` capacity error occurs), the steering files
only *mention in prose* that the MCP server "can guide you through requesting a larger
evaluation license." No steering path instructs the agent to actually **consult an MCP
tool**. This also breaches the **MCP-First Invariant** in `agent-instructions.md`, which
requires every Senzing fact — including licensing guidance — to come from an MCP tool
call rather than hardcoded prose.

The fix is a **steering-content change** (no Python/runtime code is involved). It edits
the three license-insufficient paths so each contains a defined, enforced MCP
consultation step that names a file-confirmed tool (`search_docs`) with a concrete query
for temporary/larger evaluation license guidance:

- `module-01-business-problem.md` — **Step 6d** ("does not have license" branch,
  triggered when total records exceed 500).
- `module-02-sdk-setup.md` — **Step 5a** (built-in evaluation license explanation) and
  **Step 5c** "no license" branch.

The fix is deliberately minimal. It preserves every sufficient-license path (records
≤ 500), the ⛔ mandatory gate on Module 2 Step 5, the single 👉 question per sub-step,
the 🛑 STOP markers, checkpoints, the existing email contacts
(`support@senzing.com` / `sales@senzing.com`), and the `licenses/README.md` reference.
It introduces no MCP server URL outside `mcp.json` and no new external URLs.

The tool name is confirmed against the repository, not invented. `mcp-tool-decision-tree.md`
("Troubleshooting" and "Reference and Reporting" branches) and `agent-instructions.md`
("MCP Rules": *"Docs → `search_docs`"*) both route documentation/guidance lookups to
`search_docs`. No licensing-specific MCP tool exists in those references, so `search_docs`
with a free-text `query` is the documented path.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a license-insufficient
  situation (total records > 500 OR a `SENZ9000` capacity error) with no sufficient custom
  license present, where the steering path offers MCP licensing help only as passive prose
  and never instructs the agent to call an MCP tool.
- **Property (P)**: The desired behavior — when the license is insufficient, the steering
  path defines an enforced MCP consultation step (a named `search_docs` call with a
  concrete license-guidance query), satisfying Rule 6 and the MCP-First Invariant.
- **Preservation**: Existing behavior that must remain unchanged — sufficient-license
  paths (records ≤ 500), the ⛔ mandatory gate, the single 👉 question per sub-step, 🛑 STOP
  markers, checkpoints, email contacts, the `licenses/README.md` reference, license
  mechanics (Base64 decode, `PIPELINE.LICENSEFILE`, preference recording), and all
  non-license content.
- **search_docs**: The Senzing MCP documentation-search tool confirmed in
  `mcp-tool-decision-tree.md` and `mcp-usage-reference.md`. Signature (per decision tree):
  `search_docs(query=..., category=<optional>)`. It is the documented tool for retrieving
  documentation and guidance, including licensing guidance.
- **MCP-First Invariant**: The rule in `agent-instructions.md` (absolute precedence, equal
  to a ⛔ gate) requiring all Senzing facts to be retrieved through an MCP tool call rather
  than emitted as prose from training data.
- **License-insufficient path**: A steering sub-step reached when the built-in 500-record
  evaluation license is (or will be) exceeded — Module 1 Step 6d, Module 2 Step 5a, and the
  Module 2 Step 5c "no license" branch.
- **Steering_File**: A markdown file with YAML frontmatter under
  `senzing-bootcamp/steering/` that guides agent behavior.

## Bug Details

### Bug Condition

The bug manifests when a license-insufficient situation is reached and the steering path
that handles it offers MCP licensing help only as passive prose. The path is either
silent about the MCP server entirely (Module 1 Step 6d), or mentions the MCP server in
awareness language ("you can request…", "the MCP server can guide you…") without naming a
tool the agent must call. In all three cases no enforced MCP tool consultation exists, so
the agent never consults the MCP server for a temporary/larger license — violating Rule 6
and the MCP-First Invariant for licensing facts.

**Formal Specification:**

```
FUNCTION isBugCondition(X)
  INPUT: X of type LicenseSituation
         { totalRecordCount: int, hasSufficientLicense: bool, errorCode: string|null }
  OUTPUT: boolean

  // The license is "insufficient" when capacity is (or will be) exceeded
  // or a capacity error has occurred, AND no sufficient custom license is present.
  RETURN (X.totalRecordCount > 500 OR X.errorCode = "SENZ9000")
         AND NOT X.hasSufficientLicense
END FUNCTION
```

The corresponding **defect predicate** over the steering content for a path `S` handling
a bug-condition situation:

```
FUNCTION pathIsDefective(S)
  RETURN NOT mentionsMcpConsultationStep(S)   // no named MCP tool call present
      OR isProseOnlyMention(S)                // only "can request via MCP server" awareness prose
END FUNCTION
```

### Examples

- **Module 1 Step 6d** — bootcamper has 10,000 records and no license
  (`totalRecordCount: 10000, hasSufficientLicense: false, errorCode: null`).
  *Expected:* the path instructs the agent to consult `search_docs` for temporary/larger
  license guidance, in addition to the existing `support@senzing.com` contact.
  *Actual:* the path directs the bootcamper to email `support@senzing.com` only and
  contains **no** MCP consultation step at all. → Rule 6 violated.

- **Module 2 Step 5a** — agent presents the built-in evaluation license explanation.
  *Expected:* a defined MCP consultation step (a named `search_docs` call) the agent
  performs to obtain larger/temporary license guidance.
  *Actual:* the line *"You can also request a larger evaluation license directly through
  the Senzing MCP server — it can guide you through the process…"* is passive prose with
  no tool call. → MCP-First Invariant breached for a licensing fact.

- **Module 2 Step 5c "no license" branch** — bootcamper indicates no license.
  *Expected:* an enforced MCP consultation step alongside the existing
  `support@senzing.com` / `sales@senzing.com` contacts.
  *Actual:* the line *"Alternatively, the Senzing MCP server can guide you through
  requesting a larger evaluation license interactively. See `licenses/README.md` for
  details."* is awareness prose with no tool call. → Rule 6 violated.

- **Edge case (`SENZ9000` at record 501)** — capacity error during load
  (`errorCode: "SENZ9000", hasSufficientLicense: false`).
  *Expected:* license-insufficient handling routes the agent to a `search_docs`
  consultation for license guidance (satisfying the MCP-First Invariant).
  *Actual:* license guidance is hardcoded prose with no MCP tool call.

- **Non-bug example (sufficient license)** — bootcamper has 300 records
  (`totalRecordCount: 300, hasSufficientLicense: false, errorCode: null`).
  `isBugCondition` is **false**: Module 1 Step 6a skips sub-steps 6b–6e and proceeds to
  Step 7; no MCP license consultation is triggered. This path must remain unchanged.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- **Sufficient-license path (Module 1 Step 6a).** When total records are ≤ 500, the agent
  SHALL continue to skip sub-steps 6b–6e and proceed directly to Step 7, with no MCP
  license consultation triggered.
- **Custom-license handling (Module 2 Step 5c "has license" branches).** Base64 decode to
  `licenses/g2.lic`, `.lic` file copy, the "NEVER ask the user to paste a license key into
  chat" warning, and `PIPELINE.LICENSEFILE` configuration (Step 5d) remain exactly as
  before.
- **Module 1 Step 6c "already has license" branch.** Base64 decode + `LICENSEFILE` +
  `license: custom` preference recording remain unchanged.
- **⛔ Mandatory gate (Module 2 Step 5).** The "⛔ MANDATORY GATE — Never skip this step,
  even if the SDK is already installed" marker, the Step 1 "Required Stops" callout listing
  Step 4 and Step 5, and the license-check priority order remain unchanged.
- **One 👉 question + one 🛑/STOP per sub-step boundary.** Module 2 Step 5 keeps **exactly
  one** 👉 question (the 5b license question) and **exactly one** STOP instruction. Module 1
  sub-steps 6b and 6d keep their existing 👉 question and 🛑 STOP markers; no new 👉 or 🛑 is
  added.
- **Checkpoints.** Every `**Checkpoint:** Write step N…` instruction is preserved.
- **Email contacts and README reference.** `support@senzing.com`, `sales@senzing.com`, and
  `licenses/README.md` remain present everywhere they currently appear; the fix *adds* an
  MCP step alongside them rather than replacing them.
- **Preference recording.** `license: evaluation`, `license: custom`, and
  `license_guidance_deferred: true` recording instructions remain unchanged.
- **YAML frontmatter.** Both files keep `inclusion: manual` frontmatter.

**Scope:**

All inputs that do NOT satisfy `isBugCondition` should be completely unaffected. This
includes:

- Sufficient-license situations (total records ≤ 500, or a sufficient custom license present).
- All non-license Module 2 content (SDK install, EULA, verification, database, engine
  configuration) — Steps 1–4 and 6–9.
- All non-license Module 1 content (discovery, inference, gap-filling, integration,
  deployment).
- Security invariants — no MCP URL outside `mcp.json`, no new external URLs in steering.

**Note:** The actual expected correct behavior for bug-condition inputs is defined in the
Correctness Properties section (Property 1). This section focuses on what must NOT change.

## Hypothesized Root Cause

Based on the bug analysis and the prior `licensing-guidance` spec, the most likely causes
are:

1. **Intentional prose-only mention (primary cause).** The prior `licensing-guidance` spec
   added the MCP mention to Module 2 Step 5a/5c as awareness prose. Its acceptance
   criterion 4.2 explicitly avoided hardcoding MCP tool names ("reference the MCP server
   capability without hardcoding specific MCP tool names or URLs"). This produced a
   passive mention that satisfies "the bootcamper is aware" but never instructs the agent
   to call a tool — a known gap between Rule 6 and the implementation.

2. **No MCP step in Module 1 Step 6d at all.** The Module 1 "does not have license" branch
   was authored around email-based acquisition (`support@senzing.com`) and was never
   updated to reference the MCP server, so the most common high-volume entry point
   (records > 500 during discovery) has zero MCP consultation.

3. **MCP-First Invariant not applied to licensing facts.** The invariant's pre-response
   checklist enumerates SDK methods, attributes, config options, and error codes, but
   licensing guidance was treated as generic prose rather than a Senzing fact, so the
   invariant was never enforced on these paths.

4. **Test coverage locked in the prose-only behavior.** `test_licensing_guidance.py`
   asserts only that the MCP server is *mentioned* (`"mcp" in content`), so prose-only
   text passes. There is no test asserting an *enforced, named-tool* consultation, so the
   gap went undetected.

## Correctness Properties

Property 1: Bug Condition — Enforced MCP Consultation on Insufficient License

_For any_ license situation `X` where the bug condition holds (`isBugCondition(X)` returns
true — total records > 500 OR `SENZ9000`, and no sufficient license), the fixed steering
path that handles `X` (Module 1 Step 6d, Module 2 Step 5a, or Module 2 Step 5c "no
license") SHALL contain an enforced MCP consultation step that (a) names a file-confirmed
MCP tool (`search_docs`), (b) issues a concrete query for temporary/larger evaluation
license guidance, and (c) is expressed as an imperative directive rather than a prose-only
"can request via the MCP server" mention — while introducing no MCP server URL outside
`mcp.json`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation — Sufficient-License Paths and Structural Invariants Unchanged

_For any_ license situation `X` where the bug condition does NOT hold
(`isBugCondition(X)` returns false — total records ≤ 500 or a sufficient license present),
and for all structural invariants the existing tests enforce, the fixed steering files
SHALL produce the same result as the original files — preserving the Module 1 Step 6a
skip-to-Step-7 behavior, the Module 2 ⛔ mandatory gate, exactly one 👉 question and one
STOP in Module 2 Step 5, the 🛑 STOP markers in Module 1 sub-steps, all checkpoints, the
existing email contacts and `licenses/README.md` reference, the license mechanics
(Base64 decode, `PIPELINE.LICENSEFILE`, preference recording), the `inclusion: manual`
frontmatter, and all non-license content (Module 2 Steps 1–4 and 6–9).

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6**

## Fix Implementation

### Changes Required

Assuming the root-cause analysis is correct, the fix edits the three license-insufficient
paths to add an enforced `search_docs` consultation step. All edits are additive within
the license-insufficient branches; no sufficient-license content is touched.

**File 1**: `senzing-bootcamp/steering/module-01-business-problem.md`

**Section**: Step 6d — "Does not have license" branch.

**Specific Changes**:

1. **Add an enforced MCP consultation step** to the 6d branch, placed before or alongside
   the existing email-acquisition guidance, phrased as an imperative directive the agent
   performs (not a 👉 question, to avoid adding a second pointing question to the sub-step).
   Example phrasing:
   *"**Consult the Senzing MCP server first.** Because the total record count exceeds the
   500-record evaluation limit, the current license is insufficient. Call
   `search_docs(query='temporary or larger evaluation license for more than 500 records')`
   to retrieve current Senzing guidance on obtaining a temporary/larger evaluation license,
   and present that guidance to the bootcamper. Then continue with the email path below."*
2. **Preserve** the existing email guidance block (`support@senzing.com`, what to provide,
   turnaround expectations, how to configure once received).
3. **Preserve** the existing 👉 deferral question, its 🛑 STOP marker, the branch logic
   (wait / defer → 6e / received → 6c), and the `**Checkpoint:** Write step 6d` instruction.
4. **Do not add** a new 👉 question or a new 🛑 STOP marker to 6d.
5. **Do not introduce** any URL; reference the MCP server capability via the tool name only.

**File 2**: `senzing-bootcamp/steering/module-02-sdk-setup.md`

**Section**: Step 5a — "Explain the built-in evaluation license".

**Specific Changes**:

1. **Replace the prose-only line** *"You can also request a larger evaluation license
   directly through the Senzing MCP server — it can guide you through the process without
   waiting for email responses."* with an enforced MCP consultation directive, positioned
   **after** the existing 500-record / `SENZ9000` explanation (preserving the ordering that
   `test_licensing_guidance.py` checks). Example phrasing:
   *"If a larger or temporary evaluation license is needed, **consult the Senzing MCP
   server**: call `search_docs(query='request a larger or temporary evaluation license')`
   and present the returned guidance — this avoids waiting for email responses."*
2. **Preserve** the "500 records", "SENZ9000", and "`licenses/g2.lic`" content in 5a.

**Section**: Step 5c — "Handle the response", "IF the bootcamper has no license" branch.

**Specific Changes**:

3. **Replace the prose-only line** *"Alternatively, the Senzing MCP server can guide you
   through requesting a larger evaluation license interactively."* with an enforced MCP
   consultation directive that names the tool, kept **alongside** the existing
   `support@senzing.com` / `sales@senzing.com` contacts and the `licenses/README.md`
   reference. Example phrasing:
   *"If you need a larger evaluation license for larger datasets later, **consult the
   Senzing MCP server** — call `search_docs(query='larger evaluation license for datasets
   over 500 records')` and present the guidance. You can also contact `support@senzing.com`
   (typically 1–2 business days, 30–90 day validity). For production licenses, contact
   `sales@senzing.com`. See `licenses/README.md` for details."*
4. **Preserve** the "no problem — built-in 500-record evaluation license is active"
   confirmation, the email contacts, the `licenses/README.md` reference, and the
   `license: evaluation` preference recording.
5. **Maintain exactly one 👉 question (5b) and exactly one STOP instruction in Step 5.** The
   MCP consultation must be an imperative directive, never a 👉 question or a STOP — this is
   required by `test_licensing_guidance.py::TestLicensingGuidanceScope`.
6. **Do not hardcode** any MCP server URL inside Step 5.

### Tool-Name Confirmation (Requirement 2.5)

`search_docs` is confirmed to exist in the repository references:

- `mcp-tool-decision-tree.md` — "Troubleshooting → Searching for solutions or
  documentation → `search_docs`" and "Reference and Reporting → Searching Senzing
  documentation → `search_docs`", with the call-pattern example
  `{ "tool": "search_docs", "query": "batch loading best practices" }`.
- `agent-instructions.md` — "MCP Rules": *"Docs → `search_docs`"*.
- `mcp-usage-reference.md` — "Third-party software: consult Senzing MCP (`search_docs`)…".

No licensing-specific MCP tool exists in those references, so `search_docs` with a
free-text `query` is the correct, documented consultation path for licensing guidance.

### Security and Convention Compliance

- No MCP server URL is added outside `mcp.json`; steering references the capability by tool
  name only (`security.md`: "Hardcoded MCP URLs outside `mcp.json` — HIGH").
- No external URLs are introduced into steering (`security.md`: "Steering file referencing
  external URLs — MEDIUM").
- Both files retain `inclusion: manual` frontmatter; edits are markdown-only, matching
  `structure.md` / `tech.md` steering conventions.

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that
demonstrate the bug on the **unfixed** steering files, then verify the fix works correctly
and preserves existing behavior. Because the "code under test" is steering markdown, tests
parse the steering files and assert content properties — the established pattern in this
repo (`test_licensing_guidance.py`, `test_missing_pointer_marker_exploration.py`,
`test_mcp_first_enforcement_properties.py`).

New test files (following the `test_*_exploration.py` / `test_*_preservation.py` naming
convention used by existing bugfix specs) will live in `senzing-bootcamp/tests/`:

- `test_mcp_temporary_license_consultation_exploration.py` — Fix-checking (Property 1).
- `test_mcp_temporary_license_consultation_preservation.py` — Preservation-checking
  (Property 2).

All tests use pytest + Hypothesis, stdlib + Hypothesis only, with class-based organization,
`st_`-prefixed strategies, `@settings(max_examples=20)`, and type hints (`X | None`,
`list[str]`), per `python-conventions.md`.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix.
Confirm or refute the root-cause analysis. If refuted, re-hypothesize.

**Test Plan**: Parse the three license-insufficient sections from the **unfixed** steering
files and assert each contains an enforced, named-tool MCP consultation step. Run on
unfixed code to observe failures (the prose-only / missing-step gap).

Helper functions (mirroring `test_licensing_guidance.py`):

- `_extract_5a(content)` / `_extract_5c_no_license(content)` — slice Module 2 Step 5
  sub-sections by `### 5a` / `### 5c` / `### 5d` boundaries.
- `_extract_6d(content)` — slice Module 1 Step 6d by the `**6d.`…`**6e.` boundaries.
- `_has_enforced_mcp_step(section)` — true if the section contains the tool name
  `search_docs` **and** an imperative directive (e.g., `call`/`consult`) — not merely a
  generic "MCP server" mention.
- `_tool_name_is_confirmed(name)` — true if `name` appears in the tool set documented in
  `mcp-tool-decision-tree.md` (parsed from that file, not hardcoded), proving the tool is
  valid.
- `_is_prose_only(section)` — true if the section mentions the MCP server but names no MCP
  tool (the unfixed condition).

**Test Cases**:

1. **Module 1 Step 6d enforced MCP step** — assert 6d contains a `search_docs` consultation
   directive (will fail on unfixed code — 6d has no MCP mention at all).
2. **Module 2 Step 5a enforced MCP step** — assert 5a names `search_docs` in an imperative
   directive (will fail on unfixed code — prose-only "you can also request… through the
   Senzing MCP server").
3. **Module 2 Step 5c "no license" enforced MCP step** — assert the no-license branch names
   `search_docs` in an imperative directive (will fail on unfixed code — prose-only "the
   Senzing MCP server can guide you…").
4. **Tool name confirmed** — assert the referenced tool name resolves against the
   `mcp-tool-decision-tree.md` tool set (guards against an invented tool name).
5. **Not prose-only** — assert `_is_prose_only` is false for each license-insufficient
   section after the fix (will fail on unfixed code).
6. **Edge case — SENZ9000 routing** — assert the license-insufficient handling reachable on
   a `SENZ9000` capacity error routes to a `search_docs` consultation (will fail on unfixed
   code).

**Expected Counterexamples**:

- Module 1 Step 6d: no MCP tool reference present → enforced-step assertion fails.
- Module 2 Step 5a and 5c: MCP server mentioned but no `search_docs` (or any tool) named →
  `_is_prose_only` is true, enforced-step assertion fails.
- Possible causes confirmed: prose-only mention (5a/5c), missing step entirely (6d),
  MCP-First Invariant not applied to licensing facts.

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed steering
paths define the enforced MCP consultation step (Property 1).

**Pseudocode:**

```
FOR ALL X WHERE isBugCondition(X) DO
  path := steeringPathFor(X)            // 6d, 5a, or 5c "no license"
  ASSERT mentionsMcpConsultationStep(path)        // names search_docs in a directive
     AND mcpToolNameConfirmedInReference(path)     // search_docs in decision-tree tool set
     AND NOT isProseOnlyMention(path)              // not passive "can request via MCP" prose
     AND noMcpUrlOutsideMcpJson(path)              // no MCP server URL in the section
END FOR
```

This is realized as a Hypothesis property: generate `LicenseSituation` values, filter to
those satisfying `isBugCondition`, map each to its steering path, and assert the four
conjuncts above.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed
steering files produce the same result as the original (Property 2).

**Pseudocode:**

```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)        // sufficient-license paths + structural invariants unchanged
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking
because:

- It generates many `LicenseSituation` values automatically across the input domain
  (record counts, license possession, error codes).
- It catches edge cases (e.g., exactly 500 vs 501 records) that manual unit tests miss.
- It provides strong guarantees that behavior is unchanged for all non-bug inputs.

**Test Plan**: Snapshot the **unfixed** content of all sections and invariants that must be
preserved (SHA-256 of non-license sections and of the sufficient-license branches), then
assert the post-fix content matches — mirroring the baseline-snapshot pattern in
`test_module2_license_question.py` (`_STEP_HASHES`) and
`test_missing_pointer_marker_preservation.py`.

**Test Cases**:

1. **Module 1 Step 6a skip preservation** — observe that ≤ 500 records skip 6b–6e and
   proceed to Step 7 on unfixed code; assert this is unchanged after the fix.
2. **Module 1 6b/6d marker preservation** — assert sub-steps 6b and 6d retain exactly their
   existing 👉 questions and 🛑 STOP markers (no new 👉/🛑 added), consistent with
   `test_self_answering_questions_*` and `test_leading_question_enforcement.py`.
3. **Module 2 Step 5 invariant preservation** — assert exactly one 👉 (5b) and exactly one
   STOP in Step 5; assert the ⛔ MANDATORY GATE marker, "Never skip this step…" text, and
   Step 1 "Required Stops" callout (Steps 4 and 5) are unchanged
   (`test_license_step_mandatory.py`).
4. **Module 2 license mechanics preservation** — assert the Base64 decode command, "NEVER
   paste license key" warning, `PIPELINE.LICENSEFILE` JSON with `"licenses/g2.lic"`,
   `license: custom` / `license: evaluation` preference recording, email contacts, and the
   Step 5 checkpoint are unchanged (`test_module2_license_question.py` preservation set).
5. **Hash-locked non-license sections** — assert Module 2 Steps 1–4 and 6–9 SHA-256 hashes
   are unchanged (compatible with the existing `_STEP_HASHES` baselines).
6. **Security preservation** — assert no MCP server URL and no new external URL appears in
   either edited section.
7. **Frontmatter preservation** — assert both files retain `inclusion: manual` frontmatter.

### Unit Tests

- Assert the exact `search_docs` consultation directive text is present in Module 1 Step 6d.
- Assert the `search_docs` directive in Module 2 Step 5a appears after the
  500-record / `SENZ9000` explanation (ordering preserved).
- Assert the `search_docs` directive in Module 2 Step 5c "no license" branch coexists with
  `support@senzing.com`, `sales@senzing.com`, and `licenses/README.md`.
- Assert Step 5 still contains exactly one 👉 and one STOP (regression guard for the scope
  constraint in `test_licensing_guidance.py`).
- Assert no URL is hardcoded in the edited sections.

### Property-Based Tests

- **Fix property** — generate `LicenseSituation` values via `st_license_situation()`,
  filter to `isBugCondition`, map each to its steering path, and assert the path contains an
  enforced, confirmed-tool, non-prose-only `search_docs` consultation with no MCP URL.
  `@settings(max_examples=20)`.
- **Preservation property** — generate non-bug `LicenseSituation` values (records ≤ 500 or
  sufficient license) and assert the sufficient-license paths and all snapshotted invariants
  are byte-identical to baseline. `@settings(max_examples=20)`.
- **Tool-name validity property** — generate the set of tool references found in the edited
  sections and assert each resolves against the `mcp-tool-decision-tree.md` tool set.

Strategy sketch (stdlib + Hypothesis, per `python-conventions.md`):

```python
@st.composite
def st_license_situation(draw: st.DrawFn) -> LicenseSituation:
    total = draw(st.integers(min_value=0, max_value=10_000_000))
    has_license = draw(st.booleans())
    error_code = draw(st.sampled_from([None, "SENZ9000", "SENZ0002"]))
    return LicenseSituation(total, has_license, error_code)

def is_bug_condition(x: LicenseSituation) -> bool:
    return (x.total_record_count > 500 or x.error_code == "SENZ9000") \
        and not x.has_sufficient_license
```

### Integration Tests

- Parse both edited steering files end-to-end and confirm CI structural validators still
  pass (`validate_commonmark.py`, `measure_steering.py --check`) — token budgets in
  `steering-index.yaml` remain within limits after the additive edits.
- Confirm the full Module 1 license-guidance flow (6a → 6b → 6d → MCP consultation → email →
  defer/wait/configure) is internally consistent: the new MCP step does not break the
  branch routing to 6c/6e or the Step 7 transition.
- Confirm the full Module 2 Step 5 flow (5a explanation → 5b 👉 question → 5c branches → 5d
  config → checkpoint) still satisfies the ⛔ mandatory-gate and single-question invariants
  with the MCP consultation directive added.
- Run the complete existing suite for the two files
  (`test_licensing_guidance.py`, `test_license_step_mandatory.py`,
  `test_module2_license_question.py`, `test_self_answering_questions_*`,
  `test_leading_question_enforcement.py`, `test_git_question_*`) to confirm no regression.
