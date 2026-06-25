"""Mode / metadata unit tests for the install_hooks.py installer.

Feature: hook-architecture-improvements (Theme C — capture-hook install
reliability).

These are *script-behavior* example/unit tests exercised over temporary hook
directories (never the real ``.kiro/hooks``), so per ``structure.md`` they live
in ``senzing-bootcamp/tests/`` rather than the repo-root ``tests/``.

Property-based coverage of the installer logic lives in
``test_install_hooks_properties.py`` (task 5.4); this file covers the
non-interactive mode contract, interactive-retention, the metadata overlay, and
the discovery-driven set, as example/unit tests (Hypothesis not required):

- ``--all`` installs every discovered hook and exits 0 (Req 11.1).
- ``--essential`` installs only the essential set and exits 0 (Req 11.2).
- Interactive mode is retained when no flag is supplied (Req 11.6).
- The five current hooks are present in ``HOOK_METADATA`` with accurate names
  read from each hook file's ``name`` field (Req 9.2).
- ``discover_hooks`` derives the set from the ``*.kiro.hook`` glob rather than
  from ``HOOK_METADATA`` (Req 9.5).
"""

from __future__ import annotations

import builtins
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make senzing-bootcamp/scripts/ importable (scripts aren't packages)
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import install_hooks  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_hook(power_dir: Path, hook_id: str, name: str | None = None) -> None:
    """Write a minimal, schema-valid ``<hook_id>.kiro.hook`` JSON fixture.

    Args:
        power_dir: Directory to write the hook file into.
        hook_id: Hook id (no ``.kiro.hook`` suffix).
        name: Optional ``name`` field; defaults to a "to {verb phrase}" string.
    """
    verb_phrase = hook_id.replace("-", " ")
    data = {
        "name": name if name is not None else f"to {verb_phrase}",
        "version": "1.0.0",
        "when": {"type": "agentStop"},
        "then": {"type": "askAgent", "prompt": f"Do the {verb_phrase} thing."},
    }
    (power_dir / f"{hook_id}.kiro.hook").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


# The five current hooks Requirement 9.2 mandates in the metadata overlay.
FIVE_CURRENT_HOOK_IDS = (
    "write-policy-gate",
    "session-log-events",
    "module-recap-append",
    "enforce-mandatory-gate",
    "enforce-gate-on-stop",
)


# ---------------------------------------------------------------------------
# --all mode (Req 11.1)
# ---------------------------------------------------------------------------


class TestAllMode:
    """``--all`` installs every discovered hook into a temp user dir, exits 0.

    **Validates: Requirements 11.1**
    """

    def test_all_installs_every_discovered_hook_and_exits_zero(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        user_dir = tmp_path / "user_hooks"
        hook_ids = ["ask-bootcamper", "write-policy-gate", "some-other-hook"]
        for hook_id in hook_ids:
            _write_hook(power_dir, hook_id)

        code = install_hooks.main(
            ["--all", "--power-dir", str(power_dir), "--user-dir", str(user_dir)]
        )

        assert code == 0
        # Every discovered hook is copied into the temp user dir.
        for hook_id in hook_ids:
            assert (user_dir / f"{hook_id}.kiro.hook").is_file()
        installed = {p.name for p in user_dir.glob("*.kiro.hook")}
        assert installed == {f"{hook_id}.kiro.hook" for hook_id in hook_ids}

    def test_all_does_not_call_input(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        user_dir = tmp_path / "user_hooks"
        _write_hook(power_dir, "ask-bootcamper")

        def _boom(*_args: object, **_kwargs: object) -> str:
            raise AssertionError("--all must not call input()")

        monkeypatch.setattr(builtins, "input", _boom)

        code = install_hooks.main(
            ["--all", "--power-dir", str(power_dir), "--user-dir", str(user_dir)]
        )

        assert code == 0


# ---------------------------------------------------------------------------
# --essential mode (Req 11.2)
# ---------------------------------------------------------------------------


class TestEssentialMode:
    """``--essential`` installs only the essential set, exits 0.

    **Validates: Requirements 11.2**
    """

    def test_essential_installs_only_essential_set_and_exits_zero(
        self, tmp_path: Path
    ) -> None:
        # Pick concrete essential ids from the installer's own ESSENTIAL set,
        # plus an id that is guaranteed NOT essential.
        essential_ids = sorted(install_hooks.ESSENTIAL)[:2]
        assert essential_ids, "ESSENTIAL set unexpectedly empty"
        non_essential_id = "totally-not-an-essential-hook"
        assert non_essential_id not in install_hooks.ESSENTIAL

        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        user_dir = tmp_path / "user_hooks"
        for hook_id in [*essential_ids, non_essential_id]:
            _write_hook(power_dir, hook_id)

        code = install_hooks.main(
            ["--essential", "--power-dir", str(power_dir), "--user-dir", str(user_dir)]
        )

        assert code == 0
        # Only the essential hooks are installed; the non-essential one is not.
        for hook_id in essential_ids:
            assert (user_dir / f"{hook_id}.kiro.hook").is_file()
        assert not (user_dir / f"{non_essential_id}.kiro.hook").exists()

    def test_essential_does_not_call_input(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        user_dir = tmp_path / "user_hooks"
        for hook_id in sorted(install_hooks.ESSENTIAL)[:2]:
            _write_hook(power_dir, hook_id)

        def _boom(*_args: object, **_kwargs: object) -> str:
            raise AssertionError("--essential must not call input()")

        monkeypatch.setattr(builtins, "input", _boom)

        code = install_hooks.main(
            ["--essential", "--power-dir", str(power_dir), "--user-dir", str(user_dir)]
        )

        assert code == 0


# ---------------------------------------------------------------------------
# Interactive mode retained when no flag (Req 11.6)
# ---------------------------------------------------------------------------


class TestInteractiveRetained:
    """No flag supplied → the interactive (stdin-reading) path is reached.

    **Validates: Requirements 11.6**
    """

    def test_no_flag_reaches_interactive_path_and_uses_input(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        user_dir = tmp_path / "user_hooks"
        _write_hook(power_dir, "ask-bootcamper")

        calls: list[str] = []

        def _fake_input(prompt: str = "") -> str:
            calls.append(prompt)
            return "Q"  # quit cleanly

        monkeypatch.setattr(builtins, "input", _fake_input)

        code = install_hooks.main(
            ["--power-dir", str(power_dir), "--user-dir", str(user_dir)]
        )

        # The no-flag path MUST reach the interactive menu, i.e. call input().
        assert calls, "no-flag path did not call input()"
        # Choosing 'Q' (quit) is a clean exit.
        assert code == 0

    def test_run_interactive_quit_returns_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        user_dir = tmp_path / "user_hooks"
        _write_hook(power_dir, "ask-bootcamper")
        hooks = install_hooks.discover_hooks(power_dir)

        monkeypatch.setattr(builtins, "input", lambda *_a, **_k: "Q")

        code = install_hooks.run_interactive(hooks, power_dir, user_dir)

        assert code == 0


# ---------------------------------------------------------------------------
# Metadata overlay (Req 9.2)
# ---------------------------------------------------------------------------


class TestMetadata:
    """The five current hooks are in HOOK_METADATA; names come from hook files.

    **Validates: Requirements 9.2**
    """

    def test_five_current_hooks_present_in_metadata(self) -> None:
        expected_keys = {f"{hook_id}.kiro.hook" for hook_id in FIVE_CURRENT_HOOK_IDS}
        assert expected_keys <= set(install_hooks.HOOK_METADATA)
        # Each metadata entry carries a non-empty description string.
        for key in expected_keys:
            desc = install_hooks.HOOK_METADATA[key]
            assert isinstance(desc, str) and desc.strip()

    def test_consolidated_hooks_absent_from_metadata(self) -> None:
        for consolidated in (
            "enforce-file-path-policies",
            "enforce-single-question",
            "block-direct-sql",
        ):
            assert f"{consolidated}.kiro.hook" not in install_hooks.HOOK_METADATA

    def test_discover_reads_name_field_for_current_hooks(
        self, tmp_path: Path
    ) -> None:
        # Display names must come from each hook file's `name` field (the
        # "to {verb phrase}" pattern), not from the metadata overlay.
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        names = {
            "write-policy-gate": "to process your response",
            "session-log-events": "to log session events after write operations",
            "module-recap-append": "to append module recap on completion",
            "enforce-mandatory-gate": (
                "to enforce mandatory gate step execution before advancement"
            ),
            "enforce-gate-on-stop": "to enforce mandatory gate execution on agent stop",
        }
        for hook_id, name in names.items():
            _write_hook(power_dir, hook_id, name=name)

        discovered = {
            entry[0]: entry for entry in install_hooks.discover_hooks(power_dir)
        }

        for hook_id, name in names.items():
            filename = f"{hook_id}.kiro.hook"
            assert filename in discovered
            assert discovered[filename][1] == name


# ---------------------------------------------------------------------------
# Discovery-driven set (Req 9.5)
# ---------------------------------------------------------------------------


class TestDiscoveryDriven:
    """discover_hooks derives the set from the glob, not from HOOK_METADATA.

    **Validates: Requirements 9.5**
    """

    def test_hook_absent_from_metadata_is_still_discovered(
        self, tmp_path: Path
    ) -> None:
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        novel_id = "brand-new-undocumented-hook"
        assert f"{novel_id}.kiro.hook" not in install_hooks.HOOK_METADATA
        _write_hook(power_dir, novel_id)

        discovered = install_hooks.discover_hooks(power_dir)

        # The single real file is discovered even though it has no metadata.
        assert len(discovered) == 1
        filename, name, desc = discovered[0]
        assert filename == f"{novel_id}.kiro.hook"
        # Name is read from the file's `name` field.
        assert name == "to brand new undocumented hook"
        # A fallback description is supplied for unknown hooks.
        assert "no description" in desc.lower() or "HOOK_METADATA" in desc

    def test_discovered_set_is_only_glob_not_metadata(self, tmp_path: Path) -> None:
        # A metadata-listed id absent from disk must NOT appear; only on-disk
        # *.kiro.hook files drive the discovered set.
        power_dir = tmp_path / "hooks"
        power_dir.mkdir()
        on_disk_ids = ["ask-bootcamper", "brand-new-undocumented-hook"]
        for hook_id in on_disk_ids:
            _write_hook(power_dir, hook_id)

        discovered_filenames = {
            entry[0] for entry in install_hooks.discover_hooks(power_dir)
        }

        assert discovered_filenames == {
            f"{hook_id}.kiro.hook" for hook_id in on_disk_ids
        }
        # The metadata table is larger than the on-disk set, proving the set is
        # glob-driven rather than metadata-driven.
        assert len(install_hooks.HOOK_METADATA) > len(discovered_filenames)
