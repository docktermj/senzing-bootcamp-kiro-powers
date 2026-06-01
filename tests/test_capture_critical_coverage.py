"""Capture-critical coverage example tests (Theme C).

Validates that capture-critical hook coverage is documented across both
install paths:

- **Requirement 10.2** — the createHook-from-registry path creates the
  capture-critical hooks at onboarding/session start. The onboarding steering
  (``senzing-bootcamp/steering/agent-instructions.md``) must document that
  ``module-recap-append`` and ``session-log-events`` are added to the
  onboarding ``createHook``-from-registry set alongside the existing critical
  ``ask-bootcamper`` hook.
- **Requirement 10.4** — the session-start warn-on-absence behavior. The
  session-resume steering
  (``senzing-bootcamp/steering/session-resume-phase2-setup-recovery.md``) must
  document inspecting ``.kiro/hooks`` and warning which capture-critical hooks
  are absent, plus how to install them.

These are prose/example assertions (not property-based), so they use robust
case-insensitive substring and windowed co-occurrence checks against the
rendered documents rather than brittle exact-line matches.

Requirements validated: 10.2, 10.4
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Doc paths resolved relative to this test file.
# ---------------------------------------------------------------------------

_STEERING_DIR: Path = (
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "steering"
)

_ONBOARDING_DOC: Path = _STEERING_DIR / "agent-instructions.md"
_SESSION_RESUME_DOC: Path = (
    _STEERING_DIR / "session-resume-phase2-setup-recovery.md"
)

# The two module-defined capture-critical hooks that must join the onboarding
# createHook set alongside the already-critical ask-bootcamper hook (Req 10.2).
_ONBOARDING_CAPTURE_HOOKS: tuple[str, ...] = (
    "module-recap-append",
    "session-log-events",
)

# All three capture-critical hooks (Req 10.4 warn-on-absence set).
_CAPTURE_CRITICAL: tuple[str, ...] = (
    "session-log-events",
    "module-recap-append",
    "ask-bootcamper",
)

# Window (in characters) for "appears near" co-occurrence checks. Generous so
# the assertions track meaning rather than exact phrasing/layout.
_WINDOW: int = 800


def _read(path: Path) -> str:
    """Read a steering document.

    Args:
        path: The steering file to read.

    Returns:
        The full UTF-8 text of the file.
    """
    assert path.exists(), f"Steering file not found: {path}"
    return path.read_text(encoding="utf-8")


def _near(haystack_lower: str, anchor: str, *needles: str, window: int = _WINDOW) -> bool:
    """Return True if every needle appears within ``window`` chars of ``anchor``.

    The check is case-insensitive: ``haystack_lower``, ``anchor``, and each
    ``needle`` are compared in lowercase. Every occurrence window of the anchor
    is considered, so a match anywhere is sufficient.

    Args:
        haystack_lower: The lowercased document text to search.
        anchor: The anchor substring to center the window on.
        needles: Substrings that must all appear within the window.
        window: Half-width of the search window in characters.

    Returns:
        True if some occurrence of ``anchor`` has all needles within range.
    """
    anchor_l = anchor.lower()
    needles_l = [n.lower() for n in needles]
    start = 0
    while True:
        idx = haystack_lower.find(anchor_l, start)
        if idx < 0:
            return False
        lo = max(0, idx - window)
        hi = idx + len(anchor_l) + window
        region = haystack_lower[lo:hi]
        if all(n in region for n in needles_l):
            return True
        start = idx + 1


# Module-level reads: the documents are static during a test run.
_ONBOARDING_TEXT: str = _read(_ONBOARDING_DOC)
_ONBOARDING_LOWER: str = _ONBOARDING_TEXT.lower()
_RESUME_TEXT: str = _read(_SESSION_RESUME_DOC)
_RESUME_LOWER: str = _RESUME_TEXT.lower()


# ---------------------------------------------------------------------------
# TestCaptureCriticalCoverage
# ---------------------------------------------------------------------------


class TestCaptureCriticalCoverage:
    """Validate capture-critical coverage documentation.

    **Validates: Requirements 10.2, 10.4**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        """Expose document content to every test in this class."""
        self.onboarding: str = _ONBOARDING_TEXT
        self.onboarding_lower: str = _ONBOARDING_LOWER
        self.resume: str = _RESUME_TEXT
        self.resume_lower: str = _RESUME_LOWER

    # -- Requirement 10.2: onboarding createHook-from-registry set ----------

    def test_onboarding_doc_references_createhook(self) -> None:
        """Onboarding steering must describe a createHook flow (Req 10.2)."""
        assert "createhook" in self.onboarding_lower, (
            "agent-instructions.md must document the createHook flow"
        )

    def test_capture_hooks_present_in_onboarding_doc(self) -> None:
        """Both module-defined capture hooks must appear in onboarding doc (Req 10.2)."""
        for hook_id in _ONBOARDING_CAPTURE_HOOKS:
            assert hook_id in self.onboarding, (
                f"agent-instructions.md must reference '{hook_id}'"
            )

    def test_capture_hooks_added_to_onboarding_createhook_set(self) -> None:
        """Both capture hooks must be documented as part of the onboarding createHook set (Req 10.2).

        Each of ``module-recap-append`` and ``session-log-events`` must appear
        near a ``createHook`` reference in an onboarding / session-start
        context, establishing that they are created at session start (not
        deferred to module start).
        """
        for hook_id in _ONBOARDING_CAPTURE_HOOKS:
            near_createhook = _near(self.onboarding_lower, hook_id, "createhook")
            assert near_createhook, (
                f"agent-instructions.md must document '{hook_id}' as part of "
                "the onboarding createHook-from-registry set"
            )
            near_session_start = _near(
                self.onboarding_lower, hook_id, "onboarding"
            ) or _near(self.onboarding_lower, hook_id, "session start")
            assert near_session_start, (
                f"agent-instructions.md must document '{hook_id}' as created "
                "during onboarding / session start"
            )

    def test_capture_hooks_alongside_ask_bootcamper(self) -> None:
        """Capture hooks must be documented alongside the existing critical ask-bootcamper (Req 10.2)."""
        for hook_id in _ONBOARDING_CAPTURE_HOOKS:
            assert _near(self.onboarding_lower, hook_id, "ask-bootcamper"), (
                f"agent-instructions.md must document '{hook_id}' alongside the "
                "critical ask-bootcamper hook in the onboarding createHook set"
            )

    # -- Requirement 10.4: session-start warn-on-absence --------------------

    def test_resume_doc_documents_capture_critical(self) -> None:
        """Session-resume doc must use the capture-critical designation (Req 10.4)."""
        assert "capture-critical" in self.resume_lower, (
            "session-resume-phase2-setup-recovery.md must reference the "
            "'capture-critical' hooks"
        )

    def test_resume_doc_inspects_kiro_hooks_directory(self) -> None:
        """Session-resume doc must document inspecting .kiro/hooks (Req 10.4)."""
        assert ".kiro/hooks" in self.resume, (
            "session-resume-phase2-setup-recovery.md must document inspecting "
            "the .kiro/hooks directory"
        )

    def test_resume_doc_warns_on_missing_hooks(self) -> None:
        """Session-resume doc must warn which capture-critical hooks are missing (Req 10.4)."""
        assert "warn" in self.resume_lower, (
            "session-resume-phase2-setup-recovery.md must warn the bootcamper"
        )
        assert ("missing" in self.resume_lower) or ("absent" in self.resume_lower), (
            "session-resume-phase2-setup-recovery.md must state which "
            "capture-critical hooks are missing/absent"
        )

    def test_resume_doc_runs_after_hooks_installed_check(self) -> None:
        """Warn-on-absence must be documented relative to the hooks_installed check (Req 10.4)."""
        assert "hooks_installed" in self.resume, (
            "session-resume-phase2-setup-recovery.md must anchor the check to "
            "the hooks_installed check"
        )

    def test_resume_doc_lists_all_capture_critical_hooks(self) -> None:
        """Warn-on-absence section must name all three capture-critical hooks (Req 10.4)."""
        for hook_id in _CAPTURE_CRITICAL:
            assert hook_id in self.resume, (
                f"session-resume-phase2-setup-recovery.md must name "
                f"capture-critical hook '{hook_id}'"
            )

    def test_resume_doc_documents_install_options(self) -> None:
        """Warn-on-absence doc must explain how to install missing hooks (Req 10.4)."""
        mentions_installer = "install_hooks.py" in self.resume
        mentions_createhook = "createhook" in self.resume_lower
        assert mentions_installer or mentions_createhook, (
            "session-resume-phase2-setup-recovery.md must document how to "
            "install missing capture-critical hooks (createHook from registry "
            "or install_hooks.py --essential)"
        )

    def test_warn_on_absence_is_advisory(self) -> None:
        """The warn-on-absence behavior must be documented as advisory/non-blocking (Req 10.4)."""
        assert ("advisory" in self.resume_lower) or (
            "never block" in self.resume_lower or "not block" in self.resume_lower
        ), (
            "session-resume-phase2-setup-recovery.md must state the "
            "warn-on-absence check is advisory and never blocks the session"
        )
