# Design Document

## Overview

The recap PDF generator (`senzing-bootcamp/scripts/generate_recap_pdf.py`) silently drops content when
`docs/bootcamp_recap.md` does not conform to a rigid, undocumented schema. The fix makes the parser
tolerant, adds a raw-Markdown fallback so content is never silently dropped, emits a warning when the
parsed body is empty or under-populated, and documents the expected schema — all while keeping the
strict-schema path and every existing recap test byte-for-byte unchanged in behavior.

## Glossary

- **Strict_Schema**: The current expected recap shape — `## Module N: <name> — <timestamp>` headings
  with the five `### ` subsections (Information Shared, Questions Asked, Answers Given, Actions Taken,
  Duration).
- **Loose_Heading**: A module heading without the ` — <timestamp>` suffix, e.g. `## Module 1: Business
  Problem`.
- **Generic_Content**: Renderable Markdown inside a module section that is not part of the five known
  subsections — prose paragraphs, fenced code blocks, other headings, and stray lists.
- **Raw_Body_Fallback**: Rendering the recap's raw Markdown body as generic blocks when no structured
  sections can be parsed.
- **F / F'**: The recap generator before the fix (`F`) and after the fix (`F'`).

## Bug Details

The defect manifests as a near-empty PDF (cover page only) even though `bootcamp_recap.md` has a full
header and several module sections of prose. It surfaces in three places in the pipeline:

1. `_MODULE_HEADING_RE = r"^##\s+Module\s+(\d+):\s+(.+?)\s+—\s+(.+)$"` requires an em-dash plus a
   trailing timestamp, so `_parse_sections` returns `[]` for Loose_Headings.
2. `_split_subsections` + `_extract_list_items` capture only list items under the five known `### `
   subsections; prose, code blocks, and other headings are discarded.
3. `main` renders whatever `parse_recap_markdown` returns (even zero sections) and prints
   `PDF generated:` with exit 0 — no signal that the body was empty.

This corresponds to the bug condition in `bugfix.md`: a non-empty body whose renderable content the
strict parser loses (`isBugCondition(X)`).

## Expected Behavior

- A recap with Loose_Headings is recognized: N sections parsed, `timestamp == ""` (Req 2.1).
- Generic_Content within a module is rendered, not discarded (Req 2.2).
- When no structured sections parse from a non-empty body, the Raw_Body_Fallback renders the content
  so nothing is silently dropped (Req 2.3).
- When the parsed section count is zero or substantially fewer than the headings detectable in the
  source, a warning is emitted at generation time (Req 2.4).
- The exact recap schema (heading format + recognized subsection names) is documented (Req 2.5).
- Strict_Schema recaps parse and render exactly as today; `fpdf2`-absent and missing/empty-input
  behavior is unchanged (Req 3.1–3.5).

## Hypothesized Root Cause

The parser was written to a single rigid template and treats any deviation as "no content." There is
no second-chance matching for headings, no capture path for non-subsection content, and no
post-parse sanity check comparing parsed sections against the source. Because rendering still
"succeeds" on an empty `RecapDocument`, the loss is invisible. The root cause is therefore
*intolerant parsing with no fallback and no observability*, not a rendering bug in `fpdf2`.

## Fix Implementation

### 1. Tolerant module-heading matching

Add a relaxed pattern and try strict first, then loose:

```python
_MODULE_HEADING_RE = re.compile(r"^##\s+Module\s+(\d+):\s+(.+?)\s+—\s+(.+)$", re.MULTILINE)  # unchanged
_MODULE_HEADING_LOOSE_RE = re.compile(r"^##\s+Module\s+(\d+):\s+(.+?)\s*$", re.MULTILINE)     # new
```

`_parse_sections` uses the strict pattern when it matches (identical behavior for Strict_Schema
recaps), otherwise the loose pattern with `timestamp = ""` (Req 2.1).

### 2. Capture Generic_Content per module

Add a defaulted `generic_content: list[str]` field to `RecapSection`. `_split_subsections` also returns
the leftover (non-known-subsection) text, which `_parse_sections` stores as Generic_Content.
`_render_module_page` renders those blocks after the five known subsections (Req 2.2). The field is
defaulted so `format_recap_section` and the round-trip tests are unaffected.

### 3. Raw_Body_Fallback

Add `render_markdown_body(pdf, body_text)` to render arbitrary Markdown (headings/paragraphs/lists/code)
as PDF blocks. `render_pdf` renders structured sections when present, else cover page + raw body. `main`
takes this path when sections are empty but the body is non-empty (Req 2.3).

### 4. Warning on empty / under-populated parse

`main` counts Loose_Heading occurrences in the source and compares to the parsed section count. Zero
sections with a non-empty body, or parsed sections substantially fewer than detected headings, prints a
warning to stderr (preserving the stdout `PDF generated:` contract) and exits 0 (Req 2.4).

### 5. Schema documentation

Document the expected recap schema in the module docstring (heading format `## Module N: <name>
[— <timestamp>]`, the five recognized subsection names, and that any other content renders generically)
so reconstructed recaps and the `graduation-markdown-normalization` normalizer target the same shape
(Req 2.5).

### Components touched

| Function | Change |
|---|---|
| `_MODULE_HEADING_LOOSE_RE` | NEW relaxed pattern |
| `RecapSection` | NEW defaulted `generic_content` field (back-compatible) |
| `_split_subsections` | Also return leftover text for Generic_Content |
| `_parse_sections` | Strict→loose fallback; capture Generic_Content; never raise |
| `render_markdown_body` | NEW raw-body renderer |
| `_render_module_page` | Render Generic_Content after known subsections |
| `render_pdf` | Raw-body fallback when no structured sections |
| `main` | Warning computation; structured vs fallback render |

`parse_recap_markdown`, `format_recap_document`, and `format_recap_section` keep their signatures and,
for Strict_Schema input, identical output.

## Correctness Properties

These mirror the Fix Checking and Preservation Checking specification in `bugfix.md`.

### Property 1: Fix — no content silently dropped

*For all* recap inputs `X` where `isBugCondition(X)` holds, `F'(X)` renders a non-empty PDF body
containing the input's renderable content (loose headings recognized, Generic_Content rendered, or
Raw_Body_Fallback used).

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 2: Warning visibility

*For all* recap inputs whose parsed section count is zero (non-empty body) or substantially fewer than
the headings detectable in the source, `F'` emits a warning to stderr identifying the mismatch.

**Validates: Requirements 2.4**

### Property 3: Preservation — strict recaps unchanged

*For all* recap inputs `X` where `NOT isBugCondition(X)`, `F'(X) == F(X)`: the parsed `RecapDocument`
and the rendered structured PDF are identical to today, and every existing test in
`test_generate_recap_pdf.py` (round-trip, structural completeness, Q&A pairing, append preservation,
timestamp format, chronological ordering) continues to pass.

**Validates: Requirements 3.1, 3.2, 3.5**

### Property 4: Graceful degradation preserved

*For all* environments without `fpdf2` and *for all* missing/empty inputs, `F'` behaves exactly as `F`
(same hint/error, exit code 1, no traceback).

**Validates: Requirements 3.3, 3.4**

## Testing Strategy

Tests extend `senzing-bootcamp/tests/test_generate_recap_pdf.py` (pytest + Hypothesis), reusing the
existing import pattern and strategies.

- **Loose heading parse**: `## Module N: <name>` (no timestamp) parses N sections with `timestamp == ""`.
- **Generic content captured**: a module with prose + a code block yields non-empty `generic_content`
  and those blocks appear in rendered output.
- **Raw-body fallback**: a non-empty body that produces zero structured sections renders a non-empty
  PDF body (asserted via a parse/render seam, not pixel inspection).
- **Warning emitted**: zero-section non-empty body and under-populated cases warn on stderr; exit 0.
- **Preservation (Property 3)**: re-run the full existing recap suite; assert strict `format → parse`
  round-trip equivalence is unchanged.
- **Graceful degradation (Property 4)**: monkeypatch the `fpdf` import to raise `ImportError`; assert
  hint + exit 1; assert missing/empty inputs still exit 1.
- **Hypothesis (Property 1)**: generate free-form recaps (loose headings + prose + code); assert the
  rendered body is non-empty and contains the input's renderable text tokens.
```
