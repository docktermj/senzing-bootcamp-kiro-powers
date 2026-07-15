"""Tests for the Self-Answering Reinforcement feature.

Validates that forbidden output patterns are documented, STOP markers
exist after 👉 questions, and anti-fabrication instructions are in place.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

_STEERING_DIR = Path(__file__).resolve().parent.parent / "steering"
_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"


class TestForbiddenPatterns:
    """Verify agent-instructions.md contains 'Human:' in forbidden patterns."""

    @pytest.fixture()
    def agent_instructions(self) -> str:
        return (_STEERING_DIR / "agent-instructions.md").read_text(encoding="utf-8")

    def test_contains_human_colon_forbidden(self, agent_instructions: str) -> None:
        """agent-instructions.md lists 'Human:' as a forbidden output pattern."""
        assert '"Human:"' in agent_instructions or "'Human:'" in agent_instructions

    def test_contains_forbidden_output_patterns_section(self, agent_instructions: str) -> None:
        """agent-instructions.md has a FORBIDDEN output patterns rule."""
        assert "FORBIDDEN output patterns" in agent_instructions


class TestOnboardingStopMarkers:
    """Verify onboarding files have 🛑 STOP after 👉 questions."""

    @pytest.fixture()
    def onboarding(self) -> str:
        # The verbosity preference question is Step 4a in
        # onboarding-phase1b-intro-language.md. After the preface reorder, the
        # comprehension check moved to phase 2 (Step 5b); its STOP marker is
        # asserted via the onboarding_phase2 fixture.
        return (_STEERING_DIR / "onboarding-phase1b-intro-language.md").read_text(
            encoding="utf-8"
        )

    @pytest.fixture()
    def onboarding_phase2(self) -> str:
        return (_STEERING_DIR / "onboarding-phase2-track-setup.md").read_text(encoding="utf-8")

    def test_stop_after_verbosity_question(self, onboarding: str) -> None:
        """A stop-and-wait directive follows the verbosity preference 👉 question.

        After the clean-question-presentation fix the 🛑/⛔ glyph is an
        internal-only directive that need not render beside the question, so a
        textual stop-and-wait directive ("end your turn" / "wait for the
        bootcamper") is an equally valid boundary — the same reconciliation
        TestStopMarkerProperty applies.
        """
        idx = onboarding.find("how much detail they want")
        assert idx != -1
        after = onboarding[idx:idx + 900]
        lowered = after.lower()
        assert (
            "🛑" in after
            or "⛔" in after
            or "end your turn" in lowered
            or "wait for the bootcamper" in lowered
        )

    def test_stop_after_comprehension_check(self, onboarding_phase2: str) -> None:
        """🛑 STOP exists after the comprehension check 👉 question.

        After the preface reorder, the comprehension check follows programming
        language selection and lives in onboarding-phase2-track-setup.md
        (Step 5b), so the STOP marker is asserted there.
        """
        idx = onboarding_phase2.find("does everything so far make sense")
        assert idx != -1
        after = onboarding_phase2[idx:idx + 300]
        assert "🛑" in after

    def test_stop_after_track_selection_question(self, onboarding_phase2: str) -> None:
        """🛑 STOP exists after the track selection 👉 question in Phase 2."""
        idx = onboarding_phase2.find("Present tracks")
        assert idx != -1
        after = onboarding_phase2[idx:idx + 1500]
        assert "🛑" in after


class TestAskBootcamperAntiFabrication:
    """Verify ask-bootcamper hook contains anti-fabrication instruction."""

    @pytest.fixture()
    def hook_prompt(self) -> str:
        path = _HOOKS_DIR / "ask-bootcamper.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        return data["hooks"][0]["action"]["prompt"]

    def test_contains_human_colon_prohibition(self, hook_prompt: str) -> None:
        """Hook prompt prohibits generating 'Human:' text."""
        assert "Human:" in hook_prompt
        assert "NEVER" in hook_prompt


class TestStopMarkerProperty:
    """Property test: steering files with 👉 questions have 🛑 STOP nearby."""

    @given(data=st.data())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_pointing_questions_have_stop_markers(self, data: st.DataObject) -> None:
        """For onboarding files, 👉 questions outside code blocks have 🛑 within 5 lines."""
        # Test against both onboarding-flow.md (Phase 1) and
        # onboarding-phase2-track-setup.md (Phase 2)
        onboarding_files = [
            _STEERING_DIR / "onboarding-flow.md",
            _STEERING_DIR / "onboarding-phase2-track-setup.md",
        ]

        # Collect all 👉 questions from both files.
        # A line is a 👉 question/instruction if it starts with 👉 (after
        # optional blockquote markers or whitespace). Lines that merely
        # mention 👉 in the middle of prose (e.g., describing the hook) are
        # excluded.
        all_questions: list[tuple[str, int, list[str]]] = []
        for filepath in onboarding_files:
            content = filepath.read_text(encoding="utf-8")
            lines = content.splitlines()
            in_code_block = False
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    continue
                stripped = line.lstrip("> ").strip()
                if stripped.startswith("👉"):
                    all_questions.append((filepath.name, i, lines))

        if not all_questions:
            return

        # Pick a random question from the combined set
        chosen = data.draw(st.sampled_from(all_questions))
        filename, idx, lines = chosen

        # Check for a stop-and-wait directive within 5 non-blank lines after the
        # question. Accept the 🛑 / ⛔ glyphs OR an explicit textual
        # stop-and-wait directive: the programming-language gate (now in phase 2
        # after the preface reorder) places its "end your turn ... wait for the
        # bootcamper" internal directive immediately after the 👉 question, with
        # the 🛑 glyph farther down in the same gate block. Both forms are valid
        # stop-and-wait boundaries that prevent the agent from self-answering.
        found_marker = False
        non_blank_seen = 0
        for scan_idx in range(idx + 1, min(len(lines), idx + 10)):
            scan_line = lines[scan_idx]
            if not scan_line.strip():
                continue
            non_blank_seen += 1
            lowered = scan_line.lower()
            if (
                "🛑" in scan_line
                or "⛔" in scan_line
                or "end your turn" in lowered
                or "wait for the bootcamper" in lowered
            ):
                found_marker = True
                break
            if non_blank_seen >= 5:
                break

        assert found_marker, (
            f"{filename} line {idx + 1} has a 👉 question without a stop-and-wait "
            f"directive (🛑/⛔ or 'end your turn'/'wait for the bootcamper') "
            f"within 5 lines:\n  {lines[idx].strip()[:80]}"
        )
