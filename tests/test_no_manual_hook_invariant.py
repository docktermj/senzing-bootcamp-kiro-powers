"""Property-based test for the no-manual-hook invariant (Kiro 1.0 migration).

Feature: kiro-1-0-migration, Property 10: No shipped hook is manual

This test validates the *real* shipped v1 hook files under
``senzing-bootcamp/hooks/*.json`` together with the install sets the installer
derives from them. Per ``structure.md`` ("Hook tests validating real hook files
go in repo-root ``tests/``"), a test that reads the real shipped hook files
lives here in the repo-root ``tests/`` directory rather than in
``senzing-bootcamp/tests/``.

The installer module under test lives in ``senzing-bootcamp/scripts`` (not a
package), so it is imported via a ``sys.path`` insert. Its
``DEFAULT_POWER_HOOKS`` / ``DEFAULT_CATEGORIES`` constants resolve relative to
the *script* location, so both hook discovery and the critical-set derivation
work regardless of the process cwd (the repo-root ``conftest.py`` also snaps cwd
back to the project root before each test).

Property 10 has two conjuncts, both asserted here:

1. For any shipped v1 hook file, ``hooks[0].trigger`` is a valid Kiro 1.0
   Trigger and is never the removed manual trigger ``userTriggered``.
2. None of the three Manual_Hook identifiers
   (``backup-project-on-request``, ``git-commit-reminder``,
   ``commonmark-validation``) appears in any shipped install set
   (``ESSENTIAL``, ``CAPTURE_CRITICAL``, the critical set from
   ``load_critical_hooks()``, or the ``discover_hooks`` install-all set).

**Validates: Requirements 4.4, 9.4**
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Import the installer and the canonical rename tables from
# senzing-bootcamp/scripts via the established sys.path pattern (scripts are
# not packages).
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import hook_renames as renames  # noqa: E402
import install_hooks  # noqa: E402

# ---------------------------------------------------------------------------
# Constants — the REAL shipped hooks dir, resolved relative to this test file
# (absolute, so it is independent of the process cwd).
# ---------------------------------------------------------------------------

REAL_HOOKS_DIR: Path = (
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "hooks"
)

#: The legacy manual trigger removed by Kiro 1.0 — must never appear in a
#: shipped v1 hook file.
MANUAL_TRIGGER: str = "userTriggered"


# ---------------------------------------------------------------------------
# Helpers computed against the real shipped set / installer
# ---------------------------------------------------------------------------


def _shipped_hook_filenames() -> list[str]:
    """Return the sorted shipped v1 hook filenames (``*.json``)."""
    return sorted(p.name for p in REAL_HOOKS_DIR.glob("*.json"))


def _read_first_trigger(hook_file: Path) -> str | None:
    """Return ``hooks[0].trigger`` from a v1 hook file, or None if unreadable.

    Args:
        hook_file: Path to a ``*.json`` v1 hook file.

    Returns:
        The first hook entry's ``trigger`` string, or None when the file cannot
        be parsed as a v1 wrapper with a non-empty ``hooks`` array whose first
        entry is an object.
    """
    try:
        data = json.loads(hook_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    hooks = data.get("hooks")
    if not isinstance(hooks, list) or not hooks:
        return None
    first = hooks[0]
    if not isinstance(first, dict):
        return None
    trigger = first.get("trigger")
    return trigger if isinstance(trigger, str) else None


def _discovered_ids() -> set[str]:
    """Return the installer's install-all set of hook ids from the real dir."""
    return {
        install_hooks._hook_id(filename)
        for filename, _, _ in install_hooks.discover_hooks(REAL_HOOKS_DIR)
    }


def _install_sets() -> dict[str, set[str]]:
    """Return every shipped install set keyed by a human-readable name.

    The four install sets Property 10 ranges over are the two module-level sets
    (``ESSENTIAL`` and ``CAPTURE_CRITICAL``), the critical set derived from
    ``hook-categories.yaml`` via ``load_critical_hooks()``, and the install-all
    set discovered from the real hooks directory.
    """
    return {
        "ESSENTIAL": set(install_hooks.ESSENTIAL),
        "CAPTURE_CRITICAL": set(install_hooks.CAPTURE_CRITICAL),
        "critical (load_critical_hooks)": set(install_hooks.load_critical_hooks()),
        "discovered (install-all)": _discovered_ids(),
    }


# ---------------------------------------------------------------------------
# Finite domains for the sampling strategies (computed once at import; the
# shipped set is a small finite corpus, so Hypothesis samples over it).
# ---------------------------------------------------------------------------

_SHIPPED_HOOK_FILENAMES: list[str] = _shipped_hook_filenames()
_MANUAL_HOOK_IDS: list[str] = sorted(install_hooks.MANUAL_HOOK_IDS)
_INSTALL_SET_MEMBERS: list[tuple[str, str]] = [
    (set_name, hook_id)
    for set_name, members in _install_sets().items()
    for hook_id in sorted(members)
]


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_-prefixed per python-conventions)
# ---------------------------------------------------------------------------


def st_shipped_hook_filename() -> st.SearchStrategy[str]:
    """Sample a shipped v1 hook filename (``<id>.json``) from the real dir."""
    return st.sampled_from(_SHIPPED_HOOK_FILENAMES)


def st_manual_hook_id() -> st.SearchStrategy[str]:
    """Sample one of the three removed Manual_Hook identifiers."""
    return st.sampled_from(_MANUAL_HOOK_IDS)


def st_install_set_member() -> st.SearchStrategy[tuple[str, str]]:
    """Sample a ``(set_name, hook_id)`` pair drawn from any install set."""
    return st.sampled_from(_INSTALL_SET_MEMBERS)


# ---------------------------------------------------------------------------
# Property 10: No shipped hook is manual
# ---------------------------------------------------------------------------


class TestNoShippedHookIsManual:
    """For any shipped v1 hook and any install set, nothing is manual.

    Property 10: For any shipped V1_Hook file, its trigger is a valid Kiro 1.0
    Trigger and never the removed ``userTriggered`` manual trigger; and none of
    the three Manual_Hook identifiers appears in any shipped install set.

    **Validates: Requirements 4.4, 9.4**
    """

    # -- Conjunct 1: shipped hook triggers are valid 1.0 and never manual -----

    # Feature: kiro-1-0-migration, Property 10: No shipped hook is manual
    @given(filename=st_shipped_hook_filename())
    def test_sampled_shipped_hook_trigger_is_valid_and_not_manual(
        self, filename: str
    ) -> None:
        """A sampled shipped hook's trigger is a valid 1.0 trigger, not manual."""
        trigger = _read_first_trigger(REAL_HOOKS_DIR / filename)
        assert trigger is not None, (
            f"Shipped hook '{filename}' has no readable hooks[0].trigger"
        )
        assert trigger != MANUAL_TRIGGER, (
            f"Shipped hook '{filename}' uses the removed manual trigger "
            f"'{MANUAL_TRIGGER}'"
        )
        assert trigger in renames.VALID_V1_TRIGGERS, (
            f"Shipped hook '{filename}' trigger '{trigger}' is not a valid "
            f"Kiro 1.0 trigger {sorted(renames.VALID_V1_TRIGGERS)}"
        )

    def test_every_shipped_hook_trigger_is_valid_and_not_manual(self) -> None:
        """Finite check: EVERY shipped v1 hook trigger is valid and not manual."""
        assert _SHIPPED_HOOK_FILENAMES, (
            f"No shipped v1 hook files found under {REAL_HOOKS_DIR}"
        )
        for filename in _SHIPPED_HOOK_FILENAMES:
            trigger = _read_first_trigger(REAL_HOOKS_DIR / filename)
            assert trigger is not None, (
                f"Shipped hook '{filename}' has no readable hooks[0].trigger"
            )
            assert trigger != MANUAL_TRIGGER, (
                f"Shipped hook '{filename}' uses the removed manual trigger "
                f"'{MANUAL_TRIGGER}'"
            )
            assert trigger in renames.VALID_V1_TRIGGERS, (
                f"Shipped hook '{filename}' trigger '{trigger}' is not a valid "
                f"Kiro 1.0 trigger"
            )

    # -- Conjunct 2: manual ids appear in no install set ----------------------

    # Feature: kiro-1-0-migration, Property 10: No shipped hook is manual
    @given(member=st_install_set_member())
    def test_sampled_install_set_member_is_never_manual(
        self, member: tuple[str, str]
    ) -> None:
        """A sampled member of any install set is never a Manual_Hook id."""
        set_name, hook_id = member
        assert hook_id not in install_hooks.MANUAL_HOOK_IDS, (
            f"Manual hook id '{hook_id}' leaked into install set '{set_name}'"
        )

    # Feature: kiro-1-0-migration, Property 10: No shipped hook is manual
    @given(manual_id=st_manual_hook_id())
    def test_sampled_manual_id_absent_from_all_install_sets(
        self, manual_id: str
    ) -> None:
        """A sampled Manual_Hook id is absent from every install set."""
        for set_name, members in _install_sets().items():
            assert manual_id not in members, (
                f"Manual hook id '{manual_id}' appears in install set "
                f"'{set_name}'"
            )

    def test_all_manual_ids_absent_from_every_install_set(self) -> None:
        """Finite check: none of the 3 manual ids is in ANY install set."""
        install_sets = _install_sets()
        for set_name, members in install_sets.items():
            for manual_id in install_hooks.MANUAL_HOOK_IDS:
                assert manual_id not in members, (
                    f"Manual hook id '{manual_id}' appears in install set "
                    f"'{set_name}'"
                )

    def test_no_manual_hook_file_is_shipped(self) -> None:
        """Finite check: no ``<manual_id>.json`` file ships in the hooks dir."""
        shipped = set(_SHIPPED_HOOK_FILENAMES)
        for manual_id in install_hooks.MANUAL_HOOK_IDS:
            assert f"{manual_id}.json" not in shipped, (
                f"Manual hook file '{manual_id}.json' is still shipped in "
                f"{REAL_HOOKS_DIR}"
            )
