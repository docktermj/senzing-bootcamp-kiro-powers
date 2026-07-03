"""Tests for the scaffold-visualization-specifics relocation.

Feature: scaffold-visualization-specifics.

Module 3's client-side visualization specifics are relocated out of always-loaded
steering prose and into the one local artifact that already emits working code —
``scripts/generate_standalone_demo.py`` — so those specifics are correct by
construction. The constraints that depend on the server-side MCP scaffold or the live
SDK (the four ``/api/*`` endpoints, SDK relationship discovery, ``search_builder.py``
enrichment, and the four-tab Step 9 dashboard) stay in steering.

This module owns the :data:`RELOCATION_MANIFEST` — the single declared source of truth
for the split. Each :class:`Specific` records where a Visualization_Specific is
guaranteed to live: in the generated output (``coverage == "output"``), retained in
steering (``coverage == "steering"``), or both (``coverage == "both"``). Detector fields
(``output_marker`` / ``steering_anchor``) are stable substrings the property tests key on
so no specific can be silently dropped from both places.

Example counts for property tests come from the active Hypothesis profile (registered in
the repo-root ``hypothesis_profiles`` module and loaded by ``conftest.py``); no inline
``@settings(max_examples=...)`` is set.

Validates: Requirements 4.1, 4.2
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts are not packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import generate_standalone_demo  # noqa: E402,F401
import measure_steering  # noqa: E402
import progress_utils  # noqa: E402


# ---------------------------------------------------------------------------
# Data model: one Visualization_Specific and where it is guaranteed to live
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Specific:
    """One Visualization_Specific and where it is guaranteed to live.

    Attributes:
        id: Stable id, e.g. ``"edge-key-mapping"``.
        description: Human-readable constraint.
        coverage: One of ``"output"``, ``"steering"``, or ``"both"``.
        output_marker: Substring detectable in the generated output when the
            specific is covered there, otherwise ``None``.
        steering_anchor: Substring detectable in the reduced steering (or its
            api-reference companion) when the specific is retained there,
            otherwise ``None``.
    """

    id: str
    description: str
    coverage: str
    output_marker: str | None
    steering_anchor: str | None


# ---------------------------------------------------------------------------
# RELOCATION_MANIFEST — the declared split (design's Relocation_Manifest table)
# ---------------------------------------------------------------------------
#
# Detector notes:
#   * ``output_marker`` values are stable substrings emitted verbatim by
#     ``generate_standalone_demo.py`` into ``index.html`` / ``server.py``.
#   * ``steering_anchor`` values are stable substrings retained in the reduced
#     ``module-03-phase2-visualization.md`` or its
#     ``module-03-visualization-api-reference.md`` companion.
RELOCATION_MANIFEST: tuple[Specific, ...] = (
    Specific(
        id="stdlib-http-server",
        description="Python stdlib http.server, no third-party framework",
        coverage="output",
        output_marker="from http.server import",
        steering_anchor=None,
    ),
    Specific(
        id="d3-v7-cdn",
        description="D3.js v7 from the d3js.org CDN",
        coverage="output",
        output_marker="d3.v7.min.js",
        steering_anchor=None,
    ),
    Specific(
        id="single-self-contained-page",
        description="one HTML file with embedded CSS/JS",
        coverage="output",
        output_marker="<!DOCTYPE html>",
        steering_anchor=None,
    ),
    Specific(
        id="function-callbacks",
        description="function(){} D3 callbacks, no arrow functions",
        coverage="output",
        output_marker="function (event, d)",
        steering_anchor=None,
    ),
    Specific(
        id="explicit-svg-dimensions",
        description="explicit SVG width/height attributes",
        coverage="output",
        output_marker='.attr("width", width)',
        steering_anchor=None,
    ),
    Specific(
        id="edge-key-mapping",
        description=(
            "map source_entity_id/target_entity_id to source/target before forceLink"
        ),
        coverage="both",
        output_marker="source: e.source_entity_id",
        steering_anchor="forceLink",
    ),
    Specific(
        id="truthset-source-colors",
        description="CUSTOMERS/REFERENCE/WATCHLIST source-color map",
        coverage="output",
        output_marker="COLORS = { CUSTOMERS:",
        steering_anchor=None,
    ),
    Specific(
        id="node-radius-formula",
        description="node radius = min(max(8 + record_count * 4, 8), 40)",
        coverage="output",
        output_marker="8 + node.record_count * 4",
        steering_anchor=None,
    ),
    Specific(
        id="api-endpoints",
        description="four /api/* endpoint schemas",
        coverage="steering",
        output_marker=None,
        steering_anchor="### 9.2 API Endpoints",
    ),
    Specific(
        id="sdk-relationship-discovery",
        description="find_network_by_entity_id / relationship-inclusion flag",
        coverage="steering",
        output_marker=None,
        steering_anchor="find_network_by_entity_id",
    ),
    Specific(
        id="search-enrichment",
        description="search_builder.py enrichment with the 10-entity cap",
        coverage="steering",
        output_marker=None,
        steering_anchor="search_builder.py",
    ),
    Specific(
        id="four-tab-dashboard",
        description="Entity Graph / Merges / Stats / Probe four-tab dashboard",
        coverage="steering",
        output_marker=None,
        steering_anchor="Exactly 4 tabs",
    ),
    Specific(
        id="mandatory-gate",
        description="Step 9 unconditional mandatory gate + Governing Rule 15",
        coverage="steering",
        output_marker=None,
        steering_anchor="MANDATORY GATE",
    ),
)


# ---------------------------------------------------------------------------
# Guard test: the manifest itself cannot silently shrink or lose detectors
# ---------------------------------------------------------------------------

# The complete set of Visualization_Specific ids from the design's Data Models
# table. RELOCATION_MANIFEST must cover exactly these — no more, no fewer.
_EXPECTED_SPECIFIC_IDS: frozenset[str] = frozenset(
    {
        "stdlib-http-server",
        "d3-v7-cdn",
        "single-self-contained-page",
        "function-callbacks",
        "explicit-svg-dimensions",
        "edge-key-mapping",
        "truthset-source-colors",
        "node-radius-formula",
        "api-endpoints",
        "sdk-relationship-discovery",
        "search-enrichment",
        "four-tab-dashboard",
        "mandatory-gate",
    }
)

_VALID_COVERAGE: frozenset[str] = frozenset({"output", "steering", "both"})


class TestRelocationManifestGuard:
    """Guard the RELOCATION_MANIFEST against silent shrinkage or detector loss.

    Validates: Requirement 4.1 — the manifest is the single declared source of
    truth for the split and must list every Visualization_Specific named in the
    design's Data Models table, with coverage-appropriate detector fields.
    """

    def test_manifest_lists_every_design_specific(self) -> None:
        """Every design-named specific appears exactly once in the manifest."""
        manifest_ids = [s.id for s in RELOCATION_MANIFEST]

        # No duplicates — each specific is declared once.
        assert len(manifest_ids) == len(set(manifest_ids)), (
            f"duplicate ids in RELOCATION_MANIFEST: {manifest_ids}"
        )

        # The manifest covers exactly the design's table (no drift either way).
        assert set(manifest_ids) == _EXPECTED_SPECIFIC_IDS, (
            "RELOCATION_MANIFEST drifted from the design's Data Models table; "
            f"missing={_EXPECTED_SPECIFIC_IDS - set(manifest_ids)}, "
            f"unexpected={set(manifest_ids) - _EXPECTED_SPECIFIC_IDS}"
        )

    def test_every_entry_has_valid_coverage_and_required_detectors(self) -> None:
        """Coverage is valid and the detector fields it implies are present."""
        for specific in RELOCATION_MANIFEST:
            assert specific.coverage in _VALID_COVERAGE, (
                f"{specific.id}: coverage {specific.coverage!r} not one of "
                f"{sorted(_VALID_COVERAGE)}"
            )

            # coverage including 'output' requires a non-None output_marker.
            if specific.coverage in ("output", "both"):
                assert specific.output_marker is not None, (
                    f"{specific.id}: coverage {specific.coverage!r} requires a "
                    "non-None output_marker"
                )

            # coverage including 'steering' requires a non-None steering_anchor.
            if specific.coverage in ("steering", "both"):
                assert specific.steering_anchor is not None, (
                    f"{specific.id}: coverage {specific.coverage!r} requires a "
                    "non-None steering_anchor"
                )


# ---------------------------------------------------------------------------
# Reduced steering file locator
# ---------------------------------------------------------------------------
_STEERING_FILE = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "module-03-phase2-visualization.md"
)


def _read_reduced_steering() -> str:
    """Return the text of the reduced Module 3 Phase 2 steering file.

    Returns:
        The full contents of ``steering/module-03-phase2-visualization.md``.
    """
    return _STEERING_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Steering_Pointer + gate-retention example tests
# ---------------------------------------------------------------------------


class TestSteeringReduction:
    """Steering_Pointer present, duplication gone, gates and smoke check retained.

    Validates: Requirements 2.1, 2.3, 3.1 — the reduced steering points to the
    generated artifact for the client-rendering specifics, no longer duplicates
    the seven-lesson / D3-code-style block or the external D3 CDN URL, and retains
    the mandatory gate, Rule 15 scope note, and the render smoke check with its
    Fix_Instruction.
    """

    def test_points_to_generated_demo_and_drops_duplicated_block(self) -> None:
        """Steering references the generator and no longer restates the specifics.

        Validates: Requirement 2.1.
        """
        text = _read_reduced_steering()

        # The Steering_Pointer references the local generator as the reference.
        assert "generate_standalone_demo.py" in text, (
            "reduced steering must point to scripts/generate_standalone_demo.py "
            "as the client-rendering reference"
        )

        # The duplicated seven-lesson block is gone.
        assert "CRITICAL LESSONS FOR VISUALIZATION GENERATION" not in text, (
            "the duplicated seven-item CRITICAL LESSONS block must be removed"
        )

        # The duplicated D3-code-style block is gone.
        assert "D3.js Code Style Constraints" not in text, (
            "the duplicated 'D3.js Code Style Constraints' block must be removed"
        )

    def test_external_d3_cdn_url_removed(self) -> None:
        """The external D3 CDN URL no longer appears in steering prose.

        Validates: Requirement 2.1 (clears the MEDIUM external-URL finding).
        """
        text = _read_reduced_steering()
        assert "d3js.org" not in text, (
            "the external D3 CDN URL must live only in the generated "
            "artifact code, not in steering prose"
        )

    def test_mandatory_gate_and_rule_15_retained(self) -> None:
        """The mandatory gate block and Rule 15 scope note remain.

        Validates: Requirement 3.1.
        """
        text = _read_reduced_steering()
        assert "MANDATORY GATE" in text, (
            "the MANDATORY GATE block must be retained verbatim"
        )
        assert "Governing Rule 15" in text, (
            "the Governing Rule 15 scope note must be retained"
        )

    def test_render_smoke_check_and_fix_instruction_retained(self) -> None:
        """The generated-code render smoke check and its Fix_Instruction remain.

        Validates: Requirement 2.3.
        """
        text = _read_reduced_steering()
        assert "Generated-code check" in text, (
            "the render smoke check (Generated-code check) must be retained"
        )
        assert "Fix_Instruction" in text, (
            "the render smoke check Fix_Instruction must be retained"
        )


# ---------------------------------------------------------------------------
# API-reference companion locator (steering anchors may live here too)
# ---------------------------------------------------------------------------
_API_REFERENCE_FILE = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "module-03-visualization-api-reference.md"
)


def _read_reduced_steering_bundle() -> str:
    """Return the reduced steering plus its api-reference companion, concatenated.

    A ``steering``-covered specific is retained either in the reduced
    ``module-03-phase2-visualization.md`` or in its
    ``module-03-visualization-api-reference.md`` companion, so Property 1 keys
    on the concatenation of both.

    Returns:
        The two steering files joined with a newline.
    """
    return (
        _STEERING_FILE.read_text(encoding="utf-8")
        + "\n"
        + _API_REFERENCE_FILE.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------
# Module-scoped generated artifacts — generate once, inspect many times
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def generated_artifacts(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Generate the standalone demo once and return index.html + server.py text.

    Uses a module-scoped temp working directory (``tmp_path_factory``) so
    generation happens a single time for all Property 1 examples. A
    ``progress.json`` inside the same temp dir absorbs ``generate_demo``'s
    owed-marker side effect so no repo state is touched.

    Args:
        tmp_path_factory: Session-level temp directory factory.

    Returns:
        The concatenation of the emitted ``index.html`` and ``server.py`` text.
    """
    work = tmp_path_factory.mktemp("scaffold_viz")
    out_dir = work / "web_service"
    progress_path = work / "progress.json"

    ok = generate_standalone_demo.generate_demo(
        output_dir=str(out_dir),
        progress_path=str(progress_path),
        port=8080,
    )
    assert ok, "generate_demo must succeed to produce artifacts for Property 1"

    index_html = (out_dir / "index.html").read_text(encoding="utf-8")
    server_py = (out_dir / "server.py").read_text(encoding="utf-8")
    return index_html + "\n" + server_py


# ---------------------------------------------------------------------------
# Coverage helper shared by the property test and the parametrized sweep
# ---------------------------------------------------------------------------


def _assert_specific_covered(
    specific: Specific, artifacts_text: str, steering_text: str
) -> None:
    """Assert *specific* is covered per its ``coverage`` — never by neither.

    Args:
        specific: The Visualization_Specific under test.
        artifacts_text: The generated ``index.html`` + ``server.py`` text.
        steering_text: The reduced steering + api-reference companion text.

    Raises:
        AssertionError: If a required detector is missing (a silently dropped
            constraint) or the coverage value is unrecognized.
    """
    covered_by_output = False
    covered_by_steering = False

    if specific.coverage in ("output", "both"):
        assert specific.output_marker is not None
        covered_by_output = specific.output_marker in artifacts_text
        assert covered_by_output, (
            f"{specific.id}: output_marker {specific.output_marker!r} not found "
            "in the generated artifacts (output-covered constraint dropped)"
        )

    if specific.coverage in ("steering", "both"):
        assert specific.steering_anchor is not None
        covered_by_steering = specific.steering_anchor in steering_text
        assert covered_by_steering, (
            f"{specific.id}: steering_anchor {specific.steering_anchor!r} not "
            "found in the reduced steering or its api-reference companion "
            "(steering-covered constraint dropped)"
        )

    # No specific may be covered by neither side.
    assert covered_by_output or covered_by_steering, (
        f"{specific.id}: covered by neither the generated output nor the "
        "reduced steering"
    )


@st.composite
def st_manifest_specific(draw: st.DrawFn) -> Specific:
    """Draw one :class:`Specific` from :data:`RELOCATION_MANIFEST`.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A manifest entry to check for coverage.
    """
    return draw(st.sampled_from(RELOCATION_MANIFEST))


class TestNoConstraintSilentlyDropped:
    """Property 1: no relocated constraint is silently dropped.

    Validates: Requirements 1.3, 2.3, 4.1 — every Visualization_Specific in the
    RELOCATION_MANIFEST is covered where it is declared to live (generated output
    for ``output``, reduced steering / api-reference companion for ``steering``,
    both sides for ``both``), and none is covered by neither.
    """

    # Feature: scaffold-visualization-specifics, Property 1: No relocated
    # constraint is silently dropped
    @given(specific=st_manifest_specific())
    def test_drawn_specific_is_covered(
        self, specific: Specific, generated_artifacts: str
    ) -> None:
        """A specific drawn from the manifest is covered per its coverage.

        Validates: Requirements 1.3, 2.3, 4.1.
        """
        steering_text = _read_reduced_steering_bundle()
        _assert_specific_covered(specific, generated_artifacts, steering_text)

    @pytest.mark.parametrize(
        "specific", RELOCATION_MANIFEST, ids=[s.id for s in RELOCATION_MANIFEST]
    )
    def test_every_manifest_specific_is_covered(
        self, specific: Specific, generated_artifacts: str
    ) -> None:
        """Full-manifest sweep: every entry is covered regardless of sampling.

        Validates: Requirements 1.3, 2.3, 4.1.
        """
        steering_text = _read_reduced_steering_bundle()
        _assert_specific_covered(specific, generated_artifacts, steering_text)


# ---------------------------------------------------------------------------
# Property 2 — generation-parameter strategy + embedded-graph parsing helpers
# ---------------------------------------------------------------------------

# Safe directory-name characters: no path separators, dots, or whitespace, so
# every drawn name is a single creatable subdirectory of a tmp_path root.
_DIR_NAME_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)

# Node ids are written as ``entity_id: <int>``; the negative lookbehind for an
# underscore excludes the ``source_entity_id`` / ``target_entity_id`` edge keys.
_NODE_ID_RE = re.compile(r"(?<!_)entity_id:\s*(\d+)")
_EDGE_SOURCE_RE = re.compile(r"source_entity_id:\s*(\d+)")
_EDGE_TARGET_RE = re.compile(r"target_entity_id:\s*(\d+)")


@st.composite
def st_generation_params(draw: st.DrawFn) -> tuple[str, int]:
    """Draw a safe ``output_dir`` name and a valid ``port`` for generate_demo.

    The directory name is a single creatable path segment (no separators, dots,
    or whitespace); the port is a non-privileged TCP port.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        A ``(output_dir_name, port)`` tuple.
    """
    output_dir = draw(
        st.text(alphabet=_DIR_NAME_ALPHABET, min_size=1, max_size=24).filter(
            lambda s: s not in (".", "..")
        )
    )
    port = draw(st.integers(min_value=1024, max_value=65535))
    return output_dir, port


def _extract_node_ids(index_html: str) -> set[int]:
    """Return the set of node ``entity_id`` integers embedded in ``index.html``.

    Args:
        index_html: The emitted standalone-demo HTML.

    Returns:
        The set of node ``entity_id`` values found in the embedded ``DATA``.
    """
    return {int(m) for m in _NODE_ID_RE.findall(index_html)}


def _extract_edge_endpoints(index_html: str) -> list[tuple[int, int]]:
    """Return the embedded edges as ``(source_entity_id, target_entity_id)`` pairs.

    Args:
        index_html: The emitted standalone-demo HTML.

    Returns:
        A list of ``(source, target)`` integer pairs, one per embedded edge.
    """
    sources = [int(m) for m in _EDGE_SOURCE_RE.findall(index_html)]
    targets = [int(m) for m in _EDGE_TARGET_RE.findall(index_html)]
    return list(zip(sources, targets))


class TestEdgeKeyMapping:
    """Property 2: edge-key mapping is correct by construction (blank graph impossible).

    Validates: Requirements 1.2, 3.2, 4.1 — for any generation of the standalone
    demo, the emitted ``index.html`` maps each edge's
    ``source_entity_id``/``target_entity_id`` to D3's ``source``/``target``
    BEFORE ``forceLink`` in source order, and every embedded edge endpoint
    resolves to an embedded node ``entity_id`` — so the demo cannot render the
    blank-graph silent failure.
    """

    # Feature: scaffold-visualization-specifics, Property 2: Edge-key mapping is
    # correct by construction (blank graph impossible)
    @given(params=st_generation_params())
    def test_edge_key_mapping_correct_by_construction(
        self, params: tuple[str, int], tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Mapping precedes forceLink and no edge endpoint is dangling.

        Validates: Requirements 1.2, 3.2, 4.1.
        """
        output_name, port = params
        # Session-scoped factory yields a fresh, uniquely numbered working
        # directory per example, so no repo files are touched and the shared
        # function-scoped tmp_path health check does not apply.
        work = tmp_path_factory.mktemp("edge_key_mapping")
        out_dir = work / output_name
        progress_path = work / "progress.json"

        ok = generate_standalone_demo.generate_demo(
            output_dir=str(out_dir),
            progress_path=str(progress_path),
            port=port,
        )
        assert ok, "generate_demo must succeed to produce the index.html artifact"

        index_html = (out_dir / "index.html").read_text(encoding="utf-8")

        # The *_entity_id -> source/target mapping must appear BEFORE forceLink
        # in source order, or forceLink resolves nothing and the graph is blank.
        map_index = index_html.find("source: e.source_entity_id")
        assert map_index != -1, (
            "the edge-key mapping (source: e.source_entity_id) is missing from "
            "the emitted index.html"
        )
        force_link_index = index_html.find("forceLink(")
        assert force_link_index != -1, (
            "forceLink( is missing from the emitted index.html"
        )
        assert map_index < force_link_index, (
            "the source/target edge-key mapping must precede forceLink( in source "
            f"order (map at {map_index}, forceLink at {force_link_index})"
        )

        # Every edge endpoint must resolve to an embedded node entity_id — a
        # dangling edge would silently drop links and blank the graph.
        node_ids = _extract_node_ids(index_html)
        assert node_ids, "no node entity_id values parsed from embedded DATA"

        edges = _extract_edge_endpoints(index_html)
        assert edges, "no edges parsed from embedded DATA"

        for source, target in edges:
            assert source in node_ids, (
                f"edge source_entity_id {source} does not resolve to any node "
                f"entity_id in {sorted(node_ids)} (dangling edge -> blank graph)"
            )
            assert target in node_ids, (
                f"edge target_entity_id {target} does not resolve to any node "
                f"entity_id in {sorted(node_ids)} (dangling edge -> blank graph)"
            )


class TestRequiredStructuralElements:
    """Property 3: required client-rendering structural elements are always emitted.

    Validates: Requirements 1.1, 3.2, 4.1 — for any generation (any
    ``output_dir`` and ``port``), the emitted artifacts contain every
    ``output``-covered Embeddable_Specific: the stdlib ``http.server`` import
    with a localhost bind and no third-party HTTP framework, exactly one D3.js
    v7 CDN ``<script>``, a single self-contained ``index.html``, explicit SVG
    ``width``/``height`` attributes, the TruthSet source-color map with the
    node-radius formula, and no arrow-function used as a D3 callback.
    """

    # Feature: scaffold-visualization-specifics, Property 3: Required
    # client-rendering structural elements are always emitted
    @given(params=st_generation_params())
    def test_required_structural_elements_always_emitted(
        self, params: tuple[str, int], tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Every output-covered structural element is present in the artifacts.

        Validates: Requirements 1.1, 3.2, 4.1.
        """
        output_name, port = params
        # Session-scoped factory yields a fresh, uniquely numbered working
        # directory per example (mirrors the Property 2 test) so no repo files
        # are touched and the function-scoped tmp_path health check does not
        # apply.
        work = tmp_path_factory.mktemp("structural_elements")
        out_dir = work / output_name
        progress_path = work / "progress.json"

        ok = generate_standalone_demo.generate_demo(
            output_dir=str(out_dir),
            progress_path=str(progress_path),
            port=port,
        )
        assert ok, "generate_demo must succeed to produce the emitted artifacts"

        index_html = (out_dir / "index.html").read_text(encoding="utf-8")
        server_py = (out_dir / "server.py").read_text(encoding="utf-8")

        # --- server.py: stdlib http.server, localhost bind, no framework ---
        assert "from http.server import" in server_py, (
            "server.py must import the stdlib http.server module"
        )
        assert "127.0.0.1" in server_py, (
            "server.py must bind the localhost address 127.0.0.1"
        )
        server_lower = server_py.lower()
        assert "flask" not in server_lower, (
            "server.py must not use the third-party Flask framework"
        )
        assert "fastapi" not in server_lower, (
            "server.py must not use the third-party FastAPI framework"
        )

        # --- index.html: exactly one D3 v7 CDN <script> ---
        assert index_html.count("d3.v7.min.js") == 1, (
            "index.html must reference the D3 v7 CDN bundle exactly once"
        )
        cdn_index = index_html.find("d3.v7.min.js")
        preceding = index_html[:cdn_index]
        assert preceding.rfind("<script") > preceding.rfind("</script>"), (
            "the D3 v7 CDN reference must appear inside a <script> tag"
        )

        # --- single self-contained page ---
        assert index_html.count("<!DOCTYPE html>") == 1, (
            "index.html must be a single self-contained page with exactly one "
            "<!DOCTYPE html> declaration"
        )

        # --- explicit SVG width/height attributes ---
        assert '.attr("width"' in index_html, (
            "index.html must set an explicit SVG width attribute"
        )
        assert '.attr("height"' in index_html, (
            "index.html must set an explicit SVG height attribute"
        )

        # --- TruthSet source-color map + node-radius formula ---
        assert "COLORS = { CUSTOMERS:" in index_html, (
            "index.html must embed the TruthSet source-color map"
        )
        assert "8 + node.record_count * 4" in index_html, (
            "index.html must embed the node-radius formula"
        )

        # --- no arrow function used as a D3 callback ---
        # The generated demo uses only function(){} callbacks; verified by
        # generating once and grepping — '=>' never appears in the output.
        assert "=>" not in index_html, (
            "index.html must use function(){} callbacks only — no arrow "
            "functions (=>) may appear in the generated output"
        )


# ---------------------------------------------------------------------------
# Property 4 — deterministic regeneration strategy (reuses generation params)
# ---------------------------------------------------------------------------


@st.composite
def st_regeneration_params(draw: st.DrawFn) -> tuple[str, int, int]:
    """Draw generation params plus a small re-run count N for Property 4.

    Reuses :func:`st_generation_params` for the ``output_dir`` name and ``port``,
    and draws a small ``n_reruns`` in ``[1, 4]`` — the number of times the emitted
    ``write_html.py`` is re-invoked after the initial generation.

    Args:
        draw: The Hypothesis draw callable.

    Returns:
        An ``(output_dir_name, port, n_reruns)`` tuple.
    """
    output_dir, port = draw(st_generation_params())
    n_reruns = draw(st.integers(min_value=1, max_value=4))
    return output_dir, port, n_reruns


class TestDeterministicRegeneration:
    """Property 4: regeneration is deterministic.

    Validates: Requirements 1.1 — for any output directory, generating the demo
    and then re-running the emitted ``write_html.py`` any number of times yields
    byte-identical ``index.html``, ``server.py``, and ``write_html.py``. The
    generated output is reproducible and never varies between runs.
    """

    # Feature: scaffold-visualization-specifics, Property 4: Regeneration is
    # deterministic
    @given(params=st_regeneration_params())
    def test_regeneration_is_byte_identical(
        self, params: tuple[str, int, int], tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """Re-running write_html.py N times keeps all artifacts byte-identical.

        Validates: Requirements 1.1.
        """
        output_name, port, n_reruns = params
        # Session-scoped factory yields a fresh, uniquely numbered working
        # directory per example (mirrors Property 2/3) so no repo files are
        # touched and the function-scoped tmp_path health check does not apply.
        work = tmp_path_factory.mktemp("deterministic_regen")
        out_dir = work / output_name
        progress_path = work / "progress.json"

        ok = generate_standalone_demo.generate_demo(
            output_dir=str(out_dir),
            progress_path=str(progress_path),
            port=port,
        )
        assert ok, "generate_demo must succeed to produce the initial artifacts"

        index_path = out_dir / "index.html"
        server_path = out_dir / "server.py"
        write_html_path = out_dir / "write_html.py"

        # Capture the initial bytes of every generated artifact.
        initial_index = index_path.read_bytes()
        initial_server = server_path.read_bytes()
        initial_write_html = write_html_path.read_bytes()

        # Re-run the emitted write_html.py N times, invoking it exactly the way
        # generate_demo does (subprocess with the current interpreter).
        for run in range(1, n_reruns + 1):
            result = subprocess.run(
                [sys.executable, str(write_html_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, (
                f"re-run {run} of write_html.py failed "
                f"(rc={result.returncode}): {result.stderr.strip()}"
            )

            # index.html is rewritten by write_html.py — it must be identical.
            assert index_path.read_bytes() == initial_index, (
                f"index.html changed on re-run {run} — regeneration is not "
                "deterministic"
            )
            # server.py and write_html.py are not rewritten by write_html.py;
            # assert they remain byte-identical to the initial capture.
            assert server_path.read_bytes() == initial_server, (
                f"server.py changed on re-run {run} — it must remain "
                "byte-identical across runs"
            )
            assert write_html_path.read_bytes() == initial_write_html, (
                f"write_html.py changed on re-run {run} — it must remain "
                "byte-identical across runs"
            )


# ---------------------------------------------------------------------------
# First-visualization guarantee consistency (example test, Req 3.3)
# ---------------------------------------------------------------------------


class TestFirstVisualizationConsistency:
    """First-visualization owed marker is cleared on success, kept on failure.

    Validates: Requirement 3.3 — ``generate_demo`` stays consistent with the
    ``module3-first-visualization-guarantee``: on successful generation it clears
    the journey-level owed marker with ``satisfied_by == "standalone_demo"``, and
    on a write failure it leaves the marker unchanged (still owed) so the deferred
    guarantee still applies. Reuses the existing first-visualization progress
    helpers in ``progress_utils``.
    """

    def test_success_clears_owed_marker(self, tmp_path: Path) -> None:
        """A successful generate_demo satisfies the owed marker via standalone_demo.

        Validates: Requirement 3.3.
        """
        progress_path = tmp_path / "progress.json"

        # Set up a progress file with the first visualization marked owed.
        progress_utils.mark_first_visualization_owed(
            reason="module_3_opt_out", progress_path=str(progress_path)
        )
        assert progress_utils.is_first_visualization_owed(
            progress_utils._read_progress(str(progress_path))
        ), "precondition: the first visualization must start owed"

        ok = generate_standalone_demo.generate_demo(
            output_dir=str(tmp_path / "web_service"),
            progress_path=str(progress_path),
            port=8080,
        )
        assert ok, "generate_demo must succeed when the output dir is writable"

        # The owed marker is now cleared/satisfied by the standalone demo.
        marker = progress_utils._read_progress(str(progress_path)).get(
            "first_visualization"
        )
        assert isinstance(marker, dict), "the first_visualization marker must persist"
        assert marker.get("status") == "satisfied", (
            "a successful generate_demo must satisfy the owed marker"
        )
        assert marker.get("satisfied_by") == "standalone_demo", (
            "the marker must record standalone_demo as the satisfying source"
        )
        assert not progress_utils.is_first_visualization_owed(
            progress_utils._read_progress(str(progress_path))
        ), "the first visualization must no longer be owed after success"

    def test_write_failure_leaves_owed_marker_unchanged(self, tmp_path: Path) -> None:
        """A simulated write failure returns False and preserves the owed marker.

        The write failure is simulated without touching production code: a regular
        FILE is created and ``output_dir`` is placed BENEATH that file. When
        ``generate_demo`` calls ``out.mkdir(parents=True, exist_ok=True)`` it
        raises ``OSError`` (a parent path component is not a directory), so
        ``generate_demo`` hits its ``except OSError`` fallback and returns False
        without clearing the owed marker.

        Validates: Requirement 3.3.
        """
        progress_path = tmp_path / "progress.json"

        # Set up a progress file with the first visualization marked owed.
        progress_utils.mark_first_visualization_owed(
            reason="module_3_opt_out", progress_path=str(progress_path)
        )
        assert progress_utils.is_first_visualization_owed(
            progress_utils._read_progress(str(progress_path))
        ), "precondition: the first visualization must start owed"

        # Create a FILE, then aim output_dir at a path BENEATH it so mkdir raises
        # OSError (a parent component is a file, not a directory).
        blocker_file = tmp_path / "blocker"
        blocker_file.write_text("not a directory", encoding="utf-8")
        unwritable_output_dir = blocker_file / "web_service"

        ok = generate_standalone_demo.generate_demo(
            output_dir=str(unwritable_output_dir),
            progress_path=str(progress_path),
            port=8080,
        )
        assert ok is False, (
            "generate_demo must return False when the output directory cannot "
            "be created"
        )

        # The owed marker is LEFT unchanged (still owed, never satisfied).
        marker = progress_utils._read_progress(str(progress_path)).get(
            "first_visualization"
        )
        assert isinstance(marker, dict), "the first_visualization marker must persist"
        assert marker.get("status") == "owed", (
            "a failed generate_demo must leave the owed marker unchanged"
        )
        assert marker.get("satisfied_by") is None, (
            "a failed generate_demo must not record any satisfying source"
        )
        assert progress_utils.is_first_visualization_owed(
            progress_utils._read_progress(str(progress_path))
        ), "the first visualization must still be owed after a write failure"


# ---------------------------------------------------------------------------
# Token-count consistency (smoke test, Req 2.2)
# ---------------------------------------------------------------------------

_STEERING_INDEX_FILE = (
    Path(__file__).resolve().parent.parent / "steering" / "steering-index.yaml"
)

# The reduced-file name is the key under both file_metadata and the module-03
# phase2-visualization phase entry in steering-index.yaml.
_REDUCED_FILE_NAME = "module-03-phase2-visualization.md"


class TestTokenCountConsistency:
    """The recorded token_count matches the value measured for the reduced file.

    Validates: Requirement 2.2 — after the steering reduction, the token counts
    recorded in ``steering-index.yaml`` for ``module-03-phase2-visualization.md``
    (both the ``file_metadata`` entry and the ``modules.3.phases.phase2-visualization``
    phase entry) reflect the reduced file. This smoke test measures the reduced
    file the same way the CI validator does — via
    ``measure_steering.calculate_token_count`` (``round(len(content) / 4)``) — and
    asserts the recorded values match exactly.
    """

    def test_file_metadata_token_count_matches_measured(self) -> None:
        """file_metadata token_count equals the measured count for the reduced file.

        Validates: Requirement 2.2.
        """
        measured = measure_steering.calculate_token_count(_STEERING_FILE)

        content = _STEERING_INDEX_FILE.read_text(encoding="utf-8")
        stored = measure_steering._parse_stored_metadata(content)
        assert stored is not None, (
            "steering-index.yaml must contain a file_metadata section"
        )
        assert _REDUCED_FILE_NAME in stored, (
            f"steering-index.yaml file_metadata must record {_REDUCED_FILE_NAME}"
        )
        recorded = stored[_REDUCED_FILE_NAME].get("token_count")
        assert recorded == measured, (
            f"file_metadata token_count for {_REDUCED_FILE_NAME} is {recorded} "
            f"but the measured count is {measured} — they must match after the "
            "steering reduction"
        )

    def test_phase_entry_token_count_matches_measured(self) -> None:
        """The phase entry token_count equals the measured count for the reduced file.

        Validates: Requirement 2.2.
        """
        measured = measure_steering.calculate_token_count(_STEERING_FILE)

        content = _STEERING_INDEX_FILE.read_text(encoding="utf-8")
        phase_entries = measure_steering._parse_phase_entries(content)
        matching = [e for e in phase_entries if e.filename == _REDUCED_FILE_NAME]
        assert matching, (
            f"steering-index.yaml must contain a phase entry for {_REDUCED_FILE_NAME}"
        )
        for entry in matching:
            assert entry.token_count == measured, (
                f"phase entry token_count for {_REDUCED_FILE_NAME} is "
                f"{entry.token_count} but the measured count is {measured} — they "
                "must match after the steering reduction"
            )
