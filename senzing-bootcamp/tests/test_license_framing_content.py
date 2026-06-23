"""Content-validation tests for the license-capacity-framing reframing.

Task 6.1 of the ``license-capacity-framing`` spec. These tests guard the markdown
touchpoints and cross-document consistency that the pure-helper property tests
cannot express. They assert that everywhere the bootcamp surfaces the built-in
500-record evaluation license it is framed as a *default the bootcamper already
has* plus *expansion paths*, with downsizing presented as one option rather than
the only path forward.

The assertions are deliberately tolerant of benign wording changes — each required
concept is satisfied by any one of several accepted phrasings (a "phrase group") —
but specific enough to fail if a whole framing concept were removed or if hard-cap
phrasing or an MCP-server URL were reintroduced into an edited steering file.

Definitions (per the design and task):
- "hard-cap phrasing" = the substrings "hard cap", "maximum of", "cannot exceed",
  "you are limited to".
- For edited steering files, the MCP server host must never appear — the URL lives
  only in ``mcp.json``. ``module-04-data-collection.md`` legitimately carries
  pre-existing external data-source URLs (CORD, the free-data GitHub collection,
  illustrative vendor-API examples) and a support email address, so its URL check
  is scoped to the absence of the MCP server host specifically rather than a global
  URL ban. ``module-06-phaseA-build-loading.md`` carries no URLs at all, so it is
  checked for the absence of any external web URL.

The MCP server host literal is assembled from parts in this module so the test
itself never embeds the forbidden string (consistent with the single-source-of-truth
rule that the host appears only in ``mcp.json``).

**Validates: Requirements 2.5, 3.1, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4**
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# This file lives in senzing-bootcamp/tests/.
_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent
_STEERING_DIR = _BOOTCAMP_DIR / "steering"
_DOCS_DIR = _BOOTCAMP_DIR / "docs"

_MODULE_04_STEERING = _STEERING_DIR / "module-04-data-collection.md"
_MODULE_06_PHASEA = _STEERING_DIR / "module-06-phaseA-build-loading.md"
_MODULE_01_DISCOVERY = _STEERING_DIR / "module-01-phase1-discovery.md"

_QUICK_START = _DOCS_DIR / "guides" / "QUICK_START.md"
_POWER = _BOOTCAMP_DIR / "POWER.md"
_MODULE_2_DOC = _DOCS_DIR / "modules" / "MODULE_2_SDK_SETUP.md"
_MODULE_4_DOC = _DOCS_DIR / "modules" / "MODULE_4_DATA_COLLECTION.md"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Hard-cap phrasing the reframing must avoid (design Property 1 / task definition).
_HARD_CAP_PHRASES: tuple[str, ...] = (
    "hard cap",
    "maximum of",
    "cannot exceed",
    "you are limited to",
)

# The MCP server host must never appear in an edited steering file (single source
# of truth is mcp.json). Assembled from parts so this file never embeds the literal.
_MCP_HOST: str = ".".join(("mcp", "senzing", "com"))

# Any external web URL.
_URL_RE = re.compile(r"https?://", re.IGNORECASE)


def _read(path: Path) -> str:
    """Return a file's UTF-8 text.

    Args:
        path: File to read.

    Returns:
        The file's contents.
    """
    return path.read_text(encoding="utf-8")


def _read_lower(path: Path) -> str:
    """Return a file's UTF-8 text, lower-cased for case-insensitive matching.

    Args:
        path: File to read.

    Returns:
        The file's lower-cased contents.
    """
    return _read(path).lower()


def _assert_groups_present(
    text_lower: str, groups: tuple[tuple[str, ...], ...], label: str
) -> None:
    """Assert at least one phrasing from every phrase group is present.

    Args:
        text_lower: Lower-cased file text to search.
        groups: Tuple of phrase groups; each group is a tuple of accepted
            (already lower-cased) alternative phrasings.
        label: Human-readable label for failure messages.
    """
    for group in groups:
        assert any(phrase in text_lower for phrase in group), (
            f"{label}: missing required framing concept.\n"
            f"Expected at least one of these phrasings: {list(group)}"
        )


def _assert_no_hard_cap(text_lower: str, label: str) -> None:
    """Assert none of the hard-cap phrases appear in the text.

    Args:
        text_lower: Lower-cased file text to search.
        label: Human-readable label for failure messages.
    """
    found = [phrase for phrase in _HARD_CAP_PHRASES if phrase in text_lower]
    assert not found, (
        f"{label}: hard-cap phrasing must not be present, but found: {found}. "
        "The limit must be framed as a default evaluation license with expansion "
        "paths, never as a fixed maximum."
    )


# ---------------------------------------------------------------------------
# TestFilesExist
# ---------------------------------------------------------------------------


class TestFilesExist:
    """Every reframed target file is present and non-empty.

    A renamed or deleted target would silently skip its content checks, so the
    set of files is pinned here first.

    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    """

    @pytest.mark.parametrize(
        "path",
        [
            _MODULE_04_STEERING,
            _MODULE_06_PHASEA,
            _MODULE_01_DISCOVERY,
            _QUICK_START,
            _POWER,
            _MODULE_2_DOC,
            _MODULE_4_DOC,
        ],
        ids=lambda p: p.name,
    )
    def test_target_file_present(self, path: Path) -> None:
        """The target file exists and is non-empty."""
        assert path.is_file(), f"Target file missing: {path}"
        assert _read(path).strip(), f"Target file is empty: {path}"


# ---------------------------------------------------------------------------
# TestModule4SteeringFraming
# ---------------------------------------------------------------------------


class TestModule4SteeringFraming:
    """Module 4 data-collection steering uses default+expansion framing.

    The steering must present the 500-record limit as a built-in evaluation license
    the bootcamper already has, carry the expansion paths, keep the full-dataset
    path (no mandatory downsizing gate), and retain the sampling / CORD-subset
    steps — with downsizing offered as one option, not the only path.

    **Validates: Requirements 3.1, 3.3, 3.4, 4.1**
    """

    def test_presents_default_license_with_expansion_paths(self) -> None:
        """Frames the limit as a default license and lists the expansion paths."""
        text = _read_lower(_MODULE_04_STEERING)
        groups: tuple[tuple[str, ...], ...] = (
            # Default / built-in evaluation license the bootcamper already has.
            ("built-in evaluation license",),
            ("already has", "by default"),
            # A choice, not a wall.
            ("not a wall", "as a choice", "one option among several"),
            # Expansion path: apply an existing license.
            ("apply an existing license",),
            # Expansion path: external request channel.
            ("external channel", "external request", "through senzing support"),
            # Expansion path: in-flow via the Senzing MCP server.
            ("in-flow via the senzing mcp server", "in-flow", "request one in-flow"),
        )
        _assert_groups_present(text, groups, "module-04 steering (framing)")

    def test_contains_no_hard_cap_phrasing(self) -> None:
        """Module 4 steering contains no hard-cap phrasing."""
        _assert_no_hard_cap(_read_lower(_MODULE_04_STEERING), "module-04 steering")

    def test_retains_full_dataset_path_without_mandatory_downsizing(self) -> None:
        """Keeps the full-dataset path with no mandatory downsizing gate."""
        text = _read_lower(_MODULE_04_STEERING)
        groups: tuple[tuple[str, ...], ...] = (
            # Bootcamper may keep the full dataset.
            ("keep the full dataset", "keep their full dataset", "keep your full dataset"),
            # No requirement to reduce the dataset (no mandatory downsizing gate).
            (
                "there is no requirement to reduce the dataset",
                "no requirement to reduce",
                "without requiring a reduced dataset",
            ),
            # Downsizing is one option, never the only path.
            ("one option",),
            ("never the only path", "not the only path", "not as the only"),
        )
        _assert_groups_present(text, groups, "module-04 steering (full-dataset path)")

    def test_retains_sampling_and_cord_subset_steps(self) -> None:
        """Retains the sampling / CORD-subset downsizing workflow."""
        text = _read_lower(_MODULE_04_STEERING)
        groups: tuple[tuple[str, ...], ...] = (
            ("sampling",),
            ("cord subset", "cord-subset"),
            ("smaller substitute",),
        )
        _assert_groups_present(text, groups, "module-04 steering (downsizing steps)")


# ---------------------------------------------------------------------------
# TestSteeringFramingConsistency
# ---------------------------------------------------------------------------


class TestSteeringFramingConsistency:
    """Module 6 (Phase A) and Module 1 discovery use consistent framing.

    Both must frame the limit as a default evaluation license, use the same
    ``submit_feedback`` availability gate (via ``get_capabilities`` with the 30s
    window), and route an existing-license holder to the apply-an-existing-license
    path while omitting the in-flow MCP option.

    **Validates: Requirements 2.5, 4.2**
    """

    def test_module6_phaseA_default_license_framing(self) -> None:
        """Module 6 Phase A frames licensing as a default the bootcamper has."""
        text = _read_lower(_MODULE_06_PHASEA)
        groups: tuple[tuple[str, ...], ...] = (
            ("built-in evaluation license",),
            ("default the bootcamper already has", "already has", "never as a hard cap"),
            ("apply an existing license",),
            ("external channel", "external request"),
            ("in-flow via the senzing mcp server", "in-flow"),
        )
        _assert_groups_present(text, groups, "module-06 phaseA (framing)")

    def test_module6_phaseA_submit_feedback_gate(self) -> None:
        """Module 6 Phase A gates the in-flow path on submit_feedback availability."""
        text = _read_lower(_MODULE_06_PHASEA)
        groups: tuple[tuple[str, ...], ...] = (
            ("submit_feedback",),
            ("get_capabilities",),
            # The 30-second availability window, consistent with Module 1.
            ("30s", "30 second"),
        )
        _assert_groups_present(text, groups, "module-06 phaseA (availability gate)")

    def test_module6_phaseA_existing_license_routing(self) -> None:
        """Module 6 Phase A routes existing-license holders to apply-existing."""
        text = _read_lower(_MODULE_06_PHASEA)
        groups: tuple[tuple[str, ...], ...] = (
            ("already has a license", "already has a senzing license"),
            ("apply-an-existing-license", "apply an existing license"),
            # The in-flow option is omitted for existing-license holders.
            ("omit the in-flow", "omit the in flow"),
        )
        _assert_groups_present(text, groups, "module-06 phaseA (existing-license routing)")

    def test_module1_discovery_availability_gate(self) -> None:
        """Module 1 discovery keeps the submit_feedback availability gate."""
        text = _read_lower(_MODULE_01_DISCOVERY)
        groups: tuple[tuple[str, ...], ...] = (
            ("built-in evaluation license", "built-in 500-record evaluation"),
            ("submit_feedback",),
            ("get_capabilities",),
            ("30 second", "30s"),
        )
        _assert_groups_present(text, groups, "module-01 discovery (availability gate)")

    def test_module1_discovery_existing_license_routing(self) -> None:
        """Module 1 discovery routes existing-license holders to apply-existing."""
        text = _read_lower(_MODULE_01_DISCOVERY)
        groups: tuple[tuple[str, ...], ...] = (
            ("already have a senzing license", "already has a senzing license"),
            ("apply-an-existing-license", "apply an existing license"),
            ("omit the in-flow", "omit the in flow"),
        )
        _assert_groups_present(text, groups, "module-01 discovery (existing-license routing)")


# ---------------------------------------------------------------------------
# TestUserFacingDocsFraming
# ---------------------------------------------------------------------------


class TestUserFacingDocsFraming:
    """User-facing docs present the limit as a default with expansion options.

    QUICK_START, POWER, MODULE_2_SDK_SETUP, and MODULE_4_DATA_COLLECTION must each
    describe the built-in evaluation license as a default the bootcamper already
    has, point to the expansion paths, and avoid hard-cap phrasing.

    **Validates: Requirements 4.1, 4.3**
    """

    # (label, path, required phrase groups). Each group lists accepted phrasings.
    _DOC_CASES: tuple[tuple[str, Path, tuple[tuple[str, ...], ...]], ...] = (
        (
            "QUICK_START.md",
            _QUICK_START,
            (
                ("built-in evaluation license",),
                ("you already have", "already have"),
                ("you have options", "need to process more"),
                ("apply an existing senzing license", "apply an existing license"),
                ("through senzing support", "external", "senzing support"),
                ("in-flow", "request one in-flow"),
            ),
        ),
        (
            "POWER.md",
            _POWER,
            (
                ("built-in evaluation license",),
                ("you already have", "already have"),
                ("you have options", "need to process more"),
                ("apply an existing senzing license", "apply an existing license"),
                ("through senzing support", "external", "senzing support"),
                ("in-flow", "request one in-flow"),
            ),
        ),
        (
            "MODULE_2_SDK_SETUP.md",
            _MODULE_2_DOC,
            (
                ("built-in evaluation license you already have", "built-in evaluation license"),
                # Keeps the factual SENZ9000-at-501 explanation.
                ("senz9000",),
                # Frames the figure as a default, not a wall.
                ("a default, not a wall", "not a wall", "is a default"),
                ("apply an existing senzing license", "apply an existing license"),
                (
                    "through senzing support",
                    "request an evaluation license through senzing support",
                ),
                ("in-flow", "request one in-flow"),
                # Downsizing is one option among several.
                ("just one option", "one option"),
            ),
        ),
        (
            "MODULE_4_DATA_COLLECTION.md",
            _MODULE_4_DOC,
            (
                ("built-in evaluation license you already have", "built-in evaluation license"),
                ("keep your full dataset and expand", "keep your full dataset"),
                ("work with a smaller slice", "smaller slice"),
                ("apply an existing senzing license", "apply an existing license"),
                ("through senzing support", "senzing support"),
                ("in-flow", "request one in-flow"),
                ("only ever one option", "one option"),
            ),
        ),
    )

    @pytest.mark.parametrize(
        "label, path, groups", _DOC_CASES, ids=[c[0] for c in _DOC_CASES]
    )
    def test_doc_presents_default_with_expansion(
        self, label: str, path: Path, groups: tuple[tuple[str, ...], ...]
    ) -> None:
        """The doc frames the limit as a default with expansion options."""
        _assert_groups_present(_read_lower(path), groups, label)

    @pytest.mark.parametrize(
        "label, path",
        [(c[0], c[1]) for c in _DOC_CASES],
        ids=[c[0] for c in _DOC_CASES],
    )
    def test_doc_contains_no_hard_cap_phrasing(self, label: str, path: Path) -> None:
        """The doc contains no hard-cap phrasing."""
        _assert_no_hard_cap(_read_lower(path), label)


# ---------------------------------------------------------------------------
# TestEditedSteeringNoMcpUrls
# ---------------------------------------------------------------------------


class TestEditedSteeringNoMcpUrls:
    """Edited steering files contain no hardcoded MCP/external URLs.

    The MCP server URL is the single source of truth in ``mcp.json`` and must not
    leak into steering text. ``module-04-data-collection.md`` carries pre-existing
    external data-source URLs (CORD, free-data, illustrative vendor-API examples),
    so its check is scoped to the absence of the MCP server host specifically.
    ``module-06-phaseA-build-loading.md`` carries no URLs, so it is checked for the
    absence of both the MCP server host and any external web URL.

    **Validates: Requirements 4.4**
    """

    def test_module4_steering_has_no_mcp_server_url(self) -> None:
        """Module 4 steering never names the MCP server URL (only by name)."""
        text = _read_lower(_MODULE_04_STEERING)
        assert _MCP_HOST not in text, (
            f"module-04 steering must not contain the MCP server host "
            f"({_MCP_HOST}); refer to the Senzing MCP server by name only "
            "(URL lives in mcp.json)."
        )
        # Positive check: it should still reference the Senzing MCP server by name.
        assert "senzing mcp server" in text, (
            "module-04 steering should refer to 'the Senzing MCP server' by name."
        )

    def test_module6_phaseA_has_no_mcp_server_url(self) -> None:
        """Module 6 Phase A never names the MCP server URL (only by name)."""
        text = _read_lower(_MODULE_06_PHASEA)
        assert _MCP_HOST not in text, (
            f"module-06 phaseA must not contain the MCP server host ({_MCP_HOST}); "
            "refer to the Senzing MCP server by name only (URL lives in mcp.json)."
        )
        assert "senzing mcp server" in text, (
            "module-06 phaseA should refer to 'the Senzing MCP server' by name."
        )

    def test_module6_phaseA_has_no_external_web_url(self) -> None:
        """Module 6 Phase A contains no external web URL.

        The ``#[[file:...]]`` include syntax and ``mcp.json`` path references are
        allowed; neither is an ``http(s)://`` URL, so a plain scheme search is a
        robust check for this file (which legitimately carries no URLs).
        """
        text = _read(_MODULE_06_PHASEA)
        matches = _URL_RE.findall(text)
        assert not matches, (
            f"module-06 phaseA must not contain external web URLs, but found "
            f"{len(matches)} occurrence(s) of an http(s):// scheme."
        )
