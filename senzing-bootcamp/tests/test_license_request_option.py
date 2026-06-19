"""Example-based tests for the Module 1 license-request option content.

Validates that the in-flow MCP license-request path was correctly added to the
Module 1 licensing branch in `steering/module-01-phase1-discovery.md` — the
Step 6b trigger reference (R1.3) and the Step 6d no-license branch
(capability verification, tool-enablement, single invocation, MCP-sourced
facts) — and that the edits stay scoped to the licensing branch without
hardcoded MCP URLs or hardcoded license validity figures.

Task 4.2 appends a separate class to this module validating the licensing
reference (`licenses/README.md`) against Requirement 5.

**Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3,
3.4, 4.1, 4.2, 4.3, 4.4, 6.1, 6.2, 6.3**
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = Path(__file__).resolve().parent.parent / "steering"
_MODULE_01_FILE: Path = _STEERING_DIR / "module-01-phase1-discovery.md"

_LICENSES_DIR: Path = Path(__file__).resolve().parent.parent / "licenses"
_README_FILE: Path = _LICENSES_DIR / "README.md"

# Read the steering file content once at module level for all test classes.
_CONTENT: str = _MODULE_01_FILE.read_text(encoding="utf-8")

# Read the licensing reference content once at module level (Task 4.2).
_README_CONTENT: str = _README_FILE.read_text(encoding="utf-8")

# The MCP server URL must live only in mcp.json. Built from parts here so this
# test module does not itself contain the literal URL.
_MCP_URL: str = "mcp." + "senzing.com"


# ---------------------------------------------------------------------------
# Region extraction helpers
# ---------------------------------------------------------------------------


def _extract_region(start_marker: str, end_marker: str) -> str:
    """Extract content between two inline bold sub-step markers.

    The Module 1 licensing sub-steps are inline bold headers (e.g.
    ``**6b. License Guidance Trigger**``) rather than ``###`` headers, so the
    region is bounded by the first line containing ``start_marker`` and the
    next line containing ``end_marker``.

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


def _extract_6b_region() -> str:
    """Extract the Step 6b license-guidance trigger block."""
    return _extract_region("**6b. License Guidance Trigger**", "**6c. Already has license**")


def _extract_6d_region() -> str:
    """Extract the Step 6d no-license branch block."""
    return _extract_region("**6d. Does not have license**", "**6e. Deferral handling**")


def _extract_reference_option_region() -> str:
    """Extract the licensing-reference Option 4 (MCP in-flow) section.

    The licensing reference (`licenses/README.md`) organizes its licensing
    options as ``###`` headers. The MCP in-flow option is documented under
    ``### Option 4: Request Through the MCP Server (In-Flow)`` and the next
    header is ``## Decoding a Base64-Encoded License``.

    Returns:
        The text of the Option 4 section, up to (but excluding) the next
        top-level section header.
    """
    lines = _README_CONTENT.split("\n")
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        if start is None and line.startswith("### Option 4:"):
            start = i
        elif start is not None and line.startswith("## "):
            end = i
            break
    assert start is not None, "Could not find the Option 4 reference section"
    if end is None:
        end = len(lines)
    return "\n".join(lines[start:end])


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestStep6bTrigger:
    """Step 6b names the in-flow MCP license-request option.

    Validates: Requirement 1.3
    """

    def test_6b_names_in_flow_mcp_license_request_path(self) -> None:
        """6b references the in-flow MCP path as an available licensing option.

        Validates: Requirement 1.3
        """
        region = _extract_6b_region().lower()
        assert "in-flow" in region, "Step 6b must reference the in-flow path"
        assert "mcp" in region, "Step 6b must reference the MCP server path"
        assert "license" in region, "Step 6b must mention licensing"
        # It must be framed as one of the available options, alongside the
        # existing apply-existing and external request references.
        assert "existing license" in region, "Step 6b must name the apply-existing path"
        assert "external" in region, "Step 6b must name the external request path"


class TestStep6dThreePaths:
    """Step 6d presents three distinct licensing paths with full descriptions.

    Validates: Requirements 1.1, 1.2
    """

    def test_6d_references_three_distinct_paths(self) -> None:
        """6d presents the MCP in-flow, external, and apply-existing paths distinctly.

        Validates: Requirement 1.1
        """
        region = _extract_6d_region()
        lower = region.lower()
        assert "distinct, individually selectable options" in lower, (
            "6d must present the paths as distinct, individually selectable options"
        )
        # In-flow MCP path
        assert "through the mcp server (in-flow)" in lower, (
            "6d must reference the in-flow MCP request path"
        )
        # External request path
        assert "external channel" in lower, "6d must reference the external request path"
        # Apply-existing path
        assert "apply an existing license" in lower, (
            "6d must reference the apply-an-existing-license path"
        )

    def test_6d_option_description_completeness(self) -> None:
        """The in-flow option states MCP server, evaluation license, email, download link.

        Validates: Requirement 1.2
        """
        region = _extract_6d_region().lower()
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


class TestStep6dCapabilityGate:
    """Step 6d verifies capability availability before presenting the option.

    Validates: Requirements 2.1, 2.2, 2.3, 2.4
    """

    def test_get_capabilities_called_before_presenting(self) -> None:
        """6d instructs a get_capabilities check within the licensing interaction.

        Validates: Requirement 2.1
        """
        region = _extract_6d_region()
        lower = region.lower()
        assert "get_capabilities" in region, "6d must instruct calling get_capabilities"
        assert "same licensing interaction" in lower, (
            "get_capabilities must be called within the same licensing interaction"
        )
        assert "before presenting" in lower, (
            "Availability must be checked before presenting choices"
        )
        # The check targets submit_feedback availability.
        assert "submit_feedback" in region, (
            "Capability check must determine submit_feedback availability"
        )

    def test_available_branch_presents_option(self) -> None:
        """When submit_feedback is available, all three paths are presented.

        Validates: Requirement 2.2
        """
        region = _extract_6d_region().lower()
        assert "reported available" in region, "6d must encode the available branch"
        assert "all three licensing paths" in region, (
            "Available branch must present all three licensing paths"
        )

    def test_unavailable_error_timeout_branch_omits_option(self) -> None:
        """Unavailable / error / 30s-timeout omits the option, leaving two paths.

        Validates: Requirements 2.3, 2.4
        """
        region = _extract_6d_region().lower()
        assert "reported unavailable" in region, "6d must encode the unavailable case"
        assert "error response" in region, "6d must encode the error-response case"
        assert "no response arrives within 30 seconds" in region, (
            "6d must encode the 30-second timeout case"
        )
        assert "omit the in-flow mcp request path" in region, (
            "Unavailable/error/timeout must omit the in-flow option"
        )
        assert "external request and apply-an-existing-license paths" in region, (
            "Fallback must present the external and apply-existing paths"
        )


class TestStep6dDisabledByDefault:
    """Step 6d explains the disabled-by-default tool and how to enable it.

    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """

    def test_disabled_by_default_messaging(self) -> None:
        """6d states the option requires submit_feedback and it is disabled by default.

        Validates: Requirement 3.1
        """
        region = _extract_6d_region()
        lower = region.lower()
        assert "requires the `submit_feedback` tool" in region, (
            "6d must state the option requires the submit_feedback tool"
        )
        assert "disabled by default" in lower, (
            "6d must state submit_feedback is disabled by default"
        )

    def test_enable_instructions_identify_mcp_json(self) -> None:
        """6d points at mcp.json, removing submit_feedback from disabledTools, and saving.

        Validates: Requirement 3.2
        """
        region = _extract_6d_region()
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
        """6d re-verifies via get_capabilities after re-enablement.

        Validates: Requirement 3.3
        """
        region = _extract_6d_region().lower()
        assert "re-verify availability by calling `get_capabilities` again" in region, (
            "6d must re-verify availability via get_capabilities after re-enablement"
        )
        assert "before invoking" in region, (
            "Re-verification must occur before invoking submit_feedback"
        )

    def test_decline_fallback_presents_remaining_paths(self) -> None:
        """If the bootcamper declines to re-enable, only remaining paths are presented.

        Validates: Requirement 3.4
        """
        region = _extract_6d_region().lower()
        assert "decline to re-enable" in region, "6d must handle declining to re-enable"
        assert "present only the remaining paths" in region, (
            "Declining must present only the remaining paths"
        )


class TestStep6dInvocation:
    """Step 6d invokes the request once and handles the outcomes.

    Validates: Requirements 4.1, 4.2, 4.3, 4.4
    """

    def test_single_invocation_with_license_request_category(self) -> None:
        """6d invokes submit_feedback exactly once with the license_request category.

        Validates: Requirement 4.1
        """
        region = _extract_6d_region()
        lower = region.lower()
        assert "invoke `submit_feedback` exactly once" in lower, (
            "6d must invoke submit_feedback exactly once"
        )
        assert "`license_request` category" in region, (
            "6d must invoke with the license_request category"
        )

    def test_success_instructs_email_check(self) -> None:
        """On success, 6d instructs checking email for the license and download link.

        Validates: Requirement 4.2
        """
        region = _extract_6d_region().lower()
        assert "response with no error" in region, "6d must handle the no-error response"
        assert "check the email" in region, (
            "Success must instruct the bootcamper to check email"
        )
        assert "download link" in region, "Success message must mention the download link"

    def test_receipt_routes_to_step_6c(self) -> None:
        """On confirmed receipt, 6d routes to the Step 6c configuration steps.

        Validates: Requirement 4.3
        """
        region = _extract_6d_region().lower()
        assert "confirm receipt" in region, "6d must wait for receipt confirmation"
        assert "step 6c configuration steps" in region, (
            "On receipt, 6d must route to the Step 6c configuration steps"
        )

    def test_failure_no_auto_retry_fallback(self) -> None:
        """On error/timeout, 6d reports failure and does not auto-retry.

        Validates: Requirement 4.4
        """
        region = _extract_6d_region()
        lower = region.lower()
        assert "error or no response within 30 seconds" in lower, (
            "6d must handle invocation error/timeout within 30 seconds"
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


class TestStep6dMcpSourcedFacts:
    """Step 6d sources license facts from MCP with an unavailable fallback.

    Validates: Requirements 6.1, 6.2, 6.3
    """

    def test_facts_sourced_from_mcp_with_unavailable_fallback(self) -> None:
        """6d retrieves validity/capacity from MCP and omits with an unavailable note.

        Validates: Requirements 6.1, 6.2, 6.3
        """
        region = _extract_6d_region().lower()
        assert "validity period or record capacity" in region, (
            "6d must address the validity period and record capacity"
        )
        assert "retrieve those values from a senzing mcp server tool" in region, (
            "6d must source those values from an MCP server tool at runtime"
        )
        assert "present exactly what the tool returns" in region, (
            "6d must present exactly what the MCP tool returns (no override)"
        )
        assert "unavailable from the mcp server" in region, (
            "6d must state the value is unavailable when retrieval fails"
        )
        assert "never substitute a hardcoded or remembered figure" in region, (
            "6d must never substitute a hardcoded/remembered figure"
        )

    def test_no_hardcoded_validity_period_figures(self) -> None:
        """No hardcoded validity-period figures appear in the 6d region.

        Validates: Requirements 6.1, 6.2, 6.3 (negative assertion)
        """
        region = _extract_6d_region()
        lower = region.lower()
        forbidden = ["30-90 days", "30–90 days", "90 days", "90-day", "30 days", "60 days"]
        for figure in forbidden:
            assert figure not in lower, (
                f"6d must not hardcode the validity-period figure {figure!r}"
            )
        # General defensive check: no "<n>-<n> days" validity ranges. This does not
        # match "1–2 business days" (response time) or "30 seconds" (timeouts).
        day_range = re.compile(r"\d+\s*[-–]\s*\d+\s*days", re.IGNORECASE)
        assert not day_range.search(region), (
            "6d must not hardcode a day-range validity period"
        )


class TestStep6Scope:
    """Scope and security guards for the edited licensing region.

    Validates: design security/scope guards (no hardcoded MCP URL; no new
    pointing questions or STOP markers in the 6d region).
    """

    def test_no_hardcoded_mcp_url_in_edited_regions(self) -> None:
        """Neither the 6b nor the 6d region hardcodes the MCP server URL.

        The MCP server URL must live only in mcp.json (per security.md).
        """
        for name, region in (("6b", _extract_6b_region()), ("6d", _extract_6d_region())):
            assert _MCP_URL not in region, (
                f"Step {name} must not hardcode the MCP server URL — "
                "reference the capability generically"
            )

    def test_6d_pointing_question_count_unchanged(self) -> None:
        """The 6d region still has exactly one pointing question (👉)."""
        region = _extract_6d_region()
        count = region.count("👉")
        assert count == 1, (
            f"6d should have exactly 1 pointing question (👉), found {count}"
        )

    def test_6d_stop_marker_count_unchanged(self) -> None:
        """The 6d region still has exactly one STOP marker (🛑)."""
        region = _extract_6d_region()
        stop_emoji = region.count("🛑")
        assert stop_emoji == 1, (
            f"6d should have exactly 1 STOP marker (🛑), found {stop_emoji}"
        )
        stop_word = len(re.findall(r"\bSTOP\b", region))
        assert stop_word == 1, (
            f"6d should have exactly 1 STOP instruction, found {stop_word}"
        )


class TestLicensingReference:
    """The licensing reference documents the in-flow MCP license-request option.

    Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
    """

    def test_reference_describes_mcp_evaluation_license_path(self) -> None:
        """Option 4 identifies the option as an MCP path to an evaluation license.

        Validates: Requirement 5.1
        """
        region = _extract_reference_option_region().lower()
        assert "evaluation license" in region, (
            "Reference must describe obtaining an evaluation license"
        )
        assert "mcp server" in region, (
            "Reference must identify the option as a path through the MCP server"
        )
        assert "in-flow" in region, (
            "Reference must frame the option as the in-flow path"
        )

    def test_reference_states_email_delivery_with_download_link(self) -> None:
        """Option 4 states email delivery with a download link.

        Validates: Requirement 5.2
        """
        region = _extract_reference_option_region().lower()
        assert "delivered by email" in region, (
            "Reference must state the license is delivered by email"
        )
        assert "download link" in region, (
            "Reference must state the email includes a download link"
        )

    def test_reference_states_submit_feedback_license_request_invocation(self) -> None:
        """Option 4 states it invokes submit_feedback with the license_request category.

        Validates: Requirement 5.3
        """
        region = _extract_reference_option_region()
        lower = region.lower()
        assert "submit_feedback" in region, (
            "Reference must name the submit_feedback MCP tool"
        )
        assert "license_request" in region, (
            "Reference must name the license_request category"
        )
        assert "category" in lower, (
            "Reference must describe license_request as the invocation category"
        )

    def test_reference_states_tool_disabled_by_default(self) -> None:
        """Option 4 states the submit_feedback tool is disabled by default.

        Validates: Requirement 5.4
        """
        region = _extract_reference_option_region().lower()
        assert "disabled by default" in region, (
            "Reference must state submit_feedback is disabled by default"
        )

    def test_reference_states_disabledtools_removal_instruction(self) -> None:
        """Option 4 instructs removing submit_feedback from disabledTools in mcp.json.

        Validates: Requirement 5.5
        """
        region = _extract_reference_option_region()
        lower = region.lower()
        assert "senzing-bootcamp/mcp.json" in region, (
            "Reference must identify senzing-bootcamp/mcp.json"
        )
        assert "disabledtools" in lower, (
            "Reference must reference the disabledTools array"
        )
        assert "remove `submit_feedback` from the `disabledtools` array" in lower, (
            "Reference must instruct removing submit_feedback from the disabledTools array"
        )

    def test_reference_section_has_no_hardcoded_mcp_url(self) -> None:
        """The Option 4 reference section does not hardcode the MCP server URL.

        The MCP server URL must live only in mcp.json (per security.md).

        Validates: Requirement 5 (security/scope guard)
        """
        region = _extract_reference_option_region()
        assert _MCP_URL not in region, (
            "The licensing reference section must not hardcode the MCP server URL — "
            "reference the capability generically"
        )
