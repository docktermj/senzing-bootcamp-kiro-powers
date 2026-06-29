"""Centralized Hypothesis profile registry for the senzing-bootcamp test suite.

This module is the single source of truth for the project's Hypothesis profiles.
It registers a small hierarchy of named profiles and selects the active one from
the ``HYPOTHESIS_PROFILE`` environment variable. Both ``conftest.py`` collection
roots (``senzing-bootcamp/tests/`` and ``tests/``) import this module and call
:func:`load_active_profile`, so the two roots never drift apart.

Profiles:
    fast      max_examples=10  -- local default for quick iteration
    thorough  max_examples=100 -- CI / full local run (== Hypothesis default)
    bootcamp  alias of thorough -- backward-compatible legacy name

Every profile sets ``deadline=None`` and suppresses the ``too_slow`` health
check, preserving the timing behavior of the previously duplicated inline
profiles.

This module imports only the standard library (``os``) plus ``hypothesis``.
"""

from __future__ import annotations

import os

from hypothesis import HealthCheck, settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FAST: str = "fast"
THOROUGH: str = "thorough"
LEGACY_ALIAS: str = "bootcamp"  # registered as an alias of THOROUGH
DEFAULT_PROFILE: str = FAST
ENV_VAR: str = "HYPOTHESIS_PROFILE"

BASELINE_EXAMPLE_COUNT: int = 20  # documented convention value
FAST_MAX_EXAMPLES: int = 10
THOROUGH_MAX_EXAMPLES: int = 100  # == Hypothesis default; never weakens CI


def register_profiles() -> None:
    """Register every profile (fast, thorough, bootcamp alias).

    Registers the ``fast`` profile (``max_examples=10``), the ``thorough``
    profile (``max_examples=100``), and the ``bootcamp`` alias which shares the
    thorough settings. Every profile sets ``deadline=None`` and suppresses the
    ``too_slow`` health check, preserving today's timing behavior.

    Idempotent: safe to call multiple times within one test-suite run. Later
    calls overwrite the registration with identical settings and never raise,
    so two conftests (or any re-import) registering the same profiles never
    collide.

    Returns:
        None.
    """
    settings.register_profile(
        FAST,
        max_examples=FAST_MAX_EXAMPLES,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    settings.register_profile(
        THOROUGH,
        max_examples=THOROUGH_MAX_EXAMPLES,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    settings.register_profile(
        LEGACY_ALIAS,
        max_examples=THOROUGH_MAX_EXAMPLES,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )


def registered_profile_names() -> tuple[str, ...]:
    """Return the profile names this module registers.

    Returns:
        A tuple of the registered profile names: ``fast``, ``thorough``, and
        the ``bootcamp`` alias. Useful for tests and validation.
    """
    return (FAST, THOROUGH, LEGACY_ALIAS)


def resolve_profile_name(env_value: str | None) -> str:
    """Map an environment-variable value to a registered profile name.

    This is a pure function: it performs no I/O and mutates no global state, so
    the selection logic can be property-tested in isolation and yields the same
    result for both collection roots given the same input.

    Args:
        env_value: The raw ``HYPOTHESIS_PROFILE`` value, or None when unset.

    Returns:
        ``DEFAULT_PROFILE`` when ``env_value`` is None or empty; otherwise the
        value unchanged when it names a registered profile.

    Raises:
        ValueError: When ``env_value`` is a non-empty string that does not name
            a registered profile. The message contains the offending value and
            the list of valid names.
    """
    if not env_value:
        return DEFAULT_PROFILE
    valid_names = registered_profile_names()
    if env_value in valid_names:
        return env_value
    raise ValueError(
        f"Unknown Hypothesis profile {env_value!r} ({env_value}); "
        f"valid profiles are: {', '.join(valid_names)}"
    )


def load_active_profile(env_value: str | None = None) -> str:
    """Register all profiles, resolve the active name, load it, and return it.

    Reads ``os.environ[ENV_VAR]`` when ``env_value`` is None. Registers every
    profile (idempotent), resolves the active profile name, and loads exactly
    one profile per call.

    Args:
        env_value: An explicit profile value. When None, the value is read from
            the ``HYPOTHESIS_PROFILE`` environment variable.

    Returns:
        The name of the profile that was loaded.

    Raises:
        ValueError: When the resolved value does not name a registered profile.
    """
    if env_value is None:
        env_value = os.environ.get(ENV_VAR)
    register_profiles()
    active_name = resolve_profile_name(env_value)
    settings.load_profile(active_name)
    return active_name
