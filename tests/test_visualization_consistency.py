"""Example-based unit tests for visualization-consistency feature.

Validates the visualization protocol file, enforcement hook, hook-categories
registration, tracker schema, and dispatch rule references.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_PATH = _ROOT / "senzing-bootcamp" / "steering" / "visualization-protocol.md"
HOOK_PATH = _ROOT / "senzing-bootcamp" / "hooks" / "enforce-visualization-offers.kiro.hook"
REMOVED_HOOK_PATH = _ROOT / "senzing-bootcamp" / "hooks" / "offer-visualization.kiro.hook"
CATEGORIES_PATH = _ROOT / "senzing-bootcamp" / "hooks" / "hook-categories.yaml"
TRACKER_PATH = _ROOT / "config" / "visualization_tracker.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter key-value pairs from markdown text."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _parse_checkpoint_map(text: str) -> dict[str, list[dict[str, str | list[str]]]]:
    """Parse the checkpoint map YAML block from the protocol file.

    Returns a dict mapping module keys (e.g. 'module_3') to lists of checkpoint
    dicts with 'id' and 'types' fields.
    """
    # Find the YAML code block in the Checkpoint Map section
    pattern = r"## Checkpoint Map\s*\n+```yaml\s*\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return {}

    yaml_block = match.group(1)
    result: dict[str, list[dict[str, str | list[str]]]] = {}
    current_module: str | None = None
    current_checkpoint: dict[str, str | list[str]] | None = None

    for line in yaml_block.splitlines():
        # Module line: "  module_3:" (2 spaces indent)
        module_match = re.match(r"  (module_\d+):\s*$", line)
        if module_match:
            current_module = module_match.group(1)
            result[current_module] = []
            current_checkpoint = None
            continue

        # Checkpoint id line: '    - id: "m3_demo_results"' (4 spaces + dash)
        id_match = re.match(r'\s+- id:\s*"([^"]+)"', line)
        if id_match and current_module is not None:
            current_checkpoint = {"id": id_match.group(1), "types": []}
            result[current_module].append(current_checkpoint)
            continue

        # Types line: '      types: [Static_HTML_Report, ...]' (6 spaces)
        types_match = re.match(r"\s+types:\s*\[([^\]]+)\]", line)
        if types_match and current_checkpoint is not None:
            types_str = types_match.group(1)
            types_list = [t.strip() for t in types_str.split(",")]
            current_checkpoint["types"] = types_list
            continue

    return result


def _parse_hook_categories(text: str) -> dict[int, list[str]]:
    """Parse hook-categories.yaml to extract module-to-hooks mapping.

    Returns a dict mapping module numbers to lists of hook IDs.
    """
    result: dict[int, list[str]] = {}
    current_module: int | None = None
    in_modules = False

    for line in text.splitlines():
        stripped = line.strip()

        # Detect the modules: section
        if stripped == "modules:":
            in_modules = True
            continue

        if not in_modules:
            continue

        # Module number line (e.g. "  3:")
        module_match = re.match(r"\s{2}(\d+):\s*$", line)
        if module_match:
            current_module = int(module_match.group(1))
            result[current_module] = []
            continue

        # Non-numeric top-level key under modules (e.g. "  any:")
        any_match = re.match(r"\s{2}(\w+):\s*$", line)
        if any_match and not any_match.group(1).isdigit():
            current_module = None
            continue

        # Hook entry line (e.g. "    - enforce-visualization-offers")
        hook_match = re.match(r"\s{4}- (.+)$", line)
        if hook_match and current_module is not None:
            result[current_module].append(hook_match.group(1).strip())

    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def protocol_text() -> str:
    """Read the visualization protocol file content."""
    return PROTOCOL_PATH.read_text(encoding="utf-8")


@pytest.fixture
def protocol_frontmatter(protocol_text: str) -> dict[str, str]:
    """Parse frontmatter from the protocol file."""
    return _parse_frontmatter(protocol_text)


@pytest.fixture
def checkpoint_map(protocol_text: str) -> dict[str, list[dict[str, str | list[str]]]]:
    """Parse the checkpoint map from the protocol file."""
    return _parse_checkpoint_map(protocol_text)


@pytest.fixture
def hook_data() -> dict:
    """Load and parse the enforcement hook JSON."""
    with open(HOOK_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def categories_text() -> str:
    """Read hook-categories.yaml content."""
    return CATEGORIES_PATH.read_text(encoding="utf-8")


@pytest.fixture
def module_hooks(categories_text: str) -> dict[int, list[str]]:
    """Parse module-to-hooks mapping from hook-categories.yaml."""
    return _parse_hook_categories(categories_text)


# ===========================================================================
# 11.1: Protocol file exists with correct frontmatter
# ===========================================================================


class TestProtocolFileExists:
    """Verify visualization-protocol.md exists with correct frontmatter."""

    def test_protocol_file_exists(self) -> None:
        """visualization-protocol.md exists on disk."""
        assert PROTOCOL_PATH.is_file(), f"Missing: {PROTOCOL_PATH}"

    def test_frontmatter_has_inclusion_key(
        self, protocol_frontmatter: dict[str, str]
    ) -> None:
        """Frontmatter contains the 'inclusion' key."""
        assert "inclusion" in protocol_frontmatter

    def test_frontmatter_inclusion_is_manual(
        self, protocol_frontmatter: dict[str, str]
    ) -> None:
        """Frontmatter 'inclusion' value is 'manual'."""
        assert protocol_frontmatter["inclusion"] == "manual"


# ===========================================================================
# 11.2: Checkpoint map contains exactly modules 3, 5, 7, 8
# ===========================================================================


class TestCheckpointMap:
    """Verify checkpoint map has correct modules, IDs, and type mappings."""

    def test_checkpoint_map_has_exactly_four_modules(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Checkpoint map contains exactly module_3, module_5, module_7, module_8."""
        expected_modules = {"module_3", "module_5", "module_7", "module_8"}
        assert set(checkpoint_map.keys()) == expected_modules

    def test_module_3_has_one_checkpoint(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 3 has exactly one checkpoint."""
        assert len(checkpoint_map["module_3"]) == 1

    def test_module_3_checkpoint_id(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 3 checkpoint ID is m3_demo_results."""
        assert checkpoint_map["module_3"][0]["id"] == "m3_demo_results"

    def test_module_3_types(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 3 offers Static_HTML_Report and Web_Service_Dashboard."""
        types = checkpoint_map["module_3"][0]["types"]
        assert set(types) == {"Static_HTML_Report", "Web_Service_Dashboard"}

    def test_module_5_has_one_checkpoint(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 5 has exactly one checkpoint."""
        assert len(checkpoint_map["module_5"]) == 1

    def test_module_5_checkpoint_id(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 5 checkpoint ID is m5_quality_assessment."""
        assert checkpoint_map["module_5"][0]["id"] == "m5_quality_assessment"

    def test_module_5_types(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 5 offers only Static_HTML_Report."""
        types = checkpoint_map["module_5"][0]["types"]
        assert types == ["Static_HTML_Report"]

    def test_module_7_has_two_checkpoints(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 7 has exactly two checkpoints."""
        assert len(checkpoint_map["module_7"]) == 2

    def test_module_7_first_checkpoint_id(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 7 first checkpoint ID is m7_exploratory_queries."""
        assert checkpoint_map["module_7"][0]["id"] == "m7_exploratory_queries"

    def test_module_7_first_checkpoint_types(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 7 first checkpoint offers all three types."""
        types = checkpoint_map["module_7"][0]["types"]
        expected = {"Static_HTML_Report", "Interactive_D3_Graph", "Web_Service_Dashboard"}
        assert set(types) == expected

    def test_module_7_second_checkpoint_id(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 7 second checkpoint ID is m7_findings_documented."""
        assert checkpoint_map["module_7"][1]["id"] == "m7_findings_documented"

    def test_module_7_second_checkpoint_types(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 7 second checkpoint offers all three types."""
        types = checkpoint_map["module_7"][1]["types"]
        expected = {"Static_HTML_Report", "Interactive_D3_Graph", "Web_Service_Dashboard"}
        assert set(types) == expected

    def test_module_8_has_one_checkpoint(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 8 has exactly one checkpoint."""
        assert len(checkpoint_map["module_8"]) == 1

    def test_module_8_checkpoint_id(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 8 checkpoint ID is m8_performance_report."""
        assert checkpoint_map["module_8"][0]["id"] == "m8_performance_report"

    def test_module_8_types(
        self, checkpoint_map: dict[str, list[dict[str, str | list[str]]]]
    ) -> None:
        """Module 8 offers Static_HTML_Report and Web_Service_Dashboard."""
        types = checkpoint_map["module_8"][0]["types"]
        assert set(types) == {"Static_HTML_Report", "Web_Service_Dashboard"}


# ===========================================================================
# 11.3: Enforcement hook is valid JSON with correct structure
# ===========================================================================


class TestEnforcementHook:
    """Verify enforcement hook file is valid JSON with version 2.0.0."""

    def test_hook_file_exists(self) -> None:
        """enforce-visualization-offers.kiro.hook exists on disk."""
        assert HOOK_PATH.is_file(), f"Missing: {HOOK_PATH}"

    def test_hook_is_valid_json(self) -> None:
        """Hook file parses as valid JSON."""
        with open(HOOK_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_hook_version_is_2_0_0(self, hook_data: dict) -> None:
        """Hook version is 2.0.0."""
        assert hook_data["version"] == "2.0.0"

    def test_hook_when_type_is_agent_stop(self, hook_data: dict) -> None:
        """Hook when.type is agentStop."""
        assert hook_data["when"]["type"] == "agentStop"

    def test_hook_then_type_is_ask_agent(self, hook_data: dict) -> None:
        """Hook then.type is askAgent."""
        assert hook_data["then"]["type"] == "askAgent"

    def test_hook_has_name(self, hook_data: dict) -> None:
        """Hook has a non-empty name field."""
        assert "name" in hook_data
        assert len(hook_data["name"]) > 0

    def test_hook_has_description(self, hook_data: dict) -> None:
        """Hook has a non-empty description field."""
        assert "description" in hook_data
        assert len(hook_data["description"]) > 0

    def test_hook_has_prompt(self, hook_data: dict) -> None:
        """Hook has a non-empty prompt in then block."""
        assert "prompt" in hook_data["then"]
        assert len(hook_data["then"]["prompt"]) > 20


# ===========================================================================
# 11.4: offer-visualization.kiro.hook no longer exists
# ===========================================================================


class TestRemovedHook:
    """Verify offer-visualization.kiro.hook has been removed."""

    def test_offer_visualization_hook_does_not_exist(self) -> None:
        """offer-visualization.kiro.hook must not exist on disk."""
        assert not REMOVED_HOOK_PATH.exists(), (
            f"Hook should have been removed: {REMOVED_HOOK_PATH}"
        )


# ===========================================================================
# 11.5: hook-categories.yaml has enforce-visualization-offers under 3, 5, 7, 8
# ===========================================================================


class TestHookCategoriesVisualization:
    """Verify hook-categories.yaml lists enforce-visualization-offers correctly."""

    def test_module_3_has_enforce_hook(self, module_hooks: dict[int, list[str]]) -> None:
        """Module 3 lists enforce-visualization-offers."""
        assert "enforce-visualization-offers" in module_hooks.get(3, [])

    def test_module_5_has_enforce_hook(self, module_hooks: dict[int, list[str]]) -> None:
        """Module 5 lists enforce-visualization-offers."""
        assert "enforce-visualization-offers" in module_hooks.get(5, [])

    def test_module_7_has_enforce_hook(self, module_hooks: dict[int, list[str]]) -> None:
        """Module 7 lists enforce-visualization-offers."""
        assert "enforce-visualization-offers" in module_hooks.get(7, [])

    def test_module_8_has_enforce_hook(self, module_hooks: dict[int, list[str]]) -> None:
        """Module 8 lists enforce-visualization-offers."""
        assert "enforce-visualization-offers" in module_hooks.get(8, [])


# ===========================================================================
# 11.6: Tracker schema validation
# ===========================================================================


class TestTrackerSchema:
    """Verify tracker schema: required fields, valid status values, transitions."""

    REQUIRED_FIELDS = {"module", "checkpoint_id", "timestamp", "status"}
    VALID_STATUSES = {"offered", "accepted", "declined", "generated"}
    VALID_TRANSITIONS = {
        ("offered", "accepted"),
        ("offered", "declined"),
        ("accepted", "generated"),
    }

    def test_tracker_file_exists(self) -> None:
        """visualization_tracker.json exists on disk."""
        assert TRACKER_PATH.is_file(), f"Missing: {TRACKER_PATH}"

    def test_tracker_is_valid_json(self) -> None:
        """Tracker file parses as valid JSON."""
        with open(TRACKER_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_tracker_has_version(self) -> None:
        """Tracker has a version field."""
        with open(TRACKER_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_tracker_has_offers_array(self) -> None:
        """Tracker has an offers array."""
        with open(TRACKER_PATH, encoding="utf-8") as f:
            data = json.load(f)
        assert "offers" in data
        assert isinstance(data["offers"], list)

    def test_required_fields_defined(self) -> None:
        """Required fields are module, checkpoint_id, timestamp, status."""
        assert self.REQUIRED_FIELDS == {"module", "checkpoint_id", "timestamp", "status"}

    def test_valid_status_enum_values(self) -> None:
        """Valid status values are offered, accepted, declined, generated."""
        assert self.VALID_STATUSES == {"offered", "accepted", "declined", "generated"}

    def test_offered_to_accepted_is_valid(self) -> None:
        """Transition offered → accepted is valid."""
        assert ("offered", "accepted") in self.VALID_TRANSITIONS

    def test_offered_to_declined_is_valid(self) -> None:
        """Transition offered → declined is valid."""
        assert ("offered", "declined") in self.VALID_TRANSITIONS

    def test_accepted_to_generated_is_valid(self) -> None:
        """Transition accepted → generated is valid."""
        assert ("accepted", "generated") in self.VALID_TRANSITIONS

    def test_declined_to_generated_is_invalid(self) -> None:
        """Transition declined → generated is NOT valid."""
        assert ("declined", "generated") not in self.VALID_TRANSITIONS

    def test_generated_to_offered_is_invalid(self) -> None:
        """Transition generated → offered is NOT valid."""
        assert ("generated", "offered") not in self.VALID_TRANSITIONS

    def test_declined_to_accepted_is_invalid(self) -> None:
        """Transition declined → accepted is NOT valid."""
        assert ("declined", "accepted") not in self.VALID_TRANSITIONS


# ===========================================================================
# 11.7: Protocol references visualization-guide.md for dispatch
# ===========================================================================


class TestDispatchRuleReferences:
    """Verify protocol references visualization-guide.md for correct types."""

    def test_protocol_references_visualization_guide(
        self, protocol_text: str
    ) -> None:
        """Protocol file mentions visualization-guide.md."""
        assert "visualization-guide.md" in protocol_text

    def test_interactive_d3_dispatches_to_guide(self, protocol_text: str) -> None:
        """Interactive_D3_Graph dispatch rule references visualization-guide.md."""
        # Find the dispatch rules section
        dispatch_section = protocol_text[protocol_text.find("## Dispatch Rules"):]
        assert "Interactive_D3_Graph" in dispatch_section
        assert "visualization-guide.md" in dispatch_section

    def test_web_service_dispatches_to_guide(self, protocol_text: str) -> None:
        """Web_Service_Dashboard dispatch rule references visualization-guide.md."""
        dispatch_section = protocol_text[protocol_text.find("## Dispatch Rules"):]
        assert "Web_Service_Dashboard" in dispatch_section
        assert "visualization-guide.md" in dispatch_section

    def test_dispatch_links_both_types_to_guide(self, protocol_text: str) -> None:
        """Both Interactive_D3_Graph and Web_Service_Dashboard reference the guide."""
        dispatch_section = protocol_text[protocol_text.find("## Dispatch Rules"):]
        # The dispatch section should mention both types together with the guide
        assert re.search(
            r"Interactive_D3_Graph.*Web_Service_Dashboard.*visualization-guide\.md",
            dispatch_section,
            re.DOTALL,
        ) or re.search(
            r"Web_Service_Dashboard.*Interactive_D3_Graph.*visualization-guide\.md",
            dispatch_section,
            re.DOTALL,
        )
