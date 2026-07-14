"""Degrade-safely content tests for the Ask-Once Guarantee.

Requirement 4.4 states that when a Question_Ledger read or write fails, the
behavior SHALL degrade safely — the agent falls back to the existing
checkpoint/preference state and never blocks the bootcamper — but SHALL NOT
treat an unknown state as license to re-ask a previously answered Question when
`config/bootcamp_preferences.yaml` already contains the answer (the ledger is
the primary mechanism; preferences are the safety net).

This is a documented-behavior guarantee expressed in steering. These tests
assert that the normative guidance states both halves of the guarantee:

1. A ledger read/write failure degrades safely: fall back to
   checkpoint/preference state and never block the bootcamper.
2. An unknown/unavailable ledger state does NOT license re-asking a question
   whose answer is already present in preferences.

The single normative home is ``conversation-protocol.md`` (The Ask-Once
Guarantee); ``agent-instructions.md`` (State & Progress -> Question_Ledger)
restates the operational fallback consistently.

Requirements validated: 4.4
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _REPO_ROOT / "senzing-bootcamp" / "steering"

_CONVERSATION_PROTOCOL: Path = _STEERING_DIR / "conversation-protocol.md"
_AGENT_INSTRUCTIONS: Path = _STEERING_DIR / "agent-instructions.md"

# The steering files that document the degrade-safely behavior, parametrized so
# both the single normative home and the operational restatement are asserted.
_DEGRADE_SAFELY_FILES = [
    pytest.param(_CONVERSATION_PROTOCOL, id="conversation-protocol.md"),
    pytest.param(_AGENT_INSTRUCTIONS, id="agent-instructions.md"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    """Return the UTF-8 text of a steering file, asserting it exists."""
    assert path.exists(), f"Steering file not found: {path}"
    return path.read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    """Lowercase and collapse runs of whitespace to single spaces.

    Makes substring assertions robust to line wrapping and incidental spacing
    differences in the steering prose.
    """
    return re.sub(r"\s+", " ", text).lower()


# ---------------------------------------------------------------------------
# TestDegradeSafelyGuidance
# ---------------------------------------------------------------------------


class TestDegradeSafelyGuidance:
    """Steering documents the degrade-safely fallback for the Question_Ledger.

    Requirement 4.4 — a ledger read/write failure falls back to
    checkpoint/preference state and never blocks the bootcamper.

    **Validates: Requirements 4.4**
    """

    @pytest.mark.parametrize("path", _DEGRADE_SAFELY_FILES)
    def test_states_ledger_failure_degrades_safely(self, path: Path) -> None:
        """Guidance must say a ledger read/write failure degrades safely."""
        content = _normalize(_read(path))
        assert "degrade safely" in content or "degrades safely" in content, (
            f"{path.name} must state that a Question_Ledger read/write failure "
            "degrades safely"
        )

    @pytest.mark.parametrize("path", _DEGRADE_SAFELY_FILES)
    def test_falls_back_to_checkpoint_or_preference_state(self, path: Path) -> None:
        """Guidance must say the fallback is checkpoint/preference state."""
        content = _normalize(_read(path))
        assert "checkpoint" in content and "preference" in content, (
            f"{path.name} must state that the fallback is existing "
            "checkpoint/preference state"
        )

    @pytest.mark.parametrize("path", _DEGRADE_SAFELY_FILES)
    def test_never_blocks_the_bootcamper(self, path: Path) -> None:
        """Guidance must promise the fallback never blocks the bootcamper."""
        content = _normalize(_read(path))
        assert "never block the bootcamper" in content, (
            f"{path.name} must state that degrading safely never blocks the "
            "bootcamper"
        )


# ---------------------------------------------------------------------------
# TestUnknownStateIsNotLicenseToReAsk
# ---------------------------------------------------------------------------


class TestUnknownStateIsNotLicenseToReAsk:
    """An unknown ledger state does NOT license re-asking an answered question.

    Requirement 4.4 — when preferences already contain the answer, an unknown or
    unavailable ledger state SHALL NOT be treated as license to re-ask (spam) a
    previously answered Question. The ledger is the primary mechanism;
    preferences are the safety net.

    **Validates: Requirements 4.4**
    """

    @pytest.mark.parametrize("path", _DEGRADE_SAFELY_FILES)
    def test_unknown_state_is_not_license_to_reask(self, path: Path) -> None:
        """Guidance must forbid re-asking on an unknown/unavailable ledger state."""
        content = _normalize(_read(path))
        assert "never license to re-ask" in content, (
            f"{path.name} must state that an unknown or unavailable ledger state "
            "is never license to re-ask a previously answered question"
        )

    @pytest.mark.parametrize("path", _DEGRADE_SAFELY_FILES)
    def test_preferences_answer_blocks_reask(self, path: Path) -> None:
        """The forbidden re-ask is scoped to answers already held in preferences."""
        content = _normalize(_read(path))
        assert "bootcamp_preferences.yaml" in content, (
            f"{path.name} must anchor the safety net to the answer already "
            "present in config/bootcamp_preferences.yaml"
        )
        assert "answer is already present" in content, (
            f"{path.name} must forbid re-asking when the answer is already "
            "present in preferences"
        )

    @pytest.mark.parametrize("path", _DEGRADE_SAFELY_FILES)
    def test_preferences_are_the_safety_net(self, path: Path) -> None:
        """Guidance must frame preferences as the safety net behind the ledger."""
        content = _normalize(_read(path))
        assert "preferences are the safety net" in content, (
            f"{path.name} must state that preferences are the safety net (the "
            "ledger is the primary mechanism)"
        )


# ---------------------------------------------------------------------------
# TestNormativeHomeOwnsDegradeSafely
# ---------------------------------------------------------------------------


class TestNormativeHomeOwnsDegradeSafely:
    """The single normative home documents the degrade-safely rule.

    The Ask-Once Guarantee in ``conversation-protocol.md`` is the single home of
    the ask-once rule, so it must also own the degrade-safely clause rather than
    leaving it to a downstream file only.

    **Validates: Requirements 4.4**
    """

    def test_degrade_clause_lives_in_ask_once_guarantee_section(self) -> None:
        """The degrade-safely clause must sit under The Ask-Once Guarantee."""
        content = _read(_CONVERSATION_PROTOCOL)
        heading = "## The Ask-Once Guarantee"
        assert heading in content, (
            "conversation-protocol.md must contain The Ask-Once Guarantee heading"
        )
        # Slice from the guarantee heading to the next H2 (or EOF) and assert the
        # degrade-safely clause is inside that section, not elsewhere.
        start = content.index(heading)
        rest = content[start + len(heading):]
        next_h2 = rest.find("\n## ")
        section = rest if next_h2 == -1 else rest[:next_h2]
        section_norm = _normalize(section)
        assert "never license to re-ask" in section_norm, (
            "The degrade-safely 'never license to re-ask' clause must live inside "
            "the Ask-Once Guarantee section of conversation-protocol.md"
        )
        assert "preferences are the safety net" in section_norm, (
            "The Ask-Once Guarantee section must frame preferences as the safety net"
        )
