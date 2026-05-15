"""Tests for senzing-bootcamp/scripts/install_hooks.py."""

import importlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_install_hooks():
    """Import / reload install_hooks module."""
    import install_hooks
    importlib.reload(install_hooks)
    return install_hooks


# ---------------------------------------------------------------------------
# Example-based tests  (Task 9.1)
# ---------------------------------------------------------------------------


class TestDiscoverHooks:
    """Requirement 9.1 — discover_hooks returns entries for each hook file."""

    def test_discovers_known_hooks(self, project_root):
        power_dir = project_root / "hooks"
        power_dir.mkdir()
        # Create a known hook file
        (power_dir / "code-style-check.kiro.hook").write_text("hook", encoding="utf-8")
        (power_dir / "backup-before-load.kiro.hook").write_text("hook", encoding="utf-8")

        mod = _load_install_hooks()
        result = mod.discover_hooks(power_dir)

        filenames = [entry[0] for entry in result]
        assert "code-style-check.kiro.hook" in filenames
        assert "backup-before-load.kiro.hook" in filenames
        assert len(result) == 2

    def test_discovers_unknown_hooks(self, project_root):
        power_dir = project_root / "hooks"
        power_dir.mkdir()
        (power_dir / "my-custom-hook.kiro.hook").write_text("hook", encoding="utf-8")

        mod = _load_install_hooks()
        result = mod.discover_hooks(power_dir)

        assert len(result) == 1
        filename, name, desc = result[0]
        assert filename == "my-custom-hook.kiro.hook"
        assert name == "My Custom Hook"
        assert "no description" in desc.lower() or "add to HOOKS" in desc


class TestInstallHooks:
    """Requirement 9.3, 9.4, 9.5 — install_hooks copies/skips correctly."""

    def test_installs_new_hooks(self, project_root, capsys):
        power_dir = project_root / "power_hooks"
        power_dir.mkdir()
        user_dir = project_root / "user_hooks"
        user_dir.mkdir()

        (power_dir / "hook-a.kiro.hook").write_text("content-a", encoding="utf-8")
        (power_dir / "hook-b.kiro.hook").write_text("content-b", encoding="utf-8")

        hooks_to_install = [
            ("hook-a.kiro.hook", "Hook A", "desc a"),
            ("hook-b.kiro.hook", "Hook B", "desc b"),
        ]

        mod = _load_install_hooks()
        installed, skipped = mod.install_hooks(hooks_to_install, power_dir, user_dir)

        assert installed == 2
        assert skipped == 0
        assert (user_dir / "hook-a.kiro.hook").exists()
        assert (user_dir / "hook-b.kiro.hook").exists()

    def test_skips_existing_hooks(self, project_root, capsys):
        power_dir = project_root / "power_hooks"
        power_dir.mkdir()
        user_dir = project_root / "user_hooks"
        user_dir.mkdir()

        (power_dir / "hook-a.kiro.hook").write_text("content-a", encoding="utf-8")
        # Pre-install hook-a
        (user_dir / "hook-a.kiro.hook").write_text("already-here", encoding="utf-8")

        hooks_to_install = [
            ("hook-a.kiro.hook", "Hook A", "desc a"),
        ]

        mod = _load_install_hooks()
        installed, skipped = mod.install_hooks(hooks_to_install, power_dir, user_dir)

        assert installed == 0
        assert skipped == 1
        # Content should NOT be overwritten
        assert (user_dir / "hook-a.kiro.hook").read_text(encoding="utf-8") == "already-here"

    def test_mixed_install_and_skip(self, project_root, capsys):
        power_dir = project_root / "power_hooks"
        power_dir.mkdir()
        user_dir = project_root / "user_hooks"
        user_dir.mkdir()

        (power_dir / "hook-a.kiro.hook").write_text("a", encoding="utf-8")
        (power_dir / "hook-b.kiro.hook").write_text("b", encoding="utf-8")
        # Pre-install hook-a only
        (user_dir / "hook-a.kiro.hook").write_text("existing", encoding="utf-8")

        hooks_to_install = [
            ("hook-a.kiro.hook", "Hook A", "desc a"),
            ("hook-b.kiro.hook", "Hook B", "desc b"),
        ]

        mod = _load_install_hooks()
        installed, skipped = mod.install_hooks(hooks_to_install, power_dir, user_dir)

        assert installed == 1
        assert skipped == 1



# ---------------------------------------------------------------------------
# Property-based tests  (Tasks 9.2, 9.3, 9.4)
# ---------------------------------------------------------------------------

from hypothesis import given, settings, assume
import hypothesis.strategies as st

# Strategy: generate valid hook filenames
hook_name_parts = st.from_regex(r"[a-z][a-z0-9]{1,8}", fullmatch=True)
hook_filenames = st.lists(
    st.builds(
        lambda parts: "-".join(parts) + ".kiro.hook",
        st.lists(hook_name_parts, min_size=1, max_size=3),
    ),
    min_size=1,
    max_size=8,
    unique=True,
)


class TestProperty10HookDiscoveryCompleteness:
    """Property 10: Hook discovery completeness.

    **Validates: Requirements 9.1**

    For any set of .kiro.hook files, discover_hooks returns
    one entry per file.
    """

    # Feature: script-test-suite, Property 10: Hook discovery completeness

    @given(filenames=hook_filenames)
    @settings(max_examples=10)
    def test_one_entry_per_hook_file(self, filenames):
        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "hooks"
            power_dir.mkdir()
            for fname in filenames:
                (power_dir / fname).write_text("hook content", encoding="utf-8")

            mod = _load_install_hooks()
            result = mod.discover_hooks(power_dir)

            result_filenames = {entry[0] for entry in result}
            assert result_filenames == set(filenames), (
                f"Expected {set(filenames)}, got {result_filenames}"
            )
            assert len(result) == len(filenames)
        finally:
            shutil.rmtree(td, ignore_errors=True)


# Strategy: generate hook filenames NOT in the known HOOKS list
def _known_hook_filenames():
    mod = _load_install_hooks()
    return {filename for filename, _, _ in mod.HOOKS}


unknown_hook_filenames = st.builds(
    lambda parts: "-".join(parts) + ".kiro.hook",
    st.lists(hook_name_parts, min_size=1, max_size=3),
).filter(lambda f: f not in _known_hook_filenames())


class TestProperty11UnknownHookNameDerivation:
    """Property 11: Unknown hook name derivation.

    **Validates: Requirements 9.2**

    For any filename not in HOOKS, display name is derived by
    removing suffix, replacing hyphens, title-casing.
    """

    # Feature: script-test-suite, Property 11: Unknown hook name derivation

    @given(filename=unknown_hook_filenames)
    @settings(max_examples=10)
    def test_derived_name_matches_convention(self, filename):
        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "hooks"
            power_dir.mkdir()
            (power_dir / filename).write_text("hook", encoding="utf-8")

            mod = _load_install_hooks()
            result = mod.discover_hooks(power_dir)

            assert len(result) == 1
            _, name, desc = result[0]

            # Expected: remove .kiro.hook, replace hyphens with spaces, title-case
            expected_name = filename.replace(".kiro.hook", "").replace("-", " ").title()
            assert name == expected_name, (
                f"For '{filename}': expected '{expected_name}', got '{name}'"
            )
        finally:
            shutil.rmtree(td, ignore_errors=True)


class TestProperty12HookInstallCopySkipCorrectness:
    """Property 12: Hook install copy/skip correctness.

    **Validates: Requirements 9.3, 9.4, 9.5**

    For any mix of new and existing hooks,
    installed + skipped = total with valid sources.
    """

    # Feature: script-test-suite, Property 12: Hook install copy/skip correctness

    @given(
        filenames=hook_filenames,
        pre_installed_mask=st.lists(st.booleans(), min_size=1, max_size=8),
    )
    @settings(max_examples=10)
    def test_installed_plus_skipped_equals_total(self, filenames, pre_installed_mask):
        # Align mask length with filenames
        mask = pre_installed_mask[:len(filenames)]
        while len(mask) < len(filenames):
            mask.append(False)

        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "power"
            power_dir.mkdir()
            user_dir = Path(td) / "user"
            user_dir.mkdir()

            hooks_to_install = []
            for i, fname in enumerate(filenames):
                (power_dir / fname).write_text(f"content-{i}", encoding="utf-8")
                if mask[i]:
                    (user_dir / fname).write_text("pre-existing", encoding="utf-8")
                hooks_to_install.append((fname, f"Hook {i}", f"desc {i}"))

            mod = _load_install_hooks()
            installed, skipped = mod.install_hooks(hooks_to_install, power_dir, user_dir)

            expected_skipped = sum(1 for m in mask if m)
            expected_installed = len(filenames) - expected_skipped

            assert installed == expected_installed, (
                f"Expected {expected_installed} installed, got {installed}"
            )
            assert skipped == expected_skipped, (
                f"Expected {expected_skipped} skipped, got {skipped}"
            )
            assert installed + skipped == len(filenames)

            # Verify all hooks exist in user_dir
            for fname in filenames:
                assert (user_dir / fname).exists()
        finally:
            shutil.rmtree(td, ignore_errors=True)
