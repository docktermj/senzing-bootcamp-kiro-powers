"""Bug condition exploration tests for mcp-temporary-license-consultation bugfix.

These tests parse the UNFIXED steering files and confirm the bug exists.
Tests are EXPECTED TO FAIL on unfixed code — failure confirms the bug.

The bug (Rule 6 violation): when the current Senzing license is insufficient
(total records > 500 OR a ``SENZ9000`` capacity error, and no sufficient
custom license is present), the three license-insufficient steering paths do
not instruct the agent to *consult* an MCP tool. They either omit the MCP
server entirely (Module 1 Step 6d) or mention it only as passive prose with no
named tool (Module 2 Step 5a and Step 5c "no license"). This breaches Rule 6
and the MCP-First Invariant for licensing facts.

Property 1 (Fix Checking): for every license-insufficient situation, the
handling path must contain an enforced MCP consultation step that names a
file-confirmed tool (``search_docs``), is expressed as an imperative directive
(not prose-only), and introduces no MCP server URL.

Feature: mcp-temporary-license-consultation

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5**
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _BOOTCAMP_DIR / "steering"
_MODULE_01_FILE: Path = _STEERING_DIR / "module-01-business-problem.md"
_MODULE_02_FILE: Path = _STEERING_DIR / "module-02-sdk-setup.md"
_DECISION_TREE_FILE: Path = _STEERING_DIR / "mcp-tool-decision-tree.md"
_MCP_CONFIG_FILE: Path = _BOOTCAMP_DIR / "mcp.json"

# Read steering content once at module level for all test classes.
_MODULE_01: str = _MODULE_01_FILE.read_text(encoding="utf-8")
_MODULE_02: str = _MODULE_02_FILE.read_text(encoding="utf-8")
_DECISION_TREE: str = _DECISION_TREE_FILE.read_text(encoding="utf-8")

# The file-confirmed MCP tool for documentation / guidance lookups.
_LICENSE_TOOL: str = "search_docs"


# ---------------------------------------------------------------------------
# Bug-condition domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LicenseSituation:
    """A license-handling situation encountered during the bootcamp.

    Attributes:
        total_record_count: Total records across the bootcamper's sources.
        has_sufficient_license: Whether a sufficient custom license is present.
        error_code: A Senzing error code (e.g., ``SENZ9000``) or ``None``.
    """

    total_record_count: int
    has_sufficient_license: bool
    error_code: str | None


def is_bug_condition(x: LicenseSituation) -> bool:
    """Return whether ``x`` is a license-insufficient (bug-triggering) situation.

    Args:
        x: The license situation to classify.

    Returns:
        True when capacity is exceeded or a capacity error occurred AND no
        sufficient custom license is present.
    """
    return (x.total_record_count > 500 or x.error_code == "SENZ9000") and not x.has_sufficient_license


@st.composite
def st_license_situation(draw: st.DrawFn) -> LicenseSituation:
    """Generate a ``LicenseSituation`` spanning the input domain.

    Args:
        draw: Hypothesis draw function.

    Returns:
        A randomly generated ``LicenseSituation``.
    """
    total = draw(st.integers(min_value=0, max_value=10_000_000))
    has_license = draw(st.booleans())
    error_code = draw(st.sampled_from([None, "SENZ9000", "SENZ0002"]))
    return LicenseSituation(total, has_license, error_code)


# ---------------------------------------------------------------------------
# Section extraction helpers
# ---------------------------------------------------------------------------


def _extract_6d(content: str) -> str:
    """Slice Module 1 Step 6d ("does not have license") between ``**6d.`` and ``**6e.``.

    Args:
        content: Full Module 1 steering content.

    Returns:
        The Step 6d section text (empty string if boundaries are not found).
    """
    lines = content.split("\n")
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("**6d.") and start is None:
            start = i
        elif stripped.startswith("**6e.") and start is not None:
            end = i
            break
    if start is None:
        return ""
    if end is None:
        end = len(lines)
    return "\n".join(lines[start:end])


def _extract_5a(content: str) -> str:
    """Slice Module 2 Step 5a between the ``### 5a`` and ``### 5b`` headers.

    Args:
        content: Full Module 2 steering content.

    Returns:
        The Step 5a section text (empty string if boundaries are not found).
    """
    lines = content.split("\n")
    start: int | None = None
    end: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("### 5a") and start is None:
            start = i
        elif stripped.startswith("### 5b") and start is not None:
            end = i
            break
    if start is None:
        return ""
    if end is None:
        end = len(lines)
    return "\n".join(lines[start:end])


def _extract_5c_no_license(content: str) -> str:
    """Isolate the "no license" branch of Module 2 Step 5c.

    Slices the content between ``### 5c`` and ``### 5d``, then isolates the
    block beginning at "IF the bootcamper has no license".

    Args:
        content: Full Module 2 steering content.

    Returns:
        The "no license" branch text (empty string if boundaries are not found).
    """
    lines = content.split("\n")
    start_5c: int | None = None
    end_5c: int | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("### 5c") and start_5c is None:
            start_5c = i
        elif stripped.startswith("### 5d") and start_5c is not None:
            end_5c = i
            break
    if start_5c is None:
        return ""
    if end_5c is None:
        end_5c = len(lines)
    section_5c = "\n".join(lines[start_5c:end_5c])

    no_license_idx = section_5c.lower().find("if the bootcamper has no license")
    if no_license_idx == -1:
        return ""
    return section_5c[no_license_idx:]


def _license_insufficient_sections() -> list[tuple[str, str]]:
    """Return all three license-insufficient sections as (label, content) pairs.

    Returns:
        A list of (label, section_content) tuples for Module 1 Step 6d,
        Module 2 Step 5a, and Module 2 Step 5c "no license".
    """
    return [
        ("Module 1 Step 6d", _extract_6d(_MODULE_01)),
        ("Module 2 Step 5a", _extract_5a(_MODULE_02)),
        ("Module 2 Step 5c (no license)", _extract_5c_no_license(_MODULE_02)),
    ]


def steering_path_for(x: LicenseSituation) -> tuple[str, str]:
    """Map a bug-condition situation to its primary handling path.

    Args:
        x: A license situation (assumed to satisfy ``is_bug_condition``).

    Returns:
        A (label, section_content) tuple for the path that handles ``x``.
    """
    if x.error_code == "SENZ9000":
        # A capacity error surfaces in the Module 2 Step 5a explanation path.
        return ("Module 2 Step 5a", _extract_5a(_MODULE_02))
    if x.total_record_count > 500:
        # High-volume discovery routes through Module 1 Step 6d.
        return ("Module 1 Step 6d", _extract_6d(_MODULE_01))
    # Remaining bug-condition situations are handled by the no-license branch.
    return ("Module 2 Step 5c (no license)", _extract_5c_no_license(_MODULE_02))


# ---------------------------------------------------------------------------
# Tool-set parsing and content predicates
# ---------------------------------------------------------------------------


def _mcp_tool_set() -> set[str]:
    """Parse the documented MCP tool names from ``mcp-tool-decision-tree.md``.

    Tool names are read from the call-pattern examples (``"tool": "<name>"``),
    so the set is derived from the reference file rather than hardcoded.

    Returns:
        The set of MCP tool names confirmed in the decision tree.
    """
    return set(re.findall(r'"tool"\s*:\s*"([a-z_]+)"', _DECISION_TREE))


def _tool_name_is_confirmed(name: str) -> bool:
    """Return whether ``name`` resolves to a tool documented in the decision tree.

    Args:
        name: The MCP tool name to confirm.

    Returns:
        True when ``name`` is present in the parsed tool set.
    """
    return name in _mcp_tool_set()


def _has_enforced_mcp_step(section: str) -> bool:
    """Return whether ``section`` contains an enforced MCP consultation step.

    True only if the file-confirmed tool name (``search_docs``) appears AND an
    imperative directive such as ``call`` or ``consult`` is present — not merely
    a generic "MCP server" mention.

    Args:
        section: The steering section text.

    Returns:
        True when an enforced, named-tool consultation directive is present.
    """
    lower = section.lower()
    has_tool = _LICENSE_TOOL in lower
    has_directive = bool(re.search(r"\b(call|consult|invoke|use)\b", lower))
    return has_tool and has_directive


def _is_prose_only(section: str) -> bool:
    """Return whether ``section`` mentions the MCP server but names no MCP tool.

    This is the unfixed (prose-only) condition.

    Args:
        section: The steering section text.

    Returns:
        True when the MCP server is mentioned but no documented tool is named.
    """
    mentions_mcp = "mcp server" in section.lower()
    names_tool = any(tool in section for tool in _mcp_tool_set())
    return mentions_mcp and not names_tool


def _mcp_host_from_config() -> str | None:
    """Read the MCP server host from ``mcp.json`` (single source of truth).

    The host is derived at runtime so the test never hardcodes the MCP URL.

    Returns:
        The MCP server host (parsed from ``mcp.json``), or ``None`` if no URL
        is configured.
    """
    config = json.loads(_MCP_CONFIG_FILE.read_text(encoding="utf-8"))
    for server in config.get("mcpServers", {}).values():
        url = server.get("url")
        if url:
            return urlparse(url).hostname
    return None


def _no_mcp_url(section: str) -> bool:
    """Return whether ``section`` contains no MCP server URL and no http(s) URL.

    Args:
        section: The steering section text.

    Returns:
        True when neither the configured MCP host nor any ``http``/``https``
        URL appears in the section.
    """
    host = _mcp_host_from_config()
    if host and host in section:
        return False
    return not re.search(r"https?://", section)


# ---------------------------------------------------------------------------
# PBT — Property 1: Bug Condition (Fix Checking)
# ---------------------------------------------------------------------------


class TestEnforcedMcpConsultationProperty:
    """Property 1 — Enforced MCP Consultation on Insufficient License.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

    For every license-insufficient situation, each handling path (Module 1
    Step 6d, Module 2 Step 5a, Module 2 Step 5c "no license") must contain an
    enforced ``search_docs`` consultation directive — not prose-only — with no
    MCP server URL. On UNFIXED code this FAILS: Step 6d names no tool at all,
    and Steps 5a/5c mention the MCP server only as prose.
    """

    @given(situation=st_license_situation())
    @settings(max_examples=20)
    def test_bug_condition_paths_enforce_mcp_consultation(
        self, situation: LicenseSituation
    ) -> None:
        """For all bug-condition situations, every handling path enforces consultation.

        The mapped primary path and all three license-insufficient sections
        must satisfy the four conjuncts of Property 1.
        """
        assume(is_bug_condition(situation))

        # The specific path that handles this situation must be exercised...
        primary_label, primary_section = steering_path_for(situation)
        sections = {(primary_label, primary_section), *_license_insufficient_sections()}

        for label, section in sections:
            assert section, f"{label}: section could not be extracted"
            assert _has_enforced_mcp_step(section), (
                f"{label}: no enforced MCP consultation step — "
                f"'{_LICENSE_TOOL}' is not named in an imperative directive.\n"
                f"Section:\n{section[:500]}"
            )
            assert _tool_name_is_confirmed(_LICENSE_TOOL), (
                f"{label}: tool name '{_LICENSE_TOOL}' is not confirmed in "
                f"mcp-tool-decision-tree.md"
            )
            assert not _is_prose_only(section), (
                f"{label}: MCP server is mentioned as prose only — no tool named.\n"
                f"Section:\n{section[:500]}"
            )
            assert _no_mcp_url(section), (
                f"{label}: an MCP server URL or http(s) URL is present in the section"
            )


# ---------------------------------------------------------------------------
# Example-based tests — one per license-insufficient path
# ---------------------------------------------------------------------------


class TestModule1Step6dEnforcedMcp:
    """Module 1 Step 6d must name ``search_docs`` in an imperative directive.

    **Validates: Requirements 1.1, 2.1**

    On UNFIXED code this FAILS — Step 6d directs the bootcamper to email
    support@senzing.com and contains no MCP consultation at all.
    """

    def test_6d_section_exists(self) -> None:
        """Precondition: Step 6d section can be extracted."""
        assert _extract_6d(_MODULE_01), "Could not extract Module 1 Step 6d"

    def test_6d_has_enforced_search_docs_directive(self) -> None:
        """Step 6d names ``search_docs`` in a call/consult directive."""
        section = _extract_6d(_MODULE_01)
        assert _has_enforced_mcp_step(section), (
            "Module 1 Step 6d does NOT instruct the agent to consult "
            f"'{_LICENSE_TOOL}'. The unfixed branch only points to email "
            "(support@senzing.com) with no MCP consultation step.\n"
            f"Section:\n{section[:500]}"
        )

    def test_6d_is_not_prose_only(self) -> None:
        """Step 6d is not a prose-only MCP mention."""
        section = _extract_6d(_MODULE_01)
        assert not _is_prose_only(section), (
            "Module 1 Step 6d mentions the MCP server without naming a tool."
        )

    def test_6d_has_no_mcp_url(self) -> None:
        """Step 6d introduces no MCP server URL (security guard)."""
        section = _extract_6d(_MODULE_01)
        assert _no_mcp_url(section), "Module 1 Step 6d must not contain an MCP URL"


class TestModule2Step5aEnforcedMcp:
    """Module 2 Step 5a must name ``search_docs`` in an imperative directive.

    **Validates: Requirements 1.2, 2.2**

    On UNFIXED code this FAILS — Step 5a says "you can also request a larger
    evaluation license directly through the Senzing MCP server" as prose with
    no tool named.
    """

    def test_5a_section_exists(self) -> None:
        """Precondition: Step 5a section can be extracted."""
        assert _extract_5a(_MODULE_02), "Could not extract Module 2 Step 5a"

    def test_5a_has_enforced_search_docs_directive(self) -> None:
        """Step 5a names ``search_docs`` in a call/consult directive."""
        section = _extract_5a(_MODULE_02)
        assert _has_enforced_mcp_step(section), (
            "Module 2 Step 5a does NOT instruct the agent to consult "
            f"'{_LICENSE_TOOL}'. The unfixed text mentions the MCP server only "
            "as passive prose.\n"
            f"Section:\n{section[:500]}"
        )

    def test_5a_is_not_prose_only(self) -> None:
        """Step 5a is not a prose-only MCP mention."""
        section = _extract_5a(_MODULE_02)
        assert not _is_prose_only(section), (
            "Module 2 Step 5a mentions the MCP server without naming a tool "
            "→ prose-only."
        )

    def test_5a_has_no_mcp_url(self) -> None:
        """Step 5a introduces no MCP server URL (security guard)."""
        section = _extract_5a(_MODULE_02)
        assert _no_mcp_url(section), "Module 2 Step 5a must not contain an MCP URL"


class TestModule2Step5cNoLicenseEnforcedMcp:
    """Module 2 Step 5c "no license" must name ``search_docs`` in a directive.

    **Validates: Requirements 1.3, 2.3**

    On UNFIXED code this FAILS — the branch says "the Senzing MCP server can
    guide you through requesting a larger evaluation license" as prose with no
    tool named.
    """

    def test_5c_no_license_section_exists(self) -> None:
        """Precondition: the 5c "no license" branch can be extracted."""
        assert _extract_5c_no_license(_MODULE_02), (
            "Could not extract Module 2 Step 5c 'no license' branch"
        )

    def test_5c_no_license_has_enforced_search_docs_directive(self) -> None:
        """The 5c "no license" branch names ``search_docs`` in a directive."""
        section = _extract_5c_no_license(_MODULE_02)
        assert _has_enforced_mcp_step(section), (
            "Module 2 Step 5c 'no license' branch does NOT instruct the agent "
            f"to consult '{_LICENSE_TOOL}'. The unfixed text mentions the MCP "
            "server only as awareness prose alongside email contacts.\n"
            f"Section:\n{section[:500]}"
        )

    def test_5c_no_license_is_not_prose_only(self) -> None:
        """The 5c "no license" branch is not a prose-only MCP mention."""
        section = _extract_5c_no_license(_MODULE_02)
        assert not _is_prose_only(section), (
            "Module 2 Step 5c 'no license' branch mentions the MCP server "
            "without naming a tool → prose-only."
        )

    def test_5c_no_license_has_no_mcp_url(self) -> None:
        """The 5c "no license" branch introduces no MCP server URL (security guard)."""
        section = _extract_5c_no_license(_MODULE_02)
        assert _no_mcp_url(section), (
            "Module 2 Step 5c 'no license' branch must not contain an MCP URL"
        )


class TestSenz9000CapacityRouting:
    """A ``SENZ9000`` capacity situation must route to a ``search_docs`` consultation.

    **Validates: Requirements 1.4, 2.4, 2.5**

    On UNFIXED code this FAILS — the license-insufficient handling reachable on
    a capacity error provides guidance as prose with no MCP tool consultation.
    """

    def test_senz9000_situation_is_bug_condition(self) -> None:
        """A SENZ9000 capacity error with no sufficient license is a bug condition."""
        situation = LicenseSituation(
            total_record_count=501, has_sufficient_license=False, error_code="SENZ9000"
        )
        assert is_bug_condition(situation)

    def test_senz9000_routes_to_enforced_search_docs(self) -> None:
        """The SENZ9000-mapped path enforces a ``search_docs`` consultation."""
        situation = LicenseSituation(
            total_record_count=501, has_sufficient_license=False, error_code="SENZ9000"
        )
        label, section = steering_path_for(situation)
        assert section, f"{label}: section could not be extracted"
        assert _has_enforced_mcp_step(section), (
            f"{label}: SENZ9000 capacity routing does NOT reach an enforced "
            f"'{_LICENSE_TOOL}' consultation.\n"
            f"Section:\n{section[:500]}"
        )
        assert _tool_name_is_confirmed(_LICENSE_TOOL), (
            f"Tool name '{_LICENSE_TOOL}' is not confirmed in the decision tree"
        )
        assert _no_mcp_url(section), f"{label}: must not contain an MCP URL"


class TestToolNameConfirmation:
    """The referenced tool name resolves against ``mcp-tool-decision-tree.md``.

    **Validates: Requirement 2.5**
    """

    def test_search_docs_is_confirmed(self) -> None:
        """``search_docs`` is present in the parsed decision-tree tool set."""
        assert _tool_name_is_confirmed(_LICENSE_TOOL), (
            f"'{_LICENSE_TOOL}' must resolve against the mcp-tool-decision-tree.md "
            "tool set"
        )

    def test_invented_tool_name_is_not_confirmed(self) -> None:
        """An invented tool name does not resolve (guards against fabrication)."""
        assert not _tool_name_is_confirmed("request_license"), (
            "An invented tool name must NOT resolve against the decision tree"
        )
