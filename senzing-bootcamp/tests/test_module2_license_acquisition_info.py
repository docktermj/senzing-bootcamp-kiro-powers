"""Example-based tests for the Module 2 Step 5a license-acquisition info.

Validates that the upfront Module 2 Step 5a explanation in
`steering/module-02-sdk-setup.md` (subsection
`### 5a. Explain the built-in evaluation license`) surfaces the in-flow MCP
license-request path alongside the apply-existing and Senzing-support paths,
carries the availability caveat on the in-flow path only, stays informational
(no pointing question, no STOP), directs selection/execution to the Step 5c
no-license branch, and keeps license figures MCP-sourced — without drifting
from the Step 5c branch and without hardcoding the MCP server URL or license
figures.

This feature is guidance/documentation-only, so verification is example-based
guidance validation (stdlib + region extraction), consistent with
`test_license_request_option.py`. No property-based tests are used.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1,
3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4**
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_MODULE_02_FILE: Path = _STEERING_DIR / "module-02-sdk-setup.md"

# Read the steering file content once at module level for all test classes.
_CONTENT: str = _MODULE_02_FILE.read_text(encoding="utf-8")

# The MCP server URL must live only in mcp.json. Built from parts here so this
# test module does not itself contain the literal URL.
_MCP_URL: str = "mcp." + "senzing.com"


# ---------------------------------------------------------------------------
# Region extraction helpers
# ---------------------------------------------------------------------------


def _extract_region(start_marker: str, end_marker: str) -> str:
    """Extract content between two ``###`` sub-step headers.

    The Module 2 Step 5 sub-steps are ``###`` headers (e.g.
    ``### 5a. Explain the built-in evaluation license``). The region is bounded
    by the first line containing ``start_marker`` and the next line containing
    ``end_marker``.

    Args:
        start_marker: Substring identifying the region's opening sub-step.
        end_marker: Substring identifying the following sub-step.

    Returns:
        The text from the start marker up to (but excluding) the end marker.
    """
    lines = _CONTENT.split("\n")
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        if start is None and start_marker in line:
            start = i
        elif start is not None and end_marker in line:
            end = i
            break
    assert start is not None, f"Could not find start marker {start_marker!r}"
    assert end is not None, f"Could not find end marker {end_marker!r} after start"
    return "\n".join(lines[start:end])


def _extract_5a_region() -> str:
    """Extract the Step 5a built-in-evaluation-license explanation block."""
    return _extract_region(
        "### 5a. Explain the built-in evaluation license",
        "### 5b. Ask about the bootcamper's license situation",
    )


def _extract_5c_region() -> str:
    """Extract the Step 5c handle-the-response block (consistency anchor)."""
    return _extract_region(
        "### 5c. Handle the response",
        "### 5d. Configure LICENSEFILE in engine config",
    )


def _extract_numbered_path_line(region: str, prefix: str) -> str:
    """Return the single numbered list item line beginning with ``prefix``.

    The three Step 5a acquisition paths are single-line numbered list items
    (e.g. ``1. **Request a temporary evaluation license ...``). This isolates
    one path's text so caveat scoping can be checked per path.

    Args:
        region: The region text to search within.
        prefix: The line prefix identifying the desired numbered item.

    Returns:
        The full text of the matching line.
    """
    for line in region.split("\n"):
        if line.startswith(prefix):
            return line
    raise AssertionError(f"Could not find a path line starting with {prefix!r}")


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestStep5aInFlowOption:
    """Step 5a presents the in-flow MCP license-request path.

    Validates: Requirements 1.1, 1.3
    """

    def test_in_flow_path_presented(self) -> None:
        """5a presents the in-flow path for obtaining a temporary evaluation license.

        Validates: Requirement 1.1
        """
        region = _extract_5a_region().lower()
        assert "in-flow" in region, "Step 5a must present the in-flow path"
        assert "mcp server" in region, "Step 5a must present the path through the MCP server"
        assert "temporary evaluation license" in region, (
            "Step 5a must frame it as a temporary evaluation license path"
        )

    def test_in_flow_names_submit_feedback_and_license_request_category(self) -> None:
        """5a states the path uses submit_feedback with the license_request category.

        Validates: Requirement 1.3
        """
        region = _extract_5a_region()
        lower = region.lower()
        assert "submit_feedback" in region, (
            "Step 5a must name the submit_feedback MCP tool"
        )
        assert "license_request" in region, (
            "Step 5a must name the license_request category"
        )
        assert "category" in lower, (
            "Step 5a must describe license_request as the invocation category"
        )


class TestStep5aThreePaths:
    """Step 5a names all three acquisition paths the Step 5c branch offers.

    Validates: Requirements 1.2, 3.5
    """

    def test_all_three_paths_named(self) -> None:
        """5a names the in-flow, apply-existing, and support paths.

        Validates: Requirement 1.2
        """
        region = _extract_5a_region().lower()
        # In-flow MCP request path
        assert "through the mcp server (in-flow)" in region, (
            "Step 5a must name the in-flow MCP request path"
        )
        # Apply-an-existing-license path
        assert "apply a license you already have" in region, (
            "Step 5a must name the apply-an-existing-license path"
        )
        assert "licenses/g2.lic" in region, (
            "Apply-existing path must reference placing the license at licenses/g2.lic"
        )
        # Support request path
        assert "senzing support" in region, (
            "Step 5a must name the Senzing support request path"
        )

    def test_no_path_absent_from_step_5c_branch(self) -> None:
        """The three Step 5a paths are the same three Step 5c offers; no extra path.

        Validates: Requirement 3.5
        """
        region_5a = _extract_5a_region().lower()
        region_5c = _extract_5c_region().lower()
        # Each Step 5a path concept must also appear in the Step 5c branch.
        assert "in-flow" in region_5a and "in-flow" in region_5c, (
            "The in-flow path must appear in both Step 5a and the Step 5c branch"
        )
        assert "already have" in region_5a and "existing license" in region_5c, (
            "The apply-existing path must appear in both Step 5a and the Step 5c branch"
        )
        assert "support" in region_5a and (
            "external channel" in region_5c or "support" in region_5c
        ), "The support/external request path must appear in both Step 5a and Step 5c"
        # Step 5a presents exactly three numbered acquisition paths — no extra path.
        numbered = re.findall(r"^\d+\.\s+\*\*", _extract_5a_region(), re.MULTILINE)
        assert len(numbered) == 3, (
            f"Step 5a must name exactly three acquisition paths, found {len(numbered)}"
        )


class TestStep5aInformationalOnly:
    """Step 5a stays informational — no pointing question, no STOP, no selection.

    Validates: Requirements 1.4, 3.3
    """

    def test_no_pointing_question_in_5a_region(self) -> None:
        """The 5a region contains no pointing question (👉).

        Validates: Requirements 1.4, 3.3
        """
        region = _extract_5a_region()
        assert "👉" not in region, (
            "Step 5a is informational only and must not contain a pointing question (👉)"
        )

    def test_no_stop_marker_in_5a_region(self) -> None:
        """The 5a region contains no STOP marker (🛑 emoji or STOP instruction).

        Validates: Requirements 1.4, 3.3
        """
        region = _extract_5a_region()
        assert "🛑" not in region, "Step 5a must not contain a STOP emoji (🛑)"
        assert not re.search(r"\bSTOP\b", region), (
            "Step 5a must not contain a STOP instruction"
        )

    def test_5a_marks_mention_informational(self) -> None:
        """5a frames the acquisition-path mention as informational only.

        Validates: Requirements 1.4, 3.3
        """
        region = _extract_5a_region().lower()
        assert "informational only" in region, (
            "Step 5a must frame the acquisition-path mention as informational only"
        )
        assert "nothing needs to be selected here" in region, (
            "Step 5a must state nothing needs to be selected at Step 5a"
        )

    def test_module_pointing_question_count_unchanged(self) -> None:
        """The module-wide pointing-question (👉) count is unchanged (2).

        Step 3 EULA and Step 5b each carry one pointing question; Step 5a adds
        none.

        Validates: Requirements 1.4, 3.3
        """
        count = _CONTENT.count("👉")
        assert count == 2, (
            f"Module should have exactly 2 pointing questions (👉), found {count}"
        )

    def test_module_stop_marker_count_unchanged(self) -> None:
        """The module-wide STOP count is unchanged (2 STOP instructions, 0 🛑).

        Step 3 EULA and Step 5b each carry one STOP instruction; Step 5a adds
        none.

        Validates: Requirements 1.4, 3.3
        """
        stop_emoji = _CONTENT.count("🛑")
        assert stop_emoji == 0, (
            f"Module should have 0 STOP emoji (🛑), found {stop_emoji}"
        )
        stop_word = len(re.findall(r"\bSTOP\b", _CONTENT))
        assert stop_word == 2, (
            f"Module should have exactly 2 STOP instructions, found {stop_word}"
        )


class TestStep5aSummarizedExplanation:
    """Step 5a embeds the summarized-explanation instruction.

    Validates: Requirements 1.5, 2.3
    """

    def test_summary_instruction_covers_in_flow_path(self) -> None:
        """5a instructs the spoken summary to keep the in-flow option.

        Validates: Requirement 1.5
        """
        region = _extract_5a_region().lower()
        assert "summarize this explanation" in region, (
            "Step 5a must include an instruction governing the spoken summary"
        )
        assert "in-flow" in region, (
            "The summary instruction must keep the in-flow option"
        )
        assert (
            "applying a license you already have" in region
            and "senzing support" in region
        ), "The summary must mention the apply-existing and support paths too"

    def test_summary_instruction_carries_caveat(self) -> None:
        """5a instructs the summary to carry the availability caveat.

        Validates: Requirement 2.3
        """
        region = _extract_5a_region().lower()
        # The summary instruction must keep the caveat: depends on availability
        # and may be unavailable in a given session.
        assert "depends on the `submit_feedback` tool being available" in region, (
            "The summary must carry that the in-flow path depends on submit_feedback availability"
        )
        assert "may be unavailable in a given session" in region, (
            "The summary must carry that the in-flow path may be unavailable in a session"
        )


class TestStep5aAvailabilityCaveat:
    """Step 5a states the availability caveat on the in-flow path only.

    Validates: Requirements 2.1, 2.2, 2.4
    """

    def test_caveat_dependency_on_submit_feedback(self) -> None:
        """5a states the in-flow path depends on submit_feedback enabled + available.

        Validates: Requirement 2.1
        """
        region = _extract_5a_region().lower()
        assert "both enabled and reported as available by the mcp server" in region, (
            "Step 5a must state the in-flow path depends on submit_feedback being "
            "both enabled and reported available by the MCP server"
        )

    def test_caveat_disabled_by_default_not_guaranteed(self) -> None:
        """5a states submit_feedback is disabled by default and the path is not guaranteed.

        Validates: Requirement 2.2
        """
        region = _extract_5a_region().lower()
        assert "disabled by default" in region, (
            "Step 5a must state submit_feedback is disabled by default"
        )
        assert "may be unavailable in a given session and is not guaranteed" in region, (
            "Step 5a must state the path may be unavailable and is not guaranteed"
        )

    def test_caveat_attached_only_to_in_flow_path(self) -> None:
        """The caveat phrasing is on the in-flow path only — not on the other paths.

        Validates: Requirement 2.4
        """
        region = _extract_5a_region()
        in_flow = _extract_numbered_path_line(
            region, "1. **Request a temporary evaluation license through the MCP server"
        )
        apply_existing = _extract_numbered_path_line(
            region, "2. **Apply a license you already have"
        )
        support = _extract_numbered_path_line(
            region, "3. **Request a license through Senzing support"
        )
        # The in-flow path carries the caveat.
        assert "disabled by default" in in_flow.lower(), (
            "The in-flow path must carry the disabled-by-default caveat"
        )
        assert "submit_feedback" in in_flow, (
            "The in-flow path must reference submit_feedback"
        )
        # The apply-existing and support paths must NOT carry the caveat.
        for name, line in (("apply-existing", apply_existing), ("support", support)):
            lower = line.lower()
            assert "disabled by default" not in lower, (
                f"The {name} path must not carry the disabled-by-default caveat"
            )
            assert "submit_feedback" not in line, (
                f"The {name} path must not reference submit_feedback"
            )
            assert "not guaranteed" not in lower, (
                f"The {name} path must not carry the not-guaranteed caveat"
            )


class TestStep5aConsistencyWithStep5c:
    """Step 5a mechanism and availability wording match the Step 5c branch.

    Validates: Requirements 3.1, 3.2
    """

    def test_mechanism_consistent_with_5c(self) -> None:
        """5a uses the same submit_feedback/license_request mechanism as 5c.

        Validates: Requirement 3.1
        """
        region_5a = _extract_5a_region()
        region_5c = _extract_5c_region()
        for token in ("submit_feedback", "license_request"):
            assert token in region_5a, f"Step 5a must reference {token}"
            assert token in region_5c, f"Step 5c must reference {token} (consistency anchor)"

    def test_availability_dependency_consistent_with_5c(self) -> None:
        """5a's disabled-by-default dependency matches 5c; no contradiction.

        Validates: Requirement 3.2
        """
        region_5a = _extract_5a_region().lower()
        region_5c = _extract_5c_region().lower()
        assert "disabled by default" in region_5a, (
            "Step 5a must state submit_feedback is disabled by default"
        )
        assert "disabled by default" in region_5c, (
            "Step 5c must state submit_feedback is disabled by default (consistency anchor)"
        )
        # Both reference the disabledTools array in mcp.json — the same source of truth.
        assert "disabledtools" in region_5a, (
            "Step 5a must reference the disabledTools array"
        )
        assert "disabledtools" in region_5c, (
            "Step 5c must reference the disabledTools array (consistency anchor)"
        )
        # Negative: Step 5a must not claim the in-flow path is always available /
        # enabled by default, which would contradict the Step 5c branch.
        assert "enabled by default" not in region_5a, (
            "Step 5a must not contradict Step 5c by claiming submit_feedback is "
            "enabled by default"
        )


class TestStep5aDirectsToStep5c:
    """Step 5a directs selection and execution to the Step 5c branch.

    Validates: Requirement 3.4
    """

    def test_directs_selection_execution_to_5c(self) -> None:
        """5a states choosing and carrying out a path happens at Step 5c.

        Validates: Requirement 3.4
        """
        region = _extract_5a_region().lower()
        assert "step 5c" in region, "Step 5a must direct the bootcamper to Step 5c"
        assert "no-license branch" in region, (
            "Step 5a must direct selection/execution to the Step 5c no-license branch"
        )
        assert (
            "selecting and carrying out one of these paths happens at the step 5c" in region
        ), "Step 5a must state selection/execution happens at Step 5c, not at Step 5a"


class TestStep5aMcpSourcedFigures:
    """Step 5a instructs MCP-sourced figures with omit-and-notify fallback.

    Validates: Requirements 4.1, 4.2, 4.3, 4.4
    """

    def test_figures_retrieved_from_mcp_at_runtime(self) -> None:
        """5a retrieves record/validity figures from an MCP tool this session.

        Validates: Requirements 4.1, 4.2
        """
        region = _extract_5a_region().lower()
        assert "record capacity or validity period" in region, (
            "Step 5a must address the record capacity and validity period figures"
        )
        assert "retrieve those values from a senzing mcp server tool during this session" in region, (
            "Step 5a must source those figures from an MCP server tool at runtime"
        )
        assert "present exactly what the tool returns" in region, (
            "Step 5a must present exactly what the MCP tool returns (no reformatting)"
        )

    def test_30s_unreachable_omit_and_notify(self) -> None:
        """5a treats no response within 30s as unreachable and omits + notifies.

        Validates: Requirements 4.3, 4.4
        """
        region = _extract_5a_region().lower()
        assert "30 seconds" in region, (
            "Step 5a must encode the 30-second unreachable timeout"
        )
        assert "omit the specific figure" in region, (
            "Step 5a must omit the figure when retrieval fails"
        )
        assert "unavailable from the mcp server" in region, (
            "Step 5a must tell the bootcamper the value is unavailable from the MCP server"
        )
        assert "never substitute a hardcoded or remembered figure" in region, (
            "Step 5a must never substitute a hardcoded/remembered figure"
        )

    def test_illustrative_figure_is_mcp_confirmed_not_authoritative(self) -> None:
        """The illustrative 500-record figure must be MCP-confirmed, not authoritative.

        Hybrid decision: the illustrative "500 records" figure may remain in the
        5a explanation (it is the current published value and is also pinned by
        other specs), but the explanation must instruct the agent to confirm it
        against the MCP server rather than present it as an authoritative fact
        from training data. The MCP-sourcing/confirm directive must therefore be
        present so the figure is never treated as a static, authoritative value.

        Validates: Requirements 4.1, 4.2, 4.3, 4.4
        """
        region = _extract_5a_region()
        lower = region.lower()
        # The runtime MCP-sourcing directive must be present.
        assert "retrieve those values from a senzing mcp server tool during this session" in lower, (
            "Step 5a must source the record/validity figures from an MCP server tool at runtime"
        )
        # The illustrative figure must be explicitly confirmed via the MCP server,
        # not presented as an authoritative training-data fact.
        assert "confirm it against the senzing mcp server" in lower, (
            "Step 5a must instruct confirming the illustrative figure against the MCP server"
        )
        assert "rather than presenting it as an authoritative figure from training data" in lower, (
            "Step 5a must state the figure is not an authoritative training-data fact"
        )

    def test_no_hardcoded_mcp_url_in_figure_guidance(self) -> None:
        """No hardcoded MCP server URL appears in the 5a figure guidance.

        The MCP server URL must live only in mcp.json (per security.md); the
        figure-sourcing guidance references the MCP server generically.

        Validates: Requirements 4.1, 4.2, 4.3, 4.4 (negative assertion)
        """
        region = _extract_5a_region()
        assert _MCP_URL not in region, (
            "Step 5a must not hardcode the MCP server URL in the figure guidance"
        )


class TestStep5aScope:
    """Scope and security guards for the edited Step 5a region.

    Validates: design security/scope guards (no hardcoded MCP URL).
    """

    def test_no_hardcoded_mcp_url_in_5a_region(self) -> None:
        """The 5a region does not hardcode the MCP server URL.

        The MCP server URL must live only in mcp.json (per security.md).
        """
        region = _extract_5a_region()
        assert _MCP_URL not in region, (
            "Step 5a must not hardcode the MCP server URL — reference the "
            "capability generically"
        )
