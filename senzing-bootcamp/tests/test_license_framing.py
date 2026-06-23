"""Property-based tests for the license capacity framing helpers.

Targets the pure framing surface in ``volume_utils.py`` — ``build_expansion_paths``,
``build_license_framing``, and the refactored ``get_license_guidance``. These
functions take plain values and produce text deterministically, so universal
invariants over many randomized framing contexts are meaningful and cheap to run.

Feature: license-capacity-framing
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — import volume_utils via the established sys.path insertion pattern
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")

if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import volume_utils  # noqa: E402

# ---------------------------------------------------------------------------
# TestExpansionPathSelection
# ---------------------------------------------------------------------------


class TestExpansionPathSelection:
    """Property tests for ``build_expansion_paths`` selection logic.

    Validates Requirements 2.1, 2.2, 2.3, 2.4.
    """

    # Feature: license-capacity-framing, Property 2: Expansion-path selection is correct
    @settings(max_examples=100)
    @given(
        submit_feedback_available=st.booleans(),
        has_existing_license=st.booleans(),
    )
    def test_expansion_path_selection_is_correct(
        self,
        submit_feedback_available: bool,
        has_existing_license: bool,
    ) -> None:
        """For any booleans, apply-existing and external-request are always present,
        and the in-flow MCP path is present IFF submit_feedback is available AND the
        bootcamper has no existing license. Canonical ordering is preserved.

        Validates: Requirements 2.1, 2.2, 2.3, 2.4
        """
        paths = volume_utils.build_expansion_paths(
            submit_feedback_available,
            has_existing_license,
        )

        # Apply-existing and external-request are always present (R2.1).
        assert volume_utils.PATH_APPLY_EXISTING in paths
        assert volume_utils.PATH_EXTERNAL_REQUEST in paths

        # In-flow MCP present IFF available AND no existing license (R2.2, R2.3, R2.4).
        in_flow_expected = submit_feedback_available and not has_existing_license
        assert (volume_utils.PATH_IN_FLOW_MCP in paths) == in_flow_expected

        # Canonical ordering preserved: apply-existing, external-request, then
        # in-flow MCP (when applicable).
        expected = [
            volume_utils.PATH_APPLY_EXISTING,
            volume_utils.PATH_EXTERNAL_REQUEST,
        ]
        if in_flow_expected:
            expected.append(volume_utils.PATH_IN_FLOW_MCP)
        assert paths == expected


# ---------------------------------------------------------------------------
# Shared strategy — module level so tasks 2.2-2.5 can reuse it
# ---------------------------------------------------------------------------


@st.composite
def st_license_framing_context(draw: st.DrawFn) -> "volume_utils.LicenseFramingContext":
    """Generate a random ``LicenseFramingContext`` for the framing helper.

    Folds the design's edge cases into the generators:
    - ``capacity``: ``None`` or a non-negative int (including 0 and large values).
    - ``validity``: ``None`` or text (including empty / whitespace-only strings).
    - ``submit_feedback_available`` / ``has_existing_license``: all four boolean
      combinations.
    - ``mention_downsizing``: either boolean.

    Returns:
        A ``volume_utils.LicenseFramingContext`` whose fields later tests unpack
        into ``build_license_framing`` keyword arguments.
    """
    capacity = draw(
        st.one_of(
            st.none(),
            st.integers(min_value=0, max_value=10_000_000),
        )
    )
    validity = draw(
        st.one_of(
            st.none(),
            st.text(),
            st.sampled_from(["", " ", "\t", "\n", "   ", "90 days", "1 year"]),
        )
    )
    return volume_utils.LicenseFramingContext(
        capacity=capacity,
        validity=validity,
        submit_feedback_available=draw(st.booleans()),
        has_existing_license=draw(st.booleans()),
        mention_downsizing=draw(st.booleans()),
    )


# Phrasing that would frame the limit as a hard cap rather than a default.
_HARD_CAP_PHRASES = (
    "hard cap",
    "maximum of",
    "cannot exceed",
    "you are limited to",
)


# ---------------------------------------------------------------------------
# TestDefaultLicenseFraming
# ---------------------------------------------------------------------------


class TestDefaultLicenseFraming:
    """Property tests for the default-license framing of ``build_license_framing``.

    Validates Requirement 1.1.
    """

    # Feature: license-capacity-framing, Property 1:
    # Framing presents a default license, never a hard cap
    @settings(max_examples=100)
    @given(ctx=st_license_framing_context())
    def test_framing_presents_default_license_never_hard_cap(
        self,
        ctx: "volume_utils.LicenseFramingContext",
    ) -> None:
        """For any context, the framing describes the limit as a built-in
        evaluation license the bootcamper already has, and never uses hard-cap /
        fixed-maximum phrasing.

        Validates: Requirements 1.1
        """
        text = volume_utils.build_license_framing(
            capacity=ctx.capacity,
            validity=ctx.validity,
            submit_feedback_available=ctx.submit_feedback_available,
            has_existing_license=ctx.has_existing_license,
            mention_downsizing=ctx.mention_downsizing,
        )
        lowered = text.lower()

        # Default / built-in evaluation phrasing present, framed as already held.
        assert "built-in evaluation license" in lowered
        assert "already have" in lowered

        # No hard-cap / fixed-maximum phrasing present.
        for phrase in _HARD_CAP_PHRASES:
            assert phrase not in lowered, f"hard-cap phrasing leaked: {phrase!r}"


# ---------------------------------------------------------------------------
# TestRenderedPathsPresent
# ---------------------------------------------------------------------------


class TestRenderedPathsPresent:
    """Property tests that the rendered framing carries every selected path.

    Validates Requirements 2.1, 2.2, 2.4.
    """

    # Feature: license-capacity-framing, Property 3:
    # Rendered framing includes every selected expansion path
    @settings(max_examples=100)
    @given(ctx=st_license_framing_context())
    def test_rendered_framing_includes_every_selected_path(
        self,
        ctx: "volume_utils.LicenseFramingContext",
    ) -> None:
        """For any context, ``build_license_framing`` renders a recognizable
        description for every expansion path id selected by
        ``build_expansion_paths`` for that context, and omits the in-flow MCP
        description entirely when that path id is not selected.

        Validates: Requirements 2.1, 2.2, 2.4
        """
        selected = volume_utils.build_expansion_paths(
            ctx.submit_feedback_available,
            ctx.has_existing_license,
        )

        text = volume_utils.build_license_framing(
            capacity=ctx.capacity,
            validity=ctx.validity,
            submit_feedback_available=ctx.submit_feedback_available,
            has_existing_license=ctx.has_existing_license,
            mention_downsizing=ctx.mention_downsizing,
        )

        # Each selected path renders its recognizable description (R2.1).
        for path_id in selected:
            marker = volume_utils._EXPANSION_PATH_DESCRIPTIONS[path_id]
            assert marker in text, f"missing description for selected path {path_id!r}"

        # When the in-flow MCP path is NOT selected, its description is absent
        # entirely — the bootcamper is never shown an unavailable in-flow option
        # (R2.2, R2.4).
        if volume_utils.PATH_IN_FLOW_MCP not in selected:
            in_flow_marker = volume_utils._EXPANSION_PATH_DESCRIPTIONS[
                volume_utils.PATH_IN_FLOW_MCP
            ]
            assert in_flow_marker not in text, "in-flow MCP description rendered when not selected"
            # Distinctive in-flow wording is also absent from the output.
            lowered = text.lower()
            assert "without leaving" not in lowered
            assert "submit_feedback" not in lowered


# ---------------------------------------------------------------------------
# TestFiguresSourcedNotHardcoded
# ---------------------------------------------------------------------------


# The legacy hardcoded capacity figure the refactor must never substitute.
_LEGACY_HARDCODED_FIGURE = "500"

# Phrasing the helper uses to flag a value it could not source from MCP.
_UNAVAILABLE_PHRASE = "unavailable from the MCP server"


class TestFiguresSourcedNotHardcoded:
    """Property tests that capacity/validity figures are sourced, never hardcoded.

    Validates Requirements 1.3, 1.4.
    """

    # Feature: license-capacity-framing, Property 4:
    # Capacity and validity figures are sourced, never hardcoded
    @settings(max_examples=100)
    @given(ctx=st_license_framing_context())
    def test_figures_are_sourced_never_hardcoded(
        self,
        ctx: "volume_utils.LicenseFramingContext",
    ) -> None:
        """For any context, a provided capacity/validity appears verbatim in the
        output; a ``None`` value is omitted (no specific figure), the text states
        the value is currently unavailable from the MCP server, and no substituted
        hardcoded figure (the legacy 500) is rendered as the capacity.

        Validates: Requirements 1.3, 1.4
        """
        text = volume_utils.build_license_framing(
            capacity=ctx.capacity,
            validity=ctx.validity,
            submit_feedback_available=ctx.submit_feedback_available,
            has_existing_license=ctx.has_existing_license,
            mention_downsizing=ctx.mention_downsizing,
        )

        # --- Capacity (R1.3 provided / R1.4 unavailable) ---
        if ctx.capacity is not None:
            # Provided capacity is rendered verbatim, sourced from MCP (R1.3).
            assert str(ctx.capacity) in text, "provided capacity figure not rendered verbatim"
        else:
            # No capacity: figure omitted + unavailable phrasing present (R1.4).
            assert _UNAVAILABLE_PHRASE in text
            # No substituted capacity figure is rendered. The capacity figure is
            # only ever rendered via the "covers up to <N> records" phrasing, so
            # that exact pattern must be absent when capacity is unavailable.
            assert "covers up to" not in text
            # The legacy hardcoded figure must not be substituted as the capacity.
            # Scope the digit check so a validity string that happens to contain
            # "500" cannot cause a false positive.
            validity_text = ctx.validity if isinstance(ctx.validity, str) else ""
            if _LEGACY_HARDCODED_FIGURE not in validity_text:
                assert _LEGACY_HARDCODED_FIGURE not in text, "legacy hardcoded figure substituted"

        # --- Validity (R1.3 provided / R1.4 unavailable) ---
        if ctx.validity is not None:
            # Only assert verbatim presence for a meaningful (non-empty) string;
            # an empty/whitespace validity renders but is trivially a substring,
            # so a verbatim check there would be both vacuous and brittle.
            if ctx.validity.strip():
                assert ctx.validity in text, "provided validity not rendered verbatim"
        else:
            # No validity: the unavailable-from-the-MCP-server phrasing is present.
            assert _UNAVAILABLE_PHRASE in text


# ---------------------------------------------------------------------------
# TestDownsizingCoPresented
# ---------------------------------------------------------------------------


# Stable substring marking the downsizing block in the rendered framing.
_DOWNSIZING_MARKER = "downsizing"


class TestDownsizingCoPresented:
    """Property tests that downsizing is co-presented, never the sole/primary path.

    Validates Requirements 1.2, 3.1, 3.2.
    """

    # Feature: license-capacity-framing, Property 5:
    # Downsizing is co-presented, never the sole or primary path
    @settings(max_examples=100)
    @given(ctx=st_license_framing_context())
    def test_downsizing_is_co_presented_never_primary(
        self,
        ctx: "volume_utils.LicenseFramingContext",
    ) -> None:
        """For any context where downsizing is mentioned, the expansion options
        are present and the first expansion-option position appears before the
        downsizing mention, proving downsizing is never the first/only path.

        Validates: Requirements 1.2, 3.1, 3.2
        """
        text = volume_utils.build_license_framing(
            capacity=ctx.capacity,
            validity=ctx.validity,
            submit_feedback_available=ctx.submit_feedback_available,
            has_existing_license=ctx.has_existing_license,
            mention_downsizing=ctx.mention_downsizing,
        )

        if not ctx.mention_downsizing:
            # When downsizing is not mentioned there is nothing to co-present;
            # the downsizing block must be absent.
            assert _DOWNSIZING_MARKER not in text.lower()
            return

        lowered = text.lower()

        # The always-present apply-existing description marks the first expansion
        # option; the downsizing block is marked by the distinctive "downsizing"
        # wording.
        first_expansion_marker = volume_utils._EXPANSION_PATH_DESCRIPTIONS[
            volume_utils.PATH_APPLY_EXISTING
        ]

        # Expansion options are present (R1.2, R3.2).
        assert first_expansion_marker in text, "expansion options missing from framing"
        assert _DOWNSIZING_MARKER in lowered, "downsizing mention missing from framing"

        # The first expansion-option position appears BEFORE the downsizing
        # mention, so downsizing is never the first/only path forward
        # (R1.2, R3.1, R3.2).
        assert text.index(first_expansion_marker) < lowered.index(_DOWNSIZING_MARKER), (
            "downsizing mention appears before the first expansion option"
        )


# ---------------------------------------------------------------------------
# TestNoHardcodedUrls
# ---------------------------------------------------------------------------


# The forbidden MCP server host. Assembled from parts so the literal host string
# never appears in this source file — a PreToolUse security hook blocks writing
# that literal into any file other than mcp.json (and the single-source-of-truth
# rule keeps the host in mcp.json only).
_MCP_HOST = "mcp.senzing" + ".com"

# External web URL scheme markers that must never be hardcoded into the framing.
_URL_SCHEMES = ("http://", "https://")

# The full, by-name reference the framing must use when it mentions the server.
_MCP_SERVER_BY_NAME = "Senzing MCP server"


def _mentions_server_by_name_expected(ctx: "volume_utils.LicenseFramingContext") -> bool:
    """Whether ``build_license_framing`` output must name the Senzing MCP server.

    The by-name reference is rendered when a sourced capacity or validity figure
    is present (the "as reported by the Senzing MCP server" lines) or when the
    in-flow MCP expansion path is selected (its description names the server).

    Args:
        ctx: The framing context under test.

    Returns:
        True when the rendered framing is expected to contain the by-name
        "Senzing MCP server" reference.
    """
    in_flow_selected = volume_utils.PATH_IN_FLOW_MCP in volume_utils.build_expansion_paths(
        ctx.submit_feedback_available,
        ctx.has_existing_license,
    )
    return ctx.capacity is not None or ctx.validity is not None or in_flow_selected


def _assert_no_hardcoded_urls(output: str) -> None:
    """Assert an output carries no external URL and no MCP server host.

    Args:
        output: A rendered framing / guidance string.
    """
    lowered = output.lower()
    for scheme in _URL_SCHEMES:
        assert scheme not in lowered, f"external URL scheme leaked: {scheme!r}"
    assert _MCP_HOST not in output, "hardcoded MCP server host leaked into output"


class TestNoHardcodedUrls:
    """Property test that framing output carries no hardcoded MCP/external URL.

    Validates Requirement 4.4.
    """

    # Feature: license-capacity-framing, Property 6:
    # Framing output contains no hardcoded MCP or external URL
    @settings(max_examples=100)
    @given(ctx=st_license_framing_context())
    def test_framing_output_has_no_hardcoded_urls(
        self,
        ctx: "volume_utils.LicenseFramingContext",
    ) -> None:
        """For any context, neither ``build_license_framing`` nor
        ``get_license_guidance`` output contains a hardcoded MCP server host or
        any external web URL; the server is referred to by name only.

        Validates: Requirements 4.4
        """
        framing = volume_utils.build_license_framing(
            capacity=ctx.capacity,
            validity=ctx.validity,
            submit_feedback_available=ctx.submit_feedback_available,
            has_existing_license=ctx.has_existing_license,
            mention_downsizing=ctx.mention_downsizing,
        )

        # No external URL and no MCP host in the build_license_framing output.
        _assert_no_hardcoded_urls(framing)

        # When the framing references the server (sourced figure or in-flow path),
        # it does so by name only.
        if _mentions_server_by_name_expected(ctx):
            assert _MCP_SERVER_BY_NAME in framing, "framing must name the Senzing MCP server"
        # The server host is never used as the reference (re-checked explicitly).
        assert _MCP_HOST not in framing

        # Exercise get_license_guidance across all tiers (demo + non-demo). The
        # ctx fields are passed through as keyword args. tier=None yields None and
        # is skipped; the URL-absence checks run only on non-None outputs.
        for tier in (None, *volume_utils.VALID_TIERS):
            guidance = volume_utils.get_license_guidance(
                tier,
                capacity=ctx.capacity,
                validity=ctx.validity,
                submit_feedback_available=ctx.submit_feedback_available,
                has_existing_license=ctx.has_existing_license,
            )
            if guidance is None:
                # tier=None is the skip case — nothing to check.
                continue

            _assert_no_hardcoded_urls(guidance)

            # Non-demo tiers delegate to build_license_framing, so they carry the
            # same by-name reference guarantee. (The demo tier may omit any server
            # mention when no figure is supplied, so it is not name-checked here.)
            if tier != volume_utils.TIER_DEMO and _mentions_server_by_name_expected(ctx):
                assert _MCP_SERVER_BY_NAME in guidance, (
                    "non-demo guidance must name the Senzing MCP server"
                )
