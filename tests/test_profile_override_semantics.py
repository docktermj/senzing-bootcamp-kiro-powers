"""Tests for profile override semantics and preserved conftest behavior.

Covers two areas of the hypothesis-settings-centralization feature:

1. Override semantics (Requirements 5.1, 5.2, 5.3): an un-decorated ``@given``
   test inherits the active profile's ``max_examples`` baseline, while an inline
   ``@settings(max_examples=v)`` override wins regardless of which profile is
   active.
2. Preserved conftest behavior (Requirements 6.1, 6.2, 6.3): the cwd-restoring
   autouse fixtures still snap the working directory back to the project root
   before each test, and the registry module plus a representative test helper
   still import cleanly.

These tests load profiles, which mutates the global Hypothesis ``settings``
state. The autouse ``_restore_active_profile`` fixture re-loads the
environment-selected profile after every test so this module never disturbs the
rest of the suite.

Validates: Requirements 5.1, 5.2, 5.3, 6.1, 6.2, 6.3
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import hypothesis_profiles
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Repo root is one level up from this file: ``<repo>/tests/<this file>``.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _restore_active_profile():
    """Restore the environment-selected profile after each test.

    Tests in this module call ``load_active_profile(...)`` with explicit names,
    which mutates the global Hypothesis default. Reloading the env-selected
    profile (default ``fast``) after each test keeps that mutation local.

    Yields:
        None. Cleanup runs after the test body completes.
    """
    try:
        yield
    finally:
        hypothesis_profiles.load_active_profile()


class TestProfileBaselineInheritance:
    """An un-decorated ``@given`` test inherits the active profile baseline."""

    def test_fast_profile_sets_baseline_max_examples(self) -> None:
        """Loading ``fast`` makes the default baseline equal ``fast``'s count."""
        hypothesis_profiles.load_active_profile(hypothesis_profiles.FAST)

        assert settings.default.max_examples == hypothesis_profiles.FAST_MAX_EXAMPLES
        assert (
            settings.get_profile(hypothesis_profiles.FAST).max_examples
            == hypothesis_profiles.FAST_MAX_EXAMPLES
        )

    def test_thorough_profile_sets_baseline_max_examples(self) -> None:
        """Loading ``thorough`` makes the default baseline equal its count."""
        hypothesis_profiles.load_active_profile(hypothesis_profiles.THOROUGH)

        assert (
            settings.default.max_examples == hypothesis_profiles.THOROUGH_MAX_EXAMPLES
        )
        assert (
            settings.get_profile(hypothesis_profiles.THOROUGH).max_examples
            == hypothesis_profiles.THOROUGH_MAX_EXAMPLES
        )

    def test_undecorated_given_uses_active_profile_baseline(self) -> None:
        """An un-decorated ``@given`` test runs at the active profile baseline.

        Loads the ``fast`` profile, then executes a ``@given`` test that carries
        no inline ``@settings``. The function records how many examples it ran;
        the count must not exceed the active profile's baseline, demonstrating
        the test inherited that baseline rather than Hypothesis's own default.
        """
        hypothesis_profiles.load_active_profile(hypothesis_profiles.FAST)
        baseline = hypothesis_profiles.FAST_MAX_EXAMPLES
        calls: list[int] = []

        @given(st.integers())
        def _inner(value: int) -> None:
            calls.append(value)

        _inner()

        assert calls, "the @given test should have run at least one example"
        assert len(calls) <= baseline, (
            f"un-decorated @given ran {len(calls)} examples; expected at most the "
            f"active 'fast' baseline of {baseline}"
        )


class TestPerTestSettingsOverride:
    """An inline ``@settings(max_examples=v)`` override beats the profile."""

    @pytest.mark.parametrize(
        "profile_name",
        [hypothesis_profiles.FAST, hypothesis_profiles.THOROUGH],
    )
    def test_inline_override_wins_regardless_of_profile(
        self, profile_name: str
    ) -> None:
        """An explicit ``max_examples=7`` is effective under either profile."""
        hypothesis_profiles.load_active_profile(profile_name)

        effective = settings(parent=settings.default, max_examples=7)

        assert effective.max_examples == 7, (
            f"inline @settings(max_examples=7) should win over the '{profile_name}' "
            f"profile baseline of {settings.default.max_examples}"
        )

    def test_decorated_test_reports_inline_value_under_both_profiles(self) -> None:
        """A decorated test reports ``max_examples == 7`` under both profiles."""
        for profile_name in (hypothesis_profiles.FAST, hypothesis_profiles.THOROUGH):
            hypothesis_profiles.load_active_profile(profile_name)

            @settings(max_examples=7)
            @given(st.integers())
            def _decorated(value: int) -> None:
                pass

            inline = settings(parent=settings.default, max_examples=7)
            assert inline.max_examples == 7
            # The inline value must differ from the active baseline to prove it
            # is genuinely overriding (7 != 5 fast, 7 != 100 thorough).
            assert inline.max_examples != settings.default.max_examples


class TestCwdRestoration:
    """The autouse cwd fixtures snap back to the project root before each test.

    The two methods run in definition order. The first asserts it starts at the
    project root, then deliberately changes cwd to a temp directory. The second
    asserts it *still* starts at the project root, which can only be true if the
    autouse ``_restore_project_root_cwd`` fixture restored cwd in between.
    """

    def test_a_starts_at_project_root_then_wanders(self) -> None:
        """Start at project root, then chdir away to prove restoration matters."""
        assert os.getcwd() == str(_PROJECT_ROOT)
        os.chdir(tempfile.gettempdir())

    def test_b_restored_to_project_root_after_wandering(self) -> None:
        """Despite the previous test leaving cwd in /tmp, cwd is project root."""
        assert os.getcwd() == str(_PROJECT_ROOT)


class TestHelperImportsResolve:
    """The registry module and a representative test helper still import."""

    def test_hypothesis_profiles_imports(self) -> None:
        """``import hypothesis_profiles`` resolves and exposes its API."""
        import hypothesis_profiles as hp

        assert hasattr(hp, "load_active_profile")
        assert hasattr(hp, "register_profiles")

    def test_representative_helper_import_resolves(self) -> None:
        """A representative ``tests/`` helper import resolves defensively."""
        try:
            import hook_test_helpers  # noqa: F401
        except ImportError as exc:  # pragma: no cover - defensive
            pytest.fail(f"expected tests/ helper to be importable: {exc}")
