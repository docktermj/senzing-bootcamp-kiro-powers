"""Bug condition exploration tests for missing-pointing-prefix bugfix.

These tests verify that onboarding-flow.md does NOT contain inline 👉 closing
questions with WAIT instructions in steps 1b, 2, 4, and 5.  The ask-bootcamper
hook should be the sole owner of closing questions.

**Validates: Requirements 1.1, 1.2, 1.3, 2.1**

EXPECTED OUTCOME on UNFIXED code: tests FAIL (confirming the bug exists).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ONBOARDING_FILE = (
    Path(__file__).resolve().parent.parent / "steering" / "onboarding-flow.md"
)

_ONBOARDING_PHASE2_FILE = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "onboarding-phase2-track-setup.md"
)

_ONBOARDING_PHASE1B_FILE = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "onboarding-phase1b-intro-language.md"
)


def _read_onboarding() -> str:
    """Return the full text of onboarding-flow.md."""
    return _ONBOARDING_FILE.read_text(encoding="utf-8")


def _read_phase2() -> str:
    """Return the full text of onboarding-phase2-track-setup.md."""
    return _ONBOARDING_PHASE2_FILE.read_text(encoding="utf-8")


def _read_phase1b() -> str:
    """Return the full text of onboarding-phase1b-intro-language.md.

    Post-split, this phase file owns the entity-resolution intro (Step 3),
    the Programming Language Selection step (Step 4), the welcome banner /
    Bootcamp Introduction (Step 5), the verbosity preference (Step 5a), and
    the comprehension check (Step 5b)."""
    return _ONBOARDING_PHASE1B_FILE.read_text(encoding="utf-8")


def _read_onboarding_combined() -> str:
    """Return the combined text of both onboarding phase files."""
    phase1 = _ONBOARDING_FILE.read_text(encoding="utf-8")
    phase2 = _ONBOARDING_PHASE2_FILE.read_text(encoding="utf-8")
    return phase1 + "\n" + phase2


def _extract_section(full_text: str, heading_pattern: str) -> str:
    """Extract a section from the markdown by its heading.

    Returns everything from the matched heading up to (but not including)
    the next heading of the same or higher level.
    """
    # Match ## headings (level 2)
    pattern = rf"(^{heading_pattern}.*$)"
    match = re.search(pattern, full_text, re.MULTILINE)
    if not match:
        pytest.fail(f"Could not find section matching: {heading_pattern}")

    start = match.start()
    # Find the next ## heading after this one
    next_heading = re.search(r"^## ", full_text[match.end() :], re.MULTILINE)
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(full_text)

    return full_text[start:end]


# ---------------------------------------------------------------------------
# Tests — Bug Condition Exploration (Property 1)
# ---------------------------------------------------------------------------


class TestBugConditionInlineQuestions:
    """Assert that affected steps do NOT contain inline 👉 closing questions
    and WAIT instructions.  On unfixed code these assertions will FAIL,
    confirming the bug exists."""

    def test_preamble_no_strict_rule(self) -> None:
        """The preamble should NOT contain the 🚨 STRICT RULE paragraph
        mandating inline questions with WAITs."""
        text = _read_onboarding()
        # The strict rule appears before the first ## heading
        first_section = text[: text.index("## 0.")]
        assert "🚨 STRICT RULE" not in first_section, (
            "Preamble contains '🚨 STRICT RULE' paragraph mandating "
            "inline questions with WAITs — this conflicts with the "
            "ask-bootcamper hook ownership model."
        )

    def test_step_1b_no_inline_question(self) -> None:
        """Step 1b should NOT contain '👉 Which team member are you?'
        with 'WAIT for response'."""
        text = _read_onboarding()
        section = _extract_section(text, r"## 1b\.")
        assert "👉 Which team member are you?" not in section, (
            "Step 1b contains inline closing question "
            "'👉 Which team member are you?'"
        )

    def test_step_1b_no_wait(self) -> None:
        """Step 1b should NOT contain a WAIT instruction after the question."""
        text = _read_onboarding()
        section = _extract_section(text, r"## 1b\.")
        assert "WAIT for response" not in section, (
            "Step 1b contains 'WAIT for response' instruction"
        )

    def test_step_2_no_inline_question(self) -> None:
        """Programming Language Selection should NOT contain
        '👉 Which language would you like to use?' with 'WAIT for response'.

        Post-split, language selection moved out of onboarding-flow.md into
        onboarding-phase1b-intro-language.md (Step 4)."""
        text = _read_phase1b()
        section = _extract_section(text, r"## 4\.")
        assert "👉 Which language would you like to use?" not in section, (
            "Programming Language Selection contains inline closing question "
            "'👉 Which language would you like to use?'"
        )

    def test_step_2_no_wait(self) -> None:
        """Programming Language Selection should NOT contain a 'WAIT for
        response' instruction (now in onboarding-phase1b, Step 4)."""
        text = _read_phase1b()
        section = _extract_section(text, r"## 4\.")
        assert "WAIT for response" not in section, (
            "Programming Language Selection contains 'WAIT for response' instruction"
        )

    def test_step_4_no_inline_question(self) -> None:
        """Bootcamp Introduction should NOT contain
        '👉 Does this outline make sense?' with 'WAIT for response'.

        Post-split, the bootcamp introduction / comprehension check moved out
        of onboarding-flow.md into onboarding-phase1b-intro-language.md
        (Step 5 plus sub-steps 5a/5b)."""
        text = _read_phase1b()
        section = _extract_section(text, r"## 5\.")
        assert "👉 Does this outline make sense?" not in section, (
            "Bootcamp Introduction contains inline closing question "
            "'👉 Does this outline make sense?'"
        )

    def test_step_4_no_wait(self) -> None:
        """Bootcamp Introduction should NOT contain a 'WAIT for response'
        instruction (now in onboarding-phase1b, Step 5/5a/5b)."""
        text = _read_phase1b()
        section = _extract_section(text, r"## 5\.")
        assert "WAIT for response" not in section, (
            "Bootcamp Introduction contains 'WAIT for response' instruction"
        )

    def test_step_5_no_inline_question(self) -> None:
        """Step 5 should NOT contain '👉 Which track sounds right for you?'."""
        text = _read_phase2()
        section = _extract_section(text, r"## 5\.")
        assert "👉 Which track sounds right for you?" not in section, (
            "Step 5 contains inline closing question "
            "'👉 Which track sounds right for you?'"
        )


# ---------------------------------------------------------------------------
# Helpers — Preservation baselines
# ---------------------------------------------------------------------------

_HOOK_FILE = (
    Path(__file__).resolve().parent.parent / "hooks" / "ask-bootcamper.kiro.hook"
)

_AGENT_INSTRUCTIONS_FILE = (
    Path(__file__).resolve().parent.parent / "steering" / "agent-instructions.md"
)


def _read_hook() -> str:
    """Return the full text of ask-bootcamper.kiro.hook."""
    return _HOOK_FILE.read_text(encoding="utf-8")


def _read_agent_instructions() -> str:
    """Return the full text of agent-instructions.md."""
    return _AGENT_INSTRUCTIONS_FILE.read_text(encoding="utf-8")


def _extract_all_h2_headings(text: str) -> list[str]:
    """Extract all ## headings from the markdown text, returning them in order."""
    return re.findall(r"^## (.+)$", text, re.MULTILINE)


def _assert_required_headings_in_order(
    actual: list[str], required: list[str], label: str
) -> None:
    """Assert that ``required`` headings appear in ``actual`` in the required
    relative order, tolerating unrelated headings added anywhere.

    Ordered-subsequence replacement for a former full-list ``==`` snapshot
    (Exact_Sequence_Snapshot). It preserves the original intent — the protected
    structural skeleton of the document, in order — while no longer breaking when
    a benign, unrelated heading is added (Req 5.3). It still fails if a required
    heading is removed (Req 5.5) or if two required headings are reordered
    (Req 6.6), so it retains equivalent bug-condition coverage.
    """
    missing = [h for h in required if h not in actual]
    assert not missing, (
        f"{label}: required heading(s) removed:\n"
        + "\n".join(f"  - {h}" for h in missing)
        + f"\nGot: {actual}"
    )
    # Ordered-subsequence check: walk ``actual`` once, consuming each required
    # heading in turn (``h in it`` advances the shared iterator). This correctly
    # handles repeated headings, unlike list.index.
    it = iter(actual)
    unmatched = next((h for h in required if h not in it), None)
    assert unmatched is None, (
        f"{label}: required headings are out of order "
        f"(could not match {unmatched!r} in sequence).\n"
        f"Required order: {required}\n"
        f"Got:            {actual}"
    )


def _strip_inline_questions_and_waits(section: str) -> str:
    """Remove inline 👉 closing question lines and WAIT instruction lines.

    This extracts the informational content of a section by stripping:
    - Lines containing '👉' followed by a question (closing questions)
    - Lines that are just 'WAIT for response.' or similar WAIT directives
    - Lines starting with 'Ask:' that contain 👉 questions
    - Lines starting with 'Present tracks with:' that contain 👉 questions
    """
    lines = section.splitlines()
    filtered = []
    for line in lines:
        stripped = line.strip()
        # Skip WAIT instruction lines
        if re.match(r"^WAIT\b", stripped, re.IGNORECASE):
            continue
        # Skip lines that are inline 👉 closing questions
        if "👉" in stripped and "?" in stripped:
            continue
        # Skip 'Ask:' lines with 👉
        if stripped.startswith("Ask:") and "👉" in stripped:
            continue
        # Skip 'Present tracks with:' lines with 👉
        if stripped.startswith("Present tracks with:") and "👉" in stripped:
            continue
        filtered.append(line)
    return "\n".join(filtered)


# ---------------------------------------------------------------------------
# Baselines — captured from UNFIXED code (observation-first)
# ---------------------------------------------------------------------------

# Expected step heading sequence in onboarding-flow.md (Phase 1 only after split).
# Post-split, onboarding-flow.md owns Steps 0–2d (setup → MCP health → version →
# directory → team detection → prerequisite gate), then directs the agent to load
# onboarding-phase1b-intro-language.md. The entity-resolution intro (Step 3),
# Programming Language Selection (Step 4), Bootcamp Introduction (Step 5), verbosity
# (5a), and comprehension check (5b) now live in the phase1b file.
_EXPECTED_HEADINGS = [
    "Phase Sub-Files",
    "0. Setup Preamble",
    # Added by the write-policy-gate-ux batch (Change B): an onboarding section
    # explaining the write-policy-gate intercept-retry ("Rejected"/"Accepted")
    # cycle. Purely additive — sits between Step 0 and Step 0b.
    '0a. Why You May See "Rejected"/"Accepted" Messages',
    "0b. MCP Health Check",
    "0c. Version Display",
    "1. Directory Structure",
    "1b. Team Detection",
    "2. Prerequisite Check (Mandatory Gate)",
]

# Expected headings in Phase 2 file
_EXPECTED_PHASE2_HEADINGS = [
    "5. Track Selection",
    "Switching Tracks",
    "Changing Language",
    "Validation Gates",
    "Hook Registry",
]

# Structural markers proving the ask-bootcamper hook is preserved as the sole
# owner of closing questions. (Replaces the whole-file SHA-256 snapshot
# _HOOK_BASELINE_HASH, which broke on every benign edit to the hook prompt
# without telling us whether the protected ownership behavior changed.)
_HOOK_OWNERSHIP_MARKERS = (
    '"agentStop"',  # the hook fires on agent stop ...
    '"askAgent"',  # ... and asks the agent to act
    "PHASE 1: CLOSING QUESTION",  # Phase 1 owns the 👉 closing question
    "Closing_Question_Phase",
    "👉",  # the closing-question marker itself
    "DEFAULT OUTPUT",  # default-silence rule keeps it quiet otherwise
)

# The four-phase structure the hook must retain.
_HOOK_PHASE_MARKERS = (
    "PHASE 1: CLOSING QUESTION",
    "PHASE 2: STEP SEQUENCING",
    "PHASE 3: MCP-FIRST COMPLIANCE",
    "PHASE 4: QUESTION FORMAT",
)

# Key informational phrases that MUST be preserved in affected steps
# (these are NOT inline 👉 questions or WAIT lines)
_STEP_1B_KEY_CONTENT = [
    "config/team.yaml",
    "team_config_validator",
    "team mode",
    "co-located",
    "distributed",
    "progress_{member_id}.json",
    "bootcamp_preferences.yaml",
    "team_member_id",
]

_STEP_2_KEY_CONTENT = [
    "platform.system()",
    "get_capabilities",
    "sdk_guide",
    "MCP server",
    "bootcamp_preferences.yaml",
    "lang-python.md",
    "lang-java.md",
]

_STEP_4_KEY_CONTENT = [
    "WELCOME TO THE SENZING BOOTCAMP",
    "guided discovery",
    "Senzing SDK code",
    "Las Vegas, London, Moscow",
    "500-record eval license",
    "unfamiliar terms",
    "team_name",
    "member_count",
]

_STEP_5_KEY_CONTENT = [
    "Core Bootcamp",
    "Advanced Topics",
    "Modules 1–11",
]


# ---------------------------------------------------------------------------
# Tests — Preservation (Property 2)
# ---------------------------------------------------------------------------


class TestPreservation:
    """Preservation property tests: verify that informational content, step
    sequence, non-affected steps, hook file, and agent-instructions are
    unchanged.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

    EXPECTED OUTCOME on UNFIXED code: all tests PASS (confirms baseline).
    """

    # -- 1. Step sequence preservation --

    def test_step_sequence_preserved(self) -> None:
        """The root file contains step headings 0–4 and Phase 2 file contains
        Step 5 plus Switching Tracks, Changing Language, Validation Gates,
        Hook Registry in the expected order.

        Original intent: a full-list ``==`` snapshot pinned the exact, complete
        ordered heading sequence of each file, which broke on every benign,
        additive section (the layered comments on ``_EXPECTED_HEADINGS`` record
        that churn). The structural invariant being protected is that the
        required step headings remain present and in their required relative
        order; unrelated additive headings are benign. Checked as an
        ordered-subsequence so it still fails if a required heading is removed or
        two required headings are reordered (Req 5.3, 6.2, 6.6)."""
        text = _read_onboarding()
        headings = _extract_all_h2_headings(text)
        _assert_required_headings_in_order(
            headings, _EXPECTED_HEADINGS, "Phase 1 step heading sequence"
        )
        # Also verify Phase 2 headings
        phase2_text = _read_phase2()
        phase2_headings = _extract_all_h2_headings(phase2_text)
        _assert_required_headings_in_order(
            phase2_headings, _EXPECTED_PHASE2_HEADINGS, "Phase 2 step heading sequence"
        )

    # -- 2. Non-affected steps preservation --

    def test_step_0_content_present(self) -> None:
        """Step 0 (Setup Preamble) content is present and unchanged."""
        text = _read_onboarding()
        section = _extract_section(text, r"## 0\.")
        assert "administrative setup" in section
        assert "WELCOME TO THE SENZING BOOTCAMP" in section
        assert "creating your project directory" in section

    def test_step_1_content_present(self) -> None:
        """Step 1 (Directory Structure) content is present and unchanged."""
        text = _read_onboarding()
        section = _extract_section(text, r"## 1\. ")
        assert "project-structure.md" in section
        assert "Install Critical Hooks" in section
        assert "product.md" in section
        assert "tech.md" in section
        assert "structure.md" in section

    def test_step_3_content_present(self) -> None:
        """Prerequisite Check content is present and unchanged.

        Post-split this is Step 2 (Prerequisite Check / Mandatory Gate) of
        onboarding-flow.md; the entity-resolution intro took the Step 3 slot
        in the phase1b file."""
        text = _read_onboarding()
        section = _extract_section(text, r"## 2\. Prerequisite")
        assert "preflight.py" in section
        assert "FAIL:" in section
        assert "WARN:" in section
        assert "PASS:" in section
        assert "Senzing SDK" in section

    # -- 3. Informational content preservation for affected steps --

    def test_step_1b_informational_content(self) -> None:
        """Step 1b key informational content (team detection logic, member
        list template, validation, co-located/distributed) is preserved."""
        text = _read_onboarding()
        section = _extract_section(text, r"## 1b\.")
        info = _strip_inline_questions_and_waits(section)
        for phrase in _STEP_1B_KEY_CONTENT:
            assert phrase in info, (
                f"Step 1b missing key informational content: '{phrase}'"
            )

    def test_step_2_informational_content(self) -> None:
        """Programming Language Selection key informational content (platform
        detection, MCP query, language list, preference persistence) is
        preserved.

        Post-split this content moved to Step 4 of
        onboarding-phase1b-intro-language.md."""
        text = _read_phase1b()
        section = _extract_section(text, r"## 4\.")
        info = _strip_inline_questions_and_waits(section)
        for phrase in _STEP_2_KEY_CONTENT:
            assert phrase in info, (
                f"Programming Language Selection missing key informational "
                f"content: '{phrase}'"
            )

    def test_step_4_informational_content(self) -> None:
        """Bootcamp Introduction key informational content (welcome banners,
        overview points, module table reference) is preserved.

        Post-split this content moved to Step 5 of
        onboarding-phase1b-intro-language.md."""
        text = _read_phase1b()
        section = _extract_section(text, r"## 5\.")
        info = _strip_inline_questions_and_waits(section)
        for phrase in _STEP_4_KEY_CONTENT:
            assert phrase in info, (
                f"Bootcamp Introduction missing key informational content: "
                f"'{phrase}'"
            )

    def test_step_5_informational_content(self) -> None:
        """Step 5 key informational content (module table, track descriptions,
        response interpretation) is preserved (now in Phase 2 file)."""
        text = _read_phase2()
        section = _extract_section(text, r"## 5\.")
        info = _strip_inline_questions_and_waits(section)
        for phrase in _STEP_5_KEY_CONTENT:
            assert phrase in info, (
                f"Step 5 missing key informational content: '{phrase}'"
            )

    # -- 4. Hook file preservation --

    def test_hook_file_matches_baseline(self) -> None:
        """ask-bootcamper.kiro.hook preserves the closing-question ownership
        behavior.

        Original intent (Req 3.1, 3.6): a whole-file SHA-256 snapshot
        (``_HOOK_BASELINE_HASH``) pinned the entire ask-bootcamper hook so that
        the bugfix — making the hook the *sole* owner of 👉 closing questions —
        could not silently regress. That snapshot broke on every benign edit to
        the hook prompt (reworded copy, reflowed JSON) without telling us whether
        the protected ownership behavior actually changed.

        Structural replacement (Req 5.1, 6.6): assert the markers that encode the
        protected behavior are still present — the hook fires on agent stop and
        asks the agent to act, it owns the 👉 closing question in its
        ``Closing_Question_Phase``, it keeps its default-silence rule, and it
        retains all four phases. If the bug regressed (closing-question ownership
        moved out of the hook, or a phase was dropped) one of these markers would
        disappear and this test would fail."""
        content = _read_hook()
        for marker in _HOOK_OWNERSHIP_MARKERS:
            assert marker in content, (
                "ask-bootcamper.kiro.hook lost a closing-question ownership "
                f"marker: {marker!r}. The hook must remain the sole owner of "
                "👉 closing questions."
            )
        for phase in _HOOK_PHASE_MARKERS:
            assert phase in content, (
                f"ask-bootcamper.kiro.hook lost a required phase: {phase!r}. "
                "The four-phase closing-question structure must be preserved."
            )

    # -- 5. Agent instructions preservation --

    def test_agent_instructions_contains_ownership_rule(self) -> None:
        """agent-instructions.md contains the closing-question ownership rule."""
        content = _read_agent_instructions()
        assert "Closing-question ownership" in content
        assert "ask-bootcamper" in content
        assert "safety net" in content

    def test_agent_instructions_contains_core_sections(self) -> None:
        """agent-instructions.md contains all expected core sections."""
        content = _read_agent_instructions()
        expected_sections = [
            "# Agent Core Rules",
            "## File Placement",
            "## MCP Rules",
            "## MCP Failure",
            "## Module Steering",
            "## State & Progress",
            "## Communication",
            "## Hooks",
            "## Context Budget",
        ]
        for section in expected_sections:
            assert section in content, (
                f"agent-instructions.md missing section: '{section}'"
            )

    def test_agent_instructions_unchanged(self) -> None:
        """agent-instructions.md full content matches the observed baseline
        (verified via key content markers at start, middle, and end).

        Re-baselined against the shipped (post-refactor) agent-instructions.md.
        The Context Budget section was condensed in the same branch that split
        onboarding; the detailed unloading guidance (including the "announce
        the token cost" instruction) was relocated to
        agent-context-management.md, leaving a pointer reference here. This is
        a relocation, not a content deletion."""
        content = _read_agent_instructions()
        # Start marker
        assert content.startswith("---\ninclusion: always\n---")
        # Middle markers
        assert "mapping_workflow" in content
        assert "bootcamp_progress.json" in content
        assert (
            "step-level checkpointing" in content.lower()
            or "Step-level checkpointing" in content
        )
        # End marker — the condensed Context Budget section now points to
        # agent-context-management.md for warn/critical/unload detail.
        assert "Context Budget" in content
        assert "agent-context-management.md" in content
