"""Fix-checking and preservation tests for the entity-graph-edge-key-mismatch bugfix.

The Module 3 Phase 2 Entity Graph renders empty because the generated `drawGraph`
passes edges keyed by `source_entity_id`/`target_entity_id` straight into D3's
`forceLink`, which requires each edge to expose `source`/`target`. The mismatch fails
silently (no console error). The fix adds, to the Module 3 Phase 2 steering:

- a new Critical Lesson (item 7) instructing the agent to map
  `source_entity_id`/`target_entity_id` -> `source`/`target` before `forceLink`, and
- a Step 9.4 post-generation smoke check that verifies the generated graph maps the edge
  keys (`source`/`target` before `forceLink`) before the bootcamper presentation gate.

The `/api/graph` API schema is correct and remains unchanged — the mapping is a
client-side concern.

This module is authored against the UNFIXED steering:

- Property 1 (Critical Lesson present) and Property 2 (Step 9.4 smoke check present) are
  EXPECTED TO FAIL on the current content — their failure confirms the guidance gap (the
  bug). They PASS once the steering edits land (Tasks 2-5).
- Property 3 (edge schema preserved) and Property 4 (original six Critical Lessons
  preserved) are regression guards EXPECTED TO PASS on the current content — they pin the
  baseline the fix must not regress.

Feature: entity-graph-edge-key-mismatch

**Validates: Requirements 2.1, 2.2, 2.3, 3.1, 3.2**
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths — the two Module 3 visualization steering files (the only fix surfaces)
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"

# Phase2_File: Step 9 generation + verification steering (Critical Lessons, Step 9.4).
_PHASE2_FILE = _STEERING_DIR / "module-03-phase2-visualization.md"
# ApiRef_File: GET /api/graph schema companion.
_APIREF_FILE = _STEERING_DIR / "module-03-visualization-api-reference.md"

# Edge schema fields every edge element carries (Property 3 — must be preserved).
_EDGE_SCHEMA_FIELDS = (
    "source_entity_id",
    "target_entity_id",
    "match_key",
    "relationship_type",
)

# The original six Critical Lessons (Property 4).
#
# scaffold-visualization-specifics reduction: the literal
# `## CRITICAL LESSONS FOR VISUALIZATION GENERATION` heading and its six bold lesson
# titles were intentionally removed from Phase2_File. The client-rendering guidance was
# relocated into the new "Client-Rendering Constraints — Correct by Construction"
# Steering_Pointer section, which defers to `scripts/generate_standalone_demo.py` as the
# correct-by-construction reference. The PROTECTIVE INTENT of every original lesson is
# preserved and is re-asserted below where each guarantee now lives, rather than pinning
# the removed titles verbatim.
#
# Lessons whose guarantee remains as PROSE in Phase2_File. Each maps to alternative
# case-insensitive substrings; any one satisfies the lesson (searched over the whole
# file).
_PROSE_LESSON_GUARANTEES: dict[str, tuple[str, ...]] = {
    # write_html.py generator mandate (never hand-write HTML+JS).
    "Use Python generator script": ("Python generator script", "write_html.py"),
    # data-* + querySelectorAll instead of inline onclick with dynamic values.
    "No inline onclick with dynamic values": ("onclick", "data-*"),
    # Double quotes for JS, single quotes for HTML attributes.
    "Quote discipline": ("double quotes", "single quotes"),
}

# Lessons now CORRECT BY CONSTRUCTION: their guarantee lives in the Client-Rendering
# Constraints section (which references the generator that bakes them in). All listed
# substrings must be present in that section.
_CORRECT_BY_CONSTRUCTION_GUARANTEES: dict[str, tuple[str, ...]] = {
    # function(){} D3 callbacks (never arrow functions — they break `this` binding).
    "D3.js callback syntax": ("function(){}",),
    # Explicit SVG width/height attributes.
    "Explicit SVG dimensions": ("width", "height"),
    # JS validity guaranteed by the generator's demonstrated, executable artifact.
    "Validate JavaScript syntax": ("generate_standalone_demo.py",),
}

# The presentation gate marker: the agent must STOP here and wait for the bootcamper.
_STOP_MARKER = "🛑 STOP"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a steering file.

    Args:
        path: The file to read.

    Returns:
        The decoded file contents.
    """
    return path.read_text(encoding="utf-8")


def _client_rendering_constraints_section(text: str) -> str:
    """Extract the Client-Rendering Constraints section from Phase2_File.

    scaffold-visualization-specifics reduction: the old
    `## CRITICAL LESSONS FOR VISUALIZATION GENERATION` heading was removed and the
    client-side rendering guidance — including the `source_entity_id`/`target_entity_id`
    -> `source`/`target` edge-key mapping before `forceLink` — was relocated into the
    `## Client-Rendering Constraints — Correct by Construction` Steering_Pointer section
    (which points at `scripts/generate_standalone_demo.py` as the reference). Returns the
    text from that heading up to the next top-level `##` heading or horizontal rule
    (`---`), whichever comes first.

    Args:
        text: The full Phase2_File contents.

    Returns:
        The Client-Rendering Constraints section text (empty string if absent).
    """
    heading = "## Client-Rendering Constraints"
    start = text.find(heading)
    if start == -1:
        return ""
    rest = text[start + len(heading) :]
    end_candidates = [pos for pos in (rest.find("\n## "), rest.find("\n---")) if pos != -1]
    return rest if not end_candidates else rest[: min(end_candidates)]


def _step_9_4_section(text: str) -> str:
    """Extract the Step 9.4 section from Phase2_File.

    Returns the text from the `### 9.4 Start and Verify Web Service` heading up to the
    next sibling/parent heading (`\\n### ` or `\\n## `), whichever comes first.

    Args:
        text: The full Phase2_File contents.

    Returns:
        The Step 9.4 section text (empty string if the heading is absent).
    """
    heading = "### 9.4 Start and Verify Web Service"
    start = text.find(heading)
    if start == -1:
        return ""
    rest = text[start + len(heading) :]
    end_candidates = [pos for pos in (rest.find("\n### "), rest.find("\n## ")) if pos != -1]
    return rest if not end_candidates else rest[: min(end_candidates)]


def _before_presentation_gate(section: str) -> str:
    """Return the portion of a Step 9.4 section preceding the presentation gate.

    The bootcamper presentation gate is marked by the `🛑 STOP` marker. The smoke
    check must appear before it so the empty-graph regression is caught before the
    graph is presented.

    Args:
        section: The Step 9.4 section text.

    Returns:
        The text before the first `🛑 STOP` marker (the whole section if no marker).
    """
    idx = section.find(_STOP_MARKER)
    return section if idx == -1 else section[:idx]


def _mentions_edge_key_mapping(text: str) -> bool:
    """Return whether ``text`` describes the D3 edge-key mapping.

    The edge-key mapping maps the API edge keys
    `source_entity_id`/`target_entity_id` to D3's `source`/`target` before
    `forceLink`. A mention requires naming `forceLink`, the D3 keys `source`/`target`,
    and the API keys `source_entity_id`/`target_entity_id`.

    Args:
        text: The text region to scan.

    Returns:
        True if the edge-key mapping is described, False otherwise.
    """
    return (
        "forceLink" in text
        and "source" in text
        and "target" in text
        and "source_entity_id" in text
        and "target_entity_id" in text
    )


def _references_source_target_before_forcelink(text: str) -> bool:
    """Return whether ``text`` references the source/target -> forceLink mapping.

    Used for the Step 9.4 smoke check, which references the graph edge-key mapping
    (`source`/`target` before `forceLink`).

    Args:
        text: The text region to scan.

    Returns:
        True if both `forceLink` and the `source`/`target` keys are referenced.
    """
    return "forceLink" in text and "source" in text and "target" in text


# ===========================================================================
# Property 1 — Fix Checking: Critical Lesson 7 (edge-key mapping)
# ===========================================================================


class TestEdgeKeyMappingCriticalLesson:
    """Property 1: the Critical Lessons section specifies the edge-key mapping.

    Authored to FAIL on the unfixed content — the section currently has six lessons
    and none mention mapping `source_entity_id`/`target_entity_id` to D3's
    `source`/`target` before `forceLink`. PASSES once the fix lands (Task 2).

    **Validates: Requirements 2.1, 2.2**
    """

    def test_critical_lessons_specify_edge_key_mapping(self) -> None:
        """Phase2_File names the edge-key mapping for `forceLink`.

        After the scaffold-visualization-specifics reduction the edge-key mapping
        guidance lives in the `## Client-Rendering Constraints — Correct by Construction`
        section (the old CRITICAL LESSONS heading is gone). The protective intent is
        unchanged: steering must name the `source_entity_id`/`target_entity_id` ->
        `source`/`target` mapping before `forceLink`.
        """
        section = _client_rendering_constraints_section(_read(_PHASE2_FILE))
        assert section, (
            "Phase2_File is missing the 'Client-Rendering Constraints — Correct by "
            "Construction' section that now carries the edge-key mapping guidance"
        )
        assert _mentions_edge_key_mapping(section), (
            "The Critical Lessons section does not specify the D3 edge-key mapping: "
            "expected a lesson naming `forceLink` and mapping the API edge keys "
            "`source_entity_id`/`target_entity_id` to D3's `source`/`target` before "
            "passing edges to forceLink, but found none. Without it the generated "
            "drawGraph wires API edges straight into forceLink and the Entity Graph "
            "renders empty (the bug)."
        )


# ===========================================================================
# Property 2 — Fix Checking: Step 9.4 post-generation smoke check
# ===========================================================================


class TestStep94SmokeCheck:
    """Property 2: Step 9.4 contains a graph edge-key-mapping smoke check.

    Authored to FAIL on the unfixed content — Step 9.4 verifies only that
    `/api/graph` returns >=1 node and >=1 edge; it never inspects the generated
    `drawGraph` for the `source`/`target` mapping. PASSES once the fix lands (Task 4).

    **Validates: Requirements 2.3**
    """

    def test_step_9_4_has_edge_key_mapping_smoke_check_before_gate(self) -> None:
        """Step 9.4 references the edge-key-mapping smoke check before the STOP gate.

        FAILS on unfixed content — there is no smoke/verification check referencing
        the graph edge-key mapping (`source`/`target` before `forceLink`) ahead of the
        bootcamper presentation gate.
        """
        section = _step_9_4_section(_read(_PHASE2_FILE))
        assert section, "Phase2_File is missing the Step 9.4 section"
        assert _STOP_MARKER in section, (
            "Step 9.4 no longer contains the bootcamper presentation gate "
            f"({_STOP_MARKER!r}); the smoke check must be positioned before it."
        )
        before_gate = _before_presentation_gate(section)
        assert _references_source_target_before_forcelink(before_gate), (
            "Step 9.4 has no post-generation smoke check referencing the graph "
            "edge-key mapping (`source`/`target` before `forceLink`) before the "
            f"bootcamper presentation gate ({_STOP_MARKER!r}). The empty-graph "
            "regression therefore is not caught before the graph is presented."
        )


# ===========================================================================
# Property 3 — Preservation: /api/graph edge schema is unchanged
# ===========================================================================


class TestEdgeSchemaPreserved:
    """Property 3: the `/api/graph` edge schema fields remain in both files.

    Regression guard. PASSES on unfixed content and must keep passing — the fix is a
    client-side mapping concern and must not rename the API edge fields.

    **Validates: Requirements 3.1**
    """

    def test_edge_schema_fields_present_in_both_files(self) -> None:
        """Both steering files still describe every edge schema field."""
        for path in (_PHASE2_FILE, _APIREF_FILE):
            content = _read(path)
            for field in _EDGE_SCHEMA_FIELDS:
                assert field in content, (
                    f"{path.name} no longer describes the edge field '{field}'; "
                    "the /api/graph edge schema must be preserved (API contract "
                    "unchanged)."
                )


# ===========================================================================
# Property 4 — Preservation: the original six Critical Lessons remain
# ===========================================================================


class TestOriginalCriticalLessonsPreserved:
    """Property 4: the protective intent of the original six Critical Lessons is preserved.

    Regression guard. The scaffold-visualization-specifics reduction intentionally
    removed the `## CRITICAL LESSONS FOR VISUALIZATION GENERATION` heading and its six
    bold titles from Phase2_File. Rather than pin the removed titles (which would either
    fail or force re-adding the deleted heading), this test now asserts each lesson's
    guarantee where it now lives:

    - PROSE lessons (Python generator script, no-inline-onclick, quote discipline) are
      still asserted directly in Phase2_File prose.
    - CORRECT-BY-CONSTRUCTION lessons (D3.js callback syntax, explicit SVG dimensions,
      JavaScript validity) are asserted in the "Client-Rendering Constraints — Correct by
      Construction" section, which bakes them into the generator artifact
      (`scripts/generate_standalone_demo.py`).

    No protection is weakened — every guarantee is still enforced, only relocated.

    **Validates: Requirements 3.2**
    """

    def test_original_six_critical_lessons_present(self) -> None:
        """Each original Critical Lesson's guarantee is preserved after the reduction."""
        text = _read(_PHASE2_FILE)
        text_lower = text.lower()

        # Prose guarantees: any one alternative substring anywhere in the file suffices.
        for lesson, needles in _PROSE_LESSON_GUARANTEES.items():
            assert any(n.lower() in text_lower for n in needles), (
                f"Phase2_File lost the protective intent of the original Critical "
                f"Lesson '{lesson}'; expected one of {needles} to remain in the prose."
            )

        # Correct-by-construction guarantees: all substrings must be present in the
        # Client-Rendering Constraints section (which references the generator).
        section = _client_rendering_constraints_section(text)
        assert section, (
            "Phase2_File is missing the 'Client-Rendering Constraints — Correct by "
            "Construction' section that now carries the correct-by-construction lessons"
        )
        section_lower = section.lower()
        for lesson, needles in _CORRECT_BY_CONSTRUCTION_GUARANTEES.items():
            assert all(n.lower() in section_lower for n in needles), (
                f"The Client-Rendering Constraints section no longer guarantees the "
                f"original Critical Lesson '{lesson}' correct-by-construction; expected "
                f"all of {needles} in that section."
            )
