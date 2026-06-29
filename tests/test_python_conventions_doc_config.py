"""Config-scan test: python-conventions.md documents the profile approach.

Verifies the documentation-reconciliation outcome of the
hypothesis-settings-centralization feature: the Python conventions steering
file (``.kiro/steering/python-conventions.md``) documents the registered
profile names, the selection environment variable, the default profile, and
the inline ``@settings`` override semantics.

Assertions read the markdown as text and check for the required substrings
(case-insensitive where reasonable) so they remain robust to minor prose and
formatting changes.

Validates: Requirements 7.1, 7.2, 7.3, 7.4
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Repo root is one level up from this file: ``<repo>/tests/<this file>``.
_REPO_ROOT: Path = Path(__file__).resolve().parents[1]

# The steering document under test, resolved from the repo root.
_DOC_PATH: Path = _REPO_ROOT / ".kiro" / "steering" / "python-conventions.md"


def _read_doc() -> str:
    """Read the Python conventions steering document once.

    Returns:
        The full text of ``python-conventions.md``.
    """
    assert _DOC_PATH.exists(), f"Python conventions doc not found: {_DOC_PATH}"
    return _DOC_PATH.read_text(encoding="utf-8")


# Module-level read: the document is static during a test run.
_DOC: str = _read_doc()
_DOC_LOWER: str = _DOC.lower()


class TestPythonConventionsDocConfig:
    """Validate python-conventions.md documents the centralized profiles.

    **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
    """

    @pytest.fixture(autouse=True)
    def _load_content(self) -> None:
        """Expose document content to every test in this class."""
        self.content: str = _DOC
        self.lower: str = _DOC_LOWER

    # -- Requirement 7.3: registered profile names --------------------------

    def test_documents_profile_names(self) -> None:
        """Doc must name the ``fast``, ``thorough``, and ``bootcamp`` profiles.

        The profile names are lowercase identifiers, so the check is
        case-sensitive to avoid matching unrelated prose (for example, the
        adjective "fast" mid-sentence is acceptable, but the literal tokens
        must appear verbatim).
        """
        for name in ("fast", "thorough", "bootcamp"):
            assert name in self.content, (
                f"python-conventions.md must document the profile name {name!r}"
            )

    def test_documents_bootcamp_as_alias(self) -> None:
        """Doc must describe ``bootcamp`` as an alias (Req 7.3)."""
        assert "alias" in self.lower, (
            "python-conventions.md must describe the bootcamp profile as an alias"
        )

    # -- Requirement 7.2 / 7.3: selection env var ---------------------------

    def test_documents_env_var_name(self) -> None:
        """Doc must name the ``HYPOTHESIS_PROFILE`` selection env var (Req 7.3)."""
        assert "HYPOTHESIS_PROFILE" in self.content, (
            "python-conventions.md must document the HYPOTHESIS_PROFILE env var"
        )

    # -- Requirement 7.3: default profile -----------------------------------

    def test_documents_default_profile(self) -> None:
        """Doc must document that the default profile is ``fast`` (Req 7.3).

        The document must contain both the word "default" and the ``fast``
        profile name so a reader can determine the default selection.
        """
        assert "default" in self.lower, (
            "python-conventions.md must document a default profile"
        )
        assert "fast" in self.content, (
            "python-conventions.md must document that the default profile is fast"
        )

    # -- Requirement 7.1: profile-based baseline + env-var selection --------

    def test_documents_profile_baseline_and_selection(self) -> None:
        """Doc must describe profile-based baselines and env-var selection (Req 7.1)."""
        assert "max_examples" in self.content, (
            "python-conventions.md must describe profile-based max_examples baselines"
        )
        assert "profile" in self.lower, (
            "python-conventions.md must describe the profile-based approach"
        )

    # -- Requirement 7.2 / 7.4: override semantics --------------------------

    def test_documents_override_semantics(self) -> None:
        """Doc must document inline ``@settings`` override semantics (Req 7.2, 7.4).

        The override semantics require the document mention both the
        "override" wording and the ``@settings`` decorator together, so a
        reader understands inline ``@settings`` overrides the profile baseline.
        """
        assert "override" in self.lower, (
            "python-conventions.md must document that inline settings override "
            "the profile baseline"
        )
        assert "@settings" in self.content, (
            "python-conventions.md must reference the inline @settings decorator "
            "when describing override semantics"
        )
