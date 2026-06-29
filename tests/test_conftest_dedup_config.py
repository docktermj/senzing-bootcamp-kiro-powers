"""Config-scan test: conftest files contain no inline profile registration.

Verifies the de-duplication outcome of the hypothesis-settings-centralization
feature: neither ``conftest.py`` collection root registers a Hypothesis profile
inline. Registration lives exclusively in the repo-root ``hypothesis_profiles``
module, so the two roots can never drift apart.

Validates: Requirements 2.3, 2.5
"""

from __future__ import annotations

from pathlib import Path

# Repo root is two levels up from this file: ``<repo>/tests/<this file>``.
_REPO_ROOT = Path(__file__).resolve().parents[1]

_REGISTER_CALL = "settings.register_profile("


class TestConftestDedupConfig:
    """Scan both conftest files for inline profile registration calls."""

    def test_power_conftest_has_no_inline_registration(self) -> None:
        """Power_Conftest must not call ``settings.register_profile(``."""
        conftest = _REPO_ROOT / "senzing-bootcamp" / "tests" / "conftest.py"
        text = conftest.read_text(encoding="utf-8")
        assert _REGISTER_CALL not in text, (
            f"{conftest} contains an inline {_REGISTER_CALL!r} call; "
            "profile registration must live only in hypothesis_profiles.py"
        )

    def test_repo_conftest_has_no_inline_registration(self) -> None:
        """Repo_Conftest must not call ``settings.register_profile(``."""
        conftest = _REPO_ROOT / "tests" / "conftest.py"
        text = conftest.read_text(encoding="utf-8")
        assert _REGISTER_CALL not in text, (
            f"{conftest} contains an inline {_REGISTER_CALL!r} call; "
            "profile registration must live only in hypothesis_profiles.py"
        )

    def test_registration_lives_in_hypothesis_profiles(self) -> None:
        """The repo-root ``hypothesis_profiles.py`` owns ``register_profile(``."""
        registry = _REPO_ROOT / "hypothesis_profiles.py"
        text = registry.read_text(encoding="utf-8")
        assert "register_profile(" in text, (
            f"{registry} should register profiles via register_profile(); "
            "registration is centralized here"
        )
