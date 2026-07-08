"""Tests for senzing-bootcamp/scripts/install_hooks.py (v1 ``.json`` model).

These tests exercise the installer's discovery, name resolution, and copy/skip
logic over temporary hook directories populated with Kiro 1.0 ``v1`` hook files
(``<id>.json`` wrappers of the form ``{"version": "v1", "hooks": [ ... ]}``).
The legacy ``*.kiro.hook`` model is no longer discovered or installed.
"""

import importlib
import json
import shutil
import tempfile
from pathlib import Path


def _load_install_hooks():
    """Import / reload install_hooks module."""
    import install_hooks
    importlib.reload(install_hooks)
    return install_hooks


# ---------------------------------------------------------------------------
# v1 hook-file helpers
# ---------------------------------------------------------------------------


def _v1_wrapper(name: str | None) -> dict:
    """Build a minimal v1 hook wrapper; omit ``name`` when it is None."""
    hook: dict = {"trigger": "Stop", "action": {"type": "agent", "prompt": "Do it."}}
    if name is not None:
        hook["name"] = name
    return {"version": "v1", "hooks": [hook]}


def _write_v1_hook(power_dir: Path, filename: str, name: str | None = None) -> None:
    """Write a schema-valid ``<id>.json`` v1 hook file.

    When *name* is None the hook carries no ``name`` field, forcing the
    installer onto its derived-display-name fallback path.
    """
    (power_dir / filename).write_text(
        json.dumps(_v1_wrapper(name), indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Example-based tests  (Task 9.1)
# ---------------------------------------------------------------------------


class TestDiscoverHooks:
    """Requirement 9.1 — discover_hooks returns entries for each ``.json`` file."""

    def test_discovers_known_hooks(self, project_root):
        power_dir = project_root / "hooks"
        power_dir.mkdir()
        # Create known v1 hook files.
        _write_v1_hook(power_dir, "code-style-check.json", name="to check code style")
        _write_v1_hook(power_dir, "backup-before-load.json", name="to back up first")

        mod = _load_install_hooks()
        result = mod.discover_hooks(power_dir)

        filenames = [entry[0] for entry in result]
        assert "code-style-check.json" in filenames
        assert "backup-before-load.json" in filenames
        assert len(result) == 2

    def test_discovers_unknown_hooks(self, project_root):
        power_dir = project_root / "hooks"
        power_dir.mkdir()
        # No ``name`` field → the installer derives the display name.
        _write_v1_hook(power_dir, "my-custom-hook.json", name=None)

        mod = _load_install_hooks()
        result = mod.discover_hooks(power_dir)

        assert len(result) == 1
        filename, name, desc = result[0]
        assert filename == "my-custom-hook.json"
        assert name == "My Custom Hook"
        assert "no description" in desc.lower() or "add to HOOK_METADATA" in desc

    def test_legacy_kiro_hook_files_are_not_discovered(self, project_root):
        """Residual ``*.kiro.hook`` files are ignored by the v1 ``*.json`` glob."""
        power_dir = project_root / "hooks"
        power_dir.mkdir()
        _write_v1_hook(power_dir, "code-style-check.json", name="to check code style")
        (power_dir / "legacy-hook.kiro.hook").write_text("legacy", encoding="utf-8")

        mod = _load_install_hooks()
        result = mod.discover_hooks(power_dir)

        filenames = {entry[0] for entry in result}
        assert filenames == {"code-style-check.json"}


class TestInstallHooks:
    """Requirement 9.3, 9.4, 9.5 — install_hooks copies/skips correctly."""

    def test_installs_new_hooks(self, project_root, capsys):
        power_dir = project_root / "power_hooks"
        power_dir.mkdir()
        user_dir = project_root / "user_hooks"
        user_dir.mkdir()

        _write_v1_hook(power_dir, "hook-a.json", name="to do a")
        _write_v1_hook(power_dir, "hook-b.json", name="to do b")

        hooks_to_install = [
            ("hook-a.json", "Hook A", "desc a"),
            ("hook-b.json", "Hook B", "desc b"),
        ]

        mod = _load_install_hooks()
        installed, skipped = mod.install_hooks(hooks_to_install, power_dir, user_dir)

        assert installed == 2
        assert skipped == 0
        assert (user_dir / "hook-a.json").exists()
        assert (user_dir / "hook-b.json").exists()

    def test_skips_existing_hooks(self, project_root, capsys):
        power_dir = project_root / "power_hooks"
        power_dir.mkdir()
        user_dir = project_root / "user_hooks"
        user_dir.mkdir()

        _write_v1_hook(power_dir, "hook-a.json", name="to do a")
        # Pre-install hook-a with distinct content.
        (user_dir / "hook-a.json").write_text("already-here", encoding="utf-8")

        hooks_to_install = [
            ("hook-a.json", "Hook A", "desc a"),
        ]

        mod = _load_install_hooks()
        installed, skipped = mod.install_hooks(hooks_to_install, power_dir, user_dir)

        assert installed == 0
        assert skipped == 1
        # Content should NOT be overwritten.
        assert (user_dir / "hook-a.json").read_text(encoding="utf-8") == "already-here"

    def test_mixed_install_and_skip(self, project_root, capsys):
        power_dir = project_root / "power_hooks"
        power_dir.mkdir()
        user_dir = project_root / "user_hooks"
        user_dir.mkdir()

        _write_v1_hook(power_dir, "hook-a.json", name="to do a")
        _write_v1_hook(power_dir, "hook-b.json", name="to do b")
        # Pre-install hook-a only.
        (user_dir / "hook-a.json").write_text("existing", encoding="utf-8")

        hooks_to_install = [
            ("hook-a.json", "Hook A", "desc a"),
            ("hook-b.json", "Hook B", "desc b"),
        ]

        mod = _load_install_hooks()
        installed, skipped = mod.install_hooks(hooks_to_install, power_dir, user_dir)

        assert installed == 1
        assert skipped == 1


# ---------------------------------------------------------------------------
# Property-based tests  (Tasks 9.2, 9.3, 9.4)
# ---------------------------------------------------------------------------

import hypothesis.strategies as st
from hypothesis import given, settings

# Strategy: generate valid v1 hook filenames (``<id>.json``).
hook_name_parts = st.from_regex(r"[a-z][a-z0-9]{1,8}", fullmatch=True)
hook_filenames = st.lists(
    st.builds(
        lambda parts: "-".join(parts) + ".json",
        st.lists(hook_name_parts, min_size=1, max_size=3),
    ),
    min_size=1,
    max_size=8,
    unique=True,
)


class TestProperty10HookDiscoveryCompleteness:
    """Property 10: Hook discovery completeness.

    **Validates: Requirements 9.1**

    For any set of ``.json`` v1 hook files, discover_hooks returns
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
                _write_v1_hook(power_dir, fname, name=f"to run {fname}")

            mod = _load_install_hooks()
            result = mod.discover_hooks(power_dir)

            result_filenames = {entry[0] for entry in result}
            assert result_filenames == set(filenames), (
                f"Expected {set(filenames)}, got {result_filenames}"
            )
            assert len(result) == len(filenames)
        finally:
            shutil.rmtree(td, ignore_errors=True)


# Strategy: generate hook filenames NOT in the known HOOK_METADATA overlay.
def _known_hook_filenames():
    mod = _load_install_hooks()
    return set(mod.HOOK_METADATA.keys())


# Strategy: generate hook filenames NOT in the known HOOK_METADATA overlay.
unknown_hook_filenames = st.builds(
    lambda parts: "-".join(parts) + ".json",
    st.lists(hook_name_parts, min_size=1, max_size=3),
).filter(lambda f: f not in _known_hook_filenames())


class TestProperty11UnknownHookNameDerivation:
    """Property 11: Unknown hook name derivation.

    **Validates: Requirements 9.2**

    For any ``.json`` file whose hook carries no ``name`` field, the display
    name is derived by removing the suffix, replacing hyphens, and title-casing.
    """

    # Feature: script-test-suite, Property 11: Unknown hook name derivation

    @given(filename=unknown_hook_filenames)
    @settings(max_examples=10)
    def test_derived_name_matches_convention(self, filename):
        td = tempfile.mkdtemp()
        try:
            power_dir = Path(td) / "hooks"
            power_dir.mkdir()
            # No ``name`` field → discovery falls back to derivation.
            _write_v1_hook(power_dir, filename, name=None)

            mod = _load_install_hooks()
            result = mod.discover_hooks(power_dir)

            assert len(result) == 1
            _, name, desc = result[0]

            # Expected: remove .json, replace hyphens with spaces, title-case.
            expected_name = filename[: -len(".json")].replace("-", " ").title()
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
        # Align mask length with filenames.
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
                _write_v1_hook(power_dir, fname, name=f"to run {i}")
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

            # Verify all hooks exist in user_dir.
            for fname in filenames:
                assert (user_dir / fname).exists()
        finally:
            shutil.rmtree(td, ignore_errors=True)
