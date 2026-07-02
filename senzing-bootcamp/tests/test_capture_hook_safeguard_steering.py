"""Steering-content test for the capture-hook completion safeguard.

Feature: capture-hook-completion-safeguard.

This is a *steering-content* test: it reads the on-disk steering file
``senzing-bootcamp/steering/session-resume-phase2-setup-recovery.md`` and
asserts the existing session-start **Capture-Critical Warn-on-Absence Check**
is still present and remains advisory-only / never-blocking. It is a separate
concern from the script-behavior tests in ``test_capture_hook_safeguard.py``,
so per ``structure.md`` it lives in its own module.
"""

from __future__ import annotations

from pathlib import Path

_STEERING_FILE = (
    Path(__file__).resolve().parent.parent
    / "steering"
    / "session-resume-phase2-setup-recovery.md"
)


class TestWarnOnAbsencePreserved:
    """The session-start Warn-on-Absence check must not be removed or weakened.

    Validates: Requirements 3.1
    """

    def _read(self) -> str:
        """Return the steering file's text, failing clearly if it is missing."""
        assert _STEERING_FILE.exists(), f"steering file not found: {_STEERING_FILE}"
        return _STEERING_FILE.read_text(encoding="utf-8")

    def test_warn_on_absence_section_present(self) -> None:
        """The Capture-Critical Warn-on-Absence Check heading is still present."""
        text = self._read()
        assert "## Capture-Critical Warn-on-Absence Check" in text

    def test_names_the_three_capture_critical_hooks(self) -> None:
        """The check still names all three capture-critical hooks."""
        text = self._read()
        for hook_id in ("session-log-events", "module-recap-append", "ask-bootcamper"):
            assert hook_id in text, f"missing capture-critical hook reference: {hook_id}"

    def test_advisory_only_never_blocks_language_present(self) -> None:
        """The advisory-only / never-blocks phrasing is preserved verbatim."""
        text = self._read()
        assert "**advisory only**" in text
        assert "it never blocks the session" in text

    def test_surfaces_both_install_options(self) -> None:
        """Both install options (createHook registry and installer) are still offered."""
        text = self._read()
        assert "createHook" in text
        assert "python3 senzing-bootcamp/scripts/install_hooks.py --essential" in text
