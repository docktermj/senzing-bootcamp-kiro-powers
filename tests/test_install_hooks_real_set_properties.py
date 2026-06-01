"""Property-based tests for ``install_hooks.py`` against the REAL hooks dir.

These tests validate the repaired hook installer's curated metadata, essential
set, and discovery logic against the actual ``*.kiro.hook`` files shipped in
``senzing-bootcamp/hooks``. Per ``structure.md``, tests that read the real hook
files live in the repo-root ``tests/`` directory.

Properties (from the hook-architecture-improvements design):

- **Property 10:** No consolidated hook is referenced by the installer.
  **Validates: Requirements 9.1, 12.2**
- **Property 11:** Installer display names match each hook's ``name`` field
  (the "to {verb phrase}" pattern). **Validates: Requirements 9.4**
- **Property 12:** Capture-critical hooks are in both install sets
  (all + essential). **Validates: Requirements 10.3, 12.3**
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Import install_hooks from senzing-bootcamp/scripts via the sys.path pattern.
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "scripts"
)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import install_hooks  # noqa: E402

# ---------------------------------------------------------------------------
# Constants — the REAL hooks dir resolved relative to this test file.
# ---------------------------------------------------------------------------

REAL_HOOKS_DIR: Path = (
    Path(__file__).resolve().parent.parent / "senzing-bootcamp" / "hooks"
)

# The three consolidated hooks merged into write-policy-gate (no longer files).
CONSOLIDATED_HOOKS: list[str] = [
    "enforce-file-path-policies",
    "enforce-single-question",
    "block-direct-sql",
]

# Capture-critical hooks that must be covered on both install paths.
CAPTURE_CRITICAL_HOOKS: list[str] = [
    "session-log-events",
    "module-recap-append",
    "ask-bootcamper",
]

# "to {verb phrase}" pattern: starts with "to " followed by a non-space token.
TO_VERB_PHRASE: re.Pattern[str] = re.compile(r"^to \S")


# ---------------------------------------------------------------------------
# Helpers (computed against the real hooks dir).
# ---------------------------------------------------------------------------


def _discovered() -> list[tuple[str, str, str]]:
    """Return ``discover_hooks`` output for the real hooks directory."""
    return install_hooks.discover_hooks(REAL_HOOKS_DIR)


def _discovered_ids() -> set[str]:
    """Return the set of discovered hook ids (filename without suffix)."""
    return {install_hooks._hook_id(fn) for fn, _, _ in _discovered()}


def _real_hook_filenames() -> list[str]:
    """Return the sorted list of real ``*.kiro.hook`` filenames."""
    return sorted(p.name for p in REAL_HOOKS_DIR.glob("*.kiro.hook"))


# ---------------------------------------------------------------------------
# Hypothesis strategies (st_-prefixed).
# ---------------------------------------------------------------------------


def st_consolidated_hook() -> st.SearchStrategy[str]:
    """Strategy sampling a consolidated (removed) hook id."""
    return st.sampled_from(CONSOLIDATED_HOOKS)


def st_real_hook_filename() -> st.SearchStrategy[str]:
    """Strategy sampling a real ``*.kiro.hook`` filename from the hooks dir."""
    return st.sampled_from(_real_hook_filenames())


def st_capture_critical_hook() -> st.SearchStrategy[str]:
    """Strategy sampling a capture-critical hook id."""
    return st.sampled_from(CAPTURE_CRITICAL_HOOKS)


# ---------------------------------------------------------------------------
# Property 10: No consolidated hook is referenced by the installer
# ---------------------------------------------------------------------------


class TestNoConsolidatedHookReferenced:
    """For any consolidated hook id, the installer references it nowhere.

    **Validates: Requirements 9.1, 12.2**

    Property 10: For any consolidated hook id in
    {enforce-file-path-policies, enforce-single-question, block-direct-sql},
    that id appears in neither the installer's curated metadata keys, its
    ``ESSENTIAL`` set, nor the set discovered from the real hooks directory.
    """

    # Feature: hook-architecture-improvements, Property 10
    @given(hook_id=st_consolidated_hook())
    @settings(max_examples=20)
    def test_consolidated_hook_not_in_metadata(self, hook_id: str):
        """A consolidated hook appears in no HOOK_METADATA key (id or filename)."""
        keys = set(install_hooks.HOOK_METADATA.keys())
        assert hook_id not in keys, (
            f"Consolidated hook '{hook_id}' is a HOOK_METADATA key"
        )
        assert f"{hook_id}.kiro.hook" not in keys, (
            f"Consolidated hook file '{hook_id}.kiro.hook' is a HOOK_METADATA key"
        )

    # Feature: hook-architecture-improvements, Property 10
    @given(hook_id=st_consolidated_hook())
    @settings(max_examples=20)
    def test_consolidated_hook_not_in_essential(self, hook_id: str):
        """A consolidated hook is not a member of the ESSENTIAL set."""
        assert hook_id not in install_hooks.ESSENTIAL, (
            f"Consolidated hook '{hook_id}' is in ESSENTIAL"
        )

    # Feature: hook-architecture-improvements, Property 10
    @given(hook_id=st_consolidated_hook())
    @settings(max_examples=20)
    def test_consolidated_hook_not_discovered(self, hook_id: str):
        """A consolidated hook is not discovered from the real hooks dir."""
        discovered_ids = _discovered_ids()
        assert hook_id not in discovered_ids, (
            f"Consolidated hook '{hook_id}' was discovered from {REAL_HOOKS_DIR}"
        )


# ---------------------------------------------------------------------------
# Property 11: Installer display names match each hook's `name` field
# ---------------------------------------------------------------------------


class TestDisplayNamesMatchHookNameField:
    """For any real hook, the installer's display name equals its ``name`` field.

    **Validates: Requirements 9.4**

    Property 11: For any ``*.kiro.hook`` file, the installer's resolved display
    name for that hook equals the file's ``name`` field, which follows the
    "to {verb phrase}" pattern.
    """

    # Feature: hook-architecture-improvements, Property 11
    @given(filename=st_real_hook_filename())
    @settings(max_examples=20)
    def test_display_name_equals_name_field(self, filename: str):
        """discover_hooks display name equals the hook file's ``name`` field."""
        discovered = {fn: name for fn, name, _ in _discovered()}
        assert filename in discovered, (
            f"Real hook '{filename}' was not discovered from {REAL_HOOKS_DIR}"
        )
        expected = install_hooks._read_hook_name(REAL_HOOKS_DIR / filename)
        assert expected is not None, (
            f"Real hook '{filename}' has no readable 'name' field"
        )
        assert discovered[filename] == expected, (
            f"Display name for '{filename}' was '{discovered[filename]}', "
            f"expected the hook's name field '{expected}'"
        )

    # Feature: hook-architecture-improvements, Property 11
    @given(filename=st_real_hook_filename())
    @settings(max_examples=20)
    def test_display_name_follows_to_verb_phrase_pattern(self, filename: str):
        """The resolved display name follows the "to {verb phrase}" pattern."""
        discovered = {fn: name for fn, name, _ in _discovered()}
        name = discovered[filename]
        assert TO_VERB_PHRASE.match(name), (
            f"Display name for '{filename}' was '{name}', which does not "
            f"follow the 'to {{verb phrase}}' pattern"
        )


# ---------------------------------------------------------------------------
# Property 12: Capture-critical hooks are in both install sets
# ---------------------------------------------------------------------------


class TestCaptureCriticalInBothInstallSets:
    """For any capture-critical hook, it is in both the all and essential sets.

    **Validates: Requirements 10.3, 12.3**

    Property 12: For any capture-critical hook in
    {session-log-events, module-recap-append, ask-bootcamper}, that hook is a
    member of both the installer's install-all set (the discovered set from the
    real hooks dir) and its essential set (``ESSENTIAL``).
    """

    # Feature: hook-architecture-improvements, Property 12
    @given(hook_id=st_capture_critical_hook())
    @settings(max_examples=20)
    def test_capture_critical_in_all_set(self, hook_id: str):
        """Every capture-critical hook is in the discovered (install-all) set."""
        discovered_ids = _discovered_ids()
        assert hook_id in discovered_ids, (
            f"Capture-critical hook '{hook_id}' is missing from the install-all "
            f"set discovered from {REAL_HOOKS_DIR}"
        )

    # Feature: hook-architecture-improvements, Property 12
    @given(hook_id=st_capture_critical_hook())
    @settings(max_examples=20)
    def test_capture_critical_in_essential_set(self, hook_id: str):
        """Every capture-critical hook is in the ESSENTIAL (essential) set."""
        assert hook_id in install_hooks.ESSENTIAL, (
            f"Capture-critical hook '{hook_id}' is missing from ESSENTIAL"
        )
