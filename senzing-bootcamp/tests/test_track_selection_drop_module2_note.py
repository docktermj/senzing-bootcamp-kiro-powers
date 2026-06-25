"""Fix-checking and preservation tests for the track-selection-drop-module2-note bugfix.

Feature: track-selection-drop-module2-note (BUGFIX)

Bug condition: Section "5. Track Selection" of the Track_Setup_File
(`senzing-bootcamp/steering/onboarding-phase2-track-setup.md`) still carries the
standalone Auto_Insertion_Note line:

    "Module 2 is automatically inserted before any module that needs the SDK."

Property 1 (Fix Checking): the fixed Track_Setup_File SHALL NOT contain the
Auto_Insertion_Note. Authored against the UNFIXED file, so this test is EXPECTED TO
FAIL before the edit (the failure confirms the bug exists) and PASS after.

Property 2 (Preservation): the track options (Core Bootcamp, Advanced Topics), the
⛔ mandatory stop gate, the response-interpretation guidance, and the
`onboarding-flow.md` "explicitly or auto-inserted" explanation SHALL remain present and
unchanged. These preservation tests PASS on the UNFIXED file (baseline) and continue to
PASS after the fix.

Validates: Requirements 2.1, 2.2, 3.2, 3.3
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Real files under test
# ---------------------------------------------------------------------------

_POWER_ROOT: Path = Path(__file__).resolve().parent.parent
_STEERING_DIR: Path = _POWER_ROOT / "steering"

_TRACK_SETUP_FILE: Path = _STEERING_DIR / "onboarding-phase2-track-setup.md"
_ONBOARDING_FLOW_FILE: Path = _STEERING_DIR / "onboarding-flow.md"

# The standalone Module 2 auto-insertion note removed by this bugfix.
_AUTO_INSERTION_NOTE: str = (
    "Module 2 is automatically inserted before any module that needs the SDK."
)


def _read(path: Path) -> str:
    """Read a file as UTF-8 text.

    Args:
        path: The file to read.

    Returns:
        The file contents decoded as UTF-8.
    """
    return path.read_text(encoding="utf-8")


class TestFixChecking:
    """Property 1: the Auto_Insertion_Note is removed from track selection.

    Authored against the UNFIXED Track_Setup_File, so this test FAILS before the edit
    (confirming the bug) and PASSES after the note is removed.

    Validates: Requirements 2.1
    """

    def test_track_selection_omits_auto_insertion_note(self) -> None:
        """Track_Setup_File must NOT contain the Module 2 auto-insertion note."""
        content = _read(_TRACK_SETUP_FILE)
        assert _AUTO_INSERTION_NOTE not in content, (
            "Track selection must not carry the standalone Module 2 auto-insertion "
            f"note: {_AUTO_INSERTION_NOTE!r}"
        )


class TestPreservation:
    """Property 2: everything else in track setup (and onboarding-flow) is unchanged.

    These tests pin the baseline content that must survive the fix; they PASS on the
    UNFIXED files and continue to PASS after the note is removed.

    Validates: Requirements 2.2, 3.2, 3.3
    """

    def test_track_options_present(self) -> None:
        """Both track options remain in the Track_Setup_File."""
        content = _read(_TRACK_SETUP_FILE)
        assert "Core Bootcamp" in content, "Core Bootcamp track option must remain"
        assert "Advanced Topics" in content, "Advanced Topics track option must remain"

    def test_mandatory_stop_gate_present(self) -> None:
        """The mandatory stop gate text remains in the Track_Setup_File."""
        content = _read(_TRACK_SETUP_FILE)
        assert "\u26d4" in content, "The mandatory stop gate marker must remain"
        assert "MANDATORY GATE \u2014 STOP HERE." in content, (
            "The mandatory stop gate text must remain"
        )

    def test_response_interpretation_present(self) -> None:
        """The 'Interpreting responses:' guidance remains in the Track_Setup_File."""
        content = _read(_TRACK_SETUP_FILE)
        assert "Interpreting responses:" in content, (
            "The response-interpretation guidance must remain"
        )

    def test_onboarding_flow_explanation_retained(self) -> None:
        """`onboarding-flow.md` keeps the 'explicitly or auto-inserted' explanation."""
        content = _read(_ONBOARDING_FLOW_FILE)
        assert "explicitly or auto-inserted" in content, (
            "The onboarding-flow.md auto-insertion explanation must remain"
        )
