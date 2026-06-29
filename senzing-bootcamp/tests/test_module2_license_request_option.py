"""Guidance-validation tests for the Module 2 license-request option content.

Validates that the in-flow MCP license-request path was correctly surfaced in
the Module 2 licensing branch in `steering/module-02-sdk-setup.md` — the
Step 5c no-license sub-branch (capability verification, three-path
presentation, tool-enablement, single invocation, MCP-sourced facts) — and
documented in the Module 2 companion doc
(`docs/modules/MODULE_2_SDK_SETUP.md`, "Senzing License Requirements"
section), without introducing hardcoded MCP URLs, hardcoded license validity
figures, or new Step 5 pointing questions / STOP markers.

This module mirrors the structure, helpers, and conventions of
`test_license_request_option.py` (the Module 1 lock-in test): stdlib +
Hypothesis, class-based organization, and region-extraction helpers. The
wording asserted here matches the canonical Module 1 Step 6d branch so the two
modules stay consistent (Requirement 7).

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5,
3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4,
5.5, 6.1, 6.2, 6.3, 7.1, 7.2, 7.3, 7.4, 7.5**
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_MODULE_02_FILE: Path = _STEERING_DIR / "module-02-sdk-setup.md"

_DOCS_DIR: Path = Path(__file__).resolve().parent.parent / "docs" / "modules"
_MODULE_02_DOC_FILE: Path = _DOCS_DIR / "MODULE_2_SDK_SETUP.md"

# Read the steering file content once at module level for all test classes.
_CONTENT: str = _MODULE_02_FILE.read_text(encoding="utf-8")

# Read the companion-doc content once at module level.
_DOC_CONTENT: str = _MODULE_02_DOC_FILE.read_text(encoding="utf-8")

# The MCP server URL must live only in mcp.json. Built from parts here so this
# test module does not itself contain the literal URL.
_MCP_URL: str = "mcp." + "senzing.com"

# The three licensing paths, in the order Step 5c must present them (R1.1).
_ORDERED_PATHS: tuple[str, ...] = (
    "through the mcp server (in-flow)",
    "external channel",
    "apply an existing license",
)


# ---------------------------------------------------------------------------
# Region extraction helpers
# ---------------------------------------------------------------------------


def _extract_region(start_marker: str, end_marker: str) -> str:
    """Extract steering content between two line markers.

    The Step 5 sub-steps are ``###`` headers (e.g. ``### 5c. Handle the
    response``) and the no-license sub-branch opens with an inline bold marker
    (``**IF the bootcamper has no license:**``). The region is bounded by the
    first line containing ``start_marker`` and the next line containing
    ``end_marker``.

    Args:
        start_marker: Substring identifying the region's opening line.
        end_marker: Substring identifying the following boundary line.

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


def _extract_step5_region() -> str:
    """Extract the whole Step 5 (Configure License) section."""
    return _extract_region("## Step 5: Configure License", "## Step 6:")


def _extract_5c_no_license_region() -> str:
    """Extract the Step 5c no-license sub-branch block.

    Bounded by the ``**IF the bootcamper has no license:**`` sub-block opener
    and the following ``### 5d.`` configuration header.
    """
    return _extract_region("**IF the bootcamper has no license:**", "### 5d.")


def _extract_doc_license_section() -> str:
    """Extract the Module 2 doc "Senzing License Requirements" section.

    The companion doc organizes sections as ``##`` headers. The license
    section runs from ``## Senzing License Requirements`` up to (but excluding)
    the next top-level ``## `` header.

    Returns:
        The text of the license-requirements section.
    """
    lines = _DOC_CONTENT.split("\n")
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        if start is None and line.startswith("## Senzing License Requirements"):
            start = i
        elif start is not None and line.startswith("## "):
            end = i
            break
    assert start is not None, "Could not find the 'Senzing License Requirements' section"
    if end is None:
        end = len(lines)
    return "\n".join(lines[start:end])


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestStep5cThreePaths:
    """Step 5c presents three distinct licensing paths with full descriptions.

    Validates: Requirements 1.1, 1.2
    """

    def test_5c_references_three_distinct_paths(self) -> None:
        """5c presents the MCP in-flow, external, and apply-existing paths distinctly.

        Validates: Requirement 1.1
        """
        region = _extract_5c_no_license_region()
        lower = region.lower()
        assert "distinct, individually selectable options" in lower, (
            "5c must present the paths as distinct, individually selectable options"
        )
        # In-flow MCP path
        assert "through the mcp server (in-flow)" in lower, (
            "5c must reference the in-flow MCP request path"
        )
        # External request path
        assert "external channel" in lower, "5c must reference the external request path"
        # Apply-existing path
        assert "apply an existing license" in lower, (
            "5c must reference the apply-an-existing-license path"
        )

    def test_5c_paths_presented_in_required_order(self) -> None:
        """The three paths appear in order: in-flow, external, apply-existing.

        Validates: Requirement 1.1
        """
        region = _extract_5c_no_license_region().lower()
        positions = [region.find(path) for path in _ORDERED_PATHS]
        for path, pos in zip(_ORDERED_PATHS, positions):
            assert pos != -1, f"5c must mention the path {path!r}"
        assert positions == sorted(positions), (
            "5c must present the in-flow, external, then apply-existing paths in order"
        )

    def test_5c_option_description_completeness(self) -> None:
        """The in-flow option states MCP server, evaluation license, email, download link.

        Validates: Requirement 1.2
        """
        region = _extract_5c_no_license_region().lower()
        assert "senzing mcp server" in region or "mcp server" in region, (
            "In-flow option must identify it uses the MCP server"
        )
        assert "generate an evaluation license" in region, (
            "In-flow option must state it generates an evaluation license"
        )
        assert "delivered by email" in region, (
            "In-flow option must state the license is delivered by email"
        )
        assert "download link" in region, (
            "In-flow option must state the email contains a download link"
        )


class TestStep5cSelectionHandling:
    """Step 5c acts only on the selected path and re-presents on no match.

    Validates: Requirements 1.4, 1.5
    """

    def test_acts_on_selected_path_only(self) -> None:
        """5c acts on the bootcamper's chosen path after they respond.

        Validates: Requirement 1.4
        """
        region = _extract_5c_no_license_region().lower()
        assert "once the bootcamper responds, act on their choice" in region, (
            "5c must act only on the selected path once the bootcamper responds"
        )

    def test_unrecognized_response_re_presents_options(self) -> None:
        """An unrecognized Step 5c response re-presents the same options unchanged.

        Validates: Requirement 1.5
        """
        region = _extract_5c_no_license_region().lower()
        assert "not recognized" in region or "does not match" in region, (
            "5c must indicate when the prior response was not recognized"
        )
        assert "re-present" in region or "present the same options" in region, (
            "5c must re-present the same options on an unrecognized response"
        )
        assert "do not advance" in region or "not advance past" in region, (
            "5c must not advance past Step 5c on an unrecognized response"
        )


class TestStep5cHasLicenseRouting:
    """The has-license / already-configured routes omit the in-flow option.

    Validates: Requirements 1.3, 7.5
    """

    def test_already_licensed_omits_in_flow_and_routes_to_apply_existing(self) -> None:
        """If a license already exists, 5c omits the in-flow option and applies existing.

        Validates: Requirements 1.3, 7.5
        """
        region = _extract_5c_no_license_region().lower()
        assert "already" in region, (
            "5c must address the already-has-a-license / already-configured case"
        )
        assert "omit the in-flow mcp request" in region, (
            "Already-licensed case must omit the in-flow MCP request option"
        )
        assert (
            "apply-an-existing-license path" in region
            or "apply an existing license" in region
        ), "Already-licensed case must route to the apply-an-existing-license path"


class TestStep5cCapabilityGate:
    """Step 5c verifies capability availability before presenting the option.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5
    """

    def test_get_capabilities_called_before_presenting(self) -> None:
        """5c instructs a get_capabilities check within the licensing interaction.

        Validates: Requirements 2.1, 7.1
        """
        region = _extract_5c_no_license_region()
        lower = region.lower()
        assert "get_capabilities" in region, "5c must instruct calling get_capabilities"
        assert "same licensing interaction" in lower, (
            "get_capabilities must be called within the same licensing interaction"
        )
        assert "before presenting" in lower, (
            "Availability must be checked before presenting choices"
        )
        assert "30 seconds" in lower, "Availability gate must use the 30-second window"
        # The check targets submit_feedback availability.
        assert "submit_feedback" in region, (
            "Capability check must determine submit_feedback availability"
        )

    def test_available_branch_presents_option(self) -> None:
        """When submit_feedback is available, all three paths are presented.

        Validates: Requirement 2.2
        """
        region = _extract_5c_no_license_region().lower()
        assert "reported available" in region, "5c must encode the available branch"
        assert "all three licensing paths" in region, (
            "Available branch must present all three licensing paths"
        )

    def test_unavailable_error_timeout_branch_omits_option(self) -> None:
        """Unavailable / error / 30s-timeout omits the option, leaving two paths.

        Validates: Requirements 2.3, 2.4, 7.4
        """
        region = _extract_5c_no_license_region().lower()
        assert "reported unavailable" in region, "5c must encode the unavailable case"
        assert "error response" in region, "5c must encode the error-response case"
        assert "no response arrives within 30 seconds" in region, (
            "5c must encode the 30-second timeout case"
        )
        assert "omit the in-flow mcp request path" in region, (
            "Unavailable/error/timeout must omit the in-flow option"
        )
        assert "external request and apply-an-existing-license paths" in region, (
            "Fallback must present the external and apply-existing paths"
        )

    def test_unavailable_session_message(self) -> None:
        """When the option is omitted, 5c tells the bootcamper it's unavailable this session.

        Validates: Requirement 2.5
        """
        region = _extract_5c_no_license_region().lower()
        assert "unavailable for the current session" in region, (
            "5c must tell the bootcamper the in-session capability is unavailable this session"
        )


class TestStep5cDisabledByDefault:
    """Step 5c explains the disabled-by-default tool and how to enable it.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
    """

    def test_disabled_by_default_messaging(self) -> None:
        """5c states the option requires submit_feedback and it is disabled by default.

        Validates: Requirement 3.1
        """
        region = _extract_5c_no_license_region()
        lower = region.lower()
        assert "requires the `submit_feedback` tool" in region, (
            "5c must state the option requires the submit_feedback tool"
        )
        assert "disabled by default" in lower, (
            "5c must state submit_feedback is disabled by default"
        )

    def test_enable_instructions_identify_mcp_json(self) -> None:
        """5c points at mcp.json, removing submit_feedback from disabledTools, and saving.

        Validates: Requirement 3.2
        """
        region = _extract_5c_no_license_region()
        lower = region.lower()
        assert "senzing-bootcamp/mcp.json" in region, (
            "Enable instructions must identify senzing-bootcamp/mcp.json"
        )
        assert "disabledtools" in lower, (
            "Enable instructions must reference the disabledTools array"
        )
        assert "remove `submit_feedback` from the `disabledtools` array" in lower, (
            "Enable instructions must direct removing submit_feedback from disabledTools"
        )
        assert "save the file" in lower, "Enable instructions must direct saving the file"

    def test_reverify_after_reenablement(self) -> None:
        """5c re-verifies via get_capabilities after re-enablement.

        Validates: Requirement 3.3
        """
        region = _extract_5c_no_license_region().lower()
        assert "re-verify availability by calling `get_capabilities` again" in region, (
            "5c must re-verify availability via get_capabilities after re-enablement"
        )
        assert "before invoking" in region, (
            "Re-verification must occur before invoking submit_feedback"
        )

    def test_decline_fallback_presents_remaining_paths(self) -> None:
        """If the bootcamper declines to re-enable, only remaining paths are presented.

        Validates: Requirements 3.4, 3.5
        """
        region = _extract_5c_no_license_region().lower()
        assert "decline to re-enable" in region, "5c must handle declining to re-enable"
        assert "present only the remaining paths" in region, (
            "Declining must present only the remaining paths"
        )


class TestStep5cInvocation:
    """Step 5c invokes the request once and handles the outcomes.

    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
    """

    def test_single_invocation_with_license_request_category(self) -> None:
        """5c invokes submit_feedback exactly once with the license_request category.

        Validates: Requirements 4.1, 4.6, 7.2
        """
        region = _extract_5c_no_license_region()
        lower = region.lower()
        assert "invoke `submit_feedback` exactly once" in lower, (
            "5c must invoke submit_feedback exactly once"
        )
        assert "`license_request` category" in region, (
            "5c must invoke with the license_request category"
        )

    def test_success_instructs_email_check(self) -> None:
        """On success, 5c instructs checking email for the license and download link.

        Validates: Requirement 4.2
        """
        region = _extract_5c_no_license_region().lower()
        assert "response with no error" in region, "5c must handle the no-error response"
        assert "check the email" in region, (
            "Success must instruct the bootcamper to check email"
        )
        assert "download link" in region, "Success message must mention the download link"

    def test_receipt_routes_to_step_5d(self) -> None:
        """On confirmed receipt, 5c routes to the Step 5d configuration steps.

        Validates: Requirement 4.3
        """
        region = _extract_5c_no_license_region().lower()
        assert "confirm receipt" in region, "5c must wait for receipt confirmation"
        assert "step 5d configuration steps" in region, (
            "On receipt, 5c must route to the Step 5d configuration steps"
        )

    def test_failure_no_auto_retry_fallback(self) -> None:
        """On error/timeout, 5c reports failure and does not auto-retry.

        Validates: Requirements 4.4, 4.5
        """
        region = _extract_5c_no_license_region()
        lower = region.lower()
        assert "error or no response within 30 seconds" in lower, (
            "5c must handle invocation error/timeout within 30 seconds"
        )
        assert "license request did not complete" in lower, (
            "Failure must report the request did not complete"
        )
        assert "do not automatically re-invoke `submit_feedback`" in lower, (
            "Failure must not automatically re-invoke submit_feedback"
        )
        # The remaining paths remain available on failure.
        assert "external request and apply existing" in lower, (
            "Failure fallback must present the external and apply-existing paths"
        )


class TestStep5cMcpSourcedFacts:
    """Step 5c sources license facts from MCP with an unavailable fallback.

    Validates: Requirements 6.1, 6.2, 6.3
    """

    def test_facts_sourced_from_mcp_with_unavailable_fallback(self) -> None:
        """5c retrieves validity/capacity from MCP and omits with an unavailable note.

        Validates: Requirements 6.1, 6.2, 6.3
        """
        region = _extract_5c_no_license_region().lower()
        assert "validity period or record capacity" in region, (
            "5c must address the validity period and record capacity"
        )
        assert "retrieve those values from a senzing mcp server tool" in region, (
            "5c must source those values from an MCP server tool at runtime"
        )
        assert "present exactly what the tool returns" in region, (
            "5c must present exactly what the MCP tool returns (no override)"
        )
        assert "unavailable from the mcp server" in region, (
            "5c must state the value is unavailable when retrieval fails"
        )
        assert "never substitute a hardcoded or remembered figure" in region, (
            "5c must never substitute a hardcoded/remembered figure"
        )

    def test_no_hardcoded_validity_period_figures(self) -> None:
        """No hardcoded validity-period figures appear in the 5c no-license region.

        Validates: Requirements 6.1, 6.2, 6.3 (negative assertion)
        """
        region = _extract_5c_no_license_region()
        lower = region.lower()
        forbidden = [
            "30-90 days",
            "30–90 days",
            "30-90 day",
            "30–90 day",
            "90 days",
            "90-day",
            "30 days",
            "60 days",
        ]
        for figure in forbidden:
            assert figure not in lower, (
                f"5c must not hardcode the validity-period figure {figure!r}"
            )
        # General defensive check: no "<n>-<n> day(s)" validity ranges. This does not
        # match "1–2 business days" (response time) or "30 seconds" (timeouts).
        day_range = re.compile(r"\d+\s*[-–]\s*\d+\s*days?", re.IGNORECASE)
        assert not day_range.search(region), (
            "5c must not hardcode a day-range validity period"
        )


class TestStep5Scope:
    """Scope and security guards for the edited Step 5 region.

    Validates: design security/scope guards (no hardcoded MCP URL; no new
    pointing questions or STOP markers introduced in Step 5).
    """

    def test_no_hardcoded_mcp_url_in_no_license_region(self) -> None:
        """The Step 5c no-license region does not hardcode the MCP server URL.

        The MCP server URL must live only in mcp.json (per security.md).
        """
        region = _extract_5c_no_license_region()
        assert _MCP_URL not in region, (
            "Step 5c must not hardcode the MCP server URL — "
            "reference the capability generically"
        )

    def test_step5_pointing_question_count_unchanged(self) -> None:
        """Step 5 still has exactly one pointing question (👉), introduced by 5b.

        The in-flow option is surfaced inside the 5c no-license branch without
        adding a new pointing question (design C2).
        """
        region = _extract_step5_region()
        count = region.count("👉")
        assert count == 1, (
            f"Step 5 should have exactly 1 pointing question (👉), found {count}"
        )

    def test_step5_stop_marker_count_unchanged(self) -> None:
        """Step 5 still has exactly one STOP instruction and no STOP emoji.

        The 5b "STOP and wait" instruction is the only STOP in Step 5; the in-flow
        option must not add a STOP emoji (🛑) or a second STOP (design C2).
        """
        region = _extract_step5_region()
        stop_emoji = region.count("🛑")
        assert stop_emoji == 0, (
            f"Step 5 should have 0 STOP emoji (🛑), found {stop_emoji}"
        )
        stop_word = len(re.findall(r"\bSTOP\b", region))
        assert stop_word == 1, (
            f"Step 5 should have exactly 1 STOP instruction, found {stop_word}"
        )


class TestModule2Documentation:
    """The Module 2 doc documents the in-flow MCP license-request option.

    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
    """

    def test_doc_describes_mcp_evaluation_license_path_outside_flow(self) -> None:
        """The section identifies the in-flow MCP path available outside Step 5 flow.

        Validates: Requirement 5.1
        """
        region = _extract_doc_license_section().lower()
        assert "evaluation license" in region, (
            "Doc must describe obtaining an evaluation license"
        )
        assert "mcp server" in region, (
            "Doc must identify the option as a path through the MCP server"
        )
        assert "in-flow" in region, "Doc must frame the option as the in-flow path"
        assert "conversational flow" in region, (
            "Doc must state it is available outside the Step 5 conversational flow"
        )
        assert "step 5" in region, (
            "Doc must reference the Step 5 conversational flow the option lives outside of"
        )

    def test_doc_states_email_delivery_with_download_link(self) -> None:
        """The section states email delivery with a download link.

        Validates: Requirement 5.2
        """
        region = _extract_doc_license_section().lower()
        assert "delivered by email" in region, (
            "Doc must state the license is delivered by email"
        )
        assert "download link" in region, (
            "Doc must state the email includes a download link"
        )

    def test_doc_states_submit_feedback_license_request_invocation(self) -> None:
        """The section states it invokes submit_feedback with the license_request category.

        Validates: Requirement 5.3
        """
        region = _extract_doc_license_section()
        lower = region.lower()
        assert "submit_feedback" in region, (
            "Doc must name the submit_feedback MCP tool"
        )
        assert "license_request" in region, (
            "Doc must name the license_request category"
        )
        assert "category" in lower, (
            "Doc must describe license_request as the invocation category"
        )

    def test_doc_states_tool_disabled_by_default(self) -> None:
        """The section states the submit_feedback tool is disabled by default.

        Validates: Requirement 5.4
        """
        region = _extract_doc_license_section().lower()
        assert "disabled by default" in region, (
            "Doc must state submit_feedback is disabled by default"
        )

    def test_doc_states_disabledtools_removal_instruction(self) -> None:
        """The section instructs removing submit_feedback from disabledTools in mcp.json.

        Validates: Requirement 5.5
        """
        region = _extract_doc_license_section()
        lower = region.lower()
        assert "senzing-bootcamp/mcp.json" in region, (
            "Doc must identify senzing-bootcamp/mcp.json"
        )
        assert "disabledtools" in lower, (
            "Doc must reference the disabledTools array"
        )
        assert "remove `submit_feedback` from the `disabledtools` array" in lower, (
            "Doc must instruct removing submit_feedback from the disabledTools array"
        )

    def test_doc_section_has_no_hardcoded_mcp_url(self) -> None:
        """The license section does not hardcode the MCP server URL.

        The MCP server URL must live only in mcp.json (per security.md).

        Validates: Requirement 5 (security/scope guard)
        """
        region = _extract_doc_license_section()
        assert _MCP_URL not in region, (
            "The license-requirements section must not hardcode the MCP server URL — "
            "reference the capability generically"
        )


class TestModule1Module2Consistency:
    """Module 2 wording matches the Module 1 Step 6d gate / invocation / enable text.

    Validates: Requirements 7.1, 7.2, 7.3
    """

    def test_gate_invocation_enable_phrases_match_module1(self) -> None:
        """The 5c gate, invocation, and enable phrasing match Module 1 Step 6d.

        Validates: Requirements 7.1, 7.2, 7.3
        """
        region = _extract_5c_no_license_region().lower()
        # R7.1 — the get_capabilities availability gate with the 30-second window.
        assert "get_capabilities" in region and "30 seconds" in region, (
            "Module 2 must describe the get_capabilities gate with the 30-second window"
        )
        # R7.2 — a single submit_feedback call with the license_request category.
        assert "invoke `submit_feedback` exactly once" in region, (
            "Module 2 must describe a single submit_feedback invocation"
        )
        assert "`license_request` category" in region, (
            "Module 2 must describe the license_request category invocation"
        )
        # R7.3 — enablement via removing submit_feedback from disabledTools in mcp.json.
        assert "remove `submit_feedback` from the `disabledtools` array" in region, (
            "Module 2 must describe the same enable instruction as Module 1"
        )
        assert "senzing-bootcamp/mcp.json" in region, (
            "Module 2 enable instruction must reference senzing-bootcamp/mcp.json"
        )


class TestStep5cPathOrderingProperty:
    """Property: the three licensing paths keep their required relative order.

    Validates: Requirement 1.1
    """

    @given(idx=st.integers(min_value=0, max_value=len(_ORDERED_PATHS) - 2))
    def test_each_path_precedes_the_next(self, idx: int) -> None:
        """For each adjacent pair, the earlier-listed path occurs first in the region.

        Validates: Requirement 1.1
        """
        region = _extract_5c_no_license_region().lower()
        earlier = _ORDERED_PATHS[idx]
        later = _ORDERED_PATHS[idx + 1]
        earlier_pos = region.find(earlier)
        later_pos = region.find(later)
        assert earlier_pos != -1, f"5c must mention the path {earlier!r}"
        assert later_pos != -1, f"5c must mention the path {later!r}"
        assert earlier_pos < later_pos, (
            f"Path {earlier!r} must be presented before {later!r}"
        )
