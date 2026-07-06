"""Property-based tests for the centralized Hypothesis profile registry.

These tests exercise the pure logic of the repo-root ``hypothesis_profiles``
module (``resolve_profile_name`` and ``register_profiles``). They target the
selection logic in isolation from global Hypothesis state, so each property can
run cheaply across many inputs.

Each property test is tagged with a comment referencing its design property in
the format: ``Feature: hypothesis-settings-centralization, Property {number}``.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# Ensure the repo root is importable so ``import hypothesis_profiles`` resolves.
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import hypothesis_profiles


class TestRegisteredNameResolution:
    """Property tests for resolving registered profile names."""

    # Feature: hypothesis-settings-centralization, Property 1: A registered profile name resolves to itself, for both roots  # noqa: E501
    @settings(max_examples=100)
    @given(name=st.sampled_from(hypothesis_profiles.registered_profile_names()))
    def test_registered_name_resolves_to_itself(self, name: str) -> None:
        """A registered profile name resolves to itself.

        Validates: Requirements 3.1, 3.5, 8.4

        Args:
            name: A profile name drawn from the registered set.
        """
        assert hypothesis_profiles.resolve_profile_name(name) == name


class TestUnrecognizedValueError:
    """Property tests for rejecting unrecognized profile values."""

    # Feature: hypothesis-settings-centralization, Property 2: An unrecognized profile value raises an error naming the value  # noqa: E501
    @settings(max_examples=100)
    @given(
        value=st.text().filter(
            lambda s: bool(s) and s not in hypothesis_profiles.registered_profile_names()
        )
    )
    def test_unrecognized_value_raises_error_naming_value(self, value: str) -> None:
        """An unrecognized profile value raises a ValueError naming the value.

        Validates: Requirements 3.3, 8.6

        Args:
            value: A non-empty string that is not a registered profile name.
        """
        with pytest.raises(ValueError) as exc_info:
            hypothesis_profiles.resolve_profile_name(value)
        assert value in str(exc_info.value)


class TestPreservedTimingSettings:
    """Property tests for preserved timing settings across registered profiles."""

    # Feature: hypothesis-settings-centralization, Property 3: Every registered profile preserves the timing settings  # noqa: E501
    @settings(max_examples=100)
    @given(name=st.sampled_from(hypothesis_profiles.registered_profile_names()))
    def test_registered_profile_preserves_timing_settings(self, name: str) -> None:
        """Every registered profile has ``deadline=None`` and suppresses ``too_slow``.

        Validates: Requirements 1.1, 1.6

        Args:
            name: A profile name drawn from the registered set.
        """
        hypothesis_profiles.register_profiles()
        profile = settings.get_profile(name)
        assert profile.deadline is None
        assert HealthCheck.too_slow in profile.suppress_health_check


class TestIdempotentRegistration:
    """Property tests for idempotent profile registration."""

    # Feature: hypothesis-settings-centralization, Property 4: Profile registration is idempotent
    @settings(max_examples=100)
    @given(count=st.integers(min_value=1, max_value=10))
    def test_register_profiles_is_idempotent(self, count: int) -> None:
        """Repeated registration never raises and yields identical settings.

        Captures a baseline by registering once and recording each profile's key
        settings, then re-registers ``count`` more times and asserts the
        registered names and per-profile settings are unchanged.

        Validates: Requirements 2.4

        Args:
            count: The number of additional registration calls to make.
        """

        def snapshot() -> dict[str, tuple[int, object, frozenset[HealthCheck]]]:
            """Capture key settings for every registered profile.

            Returns:
                A mapping of profile name to its ``(max_examples, deadline,
                suppress_health_check)`` tuple.
            """
            return {
                name: (
                    settings.get_profile(name).max_examples,
                    settings.get_profile(name).deadline,
                    frozenset(settings.get_profile(name).suppress_health_check),
                )
                for name in hypothesis_profiles.registered_profile_names()
            }

        hypothesis_profiles.register_profiles()
        baseline_names = hypothesis_profiles.registered_profile_names()
        baseline = snapshot()

        for _ in range(count):
            hypothesis_profiles.register_profiles()

        assert hypothesis_profiles.registered_profile_names() == baseline_names
        assert snapshot() == baseline


class TestProfileCountsAndSelection:
    """Example-based tests for profile counts, defaults, and single-load.

    These are example/unit (non-property) tests verifying the fixed
    configuration values, the default and single-load selection behavior, and
    the module's dependency policy.
    """

    def test_fast_and_thorough_are_registered(self) -> None:
        """``fast`` and ``thorough`` are both registered profile names.

        Validates: Requirements 1.1, 8.1
        """
        names = hypothesis_profiles.registered_profile_names()
        assert hypothesis_profiles.FAST in names
        assert hypothesis_profiles.THOROUGH in names

    def test_fast_profile_max_examples_matches_constant(self) -> None:
        """The ``fast`` profile sets ``max_examples == FAST_MAX_EXAMPLES`` (5).

        Validates: Requirements 1.2, 8.1
        """
        hypothesis_profiles.register_profiles()
        assert (
            settings.get_profile(hypothesis_profiles.FAST).max_examples
            == hypothesis_profiles.FAST_MAX_EXAMPLES
            == 5
        )

    def test_thorough_profile_max_examples_is_hundred(self) -> None:
        """The ``thorough`` profile sets ``max_examples == 100``.

        Validates: Requirements 1.3, 8.1
        """
        hypothesis_profiles.register_profiles()
        assert settings.get_profile(hypothesis_profiles.THOROUGH).max_examples == 100

    def test_thorough_meets_or_exceeds_baseline(self) -> None:
        """The ``thorough`` ``max_examples`` is at least the baseline (20).

        Validates: Requirements 1.4, 8.2
        """
        assert (
            hypothesis_profiles.THOROUGH_MAX_EXAMPLES
            >= hypothesis_profiles.BASELINE_EXAMPLE_COUNT
        )
        expected_baseline = 20
        assert hypothesis_profiles.BASELINE_EXAMPLE_COUNT == expected_baseline

    def test_fast_is_less_than_thorough(self) -> None:
        """The ``fast`` ``max_examples`` is strictly less than ``thorough``.

        Validates: Requirements 1.5, 8.3
        """
        assert (
            hypothesis_profiles.FAST_MAX_EXAMPLES
            < hypothesis_profiles.THOROUGH_MAX_EXAMPLES
        )

    def test_resolve_none_returns_default_fast(self) -> None:
        """``resolve_profile_name(None)`` returns the default ``fast`` profile.

        Validates: Requirements 3.2, 8.5
        """
        assert hypothesis_profiles.resolve_profile_name(None) == hypothesis_profiles.FAST
        assert hypothesis_profiles.DEFAULT_PROFILE == hypothesis_profiles.FAST

    def test_resolve_empty_string_returns_default_fast(self) -> None:
        """``resolve_profile_name("")`` returns the default ``fast`` profile.

        Validates: Requirements 3.2, 8.5
        """
        assert hypothesis_profiles.resolve_profile_name("") == hypothesis_profiles.FAST

    def test_load_active_profile_returns_explicit_thorough(self) -> None:
        """``load_active_profile("thorough")`` returns ``"thorough"`` (single load).

        Validates: Requirements 3.4, 8.5
        """
        assert hypothesis_profiles.load_active_profile("thorough") == "thorough"

    def test_load_active_profile_returns_explicit_fast(self) -> None:
        """``load_active_profile("fast")`` returns ``"fast"`` (single load).

        Validates: Requirements 3.4, 8.5
        """
        assert hypothesis_profiles.load_active_profile("fast") == "fast"

    def test_load_active_profile_defaults_to_fast_when_env_unset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``load_active_profile(None)`` resolves to ``fast`` when env is unset.

        Validates: Requirements 3.2, 3.4, 8.5

        Args:
            monkeypatch: pytest fixture used to remove the env var.
        """
        monkeypatch.delenv(hypothesis_profiles.ENV_VAR, raising=False)
        assert hypothesis_profiles.load_active_profile(None) == hypothesis_profiles.FAST

    def test_module_imports_only_stdlib_plus_hypothesis(self) -> None:
        """The module imports only stdlib plus ``hypothesis``.

        Parses the module source with ``ast``, collects the root names of every
        top-level import, and asserts they are a subset of the allowed set
        (stdlib module roots plus ``hypothesis``).

        Validates: Requirements 6.4
        """
        source = Path(hypothesis_profiles.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module is not None:
                    imported_roots.add(node.module.split(".")[0])

        allowed = set(sys.stdlib_module_names) | {"hypothesis"}
        unexpected = imported_roots - allowed
        assert unexpected == set(), f"Unexpected non-stdlib imports: {unexpected}"
        # The only non-stdlib import allowed is ``hypothesis``.
        non_stdlib = imported_roots - set(sys.stdlib_module_names)
        assert non_stdlib <= {"hypothesis"}
