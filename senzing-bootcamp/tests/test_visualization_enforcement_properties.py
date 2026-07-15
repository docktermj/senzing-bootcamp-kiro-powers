"""Property-based tests for Module 8 visualization enforcement artifacts.

Validates that mandatory WAIT blocks in the steering file use consistent
formatting and contain required behavioral elements, and that all hook
files conform to the expected JSON schema.

Feature: module8-visualization-enforcement
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_STEERING_FILE: Path = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "visualization-guide.md"
)

_HOOKS_DIR: Path = (
    Path(__file__).resolve().parent.parent / "hooks"
)

_README_FILE: Path = (
    Path(__file__).resolve().parent.parent / "hooks" / "README.md"
)

# ---------------------------------------------------------------------------
# WAIT block extraction
# ---------------------------------------------------------------------------

_RE_MANDATORY_HEADING = re.compile(
    r"🛑\s*STOP",
    re.IGNORECASE,
)


def _extract_wait_blocks(content: str) -> list[str]:
    """Extract STOP block sections from the visualization protocol file.

    A STOP block starts at a line containing the ``🛑 STOP`` pattern and
    extends until the next section heading (``##``) or the next ``🛑 STOP``
    or end of file.

    Args:
        content: Full text of the steering file.

    Returns:
        List of block text strings, one per STOP block found.
    """
    lines = content.splitlines()
    blocks: list[str] = []
    current_block_lines: list[str] | None = None

    re_section = re.compile(r"^##\s+")

    for line in lines:
        if _RE_MANDATORY_HEADING.search(line):
            # Start a new block (close any previous one first)
            if current_block_lines is not None:
                blocks.append("\n".join(current_block_lines))
            current_block_lines = [line]
        elif current_block_lines is not None:
            # End block at the next section heading
            if re_section.match(line):
                blocks.append("\n".join(current_block_lines))
                current_block_lines = None
            else:
                current_block_lines.append(line)

    # Close any trailing block
    if current_block_lines is not None:
        blocks.append("\n".join(current_block_lines))

    return blocks


# Module-level: parse once, reuse across tests
_STEERING_CONTENT: str = _STEERING_FILE.read_text(encoding="utf-8")
_WAIT_BLOCKS: list[str] = _extract_wait_blocks(_STEERING_CONTENT)

# ---------------------------------------------------------------------------
# Hook file discovery
# ---------------------------------------------------------------------------


def _discover_hook_files() -> list[Path]:
    """Return all v1 ``*.json`` hook files in the hooks directory.

    Returns:
        Sorted list of Path objects for each hook file found.
    """
    return sorted(_HOOKS_DIR.glob("*.json"))


_HOOK_FILES: list[Path] = _discover_hook_files()

# ---------------------------------------------------------------------------
# README hook entry extraction
# ---------------------------------------------------------------------------

_RE_NUMBERED_ENTRY = re.compile(r"^###\s+(\d+)\.\s+")


def _extract_readme_entries(content: str) -> list[str]:
    """Extract numbered hook entry sections from the hooks README.

    Each entry starts at a ``### N.`` heading and extends until the next
    ``### N.`` heading or end of file.

    Args:
        content: Full text of the hooks README.

    Returns:
        List of entry text strings, one per numbered section found.
    """
    lines = content.splitlines()
    entries: list[str] = []
    current_lines: list[str] | None = None

    for line in lines:
        if _RE_NUMBERED_ENTRY.match(line):
            if current_lines is not None:
                entries.append("\n".join(current_lines))
            current_lines = [line]
        elif current_lines is not None:
            current_lines.append(line)

    if current_lines is not None:
        entries.append("\n".join(current_lines))

    return entries


_README_CONTENT: str = _README_FILE.read_text(encoding="utf-8")
_README_ENTRIES: list[str] = _extract_readme_entries(_README_CONTENT)

# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------


def st_wait_block_index() -> st.SearchStrategy[int]:
    """Strategy that draws a valid index into the ``_WAIT_BLOCKS`` list.

    Returns:
        A strategy producing integer indices for mandatory WAIT blocks.
    """
    return st.sampled_from(list(range(len(_WAIT_BLOCKS))))


def st_hook_file() -> st.SearchStrategy[Path]:
    """Strategy that draws a random hook file path from the hooks directory.

    Returns:
        A strategy producing Path objects for ``.kiro.hook`` files.
    """
    return st.sampled_from(_HOOK_FILES)


def st_readme_entry() -> st.SearchStrategy[str]:
    """Strategy that draws a random numbered hook entry from the README.

    Returns:
        A strategy producing entry text strings from the hooks README.
    """
    return st.sampled_from(_README_ENTRIES)


# ---------------------------------------------------------------------------
# Property 1: Mandatory WAIT block formatting consistency
# ---------------------------------------------------------------------------


class TestWaitBlockFormattingConsistency:
    """Feature: module8-visualization-enforcement, Property 1: STOP block formatting consistency

    For any STOP block in the visualization protocol file, the block uses
    the same visual formatting pattern: a 🛑 emoji and a "STOP" instruction.

    Validates: Requirements 1.2, 1.4
    """

    @given(block_idx=st_wait_block_index())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_wait_block_has_consistent_formatting(
        self, block_idx: int
    ) -> None:
        """Each STOP block uses 🛑 and contains a STOP instruction.

        Args:
            block_idx: Index into the list of extracted STOP blocks.
        """
        block = _WAIT_BLOCKS[block_idx]
        violations: list[str] = []

        # 🛑 emoji in the block
        if "🛑" not in block:
            violations.append("missing 🛑 emoji")

        # STOP instruction
        if "STOP" not in block:
            violations.append("missing STOP instruction")

        # Wait instruction (tells agent to wait for input)
        if "Wait" not in block and "wait" not in block:
            violations.append("missing wait instruction")

        assert violations == [], (
            f"STOP block {block_idx} formatting violations: {violations}"
        )


# ---------------------------------------------------------------------------
# Property 2: Mandatory WAIT block behavioral completeness
# ---------------------------------------------------------------------------


class TestWaitBlockBehavioralCompleteness:
    """Feature: module8-visualization-enforcement, Property 2: STOP block behavioral completeness

    For any STOP block in the visualization protocol file, the block contains
    an explicit "STOP" instruction telling the agent not to proceed and
    a "Wait" instruction for the bootcamper's input.

    Validates: Requirements 1.5, 1.7
    """

    @given(block_idx=st_wait_block_index())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_wait_block_has_behavioral_completeness(
        self, block_idx: int
    ) -> None:
        """Each STOP block has a STOP instruction and wait-for-input directive.

        Args:
            block_idx: Index into the list of extracted STOP blocks.
        """
        block = _WAIT_BLOCKS[block_idx]
        violations: list[str] = []

        # (a) Explicit STOP instruction
        if "STOP" not in block:
            violations.append("missing explicit STOP instruction")

        # (b) Wait-for-input directive
        re_wait = re.compile(r"\b[Ww]ait\b")
        if not re_wait.search(block):
            violations.append(
                "missing wait-for-input directive"
            )

        assert violations == [], (
            f"STOP block {block_idx} behavioral completeness "
            f"violations: {violations}"
        )


# ---------------------------------------------------------------------------
# Property 3: Hook JSON schema conformance
# ---------------------------------------------------------------------------


class TestHookJsonSchemaConformance:
    """Feature: module8-visualization-enforcement, Property 3: Hook JSON schema conformance

    For any ``*.json`` v1 hook file in senzing-bootcamp/hooks/, parsing it as
    JSON succeeds and the wrapper declares ``version == "v1"`` with a non-empty
    ``hooks`` array whose single entry contains: name (string), trigger
    (string), action.type (string), and action.prompt (non-empty string when
    action.type is "agent") or action.command (non-empty string when
    action.type is "command").

    Validates: Requirements 2.5
    """

    @given(hook_path=st_hook_file())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_hook_file_conforms_to_schema(
        self, hook_path: Path
    ) -> None:
        """Each hook file is a valid v1 wrapper with all required fields.

        Args:
            hook_path: Path to a ``<id>.json`` v1 hook file.
        """
        raw = hook_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        violations: list[str] = []
        fname = hook_path.name

        # Wrapper-level schema tag and hooks array.
        if data.get("version") != "v1":
            violations.append(f"{fname}: wrapper version is not 'v1'")
        hooks = data.get("hooks")
        if not isinstance(hooks, list) or not hooks:
            violations.append(f"{fname}: 'hooks' is not a non-empty array")
            assert violations == [], f"Hook schema violations: {violations}"
            return

        entry = hooks[0]

        # name (required string).
        if "name" not in entry:
            violations.append(f"{fname}: missing field 'name'")
        elif not isinstance(entry["name"], str) or not entry["name"].strip():
            violations.append(f"{fname}: 'name' is not a non-empty string")

        # trigger (required string).
        if "trigger" not in entry:
            violations.append(f"{fname}: missing 'trigger'")
        elif not isinstance(entry["trigger"], str):
            violations.append(f"{fname}: 'trigger' is not a string")

        # action.type and its payload.
        action = entry.get("action")
        if not isinstance(action, dict):
            violations.append(f"{fname}: 'action' is not an object")
        else:
            action_type = action.get("type")
            if "type" not in action:
                violations.append(f"{fname}: missing 'action.type'")
            elif not isinstance(action_type, str):
                violations.append(f"{fname}: 'action.type' is not a string")

            if action_type == "agent":
                prompt = action.get("prompt")
                if "prompt" not in action:
                    violations.append(
                        f"{fname}: missing 'action.prompt' "
                        f"(required when action.type is 'agent')"
                    )
                elif not isinstance(prompt, str) or not prompt.strip():
                    violations.append(f"{fname}: 'action.prompt' is not a non-empty string")
            elif action_type == "command":
                command = action.get("command")
                if "command" not in action:
                    violations.append(
                        f"{fname}: missing 'action.command' "
                        f"(required when action.type is 'command')"
                    )
                elif not isinstance(command, str) or not command.strip():
                    violations.append(f"{fname}: 'action.command' is not a non-empty string")

        assert violations == [], (
            f"Hook schema violations: {violations}"
        )


# ---------------------------------------------------------------------------
# Property 4: README hook entry format conformance
# ---------------------------------------------------------------------------


class TestReadmeHookEntryFormatConformance:
    """Feature: module8-visualization-enforcement, Property 4: README hook entry format conformance

    For any numbered hook entry section in senzing-bootcamp/hooks/README.md,
    the entry contains a **Trigger** line, an **Action** line, and a
    **Use case** line, each with non-empty content.

    Validates: Requirements 3.2
    """

    @given(entry=st_readme_entry())
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_readme_entry_has_required_fields(
        self, entry: str
    ) -> None:
        """Each numbered hook entry has Trigger, Action, and Use case lines.

        Args:
            entry: Full text of a numbered hook entry section.
        """
        violations: list[str] = []

        # Extract the entry heading for error messages
        heading = entry.splitlines()[0].strip()

        # Check for **Trigger:** with non-empty content
        trigger_match = re.search(
            r"\*\*Trigger:\*\*\s*(.+)", entry
        )
        if not trigger_match:
            violations.append("missing **Trigger:** line")
        elif not trigger_match.group(1).strip():
            violations.append("**Trigger:** line has empty content")

        # Check for **Action:** with non-empty content
        action_match = re.search(
            r"\*\*Action:\*\*\s*(.+)", entry
        )
        if not action_match:
            violations.append("missing **Action:** line")
        elif not action_match.group(1).strip():
            violations.append("**Action:** line has empty content")

        # Check for **Use case:** with non-empty content
        use_case_match = re.search(
            r"\*\*Use case:\*\*\s*(.+)", entry
        )
        if not use_case_match:
            violations.append("missing **Use case:** line")
        elif not use_case_match.group(1).strip():
            violations.append("**Use case:** line has empty content")

        assert violations == [], (
            f"README entry '{heading}' format violations: {violations}"
        )
