"""Tests for MCP tool inventory drift (signature + preservation guards).

This file is built in stages by the `mcp-tool-inventory-drift` bugfix spec:

  * SIGNATURE SECTION (task 2 — this file): scoped property tests that encode
    the live-confirmed `analyze_record` call signature and surface the three
    divergent signatures currently documented across steering and module docs.
    These tests are EXPECTED TO FAIL on the unfixed docs (failure proves the
    bug exists) and will validate the fix once the signatures are normalized.
  * PRESERVATION SECTION (task 3 — added later): baseline assertions that the
    already-correct 13-tool inventory, counts, and routing remain unchanged.

Live source of truth (get_capabilities(version="current"), server v1.24.0):
  analyze_record(file_paths=[...], workspace_dir="<writable-dir>", version="current")
    - file_paths: optional array
    - workspace_dir: REQUIRED
    - version: optional
    - NO `record=` parameter, NO `data_source=` parameter

**Validates: Requirements 1.1, 2.1 (Property 1 — Bug Condition / Fix-Checking)**
"""

from __future__ import annotations

import re
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths — relative to this test file's location (scripts/ + sys.path style)
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR = Path(__file__).resolve().parent.parent

# The three signature-bearing files that document an `analyze_record` call.
# The defect is deterministic across this fixed set, so the property is scoped
# to iterate over these concrete files rather than generating file paths.
_DECISION_TREE = _BOOTCAMP_DIR / "steering" / "mcp-tool-decision-tree.md"
_MODULE_5 = _BOOTCAMP_DIR / "docs" / "modules" / "MODULE_5_DATA_QUALITY_AND_MAPPING.md"
_TROUBLESHOOTING = _BOOTCAMP_DIR / "steering" / "troubleshooting-commands.md"

_SIGNATURE_FILES = (_DECISION_TREE, _MODULE_5, _TROUBLESHOOTING)

# ---------------------------------------------------------------------------
# Helpers — extract `analyze_record` call examples and check the live schema
# ---------------------------------------------------------------------------


def _extract_analyze_record_examples(text: str) -> list[str]:
    """Return the argument text of every `analyze_record` call example.

    Handles both documented call styles:
      * Python kwarg form: ``analyze_record(file_paths=[...], workspace_dir=...)``
        — the balanced-parenthesis argument list is captured.
      * JSON call-pattern form: ``{ "tool": "analyze_record", ... }`` — the
        enclosing JSON object (which carries the call's arguments) is captured.

    Bare prose references such as "use ``analyze_record``" (no arguments) are
    intentionally ignored — they name the tool without documenting a signature.

    Args:
        text: Full text of a documentation file.

    Returns:
        A list of argument/payload strings, one per call example found.
    """
    examples: list[str] = []

    # Python kwarg form: analyze_record( ... )
    for match in re.finditer(r"analyze_record\s*\(", text):
        open_paren = match.end() - 1
        depth = 0
        i = open_paren
        while i < len(text):
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        examples.append(text[open_paren + 1:i])

    # JSON call-pattern form: { "tool": "analyze_record", ... }
    for match in re.finditer(r'"tool"\s*:\s*"analyze_record"', text):
        left = text.rfind("{", 0, match.start())
        right = text.find("}", match.end())
        if left != -1 and right != -1:
            examples.append(text[left:right + 1])

    return examples


def _signature_violations(args: str) -> list[str]:
    """Return the list of live-schema violations for one call example.

    The example is valid only when it contains both ``file_paths`` and
    ``workspace_dir`` and contains neither a ``record`` nor a ``data_source``
    parameter (in Python kwarg or JSON-key form). Parameter detection is
    case-sensitive so uppercase JSON *values* like ``DATA_SOURCE`` / ``RECORD_ID``
    inside a record string are not mistaken for parameters.

    Args:
        args: The captured argument text / JSON payload of a call example.

    Returns:
        A list of human-readable violation messages (empty when valid).
    """
    violations: list[str] = []

    if "file_paths" not in args:
        violations.append("missing required-by-fix `file_paths`")
    if "workspace_dir" not in args:
        violations.append("missing required `workspace_dir`")
    if "record=" in args or '"record"' in args:
        violations.append("uses forbidden `record=` parameter")
    if "data_source=" in args or '"data_source"' in args:
        violations.append("uses forbidden `data_source=` parameter")

    return violations


# ---------------------------------------------------------------------------
# SIGNATURE SECTION (task 2)
# Property 1 — Bug Condition: the documented analyze_record signature must
# match the live schema in every signature-bearing file.
#
# EXPECTED on UNFIXED docs: these tests FAIL (proving the three divergent
# signatures exist). After normalization (task 4.2) they PASS (Fix-Checking).
#
# **Validates: Requirements 1.1, 2.1**
# ---------------------------------------------------------------------------


class TestAnalyzeRecordSignature:
    """Every documented `analyze_record` call must match the live schema."""

    def test_each_signature_file_has_a_call_example(self) -> None:
        """Each of the three files must document at least one call example."""
        for path in _SIGNATURE_FILES:
            text = path.read_text(encoding="utf-8")
            examples = _extract_analyze_record_examples(text)
            assert examples, (
                f"No analyze_record call example found in "
                f"{path.relative_to(_BOOTCAMP_DIR)}"
            )

    def test_decision_tree_signature_matches_live_schema(self) -> None:
        """steering/mcp-tool-decision-tree.md uses the live analyze_record schema."""
        self._assert_file_signatures(_DECISION_TREE)

    def test_module_5_signature_matches_live_schema(self) -> None:
        """docs/modules/MODULE_5_*.md uses the live analyze_record schema."""
        self._assert_file_signatures(_MODULE_5)

    def test_troubleshooting_signature_matches_live_schema(self) -> None:
        """steering/troubleshooting-commands.md uses the live analyze_record schema."""
        self._assert_file_signatures(_TROUBLESHOOTING)

    @staticmethod
    def _assert_file_signatures(path: Path) -> None:
        """Assert every analyze_record example in `path` matches the live schema."""
        text = path.read_text(encoding="utf-8")
        examples = _extract_analyze_record_examples(text)
        for args in examples:
            violations = _signature_violations(args)
            assert not violations, (
                f"analyze_record signature in {path.relative_to(_BOOTCAMP_DIR)} "
                f"diverges from the live schema "
                f"(file_paths + workspace_dir; no record=/data_source=): "
                f"{'; '.join(violations)}\n  example args: {args.strip()!r}"
            )


# ---------------------------------------------------------------------------
# SIGNATURE SECTION — Scoped property-based test
# The defect is deterministic across a fixed set of three files, so the
# property iterates over those concrete files instead of generating paths.
# ---------------------------------------------------------------------------


@st.composite
def st_signature_file(draw: st.DrawFn) -> Path:
    """Draw one of the three concrete signature-bearing files."""
    return draw(st.sampled_from(_SIGNATURE_FILES))


class TestAnalyzeRecordSignaturePropertyBased:
    """PBT — for every signature-bearing file, every call matches the live schema.

    **Validates: Requirements 1.1, 2.1**
    """

    @given(path=st_signature_file())
    @settings(max_examples=20)
    def test_signature_matches_live_schema(self, path: Path) -> None:
        """For any signature-bearing file, all analyze_record calls are live-valid."""
        text = path.read_text(encoding="utf-8")
        examples = _extract_analyze_record_examples(text)
        assert examples, (
            f"No analyze_record call example found in "
            f"{path.relative_to(_BOOTCAMP_DIR)}"
        )
        for args in examples:
            violations = _signature_violations(args)
            assert not violations, (
                f"analyze_record signature in {path.relative_to(_BOOTCAMP_DIR)} "
                f"diverges from the live schema: {'; '.join(violations)}\n"
                f"  example args: {args.strip()!r}"
            )

# ===========================================================================
# PRESERVATION SECTION (task 3)
# Property 2 — Preservation: the already-correct 13-tool inventory, counts,
# validation routing, the submit_feedback disabled-by-default config, the
# analyze-after-mapping hook prompt, and the hook-sync gate are unchanged.
#
# Observation-first methodology: these assertions encode what the UNFIXED
# content already contains (cases where isBugCondition(X) is FALSE), so they
# PASS now and must continue to PASS after the fix (no regression).
#
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7 (Property 2)**
# ===========================================================================

import subprocess
import sys

# ---------------------------------------------------------------------------
# Preservation paths
# ---------------------------------------------------------------------------

_REPO_ROOT = _BOOTCAMP_DIR.parent
_POWER_MD = _BOOTCAMP_DIR / "POWER.md"
_ARCHITECTURE = _BOOTCAMP_DIR / "docs" / "guides" / "ARCHITECTURE.md"
_HOOK_ANALYZE = _BOOTCAMP_DIR / "hooks" / "analyze-after-mapping.kiro.hook"
_SYNC_HOOK_REGISTRY = _BOOTCAMP_DIR / "scripts" / "sync_hook_registry.py"

# ---------------------------------------------------------------------------
# Canonical live inventory — confirmed via get_capabilities(version="current")
# (server v1.24.0): 13 tools, no `lint_record`, validation tool = analyze_record.
# Hard-coded here as the observed baseline; task 4.1 introduces the shared
# canonical module that these assertions will later import.
# ---------------------------------------------------------------------------

_EXPECTED_TOOLS = (
    "get_capabilities",
    "mapping_workflow",
    "analyze_record",
    "download_resource",
    "explain_error_code",
    "search_docs",
    "find_examples",
    "generate_scaffold",
    "get_sample_data",
    "get_sdk_reference",
    "sdk_guide",
    "reporting_guide",
    "submit_feedback",
)
_EXPECTED_COUNT = 13
_DISABLED_TOOL = "submit_feedback"
_VALIDATION_TOOL = "analyze_record"
_PHANTOM_TOOL = "lint_record"

# ---------------------------------------------------------------------------
# Section-extraction helpers
# ---------------------------------------------------------------------------


def _extract_section(text: str, heading: str) -> str:
    """Return the body of a Markdown section starting at `heading`.

    The section runs from `heading` to the next heading of the same or a
    higher level (or end of file).

    Args:
        text: Full Markdown text.
        heading: The exact heading line to anchor on (e.g. "## Available MCP Tools").

    Returns:
        The section text including its heading, or "" when not found.
    """
    level = len(heading) - len(heading.lstrip("#"))
    pattern = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.start()
    # Next heading at the same or higher level (<= current level of '#').
    next_pattern = re.compile(rf"^#{{1,{level}}} ", re.MULTILINE)
    nxt = next_pattern.search(text, match.end())
    return text[start:nxt.start()] if nxt else text[start:]


def _power_md_tool_bullets(text: str) -> list[str]:
    """Return the tool names from the "Available MCP Tools" bullet list.

    Only list items of the form ``- `tool_name` - ...`` are returned; prose
    references inside the same section (e.g. in "Key rules") are ignored.

    Args:
        text: Full POWER.md text.

    Returns:
        The ordered list of bulleted tool names.
    """
    section = _extract_section(text, "## Available MCP Tools")
    return re.findall(r"^- `([a-z_]+)`", section, re.MULTILINE)


def _architecture_category_tools(text: str) -> list[str]:
    """Return the tool names listed in ARCHITECTURE.md "MCP Tool Categories".

    Args:
        text: Full ARCHITECTURE.md text.

    Returns:
        The list of tool names from the category tables (one per table row).
    """
    section = _extract_section(text, "### MCP Tool Categories")
    return re.findall(r"^\| `([a-z_]+)` \|", section, re.MULTILINE)


# ---------------------------------------------------------------------------
# Baselines — snapshot the UNFIXED content for byte-for-byte comparison
# ---------------------------------------------------------------------------

_UNFIXED_POWER_MD = _POWER_MD.read_text(encoding="utf-8")
_UNFIXED_ARCHITECTURE = _ARCHITECTURE.read_text(encoding="utf-8")
_UNFIXED_DECISION_TREE_TEXT = _DECISION_TREE.read_text(encoding="utf-8")
_UNFIXED_HOOK = _HOOK_ANALYZE.read_text(encoding="utf-8")

_UNFIXED_POWER_TOOLS_SECTION = _extract_section(
    _UNFIXED_POWER_MD, "## Available MCP Tools"
)
_UNFIXED_ARCH_CATEGORIES_SECTION = _extract_section(
    _UNFIXED_ARCHITECTURE, "### MCP Tool Categories"
)


# ---------------------------------------------------------------------------
# Preservation Test 1 - POWER.md "Available MCP Tools" inventory unchanged
# ---------------------------------------------------------------------------


class TestPowerMdInventoryPreserved:
    """POWER.md lists exactly the live 13 tools - unchanged by the fix.

    **Validates: Requirements 3.1, 3.2, 3.4**
    """

    def test_power_md_lists_exactly_the_13_live_tools(self) -> None:
        """POWER.md "Available MCP Tools" lists exactly the 13 live tools."""
        bullets = _power_md_tool_bullets(_POWER_MD.read_text(encoding="utf-8"))
        assert len(bullets) == _EXPECTED_COUNT, (
            f"POWER.md lists {len(bullets)} tools, expected {_EXPECTED_COUNT}: "
            f"{bullets}"
        )
        assert set(bullets) == set(_EXPECTED_TOOLS), (
            "POWER.md tool set diverged from the live 13-tool inventory.\n"
            f"  unexpected: {sorted(set(bullets) - set(_EXPECTED_TOOLS))}\n"
            f"  missing:    {sorted(set(_EXPECTED_TOOLS) - set(bullets))}"
        )

    def test_power_md_has_no_phantom_lint_record(self) -> None:
        """POWER.md must not introduce a phantom `lint_record` tool."""
        assert _PHANTOM_TOOL not in _POWER_MD.read_text(encoding="utf-8"), (
            f"POWER.md must not reference the non-existent `{_PHANTOM_TOOL}` tool"
        )

    def test_power_md_submit_feedback_disabled_by_default(self) -> None:
        """`submit_feedback` stays disabled-by-default via mcp.json disabledTools."""
        text = _POWER_MD.read_text(encoding="utf-8")
        assert f'"disabledTools": ["{_DISABLED_TOOL}"]' in text, (
            f"POWER.md mcp.json block must keep `{_DISABLED_TOOL}` in disabledTools"
        )

    def test_power_md_tools_section_byte_for_byte_unchanged(self) -> None:
        """The whole "Available MCP Tools" section matches the snapshot baseline."""
        current = _extract_section(
            _POWER_MD.read_text(encoding="utf-8"), "## Available MCP Tools"
        )
        assert current == _UNFIXED_POWER_TOOLS_SECTION, (
            "POWER.md 'Available MCP Tools' section changed from the baseline "
            "(names, order, or descriptions must be preserved)."
        )


# ---------------------------------------------------------------------------
# Preservation Test 2 - ARCHITECTURE.md count + categories + routing unchanged
# ---------------------------------------------------------------------------


class TestArchitectureInventoryPreserved:
    """ARCHITECTURE.md states 13 tools and routes validation to analyze_record.

    **Validates: Requirements 3.1, 3.2, 3.3**
    """

    def test_architecture_states_13_tools(self) -> None:
        """ARCHITECTURE.md "MCP Tool Categories" states exactly 13 tools."""
        text = _ARCHITECTURE.read_text(encoding="utf-8")
        assert "exposes 13 tools" in text, (
            "ARCHITECTURE.md must continue to state the MCP server exposes 13 tools"
        )
        assert "14 tools" not in text, (
            "ARCHITECTURE.md must never state 14 tools"
        )

    def test_architecture_categories_list_the_13_live_tools(self) -> None:
        """The five category tables list exactly the 13 live tools."""
        tools = _architecture_category_tools(_ARCHITECTURE.read_text(encoding="utf-8"))
        assert len(tools) == _EXPECTED_COUNT, (
            f"ARCHITECTURE.md categories list {len(tools)} tools, "
            f"expected {_EXPECTED_COUNT}: {tools}"
        )
        assert set(tools) == set(_EXPECTED_TOOLS), (
            "ARCHITECTURE.md category tool set diverged from the live inventory.\n"
            f"  unexpected: {sorted(set(tools) - set(_EXPECTED_TOOLS))}\n"
            f"  missing:    {sorted(set(_EXPECTED_TOOLS) - set(tools))}"
        )

    def test_architecture_routes_validation_to_analyze_record(self) -> None:
        """ARCHITECTURE.md routes "validate a mapped record" to analyze_record."""
        text = _ARCHITECTURE.read_text(encoding="utf-8")
        expected_row = (
            f"| `{_VALIDATION_TOOL}` | "
            "Validate a mapped record against the Entity Spec |"
        )
        assert expected_row in text, (
            "ARCHITECTURE.md must keep analyze_record as the mapped-record validator"
        )

    def test_architecture_has_no_phantom_lint_record(self) -> None:
        """ARCHITECTURE.md must not introduce a phantom `lint_record` tool."""
        assert _PHANTOM_TOOL not in _ARCHITECTURE.read_text(encoding="utf-8"), (
            f"ARCHITECTURE.md must not reference `{_PHANTOM_TOOL}`"
        )

    def test_architecture_categories_section_unchanged(self) -> None:
        """The "MCP Tool Categories" section matches the snapshot baseline."""
        current = _extract_section(
            _ARCHITECTURE.read_text(encoding="utf-8"), "### MCP Tool Categories"
        )
        assert current == _UNFIXED_ARCH_CATEGORIES_SECTION, (
            "ARCHITECTURE.md 'MCP Tool Categories' section changed from baseline"
        )


# ---------------------------------------------------------------------------
# Preservation Test 3 - decision tree validation routing unchanged
# ---------------------------------------------------------------------------


class TestDecisionTreeRoutingPreserved:
    """The decision tree routes mapped-record validation to analyze_record.

    **Validates: Requirements 3.3**

    Only the Data Preparation routing node is asserted here. The
    `analyze_record` call signature in this same file is intentionally left
    to the SIGNATURE SECTION (task 2) - it is a bug condition and is expected
    to fail until task 4.2 normalizes it.
    """

    def test_data_prep_routes_validation_to_analyze_record(self) -> None:
        """Data Preparation node routes record validation to analyze_record."""
        text = _DECISION_TREE.read_text(encoding="utf-8")
        prep = _extract_section(text, "### Data Preparation")
        assert prep, "Data Preparation section not found in decision tree"
        assert "Validating a mapped record for correctness?" in prep, (
            "Data Preparation must keep the mapped-record validation branch"
        )
        # The validation branch routes to analyze_record (next routed line).
        match = re.search(
            r"Validating a mapped record for correctness\?\s*\n[^\n]*"
            rf"{re.escape(_VALIDATION_TOOL)}",
            prep,
        )
        assert match, (
            "Data Preparation validation branch must route to analyze_record"
        )

    def test_decision_tree_has_no_phantom_lint_record(self) -> None:
        """The decision tree must not introduce a phantom `lint_record` tool."""
        assert _PHANTOM_TOOL not in _DECISION_TREE.read_text(encoding="utf-8"), (
            f"mcp-tool-decision-tree.md must not reference `{_PHANTOM_TOOL}`"
        )

    def test_decision_tree_total_count_never_14(self) -> None:
        """The decision tree never states a 14-tool total."""
        assert "14 MCP tools" not in _DECISION_TREE.read_text(encoding="utf-8"), (
            "mcp-tool-decision-tree.md must never state 14 MCP tools"
        )


# ---------------------------------------------------------------------------
# Preservation Test 4 - analyze-after-mapping hook prompt unchanged
# ---------------------------------------------------------------------------


class TestAnalyzeAfterMappingHookPreserved:
    """The analyze-after-mapping hook keeps using analyze_record for validation.

    **Validates: Requirements 3.5**
    """

    def test_hook_uses_analyze_record_for_validation_and_quality(self) -> None:
        """Hook prompt uses analyze_record for validation + quality analysis."""
        text = _HOOK_ANALYZE.read_text(encoding="utf-8")
        assert "use the analyze_record MCP tool to validate" in text, (
            "Hook prompt must keep routing validation to analyze_record"
        )
        assert "feature distribution, attribute coverage, and data quality" in text, (
            "Hook prompt must keep the data-quality analysis instructions"
        )
        assert "Senzing Generic Entity Specification" in text, (
            "Hook prompt must keep the Entity Specification conformance check"
        )

    def test_hook_has_no_phantom_lint_record(self) -> None:
        """The hook must not reference a phantom `lint_record` tool."""
        assert _PHANTOM_TOOL not in _HOOK_ANALYZE.read_text(encoding="utf-8"), (
            f"analyze-after-mapping hook must not reference `{_PHANTOM_TOOL}`"
        )

    def test_hook_file_byte_for_byte_unchanged(self) -> None:
        """The hook file matches the snapshot baseline."""
        assert _HOOK_ANALYZE.read_text(encoding="utf-8") == _UNFIXED_HOOK, (
            "analyze-after-mapping.kiro.hook changed from the baseline"
        )


# ---------------------------------------------------------------------------
# Preservation Test 5 - hook-sync registry gate stays clean
# ---------------------------------------------------------------------------


class TestHookSyncGatePreserved:
    """`sync_hook_registry.py --verify` stays clean (registries in sync).

    **Validates: Requirements 3.5, 3.6**
    """

    def test_sync_hook_registry_verify_is_clean(self) -> None:
        """Running sync_hook_registry.py --verify exits 0 (registries in sync)."""
        result = subprocess.run(
            [sys.executable, str(_SYNC_HOOK_REGISTRY), "--verify"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            "sync_hook_registry.py --verify must exit 0 (registries in sync).\n"
            f"  stdout: {result.stdout}\n  stderr: {result.stderr}"
        )


# ---------------------------------------------------------------------------
# Preservation Test 6 - MCP URL confinement (3.7)
# ---------------------------------------------------------------------------


class TestMcpUrlConfinementPreserved:
    """The MCP server URL stays confined to mcp.json as the single source.

    **Validates: Requirements 3.7**
    """

    def test_mcp_host_present_in_mcp_json(self) -> None:
        """mcp.json contains the canonical Senzing MCP server host."""
        # Host assembled from parts so the literal URL never appears in this
        # test file; mcp.json remains the single source of truth for the URL.
        host = "mcp." + "senzing.com"
        mcp_json = _BOOTCAMP_DIR / "mcp.json"
        text = mcp_json.read_text(encoding="utf-8")
        assert host in text, (
            "mcp.json must contain the canonical Senzing MCP server host"
        )


# ---------------------------------------------------------------------------
# PRESERVATION SECTION - Scoped property-based tests
# Each live tool is preserved across every documented inventory surface.
# ---------------------------------------------------------------------------


@st.composite
def st_live_tool(draw: st.DrawFn) -> str:
    """Draw one of the 13 live MCP tool names."""
    return draw(st.sampled_from(_EXPECTED_TOOLS))


class TestInventoryPreservationPropertyBased:
    """PBT - every live tool stays listed in POWER.md and ARCHITECTURE.md.

    **Validates: Requirements 3.1, 3.2 (Property 2 - Preservation)**
    """

    @given(tool=st_live_tool())
    @settings(max_examples=20)
    def test_live_tool_in_power_md_inventory(self, tool: str) -> None:
        """For any live tool, POWER.md "Available MCP Tools" still lists it."""
        bullets = _power_md_tool_bullets(_POWER_MD.read_text(encoding="utf-8"))
        assert tool in bullets, (
            f"Live tool `{tool}` missing from POWER.md 'Available MCP Tools'"
        )

    @given(tool=st_live_tool())
    @settings(max_examples=20)
    def test_live_tool_in_architecture_categories(self, tool: str) -> None:
        """For any live tool, ARCHITECTURE.md categories still list it."""
        tools = _architecture_category_tools(
            _ARCHITECTURE.read_text(encoding="utf-8")
        )
        assert tool in tools, (
            f"Live tool `{tool}` missing from ARCHITECTURE.md 'MCP Tool Categories'"
        )

# ===========================================================================
# DRIFT-GUARD SECTION (task 4.3)
# Property 1 — Fix-Checking: the documented MCP tool inventory, total count,
# validation routing, and analyze_record signature must match the canonical
# single source of truth (scripts/mcp_tool_inventory.py), which was confirmed
# against the live get_capabilities(version="current") response.
#
# The KEY value of this section over the preservation section above is that it
# sources every expectation from the IMPORTED canonical module constants
# (ACTIVE_TOOLS / ALL_TOOLS / TOTAL_COUNT / VALIDATION_TOOL) rather than from
# hard-coded literals. Drift in either direction — dropping a real tool, adding
# a phantom tool such as `lint_record`, or reintroducing a stale 12/14-tool
# total — fails CI against this single source.
#
# **Validates: Requirements 1.2, 2.2 (Property 1 — Fix-Checking)**
# ===========================================================================

# Import the canonical inventory module via the scripts/ + sys.path pattern
# (scripts are not packages, so the directory is added to sys.path directly).
_SCRIPTS_DIR = str(_BOOTCAMP_DIR / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import mcp_tool_inventory as inventory  # noqa: E402  (import after sys.path setup)


def _count_phrases(text: str, count: int) -> list[str]:
    """Return every "<count> tools" / "<count> MCP tools" phrase found in `text`.

    Used to detect stale/forbidden total-count statements (e.g. a bare "12
    tools" total or any "14 tools" total) regardless of surrounding wording.

    Args:
        text: Full text of a documentation file.
        count: The integer count to search for as a tool total.

    Returns:
        A list of matched phrases (empty when the count is not stated).
    """
    pattern = re.compile(rf"\b{count}\s+(?:MCP\s+)?tools?\b")
    return pattern.findall(text)


# ---------------------------------------------------------------------------
# Drift Guard 1 — POWER.md "Available MCP Tools" lists exactly ALL_TOOLS
# ---------------------------------------------------------------------------


class TestPowerMdInventoryGuard:
    """POWER.md lists exactly the canonical ALL_TOOLS inventory.

    Sourced from `mcp_tool_inventory.ALL_TOOLS` — fails if `lint_record` (or
    any phantom) is added or a real tool is dropped.

    **Validates: Requirements 1.2, 2.2**
    """

    def test_power_md_lists_exactly_all_tools(self) -> None:
        """POWER.md "Available MCP Tools" lists exactly ALL_TOOLS (order-independent)."""
        bullets = _power_md_tool_bullets(_POWER_MD.read_text(encoding="utf-8"))
        assert set(bullets) == set(inventory.ALL_TOOLS), (
            "POWER.md inventory diverged from canonical ALL_TOOLS.\n"
            f"  unexpected (phantom/dropped-from-canonical): "
            f"{sorted(set(bullets) - set(inventory.ALL_TOOLS))}\n"
            f"  missing (real tool dropped): "
            f"{sorted(set(inventory.ALL_TOOLS) - set(bullets))}"
        )

    def test_power_md_lists_exactly_total_count_tools(self) -> None:
        """POWER.md lists exactly TOTAL_COUNT bulleted tools."""
        bullets = _power_md_tool_bullets(_POWER_MD.read_text(encoding="utf-8"))
        assert len(bullets) == inventory.TOTAL_COUNT, (
            f"POWER.md lists {len(bullets)} tools, canonical TOTAL_COUNT is "
            f"{inventory.TOTAL_COUNT}: {bullets}"
        )


# ---------------------------------------------------------------------------
# Drift Guard 2 — decision tree references every ACTIVE_TOOLS tool
# ---------------------------------------------------------------------------


class TestDecisionTreeInventoryGuard:
    """The decision tree references every routable tool in ACTIVE_TOOLS.

    Sourced from `mcp_tool_inventory.ACTIVE_TOOLS`.

    **Validates: Requirements 1.2, 2.2**
    """

    def test_decision_tree_references_every_active_tool(self) -> None:
        """Every ACTIVE_TOOLS tool is referenced in the decision tree."""
        text = _DECISION_TREE.read_text(encoding="utf-8")
        missing = [tool for tool in inventory.ACTIVE_TOOLS if tool not in text]
        assert not missing, (
            "mcp-tool-decision-tree.md is missing canonical ACTIVE_TOOLS: "
            f"{missing}"
        )


# ---------------------------------------------------------------------------
# Drift Guard 3 — ARCHITECTURE.md categories list ALL_TOOLS and state TOTAL_COUNT
# ---------------------------------------------------------------------------


class TestArchitectureInventoryGuard:
    """ARCHITECTURE.md categories list exactly ALL_TOOLS and state TOTAL_COUNT.

    Sourced from `mcp_tool_inventory.ALL_TOOLS` and `TOTAL_COUNT`.

    **Validates: Requirements 1.2, 2.2**
    """

    def test_architecture_categories_list_exactly_all_tools(self) -> None:
        """ARCHITECTURE.md "MCP Tool Categories" lists exactly ALL_TOOLS."""
        tools = _architecture_category_tools(_ARCHITECTURE.read_text(encoding="utf-8"))
        assert set(tools) == set(inventory.ALL_TOOLS), (
            "ARCHITECTURE.md categories diverged from canonical ALL_TOOLS.\n"
            f"  unexpected: {sorted(set(tools) - set(inventory.ALL_TOOLS))}\n"
            f"  missing:    {sorted(set(inventory.ALL_TOOLS) - set(tools))}"
        )

    def test_architecture_states_total_count(self) -> None:
        """ARCHITECTURE.md states the canonical TOTAL_COUNT (e.g. "exposes 13 tools")."""
        text = _ARCHITECTURE.read_text(encoding="utf-8")
        assert f"exposes {inventory.TOTAL_COUNT} tools" in text, (
            f"ARCHITECTURE.md must state it exposes {inventory.TOTAL_COUNT} tools"
        )


# ---------------------------------------------------------------------------
# Drift Guard 4 — total-count statements are mutually consistent at TOTAL_COUNT
# ---------------------------------------------------------------------------


class TestTotalCountConsistencyGuard:
    """Total-count statements equal TOTAL_COUNT across the three doc surfaces.

    No "14" total anywhere; no bare "12 tools" stated as a *total* (the decision
    tree's "12" must remain qualified as active routable tools with the 13th
    disabled tool making the canonical TOTAL_COUNT). Sourced from
    `mcp_tool_inventory.TOTAL_COUNT` and `len(ACTIVE_TOOLS)`.

    **Validates: Requirements 1.2, 2.2**
    """

    _COUNT_FILES = (_POWER_MD, _ARCHITECTURE, _DECISION_TREE)

    def test_no_forbidden_14_total_anywhere(self) -> None:
        """No file states a 14-tool total (the refuted phantom-inflated count)."""
        forbidden = inventory.TOTAL_COUNT + 1  # 14 — the withdrawn premise's count
        for path in self._COUNT_FILES:
            text = path.read_text(encoding="utf-8")
            phrases = _count_phrases(text, forbidden)
            assert not phrases, (
                f"{path.relative_to(_BOOTCAMP_DIR)} states a forbidden "
                f"{forbidden}-tool total: {phrases}"
            )

    def test_architecture_total_equals_canonical_count(self) -> None:
        """ARCHITECTURE.md's stated total equals TOTAL_COUNT (and only that)."""
        text = _ARCHITECTURE.read_text(encoding="utf-8")
        assert _count_phrases(text, inventory.TOTAL_COUNT), (
            f"ARCHITECTURE.md must state a {inventory.TOTAL_COUNT}-tool total"
        )
        # The active-count number must not be presented as the total here.
        assert not _count_phrases(text, len(inventory.ACTIVE_TOOLS)), (
            f"ARCHITECTURE.md must not state a bare "
            f"{len(inventory.ACTIVE_TOOLS)}-tool total"
        )

    def test_decision_tree_active_count_is_qualified_by_total(self) -> None:
        """Decision tree's active "12 tools" stays qualified by the 13th tool.

        The decision tree describes the routable-tool coverage as
        len(ACTIVE_TOOLS) tools; this must remain qualified by an explicit
        reference to the TOTAL_COUNT-th (disabled) tool, so the 12 is never a
        bare total. Guards against a stale bare "12 tools" total returning.
        """
        text = _DECISION_TREE.read_text(encoding="utf-8")
        active_count = len(inventory.ACTIVE_TOOLS)
        if _count_phrases(text, active_count):
            # When the active count is stated, the total must be made explicit.
            assert f"{inventory.TOTAL_COUNT}th tool" in text, (
                f"mcp-tool-decision-tree.md states {active_count} tools but does "
                f"not qualify it with the {inventory.TOTAL_COUNT}th (disabled) "
                f"tool — a bare {active_count}-tool total is forbidden"
            )


# ---------------------------------------------------------------------------
# Drift Guard 5 — validation routing targets the canonical VALIDATION_TOOL
# ---------------------------------------------------------------------------


class TestValidationRoutingGuard:
    """Validation routing targets the canonical VALIDATION_TOOL (analyze_record).

    Sourced from `mcp_tool_inventory.VALIDATION_TOOL`.

    **Validates: Requirements 1.2, 2.2**
    """

    def test_validation_tool_is_analyze_record(self) -> None:
        """The canonical VALIDATION_TOOL constant equals "analyze_record"."""
        assert inventory.VALIDATION_TOOL == "analyze_record", (
            "Canonical VALIDATION_TOOL must be analyze_record"
        )

    def test_decision_tree_data_prep_routes_validate_to_validation_tool(self) -> None:
        """The Data Preparation node routes "validate" to VALIDATION_TOOL."""
        text = _DECISION_TREE.read_text(encoding="utf-8")
        prep = _extract_section(text, "### Data Preparation")
        assert prep, "Data Preparation section not found in decision tree"
        match = re.search(
            r"Validating a mapped record for correctness\?\s*\n[^\n]*"
            rf"{re.escape(inventory.VALIDATION_TOOL)}",
            prep,
        )
        assert match, (
            "Data Preparation validation branch must route to "
            f"{inventory.VALIDATION_TOOL}"
        )


# ---------------------------------------------------------------------------
# Drift Guard 6 — analyze_record signature in the three normalized files
# ---------------------------------------------------------------------------


class TestAnalyzeRecordSignatureGuard:
    """The analyze_record signature matches the live schema in the three files.

    Overlaps with the SIGNATURE SECTION but is anchored here as a drift guard:
    every documented call in the three normalized files contains `file_paths`
    and `workspace_dir` and contains no `record=` / `data_source=`.

    **Validates: Requirements 1.2, 2.2**
    """

    def test_all_three_files_use_live_signature(self) -> None:
        """All analyze_record calls in the three files match the live schema."""
        for path in _SIGNATURE_FILES:
            text = path.read_text(encoding="utf-8")
            examples = _extract_analyze_record_examples(text)
            assert examples, (
                f"No analyze_record call example found in "
                f"{path.relative_to(_BOOTCAMP_DIR)}"
            )
            for args in examples:
                violations = _signature_violations(args)
                assert not violations, (
                    f"analyze_record signature in "
                    f"{path.relative_to(_BOOTCAMP_DIR)} diverges from the live "
                    f"schema: {'; '.join(violations)}\n"
                    f"  example args: {args.strip()!r}"
                )


# ---------------------------------------------------------------------------
# DRIFT-GUARD SECTION — Scoped property-based tests
# Sourced from the IMPORTED canonical constants (not local literals): every
# canonical tool must appear on the documented surface that owns it.
# ---------------------------------------------------------------------------


@st.composite
def st_all_tool(draw: st.DrawFn) -> str:
    """Draw one of the canonical ALL_TOOLS names."""
    return draw(st.sampled_from(inventory.ALL_TOOLS))


@st.composite
def st_active_tool(draw: st.DrawFn) -> str:
    """Draw one of the canonical ACTIVE_TOOLS names."""
    return draw(st.sampled_from(inventory.ACTIVE_TOOLS))


class TestDriftGuardPropertyBased:
    """PBT — canonical tools are guarded across the documented surfaces.

    Expectations are sourced from the imported canonical module, so a change to
    `mcp_tool_inventory` (or to the docs) that breaks alignment fails CI.

    **Validates: Requirements 1.2, 2.2 (Property 1 — Fix-Checking)**
    """

    @given(tool=st_all_tool())
    @settings(max_examples=20)
    def test_all_tool_listed_in_power_md(self, tool: str) -> None:
        """For any canonical ALL_TOOLS tool, POWER.md lists it."""
        bullets = _power_md_tool_bullets(_POWER_MD.read_text(encoding="utf-8"))
        assert tool in bullets, (
            f"Canonical tool `{tool}` missing from POWER.md 'Available MCP Tools'"
        )

    @given(tool=st_all_tool())
    @settings(max_examples=20)
    def test_all_tool_listed_in_architecture(self, tool: str) -> None:
        """For any canonical ALL_TOOLS tool, ARCHITECTURE.md categories list it."""
        tools = _architecture_category_tools(_ARCHITECTURE.read_text(encoding="utf-8"))
        assert tool in tools, (
            f"Canonical tool `{tool}` missing from ARCHITECTURE.md categories"
        )

    @given(tool=st_active_tool())
    @settings(max_examples=20)
    def test_active_tool_referenced_in_decision_tree(self, tool: str) -> None:
        """For any canonical ACTIVE_TOOLS tool, the decision tree references it."""
        text = _DECISION_TREE.read_text(encoding="utf-8")
        assert tool in text, (
            f"Canonical active tool `{tool}` missing from mcp-tool-decision-tree.md"
        )
