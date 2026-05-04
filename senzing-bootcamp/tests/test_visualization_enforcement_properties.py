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
    / "module-07-query-validation.md"
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
    r"⛔\s*MANDATORY\s+VISUALIZATION\s+OFFER",
    re.IGNORECASE,
)


def _extract_wait_blocks(content: str) -> list[str]:
    """Extract mandatory WAIT block sections from steering file content.

    A mandatory WAIT block starts at a line containing the
    ``⛔ MANDATORY VISUALIZATION OFFER`` pattern and extends until the
    next numbered step heading (``N. **`` or ``Na. **``) or end of file.

    Args:
        content: Full text of the steering file.

    Returns:
        List of block text strings, one per mandatory WAIT block found.
    """
    lines = content.splitlines()
    blocks: list[str] = []
    current_block_lines: list[str] | None = None

    re_step = re.compile(r"^\d+[a-z]?\.\s+\*\*")

    for line in lines:
        if _RE_MANDATORY_HEADING.search(line):
            # Start a new block (close any previous one first)
            if current_block_lines is not None:
                blocks.append("\n".join(current_block_lines))
            current_block_lines = [line]
        elif current_block_lines is not None:
            # End block at the next numbered step heading
            if re_step.match(line):
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
    """Return all ``.kiro.hook`` files in the hooks directory.

    Returns:
        Sorted list of Path objects for each hook file found.
    """
    return sorted(_HOOKS_DIR.glob("*.kiro.hook"))


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
    """Feature: module8-visualization-enforcement, Property 1: Mandatory WAIT block formatting consistency

    For any mandatory WAIT block in the steering file, the block uses the
    same visual formatting pattern: a ⛔ emoji in the heading, a 🛑 bold
    stop instruction, and block quote formatting.

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
        """Each mandatory WAIT block uses ⛔, 🛑, and block quote formatting.

        Args:
            block_idx: Index into the list of extracted WAIT blocks.
        """
        block = _WAIT_BLOCKS[block_idx]
        violations: list[str] = []

        # ⛔ emoji in heading
        if "⛔" not in block:
            violations.append("missing ⛔ emoji in heading")

        # 🛑 bold stop instruction
        if "🛑" not in block:
            violations.append("missing 🛑 bold stop instruction")

        # Block quote formatting (lines starting with >)
        has_blockquote = any(
            line.strip().startswith(">")
            for line in block.splitlines()
        )
        if not has_blockquote:
            violations.append("missing block quote formatting (> prefix)")

        assert violations == [], (
            f"WAIT block {block_idx} formatting violations: {violations}"
        )


# ---------------------------------------------------------------------------
# Property 2: Mandatory WAIT block behavioral completeness
# ---------------------------------------------------------------------------


class TestWaitBlockBehavioralCompleteness:
    """Feature: module8-visualization-enforcement, Property 2: Mandatory WAIT block behavioral completeness

    For any mandatory WAIT block in the steering file, the block contains
    (a) an explicit "WAIT" instruction telling the agent not to proceed,
    and (b) a decline/no path that allows the bootcamper to skip the
    visualization and continue.

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
        """Each mandatory WAIT block has a WAIT instruction and decline path.

        Args:
            block_idx: Index into the list of extracted WAIT blocks.
        """
        block = _WAIT_BLOCKS[block_idx]
        violations: list[str] = []

        # (a) Explicit WAIT instruction
        re_wait = re.compile(r"\bWAIT\b", re.IGNORECASE)
        if not re_wait.search(block):
            violations.append("missing explicit WAIT instruction")

        # (b) Decline/no path — look for "no" or "not now" or "decline"
        re_decline = re.compile(
            r"\b(no\b|not now|decline)", re.IGNORECASE
        )
        if not re_decline.search(block):
            violations.append(
                "missing decline/no path for skipping visualization"
            )

        assert violations == [], (
            f"WAIT block {block_idx} behavioral completeness "
            f"violations: {violations}"
        )


# ---------------------------------------------------------------------------
# Property 3: Hook JSON schema conformance
# ---------------------------------------------------------------------------


class TestHookJsonSchemaConformance:
    """Feature: module8-visualization-enforcement, Property 3: Hook JSON schema conformance

    For any .kiro.hook file in senzing-bootcamp/hooks/, parsing it as JSON
    succeeds and the resulting object contains all required fields: name
    (string), version (string), description (string), when.type (string),
    then.type (string), and then.prompt (string when then.type is
    "askAgent").

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
        """Each hook file is valid JSON with all required fields.

        Args:
            hook_path: Path to a ``.kiro.hook`` file.
        """
        raw = hook_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        violations: list[str] = []
        fname = hook_path.name

        # Top-level required string fields
        for field in ("name", "version", "description"):
            if field not in data:
                violations.append(f"{fname}: missing field '{field}'")
            elif not isinstance(data[field], str):
                violations.append(
                    f"{fname}: '{field}' is not a string"
                )
            elif not data[field].strip():
                violations.append(
                    f"{fname}: '{field}' is empty"
                )

        # when.type
        when = data.get("when")
        if not isinstance(when, dict):
            violations.append(f"{fname}: 'when' is not an object")
        elif "type" not in when:
            violations.append(f"{fname}: missing 'when.type'")
        elif not isinstance(when["type"], str):
            violations.append(f"{fname}: 'when.type' is not a string")

        # then.type and then.prompt
        then = data.get("then")
        if not isinstance(then, dict):
            violations.append(f"{fname}: 'then' is not an object")
        else:
            if "type" not in then:
                violations.append(f"{fname}: missing 'then.type'")
            elif not isinstance(then["type"], str):
                violations.append(
                    f"{fname}: 'then.type' is not a string"
                )

            # When then.type is "askAgent", then.prompt must be a
            # non-empty string
            if then.get("type") == "askAgent":
                if "prompt" not in then:
                    violations.append(
                        f"{fname}: missing 'then.prompt' "
                        f"(required when then.type is 'askAgent')"
                    )
                elif not isinstance(then["prompt"], str):
                    violations.append(
                        f"{fname}: 'then.prompt' is not a string"
                    )
                elif not then["prompt"].strip():
                    violations.append(
                        f"{fname}: 'then.prompt' is empty"
                    )

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
