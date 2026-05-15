"""Unit and property tests for test_hooks.py.

Feature: hook-self-test
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Make scripts importable
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from test_hooks import (
    VALID_EVENT_TYPES,
    VALID_TOOL_CATEGORIES,
    FILE_EVENT_TYPES,
    TOOL_EVENT_TYPES,
    validate_hook,
    validate_glob_pattern,
    validate_tool_type,
    parse_categories_yaml,
    parse_registry_hook_ids,
    check_registry_consistency,
    discover_hooks,
    hook_id_from_path,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_hook(tmp_dir: Path, hook_id: str, data: dict) -> Path:
    """Write a hook JSON file to a temp directory."""
    path = tmp_dir / f"{hook_id}.kiro.hook"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _make_valid_hook(
    event_type: str = "agentStop",
    action_type: str = "askAgent",
    prompt: str = "Do something",
    patterns: list[str] | None = None,
    tool_types: list[str] | None = None,
) -> dict:
    """Create a valid hook data dict."""
    hook: dict = {
        "name": "Test Hook",
        "version": "1.0.0",
        "description": "A test hook",
        "when": {"type": event_type},
        "then": {"type": action_type},
    }
    if action_type == "askAgent":
        hook["then"]["prompt"] = prompt
    elif action_type == "runCommand":
        hook["then"]["command"] = prompt
    if patterns is not None:
        hook["when"]["patterns"] = patterns
    if tool_types is not None:
        hook["when"]["toolTypes"] = tool_types
    return hook


# ---------------------------------------------------------------------------
# Test: CLI flags accepted without error
# ---------------------------------------------------------------------------


class TestCLIFlags:
    """Validates: script accepts --hook, --categories, --verbose flags."""

    def test_hook_flag_accepted(self) -> None:
        """--hook flag is accepted without argparse error."""
        # Use a known hook ID; main() will find it
        exit_code = main(["--hook", "ask-bootcamper"])
        assert exit_code == 0

    def test_categories_flag_accepted(self) -> None:
        """--categories flag is accepted without argparse error."""
        exit_code = main(["--categories", "critical"])
        assert exit_code == 0

    def test_verbose_flag_accepted(self) -> None:
        """--verbose flag is accepted without argparse error."""
        exit_code = main(["--verbose"])
        assert exit_code == 0

    def test_all_flags_combined(self) -> None:
        """All flags can be combined."""
        exit_code = main(["--hook", "ask-bootcamper", "--verbose"])
        assert exit_code == 0


# ---------------------------------------------------------------------------
# Test: Valid hook passes all checks
# ---------------------------------------------------------------------------


class TestValidHookPasses:
    """Validates: valid hook file with all required fields passes all checks."""

    def test_valid_agent_stop_hook(self) -> None:
        """agentStop + askAgent hook with all fields passes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(event_type="agentStop", action_type="askAgent")
            path = _write_hook(tmp_dir, "test-hook", data)
            result = validate_hook(path)
            assert result.passed, f"Failures: {result.failures}"
            assert result.hook_id == "test-hook"

    def test_valid_file_event_hook(self) -> None:
        """fileEdited hook with patterns passes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(
                event_type="fileEdited",
                patterns=["src/**/*.py", "*.ts"],
            )
            path = _write_hook(tmp_dir, "file-hook", data)
            result = validate_hook(path)
            assert result.passed, f"Failures: {result.failures}"

    def test_valid_tool_event_hook(self) -> None:
        """preToolUse hook with valid toolTypes passes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(
                event_type="preToolUse",
                tool_types=["write", "read"],
            )
            path = _write_hook(tmp_dir, "tool-hook", data)
            result = validate_hook(path)
            assert result.passed, f"Failures: {result.failures}"

    def test_valid_run_command_hook(self) -> None:
        """runCommand hook with command passes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(
                event_type="userTriggered",
                action_type="runCommand",
                prompt="npm run lint",
            )
            path = _write_hook(tmp_dir, "cmd-hook", data)
            result = validate_hook(path)
            assert result.passed, f"Failures: {result.failures}"


# ---------------------------------------------------------------------------
# Test: Missing when.type detected
# ---------------------------------------------------------------------------


class TestMissingWhenType:
    """Validates: hook with missing when.type field is detected as failure."""

    def test_missing_when_type(self) -> None:
        """Hook without when.type fails validation."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = {
                "name": "Bad Hook",
                "version": "1.0.0",
                "when": {},
                "then": {"type": "askAgent", "prompt": "hello"},
            }
            path = _write_hook(tmp_dir, "bad-hook", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("when.type" in f for f in result.failures)

    def test_missing_when_entirely(self) -> None:
        """Hook without when object fails validation."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = {
                "name": "Bad Hook",
                "version": "1.0.0",
                "then": {"type": "askAgent", "prompt": "hello"},
            }
            path = _write_hook(tmp_dir, "no-when", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("when" in f for f in result.failures)


# ---------------------------------------------------------------------------
# Test: Invalid event type detected
# ---------------------------------------------------------------------------


class TestInvalidEventType:
    """Validates: hook with invalid event type is detected."""

    def test_invalid_event_type(self) -> None:
        """Hook with bogus event type fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(event_type="invalidEvent")
            path = _write_hook(tmp_dir, "bad-event", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("Invalid event type" in f for f in result.failures)

    def test_typo_event_type(self) -> None:
        """Hook with typo in event type fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(event_type="fileedited")  # wrong case
            path = _write_hook(tmp_dir, "typo-event", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("Invalid event type" in f for f in result.failures)


# ---------------------------------------------------------------------------
# Test: askAgent hook with empty prompt detected
# ---------------------------------------------------------------------------


class TestEmptyPrompt:
    """Validates: askAgent hook with empty prompt is detected."""

    def test_empty_prompt_string(self) -> None:
        """askAgent hook with empty string prompt fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(prompt="")
            path = _write_hook(tmp_dir, "empty-prompt", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("Empty prompt" in f for f in result.failures)

    def test_whitespace_only_prompt(self) -> None:
        """askAgent hook with whitespace-only prompt fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(prompt="   ")
            path = _write_hook(tmp_dir, "ws-prompt", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("Empty prompt" in f for f in result.failures)


# ---------------------------------------------------------------------------
# Test: File-event hook without when.patterns detected
# ---------------------------------------------------------------------------


class TestMissingPatterns:
    """Validates: file-event hook without when.patterns is detected."""

    def test_file_edited_no_patterns(self) -> None:
        """fileEdited hook without patterns fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(event_type="fileEdited")
            # No patterns added
            path = _write_hook(tmp_dir, "no-patterns", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("when.patterns" in f for f in result.failures)

    def test_file_created_no_patterns(self) -> None:
        """fileCreated hook without patterns fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(event_type="fileCreated")
            path = _write_hook(tmp_dir, "no-patterns-created", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("when.patterns" in f for f in result.failures)


# ---------------------------------------------------------------------------
# Test: toolType with invalid regex detected
# ---------------------------------------------------------------------------


class TestInvalidToolTypeRegex:
    """Validates: toolType with invalid regex is detected."""

    def test_invalid_regex_in_tool_types(self) -> None:
        """preToolUse hook with invalid regex in toolTypes fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(
                event_type="preToolUse",
                tool_types=["[invalid(regex"],
            )
            path = _write_hook(tmp_dir, "bad-regex", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("Invalid toolType" in f for f in result.failures)

    def test_valid_regex_passes(self) -> None:
        """preToolUse hook with valid regex pattern passes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(
                event_type="preToolUse",
                tool_types=[".*sql.*", "write"],
            )
            path = _write_hook(tmp_dir, "good-regex", data)
            result = validate_hook(path)
            assert result.passed, f"Failures: {result.failures}"

    def test_missing_tool_types_for_pre_tool_use(self) -> None:
        """preToolUse hook without toolTypes fails."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            data = _make_valid_hook(event_type="preToolUse")
            path = _write_hook(tmp_dir, "no-tool-types", data)
            result = validate_hook(path)
            assert not result.passed
            assert any("when.toolTypes" in f for f in result.failures)


# ---------------------------------------------------------------------------
# Property test: valid hooks always pass structural checks
# ---------------------------------------------------------------------------


# Strategies
st_event_type = st.sampled_from(sorted(VALID_EVENT_TYPES))
st_action_type = st.sampled_from(["askAgent", "runCommand"])
st_non_empty_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S", "Z")),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip())
st_glob_pattern = st.from_regex(r"[a-z*/]+\.[a-z*]+", fullmatch=True)
st_tool_category = st.sampled_from(sorted(VALID_TOOL_CATEGORIES))


@st.composite
def st_valid_hook(draw: st.DrawFn) -> dict:
    """Strategy that generates a structurally valid hook JSON object."""
    event_type = draw(st_event_type)
    action_type = draw(st_action_type)
    prompt_text = draw(st_non_empty_text)

    hook: dict = {
        "name": draw(st_non_empty_text),
        "version": "1.0.0",
        "description": "Generated hook",
        "when": {"type": event_type},
        "then": {"type": action_type},
    }

    if action_type == "askAgent":
        hook["then"]["prompt"] = prompt_text
    else:
        hook["then"]["command"] = prompt_text

    # Add patterns for file-event hooks
    if event_type in FILE_EVENT_TYPES:
        patterns = draw(st.lists(st_glob_pattern, min_size=1, max_size=3))
        hook["when"]["patterns"] = patterns

    # Add toolTypes for tool-event hooks
    if event_type in TOOL_EVENT_TYPES:
        tool_types = draw(st.lists(st_tool_category, min_size=1, max_size=3))
        hook["when"]["toolTypes"] = tool_types

    return hook


class TestPropertyValidHookPasses:
    """Property test: any JSON with all required fields and valid values passes.

    Validates requirement: structural checks accept all well-formed hooks.
    """

    @given(hook_data=st_valid_hook())
    @settings(max_examples=10)
    def test_valid_hook_always_passes(self, hook_data: dict) -> None:
        """Any hook with valid structure passes all checks."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            path = _write_hook(tmp_dir, "prop-hook", hook_data)
            result = validate_hook(path)
            assert result.passed, (
                f"Valid hook failed: {result.failures}\nData: {hook_data}"
            )
