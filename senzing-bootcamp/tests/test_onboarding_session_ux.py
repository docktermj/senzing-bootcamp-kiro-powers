"""Structural validation tests for the onboarding-session-ux feature.

Feature: onboarding-session-ux

Example-based (non-property) unit tests validating the *static structure* of the
steering and hook files that the onboarding-session-ux feature edits or verifies.
Each assertion reads the shipped Markdown / JSON file and confirms required
content or heading ordering — there is no randomness, clock, or network here.

Covered requirements:
    * R1.1, R1.2, R1.3 — Setup Preamble (onboarding-flow.md § 0) precedes the
      first administrative-setup action and the WELCOME banner.
    * R2.1, R2.2, R2.3 — Setup Preamble content announces setup and identifies
      the activities (project directory, hooks, environment) and start point.
    * R2.4 — the WELCOME banner section states administrative setup is complete
      and the bootcamp is starting.
    * R4.2, R4.3 — session-resume.md Step 2b states the bold-question convention
      inline (self-contained), not solely by reference to conversation-protocol.md.
    * R5.1 — write-policy-gate.json CHECK 2 strips bold markers before the
      single-question validation.
    * R6.1, R6.2 — ``measure_steering.py --check`` passes, confirming stored
      token counts are current and no file exceeds the split threshold without
      an allowlist entry.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths to the shipped files under test.
#
# This test lives at ``senzing-bootcamp/tests/test_onboarding_session_ux.py``,
# so ``parent.parent`` is the ``senzing-bootcamp/`` power root and the steering
# and hook directories are its direct children.
# ---------------------------------------------------------------------------

_BOOTCAMP_DIR: Path = Path(__file__).resolve().parent.parent
_REPO_ROOT: Path = _BOOTCAMP_DIR.parent
_STEERING_DIR: Path = _BOOTCAMP_DIR / "steering"
_HOOKS_DIR: Path = _BOOTCAMP_DIR / "hooks"
_SCRIPTS_DIR: Path = _BOOTCAMP_DIR / "scripts"

_ONBOARDING_FLOW: Path = _STEERING_DIR / "onboarding-flow.md"
_ONBOARDING_PHASE1B: Path = _STEERING_DIR / "onboarding-phase1b-intro-language.md"
_SESSION_RESUME: Path = _STEERING_DIR / "session-resume.md"
_WRITE_POLICY_GATE: Path = _HOOKS_DIR / "write-policy-gate.json"
_MEASURE_STEERING: Path = _SCRIPTS_DIR / "measure_steering.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str:
    """Read a file and return its content as a string.

    Args:
        path: Path to the file.

    Returns:
        File content decoded as UTF-8.
    """
    return path.read_text(encoding="utf-8")


def _extract_section(content: str, heading_pattern: str) -> str:
    """Extract a ``## heading`` section until the next ``## heading``.

    Sub-headings (``###`` and deeper) do not terminate the section, so nested
    sub-steps remain part of the returned block.

    Args:
        content: Full Markdown content.
        heading_pattern: Regex (without the leading ``## ``) matching the
            section heading text, e.g. ``r"\\d+\\. Bootcamp Introduction"``.

    Returns:
        The section text (including its heading line), or an empty string if the
        heading is not found.
    """
    match = re.search(rf"^(## {heading_pattern}.*)$", content, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"^## ", content[match.end():], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(content)
    return content[start:end]


def _extract_subsection(section: str, heading_pattern: str) -> str:
    """Extract a ``### heading`` subsection until the next ``### heading``.

    Args:
        section: Markdown text of a parent ``##`` section.
        heading_pattern: Regex (without the leading ``### ``) matching the
            subsection heading text, e.g. ``r"Core Rules"``.

    Returns:
        The subsection text (including its heading line), or an empty string if
        the heading is not found.
    """
    match = re.search(rf"^(### {heading_pattern}.*)$", section, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_heading = re.search(r"^### ", section[match.end():], re.MULTILINE)
    end = match.end() + next_heading.start() if next_heading else len(section)
    return section[start:end]


def _heading_position(content: str, anchored_pattern: str) -> int | None:
    """Return the character offset of a line-anchored heading, or None.

    Args:
        content: Full Markdown content.
        anchored_pattern: A ``^``-anchored regex matching the heading line,
            e.g. ``r"^## 0\\. Setup Preamble"``.

    Returns:
        The start offset of the matched heading, or None if it is absent.
    """
    match = re.search(anchored_pattern, content, re.MULTILINE)
    return match.start() if match else None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestOnboardingSessionUXStructure:
    """Static-structure assertions for the onboarding-session-ux steering edits.

    Validates: Requirements 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 4.2, 4.3, 5.1
    """

    # -- R2.4: WELCOME banner setup-complete statement ---------------------

    def test_welcome_banner_section_states_setup_complete(self) -> None:
        """Bootcamp Introduction states setup is complete before the banner (R2.4).

        The setup-complete statement was added in ``## 5. Bootcamp Introduction``
        immediately before the welcome banner display.
        """
        content = _read_file(_ONBOARDING_PHASE1B)
        section = _extract_section(content, r"\d+\. Bootcamp Introduction")
        assert section, "Bootcamp Introduction section not found in phase1b file"

        statement = "Administrative setup is complete. The bootcamp is starting."
        stmt_pos = section.find(statement)
        assert stmt_pos != -1, (
            "Setup-complete statement not found in the Bootcamp Introduction section"
        )

        # The statement must precede the WELCOME banner display.
        banner_pos = section.find("WELCOME TO THE SENZING BOOTCAMP")
        assert banner_pos != -1, "WELCOME banner text not found in the section"
        assert stmt_pos < banner_pos, (
            "Setup-complete statement must appear before the WELCOME banner display"
        )

    # -- R4.2 / R4.3: session-resume Step 2b bold rule (inline) ------------

    def test_session_resume_step2b_states_bold_rule_inline(self) -> None:
        """Step 2b Core Rules contain a self-contained bold-question rule (R4.2, R4.3).

        Rule 6 must be stated inline — with the actual CommonMark bold guidance,
        the pointer-outside-bold statement, and the enforcement action — rather
        than solely by reference to conversation-protocol.md, so the convention
        survives context compaction.
        """
        content = _read_file(_SESSION_RESUME)
        section = _extract_section(content, r"Step 2b: Behavioral Rules Reload")
        assert section, "Step 2b: Behavioral Rules Reload section not found"

        core_rules = _extract_subsection(section, r"Core Rules")
        assert core_rules, "### Core Rules subsection not found under Step 2b"

        # Rule 6 exists and starts with the expected label.
        rule6_match = re.search(r"^6\. \*\*Bold question text\*\*.*$", core_rules, re.MULTILINE)
        assert rule6_match, (
            "Rule 6 starting with '6. **Bold question text**' not found in Core Rules"
        )
        rule6 = rule6_match.group(0)

        # Inline CommonMark bold guidance is present in the rule text itself.
        assert "CommonMark bold" in rule6, (
            "Rule 6 must state the CommonMark bold guidance inline"
        )
        # The pointer-outside-bold statement is present.
        assert "\U0001f449 pointer is outside the bold span" in rule6, (
            "Rule 6 must state that the \U0001f449 pointer is outside the bold span"
        )
        # A concrete enforcement action makes the rule self-contained (not a
        # bare cross-reference to conversation-protocol.md).
        assert "wrap it before sending" in rule6, (
            "Rule 6 must state the inline enforcement action ('wrap it before sending')"
        )
        assert "conversation-protocol.md" not in rule6, (
            "Rule 6 text must stand alone, not defer to conversation-protocol.md"
        )

    # -- R1.1 / R1.2 / R1.3: Setup Preamble ordering -----------------------

    def test_setup_preamble_precedes_directory_and_prerequisite(self) -> None:
        """§ 0 Setup Preamble precedes § 1 Directory Structure and § 2 Prerequisite Check.

        Ordering by heading position confirms the preamble is displayed before
        the first administrative-setup action (R1.1, R1.2) and before the
        WELCOME banner reached later in the flow (R1.3).
        """
        content = _read_file(_ONBOARDING_FLOW)

        preamble_pos = _heading_position(content, r"^## 0\. Setup Preamble")
        directory_pos = _heading_position(content, r"^## 1\. Directory Structure")
        prereq_pos = _heading_position(content, r"^## 2\. Prerequisite Check")

        assert preamble_pos is not None, "'## 0. Setup Preamble' heading not found"
        assert directory_pos is not None, "'## 1. Directory Structure' heading not found"
        assert prereq_pos is not None, "'## 2. Prerequisite Check' heading not found"

        assert preamble_pos < directory_pos, (
            "Setup Preamble (§ 0) must precede Directory Structure (§ 1)"
        )
        assert directory_pos < prereq_pos, (
            "Directory Structure (§ 1) must precede Prerequisite Check (§ 2)"
        )

    # -- R2.1 / R2.2 / R2.3: Setup Preamble content ------------------------

    def test_setup_preamble_content_lists_activities_and_start(self) -> None:
        """§ 0 Setup Preamble names the setup activities and the start point (R2.1-R2.3).

        The preamble paragraph must mention creating the project directory,
        installing hooks, checking the environment, and the WELCOME banner as
        the official start marker.
        """
        content = _read_file(_ONBOARDING_FLOW)
        section = _extract_section(content, r"0\. Setup Preamble")
        assert section, "§ 0 Setup Preamble section not found"

        lowered = section.lower()
        for term in ("project directory", "hooks", "environment", "welcome"):
            assert term in lowered, (
                f"Setup Preamble content must mention '{term}'"
            )

    # -- R5.1: write-policy-gate CHECK 2 strips bold markers ---------------

    def test_write_policy_gate_check2_strips_bold_markers(self) -> None:
        """write-policy-gate CHECK 2 contains the STRIP BOLD MARKERS instruction (R5.1)."""
        data = json.loads(_WRITE_POLICY_GATE.read_text(encoding="utf-8"))
        prompt = data["hooks"][0]["action"]["prompt"]

        check2_start = prompt.find("CHECK 2")
        assert check2_start != -1, "CHECK 2 section not found in write-policy-gate prompt"
        check3_start = prompt.find("CHECK 3", check2_start)
        check2 = prompt[check2_start:check3_start] if check3_start != -1 else prompt[check2_start:]

        assert "STRIP BOLD MARKERS" in check2, (
            "CHECK 2 must contain the 'STRIP BOLD MARKERS' instruction"
        )
        # The strip must be ordered before rule evaluation to be meaningful.
        assert "before evaluating any rule below" in check2, (
            "STRIP BOLD MARKERS must be applied before evaluating the single-question rules"
        )


class TestSteeringTokenBudget:
    """Token-budget enforcement for the onboarding-session-ux steering edits.

    Validates: Requirements 6.1, 6.2
    """

    def test_measure_steering_check_passes(self) -> None:
        """``measure_steering.py --check`` exits 0 (R6.1, R6.2).

        Runs the shipped budget checker in its validation mode as a subprocess.
        A zero exit code confirms every stored ``token_count`` is within
        tolerance of the file on disk (R6.1) and that no steering file exceeds
        the split threshold without an allowlist entry (R6.2). The script's
        default steering/index paths are repo-root-relative, so it is invoked
        with the repository root as the working directory.
        """
        result = subprocess.run(
            [sys.executable, str(_MEASURE_STEERING), "--check"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, (
            "measure_steering.py --check exited "
            f"{result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
